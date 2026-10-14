"""What step 20 reads: its knobs, the ledger's two doors, the mothers' oos2 days and their random traders'."""

from typing import Any, cast
from pathlib import Path

import pandas as pd

from core.assetdata import load as load_asset, window as asset_window
from core.barstore import source as read_bars
from core.study import config as study_config
from engines.market import reprice
from engines.nulls import footprint
from ledger import gate, study as studymod, thresholds
from portfolio.common.construct.equity import closecurve

CONFIG = Path(__file__).with_name("config.yaml")
STEP = 20
SEGMENT = "oos2"   # the stretch no selection step looked at; not a knob (config.yaml says why)
TRADES = "trades.parquet"   # per variant, in the batch folder: step 16.5's harvest writes it
# The rebuilt panel's licence, as part A sets it: the median mother's share of days whose
# rebuilt lowest equity is within TOLERANCE (account currency) of SQX's own curve.
TOLERANCE, RECONCILED = 1.0, 0.99


def config(overrides: list[str]) -> dict[str, Any]:
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
        report prints, not a failure: the joint reading of the three pieces reads no raw
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
    first, last = pd.Timestamp(start, unit="ms"), pd.Timestamp(end, unit="ms")
    return cast(pd.Timestamp, first), cast(pd.Timestamp, last)


def mother_low(batch: Path, span: tuple[pd.Timestamp, pd.Timestamp]) -> pd.Series:
    """One mother's own SQX curve over oos2, from its batch's joined curve — a known answer.

    Args:
        batch: The mother's variant batch folder.
        span: What window() returned.

    Returns:
        Each day's LOWEST equity since oos2 began, account currency: 🔬 that is what SQX's
        daily curve holds, not a mark to market (`knowhow/sqx-format/daily-equity-bin.md`),
        so it licenses the rebuilt panel and never feeds it. The mother is the variant the
        manifest flags `origin`; `equity.parquet` holds daily increments, summed here.

        ⚠️ Each leg opens with ~2 months of zero-P&L warm-up that repeats the previous
        leg's dates (🔬 the oos2 leg from 2022-11-03, the oos1 leg to 2022-12-29), and the
        leg is not recorded. oos2 from its policy start is clear of them; a cut that still
        catches a duplicated date would add flat days that did not happen, and refuses.
    """
    origin = pd.read_parquet(batch / "manifest.parquet", columns=["variant_id", "origin"])
    column = origin.loc[origin["origin"], "variant_id"].item()
    days = cast(pd.Series, pd.read_parquet(batch / "equity.parquet", columns=[column])[column])
    days = cast(pd.Series, days[(days.index >= span[0]) & (days.index < span[1])])
    if days.index.duplicated().any():
        raise ValueError(f"{batch}: el tramo {span} cruza el solape de dos patas del retest")
    return cast(pd.Series, days.cumsum())


def trades_door(batches: dict[str, Path]) -> str | None:
    """Whether every complete mother's batch holds the trades the oos2 panel is rebuilt from.

    Args:
        batches: {mother: batch folder}, the complete mothers only.

    Returns:
        None when all do; else the refusal's text, an answer the report prints like the
        policy's: the three pieces are read and the SPA is not, with oos2 left unopened.
    """
    lacking = sorted(m for m, b in batches.items() if not (b / TRADES).exists())
    return (f"sin las operaciones de {', '.join(lacking)} ({TRADES} de su lote de variantes) "
            f"no se puede reconstruir su curva de cierre a cierre") if lacking else None


def mother_trades(batch: Path, span: tuple[pd.Timestamp, pd.Timestamp]) -> pd.DataFrame:
    """One mother's own trades inside oos2, from its batch (schema T plus `variant_id`)."""
    origin = pd.read_parquet(batch / "manifest.parquet", columns=["variant_id", "origin"])
    trades = pd.read_parquet(batch / TRADES)
    trades = trades[trades["variant_id"] == origin.loc[origin["origin"], "variant_id"].item()]
    return cast(pd.DataFrame, trades[(trades["Open time"] >= span[0]) & (trades["Close time"] < span[1])])


def panel(batches: dict[str, Path], span: tuple[pd.Timestamp, pd.Timestamp],
          feed: str) -> pd.DataFrame:
    """Every complete mother's oos2 days side by side, close to close, from its trades.

    Args:
        batches: {mother: batch folder}, the complete mothers only.
        span: What window() returned.
        feed: SQX feed name, e.g. "USDJPY_M1".

    Returns:
        One column per mother, one row per day of the feed: the day's mark-to-market P&L at
        the feed's last M1 close, rebuilt from the mother's trades and the M1 bars
        (`portfolio/common/construct/equity/closecurve`), flat days 0. The rebuild's own
        daily lows must match `mother_low`, or the panel is refused — as part A does.
    """
    trades = pd.concat([mother_trades(b, span).assign(identity=m) for m, b in batches.items()])
    bars = cast(pd.DataFrame, read_bars(feed, ["High", "Low", "Close"]))
    bars = cast(pd.DataFrame, bars[(bars.index >= span[0]) & (bars.index < span[1])])
    profit, low = closecurve.panel(trades, bars, *closecurve.measured(trades))
    gap = (low - pd.DataFrame({m: mother_low(b, span) for m, b in batches.items()})).abs()
    exact = ((gap <= TOLERANCE).sum() / gap.notna().sum()).median()
    if exact < RECONCILED:
        raise ValueError(f"la curva reconstruida de las madres no reproduce la de SQX "
                         f"({exact:.2%} de los días, hace falta {RECONCILED:.0%})")
    return cast(pd.DataFrame, profit.reindex(columns=list(batches)).fillna(0.0))


def random_traders(batches: dict[str, Path], span: tuple[pd.Timestamp, pd.Timestamp],
                   feed: str, cfg: dict) -> tuple[pd.DataFrame, pd.Series]:
    """What a random trader with each mother's own footprint earns per oos2 day.

    Args:
        batches: {mother: batch folder}, the complete mothers only.
        span: What window() returned.
        feed: SQX feed name, e.g. "USDJPY_M1".
        cfg: What config() returned.

    Returns:
        One column per mother on the panel's days (`engines.nulls.footprint`), and each column's
        Monte Carlo standard error per day. It opens nothing step 20 had not opened: the
        mothers' oos2 trades and the feed's M1 bars are what `panel` already read, behind
        the same door, and the costs are the asset card's.
    """
    bars = cast(pd.DataFrame, read_bars(feed, ["Open", "High", "Low", "Close"]))
    bars = cast(pd.DataFrame, bars[(bars.index >= span[0]) & (bars.index < span[1])])
    costs = reprice.costs(feed, SEGMENT)
    got = {m: footprint.footprint(mother_trades(b, span), bars, costs, cfg["benchmark"])
           for m, b in batches.items()}
    return (pd.DataFrame({m: g[0] for m, g in got.items()}),
            pd.Series({m: g[1] for m, g in got.items()}))
