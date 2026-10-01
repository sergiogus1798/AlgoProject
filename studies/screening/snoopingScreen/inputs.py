"""What the screen reads: its knobs, the gate's harvest and scorecard, and the asset's own bars."""

import json
from pathlib import Path

import pandas as pd

from core.assetdata import load as load_asset, window as asset_window
from core.barstore import source as read_bars
from core.paths import DATA, report_dir
from core.study import config as study_config
from ledger import thresholds

CONFIG = Path(__file__).with_name("config.yaml")


def config(overrides: list[str]) -> dict:
    """The screen's knobs, with command-line overrides applied.

    Args:
        overrides: Dotted `section.key=value` strings, as `--set` passes them.

    Returns:
        What config.yaml holds, its `ledger:<key>` replaced by the number
        `ledger/thresholds.yaml` declares.
    """
    return study_config.apply(thresholds.fill(study_config.load(CONFIG, [])), overrides)


def harvest(project: str, databank: str) -> Path:
    """The newest harvest of one databank — the one the gate judged.

    Args:
        project: Project name.
        databank: The build databank's name, as the gate was run on it.

    Returns:
        Its dated folder.
    """
    folder = DATA / "harvest" / project / databank.replace(" ", "_")
    return sorted(p for p in folder.iterdir() if p.is_dir())[-1]


def scorecard(project: str, databank: str, judged: Path) -> pd.DataFrame:
    """The newest gate scorecard written over that harvest.

    Args:
        project, databank: As harvest() takes them.
        judged: The harvest folder the panel is built from.

    Returns:
        The scorecard, indexed by identity. The gate's manifest must name this very
        harvest: a verdict read against another harvest annotates the wrong population.
    """
    reports = report_dir(project, databank, "x").parent
    folder = sorted(reports.glob("*/gate/scorecard.parquet"))[-1].parent
    named = json.loads((folder / "manifest.json").read_text())["source"]["harvest"]
    if Path(named).resolve() != judged.resolve():
        raise ValueError(f"la puerta de {folder} juzgó {named}, no {judged}: corre la puerta "
                         f"sobre la cosecha nueva primero")
    return pd.read_parquet(folder / "scorecard.parquet")


def window(symbol: str, segment: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    """The segment's dates, as the policy file declares them.

    Args:
        symbol: Asset name, e.g. "XAUUSD".
        segment: "build", "oos1" or "oos2".

    Returns:
        First instant and the instant after the last, UTC-naive like the bars.
    """
    start, end = asset_window(load_asset(symbol), segment)
    return (pd.Timestamp(start, unit="ms"), pd.Timestamp(end, unit="ms"))


def panel(folder: Path, span: tuple[pd.Timestamp, pd.Timestamp]) -> pd.DataFrame:
    """Every paired strategy's daily profit over the window, from its retest's own curve.

    Args:
        folder: A harvest directory.
        span: What window() returned.

    Returns:
        One column per identity, one row per day, account currency. The curve is SQX's
        `dailyEquity.bin`, which is marked to market — 🔬 on XAU_ISOOS_ejemplo it moves on
        390 days on which the strategy closed nothing — so a three-week position spreads
        over three weeks instead of landing on the day it closed.

        The last day is dropped: SQX marks a position still open on the last bar to market
        in the curve while its net profit counts only closed trades (up to 332 $ measured).
    """
    equity = pd.read_parquet(folder / "equity.parquet")
    oos = equity[equity["sample"] == "OOS"].pivot(index="day", columns="identity",
                                                  values="equity")
    oos = oos[(oos.index >= span[0]) & (oos.index < span[1])].ffill()
    return oos.diff().iloc[1:-1].fillna(0.0)


def moves(feed: str, days: pd.DatetimeIndex) -> pd.Series:
    """The asset's price change between consecutive days of the panel.

    Args:
        feed: SQX feed name, e.g. "XAUUSD_M1".
        days: The panel's index, as panel() returned it.

    Returns:
        Price change per panel day, the first one NaN. The M1 close is sampled at each
        label's own instant, because 🔬 SQX stamps day D with the equity it carried into D,
        not the one it left D with: the median correlation between strategies and gold on
        XAU_ISOOS_ejemplo is 0.15 cut at the label and 0.07 with a plain daily resample,
        which lags the benchmark one day behind. Sampling on the panel's own days also
        keeps every day the strategies have, weekends and holidays of the feed included.
    """
    closes = read_bars(feed, ["Close"])["Close"]
    return pd.Series(closes.asof(days).values, index=days).diff()


def point_value(symbol: str) -> float:
    """Account currency per 1.0 of price and 1.0 of lot, from the asset file.

    Args:
        symbol: Asset name, e.g. "XAUUSD".

    Returns:
        The figure SQX holds for the instrument.
    """
    return float(load_asset(symbol)["instrument"]["point_value"])
