"""The search's ledger rows: the pool's own study, and one row in every member's own study."""

import numpy as np

from ledger import record as ledger_record
from ledger.study import study_id


def record(run: dict, pool: dict, plan_key: str, members_meta: dict, cfg: dict) -> list[dict]:
    """Log the search: one row in `PORTFOLIO_<pool>_construct`, one in each member's study.

    Args:
        run: `genetic.run`'s result -- `members`, `score`, `best`; optionally `level` (the
            risk level, same length as `score`, `funded.py`'s side channel from `stagea.best`).
        pool: `inputs.pool.read`'s result (`hash`).
        plan_key: The funded plan searched against, e.g. "hantec:express:2000:USD".
        members_meta: identity -> `{symbol, timeframe, family}`, one entry per admissible
            member the search read (`n_in`).
        cfg: Unused beyond documenting the caller's run config; kept for the signature.

    Returns:
        Every row appended, the pool's row first.
    """
    del cfg
    scores = np.asarray(run["score"], dtype=float)
    identities = list(members_meta)
    symbols = "+".join(sorted({m["symbol"] for m in members_meta.values()}))
    pool_study = f"PORTFOLIO_{pool['hash'][:12]}_construct"
    base = {"step": 27, "launched_by": "funded", "segment": "build", "n_in": len(identities),
            "n_out": int(run["best"]["members"].size), "criterion": f"portfolio/funded/{plan_key}",
            "score_unit": "p_pass"}
    rows = [ledger_record.log(pool_study, {**base, "symbol": symbols, "timeframe": "mixed"}, scores)]
    for identity in identities:
        meta = members_meta[identity]
        sid = study_id(meta["symbol"], meta["timeframe"], meta["family"])
        rows.append(ledger_record.log(
            sid, {**base, "symbol": meta["symbol"], "timeframe": meta["timeframe"]}, scores))
    return rows
