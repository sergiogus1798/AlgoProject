"""A retested variant batch read back: its C3 columns by split, its usable points, its panel."""

import json
from pathlib import Path

import pandas as pd



# Which segments sit on each side of the split. Owner, 2026-09-27 (encargo 24, Q11): `build`
# is ALWAYS in sample; the in-sample side is `build` or `build+oos1`; the out-of-sample side is
# whatever is left, and `oos1` may be left out entirely. The batch is retested once and
# `sqx.variants.collect` writes a column per segment and per union, so every composition is a
# choice of columns and never a new backtest.
SEGMENTS = ("build", "oos1", "oos2")
COMPOSITIONS = ((("build",), ("oos1",)), (("build",), ("oos2",)),
                (("build",), ("oos1", "oos2")), (("build", "oos1"), ("oos2",)))

# The two readings of 2026-09-24, kept as names. `oos1_oos2` asks the ordinary question — does
# the build predict everything after it. `oos2_only` asks the strict one: with build AND oos1
# both treated as in sample, does the segment nothing has ever looked at still come back.
SHORTCUTS = {"oos1_oos2": (("build",), ("oos1", "oos2")),
             "oos2_only": (("build", "oos1"), ("oos2",))}


def composition(inside: list[str], outside: list[str]) -> tuple[tuple, tuple]:
    """Check one composition of the split against the owner's rule and put it in order.

    Args:
        inside: The in-sample segments, e.g. ["build", "oos1"].
        outside: The out-of-sample segments, e.g. ["oos2"].

    Returns:
        (inside, outside) as tuples in chronological order.

    Raises:
        ValueError: `build` is not in sample, `oos1` is out while `build+oos1` is in, a
            segment sits on both sides or is not one of the three, or nothing is out.
    """
    comp = (tuple(s for s in SEGMENTS if s in inside),
            tuple(s for s in SEGMENTS if s in outside))
    if (set(inside) | set(outside)) - set(SEGMENTS) or comp not in COMPOSITIONS:
        raise ValueError(
            f"composición no admitida: IS {'+'.join(inside)}, OOS {'+'.join(outside)}. "
            f"`build` va siempre dentro; dentro es build o build,oos1; fuera, lo que queda "
            f"de {', '.join(SEGMENTS)} (oos1 puede quedarse fuera de las dos)")
    return comp


def label(comp: tuple[tuple, tuple]) -> str:
    """The composition as a file stem and a ledger criterion: `build+oos1__oos2`."""
    return f"{'+'.join(comp[0])}__{'+'.join(comp[1])}"


def columns(comp: tuple[tuple, tuple]) -> dict:
    """The four C3 columns one composition of the split is measured on.

    Args:
        comp: What `composition` returned, or a value of `SHORTCUTS`.

    Returns:
        The in-sample and out-of-sample net-profit and trade-count column names, plus the
        two segment labels for the figure. Every admitted composition names a union
        `sqx.variants.collect` already writes (`build`, `build+oos1`, `oos1`, `oos2`,
        `oos1+oos2`), so none needs a column of its own.
    """
    inside, outside = "+".join(comp[0]), "+".join(comp[1])
    return {"is": f"NetProfit ({inside})", "oos": f"NetProfit ({outside})",
            "trades_is": f"NumberOfTrades ({inside})",
            "trades_oos": f"NumberOfTrades ({outside})",
            "is_label": inside, "oos_label": outside}


def points(metrics: pd.DataFrame, min_trades: int, cols: dict) -> pd.DataFrame:
    """The tuples that produced a real backtest on both sides of the split.

    Args:
        metrics: Contract C3, the manifest joined to the retested panel.
        min_trades: A tuple with fewer trades than this in either sample is dropped.
        cols: What `columns` returned — which composition of the split is measured.

    Returns:
        One row per usable tuple. **The filter is not tidying, it is the measurement.** A
        parameter setting that barely trades produces a net profit that is one or two
        trades wide; left in, a handful of them dominate a correlation computed over a
        dozen points and the answer becomes an artefact of the degenerate corners rather
        than a statement about the surface.
    """
    kept = metrics.dropna(subset=[cols["is"], cols["oos"]])
    return kept[(kept[cols["trades_is"]] >= min_trades)
                & (kept[cols["trades_oos"]] >= min_trades)]


def panel(work: Path, period: str) -> pd.DataFrame:
    """Every harvested variant's profit, aggregated from days to periods.

    Args:
        work: The batch directory, holding `equity.parquet` from `sqx.variants.equity`.
        period: A pandas offset alias -- "W" for weekly, "ME" for month end.

    Returns:
        Periods down, `variant_id` across, each cell that period's profit or loss.

        **The final period is dropped.** SQX marks a position that is still open on the
        last bar to market in the equity curve while its net profit counts only closed
        trades, so the last few days carry an unrealised number that no other period
        carries -- measured on 172 of 962 variants, by up to 332 dollars. Aggregating
        daily to weekly is also what makes the ranks mean anything: at roughly sixty
        trades a year a daily matrix is almost all zeros.
    """
    daily = pd.read_parquet(work / "equity.parquet")
    return daily.resample(period).sum().iloc[:-1]


def split(work: Path, comp: tuple[tuple, tuple]) -> str:
    """The in-sample / out-of-sample boundary this batch is being read at.

    Args:
        work: The batch directory.
        comp: What `composition` returned — the boundary is the first day of its first
            out-of-sample segment.

    Returns:
        The first out-of-sample day, taken from the spans `sqx.variants.equity` measured
        off the curves themselves. Read from the harvest rather than restated in this
        study's own config: two files naming one date is how they come to disagree.

        ⚠️ The CSCV proper does not use this — `cscv.run` cuts the history into 12 blocks
        and reads their 924 partitions (C(12,6)), never the declared boundary, so the PBO is
        the same number under every composition. What does move is the four chronological
        numbers computed beside it: the cost of each selection rule, the deflated Sharpe,
        the count of independent trials and the drift.
    """
    found = json.loads((work / "equity.json").read_text(encoding="utf-8"))
    return found["windows"][comp[1][0]][0]


def usable(wide: pd.DataFrame, metrics: pd.DataFrame, min_trades: int,
           cols: dict) -> pd.DataFrame:
    """Narrow the panel to the variants the correlation study already accepted.

    Args:
        wide: What `panel` returned.
        metrics: Contract C3, the manifest joined to the retested panel.
        min_trades: A variant trading less than this in either sample is dropped.
        cols: What `columns` returned.

    Returns:
        The same frame with only the columns that survive `points`, so the rho
        and the PBO are two statements about one set of points rather than two samples
        that happen to share a name.
    """
    kept = set(points(metrics, min_trades, cols)["variant_id"])
    return wide[[c for c in wide.columns if c in kept]]


def windows(wide: pd.DataFrame, boundary: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """The real chronological halves, for the statistics that are not combinatorial.

    Args:
        wide: What `usable` returned.
        boundary: What `split` returned.

    Returns:
        (in-sample, out-of-sample). The CSCV deliberately ignores this split -- it asks
        about the selection procedure, not about this particular history -- but the cost
        of a selection rule in §8c is a question about exactly this split.
    """
    return wide[wide.index < boundary], wide[wide.index >= boundary]
