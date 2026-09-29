"""MCP server over MetaTrader 5 under Wine: compile, backtest, compare with SQX, and read-only data.

Registered in the repo's .mcp.json as `mt5`, stdio. It has no tool that sends, modifies or
closes an order, on purpose (owner, 2026-09-27): trading is not this server's business.
"""
import json
import shutil
from pathlib import Path

import pandas as pd
from mcp.server.fastmcp import FastMCP

from core import trades as sqx_trades
from mt5 import compare, live, metaeditor, tester, wine

server = FastMCP("mt5")


def _sqx(path: str, strategy: str) -> pd.DataFrame:
    """SQX trades from an orderstocsv CSV, or from a harvest/export parquet filtered to one strategy."""
    p = Path(path)
    if p.suffix == ".csv":
        frame = sqx_trades.read(p)
    else:
        frame = pd.read_parquet(p)
        key = "strategy" if "strategy" in frame else "identity"
        frame = frame[frame[key] == strategy] if strategy else frame
    return frame.assign(Type=frame["Type"].astype(str)).reset_index(drop=True)


@server.tool()
def mt5_status() -> dict:
    """What is installed and running: Wine, the terminal, its data folder, the Windows Python."""
    out = {"wine": shutil.which("wine"), "prefix": str(wine.MT5_PREFIX),
           "terminal": wine.TERMINAL.exists(), "metaeditor": wine.METAEDITOR.exists(),
           "windows_python": wine.PYTHON.exists(), "terminal_running": wine.terminal_running()}
    if out["terminal"]:
        out["data_dir"] = str(wine.data_dir())
    return out


@server.tool()
def mt5_install_sqx_indicators() -> dict:
    """Copy SQX's Sq* indicators, then the project's set (mt5/indicators) over them, and compile. After an SQX update or a change there."""
    return metaeditor.sqx_indicators()


@server.tool()
def mt5_compile(source: str) -> dict:
    """Compile an EA source (.mq5 saved from SQX: Save > Source code > MetaTrader 5).

    Args:
        source: Linux path of the .mq5.
    """
    return metaeditor.expert(Path(source).expanduser())


@server.tool()
def mt5_backtest_start(source: str, symbol: str, timeframe: str, start: str, end: str,
                       model: str = "real_ticks", deposit: float = 100000,
                       leverage: int = 100) -> dict:
    """Compile an .mq5 and launch one Strategy Tester pass; returns at once with the run id.

    The terminal must be closed (the tester opens its own and shuts it at the end). Poll
    mt5_backtest_result(run) until its state is not "running".

    Args:
        source: Linux path of the .mq5.
        symbol: The terminal's symbol name, e.g. XAUUSD.
        timeframe: M1, M5, M15, M30, H1, H4, D1.
        start, end: YYYY-MM-DD, the window SQX used, to compare like with like.
        model: real_ticks, every_tick, ohlc_m1 or open_prices.
        deposit: Initial balance in USD.
        leverage: 100 means 1:100.
    """
    built = metaeditor.expert(Path(source).expanduser())
    if not built["ok"]:
        return {"state": "compile_failed", **built}
    return tester.start(built["expert"], symbol, timeframe, start, end, model, deposit, leverage)


@server.tool()
def mt5_backtest_result(run: str) -> dict:
    """The state of a run; when done, its report summary and the trades saved to parquet."""
    return tester.collect(run)


@server.tool()
def mt5_runs() -> list[dict]:
    """Every backtest run on disk, newest first, with whether it has been collected."""
    runs = sorted(tester.TESTS.glob("*/run.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return [{"run": p.parent.name, **json.loads(p.read_text()),
             "collected": (p.parent / "trades.parquet").exists()} for p in runs]


@server.tool()
def mt5_compare(run: str, sqx_trades_file: str, strategy: str = "", tolerance_minutes: float = 60,
                shift_hours: float = 0) -> dict:
    """Pair a collected MT5 run's trades with SQX's for the same window and measure the gap.

    Args:
        run: A collected run id.
        sqx_trades_file: orderstocsv CSV of one strategy, or a trades parquet of many.
        strategy: With a parquet, the strategy's name (or identity hash) to keep.
        tolerance_minutes: Largest entry-time gap still called the same trade.
        shift_hours: Added to SQX's times to put them in the MT5 server's clock
            (knowhow export/feed-clock-timezones: SQX stamps each feed in its broker's zone).
    """
    folder = tester.TESTS / run
    meta = json.loads((folder / "run.json").read_text())
    mt5_t = compare.window(pd.read_parquet(folder / "trades.parquet"), meta["start"], meta["end"])
    sqx = _sqx(sqx_trades_file, strategy)
    sqx[["Open time", "Close time"]] += pd.Timedelta(hours=shift_hours)
    sqx = compare.window(sqx, meta["start"], meta["end"])
    pairs = compare.pair(sqx, mt5_t, tolerance_minutes)
    pairs.to_parquet(folder / "pairs.parquet")
    return {**compare.gap(pairs, mt5_t), "pairs_file": str(folder / "pairs.parquet")}


@server.tool()
def mt5_account() -> dict:
    """The logged-in account and the terminal: login, server, balance, equity, leverage, build."""
    return {"account": live.ask("account"), "terminal": live.ask("terminal")}


@server.tool()
def mt5_symbols(group: str = "*") -> list[str]:
    """Symbol names the server offers; group is MT5's filter, e.g. '*USD*' or '*,!*EUR*'."""
    return live.ask("symbols", {"group": group})


@server.tool()
def mt5_symbol(symbol: str) -> dict:
    """One symbol's contract: digits, point, tick value and size, contract size, swaps, current spread."""
    return live.ask("symbol", {"symbol": symbol})


@server.tool()
def mt5_bars(symbol: str, timeframe: str, start: str, end: str) -> dict:
    """Download bars to a parquet under AlgoData/mt5/bars; returns the file and its span."""
    return live.series("bars", symbol, start, end, timeframe)


@server.tool()
def mt5_ticks(symbol: str, start: str, end: str) -> dict:
    """Download every tick (bid, ask, last, flags) to a parquet under AlgoData/mt5/ticks."""
    return live.series("ticks", symbol, start, end)


@server.tool()
def mt5_positions() -> dict:
    """Open positions and pending orders of the logged-in account. Read-only."""
    return {"positions": live.ask("positions"), "orders": live.ask("orders")}


@server.tool()
def mt5_history(start: str, end: str) -> list[dict]:
    """Deals of the logged-in account between two dates, YYYY-MM-DD. Read-only."""
    return live.ask("history", {"start": start, "end": end})


if __name__ == "__main__":
    server.run()
