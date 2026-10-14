"""The folders the PORTFOLIOS zone test reads, planted in a temp root: shared by test_ui_portfolios, not a test itself."""

import json
from pathlib import Path

import pandas as pd

A, B, C = "a" * 64, "b" * 64, "c" * 64
RUN, FUNDED = (
    "2026-01-01T0000_Test_p_real",
    "2026-01-02T0000_Test_p_ftmo_2step_10000_USD",
)
BEST = {
    "k": 2,
    "score": 0.9,
    "rar": 1.0,
    "r_cubed": 2.0,
    "gain_to_pain": 3.0,
    "p_losing_year": 0.1,
    "sharpe": 0.05,
    "floor_risk": 0.0002,
}


def plant(root: Path) -> None:
    """A portfolio folder with one real run, one stage-A run and one screened universe of three members."""
    real = root / "runs" / RUN
    real.mkdir(parents=True)
    (real / "manifest.json").write_text(
        json.dumps(
            {
                "pool": "Test_p",
                "mode": "exhaustive",
                "n_scored": 3,
                "n_reference": 3,
                "shift": "0…3 meses",
                "relaxed": {"pearson": 0.9},
                "identities": [A, B, C],
                "best_members": [A, B],
                "best": BEST,
            }
        )
    )
    pd.DataFrame(
        [{"members": f"{A}+{B}", **BEST}, {"members": A, **BEST, "k": 1, "score": 0.4}]
    ).to_parquet(real / "search.parquet")
    funded = root / "runs" / FUNDED
    funded.mkdir()
    (funded / "manifest.json").write_text(
        json.dumps(
            {
                "pool": "Test_p",
                "plan": "ftmo:2step:10000:USD",
                "firm": "ftmo",
                "relaxed": {},
                "best_members": [A],
                "best_score": 0.25,
                "n_scored": 1,
            }
        )
    )  # no "cap": a run written before the risk cap was counted
    pd.DataFrame([{"members": A, "level": 0.01, "score": 0.25}]).to_parquet(
        funded / "search.parquet"
    )
    universe = root / "universe" / "hash-fingerprint"
    universe.mkdir(parents=True)
    pairs = [(A, B, 0.10), (A, C, 0.20), (B, C, -0.45)]
    pd.DataFrame(
        [
            {
                "i": i,
                "j": j,
                "measure": "pearson_monthly",
                "value": v,
                "n_overlap_months": 60,
            }
            for i, j, v in pairs
        ]
    ).to_parquet(universe / "pairs.parquet")
    (universe / "manifest.json").write_text(
        json.dumps({"built_at": "2026-01-01T00:00:00"})
    )
    (universe / "screen.json").write_text(
        json.dumps(
            {
                "thresholds": {
                    "pearson": 0.30,
                    "spearman": 0.30,
                    "co_loss": 0.30,
                    "tail": 0.30,
                    "rolling_whole": 0.30,
                    "rolling_recent": 0.30,
                },
                "relaxed": {},
                "sign": "abs",
                "one_sided": ["tail", "co_loss"],
                "identities": [A, B, C],
                "edges": [[A, B], [A, C]],
                "failing": [{"i": B, "j": C, "filter": "pearson_monthly"}],
                "counts": {"pearson_monthly": 1},
                "n_pairs": 3,
                "n_admissible_pairs": 2,
                "n_without_rolling": 0,
                "n_in": 3,
                "n_out": 3,
                "effective_n": {
                    "calm": {"participation": 2.0, "average": 1.9},
                    "stress": {"participation": 1.5, "average": 1.4},
                },
            }
        )
    )
