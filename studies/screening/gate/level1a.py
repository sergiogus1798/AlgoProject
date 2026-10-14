"""Level 1a of the gate: R3, the t of the per-trade excess over the market's drift."""

import pandas as pd

from engines.market import reprice
from studies.screening.analysis import tradelevel

FACTS = ("drift_excess_t",)


def run(data: dict, alive: pd.Index, cfg: dict) -> pd.DataFrame:
    """R3 for the strategies alive, and the per-trade table of their oos1 trades.

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
        `out` and leaves it in `data["oos"]`: one row per oos1 trade of the strategies in
        `alive` — nobody the cascade already dropped is repriced — in time order within each identity, with `identity`, `open_time` and `close_time`
        (the open of the bar SQX's stamp belongs to, so a later level finds it on the grid:
        reprice.located), `side` (+1 / -1), `lots`, `pnl` and `cost` (reprice.real), `drift`
        (the hold counted up to the bar the trade closed in), `excess`, `window`, the
        calendar window it opened in, and `stop`, the raw price of an exit SQX filled inside
        its bar (a stop-loss), NaN on an exit at a bar open. Raises as reprice.real does.
    """
    if not data:       # tests/test_gate_rules.py runs every level on an empty harvest
        return pd.DataFrame(index=alive, columns=pd.Index(FACTS), dtype=float)
    bars, drift = data["bars"], cfg["drift"]
    trades = data["trades"]
    oos = (trades[(trades["sample"] == "OOS") & trades["identity"].isin(alive)]
           .sort_values(["identity", "Close time"]))
    priced = reprice.real(oos, bars, data["costs"], data.get("feed"))   # tests stage no feed
    term, window = tradelevel.drift_term(oos, bars, data["market"]["windows"]["OOS"],
                                         drift["window"], drift["variant"],
                                         data["costs"]["point_value"])
    when, pnl = bars.index.to_numpy(), priced["pnl"].to_numpy()
    data["oos"] = pd.DataFrame({
        "identity": oos["identity"].to_numpy(), "open_time": when[priced["enter"]],
        "close_time": when[priced["leave"]], "side": priced["side"].to_numpy(),
        "lots": oos["Size"].to_numpy(), "pnl": pnl, "cost": priced["cost"].to_numpy(),
        "drift": term, "excess": pnl - term, "window": window,
        "stop": priced["stop"].to_numpy()})
    data["oos"].to_parquet(data["out"] / "operaciones.parquet", index=False)
    t = tradelevel.t_skew_kurt if drift["se_skew_kurt"] else tradelevel.t
    return pd.DataFrame(t(data["oos"], "excess")[["ar1"]].set_axis(list(FACTS), axis=1)).reindex(alive)
