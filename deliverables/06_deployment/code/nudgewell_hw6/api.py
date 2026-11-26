"""A loopback reference interface with aggregate-only monitoring."""

from collections import Counter, deque
from contextlib import asynccontextmanager
from pathlib import Path
from secrets import compare_digest
from threading import Lock
from time import perf_counter_ns

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from .bundle import VERSION, load_bundle, time_features


class CheckIn(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    local_hour: int = Field(ge=0, le=23)
    local_weekday: int = Field(ge=0, le=6)
    elapsed_minutes: float = Field(ge=0, allow_inf_nan=False)


class Monitor:
    def __init__(self):
        self.lock = Lock()
        self.statuses = Counter()
        self.success_ms = deque(maxlen=500)
        self.candidates = 0

    def record(self, status, candidate, elapsed_ms):
        with self.lock:
            self.statuses[status] += 1
            if status == 200:
                self.candidates += int(candidate)
                self.success_ms.append(elapsed_ms)

    def snapshot(self):
        with self.lock:
            count = self.statuses[200]
            return {
                "prediction_requests": sum(self.statuses.values()),
                "prediction_status_counts": {str(k): v for k, v in sorted(self.statuses.items())},
                "successful_predictions": count,
                "candidate_alert_rate": self.candidates / count if count else None,
                "latency_window_size": len(self.success_ms),
                "p95_success_ms": float(np.quantile(self.success_ms, .95)) if self.success_ms else None,
            }


def create_app(directory: Path, key: str, *, expected_version=VERSION):
    if len(key) < 32:
        raise ValueError("Set a local API key of at least 32 characters.")
    secret = key.encode("utf-8")
    monitor = Monitor()

    @asynccontextmanager
    async def lifespan(app):
        try:
            app.state.bundle = load_bundle(directory, expected_version=expected_version)
        except (KeyError, OSError, TypeError, ValueError, RuntimeError):
            # Keep the artifact error internal. Readiness and prediction fail closed.
            app.state.bundle = None
        yield

    app = FastAPI(title="NudgeWell HW6 local reference", lifespan=lifespan)

    @app.middleware("http")
    async def local_access(request: Request, call_next):
        path = request.url.path
        start = perf_counter_ns()
        if path in {"/v1/predict", "/metrics"} and not compare_digest(
            request.headers.get("X-API-Key", "").encode("utf-8"), secret
        ):
            response = JSONResponse({"detail": "Local API key required."}, status_code=401)
        else:
            response = await call_next(request)
        if path == "/v1/predict" and request.method == "POST":
            monitor.record(response.status_code, getattr(request.state, "candidate", False),
                           (perf_counter_ns() - start) / 1_000_000)
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid_input(request, error):
        return JSONResponse({"detail": "Invalid check-in input."}, status_code=422)

    @app.get("/health")
    def health(request: Request):
        ready = request.app.state.bundle is not None
        return JSONResponse({"ready": ready}, status_code=200 if ready else 503)

    @app.post("/v1/predict")
    def predict(event: CheckIn, request: Request):
        bundle = request.app.state.bundle
        if bundle is None:
            return JSONResponse({"detail": "Model unavailable."}, status_code=503)
        features = time_features(event.local_hour, event.local_weekday, event.elapsed_minutes)
        probability = float(bundle.probabilities(features.reshape(1, -1))[0])
        candidate = bool(bundle.flags(probability))
        request.state.candidate = candidate
        return {"model_version": expected_version, "probability_high_gap": probability,
                "candidate_alert": candidate}

    @app.get("/metrics")
    def metrics():
        return monitor.snapshot()

    return app
