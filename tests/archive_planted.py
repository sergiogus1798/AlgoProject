"""A one-strategy archive version planted in a temporary data root: shared by the portfolio tests, not a test itself.

`plant()` must run before anything imports `core.paths` (it sets ALGO_DATA_ROOT, which that module reads once),
or be handed the root a sibling helper already planted (`archive_planted.plant(funding_planted.plant())`).
The market data is the one thing it does not invent: the root gets a symlink to the `bars/` of the first root
that has them (the env root, else the machine's own), so it works on a data root that holds only market data.
Everything else is synthetic and deterministic: a long USDJPY M30 strategy of 18 same-day trades (12 in the
build leg, 6 in oos1) priced on those real bars; its MAE/MFE and SQX daily-low curve are written by the same
engines the universe builder reconciles with, so the member reconciles and is licensed by construction. That
makes it a plumbing fixture, not a check of the rebuild against SQX (that stays a live-data test).
"""

import atexit
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

import sqx_synthetic

REPO = Path(__file__).resolve().parent.parent
VERSION = "2026-01-01T0000"
SYMBOL, FEED_KEY, TIMEFRAME, CLOCK = "USDJPY", "USDJPY_M1", "M30", "EETUS"
LEGS = {"IS": ("2012-03-05", 12), "OOS": ("2019-03-04", 6)}  # first day, trades
POINT_VALUE = 100.0
HOURS = (9, 15)  # open and close hour of every trade, on the feed's clock


def market_root() -> Path:
    """The first data root that holds `bars/`: the env root, else the machine's own."""
    env = os.environ.get("ALGO_DATA_ROOT")
    machine = yaml.safe_load(
        (REPO / "config" / "machine.yaml").read_text(encoding="utf-8")
    )
    for candidate in (env, machine["data_root"]):
        if candidate and (Path(candidate).expanduser() / "bars").is_dir():
            return Path(candidate).expanduser()
    raise FileNotFoundError("ninguna raíz de datos con bars/")


def _trades(bars: pd.DataFrame) -> pd.DataFrame:
    """The planted trades: weekly, 09:00 to 15:00 the same day, filled at the bars' own opens."""
    rows = []
    for sample, (first, count) in LEGS.items():
        for k, day in enumerate(pd.bdate_range(first, periods=count * 5)[::5]):
            rows.append(
                (
                    sample,
                    day + pd.Timedelta(hours=HOURS[0]),
                    day + pd.Timedelta(hours=HOURS[1]),
                    1.0 + 0.1 * k,
                )
            )
    frame = pd.DataFrame(
        rows, columns=pd.Index(["sample", "Open time", "Close time", "Size"])
    )
    price = bars["Open"]
    frame["Open price"] = price.reindex(frame["Open time"]).to_numpy()
    frame["Close price"] = price.reindex(frame["Close time"]).to_numpy()
    if frame[["Open price", "Close price"]].isna().any().any():
        raise ValueError(
            "las barras de mercado no cubren los días de las operaciones plantadas"
        )
    frame["Type"] = "Buy"
    frame["Close type"] = "Exit After X Bars"
    frame["Sample type"] = frame["sample"].map({"IS": "IST", "OOS": "OOST"})
    return frame


def plant(into: Path | None = None) -> dict[str, str | Path]:
    """Write the version into a data root and point ALGO_DATA_ROOT at it.

    Args:
        into: A root a sibling helper planted (ALGO_DATA_ROOT already points there); None for a fresh one.

    Returns:
        `identity`, `version` and `root`.
    """
    market = market_root()
    root = into or Path(tempfile.mkdtemp(prefix="algo-archive-"))
    if into is None:
        atexit.register(shutil.rmtree, root, ignore_errors=True)
    os.environ["ALGO_DATA_ROOT"] = str(root)
    held = sys.modules.get("core.paths")
    if held is not None and Path(held.DATA).resolve() != Path(root).resolve():
        raise RuntimeError(
            f"core.paths ya se importó con {held.DATA}: planta antes de importar nada del proyecto"
        )
    if not (root / "bars").exists():
        (root / "bars").symlink_to(market / "bars")
    from core import assetdata, sqxfile
    from core.barstore import source as bars_of
    from core.paths import archive_dir
    from portfolio.common.construct.equity import (
        days,
        excursions,
        paths,
        reconcile,
        stopexit,
    )
    from engines.market import calibrate

    bars = bars_of(FEED_KEY, ["Open", "High", "Low", "Close"])
    trades = _trades(bars)
    commission = assetdata.load(SYMBOL)["costs"]["commission"]["use"]
    segment = {"IS": "build", "OOS": "oos1"}
    fee = np.zeros(len(trades))
    for sample, seg in segment.items():
        leg = (trades["sample"] == sample).to_numpy()
        fee[leg] = commission[seg]["value"] * trades.loc[leg, "Size"].to_numpy()
    trades["Profit/Loss"] = (trades["Close price"] - trades["Open price"]) * trades[
        "Size"
    ] * POINT_VALUE - fee
    trades["Balance"] = 100000.0 + trades["Profit/Loss"].cumsum()
    point_value = calibrate.point_value(
        trades
    )  # what source.load will measure, same-day trades only
    rebuilt = stopexit.fills(
        excursions.rebuild(trades, bars, point_value), trades, bars, point_value
    )
    trades["MAE ($)"], trades["MFE ($)"] = (
        rebuilt["mae"].to_numpy(),
        rebuilt["mfe"].to_numpy(),
    )

    sqx = sqx_synthetic.write(
        root / "strategy.sqx", 0, feed=f"{FEED_KEY}_LOM_{TIMEFRAME}"
    )
    identity = sqxfile.identity(sqx)
    trades["identity"] = identity
    path = paths.minute_path(trades, bars, point_value, fee)
    low = reconcile.low_equity(days.server_days(path, CLOCK, CLOCK))
    parts, before = [], 0.0
    for sample in segment:
        leg = trades[trades["sample"] == sample]
        keep = low[
            (low.index >= leg["Open time"].min().normalize())
            & (low.index <= leg["Close time"].max().normalize())
        ]
        parts.append(
            pd.DataFrame(
                {
                    "day": keep.index,
                    "identity": identity,
                    "equity": (keep - before).to_numpy(),
                    "sample": sample,
                }
            )
        )
        before += float(leg["Profit/Loss"].sum())
    equity = pd.concat(parts, ignore_index=True)

    if not archive_dir().resolve().is_relative_to(Path(root).resolve()):
        raise RuntimeError(
            f"el archivo {archive_dir()} no está en la raíz plantada {root}"
        )
    folder = archive_dir() / identity / VERSION
    (folder / "harvest").mkdir(parents=True)
    shutil.move(sqx, folder / "strategy.sqx")
    trades.to_parquet(folder / "harvest" / "trades.parquet")
    equity.to_parquet(folder / "harvest" / "equity.parquet")
    (folder / "view.json").write_text(
        '{"tearsheet": "sin tearsheet"}', encoding="utf-8"
    )
    (folder / "manifest.json").write_text(
        json.dumps(
            {
                "identity": identity,
                "project": "Test_USDJPY_M30_planted",
                "databank": "Results",
                "step": "16.5",
                "note": "plantada",
                "archived_at": "2026-01-01T00:00:00",
                "clock": CLOCK,
                "commission": commission,
            }
        ),
        encoding="utf-8",
    )
    return {"identity": identity, "version": VERSION, "root": root}
