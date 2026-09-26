"""Every knob, and what the detector reads: a feed's M1 bars, its tick, its frozen K and session."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from core.barstore import library, source
from core.paths import DATA, feed_quality_dir
from core.study import config as study_config
from engines.market.feed import scale, session
from ledger import thresholds

CONFIG = Path(__file__).with_name("config.yaml")
PRICES = ["Open", "High", "Low", "Close"]


def config(overrides: list[str]) -> dict:
    """Every knob, with command-line overrides applied.

    Args:
        overrides: "section.key=value" strings, as --set gives them.

    Returns:
        The parsed config.yaml with every `ledger:<key>` replaced by the number
        `ledger/thresholds.yaml` declares, K and session per feed included.
    """
    return study_config.apply(thresholds.fill(study_config.load(CONFIG, [])), overrides)


def feeds() -> list[str]:
    """Every feed the bar library holds, in its own order."""
    return list(library())


def calendar_feeds() -> list[str]:
    """The feeds that decide the library's calendar: one provider's, Dukascopy's.

    Returns:
        Brent comes from FTMO; a silence of its own says nothing about Dukascopy's
        holidays (owner's answer 2.10).
    """
    return [f for f in feeds() if "_Dukas" in f]


def tick(b: dict, years: list[int]) -> float:
    """The feed's own price increment: its smallest close-to-close move.

    Args:
        b: bars()'s dict.
        years: [first, last] calendar years to read it from.

    Returns:
        A price. Not assets/'s `tick_size`: SQX's tick is the pip, and the Dukascopy forex
        feeds quote a tenth of it (EURUSD moves by 0.00001, USDJPY by 0.001) — a floor of
        three SQX ticks would be three pips (owner's answer 2.2: the feed's increment).
    """
    year = b["t"].year
    c = b["c"][(year >= years[0]) & (year <= years[1])]
    moves = np.round(np.abs(np.diff(c)), 8)
    return float(moves[moves > 0].min())


def bars(feed: str) -> dict:
    """One feed's M1 bars as plain arrays.

    Args:
        feed: SQX symbol without the timeframe suffix.

    Returns:
        {"t": the DatetimeIndex, "at": whole minutes (engines.market.feed.scale), and
        "o", "h", "l", "c"}.
    """
    frame = source(feed, PRICES)
    return {"t": frame.index, "at": scale.minutes(frame.index),
            **{k: frame[col].to_numpy() for k, col in zip("ohlc", PRICES)}}


def year_minute(year: int) -> int:
    """The minute (engines.market.feed.scale axis) that opens a calendar year."""
    return int(scale.minutes(pd.DatetimeIndex([pd.Timestamp(year=year, month=1, day=1)]))[0])


def week_mask(cfg: dict, feed: str) -> np.ndarray:
    """The feed's session as frozen in the ledger, a minute-of-week mask."""
    return session.mask(cfg["sessions"][feed])


def harvest(project: str, databank: str) -> Path:
    """The newest harvest of one build databank (studies.screening.gate.harvest's output).

    Returns:
        Its folder. Harvests are dated and immutable, so the newest is the current one.
    """
    folder = DATA / "harvest" / project / databank.replace(" ", "_")
    return sorted(p for p in folder.iterdir() if p.is_dir())[-1]


def strategies(folder: Path) -> pd.DataFrame:
    """One row per strategy of a harvest: its name in the retest databank and its timeframe.

    Returns:
        Indexed by identity, columns `strategy` and `TimeFrame [IS]`.
    """
    return pd.read_parquet(folder / "metrics.parquet", columns=["strategy", "TimeFrame [IS]"])


def events(feed: str, cfg: dict) -> pd.DataFrame:
    """A feed's anomalies as step 4's scan wrote them, refused if scanned under another K.

    Returns:
        events.parquet. A scan older than the K now frozen in the ledger would attribute
        against thresholds nobody set, so it stops the run instead.
    """
    folder = feed_quality_dir(feed)
    scanned = json.loads((folder / "summary.json").read_text(encoding="utf-8"))
    if scanned["K"] != cfg["K"][feed] or scanned["session"] != cfg["sessions"][feed]:
        raise SystemExit(f"feedQuality: {feed} se escaneó con K={scanned['K']} y otra sesión; "
                         "vuelve a correr `python3 -m studies.data.feedQuality.scan`")
    return pd.read_parquet(folder / "events.parquet")


def trades(folder: Path) -> pd.DataFrame:
    """A harvest's trades, IS and OOS, each carrying its strategy's `identity` and `sample`."""
    return pd.read_parquet(folder / "trades.parquet",
                           columns=["identity", "sample", "Open time", "Close time", "Profit/Loss"])
