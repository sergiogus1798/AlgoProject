"""The only writer of assets/: one value, one cost, or a whole asset in or out of the library.

A folder since 2026-09-29 (rule 1): `brokers.py` holds `set_brokers()`, re-exported below.
"""

import shutil
from datetime import date
from pathlib import Path

import yaml
from ruamel.yaml.comments import CommentedMap

from core.assetdata import BUILD, CLASSES, MARKETS, POLICY, SYMBOLS, classes
from core.assetwrite.brokers import set_brokers   # noqa: F401  (re-exported)
from core.assetwrite.markets import declare_main, flow, set_market   # noqa: F401  (re-exported)
from core.assetyaml import read, write
from core.paths import ASSETS

# The four shared files, addressable by a short name so the window never sends a path.
SHARED = {"policy": POLICY, "classes": CLASSES, "markets": MARKETS, "build": BUILD}
RETIRED = SYMBOLS / "_retired"   # a withdrawn asset, out of symbols() but not lost


def path_of(name: str) -> Path:
    """The file one write targets.

    Args:
        name: A key of SHARED, or an asset name.

    Returns:
        The file; an asset name always resolves under symbols/, never elsewhere.
    """
    return ASSETS / SHARED[name] if name in SHARED else SYMBOLS / f"{name}.yaml"


def parse(text: str, kind: str) -> object:
    """What the window typed, as the YAML scalar it means.

    Args:
        text: The raw text of the editor.
        kind: "scalar", or "list" for one item per line.

    Returns:
        A number, a bool, a date, None for `null` or an empty box, or a string — decided by
        YAML's own rules, so what is typed here means what it would mean in the file.
    """
    if kind == "list":
        return [yaml.safe_load(line) for line in text.splitlines() if line.strip()]
    return yaml.safe_load(text) if text.strip() else None


def set_value(name: str, keys: list, value: object) -> dict:
    """Put one value into one file, leaving every comment and every other line alone.

    Args:
        name: A key of SHARED, or an asset name.
        keys: The path to the value, as `assetyaml.leaves` reports it.
        value: What to write, already parsed.

    Returns:
        Where it was written and what it now holds.
    """
    path = path_of(name)
    doc = read(path)
    node = doc
    for key in keys[:-1]:
        node = node[key]
    node[keys[-1]] = value
    write(path, doc)
    reindex()
    return {"file": str(path), "path": keys, "value": value}


def set_cost(symbol: str, field: str, value: object, why: str, after: str | None = None) -> dict:
    """Change what an asset really costs, and say why in the same write.

    Args:
        symbol: Asset name.
        field: Cost field of its class, e.g. "spread_is", or one its segments name
            ("spread_oos2"), created on first write.
        value: The figure to apply, or None to hand the field back to «undecided».
        why: The line that replaces the stored one. A `use` under the previous `why` would
            claim a justification that is no longer the reason for the number.
        after: For a field the file lacks, the sibling it goes after, e.g. "spread_oos".

    Returns:
        The field as written.
    """
    path = path_of(symbol)
    doc = read(path)
    if field == "commission" and isinstance(value, (int, float)):
        # `commission.use` is one {method, value} per segment (owner, 2026-09-29): a bare figure
        # from the window or the onboard applies to every segment in the class's own method.
        method = "SizeBased" if classes()[doc["class"]]["commission"]["unit"] == "usd_per_lot" \
            else "PercentageBased"
        value = {seg: {"method": method, "value": float(value)} for seg in ("build", "oos1", "oos2")}
    if field not in doc["costs"]:
        doc["costs"].insert(list(doc["costs"]).index(after) + 1, field,
                            CommentedMap(use=None, sqx_now=None, why=""))
    doc["costs"][field].update({"use": value, "why": why})
    write(path, doc)
    reindex()
    return {"file": str(path), "field": field, "use": value, "why": why}


def rename_cost(symbol: str, old: str, new: str) -> None:
    """Give a cost field a new name in place, its `use`, `sqx_now` and `why` kept — the forex
    `spread` became `spread_is` when every asset got one spread per segment (2026-09-30)."""
    path = path_of(symbol)
    doc = read(path)
    if old in doc["costs"] and new not in doc["costs"]:
        keys = list(doc["costs"])
        doc["costs"].insert(keys.index(old), new, doc["costs"].pop(old))
        write(path, doc)
        reindex()


def create(symbol: str, cls: str, broker: str, sqx_symbol: str, session: str,
           instrument: dict) -> dict:
    """Add an asset to the library, with every decision still open.

    Args:
        symbol: Its name, which is also its file name.
        cls: "forex" or "no_forex" — it decides which cost fields the file carries.
        broker: Who quotes it.
        sqx_symbol: The feed, exactly as `-symbol action=list` prints it.
        session: The trading session SQX must apply, or None while undecided.
        instrument: tick_size, point_value and min_distance, read from SQX.

    Returns:
        The file written, with its `_policy.yaml` block. Every cost lands `use: null` and
        blocks authoring: invented values are worse than none, because they look decided.
    """
    schema = classes()[cls]
    fields = (schema["spread"]["fields"] + ["spread_oos2", schema["commission"]["field"]]
              + schema["slippage"]["fields"] + ["slippage_oos2"] + schema["swap"]["fields"])
    body = {"symbol": symbol, "class": cls, "broker": broker, "sqx_symbol": sqx_symbol,
            "feeds": [sqx_symbol], "verified": date.today(), "session": session,
            "instrument": instrument,
            "costs": {f: {"use": None, "sqx_now": None,
                          "why": "SIN DECIDIR — dado de alta desde la app el "
                                 f"{date.today()}."} for f in fields},
            "notes": [f"{date.today()}: alta desde la ventana. Ningún coste está pactado y "
                      "`instrument` es lo que se tecleó: confírmalo con "
                      "`python3 -m sqx.inspect.instruments`."],
            "mc_retest": {k: {"min": None, "max": None, "sqx_now": None}
                          for k in ("spread", "slippage")}}
    path = SYMBOLS / f"{symbol}.yaml"
    path.write_text(f"# {symbol} — lo propio de este activo, y nada más.\n"
                    f"#   · sus costes, unidades y ajustes de SQX → `../_classes.yaml`, "
                    f"clase `{cls}`\n"
                    "#   · los segmentos temporales y los swaps  → `../_policy.yaml`\n"
                    "#   · los mercados donde se retestea        → `../_markets.yaml`\n",
                    encoding="utf-8")
    doc = read(path) or {}
    doc.update(body)
    write(path, doc)
    add_segments(symbol)
    reindex()
    return {"file": str(path), "symbol": symbol, "class": cls}


def add_segments(symbol: str) -> None:
    """Give a new asset its block of `_policy.yaml`, with every window still undecided.

    Args:
        symbol: Asset name.

    Returns:
        Nothing. Without it every reader of a window raises instead of saying «sin decidir».
    """
    path = ASSETS / POLICY
    doc = read(path)
    doc["segments"][symbol] = {"data": None,
                               **{s: {"from": None, "to": None}
                                  for s in doc["segments_default"]}}
    write(path, doc)


def set_segment_end(symbol: str, segment: str, end: date) -> None:
    """Move one asset's segment to end on a given day, inclusive, keeping every comment.

    Args:
        symbol: Asset name, as `_policy.yaml`'s `segments:` names it.
        segment: "build", "oos1" or "oos2".
        end: The new last day.
    """
    path = ASSETS / POLICY
    doc = read(path)
    doc["segments"][symbol][segment]["to"] = end
    write(path, doc)


def retire(symbol: str) -> dict:
    """Take an asset out of the library without losing it.

    Args:
        symbol: Asset name.

    Returns:
        Where the file went. `symbols()` stops seeing it; its `_policy.yaml` block stays,
        since restoring an asset without the windows it held would be a silent loss.
    """
    RETIRED.mkdir(exist_ok=True)
    dest = RETIRED / f"{symbol}.yaml"
    shutil.move(SYMBOLS / f"{symbol}.yaml", dest)
    reindex()
    return {"retired": symbol, "file": str(dest)}


def restore(symbol: str) -> dict:
    """Put a retired asset back into the library.

    Args:
        symbol: Asset name.

    Returns:
        Where the file went back to.
    """
    dest = SYMBOLS / f"{symbol}.yaml"
    shutil.move(RETIRED / f"{symbol}.yaml", dest)
    if symbol not in read(ASSETS / POLICY)["segments"]:
        add_segments(symbol)
    reindex()
    return {"restored": symbol, "file": str(dest)}


def retired() -> list[str]:
    """Every asset withdrawn from the library, sorted."""
    return sorted(f.stem for f in RETIRED.glob("*.yaml")) if RETIRED.exists() else []


def reindex() -> int:
    """Rewrite assets/INDEX.md after a change, so it never contradicts the files.

    Returns:
        How many assets it listed.
    """
    from core.assets import write_index   # here: it pulls in the whole preflight

    return write_index()
