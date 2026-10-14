"""The bank tables on disk: every run of `funded.sim.run`, and per plan the latest one — its own portfolio's first."""

import json
from pathlib import Path

import pandas as pd

from core.paths import portfolio_dir


def read(folder: Path) -> dict:
    """One bank run: `folder`, `manifest`, `rows` and `addons` (lists of dicts, the parquet's columns)."""
    return {"folder": folder,
            "manifest": json.loads((folder / "manifest.json").read_text(encoding="utf-8")),
            "rows": pd.read_parquet(folder / "table.parquet").to_dict("records"),
            "addons": pd.read_parquet(folder / "addons.parquet").to_dict("records")}


def runs(root: Path | None = None) -> list[dict]:
    """Every bank run on real paths under a folder, newest first (the folder's stamp orders them).

    Args:
        root: Where `funded.sim.run` writes; `None` = `AlgoData/portfolio/bank`.
    """
    root = root or portfolio_dir() / "bank"
    found = [read(m.parent) for m in sorted(root.glob("*/manifest.json"), reverse=True)]
    return [r for r in found if not r["manifest"]["paths"]["synthetic"]]


def per_plan(tables: list[dict]) -> dict[str, dict]:
    """For every plan, the table that speaks for it.

    A portfolio is chosen per plan (PLAN §14): the newest table drawn from the portfolio of
    that very plan wins; without one, the newest table that simulated the plan with another
    plan's portfolio stands in, and `own` is False.

    Args:
        tables: `read()` dicts, newest first.

    Returns:
        plan_key -> `{table, own, rows}` (`rows`: the plan's rows, one per re-buy policy).
    """
    out: dict[str, dict] = {}
    for table in tables:
        source = table["manifest"]["paths"].get("source") or {}
        for plan in dict.fromkeys(r["plan"] for r in table["rows"]):
            own = source.get("plan") == plan
            if plan not in out or (own and not out[plan]["own"]):
                out[plan] = {"table": table, "own": own,
                             "rows": [r for r in table["rows"] if r["plan"] == plan]}
    return out
