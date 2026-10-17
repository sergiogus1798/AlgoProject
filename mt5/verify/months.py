"""The bars per month the Strategy Tester walks for one firm's symbol on the strategy's timeframe,
and the spread of the M1 history it prices from, out of one short probe pass.

🔬 2026-10-17: the timeframe's own bars, not M1's. Hantec's 2022-06..2023-04 holds about one M1
bar an hour: an H1 strategy still trades there as SQX does (USDJPY/GBPJPY matched 95 %), an M15
one cannot (XAUUSD: every SQX trade unmatched)."""

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


def _cache(account: dict, symbol: str, timeframe: str) -> Path:
    """The cache file of one server, symbol and timeframe."""
    return CACHE / f"{account['server']}_{symbol}_{timeframe}.json"


def _probe(
    symbol: str, account: dict, window: tuple[str, str], timeframe: str
) -> dict[str, dict]:
    """Compile the probe and run it on `timeframe`, ohlc_m1, on the firm's account; read its file."""
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
        timeframe,
        *window,
        "ohlc_m1",
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
    view: dict[str, dict] = {"counts": {}, "spread": {}}
    for ln in out.read_text().split():
        cells = ln.split(",")
        if cells[0] == "spread":
            view["spread"][cells[1]] = int(cells[2])
        else:
            view["counts"][cells[0]] = int(cells[1])
    if not view["spread"]:
        raise RuntimeError(
            f"el tester de {account['server']} no leyó spreads de {symbol}"
        )
    return view


def tester_view(
    symbol: str, account: dict, window: tuple[str, str], timeframe: str
) -> dict[str, dict]:
    """{"counts": «YYYY-MM» → `timeframe` bars the tester walks, "spread": points → M1 bars},
    cached per server, symbol and timeframe while the cache covers the window.

    Raises:
        RuntimeError: The probe did not run or wrote nothing — no bars is not «no gaps».
    """
    file = _cache(account, symbol, timeframe)
    if file.exists():
        got = json.loads(file.read_text())
        if got["from"] <= window[0] and got["to"] >= window[1] and got.get("spread"):
            return got
    try:
        view = _probe(symbol, account, window, timeframe)
    except RuntimeError:
        # 🔬 2026-10-17: a terminal not yet synced with the server answers «rates base receive
        # error» and the probe writes nothing (FTMO EURJPY, first pass of the batch); once more
        view = _probe(symbol, account, window, timeframe)
    CACHE.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps({"from": window[0], "to": window[1], **view}))
    return view


def median(spread: dict[str, int]) -> int:
    """The median of a points → M1 bars histogram, in the firm's points."""
    points = sorted((int(p), n) for p, n in spread.items())
    half, seen = sum(n for _, n in points) / 2, 0
    for p, n in points:
        seen += n
        if seen >= half:
            return p
    raise ValueError("histograma de spread vacío")
