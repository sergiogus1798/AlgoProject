"""The scorecard's measured columns: numbers every paired strategy gets and no screen judges."""

import pandas as pd

from studies.screening.analysis import floating, tradelevel


def table(data: dict) -> pd.DataFrame:
    """Trade-level significance, trade frequency and floating risk, per strategy.

    Args:
        data: What inputs.load returned, plus `bars` (the strategies' own timeframe) and
            `market` (inputs.market).

    Returns:
        Indexed by identity, for every strategy with trades — whichever screen it died at,
        so a rule on these never meets a fact the cascade did not compute. `trade_t` is the
        plain t of the mean OOS trade and `drift_excess_t` the AR(1) t of the OOS trade
        P&L minus the market's drift over each hold; `<is|oos>_trades_per_year`; and
        `<is|oos>_` max_dd_r, worst_day_r, worst_trade_mae_r, net_per_year_r in units of R,
        with `<is|oos>_dd_over_net_year` (max_dd_r / net_per_year_r; +inf when net <= 0).
    """
    market = data["market"]
    trades = data["trades"].sort_values(["identity", "Close time"])
    move = tradelevel.mean_move(data["bars"], market["windows"])
    trades = trades.assign(excess=trades["Profit/Loss"] - tradelevel.drift(
        trades, data["bars"], move, market["point_value"]))
    daily = data["curve"].diff()
    legs = {"IS": daily[:data["split"]].iloc[:-1], "OOS": daily[data["split"]:data["end"]]}
    parts = []
    for sample, leg in legs.items():
        mine = trades[trades["sample"] == sample]
        plain = tradelevel.t(mine, "Profit/Loss")
        if sample == "OOS":
            parts.append(pd.DataFrame({"trade_t": plain["iid"],
                                       "drift_excess_t": tradelevel.t(mine, "excess")["ar1"]}))
        risk = floating.table(leg, mine, market["risk"], market["years"][sample])
        parts.append(risk.assign(trades_per_year=plain["n"] / market["years"][sample])
                     .add_prefix(sample.lower() + "_"))
    return pd.concat(parts, axis=1)
