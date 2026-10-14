"""The bank search's ledger row: every plan × add-on set × risk-per-phase combination it scored."""

from typing import Any

import numpy as np

from ledger import record as ledger_record


def record(
    study: str,
    symbol: str,
    segment: str,
    search: list[dict],
    chosen: int,
    cfg_hash: str,
) -> dict[str, Any]:
    """Log one bank run in the study its portfolio belongs to.

    Args:
        study: The ledger study, e.g. `PORTFOLIO_<pool>_construct`.
        symbol: The members' symbols joined with `+`.
        segment: The segment the path set was built from.
        search: One dict per configuration scored, with `ev` (USD per bank draw).
        chosen: How many configurations the table kept (one per plan).
        cfg_hash: The config's fingerprint.

    Returns:
        The row as written.
    """
    return ledger_record.log(
        study,
        {
            "step": 27,
            "launched_by": "funded.sim",
            "symbol": symbol,
            "timeframe": "mixed",
            "segment": segment,
            "n_in": len(search),
            "n_out": chosen,
            "config_hash": cfg_hash,
            "criterion": "portfolio/funded/bank",
            "score_unit": "ev_bank_usd",
        },
        np.array([s["ev"] for s in search]),
    )
