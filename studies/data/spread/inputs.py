"""What the spread study reads: its knobs, a tick feed's minutes, Dukascopy's daily volatility, a harvest."""

import json
import tarfile
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from core import assetdata, cfx, manifest, tickfile
from core.barstore import source
from core.datapaths import retired_project, spread_dir, tick_file
from core.paths import DATA, bar_source
from core.study import config as study_config
from ledger import thresholds

CONFIG = Path(__file__).with_name("config.yaml")
TRADE_COLUMNS = ["identity", "sample", "Type", "Open time", "Open price", "Close time",
                 "Close price", "Size", "Profit/Loss"]


def config(overrides: list[str]) -> dict:
    """Every knob, `ledger:` placeholders filled, command-line overrides applied."""
    return study_config.apply(thresholds.fill(study_config.load(CONFIG, [])), overrides)


def asset(symbol: str) -> dict:
    """The asset as `assets/` declares it (tick size, point value, segments, costs)."""
    return assetdata.load(symbol)


def minutes(feed: str) -> pd.DataFrame:
    """One tick feed's minute table, decoded once and cached beside the `.dat`'s stamp.

    Args:
        feed: SQX tick feed, e.g. "XAUUSD_DarwTick_Infinox".

    Returns:
        `core.tickfile.minutes()`'s frame. The cache is rebuilt when the `.dat` changed size
        or date — SQX appends to it on a data update — so it never answers with old ticks.
    """
    dat = tick_file(feed).stat()
    stamp = {"size": dat.st_size, "mtime": int(dat.st_mtime)}
    folder = spread_dir(feed)
    cached, meta = folder / "minutes.parquet", folder / "minutes.json"
    if meta.exists() and json.loads(meta.read_text())["stamp"] == stamp:
        return pd.read_parquet(cached)
    frame, ticks = tickfile.minutes(feed)
    folder.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(cached)
    meta.write_text(json.dumps({"stamp": stamp, "ticks": ticks, "minutes": len(frame),
                                "from": str(frame.index[0]), "to": str(frame.index[-1])}))
    return frame


def volatility(feed: str) -> pd.DataFrame:
    """Dukascopy's daily volatility and price, for every day its M1 bars cover.

    Args:
        feed: SQX M1 feed, e.g. "XAUUSD_DukasM1_Infinox".

    Returns:
        Indexed by day: `rv` the mean absolute 1-minute log return, `price` the median close.
        The one thing known in every year, Darwinex's or not, that the spread may follow.
        From the bar library, or straight from SQX's own M1 file for a feed it lacks.
    """
    close = (source(feed, ["Close"]) if bar_source(feed).exists() else tickfile.bars(feed))["Close"]
    moves = np.log(close).diff().abs()
    day = close.index.normalize()
    got = pd.DataFrame({"rv": moves.groupby(day).mean(), "price": close.groupby(day).median()})
    return got[got["rv"] > 0]   # a day without a single move is no trading day


def harvest(project: str, databank: str) -> Path:
    """The newest harvest of one build databank (dated and immutable, so the newest is current)."""
    folder = DATA / "harvest" / project / databank.replace(" ", "_")
    return sorted(p for p in folder.iterdir() if p.is_dir())[-1]


def trades(folder: Path) -> pd.DataFrame:
    """A harvest's trades, IS and OOS, with what a repricing needs."""
    return pd.read_parquet(folder / "trades.parquet", columns=TRADE_COLUMNS)


def names(folder: Path) -> pd.Series:
    """identity -> the strategy's name in the retest databank."""
    return pd.read_parquet(folder / "metrics.parquet", columns=["strategy"])["strategy"]


def _cfx(install: Path, project: str, into: Path) -> str:
    """The project's `project.cfx`: live on its install, or out of its archive once retired.

    Returns:
        A path. `Test_` projects are retired when their task ends (hard rule 6), so a
        harvest outlives its project as a rule, and the archive keeps the `.cfx`.
    """
    live = install / "user" / "projects" / project / "project.cfx"
    if live.exists():
        return str(live)
    archive = sorted(retired_project(install.name, project, "*").parent.glob(f"{project}-*.tar.gz"))[-1]
    with tarfile.open(archive) as tar:
        tar.extract(f"{project}/project.cfx", into)
    return str(into / project / "project.cfx")


def _task_costs(folder: Path, feed: str, what: str) -> dict:
    """One cost each sample's SQX task carried for `feed`, in price units, read from its project.

    Args:
        folder: A harvest folder; its manifest names the install, the project and the two databanks.
        feed: The feed the strategies were built on.
        what: "spread" (the `<Chart spread=…>`) or "slippage" (its `<Setup slippage=…>`).

    Returns:
        {"IS": value, "OOS": value}: of the task writing the build databank and of the one
        writing the retest databank, times the tick size. Read, never assumed: a project may
        carry any cost whatever `assets/` says today.
    """
    src = manifest.read(folder)["source"]
    tick = asset(assetdata.symbol_for(feed))["instrument"]["tick_size"]
    wanted = {src["databank"]: "IS", src["oos_databank"]: "OOS"}
    out = {}
    with tempfile.TemporaryDirectory() as tmp:
        project = _cfx(Path(src["install"]), src["project"], Path(tmp))
        for task in cfx.tasks(project):
            root = cfx.task_xml(project, task["file"])
            setup = next((s for s in root.iter("Setup") if s.find(f"Chart[@symbol='{feed}']") is not None), None)
            if cfx.output_databank(root) in wanted and setup is not None:
                node = setup.find(f"Chart[@symbol='{feed}']") if what == "spread" else setup
                out[wanted[cfx.output_databank(root)]] = float(node.get(what)) * tick
    return out


def charged(folder: Path, feed: str) -> dict:
    """The spread each sample's task charged, in price: {"IS": …, "OOS": …}."""
    return _task_costs(folder, feed, "spread")


def slippage(folder: Path, feed: str) -> dict:
    """The slippage each sample's task charged per fill, in price: {"IS": …, "OOS": …}."""
    return _task_costs(folder, feed, "slippage")
