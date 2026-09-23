"""What assets/ declares: costs resolved against the shared policy, checked against the class."""

from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import yaml

from core.paths import ASSETS

POLICY, CLASSES, MARKETS = "_policy.yaml", "_classes.yaml", "_markets.yaml"
SYMBOLS = ASSETS / "symbols"   # one file per instrument; the `_*.yaml` above them are shared

RESERVED = "reserved_for"   # a segment spent by looking at it; report() flags it loudly


def _read(name: str) -> dict:
    """The parsed YAML of one file of the assets root, named with its extension."""
    return yaml.safe_load((ASSETS / name).read_text(encoding="utf-8"))


def policy() -> dict:
    """The research policy every asset inherits: segments and swap conventions."""
    return _read(POLICY)


def classes() -> dict:
    """The cost schema of each class: which fields exist, in what unit, on which SQX setting."""
    return _read(CLASSES)


def symbols() -> list[str]:
    """Every asset with a file in assets/symbols/, sorted."""
    return sorted(f.stem for f in SYMBOLS.glob("*.yaml"))


def load(symbol: str) -> dict:
    """One asset, with the shared policy folded in.

    Args:
        symbol: Asset name as the file is called, e.g. "XAUUSD".

    Returns:
        The asset's own file, plus `segments` (each one's role from `segments_default`, its
        dates from that asset's block in `_policy.yaml`) and `data`, the range SQX holds.
        FileNotFoundError on an unknown asset is the intended outcome: nothing may be
        authored for one.
    """
    base = policy()
    data = yaml.safe_load((SYMBOLS / f"{symbol}.yaml").read_text(encoding="utf-8"))
    mine = (base["segments"].get(symbol) or {})
    segments = {name: {**spec, **(mine.get(name) or {})}
                for name, spec in base["segments_default"].items()}
    return {**base, **data, "segments": segments, "data": mine.get("data")}


def schema(data: dict) -> dict:
    """The `_classes.yaml` block for this asset's class: field names, units and SQX settings.

    Args:
        data: One asset as load() returned it.

    Returns:
        The class block that `fields()` and `sqx_settings()` both read.
    """
    return classes()[data["class"]]


def fields(data: dict) -> list[str]:
    """Every cost field this asset's class says the file must carry, in reading order.

    Args:
        data: One asset as load() returned it.

    Returns:
        Field names. A forex asset carries one spread, a no_forex asset two.
    """
    s = schema(data)
    return (s["spread"]["fields"] + [s["commission"]["field"]] + s["slippage"]["fields"]
            + s["swap"]["fields"])


def _ms(bound: int | date, end: bool) -> int:
    """One segment bound as the epoch millisecond a SQX task carries.

    Args:
        bound: A year, meaning that whole year, or an explicit date meaning that day.
        end: True for the closing bound, which is inclusive and so resolves to the first
            instant after it — the day after a date, the 1 January after a year.

    Returns:
        Milliseconds UTC.
    """
    if isinstance(bound, int):
        day = date(bound + 1, 1, 1) if end else date(bound, 1, 1)
    else:
        day = bound + timedelta(days=1) if end else bound
    return int(datetime(day.year, day.month, day.day, tzinfo=timezone.utc).timestamp() * 1000)


def window(data: dict, segment: str) -> tuple[int, int]:
    """One segment as the epoch milliseconds a SQX task wants.

    Args:
        data: One asset as load() returned it.
        segment: Segment name, e.g. "build" or "oos1".

    Returns:
        (dateFrom, dateTo) in milliseconds UTC. Both ends inclusive, so `to: 2017` runs to
        the last instant of 2017 and dateTo is 2018-01-01 — the owner's convention, stated
        2026-09-22. The master's XAUUSD project differs by a day; `_policy.yaml` says so.
        Raises when the segment has no dates: a made-up window is worse than a stop.
    """
    seg = data["segments"][segment]
    if seg["from"] is None or seg["to"] is None:
        raise ValueError(f"el tramo `{segment}` de {data['symbol']} no tiene fechas decididas; "
                         f"están en assets/_policy.yaml, bajo `segments: {data['symbol']}:`")
    return _ms(seg["from"], False), _ms(seg["to"], True)


def sqx_settings(data: dict, segment: str) -> dict:
    """What a SQX task for this asset and segment must carry, in SQX's own vocabulary.

    Args:
        data: One asset as load() returned it.
        segment: Segment name, which picks the spread on a no_forex asset.

    Returns:
        defaultSpread and defaultSlippage, and the commission and swap blocks with the
        method and type their class declares. The segment picks both the spread and the
        slippage: the slippage is half its segment's spread, so it follows the spread. Costs live per symbol INSIDE EACH TASK, not
        once per project — that is what lets build carry one spread and the retest tasks
        another.
    """
    use = lambda k: data["costs"][k]["use"]
    s = schema(data)
    half = data["segments"][segment]["spread"]
    spread = "spread" if data["class"] == "forex" else f"spread_{half}"
    return {"defaultSpread": use(spread),
            "defaultSlippage": use(f"slippage_{half}"),
            "commission": {"method": s["commission"]["sqx_method"], "value": use("commission")},
            "swap": {"type": s["swap"]["sqx_type"], "long": use("swap_long"),
                     "short": use("swap_short"), **data["swap"]}}


def mc_retest(data: dict) -> dict:
    """The spread and slippage ranges the MC Retest task must randomise within.

    Args:
        data: One asset as load() returned it.

    Returns:
        {"spread": {"min", "max"}, "slippage": {"min", "max"}} in points, per this asset's
        own declaration. Both are absolute point ranges and not multiples of the real
        spread, so a range is only meaningful at the instrument's own scale — SQX's factory
        1.0-5.0 sorts between 1 and 5 points on an instrument whose spread is 1100.
    """
    return {k: {"min": v["min"], "max": v["max"]} for k, v in data["mc_retest"].items()}


def markets(symbol: str) -> dict:
    """The declared retest universe of one main asset.

    Args:
        symbol: Main asset, e.g. "XAUUSD".

    Returns:
        Keys main, timeframe and categories ({family, structural} → [{feed, data_from}]).
        Empty dict when the asset is not a declared main.
    """
    return _read(MARKETS).get(symbol, {})


def special_notes() -> list[Path]:
    """Cross-asset special cases that apply to every project, sorted."""
    return sorted((ASSETS / "special").glob("*.md"))
