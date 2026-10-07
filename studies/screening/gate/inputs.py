"""The knobs, one harvest read back, and the out-of-sample window read from the trades."""

from pathlib import Path

import numpy as np
import pandas as pd

from core import assetdata
from core.barstore import read as read_bars
from core.paths import DATA, feed_quality_dir
from core.study import config as study_config
from core.symbols import current
from engines.market import reprice
from ledger import thresholds

CONFIG = Path(__file__).with_name("config.yaml")


def config(overrides: list[str]) -> dict:
    """Every knob, with command-line overrides applied.

    Args:
        overrides: "section.key=value" strings, as --set gives them. A screen's threshold
            is addressed by its own name, e.g. "degradacion.min_retention=0.5".

    Returns:
        The parsed config.yaml, every `ledger:<key>` replaced by the number
        `ledger/thresholds.yaml` declares. Each override keeps the type of the value it
        replaces (core.study.config), so a threshold typed on the command line cannot
        silently become a string.
    """
    cfg = thresholds.fill(study_config.load(CONFIG, []))
    return study_config.apply(cfg, overrides, {s["name"]: s for s in cfg["screens"]})


def timeframe(metrics: pd.DataFrame, cfg: dict, overrides: list[str]) -> str:
    """The bar grid the monkeys are placed on: an explicit --set, else the harvest's own.

    Args:
        metrics: `load()["metrics"]`, carrying `TimeFrame [IS]`.
        cfg: What `config()` returned.
        overrides: The --set strings the command line gave.

    Returns:
        The override, else the one timeframe the strategies were built on, else config.yaml's.

    Raises:
        SystemExit: The harvest mixes timeframes and none was given.
    """
    for item in overrides:
        if item.startswith("monkey.timeframe="):
            return item.split("=", 1)[1]
    found = metrics["TimeFrame [IS]"].astype(str).unique() if "TimeFrame [IS]" in metrics else []
    if len(found) > 1:
        raise SystemExit(f"gate: la cosecha mezcla timeframes {sorted(found)}; "
                         "pasa --set monkey.timeframe=<TF>")
    return found[0] if len(found) == 1 else cfg["monkey"]["timeframe"]


def market(feed: str) -> dict:
    """What the measured columns need to know about the asset behind a feed.

    Args:
        feed: SQX feed name, e.g. "USDJPY_M1".

    Returns:
        `point_value`; `risk`, 1R in account currency (the doctrine's fixed risk per trade);
        and per sample ("IS" the asset's build segment, "OOS" its oos1) `windows`, as the
        pair of strings a DatetimeIndex slices by, and `years`, the segment's length.
    """
    asset = assetdata.load(assetdata.symbol_for(current(feed)))
    segment = {"IS": "build", "OOS": "oos1"}
    edges = {s: assetdata.window(asset, k) for s, k in segment.items()}
    return {"point_value": asset["instrument"]["point_value"],
            "risk": assetdata.doctrine()["money_management"]["params"]["Amount"],
            "windows": {s: (str(asset["segments"][k]["from"]), str(asset["segments"][k]["to"]))
                        for s, k in segment.items()},
            "years": {s: (pd.Timestamp(b, unit="ms") - pd.Timestamp(a, unit="ms")).days / 365.25
                      for s, (a, b) in edges.items()}}


def staged(data: dict, feed: str, frame: str, out: Path) -> dict:
    """A harvest with everything the levels read beside it (the `data` contract of levels.py).

    Args:
        data: What `load` returned.
        feed: SQX feed name, e.g. "USA500_M1": one run is one asset and one timeframe.
        frame: That timeframe (`timeframe`).
        out: The gate's report folder: the levels leave their per-trade tables in it.

    Returns:
        `data`, with `bars` (the strategies' own timeframe, the whole file), `market`,
        `costs` and `costs_build` (reprice.costs of the feed's oos1 and build segments),
        `out`, and `quality`, the feed's anomaly inventory, left out when it has none.
    """
    out.mkdir(parents=True, exist_ok=True)
    data.update(bars=read_bars(feed, frame), market=market(feed), out=out,
                costs=reprice.costs(feed, "oos1"), costs_build=reprice.costs(feed, "build"))
    if (feed_quality_dir(current(feed)) / "events.parquet").exists():
        data["quality"] = feed_quality_dir(current(feed))
    return data


def build_pnl(data: dict, alive: pd.Index) -> pd.DataFrame:
    """The build's trades of the strategies alive at the common repricer's P/L, for R6.

    Args:
        data: What `staged` returned.
        alive: Identities still in the cascade.

    Returns:
        `identity` and `pnl` (reprice.pnl at the build segment's costs), in close-time order
        within each identity.
    """
    bars, raw = data["bars"], data["trades"]
    raw = (raw[(raw["sample"] == "IS") & raw["identity"].isin(alive)]
           .sort_values(["identity", "Close time"]))
    enter, leave = (bars.index.get_indexer(raw[k]) for k in ("Open time", "Close time"))
    assert (enter >= 0).all() and (leave >= 0).all(), "a build trade is stamped off the bar grid"
    side = np.where(raw["Type"].astype(str) == "Sell", -1.0, 1.0)
    pnl, _ = reprice.pnl(reprice.fills(bars, enter), reprice.fills(bars, leave),
                         raw["Open time"].to_numpy(), raw["Close time"].to_numpy(), side,
                         raw["Size"].to_numpy(), data["costs_build"])
    return pd.DataFrame({"identity": raw["identity"].to_numpy(), "pnl": pnl})


def newest(project: str, databank: str) -> Path:
    """The most recent harvest of one databank.

    Args:
        project: Project name.
        databank: Databank name as SQX shows it.

    Returns:
        Its folder. Harvests are dated and immutable, so the newest is the current one.
    """
    folder = DATA / "harvest" / project / databank.replace(" ", "_")
    return sorted(p for p in folder.iterdir() if p.is_dir())[-1]


def load(folder: Path) -> dict:
    """One joined harvest, and the window each side actually occupies.

    Args:
        folder: A harvest directory.

    Returns:
        `metrics` indexed by identity, `trades` and `equity` carrying a `sample` column
        that says which databank each row came from, `equity` also pivoted into `curve`
        — one continuous daily P&L per strategy — and `missing`, the strategies the build
        databank holds and the retest databank does not.

        The two windows are two separate backtests with their own spread and slippage, so
        the curve is glued on daily returns rather than on levels. The boundary is the last
        day the build curve covers: the retest's curve opens ~2 months before its segment
        with zero P&L (knowhow/sqx-format/leg-curve-warmup.md), so its first day would cut
        the build window short and drop its last weeks.
    """
    metrics = pd.read_parquet(folder / "metrics.parquet")
    trades = pd.read_parquet(folder / "trades.parquet")
    equity = pd.read_parquet(folder / "equity.parquet")
    wide = {side: block.pivot(index="day", columns="identity", values="equity")
            for side, block in equity.groupby("sample")}
    last = wide["IS"].index.max()
    after = wide["OOS"].diff()[wide["OOS"].index > last]
    split = after.index.min()
    daily = pd.concat([wide["IS"].diff(), after])
    return {"metrics": metrics, "trades": trades, "equity": equity,
            "curve": daily.cumsum(), "missing": pd.read_csv(folder / "missing_oos.csv"),
            "split": split.date().isoformat(),
            "end": wide["OOS"].index.max().date().isoformat()}
