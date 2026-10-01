"""The worst swap of the funded accounts, side by side, read live from each firm's MT5 server."""

import sqlite3

from core.assetdata import load
from core.paths import MASTER, MT5_ACCOUNTS
from mt5 import live

REGISTRY = MASTER / "user" / "data" / "data.db"


def _usd(spec: dict, points: float) -> float:
    """A swap in the server's points as USD per lot per night."""
    return points * spec["trade_tick_value"] / spec["trade_tick_size"] * spec["point"]


def _pct(spec: dict, points: float, price: float) -> float:
    """A swap in the server's points as a % ANNUAL of that broker's own notional (SQX ÷100 ÷360)."""
    return _usd(spec, points) / (price * spec["trade_tick_value"] / spec["trade_tick_size"]) * 36000


def _tick_step(feed: str) -> tuple[float, float]:
    """The SQX instrument's pointValue and tickStep: SQX charges `size × pointValue × tickStep × points`."""
    with sqlite3.connect(f"file:{REGISTRY}?mode=ro", uri=True) as db:
        return db.execute("SELECT I.POINTVALUE, I.TICKSTEP FROM DATA D JOIN INSTRUMENTS I "
                          "ON I.INSTRUMENT = D.INSTRUMENT WHERE D.SYMBOL = ?", (feed,)).fetchone()


def worst(symbol: str, firms: tuple = ("ftmo", "hantec")) -> dict:
    """The most expensive swap of the firms, per side, in the unit the asset's class declares.

    Owner, 2026-10-01: «el peor caso de ambos brokers, para todo». Each side is taken from
    whichever firm charges it more today, so it is a figure of today: rates and, on crude, the
    futures roll move it.

    Args:
        symbol: Asset name; its `mt5:` block names the symbol at each firm.
        firms: Keys of `config/machine.yaml` `mt5_accounts` and of the asset's `mt5:`.

    Returns:
        {"long", "short"} in SQX points per night (forex, priced at the SQX instrument's
        pointValue × tickStep so SQX charges exactly that USD) or % annual on each firm's own
        notional at today's price (everything else — their contract sizes differ); plus
        "from" {side: firm} and "raw" {firm: (long, short)} in the servers' points.

    Raises:
        SystemExit: A firm the asset has no MT5 symbol for, or a server with no price for it.
    """
    asset = load(symbol)
    specs = {}
    for firm in firms:
        name = (asset.get("mt5") or {}).get(firm)
        if not name:
            raise SystemExit(f"{symbol}: no MT5 symbol for {firm} in its `mt5:` block")
        specs[firm] = live.ask("symbol", {"symbol": name}, MT5_ACCOUNTS[firm])
    out = {"from": {}, "raw": {f: (s["swap_long"], s["swap_short"]) for f, s in specs.items()}}
    pv, step = _tick_step(asset["sqx_symbol"]) if asset["class"] == "forex" else (None, None)
    for side in ("long", "short"):
        cost = {}
        for firm, s in specs.items():
            if asset["class"] == "forex":
                cost[firm] = _usd(s, s[f"swap_{side}"]) / (pv * step)
            else:
                price = s["bid"] or s["session_close"]
                if not price:
                    raise SystemExit(f"{symbol}: {firm} quotes no price now — retry with the market open")
                cost[firm] = _pct(s, s[f"swap_{side}"], price)
        firm = min(cost, key=cost.get)
        out[side], out["from"][side] = round(cost[firm], 2), firm
    return out
