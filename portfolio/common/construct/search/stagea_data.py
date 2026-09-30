"""Per-member build-day and M5 block arrays for one firm, scaled to per-(risk x size) units."""

import numpy as np
import pandas as pd


def prepare(universe: dict, firm: str, members: list[str], calendar: dict,
            factors: dict[str, float], min_size: dict[str, float]) -> dict:
    """Build the arrays `stagea.evaluate` sums over combinations of.

    Args:
        universe: `equity.store.load()` output.
        firm: Which firm's server-day clock and M5 grid to read (`days_<firm>`, `m5_<firm>`).
        members: Identities to include, in the order the output's rows follow.
        calendar: A portfolio calendar dict (`inputs.calendar.portfolio()`); only `"build"` is used.
        factors: Each member's `f = atr_multiple / (risk_usd * X)` — SQX dollars to per-(r*S) dollars.
        min_size: Each member's smallest trade lot (from its harvest, unscaled).

    Returns:
        `identities` (array of `members`), `days` (int64 ns, build server days), `closed`,
        `float_end` (float64 [N, D]), `opened` (int64 [N, D]), `low5`, `high5` (float32 [N, B],
        build blocks only), `block_day` (int32 [B], index into `days`), `lot_unit` (float64 [N]).
    """
    frame = universe["days"][firm]
    m5 = universe["m5"][firm]
    build_from, build_to = calendar["build"]
    frame = frame[(frame["day"] >= build_from) & (frame["day"] <= build_to)]
    days = np.sort(frame["day"].unique()).astype("datetime64[ns]").astype("int64")
    day_pos = pd.Series(np.arange(len(days)), index=pd.Index(days))

    n, d = len(members), len(days)
    closed = np.zeros((n, d))
    float_end = np.zeros((n, d))
    opened = np.zeros((n, d), dtype=np.int64)
    for i, identity in enumerate(members):
        f = factors[identity]
        rows = frame[frame["identity"] == identity]
        pos = day_pos[rows["day"].to_numpy().astype("datetime64[ns]").astype("int64")].to_numpy()
        closed[i, pos] = rows["closed"].to_numpy() * f
        opened[i, pos] = rows["opened"].to_numpy()
        fe = np.full(d, np.nan)
        fe[pos] = rows["float_end"].to_numpy() * f
        float_end[i] = pd.Series(fe).ffill().fillna(0.0).to_numpy()

    block_day_all = m5["block_days"].astype("int64")
    in_build = np.isin(block_day_all, days)
    block_day = np.searchsorted(days, block_day_all[in_build]).astype(np.int32)
    low5 = np.empty((n, int(in_build.sum())), dtype=np.float32)
    high5 = np.empty((n, int(in_build.sum())), dtype=np.float32)
    lot_unit = np.empty(n)
    for i, identity in enumerate(members):
        f = factors[identity]
        low5[i] = m5["low"][identity][in_build] * f
        high5[i] = m5["high"][identity][in_build] * f
        lot_unit[i] = min_size[identity] * f

    return {"identities": np.array(members), "days": days, "closed": closed,
            "float_end": float_end, "opened": opened, "low5": low5, "high5": high5,
            "block_day": block_day, "lot_unit": lot_unit}
