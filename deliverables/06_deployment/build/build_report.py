"""Fill the instructor's Deployment template with the verified HW6 evidence."""

import argparse
import json
from pathlib import Path
import sys

HW6 = Path(__file__).resolve().parents[1]
HW5 = HW6.parent / "05_model_refinement_test_submission"
sys.path.insert(0, str(HW5 / "build"))

from build_hw5_report import Report, add_link, sha256


def build_report(template):
    source = HW6 / "build" / "results" / "hw6_local_evidence.json"
    evidence = json.loads(source.read_bytes())
    export = evidence["export"]
    serving = evidence["serving"]
    host = evidence["environment"]
    monitor = serving["monitoring"]
    hw5_results = HW5 / "build" / "results" / f"{export['source_run']}_evaluation.json"
    if (evidence["status"] != "verified_local_prototype"
            or evidence["synthetic_tests_passed"] <= 0
            or export["disagreeing_alert_flags"] != 0
            or export["max_probability_difference"] > export["probability_tolerance"]
            or sha256(hw5_results) != export["hw5_evaluation_sha256"]
            or any(sha256(HW6 / file) != digest for file, digest in evidence["code_sha256"].items())):
        raise ValueError("The report requires current HW6 verification and its matching HW5 evaluation.")
    hw5 = json.loads(hw5_results.read_bytes())
    refined = hw5["new_user"]["refined_selector"]["participant_balanced_AP"]
    baseline = hw5["new_user"]["fixed_baseline_selector"]["participant_balanced_AP"]
    brier_gain = hw5["secondary_prespecified_contrast"]["point_difference"]

    report = Report(template)
    props = report.doc.core_properties
    props.title = "NudgeWell Deployment"
    props.subject = "Samsung Innovation Campus AI Capstone Homework 6"
    footer = report.doc.sections[0].footer.paragraphs[0]
    footer.runs[0].text = "NudgeWell   |   HW6   |   "
    p, h, table = report.p, report.h, report.table

    h("Machine Learning Project Documentation")
    h("Deployment")
    p("NudgeWell · Samsung Innovation Campus AI Capstone · Homework 6", "Report subtitle")
    p("Group 6 · Yusuf Ersel Kara, Bahadır Maral, Çağla Eryılmaz,\n"
      "Fatih Mehmet Menteşe and Damla Nur Öcal", "Report subtitle")
    h("1. Overview")
    p("NudgeWell evaluates high-gap prediction on previously collected check-ins and serves a "
      "verified reference model on desktop. A high-gap check-in combines a survey answer of 5 or "
      "lower with more than five minutes of further phone use.")
    p(f"HW5 evaluated five held-out participant folds. Participant-balanced average precision "
      f"was {refined:.4f} for the refined procedure and {baseline:.4f} for the fixed baseline. "
      f"The paired interval crossed zero. The separate daily adjustment reduced Brier loss by "
      f"{brier_gain:.5f} compared with the personal base rate. This deployment prototype uses "
      "only the global procedure from the first saved fold. We chose it by fold order and reused "
      "its fitted model and validation cutoff.")

    h("2. Model Serialization")
    p("The source checkpoint is a trusted local HW5 joblib file. We checked its hash against "
      "the run manifest and verified the data, protocol, and source fingerprints. The export puts "
      "median imputation, scaling, logistic regression, and clipped sigmoid calibration into one "
      "ONNX graph. The API constructs the same five ordered features from local hour, weekday, "
      "and elapsed session time. The companion manifest records that order, the cutoff, and the model digest.")
    table("Export and parity evidence", ["Check", "Verified result"], [
        ("Graph format", f"ONNX opset {export['onnx_opset']}, float64"),
        ("ONNX file size", f"{export['onnx_bytes']:,} bytes"),
        ("Held-out check-ins", f"{export['held_out_rows']:,} across {export['held_out_participants']} participants"),
        ("Maximum probability difference", f"{export['max_probability_difference']:.3g} (limit {export['probability_tolerance']:.0e})"),
        ("Candidate-alert disagreements", f"{export['disagreeing_alert_flags']} at cutoff {export['validation_cutoff']:.6f}"),
        ("Synthetic tests", f"{evidence['synthetic_tests_passed']} passed"),
    ], [2.6, 3.6])
    p("The export agrees with the original Python procedure and its saved HW5 predictions on the "
      "same held-out rows. This verifies serialization for the selected fold.", "Report note")

    h("3. Model Serving", new_page=True)
    p("FastAPI serves the ONNX model through Uvicorn, bound to 127.0.0.1. At startup the service "
      "loads the verified graph into one ONNX Runtime session on the CPU, with one intra-operator "
      "and one inter-operator thread. The showcase can use the same endpoints with a separately "
      "versioned synthetic fixture. Eşik, an earlier Android prototype, illustrates the phone "
      "interaction separately. NudgeWell device integration remains future work.")
    p(f"On {host['os']} ({host['platform']}) with ONNX Runtime {host['packages']['onnxruntime']}, "
      f"we timed {serving['timed_requests']} sequential synthetic HTTP requests after "
      f"{serving['warmup_requests']} warmups. Median latency was {serving['latency_p50_ms']:.2f} ms "
      f"and p95 was {serving['latency_p95_ms']:.2f} ms. The timing includes loopback HTTP, "
      "validation, feature construction, scoring, and response serialization. Phone latency and "
      "the effect of delivering nudges remain future tests.")

    h("4. API Integration")
    table("Local interface", ["Endpoint", "Response"], [
        ("GET /health", "Readiness. HTTP 503 if the bundle is unavailable."),
        ("POST /v1/predict", "Version, calibrated probability, and candidate-alert flag."),
        ("GET /metrics", "Aggregate request, error, latency, and alert diagnostics."),
    ], [2.15, 4.15])
    p("Prediction and metrics requests require X-API-Key. The prediction body takes integer "
      "local_hour (0–23) and local_weekday (0–6, Monday first), and a finite, nonnegative "
      "elapsed_minutes value. The candidate flag is true at or above the saved inner-validation cutoff.")
    p("Synthetic input scored by the HW5 export", "Report subheading")
    for title, value in (("Request", serving["synthetic_request"]), ("Response", serving["synthetic_response"])):
        report.caption(title, keep_next=True)
        lines = json.dumps(value, indent=2).splitlines()
        for i, line in enumerate(lines):
            paragraph = p(line, "Code excerpt")
            paragraph.paragraph_format.keep_with_next = i < len(lines) - 1
    p("Missing or wrong credentials return 401. Missing, extra, or invalid inputs return 422. "
      "A missing or unusable model returns 503.", "Report note")

    h("5. Security Considerations", new_page=True)
    p("The local service reads a user-generated key from the environment and uses constant-time "
      "comparison. Access logging is disabled. Clients send three coarse time/session fields. "
      "The service rejects extra fields and returns generic validation errors. It keeps neither "
      "request bodies nor individual scores in its logs.")
    p("Readiness checks the ONNX digest against the local manifest, verifies the saved cutoff "
      "against graph metadata, and runs a synthetic inference. Missing or altered files fail "
      "readiness. The digest relies on a trusted local bundle. A release would also need trusted "
      "artifact distribution, device validation, and written permission before publishing or "
      "deploying a model fitted on the AwareMind data.")

    h("6. Monitoring and Logging")
    p("The metrics endpoint summarizes prediction requests by HTTP status and tracks the cumulative "
      "share of successful requests that cross the threshold. It reports p95 service latency for "
      "up to 500 recent successful requests. The process stores this information in memory and "
      "resets it at restart. HTTP 503 from the health endpoint signals startup or artifact failure.")
    table("Monitoring observed during the synthetic smoke test and benchmark", ["Metric", "Observed value"], [
        ("Prediction requests", monitor["prediction_requests"]),
        ("Successful requests", monitor["successful_predictions"]),
        ("Unauthorized / invalid", f"{monitor['prediction_status_counts']['401']} / {monitor['prediction_status_counts']['422']}"),
        ("Candidate-alert share", f"{monitor['candidate_alert_rate']:.1%}"),
        ("p95 service time", f"{monitor['p95_success_ms']:.2f} ms over {monitor['latency_window_size']} successful requests"),
    ], [2.75, 3.55])
    p("These requests validate the counters. Their candidate-alert share describes the synthetic "
      "input generator. Measuring delivered alerts, user responses, and changes in behavior "
      "requires a separate device study.")
    h("Evidence and reproduction", template_heading=False)
    sources = [
        ("HW5 frozen evaluation", "https://github.com/edasaruhan/SIC_AI_18_Capstone_Group_6/blob/main/deliverables/05_model_refinement_test_submission/build/evaluation_review.md"),
        ("HW6 aggregate verification and benchmark", "build/results/hw6_local_evidence.json"),
        ("HW6 reproduction commands", "README.md"),
        ("Showcase and project status", "showcase/SUBMISSION.md"),
    ]
    for name, path in sources:
        add_link(p("", "Report note"), name, path)

    if report.headings:
        raise ValueError("The supplied template includes additional unfilled headings.")
    output = HW6 / "NudgeWell_Group6_HW6_Deployment.docx"
    report.doc.save(output)
    print(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, required=True)
    build_report(parser.parse_args().template)
