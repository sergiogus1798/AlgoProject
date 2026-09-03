"""run_evals.py — deterministic regression + guardrail harness for sqx-random-group.

The AlgoWizard import is the real oracle (human); this harness grades everything up to it
— the deterministic layer the engine controls. It is the regression net for the group
engine + validator, and executable documentation of the load-bearing rules (flat items,
the 3-state optimizer model, hybrid re-export shape, the Condition/Value type contract).

For each case it drives the REAL engine (engine/groups.py) and the skill's own
`validate.py`, then checks objective expectations:

  A. Canonical example regenerates + validates; a real AlgoWizard export still validates
  B. Engine invariants hold: the 3-state optimizer model emits correctly, a hybrid item
     re-exports a block by reference (categoryType="Custom blocks", no <Contents>),
     make_group rejects a bad type
  C. Validator catches bad output it must catch: a Condition group holding a Value item,
     a compound (AND/OR) item, a non-<RandomGroups> root
  D. Tier-1 audit-fix repro cases (evals/test_tier1.py): wrong-flavour catalog refusal,
     catalog provenance keys, loud optimize errors + int knobs + number(optimize=),
     empty file/group/operand FAILs, dead-hybrid-pool FAIL against the LIVE install,
     and the real-export false-positive sweep over blockGroups-backups

Install-agnostic: keys are discovered from catalog.json (462 rules / 198 values / 711
blocks here), not hardcoded. The golden-export check is lab-only and skips if absent;
so do the live-install cases in D when no shared install is stored.

Usage:
  python evals/run_evals.py                 # uses <skill>/catalog.json
  python evals/run_evals.py --catalog PATH [--golden PATH]
Exit 0 = every case passed; 1 = a regression.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from engine.groups import (  # noqa: E402
    load_catalog, inline_item, hybrid_ref, make_group, wrap_groups, number,
)

PY = sys.executable
ENGINE = SKILL_ROOT / "engine"
EXAMPLES = SKILL_ROOT / "examples"
# repo lab fixture (not shipped in the skill); skipped gracefully if absent
DEFAULT_GOLDEN = SKILL_ROOT.parent.parent / "strategyquant_144" / "blockGroups_144_export.xml"


def _run(args: list[str]) -> tuple[int, str]:
    env = dict(os.environ, PYTHONUTF8="1")
    p = subprocess.run(args, cwd=str(SKILL_ROOT), env=env,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def validate(xml: Path, catalog: Path) -> tuple[int, str]:
    return _run([PY, str(ENGINE / "validate.py"), str(xml), "--catalog", str(catalog)])


class Result:
    def __init__(self, name, group):
        self.name, self.group, self.ok, self.checks = name, group, True, []

    def check(self, cond, label):
        self.checks.append((bool(cond), label))
        if not cond:
            self.ok = False
        return cond


def _find_knobbed_template(T: dict) -> tuple[str, str] | None:
    """First template (prefer value atoms) with a period/double knob — for the 3-state test."""
    for key, el in T.items():
        for p in el.iter("Param"):
            if (p.get("paramType") == "period" or p.get("type") == "double") \
                    and p.get("controlType") != "combo" and p.get("key"):
                return key, p.get("key")
    return None


def _param_attrs(item_xml: str, param_key: str) -> dict | None:
    el = ET.fromstring(item_xml)
    for p in el.iter("Param"):
        if p.get("key") == param_key:
            return p.attrib
    return None


def run_cases(catalog_path: Path, golden: Path, tmp: Path) -> list[Result]:
    results: list[Result] = []
    _, T, B = load_catalog(catalog_path)

    # ---- A1: canonical example set regenerates + validates ----------------------------
    r = Result("group_example_set", "A·regression")
    out = tmp / "grp_example.xml"
    rc, _ = _run([PY, str(EXAMPLES / "gen_group_example.py"), str(catalog_path), str(out)])
    if r.check(rc == 0 and out.exists(), "gen_group_example.py runs"):
        vrc, _ = validate(out, catalog_path)
        r.check(vrc == 0, "validate.py exit 0")
        root = ET.parse(out).getroot()
        groups = root.findall("Group")
        r.check(len(groups) >= 1, f"{len(groups)} group(s) emitted")
        r.check(all(g.get("type") in ("Condition", "Value") for g in groups),
                "every group typed Condition/Value")
    results.append(r)

    # ---- A2: a real AlgoWizard export still validates (lab-only; skip if absent) -------
    r = Result("real_export_validates", "A·regression")
    if not golden.exists():
        r.check(True, f"golden export not present ({golden.name}) — skipped (lab-only)")
    else:
        vrc, vlog = validate(golden, catalog_path)
        r.check(vrc == 0, f"validator accepts the real 144 export (exit {vrc})")
    results.append(r)

    # ---- B1: 3-state optimizer model emits correctly ----------------------------------
    r = Result("optimizer_3state", "B·guardrail")
    found = _find_knobbed_template(T)
    if found is None:
        r.check(False, "no knobbed template discovered")
    else:
        tkey, knob = found
        frozen = inline_item(T[tkey])
        default = inline_item(T[tkey], optimize={knob: "default"})
        override = inline_item(T[tkey], optimize={knob: "50:200:10"})
        fa = _param_attrs(frozen, knob) or {}
        da = _param_attrs(default, knob) or {}
        oa = _param_attrs(override, knob) or {}
        r.check(fa.get("generate") != "random", f"frozen: {tkey}.{knob} has no generate=random")
        r.check(da.get("generate") == "random" and da.get("randomValue") == "default",
                "default: generate=random randomValue=default")
        r.check(oa.get("randomValue") == "50:200:10", "override: randomValue=50:200:10")
    results.append(r)

    # ---- B2: hybrid re-export shape ---------------------------------------------------
    r = Result("hybrid_reexport_shape", "B·guardrail")
    if not B:
        r.check(False, "no blocks in catalog to re-export")
    else:
        bkey = next(iter(B))
        item_xml = hybrid_ref(B[bkey])
        el = ET.fromstring(item_xml)
        r.check(el.get("key") == bkey, f"item key == {bkey}")
        r.check(el.get("categoryType") == "Custom blocks", 'categoryType="Custom blocks"')
        r.check(el.find("Contents") is None, "no <Contents> (rule body re-resolved on import)")
        r.check(len(el.findall("Param")) >= 1, "top-level params copied verbatim")
    results.append(r)

    # ---- B3: make_group rejects a bad type --------------------------------------------
    r = Result("make_group_type_guard", "B·guardrail")
    try:
        make_group("Bad", "Signal", [number("1")])
        r.check(False, "expected ValueError for type='Signal'")
    except ValueError:
        r.check(True, "make_group refuses a non-{Condition,Value} type")
    except Exception as e:
        r.check(False, f"wrong error {type(e).__name__}")
    results.append(r)

    # ---- C1: validator catches a type mismatch (Value item in a Condition group) ------
    r = Result("validator_catches_type_mismatch", "C·validator")
    bad = make_group("BadType", "Condition", [number("30")])  # number is returnType "number"
    xml = tmp / "badtype.xml"
    xml.write_text(wrap_groups([bad]), encoding="utf-8")
    vrc, vlog = validate(xml, catalog_path)
    r.check(vrc == 1 and "boolean" in vlog.lower(),
            "validate.py rejects a Value item in a Condition group")
    results.append(r)

    # ---- C2: validator catches a compound (AND/OR) item -------------------------------
    r = Result("validator_catches_compound_item", "C·validator")
    compound_item = (
        '<Item customSnippet="false" key="CompoundWrapper" name="x" display="x"'
        ' returnType="boolean" categoryType="operators">'
        '<Block key="#Left#" name="Left" type="value" controlType="value">'
        '<Item key="AND" name="AND" display="AND" returnType="boolean"'
        ' categoryType="operators"></Item>'
        '</Block></Item>')
    bad = make_group("Compound", "Condition", [compound_item])
    xml = tmp / "compound.xml"
    xml.write_text(wrap_groups([bad]), encoding="utf-8")
    vrc, vlog = validate(xml, catalog_path)
    r.check(vrc == 1 and "[6/8]" in vlog, "validate.py rejects an AND/OR compound item")
    results.append(r)

    # ---- C3: validator rejects a non-RandomGroups root --------------------------------
    r = Result("validator_rejects_wrong_root", "C·validator")
    xml = tmp / "wrongroot.xml"
    xml.write_text("<CustomBlocks></CustomBlocks>", encoding="utf-8")
    vrc, vlog = validate(xml, catalog_path)
    r.check(vrc == 1 and "randomgroups" in vlog.lower(), "validate.py rejects a non-<RandomGroups> root")
    results.append(r)

    # ---- D: Tier-1 audit-fix repro cases (AUDIT.md P0-1 / P0-3 / P0-13 + P1) ----------
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from test_tier1 import run_tier1_cases  # noqa: E402
    results += run_tier1_cases(Result, catalog_path, tmp)

    return results


def main(argv) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--catalog", default=str(SKILL_ROOT / "catalog.json"))
    ap.add_argument("--golden", default=str(DEFAULT_GOLDEN), help="real export to re-validate (lab-only)")
    ap.add_argument("--report", default=str(SKILL_ROOT / "evals" / "eval_report.json"))
    args = ap.parse_args(argv)

    catalog_path = Path(args.catalog)
    if not catalog_path.exists():
        print(f"FAIL: catalog not found: {catalog_path}\n"
              f"Bootstrap one first: python engine/bootstrap.py --install \"<SQX folder>\"")
        return 1

    with tempfile.TemporaryDirectory(prefix="sqxrg_evals_") as td:
        results = run_cases(catalog_path, Path(args.golden), Path(td))

    passed = sum(1 for r in results if r.ok)
    total = len(results)
    print(f"sqx-random-group — deterministic eval harness ({total} cases)\n" + "=" * 70)
    for r in results:
        print(f"\n[{'PASS' if r.ok else 'FAIL'}] {r.group:<14} {r.name}")
        for ok, label in r.checks:
            print(f"     {'ok ' if ok else 'XX '} {label}")
    print("\n" + "=" * 70)
    print(f"{passed}/{total} cases passed" + ("" if passed == total else f"  —  {total - passed} FAILED"))

    report = {"skill": "sqx-random-group", "catalog": str(catalog_path),
              "passed": passed, "total": total,
              "cases": [{"name": r.name, "group": r.group, "ok": r.ok,
                         "checks": [{"ok": ok, "label": lbl} for ok, lbl in r.checks]}
                        for r in results]}
    Path(args.report).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"report: {args.report}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
