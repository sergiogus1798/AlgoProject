"""Which few hundred tuples the pilot samples, and which levels its trade counts drop. Pure maths."""

import numpy as np
import pandas as pd
from scipy.stats import qmc


def sample(live: dict[str, list[float]], cfg: dict) -> pd.DataFrame:
    """A low-discrepancy sample of the live parameter space, a few hundred tuples.

    Args:
        live: Output of `design.levels.live` -- the parameters that move the result, with
            every value they may take. The frozen ones are never sampled here: whether a
            region trades is decided by what moves, and varying a frozen value would spend
            the pilot's budget on a question it does not exist to answer.
        cfg: The `pilot` block of `config.yaml`: `sample`, `seed`.

    Returns:
        One row per pilot tuple, `pilot_id` (`X00000` and up) first. Sobol, the same way
        `design.strata.coverage` draws -- a power-of-two block cut down to `sample`,
        because its balance properties hold on those block sizes and no other.
    """
    names = sorted(live)
    n = cfg["sample"]
    size = 2 ** int(np.ceil(np.log2(max(n, 2))))
    unit = qmc.Sobol(d=len(names), scramble=True, seed=cfg["seed"]).random(size)[:n]
    rows = [{name: live[name][min(int(row[i] * len(live[name])), len(live[name]) - 1)]
             for i, name in enumerate(names)} for row in unit]
    table = pd.DataFrame(rows)
    table.insert(0, "pilot_id", [f"X{i:05d}" for i in range(len(table))])
    return table


def decide(table: pd.DataFrame, counts: dict[str, float],
           min_trades: int, min_support: int) -> tuple[dict[str, set], dict]:
    """Which live-parameter levels the pilot's trade counts say do not trade enough.

    Args:
        table: What `sample` returned.
        counts: `pilot_id` to trades observed in the pilot's retest (the build segment,
            main market). A tuple the retest never returned is absent, not zero -- SQX
            drops a strategy on its own red flags before it would ever reach here, and
            counting it as a silent zero would blame the pilot for something else's
            decision.
        min_trades: The floor a level's median trade count must clear to survive
            (`pilot.min_trades`).
        min_support: How many pilot points must have used a level before its median is
            trusted (`pilot.min_support`); fewer and the level is undersampled, not silent.

    Returns:
        `(banned, report)`. `banned`: parameter name to the set of dropped level VALUES --
        never every level of a parameter, because a design left with nothing to vary over
        one of its own live parameters is not a design; a parameter that would lose all but
        one level keeps every level instead, and the report says so. `report["rows"]`: one
        row per (parameter, level) with its median trade count, how many pilot points
        supported it and whether it was dropped -- what `pilot.json` writes to disk, so the
        drop is never silent.
    """
    trades = table["pilot_id"].map(counts)
    names = [c for c in table.columns if c != "pilot_id"]
    banned: dict[str, set] = {}
    rows = []
    for name in names:
        by_level = trades.groupby(table[name])
        median, support = by_level.median(), by_level.count()
        levels_sorted = sorted(median.index)
        drop = {lvl for lvl in levels_sorted
                if support[lvl] >= min_support and median[lvl] < min_trades}
        kept = len(levels_sorted) - len(drop)
        starved = drop and kept < 2
        if starved:
            drop = set()
        for lvl in levels_sorted:
            rows.append({"parameter": name, "level": lvl,
                         "median_trades": float(median[lvl]), "support": int(support[lvl]),
                         "dropped": lvl in drop,
                         "kept_despite_floor": bool(starved and median[lvl] < min_trades
                                                    and support[lvl] >= min_support)})
        if drop:
            banned[name] = drop
    return banned, {"min_trades": min_trades, "min_support": min_support,
                    "pilot_n": len(table), "scored": int(trades.notna().sum()),
                    "rows": rows}
