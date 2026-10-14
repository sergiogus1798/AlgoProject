"""The scorecard's measured columns: numbers every paired strategy gets and no screen judges."""

import pandas as pd

from studies.screening.analysis import floating, tradelevel


def table(data: dict) -> pd.DataFrame:
    """Trade-level significance, trade frequency and floating risk, per strategy.

    Args:
        data: What inputs.load returned, plus `market` (inputs.market).

    Returns:
        Indexed by identity, for every strategy with trades — whichever level it fell at.
        `trade_t` is the plain t of the mean OOS trade; `oos_trades_per_year` (the
        build's is level 0's fact, and the t of the excess level 1a's); and
        `<is|oos>_` max_dd_r, worst_day_r, worst_trade_mae_r, net_per_year_r in units of R,
        with `<is|oos>_dd_over_net_year` (max_dd_r / net_per_year_r; +inf when net <= 0).
    """
    market = data["market"]
    trades = data["trades"].sort_values(["identity", "Close time"])
    daily = data["curve"].diff()
    legs = {
        "IS": daily[daily.index < data["split"]],
        "OOS": daily[data["split"] : data["end"]],
    }
    parts = []
    for sample, leg in legs.items():
        mine = trades[trades["sample"] == sample]
        plain = tradelevel.t(mine, "Profit/Loss")
        if sample == "OOS":
            parts.append(pd.DataFrame({"trade_t": plain["iid"]}))
        risk = floating.table(leg, mine, market["risk"], market["years"][sample])
        parts.append(
            risk.assign(
                trades_per_year=plain["n"] / market["years"][sample]
            ).add_prefix(sample.lower() + "_")
        )
    return pd.concat(parts, axis=1).drop(columns="is_trades_per_year")
