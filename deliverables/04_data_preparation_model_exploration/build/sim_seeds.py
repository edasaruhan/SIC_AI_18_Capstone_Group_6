"""Pipeline check on several SYNTHETIC datasets: NULL mode (nothing to find) versus
default mode (planted effects).

usage: python -I sim_seeds.py <simulator_dir> <work_dir> [n_seeds]
Same features, models and 5-fold participant split as hw4_pipeline.py.
Tests the code, not people.
"""

import json
import subprocess
import sys
import warnings
from pathlib import Path

import numpy as np
from sklearn.base import clone
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold

warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")
sim_dir, work = Path(sys.argv[1]), Path(sys.argv[2])
n_seeds = int(sys.argv[3]) if len(sys.argv) > 3 else 6
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))
import hw4_pipeline as hp  # noqa: E402

out = {"null": {}, "default": {}}
for mode in ("null", "default"):
    for seed in range(1, n_seeds + 1):
        d = work / f"{mode}_{seed}"
        args = [
            sys.executable,
            "-I",
            str(sim_dir / "simulate_awaremind.py"),
            "--seed",
            str(seed),
            "--out",
            str(d),
        ]
        subprocess.run(
            args + (["--null"] if mode == "null" else []),
            check=True,
            capture_output=True,
        )
        csv = next(p for p in d.glob("SYNTHETIC_*.csv") if "sample" not in p.name)
        _, df = hp.load(csv)
        X, y, g = hp.build_features(df).values, df["high_gap"].values, df["pid"].values
        for name, m in hp.make_models().items():
            oof = np.zeros(len(y))
            for tr, te in GroupKFold(n_splits=5).split(X, y, g):
                oof[te] = clone(m).fit(X[tr], y[tr]).predict_proba(X[te])[:, 1]
            out[mode].setdefault(name, []).append(float(roc_auc_score(y, oof)))
        print(
            mode, seed, {k: round(v[-1], 3) for k, v in out[mode].items()}, flush=True
        )
summary = {
    mode: {
        k: {
            "mean": float(np.mean(v)),
            "sd": float(np.std(v)),
            "min": float(np.min(v)),
            "max": float(np.max(v)),
            "n": len(v),
        }
        for k, v in r.items()
    }
    for mode, r in out.items()
}
print(json.dumps(summary, indent=1))
(work / "sim_seeds.json").write_text(
    json.dumps({"runs": out, "summary": summary}, indent=1), encoding="utf-8"
)
