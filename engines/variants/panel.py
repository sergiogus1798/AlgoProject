"""A retested variant batch read back: its C3 columns by split, its usable points, its panel."""

import json
from pathlib import Path

import pandas as pd



# The two readings of one batch, and the difference is what `oos2` is kept on a pedestal
# for (owner, 2026-09-24). `oos1_oos2` asks the ordinary question — does the build predict
# everything after it. `oos2_only` asks the strict one: with build AND oos1 both treated as
# in sample, does the segment nothing has ever looked at still come back. The batch is
# retested once and carries both, so switching reading re-runs the verdict and nothing else.
MODES = {"oos1_oos2": ("build", "oos1+oos2"), "oos2_only": ("build+oos1", "oos2")}


def columns(mode: str) -> dict:
    """The four C3 columns one reading of the split is measured on.

    Args:
        mode: A key of `MODES`.

    Returns:
        The in-sample and out-of-sample net-profit and trade-count column names, plus the
        two segment labels for the figure. `sqx.variants.collect` writes a column per
        segment and per union, so a mode is a choice of columns and never a recomputation.
    """
    inside, outside = MODES[mode]
    return {"is": f"NetProfit ({inside})", "oos": f"NetProfit ({outside})",
            "trades_is": f"NumberOfTrades ({inside})",
            "trades_oos": f"NumberOfTrades ({outside})",
            "is_label": inside, "oos_label": outside}


def points(metrics: pd.DataFrame, min_trades: int, cols: dict) -> pd.DataFrame:
    """The tuples that produced a real backtest on both sides of the split.

    Args:
        metrics: Contract C3, the manifest joined to the retested panel.
        min_trades: A tuple with fewer trades than this in either sample is dropped.
        cols: What `columns` returned — which reading of the split is being measured.

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


def split(work: Path, mode: str = "oos1_oos2") -> str:
    """The in-sample / out-of-sample boundary this batch is being read at.

    Args:
        work: The batch directory.
        mode: Which reading of the split — `oos1_oos2` puts the boundary at the first day
            of `oos1`, `oos2_only` at the first day of `oos2`.

    Returns:
        The first out-of-sample day, taken from the spans `sqx.variants.equity` measured
        off the curves themselves. Read from the harvest rather than restated in this
        study's own config: two files naming one date is how they come to disagree.

        ⚠️ The CSCV proper does not use this — `cscv.run` splits the history its own 924
        ways and never looks at the declared boundary, so the PBO is the same number under
        both modes. What does move is the four chronological numbers computed beside it:
        the cost of each selection rule, the deflated Sharpe, the count of independent
        trials and the drift.
    """
    found = json.loads((work / "equity.json").read_text(encoding="utf-8"))
    first = {"oos1_oos2": "oos1", "oos2_only": "oos2"}[mode]
    return found["windows"][first][0]


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
