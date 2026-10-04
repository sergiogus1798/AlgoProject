"""The swap each trade paid, modelled: nights crossed (triple night counted) × the card's rate.

The export has no swap column (`knowhow/costs/swap-types.md`), so the only other estimate is
the reconciliation residual, which mixes swap with rounding. This models it per trade instead.
"""

import numpy as np
import pandas as pd

from core import assetdata

WEEKDAY = {"MONDAY": 0, "TUESDAY": 1, "WEDNESDAY": 2, "THURSDAY": 3, "FRIDAY": 4,
           "SATURDAY": 5, "SUNDAY": 6}
EPOCH_WEEKDAY = 3   # 1970-01-01 was a Thursday


def charged_nights(opened: pd.Series, closed: pd.Series, swap: dict) -> np.ndarray:
    """Nights charged per trade: every rollover crossed counts 1, the triple-swap night 3.

    Args:
        opened: Open times (the feed's clock).
        closed: Close times.
        swap: `asset["swap"]`: `triple_swap_on` (weekday name or "NEVER") and `rollout_hour`
            ("23:00"). The rollover at `rollout_hour` of day D is charged as D's night.

    Returns:
        Float array, ≥ 0. A trade that opens and closes inside one day-cycle pays 0.
        🤔 A weekend crossing is charged only as the nights the calendar shows (Friday's
        rollover plus the Saturday and Sunday ones), the way a 7-day swap schedule would.
    """
    shift = pd.Timedelta(hours=int(swap["rollout_hour"].split(":")[0]),
                         minutes=int(swap["rollout_hour"].split(":")[1]))
    d0 = ((opened - shift).dt.floor("D") - pd.Timestamp(0)).dt.days.to_numpy()
    d1 = ((closed - shift).dt.floor("D") - pd.Timestamp(0)).dt.days.to_numpy()
    n = (d1 - d0).clip(min=0)
    day = swap["triple_swap_on"].upper()
    if day not in WEEKDAY:   # "NEVER" or any unknown value: no triple night
        return n.astype(float)
    r = (WEEKDAY[day] - EPOCH_WEEKDAY) % 7   # days d (since epoch) with d % 7 == r are triple days
    below = lambda x: -((r - x) // 7)         # how many such d are < x
    triples = (below(d1 + 1) - below(d0 + 1)).clip(min=0)   # rollovers of days d0+1 .. d1
    return (n + 2 * triples).astype(float)


def tick_step(asset: dict) -> float:
    """SQX's `tickStep`, the unit swap points are written in (not `tick_size`).

    🤔 The card holds no tickStep: on forex it is tick_size / 10, elsewhere equal to it
    (`knowhow/costs/swap-types.md`, checked on 9 instruments). Only the `points` type uses it.
    """
    tick = asset["instrument"]["tick_size"]
    return tick / 10 if asset["class"] == "forex" else tick


def night_money(asset: dict, size: np.ndarray | float, open_price: np.ndarray | float,
                side: pd.Series, rate_long: float, rate_short: float) -> np.ndarray:
    """One night's swap per trade in account currency, signed (positive = credit).

    Args:
        asset: `costs.asset_for()`'s dict; its class's `sqx_type` picks the formula.
        size: Lots per trade.
        open_price: Open prices (only the `percent` type reads them).
        side: +1 long, -1 short.
        rate_long: Long rate in the type's own unit (points, % annual, money per lot).
        rate_short: Short rate.
    """
    pv = asset["instrument"]["point_value"]
    rate = np.where(np.asarray(side) > 0, rate_long, rate_short)
    kind = assetdata.schema(asset)["swap"]["sqx_type"]
    if kind == "points":
        return size * pv * tick_step(asset) * rate
    if kind == "percent":
        return size * pv * open_price * rate / 100 / 360
    return size * rate   # "money"


def swap_cost(trades: pd.DataFrame, asset: dict, rate_long: float | None = None,
              rate_short: float | None = None) -> pd.Series:
    """The swap COST of each trade (positive = paid), at the card's rates unless given.

    Args:
        trades: Priced trades with `Open time`, `Close time`, `Size`, `Open price`, `direction`.
        asset: `costs.asset_for()`'s dict.
        rate_long, rate_short: Override the card's `swap_long`/`swap_short` `use` (e.g. with
            `sqx_now`, to read what SQX itself charged).
    """
    use = asset["costs"]
    rl = use["swap_long"]["use"] if rate_long is None else rate_long
    rs = use["swap_short"]["use"] if rate_short is None else rate_short
    nights = charged_nights(trades["Open time"], trades["Close time"], asset["swap"])
    one = night_money(asset, trades["Size"].to_numpy(float), trades["Open price"].to_numpy(float),
                      trades["direction"], rl, rs)
    return pd.Series(-nights * one, index=trades.index)


def sqx_now(asset: dict) -> tuple[float, float] | None:
    """The swap the master carried (`sqx_now`) as (long, short) numbers, or None when unknown."""
    got = []
    for k in ("swap_long", "swap_short"):
        v = asset["costs"][k].get("sqx_now")
        v = v.get("value") if isinstance(v, dict) else v
        if v is None:
            return None
        got.append(float(v))
    return got[0], got[1]


def reconcile(priced: pd.DataFrame, asset: dict) -> dict:
    """The modelled swap against the reconciliation residual (what SQX charged beyond price).

    The residual `Profit/Loss + commission - price_pnl` is swap plus rounding, so it should
    sit near the swap SQX itself charged. That is the project's rates (`sqx_now`, the master's
    today), not necessarily the card's `use`, which is the owner's worst-case swap of today.

    Returns:
        resid_mean and its standard error; the modelled mean swap (money, positive = credit,
        the residual's sign) at the card's rates and at `sqx_now` (None when unknown);
        `agrees` = the sqx_now model lies within 2 standard errors of the residual (None when
        unknown); and `resid_by_nights`, the residual's mean for 0 nights and for ≥ 1 night,
        which isolates the swap whatever else the residual holds.
    """
    resid = priced["Profit/Loss"] + priced["commission_cost"] - priced["price_pnl"]
    se = float(resid.std() / np.sqrt(len(resid))) if len(resid) > 1 else float("nan")
    now = sqx_now(asset)
    model_now = float(-swap_cost(priced, asset, *now).mean()) + 0.0 if now else None
    held = priced["nights"] > 0
    return {"resid_mean": float(resid.mean()), "resid_se": se,
            "model_card": float(-priced["swap_cost"].mean()), "model_sqx_now": model_now,
            "agrees": None if model_now is None else bool(abs(resid.mean() - model_now) <= 2 * se),
            "resid_no_nights": float(resid[~held].mean()) if (~held).any() else float("nan"),
            "resid_nights": float(resid[held].mean()) if held.any() else float("nan"),
            "mean_nights": float(priced["nights"].mean())}
