"""The knobs, one harvest read back, and the out-of-sample window read from the trades."""

from pathlib import Path

import pandas as pd

from core.paths import DATA
from core.study import config as study_config
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
        the curve is glued on daily returns rather than on levels: the boundary is the
        first day the retest covers, and whatever the build window ran past it is dropped
        rather than double counted.
    """
    metrics = pd.read_parquet(folder / "metrics.parquet")
    trades = pd.read_parquet(folder / "trades.parquet")
    equity = pd.read_parquet(folder / "equity.parquet")
    wide = {side: block.pivot(index="day", columns="identity", values="equity")
            for side, block in equity.groupby("sample")}
    split = wide["OOS"].index.min()
    daily = pd.concat([wide["IS"][wide["IS"].index < split].diff(), wide["OOS"].diff()])
    return {"metrics": metrics, "trades": trades, "equity": equity,
            "curve": daily.cumsum(), "missing": pd.read_csv(folder / "missing_oos.csv"),
            "split": split.date().isoformat(),
            "end": wide["OOS"].index.max().date().isoformat()}
