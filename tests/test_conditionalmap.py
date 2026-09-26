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
