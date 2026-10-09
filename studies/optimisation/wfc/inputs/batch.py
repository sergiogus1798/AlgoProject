"""A variant batch's trades on the main market as excess, net and gross, trade by trade and leg by leg."""

from pathlib import Path

import pandas as pd
import yaml

from core import assetdata, barstore
from engines.market import reprice
from engines.variants import fingerprint, look, panel
from engines.weekly import panel as weekly

TRADES = "variant_trades.parquet"       # written by sqx.variants.varianttrades
MAIN = "Main"
STEP = 17
# The excess is step 14's: the gate's drift block, never a copy of its values.
GATE = Path(__file__).resolve().parents[3] / "screening" / "gate" / "config.yaml"
# The drift a trade could have been charged knowing only earlier bars. Variants `b` and `d`
# take the drift of the trade's own calendar year, which earlier bars do not hold.
PRIOR = {"window": "year", "variant": "c"}
# What a composition is measured on, of `engines.weekly.panel.per_trade`'s columns.
COLUMNS = ["variant_id", "profit", "net", "gross", "open", "close"]


def drift() -> dict:
    """The gate's `drift` block: the window and the variant of the drift term."""
    return yaml.safe_load(GATE.read_text(encoding="utf-8"))["drift"]


def span(asset: dict, legs: tuple) -> tuple[str, str]:
    """The declared bounds of consecutive legs, as strings a DatetimeIndex slices by."""
    return (str(asset["segments"][legs[0]]["from"]), str(asset["segments"][legs[-1]]["to"]))


def window(asset: dict, legs: tuple) -> tuple[str, str]:
    """First and last day of consecutive legs as full dates, both inside; a bare year is whole."""
    last = asset["segments"][legs[-1]]["to"]
    return (assetdata.segment_start(asset, legs[0]),
            f"{last}-12-31" if isinstance(last, int) else str(last))


def years(asset: dict, legs: tuple) -> float:
    """Length of consecutive legs in years of 365.25 days, as `excess.per_year` counts them."""
    first, last = (pd.Timestamp(day) for day in window(asset, legs))
    return ((last - first).days + 1) / 365.25


def trades(work: Path, leg: str) -> pd.DataFrame:
    """One leg's trades on the main market, every variant; no other leg's rows are read."""
    got = pd.read_parquet(work / TRADES, filters=[("leg", "==", leg), ("market", "==", MAIN)])
    return got.assign(variant_id=got["variant_id"].astype(str))


def priced(raw: pd.DataFrame, symbol: str, bars: pd.DataFrame, leg: str,
           term: dict | None = None, drift_span: tuple[str, str] | None = None) -> pd.DataFrame:
    """One leg's trades with their excess, after costs (`net`) and before them (`gross`).

    Args:
        raw: What trades() returned for the leg.
        symbol: The asset: its card gives the feed, the costs and the leg's dates.
        bars: The batch's own timeframe, the whole file.
        leg: `build`, `oos1` or `oos2`.
        term: The drift block; the gate's when None.
        drift_span: The bars the drift is measured on; the leg's own when None.

    Returns:
        `engines.weekly.panel.per_trade`'s frame: the costs added back into `gross` are the
        ones `reprice.real` charged each trade from the asset's card.
    """
    asset = assetdata.load(symbol)
    feed = asset["sqx_symbol"]
    return weekly.per_trade(raw, bars, reprice.costs(feed, leg), span(asset, (leg,)),
                            term or drift(), feed, drift_span)


def read(work: Path, symbol: str, timeframe: str, legs: tuple = panel.SEGMENTS) -> dict:
    """Everything the compositions over `legs` are measured on, the door asked first.

    Args:
        work: The batch folder, holding `variant_trades.parquet`.
        symbol, timeframe: The batch's main market (`engines.variants.look.market`).
        legs: The legs read, `build` first. `("build", "oos1")` never opens an `oos2` row.

    Returns:
        `per`: leg -> one row per trade, COLUMNS; `prints`: each variant's fingerprint over
        its trades of every leg read (`engines.variants.fingerprint`), by `variant_id`; and,
        when `oos2` is read, `prior`: each variant's net excess there summed, with the drift
        measured on the bars from the first day of `build` to the last of `oos1` (`PRIOR`).

    Raises:
        PermissionError: From `look.admit`, before any trade is read.
    """
    look.admit(STEP, legs, symbol)
    asset = assetdata.load(symbol)
    bars = barstore.read(asset["sqx_symbol"], timeframe)
    raw = {leg: trades(work, leg) for leg in legs}
    got = {"per": {leg: priced(raw[leg], symbol, bars, leg)[COLUMNS] for leg in legs},
           "prints": fingerprint.prints(pd.concat(raw.values()))}
    if "oos2" in legs:
        prior = priced(raw["oos2"], symbol, bars, "oos2", PRIOR, span(asset, panel.SEGMENTS[:2]))
        got["prior"] = prior.groupby("variant_id")["net"].sum()
    return got


def live(metrics: pd.DataFrame, controls: tuple) -> int:
    """How many parameters actually move in the batch, its controls left out.

    Args:
        metrics: Contract C3: `stratum` and one `param_*` column per parameter.
        controls: The strata that are not variants of the design.

    Returns:
        The `k` of the in-sample floor. A frozen or shifted parameter sits at the mother's
        value in every variant, and so does a live one whose plateau is a single value.
    """
    params = metrics.loc[~metrics["stratum"].isin(controls)].filter(like="param_")
    return int((params.nunique() > 1).sum())
