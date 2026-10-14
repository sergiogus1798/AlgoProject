"""The knobs, one harvest read back, and the out-of-sample window read from the trades."""

from collections.abc import Mapping
from pathlib import Path
from typing import Any, TypedDict, cast

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from core import assetdata
from core.barstore import read as read_bars
from core.paths import DATA, feed_quality_dir
from core.study import config as study_config
from core.symbols import current
from engines.market import reprice
from ledger import thresholds

CONFIG = Path(__file__).with_name("config.yaml")


class Market(TypedDict):
    """What the measured columns need of the asset behind a feed."""

    point_value: float
    risk: float
    windows: dict[str, tuple[str, str]]
    years: dict[str, float]


class Harvest(TypedDict):
    """One joined harvest, as `load` returns it."""

    metrics: pd.DataFrame
    trades: pd.DataFrame
    equity: pd.DataFrame
    curve: pd.Series
    missing: pd.DataFrame
    split: str
    end: str
    folder: str


def config(overrides: list[str]) -> dict[str, Any]:
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
    found = (
        metrics["TimeFrame [IS]"].astype(str).unique()
        if "TimeFrame [IS]" in metrics
        else []
    )
    if len(found) > 1:
        raise SystemExit(
            f"gate: la cosecha mezcla timeframes {sorted(found)}; "
            "pasa --set monkey.timeframe=<TF>"
        )
    return found[0] if len(found) == 1 else cfg["monkey"]["timeframe"]


def market(feed: str) -> Market:
    """What the measured columns need to know about the asset behind a feed.

    Args:
        feed: SQX feed name, e.g. "USDJPY_M1".

    Returns:
        `point_value`; `risk`, 1R in account currency (the doctrine's fixed risk per trade);
        and per sample ("IS" the asset's build segment, "OOS" its oos1) `windows`, as the
        pair of strings a DatetimeIndex slices by, and `years`, the segment's length.
    """
    symbol = assetdata.symbol_for(current(feed))
    if symbol is None:
        raise SystemExit(f"gate: no asset file declares the feed {feed}")
    asset = assetdata.load(symbol)
    segment = {"IS": "build", "OOS": "oos1"}
    edges = {s: assetdata.window(asset, k) for s, k in segment.items()}
    return {
        "point_value": asset["instrument"]["point_value"],
        "risk": assetdata.doctrine()["money_management"]["params"]["Amount"],
        "windows": {
            s: (str(asset["segments"][k]["from"]), str(asset["segments"][k]["to"]))
            for s, k in segment.items()
        },
        "years": {
            s: (pd.Timestamp(b, unit="ms") - pd.Timestamp(a, unit="ms")).days / 365.25
            for s, (a, b) in edges.items()
        },
    }


def check_oos1(trades: pd.DataFrame, windows: tuple[str, str], where: str) -> None:
    """Refuse a harvest whose trades labelled "OOS" are not all inside the oos1 window.

    Step 8 reads the retest databank's "OOS" as oos1; a retest task that ran past it would
    carry oos2 trades into the verdict unannounced.

    Args:
        trades: The harvest's trades, with `sample`, `Open time` and `Close time`.
        windows: `market()["windows"]["OOS"]`, the oos1 pair of strings.
        where: The harvest's folder, named in the error.

    Raises:
        ValueError: Some "OOS" trade opens outside the window.
    """
    start, end = (
        cast(pd.Period, pd.Period(windows[0])).start_time,
        cast(pd.Period, pd.Period(windows[1])).end_time,
    )
    oos = trades[trades["sample"] == "OOS"]
    # By open time: a trade opened inside oos1 is oos1's even if it closes after the window.
    out = oos[(oos["Open time"] < start) | (oos["Open time"] > end)]
    if len(out):
        raise ValueError(
            f"gate: {len(out)} operaciones «OOS» de {where} caen fuera de oos1 ({start.date()} a "
            f"{end.date()}): de {out['Open time'].min()} a {out['Close time'].max()}. La tarea de "
            "retest cubrió más que oos1; rehaz el retest sobre oos1 y vuelve a cosechar"
        )


def staged(data: Mapping[str, Any], feed: str, frame: str, out: Path) -> dict[str, Any]:
    """A harvest with everything the levels read beside it (the `data` contract of levels.py).

    Args:
        data: What `load` returned.
        feed: SQX feed name, e.g. "USA500_M1": one run is one asset and one timeframe.
        frame: That timeframe (`timeframe`).
        out: The gate's report folder: the levels leave their per-trade tables in it.

    Returns:
        `data`, with `bars` (the strategies' own timeframe, the whole file), `market`,
        `costs` and `costs_build` (reprice.costs of the feed's oos1 and build segments),
        `out`, `feed`, and `quality`, the feed's anomaly inventory, left out when it has none.

    Raises:
        ValueError: An "OOS" trade lies outside the oos1 window (`check_oos1`).
    """
    out.mkdir(parents=True, exist_ok=True)
    asset = market(feed)
    check_oos1(data["trades"], asset["windows"]["OOS"], str(data.get("folder", feed)))
    staged_data: dict[str, Any] = {
        **data,
        "bars": read_bars(feed, frame),
        "market": asset,
        "out": out,
        "feed": feed,
        "costs": reprice.costs(feed, "oos1"),
        "costs_build": reprice.costs(feed, "build"),
    }
    if (feed_quality_dir(current(feed)) / "events.parquet").exists():
        staged_data["quality"] = feed_quality_dir(current(feed))
    return staged_data


def build_pnl(data: dict, alive: pd.Index) -> pd.DataFrame:
    """The build's trades of the strategies alive at the common repricer's P/L, for R6.

    Args:
        data: What `staged` returned.
        alive: Identities still in the cascade.

    Returns:
        `identity` and `pnl` (reprice.real at the build segment's costs), in close-time order
        within each identity.
    """
    bars, raw = data["bars"], pd.DataFrame(data["trades"])
    raw = pd.DataFrame(
        raw[(raw["sample"] == "IS") & raw["identity"].isin(list(alive))]
    ).sort_values(["identity", "Close time"])
    priced = reprice.real(raw, bars, data["costs_build"], data.get("feed"))
    return pd.DataFrame(
        {"identity": raw["identity"].to_numpy(), "pnl": priced["pnl"].to_numpy()}
    )


def newest(project: str, databank: str) -> Path:
    """The most recent harvest of one databank.

    Args:
        project: Project name.
        databank: Databank name as SQX shows it.

    Returns:
        Its folder. Harvests are dated and immutable, so the newest is the current one;
        `_aparte` (what `harvest.set_aside` moved away) is not a harvest and sorts after every date.
    """
    folder = DATA / "harvest" / project / databank.replace(" ", "_")
    return sorted(p for p in folder.iterdir() if p.is_dir() and p.name[0] != "_")[-1]


def wide(path: Path) -> dict[str, pd.DataFrame]:
    """The equity file as one day × identity table per sample: what `pivot` gives, without its string sort.

    Identity and sample are read as dictionary codes and scattered into a NaN matrix.

    Args:
        path: An `equity.parquet` with `sample`, `day`, `identity` and `equity` columns.

    Returns:
        Sample -> frame, equal (`DataFrame.equals`) to `pivot(index="day", columns="identity",
        values="equity")` of that sample's rows. Raises ValueError on a repeated (day, identity),
        as `pivot` does.
    """
    t = pq.read_table(
        path,
        columns=["sample", "day", "identity", "equity"],
        read_dictionary=["identity", "sample"],
    )
    ident, samp = t["identity"].combine_chunks(), t["sample"].combine_chunks()
    names = np.asarray(ident.dictionary.to_pylist(), dtype=object)
    icode, scode = ident.indices.to_numpy(), samp.indices.to_numpy()
    day, value = t["day"].to_numpy(), t["equity"].to_numpy()
    out = {}
    for k, name in enumerate(samp.dictionary.to_pylist()):
        pick = scode == k
        if not pick.any():
            continue
        days, di = np.unique(day[pick], return_inverse=True)
        used, ii = np.unique(icode[pick], return_inverse=True)
        grid = np.full(
            (len(days), len(used)),
            np.nan,
            dtype=np.result_type(value.dtype, np.float32),
        )
        seen = np.zeros(grid.shape, dtype=bool)
        seen[di, ii] = True
        if seen.sum() != len(di):
            raise ValueError("Index contains duplicate entries, cannot reshape")
        grid[di, ii] = value[pick]
        out[name] = pd.DataFrame(
            grid,
            index=pd.DatetimeIndex(days, name="day"),
            columns=pd.Index(names[used], name="identity"),
        ).sort_index(axis=1)
    return out


def load(folder: Path) -> Harvest:
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
    curves = wide(folder / "equity.parquet")
    last = curves["IS"].index.max()
    after = curves["OOS"].diff()[curves["OOS"].index > last]
    split = cast(pd.Timestamp, after.index.min())
    daily = pd.concat([curves["IS"].diff(), after])
    return Harvest(
        metrics=metrics,
        trades=trades,
        equity=equity,
        curve=daily.cumsum(),
        missing=pd.read_csv(folder / "missing_oos.csv"),
        split=split.date().isoformat(),
        end=cast(pd.Timestamp, curves["OOS"].index.max()).date().isoformat(),
        folder=str(folder),
    )
