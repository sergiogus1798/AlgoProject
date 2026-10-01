"""One surface per market and segment, read from the batch's per-market metrics."""

from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from core import assetdata

MAIN = "Main"
PROVISIONAL = "PROVISIONAL"


def main_feed(work: Path) -> tuple[str, str]:
    """The feed and the timeframe the batch was retested on as its main market.

    Args:
        work: The batch directory.

    Returns:
        ("USDJPY_M1", "H1"), read off the result key SQX stored, e.g.
        "Main: USDJPY_M1/H1". Taken from the batch and never from
        `_markets.yaml`, whose timeframe is the asset's default and not this run's.
    """
    key = pq.read_table(work / "segments.parquet", columns=["result_key"],
                        filters=[("market", "=", MAIN), ("segment", "=", "build")])
    key = key.column(0)[0].as_py()
    feed, timeframe = key.split(": ", 1)[1].split("/")
    return feed, timeframe


def declared(symbol: str) -> list[str]:
    """The cross-check markets fixed for this asset before any result was looked at.

    Args:
        symbol: The main asset, e.g. "USDJPY".

    Returns:
        Every feed of every category of `assets/_markets.yaml`, in the file's order. The
        report covers all of them and never a subset chosen after seeing where it worked.
    """
    cats = assetdata.markets(symbol)["categories"]
    return [m["feed"] for cat in ("family", "structural") for m in cats.get(cat) or []]


def provisional(feed: str) -> bool:
    """Whether the costs a market was retested at are still placeholders.

    Args:
        feed: A feed name, e.g. "EURUSD_M1".

    Returns:
        True when any cost of its asset file carries a `why` that starts PROVISIONAL —
        on 2026-09-26 every one of the ten, SQX factory defaults with zero commission.
        Read every run from `assets/symbols/`, so the flag drops the day the owner
        replaces the numbers and not before.
    """
    costs = assetdata.load(assetdata.symbol_for(feed))["costs"]
    return any(str(c.get("why", "")).startswith(PROVISIONAL) for c in costs.values())


def universe(work: Path) -> pd.Series:
    """The variants the WFC reads: the rows of contract C3.

    Args:
        work: The batch directory.

    Returns:
        `variant_id` of every row of `metrics.parquet` — what already passed the hard
        floor of `wfc.min_trades_total` on the main market. The same points as the WFC's,
        so the two studies disagree about a surface and never about a sample.
    """
    return pq.read_table(work / "metrics.parquet", columns=["variant_id"]).column(0).to_pandas()


def parameters(work: Path) -> pd.DataFrame:
    """The parameters each variant of the batch was built with.

    Args:
        work: The batch directory.

    Returns:
        `variant_id` and every `param_*` column of `metrics.parquet`, one row per variant
        the WFC reads — the axes of the surfaces the contract draws.
    """
    names = [c for c in pq.read_schema(work / "metrics.parquet").names
             if c == "variant_id" or c.startswith("param_")]
    return pq.read_table(work / "metrics.parquet", columns=names).to_pandas()


def long(work: Path, segments: list[str], metric: str, min_trades: int,
         main: str) -> pd.DataFrame:
    """Every (variant, market, segment) cell of the segments asked for, and whether it counts.

    Args:
        work: The batch directory.
        segments: Which segments to read; nothing else leaves the file.
        metric: The column each surface is made of.
        min_trades: A cell with fewer trades than this in its segment is not a point.
        main: The main feed, which replaces the harvest's "Main" label.

    Returns:
        One row per cell: `variant_id`, `market`, `segment`, `value`, `trades`, `exposure`
        (SQX's per cent of time in the market), `usable`.
        The segment filter is pushed into the Parquet read, so a reserved segment's rows
        are never materialised. The floor is per segment for the same reason the WFC's is:
        a variant with 200 trades overall and 4 in this segment measures four trades here.
    """
    table = pq.read_table(work / "segments.parquet",
                          columns=["variant_id", "market", "segment", metric, "NumberOfTrades",
                                   "Exposure"],
                          filters=[("segment", "in", segments)]).to_pandas()
    table = table[table["variant_id"].isin(set(universe(work)))]
    table["market"] = table["market"].replace(MAIN, main)
    table = table.rename(columns={metric: "value", "NumberOfTrades": "trades",
                                  "Exposure": "exposure"})
    table["usable"] = table["trades"] >= min_trades
    return table.reset_index(drop=True)


def wide(cells: pd.DataFrame, segment: str, markets: list[str],
         column: str = "value") -> pd.DataFrame:
    """One segment's surfaces side by side, a column per market.

    Args:
        cells: What `long` returned.
        segment: One of the segments it read.
        markets: Column order: the main market first, then the declared ones.
        column: `value` for the surfaces, `exposure` for the covariate `pairs` removes.

    Returns:
        `variant_id` down, market across, the metric where the cell is usable and NaN where
        it is not. A NaN is not a zero: a variant that barely traded in one market says
        nothing about its rank there, so every pair is computed on the rows both keep.
    """
    one = cells[cells["segment"] == segment]
    kept = one[column].where(one["usable"])
    return (one.assign(kept=kept).pivot(index="variant_id", columns="market", values="kept")
            .reindex(columns=markets))
