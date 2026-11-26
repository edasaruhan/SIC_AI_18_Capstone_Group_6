# Homework 6 Deployment

NudgeWell · Group 6 · Samsung Innovation Campus

[PDF report](NudgeWell_Group6_HW6_Deployment.pdf) · [Word report](NudgeWell_Group6_HW6_Deployment.docx) · [Aggregate verification and benchmark](build/results/hw6_local_evidence.json) · [Frozen HW5 evaluation](../05_model_refinement_test_submission/build/evaluation_review.md)

HW6 exports the first saved outer-fold procedure from HW5. It keeps the trained preprocessing, logistic classifier, sigmoid calibration, and validation cutoff together. The checks compare the ONNX export with the saved Python procedure on the same held-out rows. A separate synthetic benchmark exercises the HTTP interface over loopback.

## Reproduce

Use Python 3.11.9 and the trusted local HW5 run `hw5-v1-step5-20261117`, along with the original release CSV and dictionaries. Start in the Git repository root. Install [the pinned dependencies](requirements.txt) in a dedicated environment. The report builder also uses the original instructor template. The PDF export uses Microsoft Word on Windows.

```powershell
$hw6 = 'deliverables/06_deployment'
$hw6Env = Join-Path $env:LOCALAPPDATA 'nudgewell-hw6'
py -3.11 -m venv $hw6Env
$hw6Python = Join-Path $hw6Env 'Scripts/python.exe'
& $hw6Python -m pip install -r "$hw6/requirements.txt"
& $hw6Python "$hw6/code/check_deployment.py" --csv ../Capstone_Digital_Addiction/data/raw/awaremind/full_data_all_feature.csv
& $hw6Python "$hw6/build/build_report.py" --template 'path/to/Deployment Submission.docx'
& "$hw6/build/render_docx.ps1"
```

The checker runs the synthetic test suite first, checks the frozen HW5 lineage, verifies feature, probability, and decision parity, and then starts a temporary loopback server for the smoke test and benchmark. Repeat checks reuse the verified bundle when its contents match. Rebuild both reports after rerunning the benchmark so their timing values match the aggregate results.

## Showcase with the synthetic fixture

The demonstration uses the same loopback API with hand-set ONNX parameters, the distinct version `hw6-synthetic-fixture-v1`, and a synthetic cutoff of 0.35. It can run without the release CSV, any fitted model or internet access.

```powershell
& $hw6Python "$hw6/code/run_demo.py" --rehearse
```

This starts a fresh loopback server, shows health, two example decisions and aggregate metrics, and exits. Use `run_demo.py` without `--rehearse` for a persistent synthetic server using the same key and port contract as the original launcher. See the [showcase runbook](showcase/RUN_OF_SHOW.md) and [submission handoff](showcase/SUBMISSION.md).

## Replay the proposed delivery policy

```powershell
& $hw6Python "$hw6/build/replay_policy.py" --csv ../Capstone_Digital_Addiction/data/raw/awaremind/full_data_all_feature.csv
```

The [aggregate replay](build/results/hw6_policy_replay.json) compares frozen HW5 candidate flags with the fixed rule under the same cap and cooldown. The aggregate subgroup denominators stay inside the ignored run directory. See the [policy and pilot notes](showcase/POLICY_REPLAY.md).

## Serve the verified fitted prototype

```powershell
$env:NUDGEWELL_HW6_API_KEY = & $hw6Python -c "from secrets import token_urlsafe; print(token_urlsafe(32))"
& $hw6Python "$hw6/code/run_local.py"
```

The default address is `127.0.0.1:8766`. Send `X-API-Key` with `POST /v1/predict` or `GET /metrics`. A synthetic input is `{"local_hour":9,"local_weekday":1,"elapsed_minutes":2.0}`. Monday is weekday zero. `GET /health` returns readiness. A candidate flag marks the saved threshold crossing.

The fitted ONNX file and its manifest are written to the ignored `run/fold-0/` directory. Raw data, fitted artifacts and row-level evaluation outputs remain local. The research API runs on the local machine. Device integration, delivery policy, and any model release require separate testing and data-use review. [Data handling rules](../../data/README.md)
