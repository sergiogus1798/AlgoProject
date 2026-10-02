"""Read-only queries to the running MT5 terminal; runs under the Windows Python inside the Wine prefix.

Called by mt5/live.py as `python.exe query.py <verb> <json args>`. Prints one JSON line after
MARK, or writes a CSV where the args say. Never sends, modifies or closes an order: the
MetaTrader5 functions that trade are not called anywhere in this file.
"""
import csv
import datetime as dt
import json
import sys
import time

import MetaTrader5 as mt5

MARK = "@@JSON@@"


def _stamp(text: str) -> dt.datetime:
    """YYYY-MM-DD[ HH:MM] as UTC, which is how the package reads naive-free datetimes."""
    return dt.datetime.fromisoformat(text).replace(tzinfo=dt.timezone.utc)


def _rows(items: tuple) -> list[dict]:
    """Named tuples the package returns, as dicts."""
    return [i._asdict() for i in items or ()]


def _csv(array: object, path: str) -> int:
    """Write a numpy structured array to CSV; returns the row count."""
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(array.dtype.names)
        w.writerows(array.tolist())
    return len(array)


FULL_WEEK = 100      # H1 bars in a traded week: 120 whole; a server's sparse years give ~5


def _full_week(symbol: str, day: dt.datetime) -> bool:
    """Whether the server has a whole week of H1 bars from `day`, not a daily sprinkle: the
    tester reads such years as «History Quality 22 %» and trades nothing in them. H1, not M1:
    the terminal serves M1 only for its last «max bars», one row for anything older. A symbol
    not synced yet answers «Call failed» (None) for a while, so it is asked again."""
    for _ in range(10):
        rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_H1, day, day + dt.timedelta(days=7))
        if rates is not None:
            return len(rates) >= FULL_WEEK
        time.sleep(1)
    return False


def first_full(symbol: str) -> str | None:
    """The first month the server has whole weeks of `symbol`, found by halving the months
    between its first monthly bar and now — the monthly bars reach further back than the
    tester can trade (🔬 2026-09-30: USDJPY.h on Hantec, MN1 from 2008-07, whole H1 weeks and
    so the tester's trades from 2022)."""
    mt5.symbol_select(symbol, True)
    monthly = None
    for _ in range(20):
        monthly = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_MN1, 0, 1000)
        if monthly is not None and len(monthly):
            break
        time.sleep(1)
    if monthly is None or not len(monthly):
        return None
    months = [dt.datetime.fromtimestamp(int(m["time"]), dt.timezone.utc) for m in monthly]
    lo, hi = 0, len(months) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if _full_week(symbol, months[mid] + dt.timedelta(days=7)):    # skip a month's first days
            hi = mid
        else:
            lo = mid + 1
    return months[lo].date().isoformat()


def run(verb: str, a: dict) -> object:
    """Dispatch one read-only verb.

    Args:
        verb: account, terminal, symbols, symbol, bars, first, ticks, positions, orders, history.
        a: The verb's arguments.

    Returns:
        Something json.dumps can write.
    """
    if verb == "account":
        return mt5.account_info()._asdict()
    if verb == "terminal":
        return {**mt5.terminal_info()._asdict(), "version": mt5.version()}
    if verb == "symbols":
        return [s.name for s in mt5.symbols_get(a.get("group", "*"))]
    if verb == "symbol":
        mt5.symbol_select(a["symbol"], True)
        tick = mt5.symbol_info_tick(a["symbol"])
        return {**mt5.symbol_info(a["symbol"])._asdict(), "tick": tick._asdict() if tick else None}
    if verb == "bars":
        tf = getattr(mt5, "TIMEFRAME_" + a["timeframe"])
        rates = mt5.copy_rates_range(a["symbol"], tf, _stamp(a["start"]), _stamp(a["end"]))
        return {"rows": _csv(rates, a["out"]) if rates is not None else 0, "error": mt5.last_error()}
    if verb == "first":         # how far back the server has whole weeks: what the tester trades
        return {"first": first_full(a["symbol"]), "error": mt5.last_error()}
    if verb == "ticks":
        ticks = mt5.copy_ticks_range(a["symbol"], _stamp(a["start"]), _stamp(a["end"]),
                                     mt5.COPY_TICKS_ALL)
        return {"rows": _csv(ticks, a["out"]) if ticks is not None else 0, "error": mt5.last_error()}
    if verb == "positions":
        return _rows(mt5.positions_get())
    if verb == "orders":
        return _rows(mt5.orders_get())
    if verb == "history":
        return _rows(mt5.history_deals_get(_stamp(a["start"]), _stamp(a["end"])))
    raise SystemExit(f"unknown verb {verb}")


def main() -> None:
    """Attach to the terminal of this prefix, answer, detach.

    `login` and `server` among the args log the open terminal into that account with the
    password it has saved: none travels here. The terminal is started beforehand, detached
    (`mt5.wine.open_terminal`): one this package started would hold our stdout open.
    """
    args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    if not mt5.initialize(**{k: args[k] for k in ("path", "login", "server") if args.get(k)}):
        print(MARK + json.dumps({"error": f"initialize failed: {mt5.last_error()}"}))
        return
    out = run(sys.argv[1], args)
    mt5.shutdown()
    print(MARK + json.dumps(out, default=str))


if __name__ == "__main__":
    main()
