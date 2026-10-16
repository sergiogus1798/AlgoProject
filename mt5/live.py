"""Ask the running MT5 terminal read-only questions through the Windows Python in its Wine prefix."""

import json
import time
from pathlib import Path
from typing import Any

import pandas as pd

from core.paths import MT5_DATA
from mt5 import wine

QUERY = Path(__file__).resolve().parent / "winside" / "query.py"
MARK = "@@JSON@@"


def ask(verb: str, args: dict | None = None, account: dict | None = None) -> Any:
    """Run one verb of winside/query.py and return its JSON answer.

    Args:
        verb: account, terminal, symbols, symbol, bars, ticks, positions, orders, history.
        args: The verb's arguments, as winside/query.py reads them.
        account: `{login, server}` of `core.paths.MT5_ACCOUNTS`: the terminal is opened when
            closed (`wine.open_terminal`) and logged into it with its saved password. None
            asks whatever account the open terminal holds.

    Returns:
        The decoded answer. Without `account` the terminal must be open and logged in.
    """
    if account and not wine.open_terminal():
        raise SystemExit("el terminal de MT5 no arrancó")
    args = {**(args or {}), **(account or {})}
    # 🔬 2026-10-16: the first login of a just-started terminal answers "Authorization
    # failed" (-6) and the same call a minute later logs in; three tries, then the error
    for attempt in range(3):
        proc = wine.run(
            wine.PYTHON, [wine.windows(QUERY), verb, json.dumps(args)], timeout=900
        )
        line = next(
            (ln for ln in proc.stdout.splitlines() if ln.startswith(MARK)), None
        )
        if line is None:
            raise SystemExit(
                f"no answer from the Windows Python:\n{proc.stdout[-2000:]}\n{proc.stderr[-2000:]}"
            )
        answer = json.loads(line[len(MARK) :])
        error = answer.get("error", "") if isinstance(answer, dict) else ""
        if "Authorization failed" not in str(error) or attempt == 2:
            return answer
        time.sleep(30)
    return answer


def series(
    verb: str,
    symbol: str,
    start: str,
    end: str,
    timeframe: str = "",
    account: dict | None = None,
) -> dict[str, Any]:
    """Pull bars or ticks for a window into a parquet under MT5_DATA.

    Args:
        verb: bars or ticks.
        symbol: The terminal's symbol name.
        start, end: YYYY-MM-DD or YYYY-MM-DD HH:MM, in the server's clock.
        timeframe: M1, M5, M15, M30, H1, H4, D1… for bars; empty for ticks.
        account: `ask`'s `account`: log the terminal into it first; None keeps the open one.

    Returns:
        {"rows", "file", "first", "last"}; time columns become datetimes.
    """
    folder = MT5_DATA / verb / symbol
    folder.mkdir(parents=True, exist_ok=True)
    stem = f"{timeframe + '_' if timeframe else ''}{start[:10]}_{end[:10]}"
    csv = folder / f"{stem}.csv"
    answer = ask(
        verb,
        {
            "symbol": symbol,
            "timeframe": timeframe,
            "start": start,
            "end": end,
            "out": wine.windows(csv),
        },
        account,
    )
    if not answer.get("rows"):  # a failed initialize answers with "error" alone
        return {"rows": 0, "error": answer.get("error", "")}
    frame = pd.read_csv(csv)
    frame["time"] = pd.to_datetime(frame["time"], unit="s")
    if "time_msc" in frame:
        frame["time_msc"] = pd.to_datetime(frame["time_msc"], unit="ms")
    out = csv.with_suffix(".parquet")
    frame.to_parquet(out)
    csv.unlink()
    return {
        "rows": len(frame),
        "file": str(out),
        "first": str(frame["time"].iloc[0]),
        "last": str(frame["time"].iloc[-1]),
    }
