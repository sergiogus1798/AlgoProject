"""run_evals.py — deterministic STRUCTURE harness for sqx-strategy-template.

IMPORTANT — the validity gap. A SQX template being type-correct does NOT mean it builds;
only an AlgoWizard Build proves that, and that oracle is HUMAN. So unlike the block/group
harnesses, this one cannot certify correctness — it guards the deterministic *structure*
the generator controls, so a regression in the engine is caught before you waste a build:

  A. Each shape regenerates from the live install and is structurally sound:
       - output is a valid ZIP containing strategy_Portfolio.xml that parses
       - every #Group# hole resolves to an embedded <Group> id (no dangling ref)
       - generator self-validation passed (blocks resolve) — a successful from_design IS that
       - directional shapes carry the short-side mirror (NegatedCondition / OppositeValue)
       - the exit stack is present (ExitAfterBars)
       - multi-leg shapes: N entry rules, N distinct MagicNumbers
  B. Guardrails fire: phantom group, wrong group type, non-distinct groups, unknown shape
  C. Failure hygiene: a failed generation leaves NO .sqx on disk, the failure message
     names the missing CBlock_* keys, and a hostile spec name ('../', '\\') is
     sanitized into the outdir instead of escaping it

This harness is INSTALL-BOUND: generate.py reads the live install every run. It reads the
install path + clean group names from engine/catalog.json and SKIPS gracefully if that
install isn't on this machine (so it never falsely fails on a box without the install).

Usage:
  python evals/run_evals.py                      # bundled FIXTURE install — runs anywhere
  python evals/run_evals.py --install "<SQX>"    # also exercise a real install's groups
  python evals/run_evals.py --catalog <path>     # take group names from a catalog.json

Exit 0 = every case passed · 1 = a structural regression · 2 = could not run (SKIPPED).
A SKIP is not a pass: it means nothing was tested.

The default is the committed fixture under evals/fixtures/ so this harness runs on a fresh
machine and in CI. It reads groups in memory and never writes engine/catalog.json.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from engine.generate import from_design, generate_multi_leg, SHAPES, SKEL  # noqa: E402
from engine.discover import load as discover_load  # noqa: E402

# A minimal synthetic install committed under evals/fixtures/ — enough clean groups to
# realize every shape, plus one deliberately broken group. Lets the structure harness run
# on any machine instead of SKIPping wherever the real install isn't populated yet.
FIXTURE_INSTALL = SKILL_ROOT / "evals" / "fixtures" / "install"


class Result:
    def __init__(self, name, group):
        self.name, self.group, self.ok, self.checks = name, group, True, []

    def check(self, cond, label):
        self.checks.append((bool(cond), label))
        if not cond:
            self.ok = False
        return cond


@contextlib.contextmanager
def _quiet():
    """Silence generate.py's per-template validation prints."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        yield


def _read_sqx(path: str):
    if not zipfile.is_zipfile(path):
        return None, ""
    z = zipfile.ZipFile(path)
    if "strategy_Portfolio.xml" not in z.namelist():
        return None, ""
    xml = z.read("strategy_Portfolio.xml").decode("utf-8", errors="replace")
    return ET.fromstring(xml), xml


def _refs_embedded(root) -> bool:
    emb = {g.get("id") for g in root.findall(".//RandomGroups/Group")}
    refs = {p.text for p in root.iter("Param") if p.get("key") == "#Group#"}
    return bool(refs) and refs <= emb


def _assert_structure(r: Result, path: str, directional: bool):
    root, xml = _read_sqx(path)
    if not r.check(root is not None, "valid .sqx ZIP with parseable strategy_Portfolio.xml"):
        return root
    xml = xml or ""
    r.check(_refs_embedded(root), "every #Group# hole resolves to an embedded group")
    r.check("ExitAfterBars" in xml, "exit stack present (ExitAfterBars)")
    if directional:
        r.check("NegatedCondition" in xml or "OppositeValue" in xml,
                "short side mirrored (NegatedCondition / OppositeValue)")
    # trading-soundness: the TRIGGER must live in the Signal rule, never an entry IfThen, and there
    # must be no BarsSinceOrderClosed re-entry guard -- either makes a template build but never trade.
    if root is not None:
        leak = [rule.get("name") for rule in root.iter("Rule")
                if rule.get("type") in ("IfThen", "IfThenElse")
                for iff in [rule.find("If")] if iff is not None
                if any(it.get("key") == "RandomCondition" for it in iff.iter("Item"))]
        r.check(not leak, f"trigger in the Signal rule, not the entry rule (leak: {leak})")
    r.check("BarsSinceOrderClosed" not in xml, "no BarsSinceOrderClosed re-entry guard")
    return root


def _raises(fn) -> bool:
    try:
        with _quiet():
            fn()
        return False
    except (SystemExit, KeyError, Exception):
        return True


def _raises_msg(fn) -> tuple[bool, str]:
    """Like _raises, but also returns the exception message (for asserting that a
    failure names its reasons, not just that it failed)."""
    try:
        with _quiet():
            fn()
        return False, ""
    except (SystemExit, KeyError, Exception) as e:
        return True, str(e)


MIRROR_SIGNAL = "33333333-2222-1111-3333-333333333333"
PRIMARY_SIGNAL = "33333333-1111-1111-3333-333333333333"


def _short_invariants(r: Result, path: str) -> None:
    """The four properties that make a *_short template actually work.

    Guards a regression that has already bitten once: the earlier transform kept the
    mirror ("generate=opposite") signal populated and fired the entry off IT, so the
    template traded each pooled block's `oppositeBlockKey`. Non-directional blocks
    (session/time filters) carry CBlock_null and have no opposite, so any pool holding
    one silently broke. The working architecture — taken from the hand-corrected
    gold-templates-short6-FIXED set — empties the mirror and fires on the PRIMARY signal
    with #Direction#=-1.
    """
    root = ET.fromstring(zipfile.ZipFile(path).read("strategy_Portfolio.xml").decode("utf-8", "replace"))

    mirror = [s for s in root.iter("signal") if s.get("variable") == MIRROR_SIGNAL]
    r.check(bool(mirror) and len(list(mirror[0])) == 0,
            "mirror signal is EMPTY (no oppositeBlockKey dependency)")

    primary = [s for s in root.iter("signal") if s.get("variable") == PRIMARY_SIGNAL]
    r.check(bool(primary) and len(list(primary[0])) > 0, "primary signal carries the chosen groups")

    rules = [x.get("name") for x in root.iter("Rule") if x.get("type") == "IfThen"]
    r.check(not any(str(n).startswith("Long") for n in rules), f"no Long rules remain ({rules})")

    dirs = {d.text for d in root.iter("Param") if d.get("key") == "#Direction#"}
    r.check(dirs == {"-1"}, f"every #Direction# is -1 (got {sorted(dirs)})")

    entry = next((x for x in root.iter("Rule") if x.get("name") == "Short entry"), None)
    fires_on = None
    if entry is not None:
        vars_ = [v.text for v in entry.iter("Param") if v.get("controlType") == "comboVar"]
        fires_on = vars_[0] if vars_ else None
    r.check(fires_on == PRIMARY_SIGNAL,
            "Short entry fires on the PRIMARY signal, not the mirror")


def run_cases(install: str, cond: list[str], value: list[str], tmp: str,
              broken: list[dict] | None = None) -> list[Result]:
    results: list[Result] = []
    c0, c1 = cond[0], cond[1]
    v0 = value[0]
    # First BROKEN group (exists in blockGroups.xml but references missing CBlock_*),
    # if the source has one — the fixture always does (FixtureBroken).
    bname = broken[0].get("name") if broken else None
    bmissing = (broken[0].get("missing") or []) if broken else []

    def gen(spec):
        with _quiet():
            return from_design(spec, install=install, outdir=tmp)

    # ---- A0 short-only shapes: architecture invariants --------------------------------
    for shape, spec in (
        ("stop_short", {"shape": "stop_short", "filter": c0, "trigger": c1, "price_pool": v0}),
        ("mtf_filter_short", {"shape": "mtf_filter_short", "daily_filter": c0, "trigger": c1,
                              "price_pool": v0}),
        ("market_short", {"shape": "market_short", "filter": c0, "trigger": c1}),
    ):
        r = Result(f"shape_{shape}", "A·regression")
        try:
            spec = dict(spec, name=f"Eval_{shape}")
            p = gen(spec)
            r.check(True, f"from_design({shape}) ok")
            _short_invariants(r, p)
        except Exception as e:
            r.check(False, f"from_design({shape}) raised {type(e).__name__}: {e}")
        results.append(r)

    # ---- A0b every registered shape has its skeleton on disk --------------------------
    r = Result("shapes_have_skeletons", "A·regression")
    for name, (skel, _n, _v) in sorted(SHAPES.items()):
        r.check((Path(SKEL) / skel).exists(), f"{name} -> {skel}")
    results.append(r)

    # ---- A1 stop (directional) --------------------------------------------------------
    r = Result("shape_stop", "A·regression")
    try:
        p = gen({"name": "Eval_Stop", "shape": "stop", "filter": c0, "trigger": c1, "price_pool": v0})
        r.check(True, f"from_design(stop) ok [{c0}+{c1}->{v0}]")
        _assert_structure(r, p, directional=True)
    except Exception as e:
        r.check(False, f"from_design(stop) raised {type(e).__name__}: {e}")
    results.append(r)

    # ---- A2 market (directional) ------------------------------------------------------
    r = Result("shape_market", "A·regression")
    try:
        p = gen({"name": "Eval_Market", "shape": "market", "filter": c0, "trigger": c1})
        r.check(True, "from_design(market) ok")
        _assert_structure(r, p, directional=True)
    except Exception as e:
        r.check(False, f"from_design(market) raised {type(e).__name__}: {e}")
    results.append(r)

    # ---- A3 session_market (directional, build-confirmed) -----------------------------
    r = Result("shape_session_market", "A·regression")
    try:
        p = gen({"name": "Eval_Session", "shape": "session_market", "filter": c0, "trigger": c1})
        r.check(True, "from_design(session_market) ok")
        _assert_structure(r, p, directional=True)
    except Exception as e:
        r.check(False, f"from_design(session_market) raised {type(e).__name__}: {e}")
    results.append(r)

    # ---- A4 two_entry_market (long-only, build-confirmed) -----------------------------
    r = Result("shape_two_entry_market", "A·regression")
    try:
        p = gen({"name": "Eval_TwoEntry", "shape": "two_entry_market", "entry_a": c0, "entry_b": c1})
        r.check(True, "from_design(two_entry_market) ok")
        root = _assert_structure(r, p, directional=False)
        if root is not None:
            magics = {pm.text for pm in root.iter("Param") if pm.get("key") == "#MagicNumber#"}
            entries = [x for x in root.iter("Rule")
                       if x.get("type") == "IfThen" and (x.get("name") or "").startswith("Entry")]
            r.check(len(magics) >= 2, f"two distinct MagicNumbers (got {len(magics)})")
            r.check(len(entries) >= 2, f"two independent entry rules (got {len(entries)})")
    except Exception as e:
        r.check(False, f"from_design(two_entry_market) raised {type(e).__name__}: {e}")
    results.append(r)

    # ---- A5 multi_leg (long-only, generalizes two_entry) ------------------------------
    r = Result("shape_multi_leg", "A·regression")
    legs = [{"group": c0, "order": "market", "exit_bars": 10},
            {"group": c1, "order": "stop", "price_pool": v0, "exit_bars": 30},
            {"group": c0, "order": "market", "exit_bars": 20}]
    try:
        with _quiet():
            p = generate_multi_leg("Eval_MultiLeg3", legs, install=install, outdir=tmp)
        r.check(True, "generate_multi_leg(3 legs) ok")
        root = _assert_structure(r, p, directional=False)
        if root is not None:
            magics = {pm.text for pm in root.iter("Param") if pm.get("key") == "#MagicNumber#"}
            entries = [x for x in root.iter("Rule")
                       if x.get("type") == "IfThen" and (x.get("name") or "").startswith("Entry")]
            r.check(len(entries) == 3, f"3 entry rules (got {len(entries)})")
            r.check(len(magics) >= 3, f"3 distinct MagicNumbers (got {len(magics)})")
    except Exception as e:
        r.check(False, f"generate_multi_leg raised {type(e).__name__}: {e}")
    results.append(r)

    # ---- A6 role_market (directional, NEW: regime AND trigger AND NOT veto) ------------
    if len(cond) >= 3:
        r = Result("shape_role_market", "A·regression")
        try:
            p = gen({"name": "Eval_Role", "shape": "role_market",
                     "regime": c0, "trigger": c1, "veto": cond[2]})
            r.check(True, f"from_design(role_market) ok [{c0} AND {c1} AND NOT {cond[2]}]")
            root = _assert_structure(r, p, directional=True)
            if root is not None:
                holes = {pm.text for pm in root.iter("Param") if pm.get("key") == "#Group#"}
                r.check(len(holes) == 3, f"three distinct #Group# holes (got {len(holes)})")
                xml = _read_sqx(p)[1]
                r.check("BarsSinceOrderClosed" not in xml,
                        "clean signal-var architecture (no inherited bars-guard)")
        except Exception as e:
            r.check(False, f"from_design(role_market) raised {type(e).__name__}: {e}")
        results.append(r)

    # ---- A7 mtf_filter (directional, NEW: daily regime filter AND main-TF trigger) -----
    r = Result("shape_mtf_filter", "A·regression")
    try:
        p = gen({"name": "Eval_MTF", "shape": "mtf_filter",
                 "daily_filter": c0, "trigger": c1, "price_pool": v0})
        r.check(True, f"from_design(mtf_filter) ok [{c0}@daily AND {c1}@main ->{v0}]")
        root = _assert_structure(r, p, directional=True)
        if root is not None:
            streams = root.findall(".//Datas/data")
            r.check(len(streams) == 2, f"two data streams main+daily (got {len(streams)})")
            tfs = {(d.findtext("timeFrame") or "?") for d in streams}
            r.check("1440" in tfs, f"daily subchart present (timeFrames {sorted(tfs)})")
            # RandomCondition1 (the filter) must sit on the higher TF (#Chart#=1); RC2 on main (0)
            chart_by_ident = {}
            for it in root.iter("Item"):
                if it.get("key") == "RandomCondition":
                    ident = next((pp.text for pp in it.findall("Param") if pp.get("key") == "#Identification#"), None)
                    chart = next((pp.text for pp in it.findall("Param") if pp.get("key") == "#Chart#"), None)
                    if ident:
                        chart_by_ident[ident] = chart
            r.check(chart_by_ident.get("RandomCondition1") == "1",
                    f"daily filter hole on subchart (RandomCondition1 #Chart#={chart_by_ident.get('RandomCondition1')})")
            r.check(chart_by_ident.get("RandomCondition2") == "0",
                    f"trigger hole on main chart (RandomCondition2 #Chart#={chart_by_ident.get('RandomCondition2')})")
    except Exception as e:
        r.check(False, f"from_design(mtf_filter) raised {type(e).__name__}: {e}")
    results.append(r)

    # ---- B1 phantom group refused -----------------------------------------------------
    r = Result("guardrail_phantom_group", "B·guardrail")
    r.check(_raises(lambda: from_design(
        {"name": "X", "shape": "market", "filter": "NotARealGroup_zzz", "trigger": c1},
        install=install, outdir=tmp)), "phantom group refused")
    results.append(r)

    # ---- B2 wrong group type refused (Value where Condition expected) -----------------
    r = Result("guardrail_wrong_type", "B·guardrail")
    r.check(_raises(lambda: from_design(
        {"name": "X", "shape": "market", "filter": v0, "trigger": c1},
        install=install, outdir=tmp)), f"Value group {v0} refused as a Condition filter")
    results.append(r)

    # ---- B3 non-distinct condition groups refused -------------------------------------
    r = Result("guardrail_non_distinct", "B·guardrail")
    r.check(_raises(lambda: from_design(
        {"name": "X", "shape": "market", "filter": c0, "trigger": c0},
        install=install, outdir=tmp)), "same group used twice refused")
    results.append(r)

    # ---- B4 unknown shape refused -----------------------------------------------------
    r = Result("guardrail_unknown_shape", "B·guardrail")
    r.check(_raises(lambda: from_design(
        {"name": "X", "shape": "limit_mtf_grid", "filter": c0, "trigger": c1},
        install=install, outdir=tmp)), "unknown shape refused")
    results.append(r)

    # ---- C1 failed generation leaves NO file on disk ----------------------------------
    # Regression guard for the write-then-validate bug: a broken .sqx used to survive
    # VALIDATION FAILED in out/, indistinguishable from a good template.
    r = Result("fail_leaves_no_file", "C·fail-hygiene")
    if bname:
        out = Path(tmp) / "Eval_BrokenNoFile.sqx"
        raised, _msg = _raises_msg(lambda: from_design(
            {"name": "Eval_BrokenNoFile", "shape": "market", "filter": bname, "trigger": c1},
            install=install, outdir=tmp))
        r.check(raised, f"design over BROKEN group {bname} fails validation")
        r.check(not out.exists(), "no .sqx left behind after the validation failure")
    else:
        r.check(True, "no broken group in this source — broken-group leg skipped")
    out2 = Path(tmp) / "Eval_PhantomNoFile.sqx"
    raised2 = _raises(lambda: from_design(
        {"name": "Eval_PhantomNoFile", "shape": "market", "filter": "NoSuchGroup_zzz",
         "trigger": c1}, install=install, outdir=tmp))
    r.check(raised2, "design over NONEXISTENT group fails")
    r.check(not out2.exists(), "no .sqx left behind after the lookup failure")
    results.append(r)

    # ---- C2 validation failure NAMES the missing CBlock_* keys ------------------------
    if bname and bmissing:
        r = Result("fail_reason_names_missing_blocks", "C·fail-hygiene")
        raised, msg = _raises_msg(lambda: from_design(
            {"name": "Eval_BrokenReason", "shape": "market", "filter": bname, "trigger": c1},
            install=install, outdir=tmp))
        r.check(raised, f"design over BROKEN group {bname} fails validation")
        r.check("VALIDATION FAILED" in msg, f"failure is a VALIDATION FAILED (msg: {msg[:80]}...)")
        for k in bmissing:
            r.check(k in msg, f"failure message names the missing block {k}")
        results.append(r)

    # ---- C3 LLM-authored spec name is sanitized into the outdir -----------------------
    # spec['name'] used to be joined into the output path raw; '../' or '\\' could drop
    # the file outside outdir. Sanitized, it must land INSIDE outdir, nowhere else.
    r = Result("evil_name_sanitized", "C·fail-hygiene")
    try:
        p = gen({"name": "../Evil\\Escape", "shape": "market", "filter": c0, "trigger": c1})
        pp = Path(p).resolve()
        tmp_res = Path(tmp).resolve()
        r.check(pp.exists(), "template with hostile name still generated")
        r.check(pp.parent == tmp_res, f"file landed INSIDE the outdir (got {pp.parent})")
        r.check(pp.name == ".._Evil_Escape.sqx", f"separators sanitized to '_' (got {pp.name})")
        r.check(not (tmp_res.parent / "EvilEscape.sqx").exists()
                and not (tmp_res.parent / "Evil").exists(),
                "nothing escaped above the outdir")
    except Exception as e:
        r.check(False, f"hostile-name generation raised {type(e).__name__}: {e}")
    results.append(r)

    return results


def main(argv) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--install", default=None,
                    help="run against a REAL SQX install (default: the bundled fixture)")
    ap.add_argument("--catalog", default=None,
                    help="take group names from this catalog.json instead of scanning an install")
    ap.add_argument("--report", default=str(SKILL_ROOT / "evals" / "eval_report.json"))
    args = ap.parse_args(argv)

    def names(v) -> list[str]:
        if isinstance(v, dict):
            out = list(v.keys())
        elif isinstance(v, list):
            out = [x.get("name") if isinstance(x, dict) else x for x in v]
        else:
            out = []
        return [str(n) for n in out if n]

    # Where the groups come from. The DEFAULT is the bundled fixture install, so this
    # harness runs everywhere — on a fresh machine, in CI, before the user has authored a
    # single block. It used to default to the user's real catalog and SKIP whenever that
    # install lacked enough clean groups, which is the normal state of a new install: the
    # only automated check on the most complex generator in the toolkit essentially never
    # ran. `--install <path>` still exercises a real install as an ADDITIONAL run.
    #
    # Groups are read in memory via discover.load() — the harness must never write
    # engine/catalog.json, or running the evals would silently repoint the skill at the
    # fixture.
    broken_groups: list[dict] = []
    if args.catalog:
        cat = json.loads(Path(args.catalog).read_text(encoding="utf-8"))
        install = args.install or cat.get("install")
        cond, value = names(cat.get("clean_condition_groups")), names(cat.get("clean_value_groups"))
        broken_groups = cat.get("broken_groups") or []
        source = f"catalog {args.catalog}"
    else:
        install = args.install or str(FIXTURE_INSTALL)
        source = "REAL install" if args.install else "bundled FIXTURE"
        try:
            groups, _n = discover_load(install)
        except (OSError, ET.ParseError) as exc:
            print(f"FAIL: cannot read groups from {install}: {exc}")
            return 1
        clean = [g for g in groups if g["clean"]]
        cond = [g["name"] for g in clean if g["type"] == "Condition"]
        value = [g["name"] for g in clean if g["type"] == "Value"]
        broken_groups = [g for g in groups if not g["clean"]]

    print(f"sqx-strategy-template — deterministic structure harness\n" + "=" * 70)
    print(f"source : {source}")
    print(f"install: {install}")
    print(f"groups : {len(cond)} clean Condition, {len(value)} clean Value")
    if source == "bundled FIXTURE":
        print("         (run with --install \"<your SQX folder>\" to test your real groups too)")

    # Install-bound: a missing install or too few groups is NOT a pass. It used to
    # return 0, so "nothing ran" was indistinguishable from "everything passed" — the
    # harness looked green on an install where no shape could actually be generated.
    # SKIP now exits 2: 0 = ran and passed, 1 = ran and failed, 2 = could not run.
    def skipped(reason, *fixes):
        print("\n" + "!" * 70)
        print(f"SKIPPED — nothing was tested: {reason}")
        print("!" * 70)
        for f in fixes:
            print(f"  -> {f}")
        print("\n(exit 2 = did not run. This is NOT a pass.)")
        return 2

    bg = Path(install) / "user" / "settings" / "blockGroups.xml" if install else None
    if not install or bg is None or not bg.exists():
        return skipped(
            "this install isn't on this machine — the harness is install-bound",
            "Run /sqx-setup to point sqx-lab at your StrategyQuant X folder.",
            "Buildability is the human oracle; there is nothing to regress-test without it.")
    if len(cond) < 2 or len(value) < 1:
        broken = broken_groups
        fixes = [f"have {len(cond)} clean Condition group(s) (need >=2) and "
                 f"{len(value)} clean Value group(s) (need >=1)."]
        if broken:
            n = sum(len(g.get("missing") or []) for g in broken)
            fixes.append(f"{len(broken)} group(s) are BROKEN, missing {n} CBlock_* between "
                         f"them: {', '.join(g['name'] for g in broken[:4])}.")
            fixes.append("Repair them first — catalog.json's `repair_manifest` is a work "
                         "order for the sqx-custom-block skill. See /sqx-doctor.")
        fixes.append("Otherwise build more pools with sqx-random-group.")
        return skipped("not enough CLEAN random groups to fill any shape", *fixes)

    with tempfile.TemporaryDirectory(prefix="sqxtpl_evals_") as td:
        results = run_cases(install, cond, value, td, broken=broken_groups)

    passed = sum(1 for r in results if r.ok)
    total = len(results)
    print("=" * 70)
    for r in results:
        print(f"\n[{'PASS' if r.ok else 'FAIL'}] {r.group:<14} {r.name}")
        for ok, label in r.checks:
            print(f"     {'ok ' if ok else 'XX '} {label}")
    print("\n" + "=" * 70)
    print(f"{passed}/{total} cases passed" + ("" if passed == total else f"  —  {total - passed} FAILED"))
    print("note: structure only — an AlgoWizard Build remains the correctness oracle.")

    report = {"skill": "sqx-strategy-template", "install": install,
              "passed": passed, "total": total,
              "cases": [{"name": r.name, "group": r.group, "ok": r.ok,
                         "checks": [{"ok": ok, "label": lbl} for ok, lbl in r.checks]}
                        for r in results]}
    Path(args.report).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"report: {args.report}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
