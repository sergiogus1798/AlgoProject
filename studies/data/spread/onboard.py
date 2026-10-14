#!/usr/bin/env python3
"""Recompute the spreads and slippage of existing cards by the funded-firms method.

The widest funded firm's time-weighted % of price times the tramo's mean price, slippage at 35 %
of it (`funded.py`; assets/RULES.md). Prints the plan; with --write it updates each card through
`core.assetwrite` — the only module of this study that writes `assets/`, and only when the owner
asked for it (the `/asset-onboard` skill). This command does not read Darwinex (owner, 2026-10-14).
"""

import argparse

import pandas as pd

from core import assetwrite
from core.assetdata import load, symbols
from studies.data.spread import funded, inputs


def apply_funded(names: list[str], cfg: dict, write: bool) -> None:
    """The funded-firms method (`funded.py`) for existing cards: print each plan, write it with `write`.

    Only spreads and slippage are written, through `core.assetwrite`;
    a card whose name differs from its `symbol` (the XAUUSD_SYN01 twin) or with no funded
    ticks is skipped and said so.
    """
    factor, share = cfg["safety"]["factor"], cfg["safety"]["slippage_share"]
    day = pd.Timestamp.now().strftime("%Y-%m-%d")
    for s in names:
        origin = load(s)["symbol"]
        if origin != s:
            print(f"{s}: gemela de {origin}, no se recalcula")
            continue
        try:
            p = funded.plan(s, factor, share)
        except ValueError as e:
            print(e)
            continue
        print(
            f"{s}: {funded.NAMES[p['firm']]} {p['pct'] * 100:.4f} %  {p['spreads']}  {p['slippage']}"
        )
        if not write:
            continue
        why = funded.whys(p, day, share)
        for field, v in {**p["spreads"], **p["slippage"]}.items():
            assetwrite.set_cost(s, field, float(v), why[field])


def main() -> None:
    """Plan every card's (or --symbol's) spreads and, with --write, put them in `assets/`."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--symbol", help="e.g. EURGBP; absent means every card")
    ap.add_argument(
        "--write", action="store_true", help="write it; without it, only print"
    )
    a = ap.parse_args()
    apply_funded(
        [a.symbol] if a.symbol else sorted(symbols()), inputs.config([]), a.write
    )
    if not a.write:
        print("\n(sin escribir: --write para aplicarlo)")


if __name__ == "__main__":
    main()
