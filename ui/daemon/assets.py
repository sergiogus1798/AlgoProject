"""What the window needs to draw assets/, and the writes it may make on it."""

from typing import Any
from datetime import date
from functools import lru_cache

from core import assetranges, assetwrite
from core.assetcheck import (
    REQUIRED,
    mc_pending,
    past_data,
    pending,
    provisional,
    segments_pending,
    validate,
)
from core.assetdata import RESERVED, classes, fields, load, policy, schema, symbols
from core.assetmarkets import markets, special_notes
from core.assets import report
from core.assetyaml import leaves
from core.paths import ASSETS, WORKERS
from sqx.inspect.instruments import registry
from ui.daemon.assetprior import prior


def units(data: dict) -> dict[str, Any]:
    """Every cost field of this asset mapped to the unit its class declares.

    Args:
        data: One asset as load() returned it.

    Returns:
        Field to unit. The unit is never in the value: a gold swap of -7 is a percentage
        and one of -73.42 is points, and a window showing the bare number would be lying
        by omission.
    """
    s = schema(data)
    return {
        **{f: s["spread"]["unit"] for f in fields(data) if f.startswith("spread")},
        s["commission"]["field"]: s["commission"]["unit"],
        **{f: s["slippage"]["unit"] for f in fields(data) if f.startswith("slippage")},
        **{f: s["swap"]["unit"] for f in s["swap"]["fields"]},
    }


def row(symbol: str) -> dict[str, Any]:
    """One asset as the list down the left shows it.

    Args:
        symbol: Asset name.

    Returns:
        Its identity and its state: what blocks authoring, what is merely provisional, and
        whether its windows and its schema hold up.
    """
    data = load(symbol)
    return {
        "symbol": symbol,
        "class": data["class"],
        "broker": data["broker"],
        "sqx_symbol": data["sqx_symbol"],
        "session": data.get("session"),
        "pending": pending(data),
        "provisional": provisional(data),
        "segments_pending": segments_pending(data),
        "broken": validate(data),
        "data": data["data"],
    }


def state() -> dict[str, Any]:
    """Everything the asset zone needs to open, in one round trip.

    Returns:
        A row per asset, the retired shelf, the class schemas and the cross-asset notes the
        preflight surfaces. Nineteen assets is one parse, so paging it would add a mode for nothing
        on loopback.
    """
    return {
        "assets": [row(s) for s in symbols()],
        "retired": assetwrite.retired(),
        "classes": classes(),
        "special": [f.name for f in special_notes()],
        "required": REQUIRED,
    }


def one(symbol: str, leaves: bool = True) -> dict[str, Any]:
    """One asset in full: its decisions, its windows, its universe and its file.

    Args:
        symbol: Asset name.
        leaves: False leaves the file's raw leaves out (`[]`): reading the YAML for them is
            two thirds of the call and the window shows them only on request.

    Returns:
        The costs with their units and what SQX carries today, the segments already turned
        into the dates they mean, the MC Retest ranges, the Cross Market check, everything the
        preflight would complain about, and the file's own leaves for the raw editor.
    """
    data = load(symbol)
    unit = units(data)
    # «SQX hoy» is the custodian's own registry, never the master's the file recorded (owner,
    # 2026-09-30): read off its data.db, without starting it.
    now = registry(WORKERS["custodian"]["path"], data["sqx_symbol"])
    costs = [
        {
            "field": f,
            **data["costs"][f],
            "sqx_now": now.get(f),
            "unit": unit[f],
            "required": f in REQUIRED[data["class"]],
        }
        for f in fields(data)
    ]
    segments = [
        {"name": n, **s, "reserved_for": s.get(RESERVED, [])}
        for n, s in data["segments"].items()
    ]
    # What the MC Retest will draw, beside what the file says: an empty slippage range is
    # 1x-4x the build's slippage in `core.assets`, and the card read it as «sin decidir».
    applied = assetranges.mc_retest(data)
    mc = [
        {"name": n, **r, "applied": applied.get(n)}
        for n, r in (data.get("mc_retest") or {}).items()
    ]
    return {
        "symbol": symbol,
        "class": data["class"],
        "broker": data["broker"],
        "sqx_symbol": data["sqx_symbol"],
        "feeds": data["feeds"],
        "session": data.get("session"),
        "verified": str(data["verified"]),
        "instrument": dict(data["instrument"]),
        "costs": costs,
        "segments": segments,
        "data": data["data"],
        "mc_retest": mc,
        "markets": universe(symbol),
        "notes": list(data.get("notes") or []),
        "projects": list(data.get("projects_using_it") or []),
        "problems": problems(data),
        "report": report(symbol),
        "leaves": _leaves(symbol) if leaves else [],
        "prior": prior(symbol),
    }


@lru_cache(maxsize=1)
def feeds(stamp: tuple) -> dict[str, tuple[str, list[str]]]:
    """Every asset's SQX symbol and feeds, read once per version of the asset files.

    Args:
        stamp: The mtimes of every YAML under `assets/`: the cache key, so an edit is read.

    Returns:
        Asset → (sqx_symbol, feeds). 🔬 2026-10-04: `universe` loaded every asset three times
        per page — 2,527 loads and 5.6 s of the 7.7 the zone took to open its 27 pages.
    """
    return {s: (d["sqx_symbol"], d["feeds"]) for s in symbols() for d in [load(s)]}


def universe(symbol: str) -> dict[str, Any]:
    """One main asset's Cross Market check, with every market named by its asset.

    Args:
        symbol: Asset name.

    Returns:
        main, timeframe, categories ({family, structural} → [{feed, data_from, asset}]) and
        `candidates`: every other asset not yet in a category, with the feed and the first
        date with data a row added from the window writes. Empty categories and no
        candidates when the asset is not a declared main — a new main block needs its own
        feed and timeframe, which is not a row to add.
    """
    declared = markets(symbol)
    names = feeds(tuple(f.stat().st_mtime_ns for f in sorted(ASSETS.rglob("*.yaml"))))
    owner = {feed: s for s, (main, rest) in names.items() for feed in [main, *rest]}
    cats = {
        c: [
            {
                **f,
                "data_from": f["data_from"] and str(f["data_from"]),
                "asset": owner.get(f["feed"], f["feed"]),
            }
            for f in rows
        ]
        for c, rows in (declared.get("categories") or {}).items()
    }
    taken = {f["feed"] for rows in cats.values() for f in rows} | {declared.get("main")}
    spans = policy()["segments"]
    free = [
        {
            "asset": s,
            "feed": main,
            "data_from": str(
                ((spans.get(s) or {}).get("data") or {}).get("from") or ""
            ),
        }
        for s, (main, _) in names.items()
        if s != symbol and main not in taken
    ]
    return {
        "main": declared.get("main"),
        "timeframe": declared.get("timeframe"),
        "categories": cats,
        "candidates": free if declared else [],
    }


def problems(data: dict) -> dict[str, Any]:
    """Everything the preflight would say about this asset, by severity.

    Args:
        data: One asset as load() returned it.

    Returns:
        `broken` and `before_data` stop the preflight (exit 3); `pending` blocks authoring
        (exit 2); the rest are warnings it prints and carries on. The window paints them in
        that order because the owner acts on them in that order.
    """
    return {
        "broken": validate(data),
        "pending": pending(data),
        "provisional": provisional(data),
        "segments": segments_pending(data),
        "past_data": past_data(data),
        "mc": mc_pending(data),
    }


def _leaves(name: str) -> list[dict]:
    """Every editable value of one file, as JSON the window can paint.

    Args:
        name: A key of assetwrite.SHARED, or an asset name.

    Returns:
        The leaves, with dates and paths rendered as text — a date survives the round trip
        because `parse()` reads it back with the same YAML rules that wrote it.
    """
    return [
        {
            **leaf,
            "path": [str(k) for k in leaf["path"]],
            "value": str(leaf["value"])
            if isinstance(leaf["value"], date)
            else leaf["value"],
        }
        for leaf in leaves(assetwrite.path_of(name))
    ]


def set_value(name: str, path: list, text: str, kind: str) -> assetwrite.ValueWrite:
    """Write one value of one file, exactly as it was typed.

    Args:
        name: A key of assetwrite.SHARED, or an asset name.
        path: The keys leading to it; a list index arrives as its digits.
        text: What was typed. Empty means `null`, which is «undecided».
        kind: "scalar" or "list".

    Returns:
        What was written.
    """
    keys = [int(k) if k.isdigit() else k for k in path]
    return assetwrite.set_value(name, keys, assetwrite.parse(text, kind))


def set_cost(symbol: str, field: str, text: str, why: str) -> assetwrite.CostWrite:
    """Change one cost and its justification in the same write.

    Args:
        symbol: Asset name.
        field: Cost field of its class.
        text: The figure, in the unit its class declares. Empty hands it back to undecided.
        why: The line replacing the stored one.

    Returns:
        The field as written.
    """
    return assetwrite.set_cost(symbol, field, assetwrite.parse(text, "scalar"), why)


def create(new: dict) -> dict[str, Any]:
    """Add an asset, or refuse a name the library already holds.

    Args:
        new: symbol, class, broker, sqx_symbol, session and the three instrument facts.

    Returns:
        The file written, plus the asset's row.
    """
    symbol = new["symbol"]
    if symbol in symbols() or symbol in assetwrite.retired():
        return {
            "error": f"`{symbol}` ya existe. Mira la lista, o restaura el retirado."
        }
    assetwrite.create(
        symbol,
        new["class"],
        new["broker"],
        new["sqx_symbol"],
        new["session"] or None,
        {
            k: assetwrite.parse(str(new[k]), "scalar")
            for k in ("tick_size", "point_value", "min_distance")
        },
    )
    return {"created": symbol, "row": row(symbol)}
