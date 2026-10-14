"""A variant batch's trades on every market as weekly excess, gross and net, one leg at a time."""

from typing import Any, TypedDict, cast
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from core import assetdata, barstore, fanout
from engines.market import reprice
from engines.variants import filters, fingerprint
from engines.weekly import panel

TRADES = "variant_trades.parquet"  # written by sqx.variants.varianttrades
MAIN = "Main"
# The excess is step 14's: the gate's drift block, never a copy of its values.
GATE = Path(__file__).resolve().parents[3] / "screening" / "gate" / "config.yaml"
EMPTY = pd.DataFrame(
    {
        "variant_id": pd.Series(dtype=str),
        "net": [],
        "gross": [],
        "profit": [],
        "open": pd.Series(dtype="datetime64[ns]"),
        "close": pd.Series(dtype="datetime64[ns]"),
    }
)
_JOB: dict = {}  # what a forked worker reads: set by read()


def drift() -> dict[str, Any]:
    """The gate's `drift` block: the window and the variant of the drift term."""
    return yaml.safe_load(GATE.read_text(encoding="utf-8"))["drift"]


def span(asset: dict, leg: str) -> tuple[str, str]:
    """The declared bounds of one leg, as strings a DatetimeIndex slices by."""
    return (str(asset["segments"][leg]["from"]), str(asset["segments"][leg]["to"]))


def window(asset: dict, leg: str) -> tuple[str, str]:
    """First and last day of one leg as full dates, both inside; a bare year is whole."""
    last = asset["segments"][leg]["to"]
    return (
        assetdata.segment_start(asset, leg),
        f"{last}-12-31" if isinstance(last, int) else str(last),
    )


def years(asset: dict, leg: str, data_from: str | None = None) -> float:
    """Length in years of one leg on a market whose data starts at `data_from` (never negative)."""
    first, last = window(asset, leg)
    return max(0.0, panel.years((max(first, data_from or first), last)))


class Design(TypedDict):
    """A batch's design: its non-control variants, the mother, the live parameters, the grid."""

    ids: list[str]
    params: pd.DataFrame
    k: int
    mother: str


def variants(work: Path) -> Design:
    """The batch's design: which variants are read, which is the mother, how many parameters move.

    Args:
        work: The batch folder, holding `metrics.parquet` (contract C3).

    Returns:
        `ids` (every variant that is not a control, in the file's order), `mother` (its
        `variant_id`), `k` (parameters taking more than one value among them) and `params`
        (`variant_id` down, one `param_*` column each).
    """
    metrics = pd.read_parquet(work / "metrics.parquet")
    kept = metrics[~metrics["stratum"].isin(filters.CONTROLS)]
    params = kept.set_index(kept["variant_id"].astype(str)).filter(like="param_")
    return {
        "ids": list(params.index),
        "params": params,
        "k": int((params.nunique() > 1).sum()),
        "mother": str(
            kept.loc[kept["stratum"] == filters.ORIGIN, "variant_id"].iloc[0]
        ),
    }


def one(market: str) -> dict[str, Any]:
    """One market's legs, repriced: what a worker of read() returns.

    Args:
        market: `Main`, or a feed of `_markets.yaml`; `_JOB` says the rest.

    Returns:
        `legs`: leg -> `gross` and `net` (weeks x variants of that leg, `panel.weekly`), `n`
        (trades per variant), `trades`, `straddle` (`panel.straddle`), `gap` (the share of
        variants whose repriced P/L misses SQX's NetProfit, None without trades); and, on
        `Main` only, `prints`: the fingerprint of each variant's trades over these legs.
    """
    job = _JOB
    feed = job["feed"] if market == MAIN else market
    bars, ids, legs, raw = barstore.read(feed, job["timeframe"]), job["ids"], {}, []
    for leg in job["legs"][market]:
        got = pd.read_parquet(
            job["work"] / TRADES, filters=[("leg", "==", leg), ("market", "==", market)]
        )
        got = got.assign(variant_id=got["variant_id"].astype(str))
        got = cast(pd.DataFrame, got[got["variant_id"].isin(ids)])
        per, gap = EMPTY, None
        if len(got):
            per = panel.per_trade(
                got,
                bars,
                reprice.costs(feed, leg),
                span(job["asset"], leg),
                job["drift"],
                feed,
            )
            sqx = pd.read_parquet(
                job["work"] / "segments.parquet",
                columns=["variant_id", "NetProfit"],
                filters=[("segment", "==", leg), ("market", "==", market)],
            )
            sqx = cast(
                pd.Series,
                sqx.set_index(sqx["variant_id"].astype(str))["NetProfit"]
                .reindex(ids)
                .dropna(),
            )
            gap = panel.sqx_gap(
                per,
                sqx,
                tolerance=job["costs"]["tolerance"],
                relative=job["costs"]["relative"],
            )[0]
        weekly = panel.weekly(per, window(job["asset"], leg), units=ids)
        legs[leg] = weekly | {
            "n": per["variant_id"].value_counts().reindex(ids, fill_value=0).to_numpy(),
            "trades": len(per),
            "gap": gap,
            "straddle": panel.straddle(
                cast(pd.Series, per["open"]), cast(pd.Series, per["close"])
            )
            if len(per)
            else 0.0,
        }
        raw.append(got)
    return {"legs": legs} | (
        {"prints": fingerprint.prints(pd.concat(raw))} if market == MAIN else {}
    )


def read(
    work: Path,
    symbol: str,
    timeframe: str,
    legs: dict[str, tuple],
    ids: list[str],
    cfg: dict,
) -> dict[str, dict]:
    """Every market of the reading, each on its own bars and at its own costs.

    Args:
        work: The batch folder, holding `variant_trades.parquet` and `segments.parquet`.
        symbol, timeframe: The batch's main market (`engines.variants.look.market`).
        legs: `Main` and each feed -> the legs to read there. A leg that is not named is
            never opened: the parquet read carries the leg filter.
        ids: The variants read (`variants`).
        cfg: The study's config: `costs` and `workers`.

    Returns:
        Market -> what one() returned, in the order of `legs`. The legs' dates are the main
        asset's on every market, so the weeks line up; the drift and the costs are each
        market's own.
    """
    asset = assetdata.load(symbol)
    _JOB.update(
        work=work,
        feed=asset["sqx_symbol"],
        timeframe=timeframe,
        asset=asset,
        ids=ids,
        legs=legs,
        drift=drift(),
        costs=cfg["costs"],
    )
    found = dict(fanout.run(one, {m: len(k) for m, k in legs.items()}, cfg["workers"]))
    return {market: found[market] for market in legs}


def stacked(legs: list[dict], name: str) -> np.ndarray:
    """Consecutive legs' weekly panels as one, weeks x variants.

    Args:
        legs: One market's legs, in time order, as one() returned them.
        name: `gross` or `net`.

    Returns:
        The rows of every leg; a week two legs share (the one their boundary falls in) is
        summed into one row, so it takes one sign.
    """
    return pd.concat([leg[name] for leg in legs]).groupby(level=0).sum().to_numpy()
