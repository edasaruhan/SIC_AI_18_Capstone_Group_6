"""Serve the final-showcase page and the HW6 loopback API from one local origin.

Run with the HW6 environment from the repository root:

    python -B deliverables/06_deployment/showcase/demo_web/serve_showcase.py

The page scores each scripted check-in through the unchanged HW6 ``POST /v1/predict``
route, using the separately versioned illustrative model in ``fixture_v2.py``.
Delivery decisions come from the tested ``delivery_decisions`` in
``build/replay_policy.py``. ``--record`` refreshes ``day.js``, the browser-only fallback.
No research data, fitted model or internet connection is used.
"""

import argparse
from datetime import date, datetime, time, timezone
import json
from pathlib import Path
import re
from secrets import compare_digest, token_urlsafe
import sys
from tempfile import TemporaryDirectory
from threading import Timer
import webbrowser

from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel, ConfigDict, Field
import uvicorn

HERE = Path(__file__).resolve().parent
HW6 = HERE.parents[1]
sys.path.insert(0, str(HW6 / "code"))
sys.path.insert(0, str(HW6 / "build"))

from fixture_v2 import CUTOFF, VERSION, write_v2_bundle  # noqa: E402
from nudgewell_hw6.api import create_app  # noqa: E402
from nudgewell_hw6.loopback import loopback_client  # noqa: E402
from replay_policy import COOLDOWN_MINUTES, DAILY_CAP, delivery_decisions  # noqa: E402

DAY = json.loads((HERE / "scripted_day.json").read_text(encoding="utf-8"))
KEY_PLACEHOLDER = "__NUDGEWELL_KEY__"
HHMM = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


class Schedule(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    times: list[str] = Field(max_length=48)
    candidates: list[bool] = Field(max_length=48)
    elapsed_minutes: list[float] = Field(max_length=48)


def epoch_ms(day, hhmm):
    """Fixed reference timezone: the page shows local clock times only."""
    moment = datetime.combine(day, time.fromisoformat(hhmm), tzinfo=timezone.utc)
    return int(moment.timestamp() * 1000)


def decide(schedule, day=date.fromisoformat(DAY["date"])):
    if not (len(schedule.times) == len(schedule.candidates) == len(schedule.elapsed_minutes)):
        raise ValueError("Schedule lists differ in length.")
    if any(not HHMM.match(t) for t in schedule.times) or schedule.times != sorted(schedule.times):
        raise ValueError("Times must be sorted HH:MM values within one day.")
    events = [(epoch_ms(day, t), day, c) for t, c in zip(schedule.times, schedule.candidates)]
    return {
        "decisions": list(delivery_decisions(events)),
        "timer_fires": [m >= DAY["timer_minutes"] for m in schedule.elapsed_minutes],
        "daily_cap": DAILY_CAP,
        "cooldown_minutes": COOLDOWN_MINUTES,
    }


def build_app(directory, key):
    app = create_app(directory, key, expected_version=VERSION)
    page = (HERE / "index.html").read_text(encoding="utf-8").replace(KEY_PLACEHOLDER, key)
    no_store = {"Cache-Control": "no-store"}

    @app.get("/", response_class=HTMLResponse)
    def index():
        return HTMLResponse(page, headers=no_store)

    @app.get("/day.js")
    def day_js():
        return Response((HERE / "day.js").read_bytes(), media_type="text/javascript", headers=no_store)

    @app.post("/showcase/policy")
    def policy(schedule: Schedule, request: Request):
        if not compare_digest(request.headers.get("X-API-Key", "").encode(), key.encode()):
            return JSONResponse({"detail": "Local API key required."}, status_code=401)
        try:
            return decide(schedule)
        except ValueError as error:
            return JSONResponse({"detail": str(error)}, status_code=422)

    return app


def run_day(client, key):
    """Score the scripted day through HTTP exactly as the page does."""
    headers = {"X-API-Key": key}
    rows = []
    for item in DAY["checkins"]:
        hour = int(item["time"][:2])
        request = {"local_hour": hour, "local_weekday": DAY["local_weekday"],
                   "elapsed_minutes": float(item["elapsed_minutes"])}
        response = client.post("/v1/predict", json=request, headers=headers).raise_for_status().json()
        rows.append({**item, "request": request, "response": response})
    schedule = {"times": [r["time"] for r in rows],
                "candidates": [r["response"]["candidate_alert"] for r in rows],
                "elapsed_minutes": [float(r["elapsed_minutes"]) for r in rows]}
    policy = client.post("/showcase/policy", json=schedule, headers=headers).raise_for_status().json()
    for row, decision, fires in zip(rows, policy["decisions"], policy["timer_fires"]):
        row["decision"], row["timer_fires"] = decision, fires
    return rows, policy


def recorded_payload(rows, policy):
    return {
        "about": DAY["about"], "date": DAY["date"], "model_version": VERSION, "cutoff": CUTOFF,
        "timer_minutes": DAY["timer_minutes"], "daily_cap": policy["daily_cap"],
        "cooldown_minutes": policy["cooldown_minutes"], "checkins": rows,
    }


def write_day_js(payload, path=HERE / "day.js"):
    body = json.dumps(payload, ensure_ascii=False, indent=1)
    path.write_text(
        "// Generated by serve_showcase.py --record. Recorded API responses for the offline fallback.\n"
        f"window.NUDGEWELL_DAY = {body};\n", encoding="utf-8", newline="\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", type=int, default=8767)
    parser.add_argument("--record", action="store_true", help="Refresh day.js from live API responses and exit.")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    key = token_urlsafe(32)
    with TemporaryDirectory(prefix="nudgewell-showcase-") as scratch:
        directory = Path(scratch) / "bundle"
        write_v2_bundle(directory)
        app = build_app(directory, key)
        if args.record:
            with loopback_client(app) as client:
                write_day_js(recorded_payload(*run_day(client, key)))
            print(f"Wrote {HERE / 'day.js'}")
            return
        url = f"http://127.0.0.1:{args.port}/"
        print(f"NudgeWell showcase: {url}  (model {VERSION}, illustrative; Ctrl+C to stop)")
        if not args.no_browser:
            Timer(1.0, webbrowser.open, args=(url,)).start()
        uvicorn.run(app, host="127.0.0.1", port=args.port, access_log=False, log_level="warning")


if __name__ == "__main__":
    main()
