"""The rank search's ledger rows (PLAN §6): the pool's own study and one row in each member's."""

import numpy as np
import pandas as pd

from ledger import record as ledger_record
from ledger.study import study_id


def record(found: dict, pool: dict, members_meta: dict, note: str) -> list[dict]:
    """Log one search on build: every combination evaluated is a trial.

    The scores stored are the combinations' **daily Sharpes**, not their rank scores: the
    verdict deflates the chosen portfolio's Sharpe by the spread of the Sharpes it was
    chosen among, and a rank has no such spread to pool.

    Args:
        found: `choose.choose()`'s result.
        pool: `inputs.pool.read()`'s result (`hash`).
        members_meta: identity -> `{symbol, timeframe, family}`, every member the search read.
        note: What the run wants remembered (mode, relaxed thresholds).

    Returns:
        Every row appended, the pool's first.
    """
    scores = np.asarray(found["table"]["sharpe"], dtype=float)
    base = {"step": 27, "launched_by": "real", "segment": "build", "n_in": len(members_meta),
            "n_out": int(found["members"][found["best"]].sum()),
            "criterion": f"portfolio/ranks4/{found['mode']}", "score_unit": "per_period",
            "note": note}
    symbols = "+".join(sorted({m["symbol"] for m in members_meta.values()}))
    rows = [ledger_record.log(f"PORTFOLIO_{pool['hash'][:12]}_construct",
                              {**base, "symbol": symbols, "timeframe": "mixed"}, scores)]
    # a member's study gains the looks (N) but not the spread: a portfolio's Sharpe pooled with
    # single strategies' would widen that study's sigma with numbers of another kind
    for meta in members_meta.values():
        rows.append(ledger_record.log(
            study_id(meta["symbol"], meta["timeframe"], meta["family"]),
            {**base, "symbol": meta["symbol"], "timeframe": meta["timeframe"],
             "score_unit": "portfolio_sharpe"}, scores))
    return rows


def record_admission(judged: pd.DataFrame, pool: dict, members_meta: dict, how: str) -> dict:
    """Log an admission pass on build: each candidate judged against the base is a trial.

    Args:
        judged: `admission.judge()`'s frame.
        pool, members_meta: As `record`.
        how: The increment's reading ("finite" or "marginal").

    Returns:
        The row appended to the pool's study; the scores are Sharpe increments, a unit of
        their own, so they add to N and never to the Sharpes' spread.
    """
    symbols = "+".join(sorted({m["symbol"] for m in members_meta.values()}))
    row = {"step": 27, "launched_by": "real", "segment": "build", "n_in": len(judged),
           "n_out": int(judged["enters"].sum()), "criterion": f"portfolio/admission/{how}",
           "score_unit": "sharpe_increment", "symbol": symbols, "timeframe": "mixed"}
    return ledger_record.log(f"PORTFOLIO_{pool['hash'][:12]}_construct", row,
                             judged["increment"].to_numpy(float))
