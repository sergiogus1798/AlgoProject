"""run_evals.py — deterministic regression + guardrail harness for sqx-custom-block.

The AlgoWizard import+Build is the real correctness oracle, and it is HUMAN — outside
Claude's reach. This harness grades everything *up to* that boundary: the deterministic
layer the engine fully controls. It is the regression net that turns "I think the engine
still works" into a graded run, and it doubles as executable documentation of the
load-bearing rules (talib, shift-0, #Line#, name suffixes, undeclared params, phantoms).

For each case it drives the REAL engine (emit/grammar) and the skill's own
`validate.py` / `assess.py`, then checks objective expectations:

  A. Canonical examples regenerate and stay green
       - generated XML parses + passes validate.py (exit 0)
       - assess.py reports zero CRITICAL findings (exit 0 under --strict)
       - content invariants: opposite pairs symmetric, expected atom resolves
  B. Engine guardrails FIRE (refusing unsafe input is a feature, not a bug)
       - talib atom refused (Stockpicker NPE), shift-0 OHLC refused (look-ahead),
         phantom atom refused (catalog discipline), multi-output carries #Line#
  C. Validator catches bad output it is supposed to catch
       - block name ending _<digits><letters>, undeclared #IntN# param
  D. Tier-1 audit regressions (evals/test_tier1.py) — esc() quoting, validator
       --catalog hard-fail/fallback, export-param sanitization, Volume/"Price"
       harvest, _2v3 name-suffix regex, wrong-flavour catalog guard

Install-agnostic: representative atoms are DISCOVERED from catalog.json by capability,
not hardcoded — so the harness runs on any bootstrapped install. (The D-group
Volume-harvest case additionally asserts the audited install's exact 210->217 diff
when that specific install is the stored one.)

Usage:
  python evals/run_evals.py                    # uses <skill>/catalog.json
  python evals/run_evals.py --catalog PATH
Exit 0 = every case passed; 1 = a regression (details + JSON report printed).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from engine.emit import Catalog
from engine.grammar import (  # noqa: E402
    is_greater, make_block, int_param, esc, wrap_batch,
)
from test_tier1 import run_tier1_cases  # noqa: E402

PY = sys.executable
ENGINE = SKILL_ROOT / "engine"
EXAMPLES = SKILL_ROOT / "examples"
ASSESS_CRIT_RE = re.compile(r"\|\s*(\d+)\s+critical")


# --------------------------------------------------------------------------- runners
def _run(args: list[str]) -> tuple[int, str]:
    env = dict(os.environ, PYTHONUTF8="1")
    p = subprocess.run(args, cwd=str(SKILL_ROOT), env=env,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def validate(xml: Path, catalog: Path) -> tuple[int, str]:
    return _run([PY, str(ENGINE / "validate.py"), str(xml), "--catalog", str(catalog)])


def assess(xml: Path, catalog: Path, strict: bool) -> tuple[int, str, int]:
    args = [PY, str(ENGINE / "assess.py"), str(xml), "--catalog", str(catalog)]
    if strict:
        args.append("--strict")
    rc, out = _run(args)
    m = ASSESS_CRIT_RE.search(out)
    crit = int(m.group(1)) if m else (1 if rc != 0 else 0)
    return rc, out, crit


def gen_example(script: Path, catalog: Path, out: Path) -> tuple[int, str]:
    return _run([PY, str(script), str(catalog), str(out)])


# --------------------------------------------------------------------------- discovery
def discover(cat: Catalog) -> dict:
    """Pick representative atoms by capability so cases are install-agnostic."""
    atoms = cat.atoms

    def first(pred, prefer=()):
        for k in prefer:
            if k in atoms and pred(atoms[k]):
                return k
        for k, e in atoms.items():
            try:
                if pred(e):
                    return k
            except Exception:
                pass
        return None

    def has_shift(e):
        return any(p.get("role") == "shift" for p in e.get("params", []))

    return {
        "oscillator": first(
            lambda e: (e.get("isOscillator") == "true" or e.get("middleValue") not in (None, ""))
            and e.get("indicatorMin") not in (None, "") and e.get("indicatorMax") not in (None, ""),
            prefer=("RSI", "CCI")),
        "multi_output": first(lambda e: e.get("multi_output"),
                              prefer=("ADX", "Aroon", "Stochastic")),
        "talib": first(lambda e: not e.get("usable_single_symbol", True)),
        "ohlc_shift": first(
            lambda e: e.get("attrib", {}).get("categoryType") in ("priceValue", "priceRange")
            and has_shift(e),
            prefer=("HighD", "LowD", "BarRange", "TrueRange", "ATR")),
    }


def _safe_level(e: dict) -> str:
    lo, hi = e.get("indicatorMin"), e.get("indicatorMax")
    mid = e.get("middleValue")
    try:
        if mid not in (None, ""):
            return str(int(float(mid)))
        if lo not in (None, "") and hi not in (None, ""):
            return str(int((float(lo) + float(hi)) / 2))
    except (TypeError, ValueError):
        pass
    return "0"


# --------------------------------------------------------------------------- cases
class Result:
    def __init__(self, name, group):
        self.name, self.group = name, group
        self.ok = True
        self.checks: list[tuple[bool, str]] = []

    def check(self, cond: bool, label: str):
        self.checks.append((bool(cond), label))
        if not cond:
            self.ok = False
        return cond


def opposites_symmetric(xml: Path) -> bool:
    root = ET.parse(xml).getroot()
    by = {it.get("key"): it for it in root.findall("Item")}
    for it in root.findall("Item"):
        opp = it.get("oppositeBlockKey")
        if not opp or opp == "CBlock_null":
            continue
        p = by.get(opp)
        if p is None or p.get("oppositeBlockKey") != it.get("key"):
            return False
    return True


def run_cases(cat: Catalog, catalog_path: Path, tmp: Path) -> list[Result]:
    results: list[Result] = []
    picks = discover(cat)

    # ---- A1: RSI / oscillator crossover pair (canonical Condition example) ----------
    r = Result("rsi_pair_example", "A·regression")
    out = tmp / "ex_rsi.xml"
    rc, _ = gen_example(EXAMPLES / "gen_example.py", catalog_path, out)
    if r.check(rc == 0 and out.exists(), "gen_example.py runs"):
        vrc, _ = validate(out, catalog_path)
        r.check(vrc == 0, "validate.py exit 0")
        _, _, crit = assess(out, catalog_path, strict=True)
        r.check(crit == 0, f"assess: 0 CRITICAL (got {crit})")
        r.check(opposites_symmetric(out), "opposite pair symmetric")
    results.append(r)

    # ---- A2: price-level shapes (band / OHLC anchor / trail) ------------------------
    r = Result("pricelevel_example", "A·regression")
    out = tmp / "ex_pl.xml"
    rc, _ = gen_example(EXAMPLES / "gen_pricelevel_example.py", catalog_path, out)
    if r.check(rc == 0 and out.exists(), "gen_pricelevel_example.py runs"):
        vrc, _ = validate(out, catalog_path)
        r.check(vrc == 0, "validate.py exit 0")
        _, _, crit = assess(out, catalog_path, strict=True)
        r.check(crit == 0, f"assess: 0 CRITICAL (got {crit}) — period-open shift0 must be exempt")
        r.check(opposites_symmetric(out), "band pair symmetric")
    results.append(r)

    # ---- B1: engine refuses talib atoms --------------------------------------------
    r = Result("guardrail_refuse_talib", "B·guardrail")
    k = picks["talib"]
    if k is None:
        r.check(True, "no talib atom in this install — skipped")
    else:
        try:
            cat.atom(k)
            r.check(False, f"{k}: expected ValueError without allow_talib")
        except ValueError:
            r.check(True, f"{k}: refused without allow_talib")
        except Exception as e:
            r.check(False, f"{k}: wrong error {type(e).__name__}")
        try:
            cat.atom(k, allow_talib=True)
            r.check(True, f"{k}: allowed with allow_talib=True")
        except Exception as e:
            r.check(False, f"{k}: allow_talib should succeed ({e})")
    results.append(r)

    # ---- B2: engine refuses shift-0 OHLC (look-ahead) ------------------------------
    r = Result("guardrail_refuse_shift0_ohlc", "B·guardrail")
    k = picks["ohlc_shift"]
    if k is None:
        r.check(False, "no OHLC atom with a shift param discovered")
    else:
        try:
            cat.atom(k, shift="0")
            r.check(False, f"{k}: expected ValueError at shift=0")
        except ValueError:
            r.check(True, f"{k}: shift=0 refused")
        except Exception as e:
            r.check(False, f"{k}: wrong error {type(e).__name__}")
        try:
            cat.atom(k, shift="1")
            r.check(True, f"{k}: shift=1 allowed")
        except Exception as e:
            r.check(False, f"{k}: shift=1 should succeed ({e})")
        try:
            cat.atom(k, shift="0", allow_shift0=True)
            r.check(True, f"{k}: shift=0 allowed via allow_shift0")
        except Exception as e:
            r.check(False, f"{k}: allow_shift0 should succeed ({e})")
    results.append(r)

    # ---- B3: engine refuses a phantom atom -----------------------------------------
    r = Result("guardrail_refuse_phantom", "B·guardrail")
    try:
        cat.atom("ZzNotARealIndicator__")
        r.check(False, "expected KeyError for phantom atom")
    except KeyError:
        r.check(True, "phantom atom refused with KeyError")
    except Exception as e:
        r.check(False, f"wrong error {type(e).__name__}")
    results.append(r)

    # ---- B4: multi-output atom carries #Line# and validates ------------------------
    r = Result("multi_output_line_param", "B·guardrail")
    k = picks["multi_output"]
    if k is None:
        r.check(False, "no multi-output atom discovered")
    else:
        lvl = _safe_level(cat.info(k))
        try:
            block = make_block(
                key="CBlock_EvalMultiOut", name="EvalMultiOut",
                display=esc(f"{k} line vs {lvl}"), category="Eval_user",
                help_text=esc("harness multi-output check"), opposite="CBlock_null",
                params=int_param("#Int2#", "Period", "14", "2", "50"),
                contents=is_greater(cat.atom(k, period="#Int2#"), cat.number(lvl)))
            xml = tmp / "mo.xml"
            xml.write_text(wrap_batch([block]), encoding="utf-8")
            r.check('key="#Line#"' in xml.read_text(encoding="utf-8"),
                    f"{k}: emitted block carries #Line# param")
            vrc, _ = validate(xml, catalog_path)
            r.check(vrc == 0, f"validate.py exit 0 (check 7 passes) — got {vrc}")
        except Exception as e:
            r.check(False, f"{k}: build/validate raised {type(e).__name__}: {e}")
    results.append(r)

    # ---- C1: validator catches a bad name suffix -----------------------------------
    r = Result("validator_catches_name_suffix", "C·validator")
    osc = picks["oscillator"]
    lvl = _safe_level(cat.info(osc)) if osc else "50"
    atom_xml = cat.atom(osc) if osc else cat.number("1")
    block = make_block(
        key="CBlock_EvalBadName", name="EvalBadName_144Native",  # illegal _<digits><letters>
        display=esc("bad name suffix"), category="Eval_user",
        help_text=esc("harness name-suffix check"), opposite="CBlock_null",
        params="", contents=is_greater(atom_xml, cat.number(lvl)))
    xml = tmp / "badname.xml"
    xml.write_text(wrap_batch([block]), encoding="utf-8")
    vrc, vlog = validate(xml, catalog_path)
    r.check(vrc == 1 and "name suffix" in vlog.lower(), "validate.py rejects _<digits><letters> name")
    results.append(r)

    # ---- C2: validator catches an undeclared param ---------------------------------
    r = Result("validator_catches_undeclared_param", "C·validator")
    if osc:
        block = make_block(
            key="CBlock_EvalUndeclared", name="EvalUndeclared",
            display=esc("undeclared param"), category="Eval_user",
            help_text=esc("harness undeclared-param check"), opposite="CBlock_null",
            params="",  # deliberately omit int_param("#Int2#", ...)
            contents=is_greater(cat.atom(osc, period="#Int2#"), cat.number(lvl)))
        xml = tmp / "undeclared.xml"
        xml.write_text(wrap_batch([block]), encoding="utf-8")
        vrc, vlog = validate(xml, catalog_path)
        r.check(vrc == 1 and "declared" in vlog.lower(),
                "validate.py rejects undeclared #Int2#")
    else:
        r.check(False, "no oscillator atom discovered for this case")
    results.append(r)

    return results


# --------------------------------------------------------------------------- main
def main(argv) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--catalog", default=str(SKILL_ROOT / "catalog.json"),
                    help="catalog.json (default: <skill>/catalog.json)")
    ap.add_argument("--report", default=str(SKILL_ROOT / "evals" / "eval_report.json"))
    args = ap.parse_args(argv)

    catalog_path = Path(args.catalog)
    if not catalog_path.exists():
        print(f"FAIL: catalog not found: {catalog_path}\n"
              f"Bootstrap one first: python engine/bootstrap.py --install \"<SQX folder>\"")
        return 1
    cat = Catalog(catalog_path)

    with tempfile.TemporaryDirectory(prefix="sqxcb_evals_") as td:
        results = run_cases(cat, catalog_path, Path(td))
        results += run_tier1_cases(Result, cat, catalog_path, Path(td))

    passed = sum(1 for r in results if r.ok)
    total = len(results)
    print(f"sqx-custom-block — deterministic eval harness ({total} cases)\n" + "=" * 70)
    for r in results:
        head = "PASS" if r.ok else "FAIL"
        print(f"\n[{head}] {r.group:<14} {r.name}")
        for ok, label in r.checks:
            print(f"     {'ok ' if ok else 'XX '} {label}")
    print("\n" + "=" * 70)
    print(f"{passed}/{total} cases passed"
          + ("" if passed == total else f"  —  {total - passed} FAILED"))

    report = {
        "skill": "sqx-custom-block",
        "catalog": str(catalog_path),
        "passed": passed,
        "total": total,
        "cases": [{"name": r.name, "group": r.group, "ok": r.ok,
                   "checks": [{"ok": ok, "label": lbl} for ok, lbl in r.checks]}
                  for r in results],
    }
    Path(args.report).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"report: {args.report}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
