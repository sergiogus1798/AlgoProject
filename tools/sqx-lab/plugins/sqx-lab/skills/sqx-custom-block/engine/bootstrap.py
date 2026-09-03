"""bootstrap.py — derive a custom-block atom catalog from a user's OWN install.

This is what makes the skill portable. Instead of shipping one install's hardcoded
indicator schemas, we read the target user's two registries and discover what THEY
can build with:

  1. global/config.xml          -> native indicators for THEIR build (any 14x)
  2. customBlocksExport.xml      -> their compiled user-custom indicators (optional)

Output:
  catalog.json   machine catalog (full param schema per atom) -> consumed by emit.py
  catalog.md     human coverage report (what exists, midlines, knobs, talib flags)

Usage:
  python engine/bootstrap.py path/to/global/config.xml
  python engine/bootstrap.py path/to/config.xml --export path/to/customBlocksExport.xml
  python engine/bootstrap.py path/to/config.xml --out-dir .

Why per-user discovery is correct (not lazy): an indicator <Item> in config.xml is
already 90% of a usable atom. The only transform to make it block-ready is mechanical
(flatten <paramCategory> wrappers, bind a tunable to an optimizer slot, give each Param
inner text). By copying the user's own schema we are correct for their build *by
construction* — no guessing whether they run 142/143/144/145.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

try:                                    # works whether run as a script or imported
    from engine.discover import find_installs, resolve_install, SUBPATHS
except ImportError:
    from discover import find_installs, resolve_install, SUBPATHS

# Shared per-machine state + install validation live in sqx_common at the plugin root.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from sqx_common import (  # noqa: E402
    load_shared_install, save_shared_install, install_file, skill_dir,
    validate_install, install_error)

SKILL_DIR = skill_dir(__file__)


# Value return-types: an atom usable as an operand inside a comparison.
VALUE_RETURN_TYPES = {"price", "number", "pricerange", "pricenumber", "priceValue"}

# categoryTypes that are NOT operand atoms (skip these).
# NOTE: priceRange is NOT skipped — ATR and ~8 other range-type atoms live there
# (categoryType="priceRange", returnType="pricerange"); they ARE valid operands.
SKIP_CATEGORY_TYPES = {"operators", "simpleRules", "randomBlock"}

# mI families that are ACTION blocks (open/close/modify trade), not value atoms.
SKIP_MI = {"StrategyControl", "OtherActions", "Modify", "Open", "Close"}


def _classify_param(p: ET.Element) -> str:
    """Role of a <Param> inside an indicator <Item>."""
    key = p.get("key", "")
    ptype = p.get("type", "")
    param_type = p.get("paramType", "")
    control = p.get("controlType", "")
    if key == "#Line#":
        return "line"           # multi-output selector
    if ptype == "data":
        return "chart"          # #Chart# data var
    if param_type == "shift":
        return "shift"
    if param_type == "period":
        return "period"         # tunable int -> bindable optimizer knob
    if control == "combo":
        return "combo"          # ComputedFrom / Mode / MAMethod / PriceField
    if ptype == "double":
        return "double"         # tunable double -> bindable optimizer knob
    if ptype == "boolean":
        return "bool"
    return "other"


def _params_of(item: ET.Element) -> list[ET.Element]:
    """All <Param> elements of an indicator <Item>, flattening <paramCategory>
    wrappers. Direct-child Params (export form) and paramCategory-nested Params
    (config form) are both collected, in document order."""
    params: list[ET.Element] = []
    for child in item:
        if child.tag == "Param":
            params.append(child)
        elif child.tag == "paramCategory":
            params.extend(pc for pc in child if pc.tag == "Param")
    return params


def _atom_entry(item: ET.Element, source: str) -> dict:
    params = _params_of(item)
    param_specs = []
    bindable = []
    for p in params:
        role = _classify_param(p)
        spec = {"attrib": dict(p.attrib), "role": role, "text": (p.text or "").strip()}
        param_specs.append(spec)
        if role in ("period", "double"):
            bindable.append(p.get("key"))
    key = item.get("key", "")
    return {
        "key": key,
        "name": item.get("name", ""),
        "display": item.get("display", ""),
        "returnType": item.get("returnType", ""),
        "mI": item.get("mI", ""),
        "categoryType": item.get("categoryType", ""),
        "isOscillator": item.get("isOscillator", ""),
        "middleValue": item.get("middleValue", ""),
        "indicatorMin": item.get("indicatorMin", ""),
        "indicatorMax": item.get("indicatorMax", ""),
        "help": item.get("help", ""),
        "attrib": dict(item.attrib),          # full opening-tag fidelity for emit
        "params": param_specs,
        "bindable": bindable,
        "multi_output": any(s["role"] == "line" for s in param_specs),
        "usable_single_symbol": not key.startswith("talib_"),
        "source": source,
        "confidence": "proven",       # config/export schemas are real SQX output
    }


def _is_value_atom(item: ET.Element) -> bool:
    ct = item.get("categoryType")
    if ct in SKIP_CATEGORY_TYPES or ct is None:
        return False
    if item.get("mI") in SKIP_MI:
        return False
    rt = item.get("returnType")
    if rt not in VALUE_RETURN_TYPES:
        return False
    if not _params_of(item):       # index stubs like <Item key="RSI"/> have no params
        return False
    # indicator + priceValue + priceRange are the operand families; allow "other"
    # only for the bar/time and price-transform mI families
    if ct in ("indicator", "priceValue", "priceRange"):
        return True
    # mI="Price" carries Volume / Spread / SpreadInPips / talib price transforms —
    # real operands the old tuple dropped (the skill then denied the install has
    # volume). Do NOT open all of categoryType="other": that would drag in
    # Number/IntVariable/DoubleVariable and the 46 mI="Functions" operator nodes.
    if ct == "other" and item.get("mI") in ("BarAndTime", "BarRange", "Price"):
        return True
    return False


def _harvest(root: ET.Element, source: str, prefer_richest: bool = True) -> dict[str, dict]:
    """Walk a parsed tree, keep the richest schema per atom key."""
    found: dict[str, dict] = {}
    for item in root.iter("Item"):
        if not _is_value_atom(item):
            continue
        entry = _atom_entry(item, source)
        key = entry["key"]
        if key in found and prefer_richest:
            if len(entry["params"]) <= len(found[key]["params"]):
                continue
        found[key] = entry
    return found


def parse_config(path: Path) -> dict[str, dict]:
    root = ET.parse(path).getroot()
    return _harvest(root, "config")


def parse_export(path: Path) -> dict[str, dict]:
    """Harvest user-custom indicator schemas from an exported block file.
    These appear as customSnippet="true" indicator <Item>s nested in <Contents>."""
    root = ET.parse(path).getroot()
    out: dict[str, dict] = {}
    for item in root.iter("Item"):
        if item.get("categoryType") != "indicator":
            continue
        if not _params_of(item):
            continue
        entry = _atom_entry(item, "export")
        key = entry["key"]
        # keep the richest instance per key
        if key in out and len(entry["params"]) <= len(out[key]["params"]):
            continue
        out[key] = entry
    return out


def _synth_period(key: str, name: str, default: str) -> dict:
    return {"attrib": {
        "key": key, "name": name, "type": "int", "defaultValue": default,
        "genMinValue": "-1000003", "genMaxValue": "-1000004", "paramType": "period",
        "controlType": "jspinnerVar", "minValue": "1", "maxValue": "100000",
        "step": "1", "builderStep": "1",
    }, "role": "period", "text": default}


def _synth_double(key: str, name: str, default: str) -> dict:
    return {"attrib": {
        "key": key, "name": name, "type": "double", "defaultValue": default,
        "controlType": "jspinnerVar", "minValue": "0.01", "maxValue": "1000",
        "step": "0.1", "builderStep": "0.1",
    }, "role": "double", "text": default}


def parse_user_indicators(path: Path) -> dict[str, dict]:
    """Synthesize block atoms from UserCustomIndicators.xml — the install's registry of
    the user's OWN compiled indicators. This lets a user use an indicator they have built
    even if they have NOT yet used it in an exported block. The synthesized schema is
    modeled on the proven customSnippet form; flagged confidence='synthesized' (verify on
    first import). The zero-risk alternative is to use the indicator in one throwaway block,
    export, and re-bootstrap (then it arrives as confidence='proven')."""
    root = ET.parse(path).getroot()
    out: dict[str, dict] = {}
    for ci in root.iter("CustomIndicator"):
        short = (ci.get("shortName") or ci.get("fileName") or "").replace(" ", "")
        if not short:
            continue
        long = ci.get("longName") or short
        rt = ci.get("returnType") or "number"
        reg_params = ci.findall("./params/param")
        outputs = ci.findall("./outputs/output")

        specs = [{"attrib": {
            "key": "#Chart#", "name": "Chart", "type": "data",
            "controlType": "dataVar", "defaultValue": "0"}, "role": "chart", "text": ""}]
        refs, bindable = [], []
        for p in reg_params:
            pname = (p.get("name") or f"Param{p.get('index','1')}").replace(" ", "")
            pkey = f"#{pname}#"
            default = p.get("defaultValue") or "0"
            ptype = (p.get("type") or "int").lower()
            if ptype in ("double", "float"):
                specs.append(_synth_double(pkey, pname, default))
            else:
                specs.append(_synth_period(pkey, pname, default))
            refs.append(pkey)
            bindable.append(pkey)
        specs.append({"attrib": {
            "key": "#Shift#", "name": "Shift", "type": "int", "defaultValue": "1",
            "controlType": "jspinnerVar", "minValue": "0", "maxValue": "1000",
            "genMinValue": "-1000001", "genMaxValue": "-1000002", "paramType": "shift",
            "step": "1", "builderStep": "1"}, "role": "shift", "text": "1"})

        multi = len(outputs) > 1
        if multi:
            vals = ",".join(f"{(o.get('name') or f'Out{i}').replace(' ', '')}={i}"
                            for i, o in enumerate(outputs))
            specs.append({"attrib": {
                "key": "#Line#", "name": "Line", "type": "int", "controlType": "combo",
                "values": vals, "defaultValue": "0"}, "role": "line", "text": "0"})

        disp = f"{short}(@Chart@{', '.join(refs)})" + (".#Line#" if multi else "") + "[#Shift#]"
        out[short] = {
            "key": short, "name": f"({short[:4].upper()}) {long}", "display": disp,
            "returnType": rt, "mI": short, "categoryType": "indicator",
            "isOscillator": "", "middleValue": "", "indicatorMin": "", "indicatorMax": "",
            "help": "",
            "attrib": {"customSnippet": "true", "key": short,
                       "name": f"({short[:4].upper()}) {long}", "display": disp,
                       "returnType": rt, "mI": short, "categoryType": "indicator", "help": ""},
            "params": specs, "bindable": bindable, "multi_output": multi,
            "usable_single_symbol": True, "source": "registry", "confidence": "synthesized",
        }
    return out


# -- shared param-spec builders (used by registry-synth AND java-snippet paths) -------
def _chart_spec() -> dict:
    return {"attrib": {"key": "#Chart#", "name": "Chart", "type": "data",
            "controlType": "dataVar", "defaultValue": "0"}, "role": "chart", "text": ""}


def _shift_spec() -> dict:
    return {"attrib": {"key": "#Shift#", "name": "Shift", "type": "int", "defaultValue": "1",
            "controlType": "jspinnerVar", "minValue": "0", "maxValue": "1000",
            "genMinValue": "-1000001", "genMaxValue": "-1000002", "paramType": "shift",
            "step": "1", "builderStep": "1"}, "role": "shift", "text": "1"}


def _line_spec(values: str) -> dict:
    return {"attrib": {"key": "#Line#", "name": "Line", "type": "int", "controlType": "combo",
            "values": values, "defaultValue": "0"}, "role": "line", "text": "0"}


def _knob_spec(key: str, name: str, default: str, mn: str, mx: str, step: str,
               is_double: bool) -> dict:
    attrib = {"key": key, "name": name, "type": "double" if is_double else "int",
              "defaultValue": default, "controlType": "jspinnerVar",
              "minValue": mn, "maxValue": mx, "step": step, "builderStep": step}
    if not is_double:
        attrib.update({"genMinValue": "-1000003", "genMaxValue": "-1000004",
                       "paramType": "period"})
    return {"attrib": attrib, "role": "double" if is_double else "period", "text": default}


def _java_attr(text: str, name: str) -> str | None:
    """Pull name="value" from a Java annotation-argument string (quoted strings only)."""
    m = re.search(rf'\b{name}\s*=\s*"([^"]*)"', text)
    return m.group(1) if m else None


_RETURNTYPE_MAP = {"number": "number", "price": "price", "pricerange": "pricerange",
                   "percent": "number"}


def parse_snippets(indicators_dir: Path | None) -> dict[str, dict]:
    """AUTO-DETECT the user's own coded custom indicators by reading their Java sources
    anywhere under user/extend/Snippets/ (typically SQ/Blocks/Indicators/<Name>/<Name>.java,
    but the package subfolder varies between installs, so we search the whole tree). This is
    the real, complete list of their custom indicators — UserCustomIndicators.xml is only a
    tiny subset, so without this the skill silently misses most of what the user has built.

    A file is kept only if it is a value indicator: it has @BuildingBlock AND
    `extends IndicatorBlock` (so the companion `extends ConditionBlock` boolean signals and
    `FunctionBlock`/utility files in the same tree are skipped). The class-level @BuildingBlock
    gives the exact display + returnType, @Indicator the midline/min/max, each @Parameter a
    knob (or the chart data input), and each @Output a line — so the block atom is
    reconstructed faithfully, not guessed. Flagged confidence='snippet' (verify on first
    import; seed via one block + export to promote to 'proven')."""
    out: dict[str, dict] = {}
    if not indicators_dir or not indicators_dir.is_dir():
        return out
    for java in sorted(indicators_dir.rglob("*.java")):
        try:
            text = java.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "@BuildingBlock" not in text:
            continue
        # Keep value indicators; exclude the non-indicator block types that share this tree:
        # ConditionBlock = boolean signals (...AboveLevel/CrossUP), FunctionBlock = value
        # functions. We EXCLUDE those two rather than REQUIRE `extends IndicatorBlock`, so an
        # imported indicator that extends a renamed/custom base class is still picked up.
        if "extends ConditionBlock" in text or "extends FunctionBlock" in text:
            continue
        split = text.find("public class")
        header = text[:split] if split != -1 else text
        body = text[split:] if split != -1 else text

        cls = re.search(r'class\s+(\w+)', body)
        if not cls:
            continue
        # Only VALUE indicators are operands. The snippet folder also holds the user's
        # companion ConditionBlock files (returnType=Boolean, e.g. "...AboveLevel",
        # "...CrossUP") — those are complete boolean signals, NOT value atoms, so skip them.
        rt_m = re.search(r'returnType\s*=\s*ReturnTypes\.(\w+)', header)
        rt_raw = (rt_m.group(1).lower() if rt_m else "number")
        if rt_raw not in _RETURNTYPE_MAP or "extends ConditionBlock" in body:
            continue
        key = cls.group(1)
        name = _java_attr(header, "name") or key
        display = _java_attr(header, "display") or f"{key}(@Chart@)[#Shift#]"
        rt = _RETURNTYPE_MAP[rt_raw]

        ind_m = re.search(r'@Indicator\s*\(([^)]*)\)', header)
        ind = ind_m.group(1) if ind_m else ""
        osc = "true" if re.search(r'oscillator\s*=\s*true', ind) else ""

        def _ind_num(field: str) -> str:
            m = re.search(rf'\b{field}\s*=\s*(-?[\d.]+)', ind)
            return m.group(1) if m else ""
        mid, imin, imax, istep = (_ind_num("middleValue"), _ind_num("min"),
                                  _ind_num("max"), _ind_num("step"))
        help_m = re.search(r'@Help\s*\(\s*"([^"]*)"', header)
        help_text = help_m.group(1) if help_m else ""

        specs: list[dict] = [_chart_spec()]
        bindable: list[str] = []
        for am in re.finditer(
                r'@Parameter\s*(?:\(([^)]*)\))?\s*public\s+([\w<>\[\]]+)\s+(\w+)\s*;', body):
            args, ftype, fname = (am.group(1) or ""), am.group(2), am.group(3)
            if ftype == "DataSeries":          # the chart input — already represented
                continue
            if ftype not in ("int", "double"):
                continue
            pkey = f"#{fname}#"
            pname = _java_attr(args, "name") or fname
            default = _java_attr(args, "defaultValue") or "0"
            mn = re.search(r'minValue\s*=\s*(-?[\d.]+)', args)
            mx = re.search(r'maxValue\s*=\s*(-?[\d.]+)', args)
            stp = re.search(r'step\s*=\s*([\d.]+)', args)
            is_double = (ftype == "double")
            specs.append(_knob_spec(
                pkey, pname, default,
                mn.group(1) if mn else ("0.01" if is_double else "1"),
                mx.group(1) if mx else ("1000" if is_double else "100000"),
                stp.group(1) if stp else ("0.1" if is_double else "1"), is_double))
            bindable.append(pkey)

        specs.append(_shift_spec())
        outputs = re.findall(
            r'@Output\s*(?:\(([^)]*)\))?\s*public\s+DataSeries\s+(\w+)', body)
        multi = len(outputs) > 1
        if multi:
            vals = ",".join(f"{(_java_attr(a, 'name') or fn).replace(' ', '')}={i}"
                            for i, (a, fn) in enumerate(outputs))
            specs.append(_line_spec(vals))

        attrib = {"customSnippet": "true", "key": key, "name": name, "display": display,
                  "returnType": rt, "mI": key, "categoryType": "indicator", "help": help_text}
        for k, v in (("isOscillator", osc), ("middleValue", mid),
                     ("indicatorMin", imin), ("indicatorMax", imax), ("indicatorStep", istep)):
            if v:
                attrib[k] = v

        out[key] = {
            "key": key, "name": name, "display": display, "returnType": rt,
            "mI": key, "categoryType": "indicator", "isOscillator": osc,
            "middleValue": mid, "indicatorMin": imin, "indicatorMax": imax, "help": help_text,
            "attrib": attrib, "params": specs, "bindable": bindable,
            "multi_output": multi, "usable_single_symbol": True,
            "source": "snippet", "confidence": "snippet",
        }
    return out


def build_catalog(config_path: Path, export_path: Path | None,
                  user_ind_path: Path | None = None,
                  snippets_dir: Path | None = None,
                  install_root: Path | str | None = None) -> dict:
    config_atoms = parse_config(config_path)
    export_atoms = parse_export(export_path) if export_path else {}
    # auto-detect the user-custom-indicator registry next to config.xml if not given
    if user_ind_path is None:
        guess = config_path.parent / "UserCustomIndicators.xml"
        if guess.exists():
            user_ind_path = guess
    registry_atoms = parse_user_indicators(user_ind_path) if user_ind_path else {}
    # auto-detect the user's coded custom-indicator snippets from the install root if not given
    if snippets_dir is None:
        try:
            root = config_path.parents[5]                 # ...global/config.xml -> install root
            guess = root / SUBPATHS["snippets"]
            if guess.is_dir():
                snippets_dir = guess
        except IndexError:
            pass
    snippet_atoms = parse_snippets(snippets_dir)
    snippet_java_files = (len(list(snippets_dir.rglob("*.java")))
                          if snippets_dir and snippets_dir.is_dir() else 0)

    # precedence: native config > proven export-custom > coded snippet > synthesized registry.
    # An atom only falls through to a lower-confidence source if absent above.
    atoms = dict(config_atoms)
    export_added, snippet_added, registry_added = [], [], []
    for key, entry in export_atoms.items():
        if key not in atoms:
            atoms[key] = entry
            export_added.append(key)
    for key, entry in snippet_atoms.items():
        if key not in atoms:                 # config/export don't already have it
            atoms[key] = entry
            snippet_added.append(key)
    for key, entry in registry_atoms.items():
        if key not in atoms:                 # none of config/export/snippet has it
            atoms[key] = entry
            registry_added.append(key)

    # --- Identify the user's OWN custom indicators ROBUSTLY ----------------------------
    # The DECISIVE marker is config.xml's customSnippet="true". SQX stamps it on every
    # indicator the user has imported or coded AND registered into their catalog — on EVERY
    # install, with ZERO dependency on the .java source still being present on disk. We union
    # that with anything that arrived from a non-config source (their exported blocks, their
    # .java snippets, the registry). This is why a registered custom indicator is NEVER again
    # mis-counted as anonymous "native": its customSnippet flag gives it away in config alone.
    def _is_user_custom(k: str, e: dict) -> bool:
        if (e.get("attrib") or {}).get("customSnippet") == "true":
            return True
        if e.get("source") in ("export", "snippet", "registry"):
            return True
        return k in snippet_atoms
    user_custom_keys = sorted(k for k, e in atoms.items() if _is_user_custom(k, e))
    for k in user_custom_keys:
        atoms[k]["user_custom"] = True
    # the .java-confirmed subset (contract read straight from source = highest fidelity)
    user_coded_keys = sorted(k for k in snippet_atoms if k in atoms)
    for k in user_coded_keys:
        atoms[k]["user_coded"] = True
    # split the config harvest into TRUE built-ins vs the user's customs already in config
    config_custom_keys = sorted(
        k for k, e in config_atoms.items()
        if (e.get("attrib") or {}).get("customSnippet") == "true")
    config_native_count = len(config_atoms) - len(config_custom_keys)

    # The install this catalog was built FROM. doctor.py reads the top-level
    # "install" key for its which-install / stale-catalog check (audit P0-2) —
    # writing only meta.config_path made that check a silent no-op. Derive the
    # root from config.xml's fixed sub-path when the caller didn't pass it.
    if install_root is None:
        try:
            guess = config_path.resolve().parents[5]   # …/internal/web/SQWIZARD/branding/global/config.xml
            if (guess / "internal").is_dir() and (guess / "user").is_dir():
                install_root = guess
        except IndexError:
            pass

    catalog: dict = {}
    if install_root:
        catalog["install"] = str(install_root)
    catalog.update({
        "meta": {
            "skill": "sqx-custom-block",     # which flavour of catalog.json this is
            "config_path": str(config_path),
            "export_path": str(export_path) if export_path else None,
            "user_ind_path": str(user_ind_path) if user_ind_path else None,
            "snippets_dir": str(snippets_dir) if snippets_dir else None,
            "native_count": config_native_count,            # TRUE built-ins (customSnippet!=true)
            "config_custom_count": len(config_custom_keys),  # user customs already in config
            "export_count": len(export_added),               # proven, from exported blocks
            "snippet_count": len(snippet_added),             # coded, from .java not yet in config
            "snippet_matched": len(snippet_atoms),
            "snippet_java_files": snippet_java_files,
            "user_coded_count": len(user_coded_keys),
            "registry_count": len(registry_added),
            "user_custom_count": len(user_custom_keys),      # ALL of the user's own indicators
            "total": len(atoms),
        },
        "user_custom_keys": user_custom_keys,
        "config_custom_keys": config_custom_keys,
        "export_keys": sorted(export_added),
        "snippet_keys": sorted(snippet_added),
        "user_coded_keys": user_coded_keys,
        "registry_keys": sorted(registry_added),
        "atoms": atoms,
    })
    return catalog


def write_catalog(catalog: dict, out_dir: Path) -> tuple[Path, Path]:
    out_json = out_dir / "catalog.json"
    out_md = out_dir / "catalog.md"
    out_json.write_text(json.dumps(catalog, indent=1, ensure_ascii=False), encoding="utf-8")
    out_md.write_text(_render_md(catalog), encoding="utf-8")
    return out_json, out_md


def _render_md(catalog: dict) -> str:
    m = catalog["meta"]
    atoms = catalog["atoms"]
    lines = [
        "# Atom catalog — discovered from this install",
        "",
        f"- config.xml: `{m['config_path']}`",
        f"- export: `{m['export_path']}`" if m["export_path"] else "- export: (none provided)",
        f"- registry: `{m.get('user_ind_path')}`" if m.get("user_ind_path") else "- registry: (none found)",
        f"- snippets: `{m.get('snippets_dir')}`" if m.get("snippets_dir") else "- snippets: (none found)",
        f"- **{m['native_count']} native built-ins** + **{m.get('user_custom_count', 0)} YOUR custom "
        f"indicators** ({m.get('config_custom_count', 0)} registered in config, "
        f"{m.get('export_count', 0)} from exports, {m.get('snippet_count', 0)} from .java, "
        f"{m.get('registry_count', 0)} synthesized) = **{m['total']} total**",
        "",
        "`bindable` = period/double params you can attach to an outer optimizer knob.",
        "`mid` = midline for oscillators (the level a signal is measured against).",
        "`⚠` = talib_* — UNUSABLE in single-symbol/FX builds (Stockpicker NPE); portfolio-only.",
        "`◆` = multi-output — needs a #Line# pick (emit handles it; choose the output).",
        "`✦` = your coded custom indicator (parsed from its Java snippet) — contract is read "
        "straight from @BuildingBlock/@Parameter/@Output; VERIFY on first import (seed via one "
        "block + export to promote to proven).",
        "`✎` = synthesized from UserCustomIndicators.xml — best-effort schema, VERIFY on first import "
        "(or seed it: use it in one block, export, re-bootstrap → becomes proven).",
        "",
    ]
    # prominent, unmissable section: the indicators the USER coded (their own custom indicators)
    uc = catalog.get("user_custom_keys", [])
    if uc:
        lines.append(f"## ⭐ YOUR custom indicators ({len(uc)})")
        lines.append("")
        lines.append("Indicators that are **yours** — imported or coded by you, identified by the "
                     "`customSnippet` marker in your config plus any exported blocks / .java snippets / "
                     "registry entries. Build blocks from any of these exactly like the native ones. "
                     "`source` shows where each was read from.")
        lines.append("")
        lines.append("| key | display | returnType | mid | source |")
        lines.append("|---|---|---|---|---|")
        for k in uc:
            e = atoms.get(k, {})
            disp = (e.get("display", "") or "").replace("|", "\\|")
            mid = e.get("middleValue") or ("osc" if e.get("isOscillator") == "true" else "")
            lines.append(f"| `{k}` | `{disp}` | {e.get('returnType','')} | {mid} | {e.get('source','')} |")
        lines.append("")

    # group by source then categoryType
    by_group: dict[str, list[dict]] = {}
    for e in atoms.values():
        g = f"{e['source']} / {e['categoryType']}"
        by_group.setdefault(g, []).append(e)
    for g in sorted(by_group):
        items = sorted(by_group[g], key=lambda e: e["key"])
        lines.append(f"## {g}  ({len(items)})")
        lines.append("")
        lines.append("| key | display | returnType | mid | bindable | flags |")
        lines.append("|---|---|---|---|---|---|")
        for e in items:
            flags = ""
            if not e["usable_single_symbol"]:
                flags += "⚠"
            if e["multi_output"]:
                flags += "◆"
            if e.get("user_custom") or e.get("user_coded") or e.get("confidence") == "snippet":
                flags += "✦"
            if e.get("confidence") == "synthesized":
                flags += "✎"
            mid = e["middleValue"] or ("osc" if e["isOscillator"] == "true" else "")
            disp = (e["display"] or "").replace("|", "\\|")
            bindable = ", ".join(e["bindable"]) or "—"
            lines.append(
                f"| `{e['key']}` | `{disp}` | {e['returnType']} | {mid} | {bindable} | {flags} |"
            )
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    try:                                    # never crash on a non-UTF-8 console codepage
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Derive a custom-block atom catalog from a user's install.")
    ap.add_argument("config", nargs="?", help="path to config.xml (or use --install / --auto)")
    ap.add_argument("--install", help="SQX install root — derives config + UserCustomIndicators + customBlocks")
    ap.add_argument("--auto", action="store_true", help="auto-discover the SQX install on this machine")
    ap.add_argument("--export", help="override path to customBlocksExport.xml")
    ap.add_argument("--user-indicators", help="override path to UserCustomIndicators.xml")
    ap.add_argument("--snippets", help="override path to the coded custom-indicator snippets dir "
                                       "(user/extend/Snippets/SQ/Blocks/Indicators)")
    # Defaults to the SKILL folder, not the cwd: Claude Code runs commands from the
    # user's project directory, and a "." default dropped a ~500 KB catalog.json into
    # whatever repo they happened to be in.
    ap.add_argument("--out-dir", default=str(SKILL_DIR),
                    help="where to write catalog.json / catalog.md (default: the skill folder)")
    args = ap.parse_args(argv)

    config_path = export_path = user_ind_path = snippets_dir = None
    install_root = None

    if not (args.auto or args.install or args.config):
        shared = load_shared_install()
        if shared:
            print(f"using stored SQX install ({install_file()}): {shared}")
            args.install = shared

    if args.auto or args.install:
        if args.install:
            check = validate_install(args.install)
            if not check["is_sqx"]:
                print(install_error(check, rerun='python engine/bootstrap.py '
                                                 '--install "<your SQX install folder>"'))
                return 1
            info = resolve_install(Path(args.install))
        else:
            real = [i for i in find_installs() if i["is_sqx_install"]]
            if not real:
                print("FAIL: no SQX install auto-discovered. Ask the user for their folder, then:")
                print("  python engine/bootstrap.py --install <folder>")
                return 1
            if len(real) > 1:
                print("Multiple SQX installs found — pick one with --install:")
                for i in real:
                    print(f'  python engine/bootstrap.py --install "{i["root"]}"')
                return 1
            info = real[0]
            print(f"discovered SQX install: {info['root']}")
        install_root = info["root"]
        config_path = Path(info["config"])
        export_path = Path(info["export"]) if info["export"] else None
        user_ind_path = Path(info["user_indicators"]) if info["user_indicators"] else None
        snippets_dir = Path(info["snippets"]) if info.get("snippets") else None
    elif args.config:
        config_path = Path(args.config)
    else:
        # First contact for a brand-new user: give the fix, not an argparse usage dump.
        print("No StrategyQuant X install is set up yet.\n")
        print("  Easiest:  run  /sqx-setup   (points all four sqx-lab skills at your install)")
        print("  Or here:  python engine/bootstrap.py --install \"<your SQX folder>\"\n")
        print("The folder wanted is the TOP-LEVEL StrategyQuant X folder — the one containing")
        print("internal\\ and user\\ (e.g. C:\\StrategyQuantX144).")
        print("\n  python engine/discover.py     will suggest installs found on this machine.")
        return 2

    if args.export:                          # explicit overrides win
        export_path = Path(args.export)
    if args.user_indicators:
        user_ind_path = Path(args.user_indicators)
    if args.snippets:
        snippets_dir = Path(args.snippets)

    if not config_path.exists():
        print(f"FAIL: config.xml not found: {config_path}")
        return 1
    if export_path and not export_path.exists():
        print(f"  note: no export at {export_path} — skipping proven user-custom atoms")
        export_path = None
    if user_ind_path and not user_ind_path.exists():
        user_ind_path = None
    if snippets_dir and not snippets_dir.is_dir():
        snippets_dir = None

    catalog = build_catalog(config_path, export_path, user_ind_path, snippets_dir,
                            install_root=install_root)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    j, md = write_catalog(catalog, out_dir)
    m = catalog["meta"]
    print(f"OK  {m['native_count']} native built-ins + {m.get('user_custom_count', 0)} YOUR custom "
          f"+ {m.get('registry_count', 0)} synthesized = {m['total']} atoms")
    # Surface the user's OWN custom indicators BY NAME — identified primarily from config.xml's
    # customSnippet marker (+ exports / .java snippets / registry). This NEVER shows a misleading
    # "0" when the customs are sitting in config but the .java source isn't present on this machine.
    uc = catalog.get("user_custom_keys", [])
    if uc:
        print(f"    YOUR custom indicators: {m.get('user_custom_count', 0)} found "
              f"({m.get('config_custom_count', 0)} registered in your config, "
              f"{m.get('export_count', 0)} from exported blocks, "
              f"{m.get('snippet_count', 0)} from .java source, "
              f"{m.get('registry_count', 0)} synthesized):")
        for i in range(0, len(uc), 8):           # wrap the name list for readability
            print("      " + ", ".join(uc[i:i + 8]))
    else:
        print("    YOUR custom indicators: 0 found — no indicator in your config carries the "
              "customSnippet marker, and no exported blocks / .java snippets / registry customs were "
              "found. (A fresh install with no imported indicators looks exactly like this.)")
    njava = m.get("snippet_java_files", 0)        # secondary .java note, only if it adds info
    if snippets_dir and njava and not m.get("snippet_matched"):
        print(f"    (note: scanned {njava} .java under {snippets_dir} but parsed 0 as value indicators — "
              f"likely all ConditionBlock signal files, which is normal.)")
    print(f"    {j}")
    print(f"    {md}")
    talib = [k for k, e in catalog["atoms"].items() if not e["usable_single_symbol"]]
    if talib:
        print(f"    note: {len(talib)} talib_* atoms flagged UNUSABLE in single-symbol builds")
    if install_root and not save_shared_install(install_root):
        print(f"    note: could not store the install path in {install_file()}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
