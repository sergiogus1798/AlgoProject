"""test_tier1.py — repro cases for the Tier-1 audit fixes (AUDIT.md 2026-07-30).

One case per fix, written to FAIL against the pre-fix engine and pass after:

  T1  esc()/make_block/int_param escape quotes                (P0-10)
  T2  validate.py --catalog hard-fail + fallback + skip note  (P0-11)
  T3  export-harvested Params sanitized on emit               (P0-12)
  T4  Volume/Spread/talib price transforms harvested          (P1 _is_value_atom)
  T5  name-suffix regex catches _2v3 / _2V3                   (P1 NAME_SUFFIX_RE)
  T6  wrong-flavour catalog refused; install/skill tags       (P0-1/P0-2 adjacent)

Not a standalone CLI — invoked by run_evals.py, which passes its Result class in.
T4/T6b need the stored SQX install (sqx_common.load_shared_install()); they read the
install but never write to it. The bootstrap they trigger writes catalog.json /
catalog.md into the SKILL dir only (gitignored).
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_ROOT = SKILL_ROOT.parents[1]
for p in (str(SKILL_ROOT), str(PLUGIN_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

from engine.emit import Catalog                      # noqa: E402
from engine.grammar import (                          # noqa: E402
    esc, make_block, make_price_level, int_param, double_param,
    is_greater, wrap_batch,
)

PY = sys.executable
ENGINE = SKILL_ROOT / "engine"


def _run(args: list[str]) -> tuple[int, str]:
    env = dict(os.environ, PYTHONUTF8="1")
    p = subprocess.run(args, cwd=str(SKILL_ROOT), env=env,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


# --------------------------------------------------------------------- T1: esc quotes
def _case_esc_quotes(Result, cat, tmp: Path):
    r = Result("tier1_esc_quotes", "D·tier1")

    # the audit's unit test: an attribute containing a "b" & c must round-trip
    val = 'a "b" & c'
    try:
        r.check(ET.fromstring(f'<x a="{esc(val)}"/>').get("a") == val,
                'esc(): attribute a "b" & c round-trips through ET.fromstring')
    except ET.ParseError as e:
        r.check(False, f'esc(): attribute a "b" & c fails to parse: {e}')

    name = 'Eval "Q" & Co'
    category = "Mean's \"edge\" & co"
    pname = 'P "q" & r'
    try:
        blk = make_block(
            key="CBlock_EvalEsc", name=name,
            display=esc('shows "quoted" & <angled> text'), category=category,
            help_text=esc("it's > 50% & \"tight\""), opposite="CBlock_null",
            params=int_param("#Int2#", pname, "14", "2", "100"),
            contents=is_greater(cat.number("1"), cat.number("2")))
        el = ET.fromstring(blk)
        r.check(el.get("name") == name, "make_block: quoted name round-trips")
        r.check(el.get("category") == category, "make_block: quoted category round-trips")
        r.check(el.get("display") == 'shows "quoted" & <angled> text',
                "make_block: esc()'d display round-trips (no double-escape)")
        r.check(el.get("help") == "it's > 50% & \"tight\"",
                "make_block: esc()'d help round-trips (no double-escape)")
        ip = next((p for p in el.findall("Param") if p.get("key") == "#Int2#"), None)
        r.check(ip is not None and ip.get("name") == pname,
                "int_param: quoted knob name round-trips")
    except ET.ParseError as e:
        r.check(False, f"make_block with quoted name/category fails to parse: {e}")

    try:
        pl = make_price_level(
            key="CBlock_EvalEscPL", name='Lvl "hi" & lo', display=esc("level"),
            category='Cat "q"', help_text=esc("h"), opposite="CBlock_null",
            params=double_param("#Double3#", 'Mult "x"', "2.5", "0.5", "5", "0.1"),
            contents=cat.number("1"))
        el = ET.fromstring(pl)
        r.check(el.get("name") == 'Lvl "hi" & lo', "make_price_level: quoted name round-trips")
        dp = next((p for p in el.findall("Param") if p.get("key") == "#Double3#"), None)
        r.check(dp is not None and dp.get("name") == 'Mult "x"',
                "double_param: quoted knob name round-trips")
    except ET.ParseError as e:
        r.check(False, f"make_price_level with quoted name/category fails to parse: {e}")
    return r


# ------------------------------------------------- T2: validate.py --catalog handling
def _case_validator_catalog(Result, cat, catalog_path: Path, tmp: Path):
    r = Result("tier1_validator_catalog_hardfail", "D·tier1")

    good = tmp / "t2_good.xml"
    good.write_text(wrap_batch([make_block(
        key="CBlock_EvalT2", name="EvalT2", display=esc("1 > 2"), category="Eval_user",
        help_text=esc("tier1 catalog-handling fixture"), opposite="CBlock_null",
        params="", contents=is_greater(cat.number("1"), cat.number("2")))]),
        encoding="utf-8")

    # (a) bogus --catalog AND no fallback anywhere -> hard fail, paths printed
    import engine.validate as vmod
    bogus = tmp / "nope_catalog.json"
    orig = getattr(vmod, "find_catalog", None)
    vmod.find_catalog = lambda *a, **k: None
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rc = vmod.main([str(good), "--catalog", str(bogus)])
    except SystemExit as e:                     # tolerate exit-style implementations
        rc = int(e.code or 0)
    finally:
        if orig is not None:
            vmod.find_catalog = orig
        else:
            try:
                del vmod.find_catalog
            except AttributeError:
                pass
    out = buf.getvalue()
    r.check(rc == 1, f"unresolvable --catalog exits 1 (got {rc})")
    r.check("nope_catalog.json" in out and "searched" in out.lower(),
            "unresolvable --catalog prints the paths searched")
    r.check("ALL CHECKS PASSED" not in out,
            "unresolvable --catalog never prints ALL CHECKS PASSED")

    # (b) bogus --catalog with a real skill catalog present -> find_catalog fallback,
    #     check 7 still runs (a talib-using batch must FAIL, not silently pass)
    talib_key = next((k for k in sorted(cat.atoms)
                      if not cat.atoms[k].get("usable_single_symbol", True)), None)
    if talib_key is None:
        r.check(True, "no talib atom in this install — fallback sub-check skipped")
    else:
        talib_xml = tmp / "t2_talib.xml"
        talib_xml.write_text(wrap_batch([make_block(
            key="CBlock_EvalT2Talib", name="EvalTTwoTalib",
            display=esc(f"{talib_key} > 0"), category="Eval_user",
            help_text=esc("tier1 talib fixture"), opposite="CBlock_null", params="",
            contents=is_greater(cat.atom(talib_key, allow_talib=True), cat.number("0")))]),
            encoding="utf-8")
        rc, out = _run([PY, str(ENGINE / "validate.py"), str(talib_xml),
                        "--catalog", str(tmp / "does_not_exist.json")])
        r.check(rc == 1 and "talib" in out.lower(),
                f"bogus --catalog falls back to the skill catalog; check 7 still "
                f"catches {talib_key} (rc={rc})")
        r.check("not found" in out.lower(),
                "fallback is announced, not silent")

    # (c) no --catalog at all -> visible note that check 7 was skipped
    rc, out = _run([PY, str(ENGINE / "validate.py"), str(good)])
    r.check(rc == 0, f"clean file without --catalog still exits 0 (got {rc})")
    r.check("SKIPPED" in out and "check 7" in out,
            "missing --catalog prints a visible check-7 SKIPPED note")
    return r


# ------------------------------------------- T3: export-harvested param sanitization
def _synthetic_export_catalog(tmp: Path) -> Path:
    """An atom exactly as bootstrap harvests it from customBlocksExport.xml: Params
    still carrying the OLD block's knob bindings (customParam="true" value="#IntN#")
    and its picked inner texts (shift 2, mode 3)."""
    entry = {
        "key": "EvalExportInd", "name": "(EVEX) Eval Export Indicator",
        "display": "EvalExportInd(@Chart@#Period#)[#Shift#]", "returnType": "number",
        "mI": "EvalExportInd", "categoryType": "indicator", "isOscillator": "",
        "middleValue": "", "indicatorMin": "", "indicatorMax": "", "help": "",
        "attrib": {"customSnippet": "true", "key": "EvalExportInd",
                   "name": "(EVEX) Eval Export Indicator",
                   "display": "EvalExportInd(@Chart@#Period#)[#Shift#]",
                   "returnType": "number", "mI": "EvalExportInd",
                   "categoryType": "indicator", "help": ""},
        "params": [
            {"attrib": {"key": "#Chart#", "name": "Chart", "type": "data",
                        "controlType": "dataVar", "defaultValue": "0",
                        "customParam": "true", "paramType": "data", "value": "#Chart1#"},
             "role": "chart", "text": "#Chart1#"},
            {"attrib": {"key": "#Period#", "name": "Period", "type": "int",
                        "defaultValue": "14", "genMinValue": "-1000003",
                        "genMaxValue": "-1000004", "paramType": "period",
                        "controlType": "jspinnerVar", "minValue": "2", "maxValue": "100",
                        "step": "1", "builderStep": "1",
                        "customParam": "true", "value": "#Int2#"},
             "role": "period", "text": "#Int2#"},
            {"attrib": {"key": "#Mode#", "name": "Mode", "type": "int",
                        "controlType": "combo", "values": "A=1,B=2,C=3",
                        "defaultValue": "1"},
             "role": "combo", "text": "3"},
            {"attrib": {"key": "#Shift#", "name": "Shift", "type": "int",
                        "defaultValue": "1", "controlType": "jspinnerVar",
                        "minValue": "0", "maxValue": "1000", "genMinValue": "-1000001",
                        "genMaxValue": "-1000002", "paramType": "shift",
                        "step": "1", "builderStep": "1"},
             "role": "shift", "text": "2"},
        ],
        "bindable": ["#Period#"], "multi_output": False, "usable_single_symbol": True,
        "source": "export", "confidence": "proven",
    }
    p = tmp / "t3_synth_export_catalog.json"
    p.write_text(json.dumps({"meta": {"skill": "sqx-custom-block", "total": 1},
                             "atoms": {"EvalExportInd": entry}}), encoding="utf-8")
    return p


def _case_export_sanitization(Result, tmp: Path):
    r = Result("tier1_export_param_sanitization", "D·tier1")
    try:
        scat = Catalog(_synthetic_export_catalog(tmp))
        frozen = scat.atom("EvalExportInd")           # no kwargs = fully frozen
        el = ET.fromstring(frozen)
        by_key = {p.get("key"): p for p in el.findall("Param")}

        r.check(re.search(r'value="#(?:Int|Double)\d+#"', frozen) is None,
                'frozen emit carries NO stale value="#IntN#" binding')
        for k in ("#Period#", "#Mode#", "#Shift#"):
            p = by_key[k]
            r.check(p.get("customParam") is None and p.get("value") is None,
                    f"frozen emit: {k} carries no customParam/value")
        r.check(by_key["#Chart#"].get("value") == "#Chart1#",
                "chart param still binds to #Chart1#")
        r.check((by_key["#Shift#"].text or "").strip() == "1",
                f"shift default is defaultValue 1, not harvested 2 "
                f"(got {(by_key['#Shift#'].text or '').strip()!r})")
        r.check((by_key["#Mode#"].text or "").strip() == "1",
                f"combo default is defaultValue 1, not harvested 3 "
                f"(got {(by_key['#Mode#'].text or '').strip()!r})")
        r.check((by_key["#Period#"].text or "").strip() == "14",
                "unbound period freezes at defaultValue 14")

        bound = scat.atom("EvalExportInd", period="#Int5#", shift="3", mode="2")
        el = ET.fromstring(bound)
        by_key = {p.get("key"): p for p in el.findall("Param")}
        p = by_key["#Period#"]
        r.check(p.get("customParam") == "true" and p.get("value") == "#Int5#"
                and (p.text or "").strip() == "#Int5#",
                "binding THIS call re-adds customParam/value (#Int5#)")
        r.check((by_key["#Shift#"].text or "").strip() == "3"
                and (by_key["#Mode#"].text or "").strip() == "2",
                "explicit shift=/mode= kwargs still win")
    except Exception as e:
        r.check(False, f"export-atom emit raised {type(e).__name__}: {e}")
    return r


# ----------------------------------------------------- T4: Volume / "Price" harvest
_EXPECTED_GAIN = {"Volume", "Spread", "SpreadInPips", "talib_AVGPRICE",
                  "talib_MEDPRICE", "talib_TYPPRICE", "talib_WCLPRICE"}
_AUDITED_INSTALL = "SQX_144_2953_win_20260627_M1data_TEST"


def _case_volume_harvest(Result, tmp: Path):
    r = Result("tier1_volume_harvest", "D·tier1")
    from sqx_common import load_shared_install
    import engine.bootstrap as bmod
    from engine.discover import resolve_install

    root = load_shared_install()
    if not root or not Path(root).is_dir():
        r.check(True, "no stored SQX install on this machine — case skipped")
        return r
    info = resolve_install(Path(root))
    if not info["is_sqx_install"]:
        r.check(True, f"stored path is not an SQX install ({root}) — case skipped")
        return r
    cfg = Path(info["config"])
    exp = Path(info["export"]) if info["export"] else None
    ui = Path(info["user_indicators"]) if info["user_indicators"] else None
    sn = Path(info["snippets"]) if info["snippets"] else None

    def _prefix_filter(item):
        """The PRE-fix _is_value_atom (mI tuple without "Price") — the diff baseline."""
        ct = item.get("categoryType")
        if ct in bmod.SKIP_CATEGORY_TYPES or ct is None:
            return False
        if item.get("mI") in bmod.SKIP_MI:
            return False
        if item.get("returnType") not in bmod.VALUE_RETURN_TYPES:
            return False
        if not bmod._params_of(item):
            return False
        if ct in ("indicator", "priceValue", "priceRange"):
            return True
        if ct == "other" and item.get("mI") in ("BarAndTime", "BarRange"):
            return True
        return False

    try:
        new_cat = bmod.build_catalog(cfg, exp, ui, sn)
        orig = bmod._is_value_atom
        bmod._is_value_atom = _prefix_filter
        try:
            old_cat = bmod.build_catalog(cfg, exp, ui, sn)
        finally:
            bmod._is_value_atom = orig
    except Exception as e:
        r.check(False, f"build_catalog raised {type(e).__name__}: {e}")
        return r

    new_keys, old_keys = set(new_cat["atoms"]), set(old_cat["atoms"])
    gained, lost = new_keys - old_keys, old_keys - new_keys
    r.check(gained == _EXPECTED_GAIN,
            f"gained EXACTLY the 7 audited atoms (extra: {sorted(gained - _EXPECTED_GAIN)}, "
            f"missing: {sorted(_EXPECTED_GAIN - gained)})")
    r.check(not lost, f"no previously-harvested atom lost (lost: {sorted(lost)})")
    if Path(root).name == _AUDITED_INSTALL:
        r.check(len(old_keys) == 210 and len(new_keys) == 217,
                f"catalog grows 210 -> 217 on the audited install "
                f"(got {len(old_keys)} -> {len(new_keys)})")
    talib_gained = sorted(k for k in _EXPECTED_GAIN if k.startswith("talib_"))
    r.check(all(not new_cat["atoms"][k]["usable_single_symbol"]
                for k in talib_gained if k in new_cat["atoms"]),
            "the 4 talib price transforms are auto-flagged unusable (single-symbol)")
    r.check(all(new_cat["atoms"][k]["usable_single_symbol"]
                for k in ("Volume", "Spread", "SpreadInPips") if k in new_cat["atoms"]),
            "Volume / Spread / SpreadInPips are usable")
    return r


# ------------------------------------------------------- T5: name-suffix regex _2v3
def _case_name_suffix_regex(Result, cat, catalog_path: Path, tmp: Path):
    r = Result("tier1_name_suffix_regex", "D·tier1")
    import engine.validate as vmod

    for n in ("Break_2v3", "Break_2V3", "RSI_144Native", "Sig_3x"):
        r.check(vmod.NAME_SUFFIX_RE.search(n) is not None, f"regex catches {n}")
    for n in ("Break_Long", "Trend_Filter", "Band_user"):
        r.check(vmod.NAME_SUFFIX_RE.search(n) is None, f"regex spares {n}")

    xml = tmp / "t5_2v3.xml"
    xml.write_text(wrap_batch([make_block(
        key="CBlock_EvalT5", name="EvalBad_2v3", display=esc("bad suffix"),
        category="Eval_user", help_text=esc("tier1 _2v3 fixture"), opposite="CBlock_null",
        params="", contents=is_greater(cat.number("1"), cat.number("2")))]),
        encoding="utf-8")
    rc, out = _run([PY, str(ENGINE / "validate.py"), str(xml),
                    "--catalog", str(catalog_path)])
    r.check(rc == 1 and "name suffix" in out.lower(),
            f"validate.py rejects a _2v3 block name end-to-end (rc={rc})")
    return r


# ----------------------------------- T6: wrong-catalog guard + install/skill tagging
def _case_wrong_catalog_guard(Result, tmp: Path):
    r = Result("tier1_wrong_catalog_guard", "D·tier1")
    from sqx_common import load_shared_install

    # (a) a random-group-flavoured catalog.json must be REFUSED, not read as empty
    rg = tmp / "t6_rg_catalog.json"
    rg.write_text(json.dumps({"meta": {"skill": "sqx-random-group"},
                              "rules": {"CBlock_x": {}}, "values": {}}), encoding="utf-8")
    try:
        Catalog(rg)
        r.check(False, "expected SystemExit for a catalog without 'atoms'")
    except SystemExit as e:
        msg = str(e)
        r.check("t6_rg_catalog.json" in msg, "refusal names the offending file")
        r.check("bootstrap" in msg.lower(), "refusal tells how to rebuild (bootstrap.py)")
    except Exception as e:
        r.check(False, f"wrong error type {type(e).__name__}: {e}")

    # (b) a fresh bootstrap tags the catalog with the install root + owning skill
    root = load_shared_install()
    if not root or not Path(root).is_dir():
        r.check(True, "no stored SQX install on this machine — bootstrap sub-check skipped")
        return r
    rc, out = _run([PY, str(ENGINE / "bootstrap.py")])   # uses the stored install
    if not r.check(rc == 0, f"bootstrap.py (stored install) exits 0 (got {rc})"):
        return r
    data = json.loads((SKILL_ROOT / "catalog.json").read_text(encoding="utf-8"))
    got = data.get("install")
    same = bool(got) and os.path.normcase(os.path.normpath(got)) == \
        os.path.normcase(os.path.normpath(root))
    r.check(same, f"catalog top-level install == stored root (got {got!r})")
    r.check(data.get("meta", {}).get("skill") == "sqx-custom-block",
            f"meta.skill == 'sqx-custom-block' (got {data.get('meta', {}).get('skill')!r})")
    return r


# --------------------------------------------------------------------------- entry
def run_tier1_cases(Result, cat, catalog_path: Path, tmp: Path) -> list:
    return [
        _case_esc_quotes(Result, cat, tmp),
        _case_validator_catalog(Result, cat, catalog_path, tmp),
        _case_export_sanitization(Result, tmp),
        _case_volume_harvest(Result, tmp),
        _case_name_suffix_regex(Result, cat, catalog_path, tmp),
        _case_wrong_catalog_guard(Result, tmp),
    ]
