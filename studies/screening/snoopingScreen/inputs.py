"""What the screen reads: its knobs, the gate's harvest and scorecard, and the asset's own bars."""

import json
from pathlib import Path

import pandas as pd

from core.assetdata import load as load_asset, window as asset_window
from core.barstore import source as read_bars
from core.paths import DATA, report_dir
from core.study import config as study_config
from ledger import thresholds
from portfolio.common.construct.equity import closecurve

CONFIG = Path(__file__).with_name("config.yaml")
# The licence of the rebuilt panel: the median strategy's share of days whose rebuilt lowest
# equity is within TOLERANCE (account currency) of SQX's own curve. 🔬 0.997-0.999 on two
# populations of 3,700; 0.986 on one built on a feed whose clock has since changed.
TOLERANCE, RECONCILED = 1.0, 0.99


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


def panel(folder: Path, span: tuple[pd.Timestamp, pd.Timestamp], feed: str) -> pd.DataFrame:
    """Every paired strategy's daily profit over the window, close to close, from its trades.

    Args:
        folder: A harvest directory.
        span: What window() returned.
        feed: SQX feed name, e.g. "XAUUSD_M1".

    Returns:
        One column per identity, one row per day of the feed, account currency: the day's
        mark-to-market P&L at the feed's last M1 close, rebuilt from the retest's trades and
        the M1 bars (`portfolio/common/construct/equity/closecurve`). A three-week position
        spreads over three weeks, and every column sums to its trades' net profit.

        SQX's own `dailyEquity.bin` is NOT that: 🔬 it holds each day's LOWEST equity
        (`knowhow/sqx-format/daily-equity-bin.md`), whose differences are low-to-low. It is
        read here only as the known answer: the rebuild's own daily lows must match it, or
        the panel is refused — the trades, the bars and the curve are then not one backtest.
    """
    trades = pd.read_parquet(folder / "trades.parquet")
    trades = trades[(trades["sample"] == "OOS") & (trades["Open time"] >= span[0])
                    & (trades["Close time"] < span[1])]
    bars = read_bars(feed, ["High", "Low", "Close"])
    bars = bars[(bars.index >= span[0]) & (bars.index < span[1])]
    profit, low = closecurve.panel(trades, bars, *closecurve.measured(trades))

    equity = pd.read_parquet(folder / "equity.parquet")
    sqx = equity[equity["sample"] == "OOS"].pivot(index="day", columns="identity", values="equity")
    gap = (low - sqx[(sqx.index >= span[0]) & (sqx.index < span[1])]).abs()
    exact = ((gap <= TOLERANCE).sum() / gap.notna().sum()).median()
    print(f"reconstrucción contra la curva de SQX: {exact:.2%} de los días a menos de "
          f"{TOLERANCE:g} $ (mediana de {profit.shape[1]} estrategias)")
    if exact < RECONCILED:
        raise ValueError(f"{folder}: la curva reconstruida no reproduce la de SQX ({exact:.2%} "
                         f"de los días, hace falta {RECONCILED:.0%}): las operaciones, las barras "
                         f"de {feed} y la curva no son del mismo backtest")
    return profit.reindex(columns=sqx.columns).fillna(0.0)


def moves(feed: str, days: pd.DatetimeIndex) -> pd.Series:
    """The asset's price change between consecutive days of the panel, close to close.

    Args:
        feed: SQX feed name, e.g. "XAUUSD_M1".
        days: The panel's index, as panel() returned it.

    Returns:
        Price change per panel day, the first one NaN: each day's last M1 close minus the
        day before's — the same instants the panel marks its positions at. 🔬 Sampled any
        other way the benchmark loses its correlation with the strategies (median 0.32-0.46
        close to close on three populations, 0.00-0.03 with the close cut at the day's label).
    """
    return closecurve.day_closes(read_bars(feed, ["Close"])).reindex(days).diff()


def point_value(symbol: str) -> float:
    """Account currency per 1.0 of price and 1.0 of lot, from the asset file.

    Args:
        symbol: Asset name, e.g. "XAUUSD".

    Returns:
        The figure SQX holds for the instrument.
    """
    return float(load_asset(symbol)["instrument"]["point_value"])
