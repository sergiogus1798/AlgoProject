"""emit.py — generic atom emitter. Turns a catalog entry into block-ready XML.

A config.xml indicator <Item> is already 90% of a usable atom; the transform to make
it block-ready is purely mechanical and the SAME for every indicator:

  1. flatten <paramCategory> wrappers  (done at bootstrap time)
  2. #Chart#  -> bind to the block data var:  paramType="data" value="#Chart1#"
  3. #Shift#  -> give it an inner text value
  4. period/double knob -> bind to an outer optimizer slot (#Int2#/#Double3#) OR freeze
  5. combo / #Line#      -> pick a value (inner text)

emit.py does exactly that, rebuilding each Param from its full stored attribute set
(so every build-specific attribute survives), ESCAPING all attribute values and
inner text (so a help string with > or & can never break the parser), and DROPPING
any stale customParam/value binding harvested from an exported source block — a
knob is bound only when THIS call binds it.

    from engine.emit import Catalog
    cat = Catalog("catalog.json")
    cat.atom("RSI", period="#Int2#")            # bind period to an outer knob
    cat.atom("RSI", period="14")                # freeze period at 14 (literal)
    cat.atom("MACD", line="1", fast="#Int2#")   # pick the Signal line, bind Fast
    cat.atom("SuperTrend", atrperiod="#Int2#", atrmult="#Double3#")
    cat.number("50")                            # numeric constant operand
"""

from __future__ import annotations

import json
import re
from pathlib import Path

_PARAM_REF = re.compile(r"^#[A-Za-z][A-Za-z0-9]*#$")   # an outer-knob reference


def _esc_attr(v: str) -> str:
    return (v.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _esc_text(v: str) -> str:
    return v.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _friendly(param_key: str) -> str:
    """#ATRPeriod# -> 'atrperiod' — the kwarg name a caller uses to bind/pick it."""
    return param_key.strip("#").lower()


def _open_tag(attrib: dict) -> str:
    parts = "".join(f' {k}="{_esc_attr(str(v))}"' for k, v in attrib.items())
    return f"<Item{parts}>"


def _render_param(spec: dict, kwargs: dict, from_export: bool = False) -> str:
    attrib = dict(spec["attrib"])
    role = spec["role"]
    key = attrib.get("key", "")
    name = _friendly(key)
    # Atoms harvested from customBlocksExport.xml keep the SOURCE block's knob
    # bindings on their Params (customParam="true" value="#IntN#") — those are that
    # block's choices, not the atom's schema. Copying them poisoned new blocks with
    # undeclared #IntN# refs (audit P0-12). Drop both here; the chart/binding
    # branches below re-add them whenever THIS call binds the knob. config.xml
    # Params never carry them (verified: all self-closing), so this is a no-op
    # for config-sourced atoms.
    attrib.pop("customParam", None)
    attrib.pop("value", None)
    default = attrib.get("defaultValue", spec.get("text", "") or "0")

    if role == "chart":
        # bind to the block's data var; optional MTF via chart_tf kwarg
        attrib.setdefault("type", "data")
        attrib.setdefault("controlType", "dataVar")
        attrib.setdefault("defaultValue", "0")
        attrib["customParam"] = "true"          # matches the import-proven form
        attrib["paramType"] = "data"
        attrib["value"] = "#Chart1#"
        chart_tf = kwargs.get("chart_tf")
        if chart_tf:
            attrib["chartTF"] = chart_tf
            attrib["display"] = f"Chart-{chart_tf}"
        text = "#Chart1#"

    elif role == "shift":
        # Export-harvested shift text is the source block's pick (e.g. 2), not a
        # default — prefer the declared defaultValue for export-sourced atoms.
        if from_export:
            fallback = attrib.get("defaultValue") or spec.get("text") or "1"
        else:
            fallback = spec.get("text") or "1"
        text = str(kwargs.get("shift", fallback))

    elif role in ("period", "double"):
        if name in kwargs:
            val = str(kwargs[name])
            if _PARAM_REF.match(val):                 # bind to an outer optimizer knob
                attrib["customParam"] = "true"
                attrib["value"] = val
                text = val
            else:                                     # freeze at a literal
                text = val
        else:
            text = default                            # unbound -> frozen at config default

    elif role in ("combo", "line"):
        # same defaultValue preference for export-sourced combo/line picks
        if from_export:
            fallback = attrib.get("defaultValue") or spec.get("text") or "0"
        else:
            fallback = spec.get("text") or attrib.get("defaultValue", "0")
        text = str(kwargs.get(name, fallback))

    elif role == "bool":
        text = str(kwargs.get(name, spec.get("text") or attrib.get("defaultValue", "false")))

    else:
        text = str(kwargs.get(name, spec.get("text") or default))

    inner = "".join(f' {k}="{_esc_attr(str(v))}"' for k, v in attrib.items())
    return f"<Param{inner}>{_esc_text(text)}</Param>"


class Catalog:
    def __init__(self, path: str | Path):
        path = Path(path)
        data = json.loads(path.read_text(encoding="utf-8"))
        if "atoms" not in data:
            # Loading another skill's catalog.json (e.g. sqx-random-group's, which
            # shares the filename but not the schema) used to yield empty dicts and
            # silent garbage downstream (audit P0-1). Refuse loudly instead.
            top = ", ".join(sorted(data)) if isinstance(data, dict) and data else "none"
            raise SystemExit(
                f"FAIL: {path} has no 'atoms' section (top-level keys: {top}).\n"
                f"  This looks like another skill's catalog (sqx-random-group also "
                f"writes a catalog.json, with an incompatible schema).\n"
                f"  Rebuild THIS skill's catalog with:\n"
                f'    python engine/bootstrap.py --install "<your SQX folder>"'
            )
        self.meta = data["meta"]
        self.atoms = data["atoms"]

    # -- introspection -------------------------------------------------------
    def has(self, key: str) -> bool:
        return key in self.atoms

    def info(self, key: str) -> dict:
        return self.atoms[key]

    def search(self, term: str) -> list[str]:
        t = term.lower()
        return sorted(k for k, e in self.atoms.items()
                      if t in k.lower() or t in (e.get("name", "").lower()))

    # -- emit ----------------------------------------------------------------
    def atom(self, key: str, *, allow_talib: bool = False,
             allow_shift0: bool = False, **kwargs) -> str:
        """Emit a block-ready <Item> for `key`. Bind a knob by passing its friendly
        name (e.g. period="#Int2#"); freeze it with a literal (period="14"); pick a
        combo/line with its value (line="1", computedfrom="2"); set shift=, chart_tf=."""
        if key not in self.atoms:
            sugg = self.search(key)[:6]
            raise KeyError(f"atom {key!r} not in catalog. similar: {sugg}")
        e = self.atoms[key]
        if not e["usable_single_symbol"] and not allow_talib:
            raise ValueError(
                f"{key!r} is a talib_* atom — UNUSABLE in single-symbol/FX builds "
                f"(Strategy.Stockpicker NPE at build time). Use a native equivalent, "
                f"or pass allow_talib=True only for portfolio/stockpicker projects."
            )
        # Refuse a developing-bar read of any OHLC/indicator atom (look-ahead). The bar's
        # O/H/L/C — and anything derived from it — keeps changing until the bar closes, so
        # shift=0 peeks at data you would not have live (works only on TradeStation's intrabar
        # engine). Time atoms (BarHour/BarTime, categoryType "other") are deterministic and
        # exempt; constants (Number) too. Escape hatch: allow_shift0=True.
        from_export = e.get("source") == "export"
        if not allow_shift0 and e["attrib"].get("categoryType") in (
                "indicator", "priceValue", "priceRange"):
            shift_spec = next((p for p in e["params"] if p.get("role") == "shift"), None)
            if shift_spec is not None:
                # mirror _render_param's fallback so the guard judges the shift
                # value that will actually be emitted
                if from_export:
                    fb = (shift_spec.get("attrib", {}).get("defaultValue")
                          or shift_spec.get("text") or "1")
                else:
                    fb = shift_spec.get("text") or "1"
                resolved = str(kwargs.get("shift", fb))
                if resolved == "0":
                    raise ValueError(
                        f"{key!r}: refusing shift=0 (developing bar) — look-ahead on SQX/MT "
                        f"engines (TradeStation-only). Read OHLC/indicators on the last CLOSED "
                        f"bar (shift>=1); for a breakout, put the channel one bar further back. "
                        f"Pass allow_shift0=True only if you truly target TradeStation intrabar."
                    )
        # warn-by-return on unbound multi-output? No — default line is fine; caller picks.
        params = "".join(_render_param(p, kwargs, from_export) for p in e["params"])
        return f"{_open_tag(e['attrib'])}{params}</Item>"

    def number(self, value: str, bind: str | None = None, step: str = "1") -> str:
        """A numeric-constant operand (the Number value-atom). Bind to an outer knob
        with bind="#Double3#", or pass a literal value."""
        if bind:
            return (
                f'<Item customSnippet="false" key="Number" name="(NUM) Number" '
                f'display="#Number#" returnType="number" help="Number constant" '
                f'mI="Other" categoryType="other" notFirstValue="true">'
                f'<Param key="#Number#" name="Number" type="double" defaultValue="{_esc_attr(value)}" '
                f'controlType="jspinner" minValue="-999999999" maxValue="999999999" step="{step}" '
                f'builderStep="{step}" customParam="true" value="{bind}">{bind}</Param></Item>'
            )
        return (
            f'<Item customSnippet="false" key="Number" name="(NUM) Number" '
            f'display="#Number#" returnType="number" help="Number constant" '
            f'mI="Other" categoryType="other" notFirstValue="true">'
            f'<Param key="#Number#" name="Number" type="double" defaultValue="{_esc_attr(value)}" '
            f'controlType="jspinner" minValue="-999999999" maxValue="999999999" step="{step}" '
            f'builderStep="{step}">{_esc_text(value)}</Param></Item>'
        )
