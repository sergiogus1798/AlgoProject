"""The per-market controls of §7.1: aligned prices, the point value against the card, defective bars, a complete cost card."""

from typing import TypedDict

import numpy as np
import pandas as pd

from core import assetcheck, assetdata
from engines.market import reprice
from engines.market.calibrate import atr
from studies.transfer.crossmarket.travel import cells, sizing


def card(feed: str, segment: str) -> tuple[reprice.Costs | None, str]:
    """The market's cost card at one segment, or why there is none.

    Args:
        feed: SQX feed name.
        segment: "build", "oos1" or "oos2".

    Returns:
        (`reprice.costs`, "") or (None, reason): no asset file declares the feed, its card has
        no `price_rounding` (the repricer refuses it), or it still has a field the owner has
        not decided.
    """
    owner = assetdata.symbol_for(feed)
    if not owner:
        return None, "no_cost_card"
    late = assetcheck.pending(assetdata.load(owner))
    if late:
        return None, "cost_card_pending: " + ", ".join(late)
    try:
        return reprice.costs(feed, segment), ""
    except ValueError:  # no `price_rounding` on the card: the repricer refuses it
        return None, "cost_card_pending: price_rounding"


class Check(TypedDict):
    """§7.1 on one market: validity and why not, the fill error, the point value on the card and fitted, and the flat-bar share."""

    market: str
    valid: bool
    invalid_reason: str
    fill_error: float
    point_value_card: float
    point_value_fit: float
    point_value_gap: float
    flat_bars: float


def check(
    feed: str,
    trades: pd.DataFrame,
    bars: pd.DataFrame,
    costs: reprice.Costs,
    margin: float,
    flat_fraction: float,
    max_fill_error: float,
    period: int,
) -> Check:
    """§7.1 on one market, from the trades of EVERY strategy pooled and none judged alone.

    Args:
        feed: SQX feed name.
        trades: Every trade of the export on this market, within its own window; `Type`,
            `Open time`, `Close time`, `Open price`, `Close price`, `Size`, `Profit/Loss`.
        bars: The market's bars cut to its own window.
        costs: The card's, as `card()` returned it.
        margin: travel.validity.point_value_margin.
        flat_fraction: travel.validity.flat_atr_fraction.
        max_fill_error: travel.validity.max_fill_error, in median-ATR units.
        period: The doctrine's ATRPeriod.

    Returns:
        `market`, `valid`, `invalid_reason` (empty when valid), `fill_error` (the median gap
        between the recorded fills and the bar opens, side-signed, in
        median-ATR units), `point_value_card`, `point_value_fit` (the slope of P/L on side x move x
        size), `point_value_gap` (fit / card - 1) and `flat_bars` (share of bars below the
        fraction; excluded from sizing, not a reason to refuse the market). NaN where the
        market has no trade to measure.
    """
    held = cells.occupancy(trades, bars)
    mine = trades.loc[held.index]
    side = np.where(mine["Type"].astype(str) == "Buy", 1.0, -1.0)
    unit = float(
        np.nanmedian(atr(bars) / bars["Close"].to_numpy())
    )  # median ATR as a share of price
    scale = unit * float(bars["Open"].median())
    opened = (
        side
        * (mine["Open price"].to_numpy() - bars["Open"].to_numpy()[held["entry"]])
        / scale
    )
    closed = (
        side
        * (mine["Close price"].to_numpy() - bars["Open"].to_numpy()[held["exit"]])
        / scale
    )
    error = (
        max(abs(float(np.median(opened))), abs(float(np.median(closed))))
        if len(held)
        else np.nan
    )
    move = (
        side
        * (mine["Close price"] - mine["Open price"]).to_numpy()
        * mine["Size"].to_numpy()
    )
    fit = (
        float(np.polyfit(move, mine["Profit/Loss"].to_numpy(), 1)[0])
        if len(held) > 2
        else np.nan
    )
    gap = fit / costs["point_value"] - 1
    atr_ = sizing.entry_atr(bars, period)
    why = ([f"fill_mismatch {error:.3g} ATR"] if error > max_fill_error else []) + (
        [f"point_value {gap:+.1%}"] if abs(gap) > margin else []
    )
    return Check(
        market=feed,
        valid=not why,
        invalid_reason="; ".join(why),
        fill_error=error,
        point_value_card=costs["point_value"],
        point_value_fit=fit,
        point_value_gap=gap,
        flat_bars=float(np.mean(atr_ <= flat_fraction * np.nanmedian(atr_))),
    )
