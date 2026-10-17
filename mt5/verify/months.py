"""The M1 bars per month the Strategy Tester walks for one firm's symbol, from a short probe pass."""

import json
import time
from pathlib import Path

from core.paths import MT5_DATA
from mt5 import metaeditor, tester, wine
from mt5.newsfilter import testerfile

CACHE = MT5_DATA / "months"
SOURCE = Path(__file__).parent / "mql" / "AlgoProbeMonths.mq5"
OUT = "AlgoProbeMonths.csv"  # in Common\Files, where the EA writes it
MAX_MINUTES = 30


def _cache(account: dict, symbol: str) -> Path:
    """The cache file of one server and symbol."""
    return CACHE / f"{account['server']}_{symbol}.json"


def _probe(symbol: str, account: dict, window: tuple[str, str]) -> dict[str, int]:
    """Compile the probe and run it on M1, open_prices, on the firm's account; read its file."""
    if not wine.close_terminal():
        raise RuntimeError(
            "el terminal de MT5 sigue abierto y el tester no arranca con él"
        )
    built = metaeditor.expert(SOURCE)
    if not built["ok"] or not built["ex5_exists"]:
        raise RuntimeError(f"AlgoProbeMonths no compila: {built['messages'][:5]}")
    out = testerfile.common_files() / OUT
    out.unlink(missing_ok=True)
    started = tester.start(
        built["expert"],
        symbol,
        "M1",
        *window,
        "open_prices",
        10000,
        100,
        account,
        "months",
    )
    deadline = time.monotonic() + MAX_MINUTES * 60
    while tester.collect(started["run"])["state"] == "running":
        if time.monotonic() > deadline:
            wine.close_terminal()
            raise RuntimeError(
                f"el tester de {account['server']} no acabó en {MAX_MINUTES} min"
            )
        time.sleep(5)
    if not out.exists():
        raise RuntimeError(
            f"el tester de {account['server']} no contó barras de {symbol}"
        )
    pairs = (ln.split(",") for ln in out.read_text().split() if ln)
    return {m: int(n) for m, n in pairs}


def tester_months(
    symbol: str, account: dict, window: tuple[str, str]
) -> dict[str, int]:
    """«YYYY-MM» → M1 bars the tester walks, cached by server and symbol while it covers the window.

    Raises:
        RuntimeError: The probe did not run or wrote nothing — no bars is not «no gaps».
    """
    file = _cache(account, symbol)
    if file.exists():
        got = json.loads(file.read_text())
        if got["from"] <= window[0] and got["to"] >= window[1]:
            return got["counts"]
    counts = _probe(symbol, account, window)
    CACHE.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps({"from": window[0], "to": window[1], "counts": counts}))
    return counts
