"""The funded-firms method for an asset's spread: the widest firm's % of price, times the segment's price.

The method of `assets/RULES.md` (owner, 2026-10-04): per firm, the time-weighted mean spread as a
% of price over its last 12 monthly sample days and over its last 3, the larger of the two; the
widest firm wins; times each segment's mean daily close, in points of the asset's tick; factor
from the ledger, slippage a share of it. Reads `AlgoData/mt5/ticks_hist/<firm>/<ASSET>/`, never
Darwinex.
"""

from pathlib import Path
from typing import Any

import pandas as pd

from core import barstore
from core.assetdata import load, window
from core.paths import MT5_DATA

HIST = MT5_DATA / "ticks_hist"
FIRMS = ("ftmo", "hantec", "fundingpips")
CAP_S = 60  # a quote counts at most a minute: closed hours weigh nothing
LONG, SHORT = 12, 3  # sample days, one per month
SEGMENTS = {"build": "is", "oos1": "oos", "oos2": "oos2"}
NAMES = {"fundingpips": "FundingPips", "ftmo": "FTMO", "hantec": "Hantec"}
SLIP_WHY = (
    "{share:.0f} % del spread del tramo `{seg}` (dueño, 2026-10-04; antes la mitad): 600 operaciones "
    "reales costaron 1,33 × el spread de ida y vuelta, IC 95 % 1,08-1,72"
)


def day_pct(file: Path) -> float:
    """One sample day's time-weighted mean spread as a fraction of the bid."""
    t = pd.read_parquet(file)
    dt = t["time_msc"].diff().shift(-1).dt.total_seconds().fillna(0).clip(upper=CAP_S)
    if not {"bid", "ask", "time_msc"} <= set(t.columns) or dt.sum() <= 0:
        raise ValueError(f"{file}: sin columnas bid/ask/time_msc o sin duración")
    return float((((t["ask"] - t["bid"]) / t["bid"]) * dt).sum() / dt.sum())


def firm_pct(firm: str, symbol: str) -> float | None:
    """A firm's % of price: the larger of its last-12 and last-3 sample days' means; None if no ticks."""
    files = sorted((HIST / firm / symbol).glob("*.parquet"))
    if not files:
        return None
    days = [day_pct(f) for f in files]
    return max(
        sum(days[-LONG:]) / len(days[-LONG:]), sum(days[-SHORT:]) / len(days[-SHORT:])
    )


def widest(symbol: str) -> tuple[str, float, dict[str, float]]:
    """The widest firm, its fraction of price and every firm's. Raises when no firm has ticks."""
    per = {f: p for f in FIRMS if (p := firm_pct(f, symbol)) is not None}
    if not per:
        raise ValueError(
            f"{symbol}: sin ticks de fondeo en {HIST} — este método no aplica"
        )
    best = max(per, key=lambda f: per[f])
    return best, per[best], per


def segment_prices(data: dict) -> dict[str, float]:
    """Each segment's mean of daily last closes, from the asset's M1 bars."""
    close = barstore.source(data["sqx_symbol"], ["Close"])["Close"]
    daily = close.resample("D").last().dropna()
    out = {}
    for seg in SEGMENTS:
        a, b = (pd.Timestamp(ms, unit="ms") for ms in window(data, seg))
        out[seg] = float(daily[(daily.index >= a) & (daily.index < b)].mean())
    return out


def plan(symbol: str, factor: float, share: float) -> dict[str, Any]:
    """Spreads and slippage per segment, in SQX points, and the line that explains them.

    Args:
        symbol: Card name.
        factor: Multiplier of the measured spread; the `why` says «sin factor», so only 1.0 is allowed.
        share: Slippage as a fraction of the spread (0.35).
    """
    if factor != 1.0:
        raise ValueError(
            f"factor {factor}: el método vigente no lleva factor de seguridad"
        )
    data = load(symbol)
    firm, pct, per = widest(
        data["symbol"]
    )  # a twin card (XAUUSD_SYN01) reads its original's ticks
    tick, prices = data["instrument"]["tick_size"], segment_prices(data)
    spreads = {
        f"spread_{h}": round(pct * prices[s] / tick * factor, 2)
        for s, h in SEGMENTS.items()
    }
    return {
        "symbol": symbol,
        "firm": firm,
        "pct": pct,
        "per_firm": per,
        "prices": prices,
        "spreads": spreads,
        "slippage": {
            f"slippage_{k[7:]}": round(v * share, 2) for k, v in spreads.items()
        },
    }


def whys(p: dict[str, Any], day: str, share: float) -> dict[str, str]:
    """The `why` of every field the plan writes; the spread's carries «sin factor», the marker
    `onboard.apply` refuses to overwrite."""
    seg = {"is": "build", "oos": "oos1", "oos2": "oos2"}
    out = {}
    for field in p["spreads"]:
        h = field.removeprefix("spread_")
        out[field] = (
            f"recalibrado {day} — {p['pct'] * 100:.4f} % del precio medio del tramo `{seg[h]}` "
            f"({p['prices'][seg[h]]:.1f}): spread medio por tiempo de {NAMES[p['firm']]}, la más ancha "
            "de FTMO/Hantec/FundingPips, media de 12 meses de sus ticks, sin factor. "
            "knowhow/costs/funded-tick-spread-vs-price.md"
        )
        out[f"slippage_{h}"] = SLIP_WHY.format(share=share * 100, seg=seg[h])
    return out
