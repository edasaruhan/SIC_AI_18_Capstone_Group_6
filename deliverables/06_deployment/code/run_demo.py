"""Serve or rehearse the synthetic HW6 demo without any research data or model."""

import argparse
import json
import os
from pathlib import Path
from secrets import token_urlsafe
from tempfile import TemporaryDirectory

import uvicorn

from nudgewell_hw6.api import create_app
from nudgewell_hw6.demo import ABOVE, BELOW, CUTOFF, DEMO_VERSION, write_demo_bundle
from nudgewell_hw6.loopback import loopback_client


def rehearse(app, key):
    headers = {"X-API-Key": key}
    with loopback_client(app) as client:
        health = client.get("/health").raise_for_status().json()
        before = client.get("/metrics", headers=headers).raise_for_status().json()
        requests = []
        for event, flag in ((BELOW, False), (ABOVE, True)):
            prediction = client.post("/v1/predict", json=event, headers=headers).raise_for_status().json()
            if (prediction["candidate_alert"] is not flag
                    or prediction["model_version"] != DEMO_VERSION):
                raise RuntimeError("Unexpected synthetic prediction or version.")
            requests.append({"request": event, "response": prediction})
        after = client.get("/metrics", headers=headers).raise_for_status().json()
    if (health != {"ready": True} or before["prediction_requests"] != 0
            or after["prediction_status_counts"] != {"200": 2}
            or after["candidate_alert_rate"] != .5):
        raise RuntimeError("Unexpected readiness or aggregate counters.")
    return {
        "model": DEMO_VERSION,
        "scope": "Hand-set synthetic fixture. Scores demonstrate the API flow.",
        "cutoff": CUTOFF,
        "GET /health": health,
        "GET /metrics before": before,
        "POST /v1/predict": requests,
        "GET /metrics after": after,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rehearse", action="store_true", help="Run two live HTTP examples and exit.")
    parser.add_argument("--port", type=int, default=8766, help="Port for persistent loopback serving.")
    args = parser.parse_args()
    key = token_urlsafe(32) if args.rehearse else os.environ.get("NUDGEWELL_HW6_API_KEY", "")
    with TemporaryDirectory(prefix="nudgewell-demo-") as scratch:
        directory = Path(scratch) / "bundle"
        write_demo_bundle(directory)
        app = create_app(directory, key, expected_version=DEMO_VERSION)
        if args.rehearse:
            print(json.dumps(rehearse(app, key), indent=2))
        else:
            uvicorn.run(app, host="127.0.0.1", port=args.port, access_log=False)


if __name__ == "__main__":
    main()
