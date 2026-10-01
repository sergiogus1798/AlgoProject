"""The original strategy against random traders with its own footprint, on its own bars."""

import numpy as np
import pandas as pd

from engines.nulls import inputs, simulate, verdict

RUNG = "timing"       # same trades, holds, sizes and costs; only when each one enters is drawn


def against(trades: pd.DataFrame, frame: pd.DataFrame, draws: int, name: str) -> dict:
    """Where the real run lands among its monkeys.

    Args:
        trades: The original's trades inside the window judged.
        frame: The bars of its own timeframe.
        draws: Random traders to draw.
        name: The strategy, which seeds its own monkeys.

    Returns:
        `rows` (one per statistic: the real value, the monkeys' mean and 95th percentile,
        the share of monkeys below it, the empirical p), `reconcile` (how well the engine
        reprices the real trades from the bars — a p from a poor one is decoration),
        `trades`, `draws` and the `seed` drawn.
    """
    cfg = inputs.config([f"nulls.draws={draws}"])
    kept = simulate.fixed(trades.reset_index(drop=True), frame, cfg)
    names = cfg["statistics"]["report"]
    seen, drawn = simulate.real(kept, names), simulate.nulls(kept, RUNG, cfg, name)
    rows = [{"statistic": n, "real": float(seen[n]), "mean": float(drawn[n].mean()),
             "p95": float(np.percentile(drawn[n], 95)),
             "below": float((drawn[n] < seen[n]).mean()),
             "p": verdict.pvalue(seen[n], drawn[n], n)} for n in names]
    return {"rows": rows, "reconcile": float(kept["checks"]["corr"]), "trades": len(trades),
            "draws": draws, "seed": cfg["nulls"]["seed"]}
