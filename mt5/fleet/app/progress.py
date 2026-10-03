"""How far an account is through its stage: profit against the target, the days counted on the firm's clock, the payout."""
import numpy as np

from mt5.fleet.app import floors, fmt, history
from portfolio.funded.rules import floors as rules

DAY = 86400


def day_of(server_time: int, offset: int, zone: str | None) -> int:
    """The firm's day a server-clock time belongs to, as the UTC epoch it began.

    Args:
        server_time: Server epoch of a deal.
        offset: Seconds the server clock is ahead of UTC (`floors.server_offset`).
        zone: The firm's daily-loss clock; None reads the server's own midnight.
    """
    if zone is None:
        return server_time // DAY * DAY - offset
    return floors.day_start(server_time - offset, zone)


def by_day(rows: list[dict], offset: int, zone: str | None) -> dict[int, float]:
    """The net result of every firm day that had a trade, from the deals of that day, balance operations left out."""
    days: dict[int, float] = {}
    for d in rows:
        if d["type"] != history.BALANCE_TYPE:
            key = day_of(d["time"], offset, zone)
            days[key] = days.get(key, 0.0) + d["profit"] + d["swap"] + d["commission"] + d["fee"]
    return days


def consistency(days: dict[int, float], stage: dict) -> dict | None:
    """The best day against the stage's consistency rule: `limit`, `ratio`, `ok`; None when it has none."""
    if not stage["consistency"] or not days:
        return None
    profits = np.array(list(days.values()))
    base = profits.sum() if stage["consistency_kind"] == "best_over_total" else profits[profits > 0].sum()
    return {"limit": stage["consistency"], "ratio": profits.max() / base if base > 0 else None,
            "ok": rules.consistency_ok(profits, stage) if base > 0 else None}


def payouts(rows: list[dict], first_trade: int | None, share: float | None, days: int | None,
            balance: float, size: float) -> dict:
    """The funded stage's payout: the last withdrawal, the next date and what is payable now.

    Args:
        rows: The account's deals since the stage began.
        first_trade: Server epoch of its first trade, from which the cycle counts before any payout.
        share: The trader's reward share as a fraction, None when the catalogue has none.
        days: The payout cycle in days, None when the catalogue has none.
        balance: The closed balance.
        size: The account's starting balance.

    Returns:
        `last` (server epoch, amount) or None, `next` (server epoch, approximate: the last payout
        — or the first trade — plus one cycle) or None, `payable` or None.
    """
    out = [d for d in rows if d["type"] == history.BALANCE_TYPE and d["profit"] < 0]
    last = max(out, key=lambda d: d["time"]) if out else None
    since = last["time"] if last else first_trade
    return {"last": (last["time"], -last["profit"]) if last else None,
            "next": since + days * DAY if days and since else None,
            "payable": max(balance - size, 0.0) * share if share is not None else None}


def reading(beat: dict, stage: dict, terms: dict, rows: list[dict], zone: str | None) -> dict:
    """One account's progress through its stage.

    Args:
        beat: FleetBeacon's JSON (`balance`, `deposit_time`, `server_time`, `written_gmt`).
        stage: `read.stage()`.
        terms: `read.terms()`.
        rows: The account's deals since it opened (`history.deals`).
        zone: The firm's daily-loss clock, None for the server's midnight.

    Returns:
        `funded`, `profit` (closed balance minus size), `target` (currency, None when funded),
        `done` (share of the target), `trading_days`, `profitable_days`, `min_days`, `days_kind`,
        `days_ok` (None when the catalogue has no minimum), `consistency` (`consistency()`), and
        for a funded stage `payout` (`payouts()`).
    """
    rows = [d for d in rows if d["time"] >= beat["deposit_time"]]
    days = by_day(rows, floors.server_offset(beat), zone)
    size, funded = stage["size"], stage["target"] == 0
    bar = (stage["profitable_pct"] or 0.0) * size
    # With a share, a profitable day reaches it; with none, any gain counts.
    stats = {"trading_days": len(days),
             "profitable_days": sum((p >= bar if bar else p > 0) for p in days.values())}
    profit = beat["balance"] - size
    first = min((t["open"] for t in history.trades(rows)), default=None)
    return {"funded": funded, "profit": profit, "target": None if funded else stage["target"] * size,
            "done": None if funded else profit / (stage["target"] * size), **stats,
            "min_days": stage["min_days"], "days_kind": stage["min_days_kind"],
            "days_ok": None if stage["min_days"] is None else rules.days_ok(stats, stage),
            "consistency": consistency(days, stage),
            "payout": payouts(rows, first, terms["reward_share"], terms["payout_days"], beat["balance"],
                              size) if funded else None}


def lines(prog: dict) -> list[str]:
    """A progress reading as the Spanish lines the Flota tab shows."""
    out = []
    if not prog["funded"]:
        out.append(f"Beneficio {fmt.money(prog['profit'])} de {fmt.money(prog['target'])} "
                   f"({fmt.pct(prog['done'])} del objetivo)")
    else:
        pay = prog["payout"]
        out.append("Último pago: " + (f"{fmt.day(pay['last'][0])} · {fmt.money(pay['last'][1])}" if pay["last"]
                                      else "ninguno todavía"))
        out.append(f"Próximo pago ≈ {fmt.day(pay['next'])} · a cobrar ahora ≈ {fmt.money(pay['payable'])}")
    if prog["min_days"] is None:
        out.append(f"Días: {prog['trading_days']} de trading, {prog['profitable_days']} rentables "
                   "(el catálogo no trae un mínimo)")
    else:
        kind = "rentables" if prog["days_kind"] == "profitable" else "de trading"
        have = prog["profitable_days"] if prog["days_kind"] == "profitable" else prog["trading_days"]
        out.append(f"Días {kind}: {have} (mínimo {prog['min_days']}) · "
                   f"{'cumplido' if prog['days_ok'] else 'sin cumplir'}")
    c = prog["consistency"]
    if c:
        out.append(f"Consistencia: mejor día {fmt.pct(c['ratio'])} (límite {fmt.pct(c['limit'], 0)}) · "
                   + ("sin dato" if c["ok"] is None else "se cumple" if c["ok"] else "NO se cumple"))
    return out
