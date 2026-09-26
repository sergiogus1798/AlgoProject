"""Which trades touch an anomaly: in the bar of their signal, entry or exit, or while open."""

import numpy as np
import pandas as pd

from core.barstore import RULE
from engines.market.feed import scale

FAMILIES = ("cierre", "mecha", "extremo", "congelado", "hueco")


def families(ev: pd.DataFrame) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """The feed's anomalies as sorted, disjoint [start, end) minute intervals, one set per family.

    Args:
        ev: A feed's events.parquet.

    Returns:
        {family: (starts, ends)}. `cierre` and `mecha` are the spike-and-reverts of each column;
        `extremo` the spikes that stayed (both columns, merged); `hueco` the symbol's own gaps
        and the provider's outages. Rollover runs, partial closes and holidays mark nothing.
    """
    pick = {"cierre": (ev["kind"] == "cierre") & (ev["cls"] == "vuelta"),
            "mecha": (ev["kind"] == "mecha") & (ev["cls"] == "vuelta"),
            "extremo": ev["kind"].isin(["cierre", "mecha"]) & (ev["cls"] == "extremo"),
            "congelado": (ev["kind"] == "congelado") & (ev["cls"] == "congelado"),
            "hueco": (ev["kind"] == "hueco") & ev["cls"].isin(["símbolo", "caída del proveedor"])}
    out = {}
    for name, mask in pick.items():
        spans = ev.loc[mask, ["start_min", "end_min"]].drop_duplicates("start_min")
        spans = spans.sort_values("start_min")
        out[name] = (spans["start_min"].to_numpy(), spans["end_min"].to_numpy())
    return out


def hits(spans: tuple[np.ndarray, np.ndarray], a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """How many intervals of one family overlap each window [a, b).

    Returns:
        Per window. Counting starts before b and ends at or before a is exact because the
        intervals of one family are sorted and never overlap one another.
    """
    starts, ends = spans
    return np.searchsorted(starts, b, "left") - np.searchsorted(ends, a, "right")


def bars(trades: pd.DataFrame, index: pd.DatetimeIndex, timeframe: str) -> dict:
    """Each trade's signal, entry and exit bars, and the time between, as minute windows.

    Args:
        trades: One row per trade with `Open time` and `Close time`.
        index: Open times of the strategy's bars (core.barstore.read).
        timeframe: Its code, e.g. "H1".

    Returns:
        {"signal", "entry", "exit", "during"}, each a pair of arrays (from, to). The signal
        bar is the one before the entry bar: a market order fills at the open after the bar
        that decided it.
    """
    width = int(pd.Timedelta(RULE[timeframe]).total_seconds() // 60)
    starts = scale.minutes(index)
    k = np.searchsorted(index, trades["Open time"].to_numpy(), "right") - 1
    j = np.searchsorted(index, trades["Close time"].to_numpy(), "right") - 1
    span = {"signal": starts[k - 1], "entry": starts[k], "exit": starts[j]}
    out = {name: (s, s + width) for name, s in span.items()}
    out["during"] = (starts[k] + width, np.maximum(starts[k] + width, starts[j]))
    return out


def mark(trades: pd.DataFrame, ev: pd.DataFrame, index: pd.DatetimeIndex, timeframe: str,
         rules: dict, include_non_reverting: bool) -> pd.DataFrame:
    """Every trade of one strategy, with what it touched and whether it is flagged.

    Args:
        trades: That strategy's trades.
        ev: The feed's events.parquet.
        index, timeframe: The strategy's bars.
        rules: template.rules() for the strategy.
        include_non_reverting: Whether spikes that stayed mark a trade too (decision 6: no).

    Returns:
        The trades with one bool column per family touched in the three bars, `durante`
        (anything touched while open, read with the wick — only counted with a stop),
        `spike` and `hueco o congelado` (what flagged it) and `marcada`.
    """
    fam, win = families(ev), bars(trades, index, timeframe)
    out = trades.copy()
    for name in FAMILIES:
        out[name] = np.any([hits(fam[name], *win[b]) > 0 for b in ("signal", "entry", "exit")],
                           axis=0)
    out["durante"] = np.any([hits(fam[n], *win["during"]) > 0
                             for n in ("mecha", "congelado", "hueco")], axis=0)
    out["spike"] = out[rules["column"]] | (out["extremo"] & include_non_reverting)
    out["hueco o congelado"] = out["congelado"] | out["hueco"]
    out["marcada"] = out["spike"] | out["hueco o congelado"] | (out["durante"] & rules["stop"])
    return out
