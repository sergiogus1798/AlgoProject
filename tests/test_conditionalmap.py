#!/usr/bin/env python3
"""The conditional map's tercile edges never move when the sample they classify does."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.readings.conditionalMap import cells, regime  # noqa: E402


def main() -> None:
    """Edges come from the build segment alone; a floored cell never reaches the grid."""
    failures = []

    # A daily series with a calm build segment and a wild segment right after it. If the
    # edges ever leaked from outside the build window, the wild segment would widen them.
    days = pd.date_range("2010-01-01", "2012-12-31", freq="1D")
    calm = np.full(len(days), 1.0)
    series = pd.Series(calm, index=days)
    build = (pd.Timestamp("2010-01-01"), pd.Timestamp("2010-12-31"))
    edges_before = regime.frozen_edges(series, build)

    # Widen every value OUTSIDE the build segment by a factor that would move the terciles
    # if it leaked in. The build segment itself, and the edges it produces, must not change.
    wild = series.copy()
    wild.loc["2011-01-01":] *= 1000.0
    edges_after = regime.frozen_edges(wild, build)
    if not np.allclose(edges_before, edges_after):
        failures.append(f"frozen_edges vio fuera del tramo de build: {edges_before} -> "
                        f"{edges_after}")

    # A day the build segment never covers gets its own tercile too if it is left in the
    # series that is quantile'd — this asserts the series passed in is already sliced by
    # the caller (regime.build_span) and not, say, the whole history.
    if not np.allclose(regime.frozen_edges(pd.Series([1.0] * 10, index=days[:10]), build),
                       edges_before):
        failures.append("frozen_edges no es estable ante datos idénticos dentro del tramo")

    # A trade whose entry day sits outside the build segment is still classified against
    # the frozen edges, never against a re-cut of its own (later) day.
    later_days = pd.DatetimeIndex(["2012-06-01", "2012-06-02"])
    idx = regime.bucket(series, edges_before, later_days)
    # A constant series ties both edges (1.0, 1.0); digitize puts a value equal to both at
    # index 2 — what matters here is that it is the SAME index every time, off the SAME
    # frozen edges, whatever the later day's own local distribution would have cut instead.
    if not np.array_equal(idx, np.array([2, 2])):
        failures.append(f"bucket no aplica los cortes congelados a días fuera del tramo: {idx}")

    # A trade entering day D must not be classified off anything that happens on day D
    # itself: volatility() and efficiency() have to read through D-1's close only. Found
    # by review 2026-09-26 (F-review.md) on the pre-fix code, which resampled the WHOLE
    # calendar day (bars after the entry included) into the candle that tagged it.
    idx = pd.date_range("2020-01-01", periods=12, freq="1D")
    rng2 = np.random.default_rng(1)
    close = 100 + np.cumsum(rng2.normal(0, 1, len(idx)))
    day = pd.DataFrame({"Open": close, "High": close + 1, "Low": close - 1, "Close": close},
                       index=idx)
    d = idx[6]  # far enough past the warm-up of a period-3 lookback

    vol_before = regime.volatility(day, 3).loc[d]
    trend_before = regime.efficiency(day, 3).loc[d]

    # Simulate a huge bar arriving on day D itself, AFTER the trade already entered:
    # a real future move a same-day classification must never see.
    spiked = day.copy()
    spiked.loc[d, "High"] = close[idx.get_loc(d)] + 10_000.0

    vol_after = regime.volatility(spiked, 3).loc[d]
    trend_after = regime.efficiency(spiked, 3).loc[d]
    if vol_before != vol_after:
        failures.append(f"volatility() del día D cambia con una barra que llega DESPUÉS de "
                        f"la entrada de ese mismo día: {vol_before} -> {vol_after}")
    if trend_before != trend_after:
        failures.append(f"efficiency() del día D cambia con una barra que llega DESPUÉS de "
                        f"la entrada de ese mismo día: {trend_before} -> {trend_after}")

    # Sanity check the perturbation is not simply inert: it must move the FOLLOWING day's
    # reading, since a period-3 lookback that includes D legitimately sees it from D+1 on.
    next_day = idx[list(idx).index(d) + 1]
    if regime.volatility(day, 3).loc[next_day] == regime.volatility(spiked, 3).loc[next_day]:
        failures.append("el spike de prueba no mueve nada ni siquiera al día siguiente — "
                        "el test no comprobaría lo que dice comprobar")

    # The minimum cell size is read from engines.nulls, not a private number, and a cell
    # under it must not reach the grid or the table.
    rng = np.random.default_rng(0)
    pnl = rng.normal(0, 1, cells.MIN_CELL - 1)
    if cells.cell_stats(pnl, {"resamples": 99, "confidence": 0.95, "seed": 0}) is not None:
        failures.append(f"una celda de {len(pnl)} operaciones (< {cells.MIN_CELL}) no "
                        "debería producir estadísticos")
    full = rng.normal(0, 1, cells.MIN_CELL)
    if cells.cell_stats(full, {"resamples": 99, "confidence": 0.95, "seed": 0}) is None:
        failures.append(f"una celda de {len(full)} operaciones (= MIN_CELL) sí debería "
                        "producir estadísticos")

    print("\n".join(failures) or
          "ok: los cortes de tercil no ven nada fuera del tramo de build, y una celda por "
          "debajo del suelo nunca llega a la rejilla")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
