"""A variant batch as the CSCV's cells: weekly excess per variant, net and gross, cached beside the batch."""

from typing import Any, TypedDict, cast
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from core import assetdata, barstore, fanout
from core.study.config import fingerprint as digest
from engines.market import reprice
from engines.variants import filters, fingerprint
from engines.variants.panel import SEGMENTS
from engines.weekly import panel

TRADES = "variant_trades.parquet"  # written by sqx.variants.varianttrades
WEEKLY = "cscv_weekly.parquet"  # the cache: weeks x (net | gross, variant)
VARIANTS = (
    "cscv_variants.parquet"  # the cache: per variant, its trades and its fingerprint
)
MAIN = "Main"
PIECES = 16  # groups of variants priced side by side, per leg
# The excess is step 14's: the gate's drift block, never a copy of its values.
GATE = Path(__file__).resolve().parents[3] / "screening" / "gate" / "config.yaml"

# What the pricing workers read, set before the fork.
_SHARED: dict = {}


def drift() -> dict[str, Any]:
    """The gate's `drift` block: the window and the variant of the drift term."""
    return yaml.safe_load(GATE.read_text(encoding="utf-8"))["drift"]


def window(asset: dict) -> tuple[str, str]:
    """First day of `build` and last day of `oos2` as full dates: the whole history."""
    last = asset["segments"][SEGMENTS[-1]]["to"]
    return (
        assetdata.segment_start(asset, SEGMENTS[0]),
        f"{last}-12-31" if isinstance(last, int) else str(last),
    )


def _priced(key: tuple[str, int]) -> pd.DataFrame:
    """One leg's trades of one group of variants, each with its net and gross excess."""
    leg, piece = key
    got = _SHARED
    trades = got["trades"][leg]
    trades = trades[trades["variant_id"].isin(got["pieces"][piece])]
    bounds = got["asset"]["segments"][leg]
    per = panel.per_trade(
        trades,
        got["bars"],
        got["costs"][leg],
        (str(bounds["from"]), str(bounds["to"])),
        got["drift"],
        got["feed"],
    )
    return cast(pd.DataFrame, per[["variant_id", "close", "net", "gross"]])


def build(
    trades: pd.DataFrame,
    bars: pd.DataFrame,
    asset: dict,
    costs: dict,
    term: dict,
    workers: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """The weekly panel and the per-variant facts of one batch's trades.

    Args:
        trades: Every trade on the main market, the three legs, with `leg` and `variant_id`.
        bars: The batch's own timeframe, the whole file.
        asset: `assetdata.load` of the batch's asset.
        costs: Leg -> `reprice.costs`.
        term: The drift block.
        workers: Processes to price with.

    Returns:
        (weeks x (`net` | `gross`, variant): each trade whole in the week it closes in, over
        the whole history; per variant, `trades` and `print`, its trade list's fingerprint).
    """
    ids = np.sort(np.asarray(trades["variant_id"].unique()))
    _SHARED.update(
        trades={leg: trades[trades["leg"] == leg] for leg in SEGMENTS},
        bars=bars,
        asset=asset,
        costs=costs,
        drift=term,
        feed=asset["sqx_symbol"],
        pieces=np.array_split(ids, min(PIECES, len(ids))),
    )
    load = {
        (leg, i): int(_SHARED["trades"][leg]["variant_id"].isin(piece).sum())
        for leg in SEGMENTS
        for i, piece in enumerate(_SHARED["pieces"])
    }
    per = pd.concat(
        [
            got
            for _, got in fanout.run(
                _priced, {key: rows for key, rows in load.items() if rows}, workers
            )
        ]
    )
    _SHARED.clear()
    wide = panel.weekly(per, window(asset), units=cast(Any, ids))
    info = pd.DataFrame(
        {
            "trades": trades.groupby("variant_id").size(),
            "print": fingerprint.prints(trades),
        }
    )
    return pd.concat(wide, axis=1), info


class Weekly(TypedDict):
    """A batch's weekly cells: net and gross excess, per-variant info, years, cache flag, seconds."""

    net: pd.DataFrame
    gross: pd.DataFrame
    info: pd.DataFrame
    years: float
    cached: bool
    wall_s: float


def read(work: Path, symbol: str, timeframe: str, workers: int) -> Weekly:
    """The batch's weekly cells, from the cache when it is this batch's under these costs.

    Args:
        work: The batch folder, holding `variant_trades.parquet`.
        symbol, timeframe: The batch's main market (`engines.variants.look.market`).
        workers: Processes to price with when the cache has to be built.

    Returns:
        `net` and `gross` (weeks x variants, account currency), `info` (per variant: `trades`,
        `print`), `years` (length of the whole history), `cached` and `wall_s`.
    """
    began = time.time()
    asset = assetdata.load(symbol)
    costs = {leg: reprice.costs(asset["sqx_symbol"], leg) for leg in SEGMENTS}
    stat, term = (work / TRADES).stat(), drift()
    key = digest(
        {
            "trades": [stat.st_mtime_ns, stat.st_size],
            "drift": term,
            "costs": costs,
            "window": window(asset),
            "timeframe": timeframe,
        }
    )
    wide = pd.read_parquet(work / WEEKLY) if (work / WEEKLY).exists() else None
    cached = wide is not None and wide.attrs.get("key") == key
    if not cached:
        trades = pd.read_parquet(work / TRADES, filters=[("market", "==", MAIN)])
        trades = trades.assign(variant_id=trades["variant_id"].astype(str))
        wide, info = build(
            trades,
            barstore.read(asset["sqx_symbol"], timeframe),
            asset,
            costs,
            term,
            workers,
        )
        wide.attrs["key"] = key
        wide.to_parquet(work / WEEKLY)
        info.to_parquet(work / VARIANTS)
    assert wide is not None  # cached implies it was read; otherwise it was just built
    return {
        "net": cast(pd.DataFrame, wide["net"]),
        "gross": cast(pd.DataFrame, wide["gross"]),
        "info": pd.read_parquet(work / VARIANTS),
        "years": panel.years(window(asset)),
        "cached": bool(cached),
        "wall_s": time.time() - began,
    }


def live(metrics: pd.DataFrame) -> int:
    """How many parameters actually move in the batch, its controls left out."""
    params = metrics.loc[~metrics["stratum"].isin(filters.CONTROLS)].filter(
        like="param_"
    )
    return int((params.nunique() > 1).sum())


def screen(
    metrics: pd.DataFrame, info: pd.DataFrame, years: float, knobs: dict
) -> tuple[list[str], dict]:
    """The variants that enter the panel, and how many each filter removed.

    Controls out; variants without a trade out; exact duplicates (equal trade lists) cut to
    one, the mother first; then the two floors over the whole history. A mother under a floor
    warns and that floor is not applied.

    Args:
        metrics: Contract C3: `variant_id`, `stratum`, one `param_*` per parameter.
        info: Per variant, `trades` and `print` (read()).
        years: Length of the whole history.
        knobs: The config's `panel` section.

    Returns:
        (the variants kept, in `metrics`' order; `lote`, `controles`, `sin_operaciones`,
        `duplicados`, `duplicados_pct` (the share of the traded design variants that were
        copies), `suelo_parametros`, `suelo_anual`, `quedan`, `vivos`, `madre` and `avisos`).
    """
    ids = metrics["variant_id"].astype(str)
    design = cast(pd.Series, ids[~metrics["stratum"].isin(filters.CONTROLS)])
    traded = cast(pd.Series, design[design.isin(cast(Any, info.index))])
    mother = cast(pd.Series, ids[metrics["stratum"] == filters.ORIGIN]).iloc[0]
    kept, share = fingerprint.keep(info.loc[traded, "print"], first=[mother])
    counts = {
        "lote": len(ids),
        "controles": len(ids) - len(design),
        "sin_operaciones": len(design) - len(traded),
        "duplicados": len(traded) - len(kept),
        "duplicados_pct": share,
        "vivos": live(metrics),
        "madre": mother,
        "avisos": [],
    }
    count = info.loc[kept, "trades"]
    for name, need in (
        ("suelo_parametros", knobs["floor_per_param"] * counts["vivos"]),
        ("suelo_anual", knobs["floor_per_year"] * years),
    ):
        if count[mother] < need:
            counts["avisos"].append(
                f"{name}: la madre ({count[mother]:.0f} operaciones) no "
                f"llega a {need:.0f}; el suelo no se aplica"
            )
            counts[name] = 0
            continue
        counts[name] = int((count < need).sum())
        count = count[count >= need]
    counts["quedan"] = len(count)
    return [v for v in ids if v in count.index], counts
