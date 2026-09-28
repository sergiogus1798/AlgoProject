"""Run one Strategy Tester pass: write its ini, start the terminal detached, and collect the report."""
import json
import os
import shutil
import subprocess
from pathlib import Path

from core.paths import MT5_DATA
from mt5 import report, wine

# The tester's Model= codes (MT5 help, "Platform Start"). real_ticks is what a live EA would see.
MODELS = {"every_tick": 0, "ohlc_m1": 1, "open_prices": 2, "real_ticks": 4}
TESTS = MT5_DATA / "tests"


def _ini(expert: str, symbol: str, timeframe: str, start: str, end: str, model: str,
         deposit: float, leverage: int, report_name: str) -> str:
    """The [Tester] section. Dates are YYYY-MM-DD; the tester wants YYYY.MM.DD."""
    lines = ["[Tester]", f"Expert={expert}", f"Symbol={symbol}", f"Period={timeframe}",
             f"Model={MODELS[model]}", "ExecutionMode=0", "Optimization=0", "ForwardMode=0",
             f"FromDate={start.replace('-', '.')}", f"ToDate={end.replace('-', '.')}",
             f"Deposit={deposit:g}", "Currency=USD", f"Leverage={leverage}",
             f"Report=reports\\{report_name}", "ReplaceReport=1", "ShutdownTerminal=1",
             "Visual=0", "UseLocal=1", "UseRemote=0", "UseCloud=0"]
    return "\r\n".join(lines) + "\r\n"


def start(expert: str, symbol: str, timeframe: str, start_date: str, end_date: str,
          model: str, deposit: float, leverage: int) -> dict:
    """Launch one backtest and return at once; the terminal shuts itself down when it ends.

    Args:
        expert: Compiled EA relative to MQL5/Experts, as compile.expert() names it.
        symbol, timeframe: The terminal's names, e.g. XAUUSD and H1.
        start_date, end_date: YYYY-MM-DD.
        model: A key of MODELS.
        deposit: Initial balance in USD.
        leverage: 100 means 1:100.

    Returns:
        {"run": its id, "dir": where the result will land}.
    """
    if wine.terminal_running():
        raise SystemExit("the MT5 terminal is open: the tester needs it closed (one terminal per data folder)")
    stem = Path(expert.replace("\\", "/")).stem
    run = f"{stem}_{symbol}_{timeframe}_{start_date}_{end_date}_{model}"
    folder = TESTS / run
    folder.mkdir(parents=True, exist_ok=True)
    ini = folder / "tester.ini"
    ini.write_text(_ini(expert, symbol, timeframe, start_date, end_date, model, deposit, leverage,
                        run), encoding="utf-16")
    (wine.data_dir() / "reports" / f"{run}.htm").unlink(missing_ok=True)
    with open(folder / "terminal.out", "w") as out:
        proc = subprocess.Popen(["wine", str(wine.TERMINAL), f"/config:{wine.windows(ini)}"],
                                env=wine.env(), stdout=out, stderr=subprocess.STDOUT,
                                start_new_session=True)
    (folder / "run.json").write_text(json.dumps(
        {"pid": proc.pid, "expert": expert, "symbol": symbol, "timeframe": timeframe,
         "start": start_date, "end": end_date, "model": model, "deposit": deposit,
         "leverage": leverage}, indent=1))
    return {"run": run, "dir": str(folder)}


def _alive(pid: int) -> bool:
    """Whether the wine process that started the terminal is still there."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


def collect(run: str) -> dict:
    """The result of a run: still running, failed, or its summary with the trades saved to parquet.

    Args:
        run: The id start() returned.

    Returns:
        {"state": "running" | "no_report" | "done", ...}; on done, the summary and the paths
        of deals.parquet and trades.parquet in the run folder.
    """
    folder = TESTS / run
    meta = json.loads((folder / "run.json").read_text())
    htm = wine.data_dir() / "reports" / f"{run}.htm"
    if _alive(meta["pid"]) or wine.terminal_running():
        return {"state": "running", "run": run}
    if not htm.exists():
        return {"state": "no_report", "run": run,
                "hint": "the terminal ended without a report: see its log in the data folder's "
                        "tester/logs, and whether the symbol and dates have history"}
    shutil.copy2(htm, folder / "report.htm")
    summary, deals = report.read(folder / "report.htm")
    trades = report.trades(deals)
    deals.to_parquet(folder / "deals.parquet")
    trades.to_parquet(folder / "trades.parquet")
    (folder / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False))
    return {"state": "done", **meta, "summary": summary, "trades": len(trades),
            "trades_file": str(folder / "trades.parquet"), "dir": str(folder)}
