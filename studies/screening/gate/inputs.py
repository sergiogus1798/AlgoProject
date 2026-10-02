"""The knobs, one harvest read back, and the out-of-sample window read from the trades."""

from pathlib import Path

import pandas as pd

from core import assetdata
from core.paths import DATA
from core.study import config as study_config
from core.symbols import current
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
