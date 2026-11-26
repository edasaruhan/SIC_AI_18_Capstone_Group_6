import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const scratch = path.join(root, "run", "final-package-qa");
const skill = process.env.NUDGEWELL_PRESENTATION_SKILL;
const modules = process.env.NUDGEWELL_RUNTIME_MODULES;
const python = process.env.NUDGEWELL_RUNTIME_PYTHON;
process.env.RUNTIME_NODE_MODULES ??= modules;
const { Presentation, PresentationFile } = await import(
  pathToFileURL(path.join(modules, "@oai/artifact-tool/dist/artifact_tool.mjs")).href
);
const { finalizePresentation } = await import(
  pathToFileURL(path.join(skill, "container_tools/artifact_tool_utils.mjs")).href
);
const read = async (file) => JSON.parse(await fs.readFile(file, "utf8"));
const hw6 = await read(path.join(root, "build/results/hw6_local_evidence.json"));
const replay = await read(path.join(root, "build/results/hw6_policy_replay.json"));
const hw5 = await read(path.join(root, "../05_model_refinement_test_submission/build/results",
  "hw5-v1-step5-20261117_evaluation.json"));
const presentation = Presentation.create({ slideSize: { width: 1280, height: 720 } });

const ink = "#15302A";
const pale = "#F5F3EC";
const olive = "#557366";
const line = "#CAD2C6";
const rust = "#922F36";
const mint = "#D3E8D7";
const fontFamily = "Arial";
const hw5Source = "https://github.com/edasaruhan/SIC_AI_18_Capstone_Group_6/blob/cff439ecb7574529e6735c71c307722e438edad8/deliverables/05_model_refinement_test_submission/build/evaluation_review.md";

function block(slide, name, x, y, width, height, fill, geometry = "rect") {
  return slide.shapes.add({
    name, geometry, fill, position: { left: x, top: y, width, height },
    line: { fill: "none", width: 0 },
  });
}

function text(slide, name, value, x, y, width, height, { size = 28, bold = false, color = ink, align = "left" } = {}) {
  const box = block(slide, name, x, y, width, height, "none", "textbox");
  box.text = value;
  box.text.style = {
    fontFamily, fontSize: size, bold, color, alignment: align, verticalAlignment: "middle",
    insets: { left: 0, right: 0, top: 0, bottom: 0 },
  };
}

function slide(title, notes) {
  const page = presentation.slides.add();
  page.background.fill = pale;
  text(page, "Title", title, 78, 53, 1130, 97, { size: 49, bold: true });
  block(page, "Title rule", 78, 158, 1124, 2, line);
  page.speakerNotes.text = notes;
  return page;
}

function footer(page, value) {
  text(page, "Source or scope", value, 78, 649, 1120, 42, { size: 19, color: olive });
}

{
  const page = presentation.slides.add();
  page.background.fill = ink;
  block(page, "Vertical rule", 82, 84, 4, 516, mint);
  text(page, "Project", "NudgeWell", 115, 121, 1030, 101, { size: 83, bold: true, color: "#FFFFFF" });
  text(page, "Focus", "Predicting high-gap phone check-ins", 120, 238, 1020, 72, { size: 43, color: mint });
  text(page, "Course and team", "Samsung Innovation Campus  /  Group 6", 120, 481, 1010, 41,
    { size: 25, bold: true, color: "#FFFFFF" });
  text(page, "Showcase scope", "Desktop deployment and an earlier phone interaction prototype", 120, 533, 1030, 51,
    { size: 25, color: mint });
  page.speakerNotes.text = "0:00. A high-gap check-in is an answer of 5 or lower followed by more than five minutes of additional phone use. Group 6 evaluates prediction from signals available at the check-in. Source: HW5 report pp. 1 and 3. " + hw5Source;
}

{
  const page = slide("What the HW5 evaluation found",
    "0:20. Explain that average precision summarizes ranking and Brier loss summarizes probability error. The paired AP interval crosses zero. The Brier gain is against a personal rate and does not establish better within-day ordering. " + hw5Source);
  const refined = hw5.new_user.refined_selector.participant_balanced_AP.toFixed(4);
  const baseline = hw5.new_user.fixed_baseline_selector.participant_balanced_AP.toFixed(4);
  const brier = hw5.secondary_prespecified_contrast.point_difference.toFixed(5);
  block(page, "Column separator", 650, 211, 2, 345, line);
  text(page, "Ranking heading", "New-user ranking", 78, 212, 535, 51, { size: 31, bold: true });
  text(page, "Average precision values", refined + " vs " + baseline, 78, 274, 535, 75, { size: 55, bold: true });
  text(page, "Average precision metric", "Participant-balanced AP", 78, 352, 535, 40, { size: 25, color: olive });
  text(page, "Ranking conclusion", "No clear refinement gain.\nPaired 95% interval −0.0652 to +0.0222.", 78, 424, 546, 100, { size: 27 });
  text(page, "Personalization heading", "Personal probability accuracy", 690, 212, 510, 51, { size: 31, bold: true });
  text(page, "Brier change", brier, 690, 274, 510, 75, { size: 55, bold: true });
  text(page, "Brier metric", "Lower Brier loss with the daily offset", 690, 352, 510, 45, { size: 25, color: olive });
  text(page, "Personalization conclusion", "Small gain over a personal base rate.\nWithin-day ordering was unchanged.", 690, 424, 510, 100, { size: 27 });
  footer(page, "Retrospective evaluation · 5,627 unique check-ins from 37 adults · HW5 report, pp. 4–5");
}

{
  const page = slide("Two test requests through the desktop API",
    "0:45. Run the synthetic launcher. Point to readiness and the synthetic model version. Show the below-cutoff and above-cutoff responses, and end on aggregate counters. Source: HW6 synthetic rehearsals and code/nudgewell_hw6/demo.py.");
  text(page, "Input definition", "Local hour, weekday (Monday = 0), elapsed session minutes", 78, 188, 1124, 59, { size: 28 });
  const variants = [
    ["(0, 0, 0)", "0.3100", "Candidate flag false", 78],
    ["(9, 1, 2)", "0.4123", "Candidate flag true", 690],
  ];
  for (const [request, score, flag, x] of variants) {
    text(page, request, request, x, 275, 510, 54, { size: 30, color: olive });
    text(page, score, score, x, 330, 510, 89, { size: 69, bold: true });
    text(page, flag, flag, x, 439, 510, 55, { size: 32, bold: true });
  }
  block(page, "Score column separator", 650, 285, 2, 239, line);
  text(page, "Fixture name", "hw6-synthetic-fixture-v1  ·  cutoff 0.35", 78, 557, 1124, 55, { size: 27, bold: true });
  footer(page, "Fixture scores use hand-set parameters. HW6 research performance comes from the separate saved evaluation.");
}

{
  const page = slide("A cap and cooldown limit delivery",
    "2:15. This is an illustrative timeline for the planned policy. Every time shown starts with a candidate flag. Deliveries at 09:00, 09:30 and 10:00 exhaust the day’s cap. Source: HW3 concept note §4.5 and HW6 policy replay.");
  text(page, "Policy", "Up to three prompts per day  ·  at least 30 minutes between deliveries", 78, 199, 1124, 55, { size: 29 });
  block(page, "Timeline", 181, 364, 918, 3, line);
  const times = [
    ["09:00", "Delivery 1", ink],
    ["09:10", "Cooldown", rust],
    ["09:30", "Delivery 2", ink],
    ["10:00", "Delivery 3", ink],
    ["10:30", "Daily cap", rust],
  ];
  for (const [index, [stamp, outcome, color]] of times.entries()) {
    const center = 181 + index * 229.5;
    block(page, stamp + " marker", center - 9, 356, 18, 18, color, "ellipse");
    text(page, stamp, stamp, center - 100, 298, 200, 48, { size: 32, bold: true, align: "center" });
    text(page, outcome + " at " + stamp, outcome, center - 100, 397, 200, 49, { size: 28, color, align: "center" });
  }
  footer(page, "Illustrative policy timeline. HW6 serves the candidate decision.");
}

{
  const page = slide("Eşik illustrates the phone interaction",
    "3:00. Introduce Eşik as the earlier threshold-triggered Android prototype. Run the keyless CI build offline with scripted inputs, or use this diagram if a verified phone rehearsal is unavailable. Source: Eşik repository README and AI_DEVICE_QA.md. https://github.com/Thynatos/esik-android");
  const steps = [
    ["01", "Limit reached", "The phone observes a\nuser-set daily app limit."],
    ["02", "Offer shown", "Eşik suggests a brief\nalternative activity."],
    ["03", "User decides", "The user can dismiss\nthe prompt in one tap."],
  ];
  for (const [index, [number, heading, detail]] of steps.entries()) {
    const x = 78 + index * 383;
    block(page, "Step line " + number, x, 259, 334, 3, line);
    text(page, "Step " + number, number, x, 279, 330, 48, { size: 24, color: olive });
    text(page, heading, heading, x, 346, 334, 49, { size: 34, bold: true });
    text(page, detail.split("\n")[0], detail, x, 414, 350, 104, { size: 26 });
  }
  footer(page, "Earlier Eşik prototype · fixed daily threshold · separate from the NudgeWell desktop model");
}

{
  const page = slide("What remains before a pilot",
    "4:15. The desktop research package supports a coursework submission and a separate interaction demonstration. Real use requires authorization and prospective evaluation. Source: HW3 objectives, HW6 report, showcase/O1-O6_Status.pdf and showcase/POLICY_REPLAY.md.");
  const items = [
    ["Data-use permission", "Document which activities the data owner authorizes."],
    ["Phone verification", "Verify offline sensing, scoring, prompt controls and full deletion."],
    ["Prospective comparison", "Measure helpfulness, unwanted interruptions and behavior separately."],
  ];
  for (const [index, [heading, detail]] of items.entries()) {
    const top = 221 + index * 119;
    text(page, heading, heading, 78, top, 412, 63, { size: 31, bold: true });
    text(page, detail, detail, 505, top, 693, 63, { size: 28 });
    block(page, "Divider " + index, 78, top + 83, 1122, 1, line);
  }
  footer(page, "Group 6 · Samsung Innovation Campus");
}

{
  const page = slide("Verification and policy replay",
    "Backup for questions. The benchmark ran on Windows loopback with 30 warmups and 200 timed synthetic HTTP requests against the fitted fold-zero bundle. The replay covers historical sampled check-ins and uses each policy’s frozen candidate flags. Sources: build/results/hw6_local_evidence.json and build/results/hw6_policy_replay.json.");
  const fitted = replay.methods.refined_fixed_cutoffs;
  const rule = replay.methods.fixed_three_signal_rule;
  const lat = hw6.serving;
  text(page, "Benchmark heading", "HW6 desktop export", 78, 200, 500, 60, { size: 33, bold: true });
  text(page, "Parity result", "1,320 held-out check-ins\n0 candidate-flag disagreements", 78, 279, 520, 99, { size: 29 });
  text(page, "Latencies", lat.latency_p50_ms.toFixed(2) + " ms median\n" + lat.latency_p95_ms.toFixed(2) + " ms p95", 78, 415, 520, 99, { size: 33, bold: true });
  block(page, "Evidence column separator", 650, 214, 2, 339, line);
  text(page, "Replay heading", "Historical policy replay", 690, 200, 510, 60, { size: 33, bold: true });
  text(page, "Replay setting", "Same cap and cooldown · 638 participant-days", 690, 265, 510, 52, { size: 23 });
  text(page, "Policy column", "Policy", 690, 339, 115, 37, { size: 21, color: olive });
  text(page, "Delivery column", "Deliveries", 835, 339, 147, 37, { size: 21, color: olive });
  text(page, "Positives column", "Positives reached", 1010, 339, 188, 37, { size: 21, color: olive });
  block(page, "Replay table rule", 690, 380, 505, 1, line);
  for (const [index, [label, method]] of [["Model", fitted], ["Fixed rule", rule]].entries()) {
    const y = 394 + index * 60;
    text(page, label, label, 690, y, 138, 46, { size: 26, bold: true });
    text(page, label + " deliveries", String(method.delivered_prompts), 835, y, 147, 46, { size: 28, bold: true });
    text(page, label + " positives", String(method.positive_labels_reached), 1010, y, 188, 46, { size: 28, bold: true });
  }
  footer(page, "Windows loopback timings · replay counts are simulated deliveries on sampled check-ins");
}

await fs.mkdir(scratch, { recursive: true });
for (const [index, page] of presentation.slides.items.entries()) {
  const png = await presentation.export({ slide: page, format: "png", scale: 1 });
  await fs.writeFile(path.join(scratch, "showcase-" + (index + 1) + ".png"), new Uint8Array(await png.arrayBuffer()));
}
const staging = await fs.mkdtemp(path.join(scratch, "showcase-build-"));
const candidate = path.join(staging, "NudgeWell_Showcase.draft.pptx");
await (await PresentationFile.exportPptx(presentation)).save(candidate);
const finalDir = path.join(staging, "verified");
await fs.mkdir(finalDir);
const verified = path.join(finalDir, "NudgeWell_Showcase.pptx");
const output = path.join(root, "showcase", "NudgeWell_Showcase.pptx");
await finalizePresentation({
  workspaceDir: root,
  candidatePath: candidate,
  finalPath: verified,
  pythonExecutable: python,
  integrityValidatorPath: path.join(skill, "container_tools/inspect_presentation_package_integrity.py"),
  layoutValidatorPath: path.join(skill, "container_tools/inspect_presentation_layout_geometry.py"),
  layoutArgs: ["--expected-slide-size-emu", "12192000,6858000"],
  explicitTotalSlideCount: 7,
  fontPolicy: { basis: "design", families: [fontFamily] },
  verifyArtifactToolImport: true,
  receiptPath: path.join(staging, "showcase.validation.json"),
});
await fs.copyFile(verified, output);
console.log(output);

