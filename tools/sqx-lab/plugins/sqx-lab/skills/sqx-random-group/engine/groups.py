"""groups.py — SQX random-group engine (build-144).

Emits <RandomGroups> sets in the two item modes confirmed byte-faithful against a
real 144 export (see strategyquant_144/blockGroups_144_export.xml):

  HYBRID  — re-export an EXISTING custom block by key. categoryType="Custom blocks",
            a bare CBlock_* reference with NO <Contents> (AlgoWizard re-resolves the
            rule body at import). Top-level <Param>s are copied verbatim from the
            block; the #Chart1# data param gets an inner "0".

  INLINE  — a FRESH rule/value/comparison built from the install's config.xml
            templates: a simpleRules boolean ("HMA is falling"), a value atom
            ("Close", "EMA"), or an operator over two operands ("Close >= EMA").
            Native param keys + the catalog's verbose metadata, with optimizer hints.

Optimizer-hint model (per <Param>, confirmed in the export):
  frozen    no generate attr                          -> builder never varies it
  default   generate="random" randomValue="default"   -> optimize over the param's OWN min/max/step
  override  generate="random" randomValue="lo:hi:step" -> optimize over an explicit (narrower) range

Any numeric knob is optimizable: type "int"/"double" or paramType "period"/"double"
(this includes every custom-block #IntN# knob and session-gate hours). An optimize
key that matches NO param, or targets a data/combo/shift param, raises ValueError —
a silently dropped knob is how "v1 froze the knobs" happened. number() constants are
optimized via number(value, optimize="lo:hi:step").

An item is FLAT: a single boolean atom, OR one operator with two value operands.
Compound AND/OR logic belongs in a custom block, then referenced via HYBRID.

    from engine.groups import load_templates, load_blocks, inline_item, compare, \
        hybrid_ref, make_group, wrap_groups
    T = load_templates("config.xml")          # config.xml indicator/simpleRules templates
    B = load_blocks("customBlocks.xml")        # the user's CBlock_* definitions
    cond = make_group("MyFilters", "Condition", [
        inline_item(T["HMAFalling"]),                                  # frozen
        inline_item(T["MomRising"], optimize={"#Period#": "10:60:5"}), # override
    ], category="Filters")
"""

from __future__ import annotations

import json
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

# ---------------------------------------------------------------------------
# escaping (attribute values + inner text) — same rule that breaks the parser
# if a help/display string carries a raw < > &
# ---------------------------------------------------------------------------

def _esc_attr(v: str) -> str:
    return (str(v).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _esc_text(v: str) -> str:
    return str(v).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------------------------------------------------------------------------
# template / block loading
# ---------------------------------------------------------------------------

def _params_of(item: ET.Element) -> list[ET.Element]:
    """Direct-child <Param>s plus those nested in <paramCategory> (config form),
    in document order — matching bootstrap.py's flattening."""
    out: list[ET.Element] = []
    for child in item:
        if child.tag == "Param":
            out.append(child)
        elif child.tag == "paramCategory":
            out.extend(pc for pc in child if pc.tag == "Param")
    return out


def load_templates(config_path: str | Path) -> dict[str, ET.Element]:
    """Index every <Item key=...> in config.xml that carries params (indicators,
    priceValue/priceRange atoms, and simpleRules boolean rules), keeping the richest
    schema per key. These are the templates INLINE items are built from."""
    root = ET.parse(config_path).getroot()
    out: dict[str, ET.Element] = {}
    for item in root.iter("Item"):
        key = item.get("key")
        if not key:
            continue
        params = _params_of(item)
        if not params:                       # weight-preset stubs (<Set .../>) have none
            continue
        if key in out and len(_params_of(out[key])) >= len(params):
            continue
        out[key] = item
    return out


def load_blocks(customblocks_path: str | Path) -> dict[str, ET.Element]:
    """Parse a customBlocks*.xml -> {CBlock_key: <Item>} for HYBRID re-export."""
    root = ET.parse(customblocks_path).getroot()
    out: dict[str, ET.Element] = {}
    for it in root.findall("Item"):
        k = it.get("key")
        if k:
            out[k] = it
    return out


def load_catalog(catalog_path: str | Path) -> tuple[dict, dict[str, ET.Element],
                                                     dict[str, ET.Element]]:
    """Load a bootstrap catalog.json. Returns (meta, templates, blocks) where templates
    merges inline `rules` + `values` ({key: <Item>}) and blocks is the HYBRID index
    ({CBlock_key: <Item>}). The stored items are clean (paramCategory flattened, no
    <Contents>), so inline_item / hybrid_ref consume them unchanged.

    Raises SystemExit if the file is not an sqx-random-group catalog: every skill
    writes a catalog.json, and loading another skill's flavour used to return empty
    dicts — the generator then emitted an EMPTY group and printed success (P0-1)."""
    path = Path(catalog_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    missing = [k for k in ("rules", "values", "blocks")
               if not isinstance(data, dict) or k not in data]
    if missing:
        if isinstance(data, dict) and "atoms" in data:
            hint = ('It looks like the sqx-custom-block skill\'s catalog — that one keeps '
                    '"atoms" where this skill keeps "rules"/"values"/"blocks".')
        else:
            owner = (data.get("meta") or {}).get("skill") if isinstance(data, dict) else None
            hint = (f"It says it belongs to {owner!r} — a different skill's catalog."
                    if owner and owner != "sqx-random-group" else
                    "It does not have this skill's schema — most likely a different "
                    "skill's catalog.json landed here.")
        raise SystemExit(
            f"FAIL: {path} is not an sqx-random-group catalog — missing key(s): "
            f"{', '.join(missing)}. {hint}\n"
            f"  Rebuild this skill's catalog from your install:\n"
            f"    python engine/bootstrap.py")
    templates: dict[str, ET.Element] = {}
    for section in ("rules", "values"):
        for key, xml in data.get(section, {}).items():
            templates[key] = ET.fromstring(xml)
    blocks = {key: ET.fromstring(xml) for key, xml in data.get("blocks", {}).items()}
    return data.get("meta", {}), templates, blocks


# ---------------------------------------------------------------------------
# param roles + emission
# ---------------------------------------------------------------------------

def _role(p: ET.Element) -> str:
    key, ptype = p.get("key", ""), p.get("type", "")
    pt, ctrl = p.get("paramType", ""), p.get("controlType", "")
    if key == "#Line#":
        return "line"
    if ptype == "data":
        return "chart"
    if pt == "shift":
        return "shift"
    if pt == "period":
        return "period"
    if ctrl == "combo":
        return "combo"
    if ptype == "double":
        return "double"
    if ptype == "boolean":
        return "bool"
    return "other"


def _attrs(elem: ET.Element) -> str:
    return "".join(f' {k}="{_esc_attr(v)}"' for k, v in elem.attrib.items())


def _optimize_refusal(p: ET.Element) -> str | None:
    """Why this param can NOT be optimized (None = it can). Optimizable = any numeric
    knob: type "int"/"double" or paramType "period"/"double" — which covers every
    custom-block #IntN# knob and the session-gating hour params. data/combo/shift are
    refused LOUDLY: silently dropping them is exactly the P0-13 failure mode."""
    if p.get("type") == "data":
        return "it is a data/chart param (charts are wired by the builder, not optimized)"
    if p.get("controlType") == "combo":
        return "it is a combo pick, not a numeric knob (set it via picks= instead)"
    if p.get("paramType") == "shift":
        return "it is a bar-shift param (set it via shift= instead)"
    if p.get("type") in ("int", "double") or p.get("paramType") in ("period", "double"):
        return None
    return (f"type={p.get('type')!r} / paramType={p.get('paramType')!r} is not an "
            f"optimizable numeric knob (need type int/double or paramType period/double)")


def _check_optimize(owner: ET.Element, params: list[ET.Element],
                    optimize: dict[str, str]) -> None:
    """Every optimize key must name a REAL param of the item, and that param must be
    an optimizable numeric knob — otherwise ValueError. A misspelled or ineligible
    key must never be silently ignored (that is how 'v1 froze the knobs')."""
    if not optimize:
        return
    by_key = {p.get("key"): p for p in params if p.get("key")}
    unknown = sorted(k for k in optimize if k not in by_key)
    if unknown:
        raise ValueError(
            f"optimize key(s) {', '.join(map(repr, unknown))} match no param of "
            f"{owner.get('key')!r} — its actual param keys are: {sorted(by_key)}")
    for k in sorted(optimize):
        why = _optimize_refusal(by_key[k])
        if why:
            raise ValueError(f"cannot optimize param {k!r} of {owner.get('key')!r}: {why}")


def _inline_param(p: ET.Element, optimize: dict[str, str], shift: str,
                  picks: dict[str, str], is_snippet: bool) -> str:
    """Emit one INLINE <Param> from a config template param: copy its attribs (verbose
    catalog metadata preserved, in order), give it an inner value, and stamp an
    optimizer hint if the caller asked to optimize it. A customSnippet indicator's
    #Shift# carries customParam="false" in the export (a no-op default reproduced for
    byte-fidelity); native rules omit it."""
    role = _role(p)
    key = p.get("key", "")
    default = (p.get("defaultValue") or (p.text or "").strip() or "0")
    if role == "chart":
        body = "0"
    elif role == "shift":
        body = str(shift)
    elif role in ("combo", "line"):
        body = str(picks.get(key, p.get("defaultValue", "0")))
    elif role == "bool":
        body = p.get("defaultValue", "false")
    else:
        body = default
    extra = ""
    if role == "shift" and is_snippet:
        extra = ' customParam="false"'
    elif key in optimize:
        # eligibility already enforced by _check_optimize (any int/double knob;
        # data/combo/shift raise there) — emit the hint unconditionally here
        extra = f' generate="random" randomValue="{_esc_attr(optimize[key])}"'
    return f"<Param{_attrs(p)}{extra}>{_esc_text(body)}</Param>"


# ---------------------------------------------------------------------------
# INLINE items — fresh rules / values / comparisons
# ---------------------------------------------------------------------------

def inline_item(tmpl: ET.Element, optimize: dict[str, str] | None = None,
                shift: str = "1", picks: dict[str, str] | None = None) -> str:
    """A fresh group item from a config template (simpleRules boolean OR value atom).
    `optimize` = {param_key: "default" | "lo:hi:step"} for the knobs to randomize
    (others stay frozen) — any int/double knob qualifies; a key that matches no param
    or targets a data/combo/shift param raises ValueError. `picks` = {combo/line key:
    value}. `shift` = bar offset. Use the same call to build an operator OPERAND,
    then pass it to compare()."""
    optimize = optimize or {}
    picks = picks or {}
    plist = _params_of(tmpl)
    _check_optimize(tmpl, plist, optimize)
    is_snippet = tmpl.get("customSnippet") == "true"
    params = "".join(_inline_param(p, optimize, shift, picks, is_snippet)
                     for p in plist)
    return f"<Item{_attrs(tmpl)}>{params}</Item>"


def _value_block(slot: str, name: str, inner: str) -> str:
    return f'<Block key="{slot}" name="{name}" type="value" controlType="value">{inner}</Block>'


def compare(op_key: str, op_name: str, op_display: str, left: str, right: str) -> str:
    """An operator comparison item: one operator over two value operands (each an
    inline value atom). op_name/op_display must be pre-escaped. Boolean result."""
    return (
        f'<Item customSnippet="false" key="{op_key}" name="{op_name}"'
        f' display="{op_display}" returnType="boolean" mI="Comparisons"'
        f' categoryType="operators">'
        f'{_value_block("#Left#", "Left", left)}{_value_block("#Right#", "Right", right)}'
        f'</Item>'
    )


# common operators (name/display pre-escaped to match the export)
def is_greater(left, right):          return compare("IsGreater", "(&gt;) Is greater", "#Left# &gt; #Right#", left, right)
def is_lower(left, right):            return compare("IsLower", "(&lt;) Is lower", "#Left# &lt; #Right#", left, right)
def is_greater_or_equal(left, right): return compare("IsGreaterOrEqual", "(&gt;=) Is greater or equal", "#Left# &gt;= #Right#", left, right)
def is_lower_or_equal(left, right):   return compare("IsLowerOrEqual", "(&lt;=) Is lower or equal", "#Left# &lt;= #Right#", left, right)
def crosses_above(left, right):       return compare("CrossesAbove", "Crosses Above", "#Left# crosses above #Right#", left, right)
def crosses_below(left, right):       return compare("CrossesBelow", "Crosses Below", "#Left# crosses below #Right#", left, right)


def number(value: str, bind: str | None = None, step: str = "1",
           optimize: str | None = None) -> str:
    """A numeric-constant value atom — to compare an indicator against a level, e.g.
    is_lower(inline_item(T["RSI"]), number("30")). Pass optimize="lo:hi:step" to make
    the constant a real optimizer knob: emits generate="random" randomValue="lo:hi:step"
    on the #Number# param, keeps the value in the element text and sets
    defaultValue="0" — the exact shape of a real AlgoWizard export. bind="#Double3#"
    (a custom-param reference) is mutually exclusive with optimize."""
    if bind and optimize:
        raise ValueError("number(): pass either bind= or optimize=, not both")
    cp = f' customParam="true" value="{_esc_attr(bind)}"' if bind else ""
    opt = f' generate="random" randomValue="{_esc_attr(optimize)}"' if optimize else ""
    body = bind if bind else value
    default = "0" if optimize else value
    return ('<Item customSnippet="false" key="Number" name="(NUM) Number" display="#Number#"'
            ' returnType="number" help="Number constant" mI="Other" categoryType="other"'
            ' notFirstValue="true">'
            f'<Param key="#Number#" name="Number" type="double" defaultValue="{_esc_attr(default)}"'
            f' controlType="jspinner" minValue="-999999999" maxValue="999999999" step="{step}"'
            f' builderStep="{step}"{cp}{opt}>{_esc_text(body)}</Param></Item>')


# ---------------------------------------------------------------------------
# HYBRID items — re-export an existing custom block by reference
# ---------------------------------------------------------------------------

def hybrid_ref(block: ET.Element, optimize: dict[str, str] | None = None) -> str:
    """Re-export `block` (a <Item> from customBlocks.xml) as a group item: copy its
    opening-tag attribs (incl. categoryType="Custom blocks", oppositeBlockKey) and
    its TOP-LEVEL <Param>s verbatim, drop <Contents>. The #Chart1# data param gets an
    inner "0". Pass optimize={param_key: range} to randomize chosen knobs (default:
    copy the block's frozen values — which is what your 144 export does). An optimize
    key matching no param, or targeting a data/combo/shift param, raises ValueError."""
    optimize = optimize or {}
    _check_optimize(block, block.findall("Param"), optimize)
    parts = []
    for p in block.findall("Param"):                 # direct children only (not Contents)
        key = p.get("key", "")
        if p.get("type") == "data" or key == "#Chart1#":
            body = "0"
        else:
            body = (p.text or p.get("defaultValue") or "0").strip()
        extra = ""
        if key in optimize:
            extra = f' generate="random" randomValue="{_esc_attr(optimize[key])}"'
        parts.append(f"<Param{_attrs(p)}{extra}>{_esc_text(body)}</Param>")
    return f"<Item{_attrs(block)}>{''.join(parts)}</Item>"


# ---------------------------------------------------------------------------
# group + document wrappers
# ---------------------------------------------------------------------------

def make_group(name: str, type_: str, items: list[str], category: str = "No category",
               group_id: str | None = None, status: str | None = "0",
               action: str | None = "add") -> str:
    """Wrap items in a <Group>. type_ in {Condition, Value}. status/action default to
    the generator convention ("0"/"add"); pass None to omit (a freshly UI-created
    group omits them, and AlgoWizard tolerates absence either way)."""
    if type_ not in ("Condition", "Value"):
        raise ValueError(f"group type must be 'Condition' or 'Value', got {type_!r}")
    gid = group_id or str(uuid.uuid4())
    extra = ""
    if status is not None:
        extra += f' status="{_esc_attr(status)}"'
    if action is not None:
        extra += f' action="{_esc_attr(action)}"'
    return (f'<Group id="{gid}" name="{_esc_attr(name)}" type="{type_}"'
            f' strategyType="Standard" category="{_esc_attr(category)}"{extra}>'
            f'{"".join(items)}</Group>')


def wrap_groups(groups: list[str]) -> str:
    return "<RandomGroups>" + "".join(groups) + "</RandomGroups>"
