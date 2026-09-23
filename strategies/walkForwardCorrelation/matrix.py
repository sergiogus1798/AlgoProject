"""The N x T panel the CSCV runs on: one variant per column, one period of P&L per row."""

import json
from pathlib import Path

import pandas as pd

from strategies.walkForwardCorrelation import measure


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


def split(work: Path) -> str:
    """The in-sample / out-of-sample boundary this batch was retested on.

    Args:
        work: The batch directory.

    Returns:
        The first out-of-sample day, as `sqx.variants.equity` recorded it. Read from the
        harvest rather than restated in this study's own config: two files naming one
        date is how they come to disagree.
    """
    return json.loads((work / "equity.json").read_text(encoding="utf-8"))["split"]


def usable(wide: pd.DataFrame, metrics: pd.DataFrame, min_trades: int) -> pd.DataFrame:
    """Narrow the panel to the variants the correlation study already accepted.

    Args:
        wide: What `panel` returned.
        metrics: Contract C3, the manifest joined to the retested panel.
        min_trades: A variant trading less than this in either sample is dropped.

    Returns:
        The same frame with only the columns that survive `measure.points`, so the rho
        and the PBO are two statements about one set of points rather than two samples
        that happen to share a name.
    """
    kept = set(measure.points(metrics, min_trades)["variant_id"])
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
