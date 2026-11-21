"""Frozen inputs and point-in-time feature construction; no model fitting."""

from dataclasses import dataclass
import copy
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[4]
HOME = Path(__file__).resolve().parents[2]
PROTOCOL_SHA256 = "566f08be28187c6c3ddfc7683eae43d1d9fac7caa0f63821fc71a843bb4a7d06"


class ContractError(ValueError):
    """A failed boundary must stop the run, not silently remove observations."""


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@dataclass(frozen=True)
class FrozenProtocol:
    _config: dict
    digest: str

    @property
    def config(self):
        return copy.deepcopy(self._config)


def load_protocol(path=None):
    path = Path(path or HOME / "build/protocol.json")
    seal = path.with_suffix(".sha256")
    if not seal.is_file() or sha256(path) != PROTOCOL_SHA256:
        raise ContractError("Protocol is missing its seal or differs from frozen v1.")
    if seal.read_text(encoding="utf-8").split()[0] != PROTOCOL_SHA256:
        raise ContractError("Protocol seal mismatch.")
    p = json.loads(path.read_text(encoding="utf-8"))
    if p["status"] != "frozen" or p["version"] != "1.0.0":
        raise ContractError("Expected frozen protocol v1.0.0.")
    for source in p["sources"].values():
        file = ROOT / source["path"]
        if not file.is_file() or sha256(file) != source["sha256"]:
            raise ContractError("A frozen source fingerprint changed.")
    if list(sys.version_info[:2]) != p["environment"]["python_major_minor"]:
        raise ContractError("Python version differs from the protocol.")
    for name, version in p["environment"]["exact_packages"].items():
        if importlib.metadata.version(name) != version:
            raise ContractError("A numerical-library version differs from the protocol.")
    return FrozenProtocol(p, PROTOCOL_SHA256)


def row_positions(size, rows=None):
    """Positions are unique and always returned in released-file order."""
    if rows is None:
        return tuple(range(size))
    a = np.asarray(tuple(rows))
    if a.size == 0:
        return ()
    if a.ndim != 1 or a.dtype.kind not in "iu" or len(np.unique(a)) != len(a):
        raise ContractError("Rows must be unique integer positions.")
    if a.min() < 0 or a.max() >= size:
        raise ContractError("Row position outside the dataset.")
    return tuple(sorted(map(int, a)))


def _numeric(frame, columns):
    try:
        a = frame[columns].apply(pd.to_numeric, errors="raise").to_numpy(dtype=float)
    except (ValueError, TypeError):
        raise ContractError("Invalid numeric metadata.") from None
    if not np.isfinite(a).all():
        raise ContractError("Missing or nonfinite numeric metadata.")
    return a


def clock_parts(frame):
    required = {"esm_time", "unlock_time", "timezone"}
    if not required.issubset(frame.columns) or not frame.index.is_unique:
        raise ContractError("Missing clock inputs or nonunique row index.")
    a = _numeric(frame, ["esm_time", "unlock_time"])
    if (a[:, 1] > a[:, 0]).any() or frame["timezone"].isna().any():
        raise ContractError("Invalid unlock/prompt order or missing timezone.")
    hour = pd.Series(index=frame.index, dtype=float)
    weekday = pd.Series(index=frame.index, dtype=float)
    utc = pd.to_datetime(frame["esm_time"], unit="ms", utc=True)
    for zone, idx in frame.groupby("timezone", sort=False).groups.items():
        try:
            local = utc.loc[idx].dt.tz_convert(str(zone))
        except (ValueError, TypeError, KeyError):
            raise ContractError("Unknown timezone.") from None
        hour.loc[idx], weekday.loc[idx] = local.dt.hour, local.dt.dayofweek
    return hour, weekday, (a[:, 0] - a[:, 1]) / 60000


def build_features(frame, protocol, pack="main_context"):
    """No outcome/lock field is required or read for inference."""
    p = protocol.config
    if pack not in p["features"]["packs"]:
        raise ContractError("Unknown frozen feature pack.")
    h, w, elapsed = clock_parts(frame)
    x = pd.DataFrame(index=frame.index)
    x["hour_sin"], x["hour_cos"] = np.sin(2 * np.pi * h / 24), np.cos(2 * np.pi * h / 24)
    x["weekday_sin"], x["weekday_cos"] = np.sin(2 * np.pi * w / 7), np.cos(2 * np.pi * w / 7)
    x["log_session_minutes"] = np.log1p(elapsed)
    if pack == "main_context":
        if "Category_L1" not in frame:
            raise ContractError("Missing app-category input.")
        category = frame["Category_L1"]
        for c in p["features"]["app_categories"]:
            x["genre_" + c] = category.eq(c).astype(float)
        x["app_context_missing"] = (~category.isin(p["features"]["app_categories"])).astype(float)
    return x.loc[:, p["features"]["packs"][pack]].astype(np.float64)


def validate_feature_matrix(x, protocol, pack):
    if list(x.columns) != protocol.config["features"]["packs"][pack]:
        raise ContractError("Classifier inputs differ from the frozen feature order.")
    try:
        a = x.to_numpy(dtype=float)
    except (ValueError, TypeError):
        raise ContractError("Nonnumeric classifier input.") from None
    if np.isinf(a).any():
        raise ContractError("Infinite classifier input.")


def _row_keys(frame):
    # Canonical JSON pairs: missing values become null, columns sorted by name.
    columns = sorted(frame.columns)
    keys = []
    for values in frame[columns].itertuples(index=False, name=None):
        clean = [None if pd.isna(v) else v.item() if isinstance(v, np.generic) else v for v in values]
        text = json.dumps(list(zip(columns, clean)), ensure_ascii=False, allow_nan=False, separators=(",", ":"))
        keys.append(hashlib.sha256(text.encode("utf-8")).hexdigest())
    return tuple(keys)


@dataclass(frozen=True)
class Dataset:
    _frame: pd.DataFrame
    _labels: np.ndarray
    keys: tuple
    protocol: FrozenProtocol
    counts: dict
    fixture: bool

    def __len__(self):
        return len(self._frame)

    def frame(self, rows=None):
        return self._frame.iloc[list(row_positions(len(self), rows))].copy(deep=True)

    def labels(self, rows=None):
        return self._labels[list(row_positions(len(self), rows))].copy()

    def groups(self, rows=None):
        return self.frame(rows)["pid"].astype(str).to_numpy()

    def features(self, rows=None, pack="main_context"):
        return build_features(self.frame(rows), self.protocol, pack)


def _prepare(raw, protocol, fixture):
    p = protocol.config
    if not raw.columns.is_unique or not set(p["data"]["required_columns"]).issubset(raw.columns):
        raise ContractError("Missing required columns or duplicate column names.")
    df = raw.drop_duplicates(keep="first").reset_index(drop=True).copy(deep=True)
    if df.empty:
        raise ContractError("Dataset has no rows.")
    a = _numeric(df, ["answer", "remaining_minutes", "esm_time", "unlock_time", "lock_time"])
    if not ((a[:, 0] >= 1) & (a[:, 0] <= 10)).all() or (a[:, 1] < 0).any():
        raise ContractError("Invalid target fields.")
    if ((a[:, 3] > a[:, 2]) | (a[:, 2] > a[:, 4])).any():
        raise ContractError("Invalid unlock/prompt/lock order.")
    if df[["pid", "session_id_combined", "timezone"]].isna().any().any():
        raise ContractError("Missing grouping metadata.")
    for column in ["pid", "session_id_combined"]:
        if df[column].astype(str).str.len().eq(0).any():
            raise ContractError("Empty grouping metadata.")
    session = df.groupby(["pid", "session_id_combined"])
    if not session["unlock_time"].nunique().eq(1).all() or not session["lock_time"].nunique().eq(1).all():
        raise ContractError("Inconsistent timestamps within a session.")
    hour, weekday, elapsed = clock_parts(df)
    if not np.isclose(elapsed, df["session_minutes"].to_numpy(dtype=float), rtol=0, atol=1e-6).all():
        raise ContractError("Released session duration disagrees with prompt/unlock.")
    if not np.array_equal(hour.to_numpy(), df["esm_hour"].to_numpy()) or not np.array_equal(weekday.to_numpy(), df["esm_weekday"].to_numpy()):
        raise ContractError("Released clock fields disagree with timezone conversion.")
    utc = pd.to_datetime(df["esm_time"], unit="ms", utc=True)
    for zone, idx in df.groupby("timezone").groups.items():
        actual = utc.loc[idx].dt.tz_convert(str(zone)).dt.strftime("%Y-%m-%d %H:%M:%S")
        supplied = df.loc[idx, "esm_local"].astype(str).str[:19].str.replace("T", " ", regex=False)
        if not actual.eq(supplied).all():
            raise ContractError("Released local timestamps disagree with timezone conversion.")
    categories = p["features"]["app_categories"]
    if not df["Category_L1"].dropna().isin(categories).all():
        raise ContractError("Unknown category in the fixed training release.")
    for c in categories:
        if not df["genre_" + c].astype(bool).eq(df["Category_L1"].eq(c)).all():
            raise ContractError("Released genre bits disagree with category.")
    overlap = df["package_name"].notna() & df["app_at_prompt"].notna()
    if not df.loc[overlap, "package_name"].eq(df.loc[overlap, "app_at_prompt"]).all():
        raise ContractError("Recorded package differs from app at prompt.")
    if (df["Category_L1"].notna() & (df["app_at_prompt"].isna() | df["package_name"].isna())).any():
        raise ContractError("Recorded category lacks current-app provenance.")
    y = ((df["answer"] <= 5) & (df["remaining_minutes"] > 5)).to_numpy(dtype=int)
    counts = {"released_rows": len(raw), "unique_rows": len(df), "positive_rows": int(y.sum()), "participants": int(df["pid"].nunique()), "columns": len(raw.columns)}
    if not fixture and counts != p["data"]["expected_counts"]:
        raise ContractError("Release counts differ from the frozen contract.")
    y.setflags(write=False)
    return Dataset(df, y, _row_keys(df), protocol, counts, fixture)


def fixture_dataset(frame, protocol):
    """Synthetic-test entry point: same validation, without release size/hash."""
    return _prepare(frame, protocol, fixture=True)


def load_dataset(csv, protocol):
    path = Path(csv)
    p = protocol.config
    if sha256(path) != p["data"]["raw_sha256"]:
        raise ContractError("CSV fingerprint differs from the frozen release.")
    for name, expected in p["data"]["dictionary_sha256"].items():
        file = path.parent / name
        if not file.is_file() or sha256(file) != expected:
            raise ContractError("Retained data-dictionary fingerprint changed.")
    return _prepare(pd.read_csv(path, low_memory=False), protocol, fixture=False)


def private_path(path):
    root = (HOME / "run").resolve()
    path = Path(path).resolve()
    if not path.is_relative_to(root) or path == root:
        raise ContractError("Private output must be a file inside the ignored HW5 run directory.")
    ignored = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    if "deliverables/05_model_refinement_test_submission/run/" not in ignored:
        raise ContractError("HW5 private run directory is not ignored.")
    return path


def write_private_json(path, payload):
    path = private_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return path
