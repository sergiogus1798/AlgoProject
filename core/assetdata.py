"""What assets/ declares: costs resolved against the shared policy, checked against the class."""

import copy
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import yaml

from core import assetoverride
from core.paths import ASSETS

POLICY, CLASSES, MARKETS = "_policy.yaml", "_classes.yaml", "_markets.yaml"
BUILD = "_build.yaml"   # how a strategy is generated; the symbol files say what it costs
SYMBOLS = ASSETS / "symbols"   # one file per instrument; the `_*.yaml` above them are shared

RESERVED = "reserved_for"   # a segment spent by looking at it; binds only under enforced()
AUTONOMOUS = "ALGO_AUTONOMOUS"


def enforced() -> bool:
    """Whether `reserved_for` binds this process: only when `ALGO_AUTONOMOUS=1`.

    Owner, 2026-09-28: a human may look at any segment at any time; whether an autonomous
    agent deciding alone should still be held is open, so it opts in. Nothing sets it today.
    """
    return os.environ.get(AUTONOMOUS) == "1"


# Parsed files, keyed by path and stamped with the mtime and size they were parsed at, so an
# edit from the window is read on the next call. 🔬 2026-09-25: `symbol_for()` parses every
# asset file and a study calls it once per strategy or per cell -- 54 s of crossTF's 60 went
# to parsing the same YAML 1,971 times.
_PARSED: dict = {}


def _parse(path: Path) -> dict:
    """One YAML file, parsed once per version of it on disk; each caller gets its own copy."""
    stamp = path.stat()
    stamp = (stamp.st_mtime_ns, stamp.st_size)
    if _PARSED.get(path, (None,))[0] != stamp:
        _PARSED[path] = (stamp, yaml.safe_load(path.read_text(encoding="utf-8")))
    return copy.deepcopy(_PARSED[path][1])


def _read(name: str) -> dict:
    """The parsed YAML of one file of the assets root, named with its extension."""
    return _parse(ASSETS / name)


def policy() -> dict:
    """The research policy every asset inherits: segments and swap conventions."""
    return _read(POLICY)


def classes() -> dict:
    """The cost schema of each class: which fields exist, in what unit, on which SQX setting."""
    return _read(CLASSES)


def doctrine() -> dict:
    """The build doctrine: rule complexity, order types, exits, sizing, hours, cross-checks.

    `assetoverride.PRECISION` and `.MC_SIMULATIONS` (unset by default) replace every
    `precision` or `simulations` the doctrine carries, wherever it nests one — the build's
    own, `crosschecks.precision` (the builder's `RetestWithHigherPrecision`), every retest's,
    each MC Retest task's and SPP task's own. Set for one configurator's process only, to
    apply a temporary run-wide setting to one project without touching `_build.yaml`.
    """
    d = _read(BUILD)
    precision = os.environ.get(assetoverride.PRECISION)
    if precision:
        d = assetoverride.replace(d, "precision", int(precision))
    simulations = os.environ.get(assetoverride.MC_SIMULATIONS)
    if simulations:
        d = assetoverride.replace(d, "simulations", int(simulations))
    return d


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
    data = _parse(SYMBOLS / f"{symbol}.yaml")
    mine = (base["segments"].get(symbol) or {})
    # `from`/`to` first: an asset with no block yet in _policy.yaml — one just added, or
    # one that arrived as a cross-market feed — has undecided windows, not missing keys.
    segments = {name: {"from": None, "to": None, **spec, **(mine.get(name) or {})}
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
        Field names: a spread and a slippage per half the asset's segments name in
        `_policy.yaml` — `is`, `oos` and, since 2026-09-30 for every asset, `oos2`.
    """
    s = schema(data)
    extra = sorted({seg["spread"] for seg in data["segments"].values()} - {"is", "oos"})
    return (s["spread"]["fields"] + [f"spread_{h}" for h in extra] + [s["commission"]["field"]]
            + s["slippage"]["fields"] + [f"slippage_{h}" for h in extra] + s["swap"]["fields"])


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


def segment_start(data: dict, segment: str) -> str:
    """One segment's own first day, as an ISO date — never a retested leg's warm-up start
    (`knowhow/sqx-format/leg-curve-warmup.md`). Raises when `from` is undecided.

    Args:
        data: One asset as load() returned it.
        segment: Segment name, e.g. "oos2".

    Returns:
        ISO date; a bare year means 1 January of it, as `window()` reads its opening bound.
    """
    bound = data["segments"][segment]["from"]
    if bound is None:
        raise ValueError(f"el tramo `{segment}` de {data['symbol']} no tiene fechas decididas; "
                         f"están en assets/_policy.yaml, bajo `segments: {data['symbol']}:`")
    return f"{bound}-01-01" if isinstance(bound, int) else str(bound)


def sqx_settings(data: dict, segment: str) -> dict:
    """What a SQX task for this asset and segment must carry, in SQX's own vocabulary.

    Args:
        data: One asset as load() returned it.
        segment: Segment name, which picks the spread and the slippage.

    Returns:
        defaultSpread and defaultSlippage (the slippage follows the spread's segment), and
        the commission and swap blocks. `costs.commission.use` carries one `{method, value}`
        per segment (owner, 2026-09-29): the most-restrictive CONFIRMED broker can differ by
        segment and method both — gold's build is Infinox's `SizeBased 8`, its oos2 is
        Darwinex's `PercentageBased 0.005` — so this segment's own winner is what gets
        written, never the class's default method. Costs live INSIDE EACH TASK, not once per
        project, which is what lets build carry one spread and the retest tasks another.
    """
    use = lambda k: data["costs"][k]["use"]
    s = schema(data)
    half = data["segments"][segment]["spread"]
    commission = use("commission")[segment]
    return {"defaultSpread": use(f"spread_{half}"),
            "defaultSlippage": use(f"slippage_{half}"),
            "commission": {"method": commission["method"], "value": commission["value"]},
            "swap": {"type": s["swap"]["sqx_type"], "long": use("swap_long"),
                     "short": use("swap_short"), **data["swap"]}}


def markets(symbol: str) -> dict:
    """The declared retest universe of one main asset.

    Args:
        symbol: Main asset, e.g. "XAUUSD".

    Returns:
        Keys main, timeframe and categories ({family, structural} → [{feed, data_from}]).
        Empty dict when the asset is not a declared main.
    """
    return _read(MARKETS).get(symbol, {})


def symbol_for(feed: str) -> str | None:
    """Which asset file declares this SQX feed.

    Args:
        feed: SQX symbol name, e.g. "USDJPY_M1".

    Returns:
        The asset name, or None when no file claims it. Lets a study that only knows the
        feed it read say whose costs its numbers carry, instead of naming one asset in a
        sentence that every asset then gets.
    """
    return next((s for s in symbols() if load(s)["sqx_symbol"] == feed), None)


def special_notes() -> list[Path]:
    """Cross-asset special cases that apply to every project, sorted."""
    return sorted((ASSETS / "special").glob("*.md"))
