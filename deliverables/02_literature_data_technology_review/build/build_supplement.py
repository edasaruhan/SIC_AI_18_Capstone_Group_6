"""Builds the interactive supplement to the review: one self-contained HTML file (figures embedded),
plus an optional PDF copy printed with Microsoft Edge.

Run from this folder:
    python -I build_supplement.py          # HTML only
    python -I build_supplement.py --pdf    # HTML and PDF

Numbers come from eda_summary.json (written by notebooks/01_awaremind_eda.ipynb); figure captions and
APA references are copied from report.md, so the supplement stays in step with the report.
"""
import base64
import html
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
DELIV = HERE.parent
FIG = DELIV / "figures"
NAME = "NudgeWell_Group6_Literature_Data_Technology_Review_Supplement"
OUT_HTML = DELIV / f"{NAME}.html"
OUT_PDF = DELIV / f"{NAME}.pdf"

SUMMARY = json.loads((HERE / "eda_summary.json").read_text(encoding="utf-8"))
REPORT = (HERE / "report.md").read_text(encoding="utf-8")
FRONT = dict(re.findall(r"^(\w+): (.+)$", REPORT.split("---")[1], flags=re.M))
MEMBERS = [m.strip() for m in FRONT["members"].split("·")]

# References cited in the supplement, in APA order; each is copied from report.md
REF_KEYS = [
    "Android Developers. (n.d.). *UsageStatsManager*", "Google AI Edge. (n.d.)", "Haliburton, L.", "Katevas, K.",
    "Law No. 6698", "Lundberg, S.", "Noyan, C.", "ONNX Runtime. (n.d.)", "Orzikulova, A.", "Parry, D. A.",
    "Winbush, A.", "Xu, X.", "Zheng, J., & Choe, E. K. (2026a)", "Zheng, J., & Choe, E. K. (2026b)",
]


def reference(key):
    line = next(l for l in REPORT.splitlines() if l.startswith(key))
    text = html.escape(line, quote=False)
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    return re.sub(r"(https?://\S+)", r'<a href="\1">\1</a>', text)


def img(file):
    return "data:image/png;base64," + base64.b64encode((FIG / file).read_bytes()).decode()


ROWS = SUMMARY["by_answer"]["rows"]
ANSWERS = [{"a": r["answer"], "n": r["n"], "over5": r["over5_pct"], "med": r["median_min"]} for r in ROWS]


def answer_table():
    head = "".join(f'<th scope="col" class="{"s" if r["answer"] <= 5 else "c"}">{r["answer"]}</th>' for r in ROWS)
    rows = [
        ("Check-ins", [f'{r["n"]:,}' for r in ROWS]),
        ("Over 5 more minutes", [f'{r["over5_pct"]:.1f}%' for r in ROWS]),
        ("Median further use (min)", [f'{r["median_min"]:.1f}' for r in ROWS]),
    ]
    body = "".join(f'<tr><th scope="row">{label}</th>' + "".join(f"<td>{v}</td>" for v in vals) + "</tr>"
                   for label, vals in rows)
    return (f'<div class="answers-wrap" role="region" aria-label="What happened after each answer" tabindex="0">'
            f'<table class="answers"><caption>What happened after each answer (all {SUMMARY["dataset"]["rows"]:,} check-ins)</caption>'
            f'<thead><tr><th scope="row">Answer</th>{head}</tr></thead><tbody>{body}</tbody></table></div>')


BA = SUMMARY["by_answer"]
TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Interactive supplement to Group 6's NudgeWell Literature, Data and Technology Review.">
<title>NudgeWell · Interactive supplement · Group 6</title>
<style>
:root {
  --night: #101b33;        /* 3 am indigo: the hero */
  --night-2: #1b2b52;
  --ink: #1f3a5f;          /* ink navy: headings (the report's colour) */
  --text: #243042;
  --muted: #5a6678;
  --signal: #2a78d6;       /* signal blue: data, same as the figures */
  --link: #1f5fad;
  --coral: #eb6834;        /* stop coral: the gap, used sparingly */
  --coral-text: #b8461c;
  --paper: #f5f7fa;
  --mist: #dce4ee;
  --card: #ffffff;
  --display: "Bahnschrift", "DIN Alternate", "Arial Narrow", sans-serif;
  --body: "Segoe UI Variable Text", "Segoe UI", system-ui, sans-serif;
  --mono: "Cascadia Mono", Consolas, ui-monospace, monospace;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body { margin: 0; background: var(--paper); color: var(--text); font: 16px/1.6 var(--body); }
a { color: var(--link); text-underline-offset: 3px; }
:focus-visible { outline: 3px solid var(--signal); outline-offset: 3px; border-radius: 6px; }
code { font-family: var(--mono); font-size: .86em; }
.wrap { max-width: 1080px; margin: 0 auto; padding: 0 24px; }

/* ---------- hero: the 3 am lock screen ---------- */
.hero { background: radial-gradient(120% 90% at 20% 0%, var(--night-2) 0%, var(--night) 60%); color: #e8eefb; padding: 56px 0 64px; }
.hero .wrap { display: grid; grid-template-columns: 330px 1fr; gap: 64px; align-items: center; }
.phone { width: 330px; border-radius: 48px; padding: 14px; background: #070c18; box-shadow: 0 30px 80px rgba(0,0,0,.45), inset 0 0 0 2px #2a3550; }
.screen { border-radius: 36px; min-height: 640px; padding: 26px 20px 22px; background: linear-gradient(170deg, #253a6b 0%, #142246 45%, #0c1630 100%); display: flex; flex-direction: column; }
.lock-date { text-align: center; font: 500 15px/1.2 var(--display); letter-spacing: .02em; color: #c7d3ee; margin-top: 18px; }
.lock-clock { text-align: center; font: 600 92px/1 var(--display); font-stretch: 87.5%; letter-spacing: -.01em; color: #f4f7ff; margin: 6px 0 26px; }
.checkin { margin-top: auto; background: rgba(255,255,255,.09); border: 1px solid rgba(255,255,255,.14); border-radius: 22px; padding: 16px 16px 14px; }
.checkin .eyebrow { font: 600 11px/1 var(--body); letter-spacing: .12em; text-transform: uppercase; color: #9fb4dd; }
.checkin .question { font: 500 19px/1.35 var(--body); color: #fff; margin: 8px 0 12px; }
.blank { display: inline-block; min-width: 54px; border-bottom: 2px solid #f4f7ff; text-align: center; font-family: var(--display); font-weight: 600; color: #fff; }
.scale { display: grid; grid-template-columns: repeat(5, 1fr); gap: 7px; }
.scale button { font: 600 17px/1 var(--display); color: #e8eefb; background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.18); border-radius: 12px; height: 44px; cursor: pointer; transition: background .15s, border-color .15s; }
.scale button:hover { background: rgba(255,255,255,.16); }
.scale button.stop[aria-pressed="true"] { background: var(--coral); border-color: var(--coral); color: #fff; }
.scale button.go[aria-pressed="true"] { background: var(--signal); border-color: var(--signal); color: #fff; }
.scale-ends { display: flex; justify-content: space-between; font-size: 12px; color: #9fb4dd; margin-top: 6px; }
.answer { margin-top: 14px; min-height: 118px; font-size: 14.5px; line-height: 1.5; color: #dbe4f7; }
.answer strong { font: 600 30px/1 var(--display); display: block; margin-bottom: 4px; }
.answer .stop-num { color: #ffb08d; }
.answer .go-num { color: #9cc4f5; }
.hero-text .eyebrow { font: 600 13px/1.4 var(--body); letter-spacing: .14em; text-transform: uppercase; color: #9fb4dd; }
.hero-text h1 { font: 600 clamp(38px, 5vw, 62px)/1.04 var(--display); font-stretch: 87.5%; margin: 14px 0 20px; color: #fff; }
.hero-text h1 em { font-style: normal; color: #ffb08d; }
.hero-text p { font-size: 18px; color: #c7d3ee; max-width: 560px; margin: 0 0 16px; }
.hero-fact { display: flex; gap: 28px; margin: 28px 0 30px; flex-wrap: wrap; }
.hero-fact div { border-left: 3px solid var(--coral); padding-left: 14px; max-width: 250px; }
.hero-fact b { display: block; font: 600 40px/1 var(--display); color: #fff; margin-bottom: 4px; }
.hero-fact span { font-size: 14px; color: #aebcdb; }
.hero-cta { display: inline-block; font-weight: 600; color: #fff; text-decoration: none; border-bottom: 2px solid var(--coral); padding-bottom: 2px; }
.hero-meta { margin-top: 30px; padding-top: 14px; border-top: 1px solid rgba(255,255,255,.14); font-size: 13.5px; line-height: 1.55; color: #aebcdb; max-width: 560px; }
.hero-meta b { color: #e8eefb; font-weight: 600; }

/* ---------- nav ---------- */
.nav { position: sticky; top: 0; z-index: 5; background: rgba(245,247,250,.94); border-bottom: 1px solid var(--mist); }
.nav .wrap { display: flex; gap: 22px; overflow-x: auto; padding-top: 12px; padding-bottom: 12px; white-space: nowrap; }
.nav a { color: var(--muted); text-decoration: none; font-size: 14px; font-weight: 600; }
.nav a:hover { color: var(--ink); }

/* ---------- sections ---------- */
section.block { padding: 72px 0 8px; scroll-margin-top: 52px; }
.kicker { font: 600 13px/1 var(--body); letter-spacing: .14em; text-transform: uppercase; color: var(--signal); }
h2 { font: 600 clamp(28px, 3.6vw, 42px)/1.1 var(--display); font-stretch: 87.5%; color: var(--ink); margin: 10px 0 14px; }
h3 { font: 600 21px/1.25 var(--display); color: var(--ink); margin: 0 0 6px; }
.subhead { font-size: 23px; margin: 34px 0 14px; }
.lead { font-size: 18px; color: var(--muted); max-width: 760px; margin: 0 0 28px; }
.card { background: var(--card); border: 1px solid var(--mist); border-radius: 16px; padding: 22px 24px; }
.grid3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
.grid4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }

/* project */
.pipe { display: grid; grid-template-columns: repeat(5, 1fr); gap: 0; margin-top: 8px; }
.pipe div { background: var(--card); border: 1px solid var(--mist); padding: 16px 14px; position: relative; }
.pipe div:first-child { border-radius: 14px 0 0 14px; }
.pipe div:last-child { border-radius: 0 14px 14px 0; background: #fff6f1; border-color: #f6d3c3; }
.pipe div + div { border-left: none; }
.pipe div:not(:last-child)::after { content: ""; position: absolute; right: -8px; top: 50%; width: 14px; height: 14px; background: inherit; border-top: 1px solid var(--mist); border-right: 1px solid var(--mist); transform: translateY(-50%) rotate(45deg); z-index: 1; }
.pipe b { display: block; font: 600 16px/1.2 var(--display); color: var(--ink); margin-bottom: 4px; }
.pipe span { font-size: 13.5px; color: var(--muted); }
.facts { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 22px; }
.facts .card b { display: block; font: 600 15px/1.2 var(--body); color: var(--ink); margin-bottom: 4px; }
.facts .card { padding: 16px 18px; font-size: 14.5px; }

/* findings */
.finding { display: grid; grid-template-columns: 250px 1fr; gap: 28px; padding: 26px 0; border-top: 1px solid var(--mist); align-items: start; }
.finding:first-of-type { border-top: none; }
.finding > div { min-width: 0; }   /* lets the answer table scroll inside its box on narrow screens */
.num { font: 600 64px/0.95 var(--display); font-stretch: 87.5%; color: var(--signal); }
.num.gap { color: var(--coral); }
.num-label { font-size: 14px; color: var(--muted); margin-top: 6px; }
.finding p { margin: 0 0 12px; }
.which { font-size: 12px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }
.sup { font-size: 12px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--coral-text); }
figure { margin: 4px 0 0; }
figure img { display: block; width: 100%; height: auto; border: 1px solid var(--mist); border-radius: 12px; background: #fff; }
figcaption { font-size: 13px; line-height: 1.45; color: var(--muted); margin-top: 8px; }
.answers-wrap { overflow-x: auto; margin: 6px 0 18px; background: var(--card); border: 1px solid var(--mist); border-radius: 12px; }
.answers { border-collapse: collapse; width: 100%; min-width: 620px; font-size: 13.5px; font-variant-numeric: tabular-nums; }
.answers caption { text-align: left; font-weight: 600; color: var(--ink); padding: 10px 12px 4px; }
.answers th, .answers td { padding: 6px 8px; text-align: right; white-space: nowrap; border-top: 1px solid var(--mist); }
.answers thead th { border-top: none; font: 600 15px/1.2 var(--display); }
.answers th[scope="row"] { text-align: left; font-weight: 600; color: var(--ink); padding-left: 12px; }
.answers thead th.s { color: var(--coral-text); }
.answers thead th.c { color: var(--link); }
.answers td:last-child, .answers thead th:last-child { padding-right: 12px; }

/* literature */
.theme { border-top: 3px solid var(--signal); }
.theme .says { font: 600 19px/1.3 var(--display); color: var(--ink); margin: 6px 0 8px; }
.theme p { font-size: 14.5px; margin: 0; }
.gaplist { margin: 22px 0 0; padding: 0; list-style: none; display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.gaplist li { background: #fff6f1; border: 1px solid #f6d3c3; border-radius: 14px; padding: 16px; font-size: 14.5px; }
.gaplist b { display: block; color: var(--coral-text); font-family: var(--display); font-size: 17px; margin-bottom: 4px; }

/* technology */
.stack { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; }
.stack .card { padding: 16px; font-size: 14px; border-top: 3px solid var(--signal); }
.stack b { display: block; font: 600 16px/1.25 var(--display); color: var(--ink); margin-bottom: 4px; }
.notnow-title { font: 600 13px/1 var(--body); letter-spacing: .1em; text-transform: uppercase; color: var(--muted); margin: 26px 0 10px; }
.notnow { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.notnow div { font-size: 14px; color: var(--muted); border: 1px dashed #c3cedc; border-radius: 12px; padding: 12px 14px; }
.notnow b { color: var(--text); }

/* data quality and privacy */
.qa { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.qa .card { font-size: 14.5px; padding: 18px 20px; }
.qa h3 { font-size: 18px; }
.qa .ev { color: var(--muted); margin: 0 0 10px; }
.qa .how { margin: 0; padding-top: 10px; border-top: 1px dashed var(--mist); }
.qa .how b { color: var(--ink); }
.privacy { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.privacy li { background: var(--card); border: 1px solid var(--mist); border-left: 3px solid var(--signal); border-radius: 12px; padding: 14px 16px; font-size: 14.5px; }
.privacy b { display: block; font: 600 17px/1.25 var(--display); color: var(--ink); margin-bottom: 4px; }
.art { color: var(--muted); white-space: nowrap; }
.note { font-size: 14.5px; color: var(--muted); max-width: 820px; margin: 16px 0 0; }

/* next steps */
.next .card h3 { font-size: 20px; }
.next .card p { margin: 0; font-size: 15px; }

/* references */
.refs { list-style: none; margin: 0; padding: 0; font-size: 14px; max-width: 900px; }
.refs li { padding-left: 2em; text-indent: -2em; margin: 0 0 8px; overflow-wrap: anywhere; }
footer { margin: 72px 0 0; padding: 26px 0 40px; border-top: 1px solid var(--mist); color: var(--muted); font-size: 13.5px; }
footer p { margin: 0 0 6px; }

@media (max-width: 920px) {
  .hero .wrap { grid-template-columns: 1fr; gap: 40px; justify-items: center; }
  .hero-text { order: -1; }
  .grid3, .grid4, .facts, .gaplist, .stack, .notnow, .qa, .privacy { grid-template-columns: 1fr 1fr; }
  .pipe { grid-template-columns: 1fr; }
  .pipe div { border-radius: 0 !important; border-left: 1px solid var(--mist) !important; border-top: none; }
  .pipe div:first-child { border-radius: 14px 14px 0 0 !important; border-top: 1px solid var(--mist); }
  .pipe div:last-child { border-radius: 0 0 14px 14px !important; }
  .pipe div:not(:last-child)::after { display: none; }
  .finding { grid-template-columns: 1fr; gap: 12px; }
}
@media (max-width: 620px) {
  .phone { width: 100%; max-width: 330px; }
  .grid3, .grid4, .facts, .gaplist, .stack, .notnow, .qa, .privacy { grid-template-columns: 1fr; }
}
@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }
  * { transition: none !important; }
}

/* ---------- print / PDF ---------- */
@page { size: A4; margin: 12mm 12mm 13mm; }
@media print {
  * { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  html { scroll-behavior: auto; }
  body { background: #fff; font-size: 13px; line-height: 1.5; }
  .wrap { max-width: none; padding: 0; }
  .nav, .hero-cta { display: none; }
  .hero { border-radius: 14px; padding: 26px 26px 24px; }
  .hero .wrap { grid-template-columns: 236px 1fr; gap: 30px; justify-items: stretch; align-items: center; }
  .hero-text { order: 0; }
  .phone { width: 236px; border-radius: 36px; padding: 9px; box-shadow: none; }
  .screen { min-height: 462px; border-radius: 28px; padding: 16px 12px 14px; }
  .lock-date { font-size: 12px; margin-top: 8px; }
  .lock-clock { font-size: 62px; margin: 4px 0 14px; }
  .checkin { padding: 12px 11px 10px; border-radius: 16px; }
  .checkin .question { font-size: 15px; margin: 6px 0 9px; }
  .scale { gap: 5px; }
  .scale button { height: 32px; font-size: 14px; border-radius: 9px; }
  .scale-ends { font-size: 10.5px; }
  .answer { font-size: 11.5px; min-height: 0; margin-top: 10px; }
  .answer strong { font-size: 23px; }
  .hero-text .eyebrow { font-size: 10.5px; }
  .hero-text h1 { font-size: 34px; margin: 10px 0 12px; }
  .hero-text p { font-size: 13.5px; }
  .hero-fact { margin: 16px 0 6px; gap: 12px; }
  .hero-fact div { max-width: none; }
  .hero-fact b { font-size: 28px; }
  .hero-fact span { font-size: 11.5px; }
  .hero-meta { margin-top: 14px; padding-top: 10px; font-size: 11px; }
  section.block { padding: 18px 0 0; }
  #findings, #literature, #quality, #next { break-before: page; }
  h2 { font-size: 27px; margin: 6px 0 8px; break-after: avoid; }
  .kicker { break-after: avoid; }
  .lead { font-size: 14px; margin-bottom: 10px; }
  .subhead { font-size: 18px; margin: 18px 0 10px; }
  .gaplist { margin-top: 12px; }
  .notnow-title { margin: 14px 0 8px; break-after: avoid; }
  .grid3, .qa, .privacy { grid-template-columns: repeat(3, 1fr); gap: 10px; }
  .grid4, .gaplist, .facts, .notnow { grid-template-columns: repeat(4, 1fr); gap: 10px; }
  .stack { grid-template-columns: repeat(5, 1fr); gap: 8px; }
  .pipe { grid-template-columns: repeat(5, 1fr); }
  .pipe div { border-radius: 0 !important; border-left: none !important; border-top: 1px solid var(--mist); padding: 10px; }
  .pipe div:first-child { border-radius: 12px 0 0 12px !important; border-left: 1px solid var(--mist) !important; }
  .pipe div:last-child { border-radius: 0 12px 12px 0 !important; }
  .pipe div:not(:last-child)::after { display: block; }
  .pipe b { font-size: 13.5px; }
  .pipe span, .facts .card, .stack .card, .notnow div, .theme p, .gaplist li, .qa .card, .privacy li, .next .card p { font-size: 11.5px; }
  .card, .qa .card, .stack .card, .facts .card { padding: 11px 12px; border-radius: 12px; }
  .theme .says { font-size: 15px; }
  .gaplist b, .privacy b, .stack b { font-size: 14px; }
  .qa h3, .next .card h3 { font-size: 15px; }
  .finding { grid-template-columns: 1fr; gap: 6px; padding: 14px 0; break-inside: avoid; }
  .num { font-size: 40px; }
  .num-label { font-size: 12px; }
  .answers { min-width: 0; font-size: 11px; }
  figure img { max-height: 290px; width: auto; max-width: 100%; margin: 0 auto; }
  figcaption { font-size: 11px; }
  .card, .gaplist li, .privacy li, .notnow div, figure, .answers-wrap { break-inside: avoid; }
  .refs { font-size: 11.5px; }
  .refs li { margin-bottom: 5px; }
  footer { margin-top: 14px; padding: 8px 0 0; font-size: 11px; break-inside: avoid; }
  footer p { margin: 0 0 2px; }
}
</style>
</head>
<body>

<header class="hero">
  <div class="wrap">
    <div class="phone" aria-label="Illustration: a phone lock screen at 3:00 showing the AwareMind check-in question">
      <div class="screen">
        <div class="lock-date">Monday, 12 October</div>
        <div class="lock-clock">3:00</div>
        <div class="checkin">
          <div class="eyebrow">Quick check-in</div>
          <div class="question">I should <span class="blank" id="blank">…</span> using my phone now</div>
          <div class="scale" role="group" aria-label="Answer from 1 (stop) to 10 (continue)" id="scale"></div>
          <div class="scale-ends"><span>1 = stop</span><span>10 = continue</span></div>
          <div class="answer" id="answer" aria-live="polite"></div>
        </div>
      </div>
    </div>
    <div class="hero-text">
      <div class="eyebrow">NudgeWell · Group 6 · Interactive supplement</div>
      <h1>The gap between <em>“I&nbsp;should&nbsp;stop”</em> and actually stopping.</h1>
      <p>That gap is what NudgeWell predicts. The phone shows the real check-in question that 37 adults answered 5,772 times in the AwareMind study (Zheng &amp; Choe, 2026b). Choose an answer to see what people who gave it actually did next.</p>
      <div class="hero-fact">
        <div><b>14.9%</b><span>of all check-ins were high-gap moments: leaning “stop”, then over 5 more minutes of use</span></div>
        <div><b>33.7%</b><span>of check-ins between midnight and 6 am, against 12.6% from 9 am to 6 pm</span></div>
      </div>
      <a class="hero-cta" href="#findings">Explore the findings</a>
      <div class="hero-meta">Supplement to <b>NudgeWell: Literature, Data &amp; Technology Review</b> · Digital Addiction Capstone, Samsung Innovation Campus AI, Cohort 18, in partnership with Yeşilay · 12&nbsp;October&nbsp;2026<br><b>Group 6:</b> __MEMBERS__</div>
    </div>
  </div>
</header>

<nav class="nav" aria-label="Sections">
  <div class="wrap">
    <a href="#project">The project</a><a href="#findings">Findings</a><a href="#literature">Literature</a><a href="#technology">Technology</a>
    <a href="#quality">Data quality &amp; privacy</a><a href="#next">Next steps</a><a href="#references">References</a>
  </div>
</nav>

<main class="wrap">

<section class="block" id="project">
  <div class="kicker">NudgeWell in one minute</div>
  <h2>Predict the unwanted moment, then help once or stay quiet</h2>
  <div class="facts">
    <div class="card"><b>Problem</b>Time limits interrupt purposeful use and miss unwanted use.</div>
    <div class="card"><b>Target</b>The intention–behavior gap: the person says “stop”, then keeps going.</div>
    <div class="card"><b>For whom</b>Adults who use their phones heavily and want to cut down.</div>
    <div class="card"><b>Data</b>AwareMind: 5,772 check-ins from 37 US adults, July–October 2025.</div>
  </div>
  <div class="pipe" aria-label="How the planned prototype would work">
    <div><b>Phone use</b><span>Android usage events, read on the device</span></div>
    <div><b>Context</b><span>Time, app type, minutes in session, earlier sessions</span></div>
    <div><b>Gap model</b><span>Starts global, then learns the person</span></div>
    <div><b>Decide</b><span>Confident, with prompt budget left? Otherwise stay quiet</span></div>
    <div><b>One suggestion</b><span>From the user’s own list; dismissed with one tap</span></div>
  </div>
</section>

<section class="block" id="findings">
  <div class="kicker">What the data shows</div>
  <h2>Five things the AwareMind data shows</h2>
  <p class="lead">The analysis uses all 5,772 in-session check-ins from 37 US adults (Zheng &amp; Choe, 2026a). A <b>high-gap moment</b> means leaning toward “stop” (an answer below 5.5) and then using the phone for more than 5 more minutes. Figures are numbered as in the report.</p>

  <div class="finding">
    <div><div class="num gap">14.9%</div><div class="num-label">of check-ins were high-gap moments (859 of 5,772), matching the paper’s published figure exactly</div></div>
    <div>
      <div class="which">Report: Insight 1 · Figure 1</div>
      <p><b>Most check-ins lean toward continuing, but the gap is a substantial minority.</b> 72% of answers leaned toward continuing, and 29.4% were a firm 10. Further use was heavily skewed: a median of 5.1 minutes, while 5.2% of check-ins ran past an hour.</p>
      <p><span class="sup">Supplementary analysis</span><br>Leaning toward “stop” barely changed what happened next: __STOP5__% of those check-ins were followed by more than 5 more minutes of use, against __GO5__% when leaning toward “continue”. Only a firm 1 usually ended the session (__A1__%). After an answer of 3, the median further use was __A3MED__ minutes.</p>
      __TABLE__
      <figure><img src="__FIG1__" alt="Figure 1: distribution of intention ratings (28% leaned toward stopping) and of further phone use after answering (median 5.1 minutes)"><figcaption>__CAP1__</figcaption></figure>
    </div>
  </div>

  <div class="finding">
    <div><div class="num gap">33.7%</div><div class="num-label">high-gap share between midnight and 6 am (n = 395), against 12.6% from 9 am to 6 pm</div></div>
    <div>
      <div class="which">Report: Insight 2 · Figure 2</div>
      <p><b>The gap peaks at night</b>, reaching 45% at 3 am (n = 49, with a wide confidence interval). Weekends (15.4%) barely differ from weekdays (14.7%). This matches the finding that usage profiles with lower well-being are marked by night-time sessions (Katevas et al., 2018). Time of day is known before the outcome, so a real-time model can use it.</p>
      <figure><img src="__FIG2__" alt="Figure 2: high-gap share by hour of day, peaking between midnight and 6 am"><figcaption>__CAP2__</figcaption></figure>
    </div>
  </div>

  <div class="finding">
    <div><div class="num">23.7%</div><div class="num-label">high-gap share in social media apps (n = 908), against 10.6% in messaging</div></div>
    <div>
      <div class="which">Report: Insight 3 · Figure 3</div>
      <p><b>Social media carries the largest gap</b>, followed by media and video (18.4%) and browsers (16.2%). System tools are lowest (4.4%). This agrees with one sec users choosing to restrict social media most often (Haliburton et al., 2024). The app category is missing for 12.4% of check-ins.</p>
      <figure><img src="__FIG3__" alt="Figure 3: high-gap share by app category; social media highest"><figcaption>__CAP3__</figcaption></figure>
    </div>
  </div>

  <div class="finding">
    <div><div class="num">13% → 22%</div><div class="num-label">high-gap share from the first 30 seconds of a session to more than 10 minutes in</div></div>
    <div>
      <div class="which">Report: Insight 4 · Figure 4</div>
      <p><b>The gap grows as a session goes on</b> (13.4% → 21.6%), so elapsed time is a useful real-time signal. The participants are heavy users: at least 3.7 hours of screen time on the median participant-day, rising with age (3.0, 3.6 and 4.6 hours).</p>
      <figure><img src="__FIG4__" alt="Figure 4: daily screen time by age group, and high-gap share rising with minutes into the session"><figcaption>__CAP4__</figcaption></figure>
    </div>
  </div>

  <div class="finding">
    <div><div class="num">0.44</div><div class="num-label">intraclass correlation: about 44% of the gap’s variation lies between people</div></div>
    <div>
      <div class="which">Report: Insight 5 · Figure 5</div>
      <p><b>The gap is strongly person-specific.</b> Individual high-gap shares range from 0% to 97.2% (median 7.0%). This explains why one shared model barely works for new users (R² = .035; Zheng &amp; Choe, 2026b), and it makes personalization the core of NudgeWell.</p>
      <figure><img src="__FIG5__" alt="Figure 5: each participant's share of high-gap moments, from 0% to 97%"><figcaption>__CAP5__</figcaption></figure>
    </div>
  </div>
</section>

<section class="block" id="literature">
  <div class="kicker">What the literature says</div>
  <h2>14 studies, four themes, four gaps</h2>
  <p class="lead">Part 1 of the report reviews 14 studies in four themes. Each card gives a theme’s main takeaway; the coral cards are the gaps NudgeWell addresses.</p>
  <div class="grid4">
    <div class="card theme"><div class="kicker">Measurement</div><div class="says">Scales measure people, not moments</div><p>Self-reported use only moderately matches logged use (Parry et al., 2021). The SAS-SV scale has a validated Turkish version (Noyan et al., 2015).</p></div>
    <div class="card theme"><div class="kicker">Consequences</div><div class="says">Patterns matter more than minutes</div><p>In 10,099 US adults, objectively measured use showed weak or null links with mood (Winbush et al., 2025). Lower-well-being profiles were marked by night-time use (Katevas et al., 2018).</p></div>
    <div class="card theme"><div class="kicker">Interventions</div><div class="says">Brief nudges work, then fade</div><p>Short frictions made app openings more intentional for 1,039 <i>one sec</i> users, who then took breaks and rebounded (Haliburton et al., 2024). <i>TypeOut</i> cut app usage by more than half (Xu et al., 2022).</p></div>
    <div class="card theme"><div class="kicker">AI</div><div class="says">Models find problem users, not moments</div><p><i>Time2Stop</i> learns when to intervene (Orzikulova et al., 2024). Only AwareMind predicts the gap itself, and its model barely works for new users (Zheng &amp; Choe, 2026b).</p></div>
  </div>
  <ul class="gaplist" aria-label="Research gaps">
    <li><b>Measurement</b>Only one dataset captures the momentary clash between intention and behaviour.</li>
    <li><b>Prediction</b>The gap has only been modelled with random forests: no sequence models and no systematic personalization.</li>
    <li><b>Intervention</b>Just-in-time systems decide <i>when</i> to interrupt, not whether the person wants to stop.</li>
    <li><b>Population</b>There is no momentary data from Turkey, or from outside the US, Europe and East Asia.</li>
  </ul>
</section>

<section class="block" id="technology">
  <div class="kicker">Technology choices</div>
  <h2>A deliberately modest stack</h2>
  <p class="lead">Part 3 of the report compares sensing APIs, models and deployment options. These are the choices it makes.</p>
  <div class="stack">
    <div class="card"><b>Android usage access</b><code>UsageStatsManager</code> (Android Developers, n.d.). Events are kept for only a few days, so the app stores its own minimal history.</div>
    <div class="card"><b>Baselines</b>A random forest, as in the paper, plus gradient-boosted trees (XGBoost).</div>
    <div class="card"><b>Temporal model</b>A compact TCN or GRU over recent sessions.</div>
    <div class="card"><b>Personal and explainable</b>Global, personal and combined variants, with calibration, a daily prompt budget and SHAP explanations (Lundberg &amp; Lee, 2017).</div>
    <div class="card"><b>On the phone</b>LiteRT or ONNX Runtime (Google AI Edge, n.d.; ONNX Runtime, n.d.), inside the existing Kotlin/Compose Eşik app.</div>
  </div>
  <div class="notnow-title">Ruled out for now</div>
  <div class="notnow">
    <div><b>AccessibilityService:</b> richer data, but it needs Play Store disclosure and approval, and it is weaker on privacy.</div>
    <div><b>iOS Screen Time APIs:</b> built around parental controls, with no raw logs for custom models.</div>
    <div><b>Transformers:</b> they typically need far more data than 5,772 labelled moments.</div>
    <div><b>Cloud inference:</b> easier to update, but it sends behavioural data off the phone.</div>
  </div>
</section>

<section class="block" id="quality">
  <div class="kicker">Data quality and privacy</div>
  <h2>Known limits, and how we handle them</h2>
  <p class="lead">From Part 2 of the report (Table 4 and Section 2.4).</p>
  <div class="qa">
    <div class="card"><h3>Target leakage</h3><p class="ev"><code>answer</code>, the <code>remaining_*</code> columns, <code>lock_time</code> and the undocumented <code>temp_scaled</code> (a rescaled copy of the outcome) all reveal the target.</p><p class="how"><b>Handling:</b> excluded; features use only what is known at the check-in.</p></div>
    <div class="card"><h3>Class imbalance</h3><p class="ev">High-gap moments are 14.9% of check-ins.</p><p class="how"><b>Handling:</b> precision–recall AUC and F1, class weights and a tuned threshold; never accuracy alone.</p></div>
    <div class="card"><h3>Self-report bias</h3><p class="ev">11 participants answered 10 to more than half of their prompts (up to 89%).</p><p class="how"><b>Handling:</b> per-person standardization, personal models, and a sensitivity analysis without near-constant raters.</p></div>
    <div class="card"><h3>Missing app information</h3><p class="ev">12.4% of check-ins (717) lack the app category; activity is missing for 2.3%.</p><p class="how"><b>Handling:</b> explicit “not recorded” categories with missingness flags; nothing is dropped silently.</p></div>
    <div class="card"><h3>Repeated measures</h3><p class="ev">72–294 check-ins per person; 5,549 sessions, 204 of them with more than one check-in.</p><p class="how"><b>Handling:</b> leave-one-participant-out splits for new users; chronological splits within each person.</p></div>
    <div class="card"><h3>Small, US-only sample</h3><p class="ev">37 adults in five US time zones. Group differences, such as women 19.7% against men 8.1%, rest on 22 and 15 people.</p><p class="how"><b>Handling:</b> confidence intervals, per-person results, and explicit limits on transfer to Turkish users.</p></div>
  </div>

  <h3 class="subhead">Privacy by design under KVKK (Law No. 6698, 2016)</h3>
  <ul class="privacy">
    <li><b>Explicit opt-in consent</b>Before any processing, in plain language <span class="art">(Art. 5)</span>. An inferred “problematic use” state may count as health data, a special category <span class="art">(Art. 6)</span>.</li>
    <li><b>Minimal data</b>App categories and session timing only: no message or keystroke content and no screen captures <span class="art">(Art. 4)</span>.</li>
    <li><b>On the device</b>Processing and storage stay on the phone: no account, no advertising use, no sale of data <span class="art">(Art. 12)</span>.</li>
    <li><b>User control</b>View, correct, export or delete the data; pause the app or withdraw at any time <span class="art">(Art. 11)</span>.</li>
    <li><b>Adults only</b>Minors are outside the target group; including them would need parental consent and a separate ethics review.</li>
    <li><b>Real help, not therapy</b>Crisis-related language leads to Yeşilay YEDAM and the 115 line, never to generated advice.</li>
  </ul>
  <p class="note">For AwareMind itself, we report only aggregated results, show no participant codes, keep the raw files local, and use the data for coursework analysis only. OSF lists no licence for the data, so we will obtain written permission from the authors before model training or publication.</p>
</section>

<section class="block next" id="next">
  <div class="kicker">What comes next</div>
  <h2>From review to concept note</h2>
  <div class="grid3">
    <div class="card"><h3>Model</h3><p>Benchmark compact temporal and personalized models of the gap against the published random forest, and report negative results honestly.</p></div>
    <div class="card"><h3>Evaluation</h3><p>Leakage-safe splits: leave-one-participant-out for new users, and chronological splits within each person to test personalization.</p></div>
    <div class="card"><h3>Prototype</h3><p>An opt-in Android prototype built on the Eşik app: quiet by default, a daily prompt budget, and one suggestion from the user’s own list.</p></div>
  </div>
</section>

<section class="block" id="references">
  <div class="kicker">Sources</div>
  <h2>References</h2>
  <ul class="refs">
__REFS__
  </ul>
</section>

<footer>
  <p>NudgeWell · Group 6: __MEMBERS_AND__.</p>
  <p>Interactive supplement to the Literature, Data &amp; Technology Review, 12&nbsp;October&nbsp;2026. Statistics and figures come from the same analysis notebook as Part 2 of the report; AwareMind data are used for coursework analysis only and shown in aggregate.</p>
</footer>
</main>

<script>
const ANSWERS = __ANSWERS__;
const scale = document.getElementById("scale");
const answer = document.getElementById("answer");
const blank = document.getElementById("blank");
function describe(d) {
  const pct = d.over5.toFixed(1), med = d.med.toFixed(1);
  const lead = `Of the ${d.n.toLocaleString("en-US")} check-ins answered ${d.a}`;
  if (d.a === 1) return `<strong class="go-num">${pct}%</strong>${lead}, only ${pct}% were followed by over 5 more minutes of use (median ${med} min). A firm “stop” usually worked.`;
  if (d.a <= 5) return `<strong class="stop-num">${pct}%</strong>${lead}, ${pct}% were still followed by over 5 more minutes of use (median ${med} min). That is the gap.`;
  return `<strong class="go-num">${pct}%</strong>${lead}, ${pct}% were followed by over 5 more minutes of use (median ${med} min), in line with the stated intention.`;
}
function select(a) {
  const d = ANSWERS[a - 1];
  scale.querySelectorAll("button").forEach(b => b.setAttribute("aria-pressed", String(+b.dataset.a === a)));
  blank.textContent = a <= 5 ? "stop" : "continue";
  answer.innerHTML = describe(d);
}
ANSWERS.forEach(d => {
  const b = document.createElement("button");
  b.type = "button";
  b.textContent = d.a;
  b.dataset.a = d.a;
  b.className = d.a <= 5 ? "stop" : "go";
  b.setAttribute("aria-label", `Answer ${d.a}`);
  b.addEventListener("click", () => select(d.a));
  scale.appendChild(b);
});
select(3);
</script>
</body>
</html>
"""


def build_html():
    caps = {}
    for m in re.finditer(r"^!\[(Figure (\d)\. .+?)\]\(\.\./figures/(.+?)\)$", REPORT, flags=re.M):
        caps[int(m.group(2))] = (html.escape(m.group(1)), m.group(3))
    assert sorted(caps) == [1, 2, 3, 4, 5], caps.keys()
    rows = {r["answer"]: r for r in ROWS}
    NBSP = [m.replace(" ", "&nbsp;") for m in MEMBERS]  # never break inside a name
    page = (TEMPLATE
            .replace("__MEMBERS_AND__", ", ".join(NBSP[:-1]) + " and " + NBSP[-1])
            .replace("__MEMBERS__", " · ".join(NBSP))
            .replace("__STOP5__", f'{BA["stop_leaning_over5_pct"]:.1f}')
            .replace("__GO5__", f'{BA["continue_leaning_over5_pct"]:.1f}')
            .replace("__A1__", f'{rows[1]["over5_pct"]:.1f}')
            .replace("__A3MED__", f'{rows[3]["median_min"]:.0f}')
            .replace("__TABLE__", answer_table())
            .replace("__REFS__", "\n".join(f"    <li>{reference(k)}</li>" for k in REF_KEYS))
            .replace("__ANSWERS__", json.dumps(ANSWERS)))
    for n, (cap, file) in caps.items():
        page = page.replace(f"__CAP{n}__", cap).replace(f"__FIG{n}__", img(file))
    leftover = re.findall(r"__[A-Z0-9_]+__", page)
    assert not leftover, leftover
    OUT_HTML.write_text(page, encoding="utf-8")
    print("wrote", OUT_HTML, f"{OUT_HTML.stat().st_size / 1024:.0f} KB")


def build_pdf():
    roots = [os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"), os.environ.get("ProgramFiles", r"C:\Program Files")]
    edge = next((Path(r) / "Microsoft/Edge/Application/msedge.exe" for r in roots
                 if (Path(r) / "Microsoft/Edge/Application/msedge.exe").exists()), None)
    if edge is None:
        sys.exit("Microsoft Edge not found: open the HTML in a browser and print it to PDF instead.")
    # A throwaway profile keeps this separate from any Edge window that is already open.
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as profile:
        subprocess.run([str(edge), "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
                        f"--user-data-dir={profile}", "--no-pdf-header-footer", "--virtual-time-budget=10000",
                        f"--print-to-pdf={OUT_PDF}", OUT_HTML.as_uri()],
                       check=True, timeout=180, capture_output=True)
    print("wrote", OUT_PDF, f"{OUT_PDF.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    build_html()
    if "--pdf" in sys.argv:
        build_pdf()
