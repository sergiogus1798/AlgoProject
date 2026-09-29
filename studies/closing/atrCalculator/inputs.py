"""What the study is run on: its knobs, the trades of one or more exports, the bars and the windows."""

import re
from pathlib import Path

import pandas as pd

from core.assetdata import load as load_asset, window as asset_window
from core.barstore import read as read_bars
from core.paths import DATA
from core.study import config as study_config

CONFIG = Path(__file__).with_name("config.yaml")
SEGMENTS = ("build", "oos1", "oos2")
RENAMED = re.compile(r"\(\d+\)$")      # SQX appends (N) to a name that collided on load


def config(overrides: list[str]) -> dict:
    """The study's knobs, with command-line overrides applied.

    Args:
        overrides: Dotted `section.key=value` strings, as `--set` passes them.

    Returns:
        What config.yaml holds.
    """
    cfg = study_config.load(CONFIG, overrides)
    cfg["stop"]["percentiles"] = percentiles(cfg["stop"]["percentiles"])
    return cfg


def number(p: float) -> float | int:
    """A percentile as it should print: 80 rather than 80.0, 97.5 kept as it is."""
    return int(p) if float(p).is_integer() else float(p)


def percentiles(values: list[float]) -> list[float | int]:
    """The owner's percentiles, as many as he wants: checked, deduplicated, ascending.

    Args:
        values: Whatever config.yaml or `--percentiles` gave, e.g. [80, 85, 90, 95].

    Returns:
        Each strictly between 0 and 100, once, in order. Each is one sub-study: one X, one
        interval, one stability grid in SQX, so every extra percentile costs `2 * steps + 1`
        more variants per strategy.

    Raises:
        SystemExit: Empty, or a value outside (0, 100).
    """
    got = sorted({number(v) for v in values})
    if not got or not all(0 < v < 100 for v in got):
        raise SystemExit(f"atrCalculator: los percentiles van entre 0 y 100, sin incluirlos "
                         f"(recibido {values})")
    return got


def newest(project: str, databank: str) -> Path:
    """The most recent dated trade export of one databank.

    Args:
        project: Project name.
        databank: Databank name as SQX shows it.

    Returns:
        Its `trades.parquet`. Prefers an export tagged `--batch stopgrid`
        (`sqx.export.export_retest`) over the untagged layout an older export used, so a
        same-day structural export (step 23, tag `structure`) into the same databank cannot
        shadow this one.
    """
    folder = DATA / "raw" / project / databank.replace(" ", "_")
    tagged = sorted(folder.glob("*/stopgrid/trades.parquet"))
    if tagged:
        return tagged[-1]
    return sorted(folder.glob("*/trades.parquet"))[-1]


def windows(symbol: str) -> dict[str, tuple[pd.Timestamp, pd.Timestamp]]:
    """Each segment's first instant and the instant after its last, from the asset's policy.

    Args:
        symbol: Asset name, e.g. "XAUUSD".

    Returns:
        {"build": (start, end), "oos1": ..., "oos2": ...}, UTC-naive to match the trades.
    """
    data = load_asset(symbol)
    return {s: tuple(pd.Timestamp(t, unit="ms") for t in asset_window(data, s))
            for s in SEGMENTS}


def trades(packed: list[Path], feed: str, spans: dict) -> pd.DataFrame:
    """Every trade of several exports on the main market, each tagged with its segment.

    Args:
        packed: `trades.parquet` files — the three WFC legs of one retest, or one export
            that already spans the windows.
        feed: The main market's SQX symbol; a leg that also carried extra markets keeps
            them in the same file, and they are not this strategy's trades.
        spans: What `windows` returned.

    Returns:
        One frame, `segment` cut by `Open time` against the policy — no code tags oos2, and
        a leg that ran one segment is still cut, so a trade can never count in two windows.
        Trades outside every segment are dropped. `strategy` has SQX's collision suffix
        stripped, so it joins the batch's `variant_id`.
    """
    frames = [pd.read_parquet(p) for p in packed]
    frame = pd.concat(frames, ignore_index=True)
    frame["strategy"] = frame["strategy"].astype(str).str.replace(RENAMED, "", regex=True)
    if "Symbol" in frame:              # exports older than export_retest carry no Symbol
        frame = frame[frame["Symbol"].astype(str) == feed]
    frame["segment"] = None
    for name, (start, end) in spans.items():
        inside = (frame["Open time"] >= start) & (frame["Open time"] < end)
        frame.loc[inside, "segment"] = name
    return frame[frame["segment"].notna()].sort_values(["strategy", "Open time"]) \
        .reset_index(drop=True)


def bars(feed: str, timeframe: str) -> pd.DataFrame:
    """The strategy's own timeframe, whole: the ATR forgets its start in a few hundred bars.

    Args:
        feed: The SQX feed name, e.g. "XAUUSD_DukasM1_Infinox".
        timeframe: "M30", "H1" and the rest; resampled from M1 and cached by barstore.

    Returns:
        One row per bar, indexed by open time.
    """
    return read_bars(feed, timeframe)


def point_value(symbol: str) -> float:
    """Account currency per 1.0 of price and 1.0 of lot, from the asset file."""
    return float(load_asset(symbol)["instrument"]["point_value"])


def batch(work: Path) -> pd.DataFrame:
    """The stop-loss batch's manifest: which file is which mother, and which X it carries.

    Args:
        work: The folder `sqx.variants.stopgrid` wrote.

    Returns:
        One row per variant: `variant_id`, `strategy` (the mother), `mother` path,
        `stratum` (reference, probe, grid), `percentile`, `step`, `x`.
    """
    return pd.read_parquet(work / "manifest.parquet")
