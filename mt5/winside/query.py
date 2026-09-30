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
    if verb == "first":         # the server's history depth: its first monthly bar
        mt5.symbol_select(a["symbol"], True)
        for _ in range(20):     # a symbol just selected answers «Call failed» until it syncs
            rates = mt5.copy_rates_from_pos(a["symbol"], mt5.TIMEFRAME_MN1, 0, 1000)
            if rates is not None and len(rates):
                break
            time.sleep(1)
        return {"first": (dt.datetime.fromtimestamp(int(rates[0]["time"]), dt.timezone.utc)
                          .date().isoformat() if rates is not None and len(rates) else None),
                "error": mt5.last_error()}
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
