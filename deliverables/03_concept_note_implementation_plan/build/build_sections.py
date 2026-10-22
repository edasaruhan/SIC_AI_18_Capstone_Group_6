"""Fill the instructor's concept-note template from a markdown file.

Usage (from anywhere):
  python -I build_sections.py                  concept_note.md -> ../NudgeWell_Group6_Concept_Note_Implementation_Plan.docx
  python -I build_sections.py SRC.md OUT.docx  any other markdown file in the same format
Relative paths are resolved against this folder.
Template (read only): <root>/guidelines/Concept_Note_and_Implementation_Plan_Template.docx, the instructor's file.
It is not part of the GitHub repository; put a copy there to rebuild.

The output keeps the template's own look (Times New Roman 12 pt, bold numbered headings, its bullet lists).
Template headings that the markdown leaves out keep the instructor's prompts. '## References' fills '6. References'.

Markdown conventions
- Front matter between the first two '---' lines: title, team_heading, members (separated by '·');
  optional doc_title and subject for the file properties.
- '## N. Heading' must match a template heading; the prompt bullets under it are replaced by the content below it.
  '## References' fills the template's '6. References'.
- '### ' sub-headings; '- ' bullets; '1. ' numbered items.
- 'Table N. caption' + optional '<!-- widths: a,b,c -->' + a pipe table ('<br>' splits a cell into paragraphs);
  a paragraph starting with 'Note.' right after a table.
- 'Figure N. caption' + '<!-- image: relative/path.png width=16 -->' (width in cm); optional 'Note.' after it.
- Inline **bold**, *italic* and bare https:// links.
"""
import copy
import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docx.text.paragraph import Paragraph

HERE = Path(__file__).resolve().parent
SRC = HERE / "concept_note.md"
TEMPLATE = HERE.parents[2] / "guidelines" / "Concept_Note_and_Implementation_Plan_Template.docx"
OUT = HERE.parent / "NudgeWell_Group6_Concept_Note_Implementation_Plan.docx"

FONT = "Times New Roman"
BODY_PT, CAPTION_PT, TABLE_PT, NOTE_PT = 12, 11, 10, 10
BULLET_NUM_ID = 12            # the template's own bullet list (the one under '1. Project Overview')
PROMPT_STYLES = {"List Paragraph", "Normal (Web)"}
HEAD_FILL, RULE, LINK = "F2F2F2", "808080", "0563C1"
TEXT_WIDTH_CM = 16.0          # A4 with the template's 2.5 cm margins

TOKEN = re.compile(r"(\*\*.+?\*\*|\*[^*\s][^*]*?\*|https?://[^\s)]+)")


# ---------- runs and inline markup ----------

def style_run(run, size=BODY_PT, bold=False, italic=False):
    run.bold, run.italic = bold or None, italic or None
    run.font.size = Pt(size)
    run.font.name = FONT
    rfonts = run._r.get_or_add_rPr().get_or_add_rFonts()
    for attr in ("w:eastAsia", "w:cs"):
        rfonts.set(qn(attr), FONT)
    return run


def add_hyperlink(paragraph, url, size):
    r_id = paragraph.part.relate_to(url, RT.HYPERLINK, is_external=True)
    link = OxmlElement("w:hyperlink")
    link.set(qn("r:id"), r_id)
    run = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")
    fonts = OxmlElement("w:rFonts")
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        fonts.set(qn(attr), FONT)
    color = OxmlElement("w:color")
    color.set(qn("w:val"), LINK)
    underline = OxmlElement("w:u")
    underline.set(qn("w:val"), "single")
    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), str(int(size * 2)))
    for el in (fonts, color, sz, underline):  # schema order: rFonts, color, sz, u
        rpr.append(el)
    run.append(rpr)
    text = OxmlElement("w:t")
    text.set(qn("xml:space"), "preserve")
    text.text = url
    run.append(text)
    link.append(run)
    paragraph._p.append(link)


def add_inline(paragraph, text, size=BODY_PT, bold=False, italic=False):
    pos = 0
    for m in TOKEN.finditer(text):
        if m.start() > pos:
            style_run(paragraph.add_run(text[pos:m.start()]), size, bold, italic)
        tok = m.group(0)
        if tok.startswith("**"):
            add_inline(paragraph, tok[2:-2], size, True, italic)
        elif tok.startswith("http"):
            add_hyperlink(paragraph, tok, size)
        else:
            add_inline(paragraph, tok[1:-1], size, bold, True)
        pos = m.end()
    if pos < len(text):
        style_run(paragraph.add_run(text[pos:]), size, bold, italic)


def fmt(paragraph, before=0, after=6, keep=False, line=1.15):
    pf = paragraph.paragraph_format
    pf.space_before, pf.space_after, pf.line_spacing = Pt(before), Pt(after), line
    pf.keep_with_next = keep or None
    return paragraph


# ---------- table ----------

def border(parent, side, size=4, color=RULE):
    el = OxmlElement(f"w:{side}")
    el.set(qn("w:val"), "single")
    el.set(qn("w:sz"), str(size))
    el.set(qn("w:space"), "0")
    el.set(qn("w:color"), color)
    parent.append(el)


def shade(cell, fill):
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tcpr = cell._tc.get_or_add_tcPr()
    tcpr.insert_element_before(shd, "w:noWrap", "w:tcMar", "w:textDirection", "w:tcFitText", "w:vAlign", "w:hideMark")


TBLPR_ORDER = ("w:tblStyle", "w:tblpPr", "w:tblOverlap", "w:bidiVisual", "w:tblStyleRowBandSize", "w:tblStyleColBandSize",
               "w:tblW", "w:jc", "w:tblCellSpacing", "w:tblInd", "w:tblBorders", "w:shd", "w:tblLayout", "w:tblCellMar",
               "w:tblLook", "w:tblCaption", "w:tblDescription")


def tblpr_insert(tblpr, el):
    tag = "w:" + el.tag.split("}")[1]
    tblpr.insert_element_before(el, *TBLPR_ORDER[TBLPR_ORDER.index(tag) + 1:])


def build_table(doc, rows, widths):
    ncol = len(rows[0])
    widths = widths or [1] * ncol
    cms = [w / sum(widths) * TEXT_WIDTH_CM for w in widths]
    t = doc.add_table(rows=0, cols=ncol)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    tblpr = t._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        border(borders, side)
    tblpr_insert(tblpr, borders)
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tblpr_insert(tblpr, layout)
    mar = OxmlElement("w:tblCellMar")
    for side, val in (("top", 40), ("left", 80), ("bottom", 40), ("right", 80)):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:w"), str(val))
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    tblpr_insert(tblpr, mar)
    for gc, cm in zip(t._tbl.tblGrid.findall(qn("w:gridCol")), cms):  # fixed layout reads the grid
        gc.set(qn("w:w"), str(round(cm / 2.54 * 1440)))
    for i, row in enumerate(rows):
        cells = t.add_row().cells
        trpr = t.rows[-1]._tr.get_or_add_trPr()
        trpr.append(OxmlElement("w:cantSplit"))
        if i == 0:
            trpr.append(OxmlElement("w:tblHeader"))
        for j, text in enumerate(row):
            cell = cells[j]
            cell.width = Cm(cms[j])
            if i == 0:
                shade(cell, HEAD_FILL)
            parts = text.split("<br>")  # '<br>' starts a new paragraph inside the cell
            p = fmt(cell.paragraphs[0], after=0, keep=(i == 0), line=1.0)  # header stays with the first row; tables may split
            add_inline(p, parts[0], TABLE_PT, bold=(i == 0))
            for part in parts[1:]:
                add_inline(fmt(cell.add_paragraph(), before=2, after=0, line=1.0), part, TABLE_PT, bold=(i == 0))
    return t


# ---------- markdown blocks -> document elements ----------

class Writer:
    """Creates elements at the end of the body, then moves each one to just after the current anchor."""

    def __init__(self, doc, anchor, base):
        self.doc, self.anchor, self.base = doc, anchor, base  # base: folder that figure paths are relative to

    def place(self, el):
        self.anchor.addnext(el)
        self.anchor = el

    def paragraph(self):
        p = self.doc.add_paragraph()
        self.place(p._p)
        return p

    def table(self, rows, widths):
        t = build_table(self.doc, rows, widths)
        self.place(t._tbl)
        return t


def write_blocks(w, lines, refs=False):
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if not s:
            i += 1
            continue
        if s.startswith("### "):
            add_inline(fmt(w.paragraph(), before=8, after=4, keep=True), s[4:], BODY_PT, bold=True, italic=True)
            i += 1
            continue
        if re.match(r"^Table \d+\. ", s):
            label, _, rest = s.partition(". ")
            p = fmt(w.paragraph(), before=6, after=4, keep=True)
            style_run(p.add_run(label + ". "), CAPTION_PT, bold=True)
            add_inline(p, rest, CAPTION_PT)
            i += 1
            widths = None
            if i < len(lines) and lines[i].strip().startswith("<!-- widths:"):
                widths = [float(x) for x in re.findall(r"[\d.]+", lines[i])]
                i += 1
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            w.table(rows, widths)
            while i < len(lines) and not lines[i].strip():
                i += 1
            if i < len(lines) and lines[i].strip().startswith("Note. "):
                p = fmt(w.paragraph(), before=3, after=10, line=1.0)
                style_run(p.add_run("Note. "), NOTE_PT, italic=True)
                add_inline(p, lines[i].strip()[6:], NOTE_PT)
                i += 1
            else:
                fmt(w.paragraph(), after=4)  # spacer after the table
            continue
        if re.match(r"^Figure \d+\. ", s):
            label, _, rest = s.partition(". ")
            p = fmt(w.paragraph(), before=6, after=4, keep=True)
            style_run(p.add_run(label + ". "), CAPTION_PT, bold=True)
            add_inline(p, rest, CAPTION_PT)
            i += 1
            m = re.match(r"^<!-- image: (\S+) width=([\d.]+) -->$", lines[i].strip()) if i < len(lines) else None
            assert m, f"'{s}' must be followed by an '<!-- image: path width=cm -->' line"
            img = (w.base / m.group(1)).resolve()
            assert img.exists(), f"missing figure file {img}"
            p = fmt(w.paragraph(), after=4, line=1.0)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.add_run().add_picture(str(img), width=Cm(float(m.group(2))))
            i += 1
            while i < len(lines) and not lines[i].strip():
                i += 1
            if i < len(lines) and lines[i].strip().startswith("Note. "):
                p = fmt(w.paragraph(), before=3, after=10, line=1.0)
                style_run(p.add_run("Note. "), NOTE_PT, italic=True)
                add_inline(p, lines[i].strip()[6:], NOTE_PT)
                i += 1
            else:
                fmt(w.paragraph(), after=4)
            continue
        if s.startswith("- "):
            while i < len(lines) and lines[i].strip().startswith("- "):
                p = w.paragraph()
                p.style = w.doc.styles["List Paragraph"]
                num = p._p.get_or_add_pPr().get_or_add_numPr()
                num.get_or_add_ilvl().val = 0
                num.get_or_add_numId().val = BULLET_NUM_ID
                add_inline(fmt(p, after=3), lines[i].strip()[2:])
                i += 1
            p.paragraph_format.space_after = Pt(8)  # List Paragraph drops spacing inside the list; keep a gap after it
            continue
        if re.match(r"^\d+\. ", s):
            while i < len(lines) and re.match(r"^\d+\. ", lines[i].strip()):
                n, text = lines[i].strip().split(". ", 1)
                p = fmt(w.paragraph(), after=4)
                p.paragraph_format.left_indent = Cm(0.63)
                p.paragraph_format.first_line_indent = Cm(-0.63)
                p.paragraph_format.tab_stops.add_tab_stop(Cm(0.63))
                style_run(p.add_run(f"{n}.\t"))
                add_inline(p, text)
                i += 1
            continue
        buf = []
        while i < len(lines) and lines[i].strip() and not re.match(r"^(### |- |\d+\. |\||Table \d+\. |Figure \d+\. |<!--)",
                                                                   lines[i].strip()):
            buf.append(lines[i].strip())
            i += 1
        p = fmt(w.paragraph(), after=6)
        if refs:  # APA hanging indent
            p.paragraph_format.left_indent = Cm(1.27)
            p.paragraph_format.first_line_indent = Cm(-1.27)
        add_inline(p, " ".join(buf))


# ---------- template edits ----------

def parse(md):
    lines = md.splitlines()
    meta, i = {}, 0
    if lines and lines[0].strip() == "---":
        i = 1
        while lines[i].strip() != "---":
            k, _, v = lines[i].partition(":")
            meta[k.strip()] = v.strip()
            i += 1
        i += 1
    sections, current = {}, None
    for line in lines[i:]:
        m = re.match(r"^## (.+)$", line.strip())
        if m:
            current = m.group(1).strip()
            sections[current] = []
        elif current is not None:
            sections[current].append(line.rstrip())
    return meta, sections


def set_text(paragraph, text):
    runs = paragraph.runs
    runs[0].text = text
    for r in runs[1:]:
        r._r.getparent().remove(r._r)


def find(doc, text):
    hits = [p for p in doc.paragraphs if p.text.strip() == text]
    assert len(hits) == 1, f"expected one template paragraph {text!r}, found {len(hits)}"
    return hits[0]


def build(src=SRC, out=OUT):
    meta, sections = parse(src.read_text(encoding="utf-8"))
    doc = Document(str(TEMPLATE))

    title = [p for p in doc.paragraphs if p.text.startswith("Project Title:")]
    assert len(title) == 1
    set_text(title[0], f"Project Title: {meta['title']}")
    set_text(find(doc, "Team Members"), meta["team_heading"])

    names = [n.strip() for n in meta["members"].split("·")]
    first, second = find(doc, "[Team Member 1]"), find(doc, "[Team Member 2]")
    set_text(first, names[0])
    set_text(second, names[1])
    anchor = second._p
    for name in names[2:]:
        el = copy.deepcopy(second._p)
        anchor.addnext(el)
        anchor = el
        set_text(Paragraph(el, second._parent), name)

    for heading, lines in sections.items():
        target = find(doc, "6. References" if heading == "References" else heading)
        fmt(target, before=10, after=6, keep=True, line=None)
        nxt = target._p.getnext()  # drop the instructor's prompt bullets under this heading
        while nxt is not None and nxt.tag == qn("w:p") and Paragraph(nxt, target._parent).style.name in PROMPT_STYLES:
            following = nxt.getnext()
            nxt.getparent().remove(nxt)
            nxt = following
        write_blocks(Writer(doc, target._p, src.parent), lines, refs=(heading == "References"))

    props = doc.core_properties
    props.title = meta.get("doc_title", "NudgeWell: Concept Note and Implementation Plan")
    props.author = props.last_modified_by = "Group 6"
    props.subject = meta.get("subject", "SIC AI Cohort 18 Digital Addiction Capstone, homework 3")
    doc.save(out)
    print("wrote", out)


if __name__ == "__main__":
    args = [(HERE / a).resolve() for a in sys.argv[1:3]]
    build(*args)
