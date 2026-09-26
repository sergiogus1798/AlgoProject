"""What step 20 reads: its knobs, the ledger's two doors, the mothers' oos2 days and the asset's bars."""

from pathlib import Path

import pandas as pd

from core.assetdata import load as load_asset, window as asset_window
from core.barstore import source as read_bars
from core.study import config as study_config
from ledger import gate, study as studymod, thresholds

CONFIG = Path(__file__).with_name("config.yaml")
STEP = 20
SEGMENT = "oos2"   # the stretch no selection step looked at; not a knob (config.yaml says why)


def config(overrides: list[str]) -> dict:
    """Step 20's knobs, with command-line overrides applied.

    Args:
        overrides: Dotted `section.key=value` strings, as `--set` passes them.

    Returns:
        What config.yaml holds, its `ledger:<key>` replaced by the number
        `ledger/thresholds.yaml` declares.
    """
    return study_config.apply(thresholds.fill(study_config.load(CONFIG, [])), overrides)


def blind_door(study: str) -> pd.DataFrame:
    """Refuse to open 17, 18 and 19 unless the study's ledger says all three ran.

    Args:
        study: What `ledger.study.study_id` returned.

    Returns:
        The study's ledger. Raises PermissionError from `ledger.gate.allow_read` otherwise:
        presence in the ledger is what "ran" means, whatever lies on disk.
    """
    frame = studymod.read(study)
    gate.allow_read(frame)
    return frame


def segment_door(symbol: str) -> str | None:
    """Whether the policy lets step 20 read oos2 itself.

    Args:
        symbol: Asset as `assets/symbols/` spells it.

    Returns:
        None when it may; the refusal's text when it may not. A refusal is an answer the
        report prints, not a failure: the joint reading of the four pieces reads no raw
        segment and goes on without the SPA. Who may read oos2 is `_policy.yaml`'s, the
        owner's file.
    """
    try:
        gate.allow(STEP, SEGMENT, symbol)
    except PermissionError as refusal:
        return str(refusal)
    return None


def window(symbol: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    """The oos2 dates, as the policy file declares them.

    Args:
        symbol: Asset name, e.g. "USDJPY".

    Returns:
        First instant and the instant after the last, UTC-naive like the bars.
    """
    start, end = asset_window(load_asset(symbol), SEGMENT)
    return pd.Timestamp(start, unit="ms"), pd.Timestamp(end, unit="ms")


def mother_days(batch: Path, span: tuple[pd.Timestamp, pd.Timestamp]) -> pd.Series:
    """One mother's own daily profit over oos2, from its batch's joined curve.

    Args:
        batch: The mother's variant batch folder.
        span: What window() returned.

    Returns:
        Daily profit, account currency, marked to market. The mother is the variant the
        manifest flags `origin`. `equity.parquet` already holds daily increments, so
        nothing is differenced. The last day is dropped: SQX marks a position still open
        on the last bar to market while its net profit counts only closed trades.

        ⚠️ Each leg opens with ~2 months of zero-P&L warm-up that repeats the previous
        leg's dates (🔬 the oos2 leg from 2022-11-03, the oos1 leg to 2022-12-29), and the
        leg is not recorded. oos2 from its policy start is clear of them; a cut that still
        catches a duplicated date would add flat days that did not happen, and refuses.
    """
    origin = pd.read_parquet(batch / "manifest.parquet", columns=["variant_id", "origin"])
    column = origin.loc[origin["origin"], "variant_id"].item()
    days = pd.read_parquet(batch / "equity.parquet", columns=[column])[column]
    days = days[(days.index >= span[0]) & (days.index < span[1])]
    if days.index.duplicated().any():
        raise ValueError(f"{batch}: el tramo {span} cruza el solape de dos patas del retest")
    return days.iloc[:-1]


def panel(batches: dict[str, Path], span: tuple[pd.Timestamp, pd.Timestamp]) -> pd.DataFrame:
    """Every complete mother's oos2 days side by side.

    Args:
        batches: {mother: batch folder}, the complete mothers only.
        span: What window() returned.

    Returns:
        One column per mother, one row per day any of them has; a day one lacks is flat.
    """
    return pd.DataFrame({m: mother_days(b, span) for m, b in batches.items()}).fillna(0.0)


def moves(feed: str, days: pd.DatetimeIndex) -> pd.Series:
    """The asset's price change between consecutive days of the panel.

    Args:
        feed: SQX feed name, e.g. "USDJPY_DukasM1_the5ers".
        days: The panel's index.

    Returns:
        Price change per panel day, the first one NaN. The M1 close is sampled at each
        label's own instant because SQX stamps day D with the equity it carried into D
        (part A, `studies/screening/snoopingScreen/inputs.py`, copied not imported).
    """
    closes = read_bars(feed, ["Close"])["Close"]
    return pd.Series(closes.asof(days).values, index=days).diff()


def point_value(symbol: str) -> float:
    """Account currency per 1.0 of price and 1.0 of lot, from the asset file.

    Args:
        symbol: Asset name, e.g. "USDJPY".

    Returns:
        The figure SQX holds for the instrument.
    """
    return float(load_asset(symbol)["instrument"]["point_value"])
