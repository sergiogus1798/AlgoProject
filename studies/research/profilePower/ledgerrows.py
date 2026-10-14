"""The power study's looks at the data, as rows of the ledger's contract L1."""

from typing import Any, cast

import pandas as pd

from core.study.config import fingerprint
from ledger import record, study
from studies.research.marketProfile import inputs as profile

STEP = 1    # like the profile it examines, the workflow's step 1


def rows(runs: pd.DataFrame, cfg: dict) -> list[dict]:
    """One ledger row per cell, measure and direction: the replications run and those detected.

    Args:
        runs: Judged replications (many.judged) measured in this run.
        cfg: The parsed config.

    Returns:
        Rows as `ledger.record.search` stamps them, under the study
        `<SYMBOL>_<TF>_profilePower`: n_in the replications, n_out those significant at the
        cut. The bars are the cell's `build` segment with every bar's sign tossed, so no
        real direction was looked at; the row says so.
    """
    out = []
    for (symbol, timeframe, measure, direction), part in cast("Any", runs.groupby(
            ["symbol", "timeframe", "measure", "direction"], sort=False)):
        lo, hi = profile.span(symbol)
        out.append(record.search(
            study.study_id(symbol, timeframe, "profilePower"),
            {"step": STEP, "launched_by": "studies.research.profilePower.report",
             "config_hash": fingerprint(cfg), "symbol": symbol, "timeframe": timeframe,
             "segment": profile.SEGMENT, "window_from": str(lo.date()),
             "window_to": str(hi.date()), "n_in": len(part),
             "n_out": int(part["significant"].sum()),
             "criterion": f"profilePower/{part['family'].iloc[0]}/{measure}/{direction}",
             "thresholds": {"cut": cfg["judge"]["cut"], **cfg["profile"]["filters"]},
             "seeds": [cfg["run"]["seed"]],
             "note": f"edge plantado ({cfg['plant']['how']}) en copias sin dirección; efectos "
                     f"{sorted(part['effect_planted'].unique())} costes"}))
    return out
