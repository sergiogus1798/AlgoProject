"""Each broker's own commission as a %, refreshed weekly from the latest close.

Owner, 2026-09-29 — corrects the earlier "max broker per segment" default: for a `no_forex`
asset the whole SQX workflow (build and every retest) prices at Darwinex's own `%`, written
once with `core.assetwrite.set_cost` and never recomputed per segment. What this module still
does is the OTHER half of the 2026-09-29 broker table: every confirmed broker's own figure,
converted to a percentage AT TODAY'S PRICE so a `$/lot` broker (Infinox) and a `%` broker
(Darwinex, FTMO) read on the same scale. That percentage is `pct_now`, read only by step 26
(MT5 validation on each firm's feed) and by `weeklyReconciler`'s SQX-vs-live check — never by
an SQX workflow task, which prices at `costs.commission.use` instead (`assets/RULES.md`).
"""

import sys

from core import barstore
from core.assetdata import load, symbols
from core.assetwrite import set_brokers
from core.paths import bar_source


def commission_pct(method: str, value: float, price: float, point_value: float) -> float:
    """One broker's round-turn commission as a percentage of notional, at a given price.

    Args:
        method: `"SizeBased"` (value is $/lot) or `"PercentageBased"` (value is already a %).
        value: The broker's own figure, in its own unit.
        price: The instrument's price to convert a $/lot figure at. Unused when `method` is
            `"PercentageBased"`, so `None` is fine there.
        point_value: `$` per 1.0 of price and 1.0 of lot (the asset's `instrument.point_value`).

    Returns:
        A percentage of notional, comparable across methods.
    """
    return value if method == "PercentageBased" else value / (price * point_value) * 100


def broker_pct(asset: str, broker: str) -> float:
    """One broker's own commission on this asset, as the % `--refresh` last stored.

    Args:
        asset: Asset name.
        broker: Key of `costs.commission.brokers`.

    Returns:
        `pct_now` — refreshed weekly, from the last close, by `python3 -m core.commission
        --refresh`. `KeyError` when that broker has never been confirmed or never refreshed:
        nothing to read is worse hidden as a guessed 0.
    """
    return load(asset)["costs"]["commission"]["brokers"][broker]["pct_now"]


def refresh() -> dict:
    """Recompute every confirmed broker's `pct_now` from the latest close, and write it.

    Returns:
        `{asset: {broker: pct_now}}`, only the brokers this run could price — a `SizeBased`
        broker on a feed with no bars synced yet (the five indices) is left untouched rather
        than guessed.
    """
    out = {}
    for asset in symbols():
        data = load(asset)
        brokers = data["costs"]["commission"].get("brokers") or {}
        confirmed = {n: b for n, b in brokers.items() if b.get("confirmed")}
        if not confirmed:
            continue
        feed = data["sqx_symbol"]
        price, when = None, None
        if bar_source(feed).exists():
            bars = barstore.source(feed, columns=["Close"])
            price, when = float(bars["Close"].iloc[-1]), bars.index[-1].date().isoformat()
        point_value = data["instrument"]["point_value"]
        priced = {}
        for name, b in confirmed.items():
            if b["method"] == "SizeBased" and price is None:
                continue
            b["pct_now"] = round(commission_pct(b["method"], b["value"], price, point_value), 6)
            b["price_now"], b["price_date"] = price, when
            priced[name] = b["pct_now"]
        if priced:
            set_brokers(asset, brokers)
            out[asset] = priced
    return out


def main() -> None:
    """`--refresh`: recompute every asset's broker percentages and print what changed."""
    if "--refresh" not in sys.argv:
        print("uso: python3 -m core.commission --refresh")
        sys.exit(1)
    for asset, brokers in refresh().items():
        print(f"{asset}: " + ", ".join(f"{n} {v}%" for n, v in brokers.items()))


if __name__ == "__main__":
    main()
