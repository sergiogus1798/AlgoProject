"""The three checks that the surfaces were read from the right result and paired by identity."""

from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from studies.optimisation.marketSurfaces.measure.pairs import spearman

# A misread result shows up as a rank agreement of a surface with ANOTHER market's, which
# on these batches runs from -0.4 to +0.6. A daily curve summed against SQX's own net
# profit agrees at 0.996 or better (🔬 2026-09-26, 3 USDJPY mothers x 9 markets x 2
# segments), although the dollars do not — see `against`. So the check is on rank.
RANK_AGREES = 0.99


def totals(work: Path, market: str, segment: str) -> pd.Series:
    """One market's per-day P&L of one segment, summed per variant.

    Args:
        work: The batch directory, holding `equity_markets.parquet`.
        market: The feed.
        segment: The leg.

    Returns:
        Total per `variant_id`. Read with the filters pushed into the Parquet read and the
        sum done in Arrow: 🔬 one (market, segment) is 6.8 M rows and 1.3 s, and the file
        is 228 M rows — never loaded whole.
    """
    table = pq.read_table(work / "equity_markets.parquet", columns=["variant_id", "pnl"],
                          filters=[("market", "=", market), ("segment", "=", segment)])
    summed = table.group_by("variant_id").aggregate([("pnl", "sum")]).to_pandas()
    return summed.set_index("variant_id")["pnl_sum"]


def against(curve: pd.Series, stored: pd.Series) -> dict:
    """How a harvested curve's total compares with the net profit SQX stored for the cell.

    Args:
        curve: Sum of the daily P&L per variant.
        stored: SQX's NetProfit per variant for the same market and segment.

    Returns:
        n, rank agreement, the share within one dollar, and the median and largest gap.
        ⚠️ The dollars do NOT have to agree, and on some markets they do not: 🔬 on
        EURUSD build the curve sits below the net profit on 3 of 4 variants, one-sided,
        median 474 $ — while the ranks agree at 0.9995. `sqx.variants.equity` already
        counts these as `open_at_end`. `knowhow/sqx-format/daily-equity-bin.md`.
    """
    both = pd.DataFrame({"curve": curve, "stored": stored}).dropna()
    gap = (both["curve"] - both["stored"]).abs()
    return {"n": len(both), "rho": spearman(both["curve"].to_numpy(), both["stored"].to_numpy()),
            "within_1usd": float((gap <= 1.0).mean()), "gap_median": float(gap.median()),
            "gap_max": float(gap.max())}


def markets(work: Path, cells: pd.DataFrame, extra: list[str]) -> pd.DataFrame:
    """Check 1 on every cross-check market: its curve against its own and a neighbour's profit.

    Args:
        work: The batch directory.
        cells: What `inputs.surfaces.long` returned.
        extra: The cross-check feeds, in report order.

    Returns:
        One row per (market, segment) with what `against` returns, plus `rho_wrong`: the
        same curve against the NEXT market's profit. That control is what makes 0.99 mean
        something — a pairing or result mix-up reads like `rho_wrong`, not like `rho`.
    """
    rows = []
    for segment in cells["segment"].unique():
        one = cells[cells["segment"] == segment].pivot(index="variant_id", columns="market",
                                                       values="value")
        for i, market in enumerate(extra):
            curve = totals(work, market, segment)
            wrong = against(curve, one[extra[(i + 1) % len(extra)]])["rho"]
            rows.append({"check": "curva = beneficio", "market": market, "segment": segment,
                         **against(curve, one[market]), "rho_wrong": wrong})
    return pd.DataFrame(rows)


def main(work: Path, cells: pd.DataFrame, feed: str,
         build: tuple[pd.Timestamp, pd.Timestamp]) -> pd.DataFrame:
    """Checks 1 and 2 on the main market: its wide curve, and the WFC's own C3 column.

    Args:
        work: The batch directory, holding `equity.parquet` and `metrics.parquet`.
        cells: What `inputs.surfaces.long` returned.
        feed: The main feed.
        build: First and last day of `build` as the policy declares it.

    Returns:
        Up to three rows. `equity.parquet` is checked on `build` only: its legs overlap
        (🔬 each leg's curve opens about two months before its segment, with zero P&L),
        so a date slice of `oos1` would also take the first rows of the reserved leg.
        The C3 check is exact — the WFC reads that column, so a surface that disagreed
        with it would be a different sample from the WFC's.
    """
    main_cells = cells[cells["market"] == feed].pivot(index="variant_id", columns="segment",
                                                      values="value")
    wide = pd.read_parquet(work / "equity.parquet", columns=list(main_cells.index))
    curve = wide.loc[build[0]:build[1]].sum()
    rows = [{"check": "curva = beneficio", "market": feed, "segment": "build",
             **against(curve, main_cells["build"]), "rho_wrong": np.nan}]
    c3 = pd.read_parquet(work / "metrics.parquet").set_index("variant_id")
    for segment in main_cells.columns:
        rows.append({"check": "C3 = superficie", "market": feed, "segment": segment,
                     **against(c3[f"NetProfit ({segment})"], main_cells[segment]),
                     "rho_wrong": np.nan})
    return pd.DataFrame(rows)


def diagonal(pairs: pd.DataFrame) -> pd.DataFrame:
    """Check 3: every market's rho with itself.

    Args:
        pairs: What `measure.pairs.matrix` returned, with a `segment` column.

    Returns:
        The diagonal rows. Each must read 1.0 to rounding and a Jaccard of exactly 1.0.
    """
    return pairs[pairs["a"] == pairs["b"]][["segment", "a", "n", "rho", "j"]]
