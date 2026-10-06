"""Level 1a of the gate: R3, the t of the per-trade excess over the market's drift."""

import numpy as np
import pandas as pd

from engines.market import reprice
from studies.screening.analysis import tradelevel

FACTS = ("drift_excess_t",)


def run(data: dict, alive: pd.Index, cfg: dict) -> pd.DataFrame:
    """R3 for the strategies alive, and the per-trade table of oos1 for every paired one.

    Args:
        data: The harvest as `inputs.load` gives it, plus `bars` (the strategies' own
            timeframe), `market` (inputs.market), `costs` (reprice.costs of the feed's oos1)
            and `out`, the gate's report folder.
        alive: Identities still in the cascade.
        cfg: The gate's config; reads `drift`.

    Returns:
        Indexed by `alive`: `drift_excess_t`, the AR(1) t of the oos1 trades' excess — the
        common repricer's P/L minus `tradelevel.drift_term` — with the skewness and kurtosis
        standard error when `drift.se_skew_kurt`. It also writes `operaciones.parquet` into
        `out` and leaves it in `data["oos"]`: one row per oos1 trade in time order within each
        identity, with `identity`, `open_time`, `close_time`, `side` (+1 / -1), `lots`, `pnl`
        and `cost` (reprice.pnl), `drift`, `excess` and `window`, the calendar window it
        opened in.
    """
    if not data:       # tests/test_gate_rules.py runs every level on an empty harvest
        return pd.DataFrame(index=alive, columns=list(FACTS), dtype=float)
    bars, drift = data["bars"], cfg["drift"]
    oos = data["trades"][data["trades"]["sample"] == "OOS"].sort_values(["identity", "Close time"])
    enter, leave = (bars.index.get_indexer(oos[k]) for k in ("Open time", "Close time"))
    assert (enter >= 0).all() and (leave >= 0).all(), "an oos1 trade is stamped off the bar grid"
    side = np.where(oos["Type"].astype(str) == "Sell", -1.0, 1.0)
    pnl, cost = reprice.pnl(reprice.fills(bars, enter), reprice.fills(bars, leave),
                            oos["Open time"].to_numpy(), oos["Close time"].to_numpy(), side,
                            oos["Size"].to_numpy(), data["costs"])
    term, window = tradelevel.drift_term(oos, bars, data["market"]["windows"]["OOS"],
                                         drift["window"], drift["variant"],
                                         data["costs"]["point_value"])
    data["oos"] = pd.DataFrame({
        "identity": oos["identity"].to_numpy(), "open_time": oos["Open time"].to_numpy(),
        "close_time": oos["Close time"].to_numpy(), "side": side, "lots": oos["Size"].to_numpy(),
        "pnl": pnl, "cost": cost, "drift": term, "excess": pnl - term, "window": window})
    data["oos"].to_parquet(data["out"] / "operaciones.parquet", index=False)
    t = tradelevel.t_skew_kurt if drift["se_skew_kurt"] else tradelevel.t
    return t(data["oos"], "excess")[["ar1"]].set_axis(list(FACTS), axis=1).reindex(alive)
