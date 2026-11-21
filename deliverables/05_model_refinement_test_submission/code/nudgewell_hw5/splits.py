"""Label-blind nested participant folds and resolved-history calendar days."""

from dataclasses import dataclass
import hashlib

import pandas as pd

from .data_contract import ContractError, row_positions


@dataclass(frozen=True)
class FitScope:
    rows: tuple
    allowed_rows: tuple
    forbidden_groups: frozenset = frozenset()
    subject: str | None = None
    cutoff_ms: int | None = None
    purpose: str = "population"


def assert_scope(data, scope):
    rows = row_positions(len(data), scope.rows)
    allowed = row_positions(len(data), scope.allowed_rows)
    if rows != scope.rows or not set(rows).issubset(allowed):
        raise ContractError("Fit rows exceed their permitted universe or order.")
    part = data.frame(rows)
    groups = set(part["pid"].astype(str))
    if groups & set(scope.forbidden_groups):
        raise ContractError("Forbidden participant entered an upstream fit.")
    if scope.subject is not None and groups - {scope.subject}:
        raise ContractError("Personal history contains another participant.")
    if scope.cutoff_ms is not None and not (
        (part["esm_time"] < scope.cutoff_ms) & (part["lock_time"] < scope.cutoff_ms)
    ).all():
        raise ContractError("Unresolved or future outcome entered history.")


@dataclass(frozen=True)
class GroupSplit:
    train: tuple
    test: tuple
    universe: tuple
    forbidden_groups: frozenset
    namespace: str
    fold: int

    def fit_scope(self):
        return FitScope(self.train, self.train, self.forbidden_groups, purpose=self.namespace)


def fold_groups(groups, namespace, n_splits, seed=42):
    groups = sorted(set(map(str, groups)))
    if len(groups) < n_splits or n_splits < 2:
        raise ContractError("Not enough participants for the frozen fold count.")
    ordered = sorted(groups, key=lambda g: (hashlib.sha256(f"{seed}|{namespace}|{g}".encode("utf-8")).hexdigest(), g))
    return {g: i % n_splits for i, g in enumerate(ordered)}


def assert_group_split(data, split):
    tr, te, universe = (row_positions(len(data), r) for r in (split.train, split.test, split.universe))
    if (tr, te, universe) != (split.train, split.test, split.universe):
        raise ContractError("Split rows are not in source order.")
    if set(tr) & set(te) or set(tr) | set(te) != set(universe):
        raise ContractError("Split does not partition its permitted universe.")
    if set(data.groups(tr)) & set(data.groups(te)):
        raise ContractError("Participant crosses a fitting/evaluation boundary.")
    if not set(data.groups(te)).issubset(split.forbidden_groups):
        raise ContractError("Evaluation participants are not explicitly excluded.")
    assert_scope(data, split.fit_scope())


def group_splits(data, universe, namespace, n_splits, inherited_exclusions=frozenset()):
    universe = row_positions(len(data), universe)
    groups = data.groups(universe)
    if set(groups) & set(inherited_exclusions):
        raise ContractError("Forbidden participant entered the split universe.")
    assignment = fold_groups(groups, namespace, n_splits, data.protocol.config["splits"]["seed"])
    for fold in range(n_splits):
        test = tuple(r for r, g in zip(universe, groups) if assignment[g] == fold)
        train = tuple(r for r, g in zip(universe, groups) if assignment[g] != fold)
        forbidden = frozenset(inherited_exclusions) | frozenset(data.groups(test))
        split = GroupSplit(train, test, universe, forbidden, namespace, fold)
        assert_group_split(data, split)
        yield split


def outer_splits(data):
    p = data.protocol.config["splits"]
    return tuple(group_splits(data, range(len(data)), p["outer_namespace"], p["outer_folds"]))


def inner_splits(data, outer):
    assert_group_split(data, outer)
    p = data.protocol.config["splits"]
    namespace = p["inner_namespace"].format(outer_fold=outer.fold)
    return tuple(group_splits(data, outer.train, namespace, p["inner_folds"], outer.forbidden_groups))


def calibration_splits(data, outer, inner):
    assert_group_split(data, outer)
    assert_group_split(data, inner)
    if inner.universe != outer.train or not outer.forbidden_groups.issubset(inner.forbidden_groups):
        raise ContractError("Inner calibration lost its outer boundary.")
    p = data.protocol.config["splits"]
    namespace = p["calibration_namespace"].format(outer_fold=outer.fold, inner_fold=inner.fold)
    return tuple(group_splits(data, inner.train, namespace, p["calibration_folds"], inner.forbidden_groups))


@dataclass(frozen=True)
class DaySplit:
    subject: str
    reference_timezone: str
    cutoff_ms: int
    end_ms: int
    history: tuple
    test: tuple
    unresolved_prior: tuple

    def fit_scope(self):
        return FitScope(self.history, self.history, subject=self.subject, cutoff_ms=self.cutoff_ms, purpose="personal_history")


def _reference_clock(data, subject):
    frame = data.frame()
    part = frame.loc[frame["pid"].astype(str).eq(str(subject))]
    if part.empty:
        raise ContractError("Unknown participant for daily evaluation.")
    zone = str(part.sort_values("esm_time", kind="stable")["timezone"].iloc[0])
    local = pd.to_datetime(part["esm_time"], unit="ms", utc=True).dt.tz_convert(zone)
    return part, zone, local


def assert_day_split(data, day):
    part, zone, local = _reference_clock(data, day.subject)
    if zone != day.reference_timezone:
        raise ContractError("Daily evaluation changed the first-observed timezone.")
    cutoff = pd.Timestamp(day.cutoff_ms, unit="ms", tz="UTC").tz_convert(zone)
    first_test = local.min().normalize() + pd.DateOffset(days=data.protocol.config["known_user"]["warmup_calendar_days"])
    if cutoff != cutoff.normalize() or cutoff < first_test:
        raise ContractError("Daily cutoff is not a post-warmup reference midnight.")
    expected_end = (cutoff + pd.DateOffset(days=1)).tz_convert("UTC").value // 1_000_000
    if day.end_ms != expected_end:
        raise ContractError("Daily interval does not follow timezone calendar arithmetic.")
    tr = (part["esm_time"] < day.cutoff_ms) & (part["lock_time"] < day.cutoff_ms)
    te = (part["esm_time"] >= day.cutoff_ms) & (part["esm_time"] < day.end_ms)
    unresolved = (part["esm_time"] < day.cutoff_ms) & (part["lock_time"] >= day.cutoff_ms)
    if day.history != tuple(part.index[tr]) or day.test != tuple(part.index[te]) or day.unresolved_prior != tuple(part.index[unresolved]):
        raise ContractError("Daily masks omit rows or admit future/unresolved outcomes.")
    if not day.test or set(day.history) & set(day.test):
        raise ContractError("Daily evaluation is empty or overlaps history.")
    if set(part.loc[list(day.history), "session_id_combined"]) & set(part.loc[list(day.test), "session_id_combined"]):
        raise ContractError("A session crosses the history/evaluation boundary.")
    assert_scope(data, day.fit_scope())


def day_splits(data, subject):
    part, zone, local = _reference_clock(data, subject)
    first_test = local.min().normalize() + pd.DateOffset(days=data.protocol.config["known_user"]["warmup_calendar_days"])
    for day in sorted(set(local.loc[local >= first_test].dt.normalize())):
        end = day + pd.DateOffset(days=1)
        cutoff_ms = int(day.tz_convert("UTC").value // 1_000_000)
        end_ms = int(end.tz_convert("UTC").value // 1_000_000)
        tr = (part["esm_time"] < cutoff_ms) & (part["lock_time"] < cutoff_ms)
        te = (part["esm_time"] >= cutoff_ms) & (part["esm_time"] < end_ms)
        unresolved = (part["esm_time"] < cutoff_ms) & (part["lock_time"] >= cutoff_ms)
        split = DaySplit(str(subject), zone, cutoff_ms, end_ms, tuple(part.index[tr]), tuple(part.index[te]), tuple(part.index[unresolved]))
        assert_day_split(data, split)
        yield split


def peer_scope(data, outer, day):
    assert_group_split(data, outer)
    assert_day_split(data, day)
    if day.subject not in outer.forbidden_groups:
        raise ContractError("Population archive did not exclude the evaluated person.")
    return outer.fit_scope()


def split_manifest(data, outers, days):
    """Private payload; write only with data_contract.write_private_json."""
    return {
        "protocol_sha256": data.protocol.digest,
        "private_row_keys": list(data.keys),
        "outer": [{"fold": s.fold, "train": list(s.train), "test": list(s.test), "excluded_people": sorted(s.forbidden_groups)} for s in outers],
        "days": [{"subject": d.subject, "reference_timezone": d.reference_timezone, "cutoff_ms": d.cutoff_ms, "end_ms": d.end_ms, "history": list(d.history), "test": list(d.test), "unresolved_prior": list(d.unresolved_prior)} for d in days],
    }
