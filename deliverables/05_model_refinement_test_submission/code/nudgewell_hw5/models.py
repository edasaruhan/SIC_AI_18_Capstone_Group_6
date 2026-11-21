"""Exact frozen candidate factory and per-outer-universe fit cache."""

from dataclasses import dataclass
import time

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

from .data_contract import ContractError
from .evaluation_contract import CandidateFitError, fit_base
from .splits import assert_scope


@dataclass(frozen=True)
class Candidate:
    id: str
    base_id: str
    family: str
    pack: str


class CandidateFactory:
    def __init__(self, protocol):
        self.config = protocol.config["models"]
        self.base = {c["id"]: c for c in self.config["ordered_base_candidates"]}
        self.candidates = tuple(Candidate(c["id"], c["base_id"], self.base[c["base_id"]]["family"], c["feature_pack"]) for c in self.config["ordered_structural_candidates"])
        self.by_id = {c.id: c for c in self.candidates}
        pack = self.config["fixed_anchor_feature_pack"]
        self.anchors = {family: self.by_id[pack + "__" + base] for family, base in self.config["fixed_anchor_ids"].items()}

    def estimator(self, candidate):
        if self.by_id.get(candidate.id) != candidate:
            raise ContractError("Candidate is outside the frozen registry.")
        spec = self.base[candidate.base_id]
        params = {**self.config[candidate.family + "_common"], **spec["parameters"]}
        return LogisticRegression(**params) if candidate.family == "LR" else RandomForestClassifier(**params)

    def describe(self, candidate):
        return {"id": candidate.id, "base_id": candidate.base_id, "family": candidate.family, "feature_pack": candidate.pack, "parameters": {**self.config[candidate.family + "_common"], **self.base[candidate.base_id]["parameters"]}}


class FitCache:
    """Never shared across datasets or outer selectors; failures are cached too."""
    def __init__(self, data, factory=None, fixture_estimator=None):
        if fixture_estimator is not None and not data.fixture:
            raise ContractError("Estimator substitution is restricted to synthetic fixtures.")
        self.data = data
        self.factory = factory or CandidateFactory(data.protocol)
        self.fixture_estimator = fixture_estimator
        self.models = {}
        self.failures = {}
        self.jobs = []
        self.hits = 0

    def get(self, scope, candidate):
        assert_scope(self.data, scope)
        if self.factory.by_id.get(candidate.id) != candidate:
            raise ContractError("Candidate is outside the frozen registry.")
        key = (scope.rows, scope.allowed_rows, scope.forbidden_groups, scope.subject, scope.cutoff_ms, candidate.id)
        if key in self.models:
            self.hits += 1
            return self.models[key]
        if key in self.failures:
            self.hits += 1
            message, records, attempts = self.failures[key]
            raise CandidateFitError(message, records, attempts)
        estimator = self.fixture_estimator(candidate) if self.fixture_estimator else self.factory.estimator(candidate)
        start = time.perf_counter()
        try:
            fitted = fit_base(self.data, scope, estimator, candidate.family, candidate.pack)
        except CandidateFitError as error:
            self.failures[key] = (str(error), error.warning_records, error.attempts)
            self.jobs.append({"candidate": candidate.id, "scope": scope.purpose, "training_rows": len(scope.rows), "status": "failed", "attempts": error.attempts, "warnings": error.warning_records, "error": str(error), "seconds": time.perf_counter() - start})
            raise
        self.models[key] = fitted
        self.jobs.append({"candidate": candidate.id, "scope": scope.purpose, "training_rows": len(scope.rows), "status": fitted.status, "attempts": 0 if fitted.constant is not None else 2 if fitted.status == "retried_convergence" else 1, "warnings": fitted.warning_records, "seconds": time.perf_counter() - start})
        return fitted

    def summary(self):
        return {"base_fit_jobs": len(self.jobs), "estimator_fit_attempts": sum(j["attempts"] for j in self.jobs), "cache_hits": self.hits, "failed_jobs": sum(j["status"] == "failed" for j in self.jobs), "constant_fallback_jobs": sum(j["status"] in ["empty_training", "one_class_training"] for j in self.jobs), "warning_counts": {name: sum(w[0] == name for j in self.jobs for w in j["warnings"]) for name in sorted({w[0] for j in self.jobs for w in j["warnings"]})}, "fit_seconds": sum(j["seconds"] for j in self.jobs)}
