"""The profile's own looks at the data, as rows of the ledger's contract L1."""

import json
from pathlib import Path

import pandas as pd

from core.study.config import fingerprint
from ledger import record, study
from studies.research.marketProfile import inputs

STEP = 1    # the profile belongs to the workflow's step 1, the idea


def rows(measures: pd.DataFrame, cfg: dict) -> list[dict]:
    """One ledger row per measure and direction: each is a hypothesis looked at on `build`.

    Args:
        measures: Judged measure rows (many.judged) of the assets measured in this run.
        cfg: The parsed config.

    Returns:
        Rows as `ledger.record.search` stamps them — n_in 1, n_out 1 when the measure passed
        its filters (significance alone for a measure with no trade), the thresholds, the
        seed root and the build window — under the study `<SYMBOL>_<TF>_marketProfile`.
    """
    out = []
    for m in measures.to_dict("records"):
        lo, hi = inputs.span(m["symbol"])
        kept = m["significant"] if pd.isna(m["n_trades"]) else m["passes"]
        out.append(record.search(
            study.study_id(m["symbol"], m["timeframe"], "marketProfile"),
            {"step": STEP, "launched_by": "studies.research.marketProfile.report",
             "config_hash": fingerprint(cfg), "symbol": m["symbol"],
             "timeframe": m["timeframe"], "segment": inputs.SEGMENT,
             "window_from": str(lo.date()), "window_to": str(hi.date()), "n_in": 1,
             "n_out": int(kept),
             "criterion": f"marketProfile/{m['family']}/{m['measure']}/{m['direction']}",
             "thresholds": cfg["filters"], "seeds": [cfg["nulls"]["seed"]],
             "note": f"p {m['p']:.4g}, q {m['q']:.4g}, {cfg['nulls']['draws']} sorteos"}))
    return out


def append(path: Path, new: list[dict]) -> None:
    """Add rows to the profile's own ledger file, one JSON object per line."""
    with path.open("a", encoding="utf-8") as handle:
        for row in new:
            handle.write(json.dumps(row, default=str) + "\n")
