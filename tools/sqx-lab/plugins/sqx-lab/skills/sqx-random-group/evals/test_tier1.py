"""test_tier1.py — Tier-1 audit-fix repro cases for sqx-random-group (AUDIT.md
P0-1, P0-3, P0-13 + the random-group P1 block). Invoked from run_evals.py.

What each case pins down:
  D1  load_catalog refuses a wrong-flavour catalog.json (the sqx-custom-block one
      carries "atoms", not rules/values/blocks) with an actionable SystemExit  [P0-1]
  D2  bootstrap stamps provenance: meta.skill + top-level "install" (what doctor.py
      reads for its stale-catalog check)                                       [P0-1]
  D3  a misspelled optimize= key raises ValueError listing the item's REAL
      param keys (inline_item AND hybrid_ref)                                  [P0-13]
  D4  int knobs are optimizable (BarHourIsBigger #Hour#); data / combo / shift
      params are refused loudly, never silently dropped                        [P0-13]
  D5  number(optimize="lo:hi:step") emits generate="random" on #Number# with
      defaultValue="0" and the value kept in the element text                  [P0-13]
  D6  an empty file (0 groups) FAILS validation                                [P1]
  D7  an empty group (0 items) FAILS validation                                [P1]
  D8  an operator item with a missing / keyless operand FAILS validation       [P1]
  D9  a hybrid ref to a block missing from the LIVE install FAILS; a ref to a
      real live block still passes                                             [P0-3]
  D10 false-positive sweep — the newest non-empty <RandomGroups> AlgoWizard
      export from the install's blockGroups-backups: structure is ground truth
      (no structural FAILs); refs to since-deleted blocks are TRUE positives
      (exact-set match against live customBlocks.xml); against a catalog
      snapshot of its own block set it fully PASSES                            [P0-3]
  D11 the stale shipped example BreakoutTriggersLong_Smoke.xml PASSES against
      its own catalog snapshot (with its frozen #Int2# knobs now reported) and
      FAILS against the live re-seeded install — correct new behavior          [P0-3/P0-13]

Live-install cases resolve the install via sqx_common.load_shared_install() and
skip gracefully (A2-style) when this machine has none. Catalog-snapshot cases
force catalog mode by pointing SQX_LAB_HOME at an empty dir so the subprocess
sees no stored install.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_ROOT = SKILL_ROOT.parent.parent
ENGINE = SKILL_ROOT / "engine"
PY = sys.executable

sys.path.insert(0, str(SKILL_ROOT))
sys.path.insert(0, str(PLUGIN_ROOT))

from engine.groups import (  # noqa: E402
    load_catalog, load_blocks, inline_item, hybrid_ref, make_group, wrap_groups, number,
)

try:  # live-install resolution is optional — cases depending on it skip without it
    from sqx_common import load_shared_install, validate_install  # noqa: E402
except ImportError:  # pragma: no cover
    load_shared_install = validate_install = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _validate(xml: Path, catalog: Path | None = None, install: str | None = None,
              hermetic_home: Path | None = None) -> tuple[int, str]:
    """Run engine/validate.py. hermetic_home forces catalog mode: SQX_LAB_HOME is
    pointed at an empty dir so the subprocess resolves NO stored install."""
    args = [PY, str(ENGINE / "validate.py"), str(xml)]
    if catalog:
        args += ["--catalog", str(catalog)]
    if install:
        args += ["--install", str(install)]
    env = dict(os.environ, PYTHONUTF8="1")
    if hermetic_home is not None:
        hermetic_home.mkdir(parents=True, exist_ok=True)
        env["SQX_LAB_HOME"] = str(hermetic_home)
    p = subprocess.run(args, cwd=str(SKILL_ROOT), env=env, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def _live_install() -> dict | None:
    """The stored SQX install, iff it is usable for live block resolution."""
    if load_shared_install is None:
        return None
    root = load_shared_install()
    if not root:
        return None
    info = validate_install(root)
    if not (info.get("is_sqx") and info["resolved"].get("custom_blocks")):
        return None
    return info


def _live_block_keys(info: dict) -> set[str]:
    root = ET.parse(info["resolved"]["custom_blocks"]).getroot()
    return {it.get("key") for it in root.findall("Item") if it.get("key")}


def _cblock_refs(root: ET.Element) -> set[str]:
    """Every CBlock_* item key referenced anywhere in a <RandomGroups> tree."""
    out = set()
    for it in root.iter("Item"):
        k = it.get("key") or ""
        if k.startswith("CBlock_") or (k and it.get("categoryType") == "Custom blocks"):
            out.add(k)
    return out


def _snapshot_catalog(xml_path: Path, out_path: Path) -> Path:
    """A minimal random-group catalog whose blocks are the hybrid items of the given
    set — a contemporaneous snapshot (hybrid items re-export blocks verbatim)."""
    root = ET.parse(xml_path).getroot()
    blocks = {}
    for it in root.iter("Item"):
        k = it.get("key") or ""
        if k.startswith("CBlock_") or (k and it.get("categoryType") == "Custom blocks"):
            blocks.setdefault(k, ET.tostring(it, encoding="unicode"))
    out_path.write_text(json.dumps({
        "install": None,
        "meta": {"skill": "sqx-random-group",
                 "note": f"snapshot derived from {xml_path.name} (eval fixture)"},
        "rules": {}, "values": {}, "blocks": blocks}), encoding="utf-8")
    return out_path


def _newest_randomgroups_export(backups: Path) -> Path | None:
    """Newest backup that is <RandomGroups>-rooted AND holds at least one group.
    (The 16-byte `<RandomGroups />` snapshots are excluded by construction: a
    0-group file is exactly what the empty-file FAIL check must reject.)"""
    cands = sorted(backups.glob("*.xml"), key=lambda p: p.stat().st_mtime, reverse=True)
    for p in cands:
        try:
            root = ET.parse(p).getroot()
        except ET.ParseError:
            continue
        if root.tag == "RandomGroups" and root.findall("Group"):
            return p
    return None


def _param_attrs(item_xml: str, key: str) -> dict:
    for p in ET.fromstring(item_xml).iter("Param"):
        if p.get("key") == key:
            return dict(p.attrib)
    return {}


def _raises(fn, exc) -> BaseException | None:
    try:
        fn()
        return None
    except exc as e:  # noqa: PERF203
        return e
    except BaseException as e:
        return e  # wrong type — caller inspects


_STRUCTURAL_FAIL = re.compile(r"FAIL \[[2-7]/8\]")


# ---------------------------------------------------------------------------
# cases
# ---------------------------------------------------------------------------

def run_tier1_cases(result_cls, catalog_path: Path, tmp: Path) -> list:
    R = result_cls
    results = []
    _, T, B = load_catalog(catalog_path)
    live = _live_install()
    nohome = tmp / "nohome"           # empty SQX_LAB_HOME -> forces catalog mode

    # ---- D1: wrong-flavour catalog refused loudly (P0-1) --------------------------
    r = R("wrong_catalog_schema_guard", "D·tier1")
    fake = tmp / "customblock_flavour_catalog.json"
    fake.write_text(json.dumps({
        "meta": {"skill": "sqx-custom-block", "install": "X:\\nowhere"},
        "user_custom_keys": [], "config_custom_keys": [], "export_keys": [],
        "snippet_keys": [], "user_coded_keys": [], "registry_keys": [],
        "atoms": {"CCI": "<Item key='CCI'/>"}}), encoding="utf-8")
    e = _raises(lambda: load_catalog(fake), SystemExit)
    if r.check(isinstance(e, SystemExit), "load_catalog raises SystemExit on the sqx-custom-block flavour"):
        msg = str(e)
        r.check(fake.name in msg, "error names the offending file")
        r.check("atoms" in msg or "sqx-custom-block" in msg,
                "error says it looks like the sqx-custom-block catalog")
        r.check("bootstrap.py" in msg, "error gives the rebuild command (python engine/bootstrap.py)")
    meta_ok, T_ok, B_ok = load_catalog(catalog_path)
    r.check(bool(T_ok) and bool(B_ok), "the real random-group catalog still loads")
    results.append(r)

    # ---- D2: bootstrap provenance for doctor's stale-catalog check (P0-1) ----------
    r = R("catalog_provenance_keys", "D·tier1")
    data = json.loads(catalog_path.read_text(encoding="utf-8"))
    r.check("install" in data, 'catalog has a top-level "install" key (doctor.py reads it)')
    r.check((data.get("meta") or {}).get("skill") == "sqx-random-group",
            'meta.skill == "sqx-random-group"')
    stored = load_shared_install() if load_shared_install else None
    if stored and data.get("install"):
        same = os.path.normcase(str(data["install"]).rstrip("\\/")) == \
            os.path.normcase(stored.rstrip("\\/"))
        r.check(same, "catalog install matches the stored shared install")
    else:
        r.check(True, "install match skipped (no stored install to compare)")
    results.append(r)

    # ---- D3: misspelled optimize key raises, listing real keys (P0-13) -------------
    r = R("optimize_unknown_key_raises", "D·tier1")
    tkey = "EMA" if "EMA" in T else next(iter(T))
    real_keys = [p.get("key") for p in T[tkey].iter("Param") if p.get("key")]
    e = _raises(lambda: inline_item(T[tkey], optimize={"#Perod#": "default"}), ValueError)
    if r.check(isinstance(e, ValueError), f"inline_item({tkey}, optimize=#Perod#) raises ValueError"):
        r.check("#Perod#" in str(e), "error names the misspelled key")
        r.check(any(k in str(e) for k in real_keys), "error lists the item's ACTUAL param keys")
    if B:
        bkey = next(iter(B))
        bkeys = [p.get("key") for p in B[bkey].findall("Param") if p.get("key")]
        e2 = _raises(lambda: hybrid_ref(B[bkey], optimize={"#Nope#": "1:2:1"}), ValueError)
        if r.check(isinstance(e2, ValueError), f"hybrid_ref({bkey}, optimize=#Nope#) raises ValueError"):
            r.check(any(k in str(e2) for k in bkeys), "hybrid error lists the block's actual param keys")
    else:
        r.check(True, "hybrid part skipped (no blocks in catalog)")
    results.append(r)

    # ---- D4: int knobs optimizable; data/combo/shift refused loudly (P0-13) --------
    r = R("optimize_int_knob_and_refusals", "D·tier1")
    if "BarHourIsBigger" not in T:
        r.check(False, "BarHourIsBigger not in catalog (expected on this install)")
    else:
        item = inline_item(T["BarHourIsBigger"], optimize={"#Hour#": "0:23:1"})
        a = _param_attrs(item, "#Hour#")
        r.check(a.get("generate") == "random" and a.get("randomValue") == "0:23:1",
                'int knob #Hour# emits generate="random" randomValue="0:23:1"')
        e = _raises(lambda: inline_item(T["BarHourIsBigger"], optimize={"#Shift#": "0:3:1"}),
                    ValueError)
        r.check(isinstance(e, ValueError), "optimizing the #Shift# param is refused (ValueError)")
        e = _raises(lambda: inline_item(T["BarHourIsBigger"], optimize={"#Chart#": "default"}),
                    ValueError)
        r.check(isinstance(e, ValueError), "optimizing a data/chart param is refused (ValueError)")
    combo = None
    for k, el in T.items():
        for p in el.iter("Param"):
            if p.get("controlType") == "combo" and p.get("key"):
                combo = (k, p.get("key"))
                break
        if combo:
            break
    if combo:
        ck, cp = combo
        e = _raises(lambda: inline_item(T[ck], optimize={cp: "default"}), ValueError)
        r.check(isinstance(e, ValueError), f"optimizing a combo param ({ck}.{cp}) is refused (ValueError)")
    else:
        r.check(True, "combo refusal skipped (no combo param in catalog)")
    results.append(r)

    # ---- D5: number(optimize=) — the constant becomes a real knob (P0-13) ----------
    r = R("number_optimize_range", "D·tier1")
    try:
        opt = number("30", optimize="20:40:1")
        a = _param_attrs(opt, "#Number#")
        r.check(a.get("generate") == "random" and a.get("randomValue") == "20:40:1",
                'number("30", optimize="20:40:1") emits generate="random" randomValue="20:40:1"')
        r.check(a.get("defaultValue") == "0", 'optimized number has defaultValue="0" (matches real exports)')
        txt = next(p.text for p in ET.fromstring(opt).iter("Param") if p.get("key") == "#Number#")
        r.check(txt == "30", "the value stays in the element text")
    except TypeError as e:
        r.check(False, f"number() has no optimize= support ({e})")
    plain = _param_attrs(number("30"), "#Number#")
    r.check(plain.get("defaultValue") == "30" and "generate" not in plain,
            "plain number('30') unchanged (frozen, defaultValue=30)")
    results.append(r)

    # ---- D6: empty file (0 groups) FAILS (P1) --------------------------------------
    r = R("validator_empty_file_fails", "D·tier1")
    xml = tmp / "t1_empty_file.xml"
    xml.write_text(wrap_groups([]), encoding="utf-8")
    rc, log = _validate(xml, catalog=catalog_path)
    r.check(rc == 1, "an empty <RandomGroups> set exits 1")
    r.check("[2/8]" in log, "the empty-set FAIL check fires ([2/8])")
    results.append(r)

    # ---- D7: empty group (0 items) FAILS (P1) --------------------------------------
    r = R("validator_empty_group_fails", "D·tier1")
    xml = tmp / "t1_empty_group.xml"
    xml.write_text(wrap_groups([make_group("EmptyPool", "Condition", [])]), encoding="utf-8")
    rc, log = _validate(xml, catalog=catalog_path)
    r.check(rc == 1, "a group with 0 items exits 1")
    r.check("[3/8]" in log and "EmptyPool" in log, "the empty-group FAIL names the group ([3/8])")
    results.append(r)

    # ---- D8: operator item with a missing / keyless operand FAILS (P1) -------------
    r = R("validator_empty_operand_fails", "D·tier1")
    num = ('<Item customSnippet="false" key="Number" name="(NUM) Number" display="#Number#"'
           ' returnType="number" categoryType="other">'
           '<Param key="#Number#" name="Number" type="double" defaultValue="30">30</Param></Item>')
    missing_operand = (
        '<Item customSnippet="false" key="IsGreater" name="(&gt;) Is greater"'
        ' display="#Left# &gt; #Right#" returnType="boolean" mI="Comparisons"'
        ' categoryType="operators">'
        '<Block key="#Left#" name="Left" type="value" controlType="value"></Block>'
        f'<Block key="#Right#" name="Right" type="value" controlType="value">{num}</Block>'
        '</Item>')
    keyless_operand = (
        '<Item customSnippet="false" key="IsLower" name="(&lt;) Is lower"'
        ' display="#Left# &lt; #Right#" returnType="boolean" mI="Comparisons"'
        ' categoryType="operators">'
        f'<Block key="#Left#" name="Left" type="value" controlType="value">{num}</Block>'
        '<Block key="#Right#" name="Right" type="value" controlType="value">'
        '<Item name="broken" returnType="number"></Item></Block>'
        '</Item>')
    xml = tmp / "t1_empty_operand.xml"
    xml.write_text(wrap_groups([make_group("BadOperands", "Condition",
                                           [missing_operand, keyless_operand])]),
                   encoding="utf-8")
    rc, log = _validate(xml, catalog=catalog_path)
    r.check(rc == 1, "operator items with empty operands exit 1")
    r.check("[7/8]" in log, "the empty-operand FAIL check fires ([7/8])")
    r.check("#Left#" in log and "#Right#" in log,
            "both defects are reported (missing operand AND keyless operand)")
    results.append(r)

    # ---- D9: dead hybrid ref FAILS against the LIVE install; real one passes (P0-3) -
    r = R("dead_pool_fails_against_live_install", "D·tier1")
    if live is None:
        r.check(True, "skipped — no usable live install on this machine")
    else:
        ghost = ('<Item categoryType="Custom blocks" key="CBlock_DoesNotExist" name="ghost"'
                 ' display="ghost" returnType="boolean" type="Condition" strategyType="Standard">'
                 '<Param name="Chart" key="#Chart1#" type="data" paramType="data"'
                 ' controlType="dataVar" defaultValue="0">0</Param></Item>')
        xml = tmp / "t1_dead_pool.xml"
        xml.write_text(wrap_groups([make_group("DeadPool", "Condition", [ghost])]),
                       encoding="utf-8")
        rc, log = _validate(xml, install=live["root"])
        r.check(rc == 1, "a pool holding CBlock_DoesNotExist exits 1 against the live install")
        r.check("CBlock_DoesNotExist" in log and "[8/8]" in log,
                "the dead key is named by the [8/8] FAIL")
        live_blocks = load_blocks(live["resolved"]["custom_blocks"])
        good_key = next(iter(live_blocks))
        xml2 = tmp / "t1_live_pool.xml"
        xml2.write_text(wrap_groups([make_group("LivePool", "Condition",
                                                [hybrid_ref(live_blocks[good_key])])]),
                        encoding="utf-8")
        rc2, log2 = _validate(xml2, install=live["root"])
        r.check(rc2 == 0, f"a pool of the live block {good_key} still passes (no false positive)")
    results.append(r)

    # ---- D10: false-positive sweep over the newest real AlgoWizard export (P0-3) ----
    r = R("real_export_sweep", "D·tier1")
    if live is None:
        r.check(True, "skipped — no usable live install on this machine")
    else:
        backups = Path(live["root"]) / "user" / "settings" / "blockGroups-backups"
        export = _newest_randomgroups_export(backups) if backups.is_dir() else None
        if export is None:
            r.check(True, "skipped — no non-empty <RandomGroups> export in blockGroups-backups")
        else:
            refs = _cblock_refs(ET.parse(export).getroot())
            missing = refs - _live_block_keys(live)
            rc, log = _validate(export, install=live["root"])
            r.check(not _STRUCTURAL_FAIL.search(log),
                    f"{export.name}: no structural FAILs ([2/8]-[7/8]) — real wire format is ground truth")
            if missing:
                r.check(rc == 1 and "FAIL [8/8]" in log,
                        f"{len(missing)}/{len(refs)} refs point at since-deleted blocks -> [8/8] FAIL (true positives)")
                seg = log.split("FAIL [8/8]", 1)[1] if "FAIL [8/8]" in log else ""
                flagged = set(re.findall(r"^\s+(CBlock_[A-Za-z0-9_]+)$", seg, re.M))
                r.check(flagged == missing,
                        "flagged keys == exactly the truly-missing set (no false positives, none missed)")
            else:
                r.check(rc == 0, "every ref resolves against the live install -> full PASS")
            snap = _snapshot_catalog(export, tmp / "t1_export_snapshot.json")
            rc2, log2 = _validate(export, catalog=snap, hermetic_home=nohome)
            r.check(rc2 == 0 and "ALL CHECKS PASSED" in log2,
                    "the same export fully PASSES against its own-era catalog snapshot")
    results.append(r)

    # ---- D11: stale smoke example — snapshot PASS + frozen #Int2#; live FAIL (fix 4) -
    r = R("smoke_example_snapshot_vs_live", "D·tier1")
    smoke = SKILL_ROOT / "examples" / "BreakoutTriggersLong_Smoke.xml"
    if not smoke.exists():
        r.check(False, "examples/BreakoutTriggersLong_Smoke.xml missing")
    else:
        snap = _snapshot_catalog(smoke, tmp / "t1_smoke_snapshot.json")
        rc, log = _validate(smoke, catalog=snap, hermetic_home=nohome)
        r.check(rc == 0, "smoke example PASSES against its own catalog snapshot")
        n_int2 = log.count("#Int2#")
        r.check(n_int2 >= 4, f"widened frozen-knob warning reports its #Int2# knobs ({n_int2} listed)")
        if live is None:
            r.check(True, "live half skipped — no usable live install")
        else:
            smoke_refs = _cblock_refs(ET.parse(smoke).getroot())
            gone = smoke_refs - _live_block_keys(live)
            rc2, log2 = _validate(smoke, install=live["root"])
            if gone:
                r.check(rc2 == 1 and "[8/8]" in log2,
                        f"against the live re-seeded install it FAILS ({len(gone)}/{len(smoke_refs)} "
                        f"keys no longer exist) — correct new behavior")
            else:
                r.check(rc2 == 0, "all smoke keys exist in the live install -> passes")
    results.append(r)

    return results
