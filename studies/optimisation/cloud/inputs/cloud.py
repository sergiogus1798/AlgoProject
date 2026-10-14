"""The cloud this study reads: each variant's parameters and its excess per year, on build and on oos1."""

from typing import Any, cast
from pathlib import Path

import pandas as pd
import yaml

from core import assetdata, barstore
from core.paths import ROOT
from engines.market import reprice
from engines.variants import excess, filters, look

LEGS = (
    "build",
    "oos1",
)  # the only legs ever asked of the parquet: the map never reads oos2
# The measure's parameters are the gate's, not a copy: the map's excess is step 14's.
GATE = ROOT / "studies" / "screening" / "gate" / "config.yaml"


def measured(work: Path) -> pd.DataFrame:
    """Every returned variant of a batch with its excess on the main market, per leg.

    Args:
        work: The batch directory: `manifest.parquet`, `metrics.parquet`, `segments.parquet`
            and `variant_trades.parquet` (`sqx.variants.varianttrades`).

    Returns:
        One row per variant SQX returned: `variant_id`, `stratum`, `origin`, the `param_`
        columns and, per leg of LEGS, `<leg>_excess` (account currency per year of the
        window, `engines.variants.excess`), `<leg>_profit` and `<leg>_trades`. A variant
        without a trade in a leg has zeros there. Of `metrics.parquet` only `variant_id` is
        read, and of the trades only the two legs, filtered before a row is loaded.
    """
    symbol, timeframe = look.market(work)
    asset = assetdata.load(symbol)
    feed = asset["sqx_symbol"]
    bars = barstore.read(feed, timeframe)
    drift = yaml.safe_load(GATE.read_text(encoding="utf-8"))["drift"]
    back = pd.read_parquet(work / "metrics.parquet", columns=["variant_id"])[
        "variant_id"
    ]
    plan = pd.read_parquet(work / "manifest.parquet")
    keep = ["variant_id", "stratum", "origin"] + [
        c for c in plan.columns if c.startswith("param_")
    ]
    frame = plan.loc[plan["variant_id"].isin(back), keep].reset_index(drop=True)
    for leg in LEGS:
        trades = cast(
            pd.DataFrame,
            pd.read_parquet(
                work / "variant_trades.parquet",
                filters=[("leg", "==", leg), ("market", "==", look.MAIN)],
            ),
        )
        trades["variant_id"] = trades["variant_id"].astype(str)
        span = (str(asset["segments"][leg]["from"]), str(asset["segments"][leg]["to"]))
        first, end = pd.to_datetime(assetdata.window(asset, leg), unit="ms")
        per = excess.per_trade(
            trades, bars, reprice.costs(feed, leg), span, drift, feed
        )
        got = cast(
            pd.DataFrame,
            per.groupby("variant_id").agg(
                profit=("profit", "sum"), trades=("profit", "size")
            ),
        )
        got["excess"] = excess.per_year(per, (first, end - pd.Timedelta(days=1)))
        frame = frame.merge(
            got.add_prefix(f"{leg}_"),
            left_on="variant_id",
            right_index=True,
            how="left",
        )
    return frame.fillna(
        {
            f"{leg}_{name}": 0.0
            for leg in LEGS
            for name in ("excess", "profit", "trades")
        }
    )


def screen(
    frame: pd.DataFrame, floor_per_param: float
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """The variants the map is drawn with: no controls, the inside floor, no exact duplicates.

    Args:
        frame: What `measured` returned.
        floor_per_param: Trades on build a variant needs per live parameter.

    Returns:
        (the surviving rows; counts = {lote, controles, suelo_dentro, duplicados, quedan,
        vivos, suelo, avisos}). `suelo` is the trades asked for, `vivos` the parameters that
        vary once the controls are out — the factory moves no other. A mother under the
        floor warns and the floor is not applied.
        A duplicate is the same profit to the cent on build AND on oos1; the mother is the
        copy kept.
    """
    counts: dict[str, Any] = {"lote": len(frame)}
    notes: list[str] = []
    left = cast(pd.DataFrame, frame[~frame["stratum"].isin(filters.CONTROLS)])
    counts["controles"] = len(frame) - len(left)
    params = [c for c in frame.columns if c.startswith("param_")]
    counts["vivos"] = int(cast(pd.Series, left[params].nunique() > 1).sum())
    need = counts["suelo"] = floor_per_param * counts["vivos"]
    mother = left.loc[left["origin"], "build_trades"].iloc[0]
    if mother < need:
        notes.append(
            f"La madre hace {mother:.0f} operaciones en build y el suelo son "
            f"{need:.0f}: el suelo no se aplica."
        )
    else:
        left = cast(pd.DataFrame, left[left["build_trades"] >= need])
    counts["suelo_dentro"] = len(frame) - counts["controles"] - len(left)
    first = left.sort_values("origin", ascending=False, kind="stable")
    same = (
        first[["build_profit", "oos1_profit"]].round(2).duplicated().reindex(left.index)
    )
    counts |= {
        "duplicados": int(same.sum()),
        "quedan": int((~same).sum()),
        "avisos": notes,
    }
    return cast(pd.DataFrame, left[~same]).reset_index(drop=True), counts
