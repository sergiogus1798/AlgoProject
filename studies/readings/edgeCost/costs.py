"""Rebuild the gross P&L per trade, and reconcile it against what SQX reported.

The spread is never a charge in the trade export (`knowhow/costs/where-the-spread-is.md`):
it sits inside the fill price, so `(Close price - Open price)` already has it baked in.
`price_pnl` recovers that raw price move; adding the spread and commission back to the
*reported* net P/L is what turns it into the gross the owner asked for.

Two different spread numbers are used on purpose, and they must never be swapped:
`spread_share.measure()` gives the round-trip cost the historical fill ACTUALLY embedded
(measured against the bars, per feed and segment) — that is what gross has to remove.
`_spread_points()` gives what `assets/symbols/*.yaml` says the cost is TODAY — that is the
"coste modelado hoy" the encargo asks the edge to be expressed in multiples of. A run built
years ago may not have carried today's declared spread; the two are kept apart precisely so
one is never mistaken for the other (review BLOCKER, 2026-09-26).
"""

import numpy as np
import pandas as pd

from core import assetcheck, assetdata
from studies.readings.edgeCost import spread_share

DIRECTION = {"Buy": 1, "Sell": -1}


def asset_for(feed: str) -> dict:
    """The asset file that prices this feed's costs.

    Args:
        feed: SQX symbol as the harvest's manifest names it, e.g. "XAUUSD_DukasM1_Infinox".

    Returns:
        `core.assetdata.load()`'s dict. Raises when no `assets/symbols/*.yaml` claims the
        feed — this study refuses to price a trade against a guess.
    """
    symbol = assetdata.symbol_for(feed)
    if symbol is None:
        raise SystemExit(f"ningún fichero de assets/symbols/ declara el feed {feed!r}")
    return assetdata.load(symbol)


def _spread_points(asset: dict, sample: pd.Series) -> pd.Series:
    """The spread each trade's segment carries TODAY, in points (assets/symbols/*.yaml)."""
    fields = assetdata.schema(asset)["spread"]["fields"]
    by_sample = {"IS": asset["costs"][fields[0]]["use"], "OOS": asset["costs"][fields[-1]]["use"]}
    return sample.map(by_sample)


def _commission(asset: dict, size: pd.Series, open_price: pd.Series, point_value: float) -> pd.Series:
    """Commission per trade, by the method the asset's class declares.

    ⚠️ `PercentageBased` (no_forex, e.g. XAUUSD) is OPEN.md issue 26: unverified whether SQX
    charges it once per trade or once per leg — a factor of two this function does not
    resolve. Callers on a `no_forex` asset must mark their result `costs_provisional`.
    """
    schema = assetdata.schema(asset)["commission"]
    use = asset["costs"][schema["field"]]["use"]
    if schema["sqx_method"] == "SizeBased":
        return use * size
    return (use / 100) * size * open_price * point_value


def per_trade(trades: pd.DataFrame, asset: dict, feed: str, timeframe: str) -> pd.DataFrame:
    """Every trade with its price-only P&L, the ACTUAL cost it paid, and today's modelled cost.

    Args:
        trades: One harvest's trades (`inputs.trades`), carrying `sample` ("IS"/"OOS").
        asset: `asset_for()`'s dict.
        feed: SQX feed, for `spread_share.measure()`.
        timeframe: The bars the strategies were priced on, e.g. "M30".

    Returns:
        `trades` plus `price_pnl` (the raw price move at the fill prices), `spread_cost`
        (the round-trip spread ACTUALLY embedded, measured against the bars — never
        assumed), `commission_cost`, `gross` = `Profit/Loss` + `commission_cost` +
        `spread_cost`, and `cost_today` = today's declared spread (assets/symbols/) plus
        commission — the denominator `one.measure()` reads the edge in multiples of.
    """
    tick = asset["instrument"]["tick_size"]
    point_value = asset["instrument"]["point_value"]
    direction = trades["Type"].astype(str).map(DIRECTION)
    price_pnl = (trades["Close price"] - trades["Open price"]) * direction * trades["Size"] * point_value
    measured = spread_share.measure(trades, feed, timeframe)
    spread_cost = trades["sample"].map(measured) * point_value * trades["Size"]
    commission_cost = _commission(asset, trades["Size"], trades["Open price"], point_value)
    gross = trades["Profit/Loss"] + commission_cost + spread_cost
    spread_today = _spread_points(asset, trades["sample"]) * tick * point_value * trades["Size"]
    return trades.assign(direction=direction, price_pnl=price_pnl, spread_cost=spread_cost,
                         commission_cost=commission_cost, gross=gross,
                         cost_today=spread_today + commission_cost)


def warnings(asset: dict) -> list[dict]:
    """What must be said about this asset's costs before trusting a money figure.

    Args:
        asset: `asset_for()`'s dict.

    Returns:
        One warning per stand-in cost field (`core.assetcheck.provisional`), plus, on a
        `no_forex` asset, OPEN.md issue 26: whether `PercentageBased` charges once per
        trade or once per leg is unverified, and this study cannot resolve it without a
        SQX run — every gross figure it produces there is `costs_provisional`.
    """
    stood_in = assetcheck.provisional(asset)
    out = [{"code": "provisional", "state": "watch",
            "text": f"{asset['symbol']}: {', '.join(stood_in)} son valores puestos por el "
                    "dueño para desbloquear la autoría, no cifras pactadas con el bróker "
                    "(assets/symbols/*.yaml). Todo bruto de este resultado los hereda."}
          ] if stood_in else []
    if asset["class"] == "no_forex":
        out.append({"code": "issue26", "state": "watch",
                    "text": "OPEN.md #26: sin verificar si la comisión porcentual se cobra "
                            "una vez por operación o una vez por pata (factor 2 sin medir). "
                            "costs_provisional para todo bruto y coste de este activo."})
    return out


def reconcile(priced: pd.DataFrame) -> dict:
    """How well the price-only P&L explains what SQX actually reported.

    Args:
        priced: `per_trade()`'s output.

    Returns:
        `corr` between `price_pnl` and `Profit/Loss + commission_cost` (what price alone
        should equal once commission, the one cost NOT in the fill price, is added back);
        the residual's mean and std (swap and rounding); and one worked trade, plain floats.
    """
    target = priced["Profit/Loss"] + priced["commission_cost"]
    corr = float(np.corrcoef(priced["price_pnl"], target)[0, 1])
    resid = target - priced["price_pnl"]
    row = priced.iloc[0]
    example = {"open_time": str(row["Open time"]), "type": row["Type"],
              "open_price": float(row["Open price"]), "close_price": float(row["Close price"]),
              "size": float(row["Size"]), "reported_pnl": float(row["Profit/Loss"]),
              "price_pnl": float(row["price_pnl"]), "spread_cost": float(row["spread_cost"]),
              "commission_cost": float(row["commission_cost"]), "gross": float(row["gross"])}
    return {"corr": corr, "resid_mean": float(resid.mean()), "resid_std": float(resid.std()),
           "n": int(len(priced)), "example": example}
