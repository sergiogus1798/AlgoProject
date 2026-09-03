r"""
run_evals.py — deterministic STRUCTURE self-test for sqx-strategy-project.

Proves the engine reproduces the build-confirmed clone-and-wire mechanic and that the
guardrails fire. Structure only — an AlgoWizard Build is the real oracle.

    python evals/run_evals.py "C:\StrategyQuantX"
    python evals/run_evals.py            # uses the install in engine/catalog.json, if present

Picks the first clonable base project that has template build tasks + the first template
set, deterministically (sorted). Emits to a temp dir; writes nothing into the install.
"""
import os
import re
import sys
import json
import shutil
import zipfile
import tempfile
from pathlib import Path
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.dirname(ROOT)))     # plugin root (sqx_common)
from engine.generate import (make_project, clone_task, read_base, base_build_tasks,  # noqa: E402
                             ensure_mtf_charts, detect_instrument, set_instrument,
                             set_acceptance, set_trading_options, build_config, verify)
from engine.discover import discover  # noqa: E402
import sqx_common  # noqa: E402

PASS, FAIL = "PASS", "FAIL"
results = []


def _kids(root, tag):
    """Children of root/<tag>, or () — without ElementTree's deprecated truth test."""
    el = root.find(tag)
    return list(el) if el is not None else ()


def check(name, cond, detail=""):
    results.append((PASS if cond else FAIL, name, detail))
    print(f"  [{PASS if cond else FAIL}] {name}" + (f"  — {detail}" if detail and not cond else ""))
    return cond


def resolve_install(argv):
    if len(argv) > 1:
        return argv[1].rstrip("\\/")
    cat = os.path.join(ROOT, "engine", "catalog.json")
    if os.path.isfile(cat):
        with open(cat, encoding="utf-8") as f:
            return json.load(f).get("install")
    return None


def main():
    install = resolve_install(sys.argv)
    if not install or not os.path.isdir(install):
        print("SKIP: no install. Pass one: python evals/run_evals.py \"<install>\"")
        return 0

    cat = discover(install)

    # pick a deterministic base (first project with template build tasks) + first template set
    base = members = donor_bytes = None
    for p in cat["projects"]:
        if p.get("error") or not p.get("build_tasks"):
            continue
        mm = read_base(p["path"])
        donor = base_build_tasks(mm)[0]
        raw = mm[donor[1]]
        if b"<StrategyType" in raw and b"templateFile=" in raw:
            base, members, donor_bytes = p, mm, raw
            break
    if not base:
        print("SKIP: no clonable base project with template build tasks on this install")
        return 0
    tpl_sets = [(k, v) for k, v in cat["template_paths"].items() if v]
    if not tpl_sets:
        print("SKIP: no template sets on this install")
        return 0

    # This block used to EXCLUDE every multi-stream (MTF) template from the pick, on the
    # grounds that ensure_mtf_charts hard-fails on donors with no task-level <Datas>
    # mapping — calling that "a pre-existing engine limit ... by design". That was the
    # eval steering around a real bug instead of covering it, and it is exactly why the
    # MTF path had zero coverage on this install's donor dialect. The engine now handles
    # both donor shapes (inserting the stream when <Datas> exists, warning loudly when it
    # does not), so the pick DELIBERATELY includes an MTF template whenever one exists.
    def _extra_streams(sqx_path):
        try:
            with zipfile.ZipFile(sqx_path) as z:
                tpl = z.read("strategy_Portfolio.xml")
        except Exception:
            return []
        return [int(t) for t in re.findall(rb"<timeFrame>(\d+)</timeFrame>", tpl)
                if int(t) > 0]

    donor_has_datas = bool(re.search(rb"</data>\s*</Datas>", donor_bytes))
    set_name, tpl_paths = sorted(tpl_sets)[0]
    all_tpl = sorted(tpl_paths)
    mtf_tpl = [p for p in all_tpl if _extra_streams(p)]
    single_tpl = [p for p in all_tpl if not _extra_streams(p)]
    picks = (single_tpl[:2] + mtf_tpl[:1]) or all_tpl[:3]
    if not picks:
        print("SKIP: no templates in the first template set")
        return 0

    print(f"base    : {base['folder']}  ({base['build_tasks']} tasks)")
    print(f"template: {set_name}  (using {len(picks)} of {len(tpl_paths)})")
    print(f"donor   : task-level <Datas> mapping = {donor_has_datas}"
          f"  |  pick includes {len(mtf_tpl[:1])} MTF template(s) of {len(mtf_tpl)} available")
    print()

    tmp = tempfile.mkdtemp(prefix="sqxproj_eval_")
    try:
        # ---- E1: discover surfaced a usable install -----------------------------------
        check("E1 discover: >=1 clonable project + >=1 template set",
              any(p.get("build_tasks") for p in cat["projects"]) and bool(tpl_sets))

        # ---- E2: make_project emits + self-verifies -----------------------------------
        tasks = [{"template": p,
                  "output_db": "BS-Eval_" + os.path.splitext(os.path.basename(p))[0],
                  "avg_trades": 3, "time_minutes": 7} for p in picks]
        out_cfx = os.path.join(tmp, "EVAL_CLONE", "project.cfx")
        rep = make_project(base["path"], "EVAL_CLONE", tasks, out_cfx=out_cfx)
        check("E2 make_project verify report clean",
              rep["build_tasks"] == len(picks) and rep["templates_resolve"]
              and rep["system_databanks_ok"], str(rep))

        # ---- E3: faithful clone — donor + the 4 swaps + MTF chart provisioning ---------
        # make_project's transform is clone_task() THEN ensure_mtf_charts(): a template
        # that declares a higher-timeframe stream needs the matching data <Chart> added to
        # the task, or it can't build. This eval used to compare against clone_task alone
        # and therefore FAILED on any MTF template — the eval was stale, not the engine.
        # Reproducing the full pipeline keeps the "no unexplained drift" guarantee while
        # still catching a real regression in either step. (members/donor_bytes were
        # loaded once during base selection above.)
        with zipfile.ZipFile(out_cfx) as z:
            faithful, mtf_provisioned = True, 0
            for i, t in enumerate(tasks, 1):
                swapped = clone_task(donor_bytes, t["template"], t["output_db"],
                                     avg_trades=3, time_minutes=7)
                expected = ensure_mtf_charts(swapped, t["template"])
                if expected != swapped:
                    mtf_provisioned += 1
                faithful &= (z.read(f"Build-Task{i}.xml") == expected)
        check("E3 every clone == donor + the 4 swaps + MTF charts (byte-identical)", faithful)
        print(f"       ({mtf_provisioned} of {len(tasks)} task(s) needed MTF chart provisioning)")

        # ---- E4: config preserved (project tag/version, system DBs, inactive tasks) ----
        with zipfile.ZipFile(out_cfx) as z:
            cfg = ET.fromstring(z.read("config.xml").decode("utf-8"))
        # `elem or []` is a DeprecationWarning on 3.12+ (an empty element is falsy today,
        # truthy in future versions) and printed 3 warnings over every eval run.
        names_db = {d.get("name") for d in _kids(cfg, "Databanks")}
        inactive = {t.get("name") for t in _kids(cfg, "Tasks") if t.get("type") != "Build"}
        sys5 = {"Results", "Last generation", "Initial population",
                "Strategies to improve", "Existing portfolio"}
        base_cfg = ET.fromstring(read_base(base["path"])["config.xml"].decode("utf-8"))
        base_inactive = {t.get("name") for t in _kids(base_cfg, "Tasks")
                         if t.get("type") != "Build"}
        check("E4 project name swapped, version preserved",
              cfg.get("name") == "EVAL_CLONE" and cfg.get("version") == base_cfg.get("version"))
        check("E4 all 5 system databanks survive", sys5 <= names_db,
              str(sorted(sys5 - names_db)))
        check("E4 inactive tasks preserved exactly from base", inactive == base_inactive,
              f"clone={sorted(inactive)} base={sorted(base_inactive)}")

        # ---- E5: settings overrides actually landed -----------------------------------
        # EXPECTATION CHANGED with the Tier-1 audit fixes (P0-5 / P0-6): the digit
        # landing in the file was never enough. Both real donors ship the AvgTrades
        # condition use="false" and a type="databank-full" stop condition, under which
        # the number gates nothing and minutes= is ignored. "Applied" now means: value
        # written AND the enclosing condition enabled AND the stop type = time-limit.
        with zipfile.ZipFile(out_cfx) as z:
            raw = z.read("Build-Task1.xml").decode("utf-8", "replace")
        av = re.search(r'class="AvgTradesPerMonth"\s*/>\s*</Left-Side>\s*<Comparator value="&gt;" />'
                       r'\s*<Right-Side valueType="numeric">\s*<Numeric-Value value="(\d+)"', raw)
        rk5 = re.search(r"<Rankings\b.*?</Rankings>", raw, re.S).group(0)
        av_cond = [c for c in re.findall(r"<Condition\b[^>]*>.*?</Condition>", rk5, re.S)
                   if 'class="AvgTradesPerMonth"' in c]
        av_enabled = bool(av_cond) and 'use="true"' in re.match(r"<Condition\b[^>]*>",
                                                                av_cond[0]).group(0)
        sc5 = re.search(r"<StopCondition\b[^>]*>", raw).group(0)
        mins = re.search(r'\bminutes="(\d+)"', sc5)
        check("E5 AvgTradesPerMonth override applied (=3) AND condition enabled",
              bool(av) and av.group(1) == "3" and av_enabled,
              f"value={av and av.group(1)} enabled={av_enabled}")
        check("E5 time-cap override applied (=7) AND type=time-limit",
              bool(mins) and mins.group(1) == "7" and 'type="time-limit"' in sc5,
              sc5)

        # ---- E6: guardrail — duplicate output databanks rejected ----------------------
        # (the same template twice is fine here — the guardrail under test is the
        # duplicate output_db name, and the pick may legitimately hold only 1 template)
        dup = [{"template": picks[0], "output_db": "X"},
               {"template": picks[0], "output_db": "X"}]
        try:
            make_project(base["path"], "DUP", dup, out_cfx=os.path.join(tmp, "DUP", "project.cfx"))
            check("E6 duplicate output databanks rejected", False, "no error raised")
        except AssertionError:
            check("E6 duplicate output databanks rejected", True)

        # ---- E7: guardrail — unresolvable templateFile rejected -----------------------
        bad = [{"template": os.path.join(tmp, "nope_does_not_exist.sqx"), "output_db": "BS-Nope"}]
        try:
            make_project(base["path"], "BAD", bad, out_cfx=os.path.join(tmp, "BAD", "project.cfx"))
            check("E7 unresolvable templateFile rejected", False, "no error raised")
        except AssertionError:
            check("E7 unresolvable templateFile rejected", True)

        # ---- E8: guardrail — donor without a template hole rejected -------------------
        synthetic = donor_bytes.replace(b"<StrategyType", b"<NoStrategyHere", 1)
        try:
            clone_task(synthetic, picks[0], "BS-Z")
            check("E8 donor without <StrategyType templateFile> rejected", False, "no error")
        except ValueError:
            check("E8 donor without <StrategyType templateFile> rejected", True)

        # ================================================================================
        # Tier-1 audit repro cases (P0-5..9, P0-14) — in-memory against REAL donor bytes
        # ================================================================================
        def _rankings(b):
            return re.search(rb"<Rankings\b.*?</Rankings>", b, re.S)

        def _conds(block):
            return re.findall(rb"<Condition\b[^>]*>.*?</Condition>", block, re.S)

        def _use(cond):
            m = re.search(rb'\buse="([^"]*)"', re.match(rb"<Condition\b[^>]*>", cond).group(0))
            return m.group(1) if m else None

        # ---- E9 (P0-5): avg_trades must ENABLE the donor's disabled condition ---------
        n9 = []
        c9 = clone_task(donor_bytes, picks[0], "BS-E9", avg_trades=4, notes=n9)
        rk9 = _rankings(c9).group(0)
        avg9 = [c for c in _conds(rk9) if b'class="AvgTradesPerMonth"' in c]
        oth9 = [c for c in _conds(rk9) if b'class="AvgTradesPerMonth"' not in c]
        donor_rk = _rankings(donor_bytes).group(0)
        donor_avg = [c for c in _conds(donor_rk) if b'class="AvgTradesPerMonth"' in c]
        donor_oth = [c for c in _conds(donor_rk) if b'class="AvgTradesPerMonth"' not in c]
        check("E9 avg_trades: condition enabled (use=true) with value 4",
              bool(avg9) and _use(avg9[0]) == b"true"
              and b'<Numeric-Value value="4"' in avg9[0])
        was_disabled = bool(donor_avg) and _use(donor_avg[0]) == b"false"
        check("E9 avg_trades: enable recorded in notes (donor had it disabled)",
              (not was_disabled)
              or any("enabled AvgTradesPerMonth acceptance" in x for x in n9), str(n9))
        check("E9 avg_trades: OTHER acceptance conditions untouched", oth9 == donor_oth)

        # ---- E10 (P0-6): time cap switches the stop condition to type=time-limit ------
        # Enum confirmed on THIS install (read-only investigation): the GUI-built
        # project user/settings/StrategyTemplates/Pacino Only Long/INDICES_ID_60_MKT_LONG
        # carries <StopCondition type="time-limit" … minutes="5"/> on all 24 build
        # tasks, and internal/web/RESULTS2/result2.js lists buildStopConditionTypes =
        # {timeLimit:"time-limit", never:"never", passedCount:"passed-count",
        #  databankFull:"databank-full"}.
        n10 = []
        c10 = clone_task(donor_bytes, picks[0], "BS-E10", time_minutes=7, notes=n10)
        sc10 = re.search(rb"<StopCondition\b[^>]*>", c10).group(0)
        donor_sc = re.search(rb"<StopCondition\b[^>]*>", donor_bytes).group(0)
        donor_was_timelimit = b'type="time-limit"' in donor_sc
        check("E10 time cap: minutes=7 AND type=time-limit on the stop condition",
              b'minutes="7"' in sc10 and b'type="time-limit"' in sc10,
              sc10.decode("utf-8", "replace"))
        check("E10 time cap: type switch recorded in notes",
              donor_was_timelimit or any("time-limit" in x for x in n10), str(n10))

        # ---- E11/E12 (P0-7): anchored set_instrument on the REAL donors ----------------
        # classify this install's donors: aliasing (symbol string == instrument id) and
        # multi-chart (a second chart on a different symbol)
        donors = {}
        for p in cat["projects"]:
            if p.get("error") or not p.get("build_tasks"):
                continue
            mm = read_base(p["path"])
            bts = base_build_tasks(mm)
            if not bts:
                continue
            braw = mm[bts[0][1]]
            if b"<StrategyType" in braw and b"templateFile=" in braw:
                donors[p["folder"]] = braw
        aliasing = {f: b for f, b in donors.items()
                    if detect_instrument(b)[0] and
                    detect_instrument(b)[0] == detect_instrument(b)[1]}
        multi = {f: b for f, b in donors.items()
                 if len(set(re.findall(rb'<Chart symbol="([^"]*)"', b))) > 1}

        if aliasing:
            fld, d11 = sorted(aliasing.items())[0]
            osym11 = detect_instrument(d11)[0]
            n11 = []
            o11 = set_instrument(d11, "EURUSD_M1_EVAL", "EURUSD_eval_instr", notes=n11)
            check(f"E11 aliasing donor ({fld}): instrument id actually swapped",
                  b'instrument="EURUSD_eval_instr"' in o11
                  and b'instrument="EURUSD_M1_EVAL"' not in o11)
            check(f"E11 aliasing donor ({fld}): primary symbol swapped in every context",
                  o11.count(osym11.encode()) == 0
                  and b'<Chart symbol="EURUSD_M1_EVAL"' in o11
                  and b'<Symbol name="EURUSD_M1_EVAL"' in o11)
        else:
            print("       (E11 skipped: no aliasing donor on this install)")

        if multi:
            # prefer a NON-aliasing multi-chart donor so E12 exercises the normal case
            plain = {f: b for f, b in multi.items() if f not in aliasing} or multi
            fld, d12 = sorted(plain.items())[0]
            osym12, oins12 = detect_instrument(d12)
            foreign12 = sorted({s for s in re.findall(rb'<Chart symbol="([^"]*)"', d12)
                                if s != osym12.encode()})
            n12 = []
            o12 = set_instrument(d12, "EURUSD_M1_EVAL", "EURUSD_eval_instr", notes=n12)
            check(f"E12 2-chart donor ({fld}): primary swapped everywhere",
                  o12.count(osym12.encode()) == 0 and o12.count(oins12.encode()) == 0)
            warns12 = " ".join(x for x in n12 if x.startswith("WARNING"))
            check(f"E12 2-chart donor ({fld}): foreign chart untouched + named in warning",
                  all(f in o12 for f in foreign12)
                  and all(f.decode() in warns12 for f in foreign12),
                  f"foreign={foreign12} notes={n12}")
        else:
            print("       (E12 skipped: no multi-chart donor on this install)")

        # ---- E13 (P0-8): build_config keeps every non-Tasks/Databanks section ----------
        res_base = None
        for p in cat["projects"]:
            if p.get("error") or not p.get("build_tasks"):
                continue
            mm = read_base(p["path"])
            cfg_txt = mm["config.xml"].decode("utf-8")
            extra = [c.tag for c in ET.fromstring(cfg_txt)
                     if c.tag not in ("Tasks", "Databanks")]
            if extra:
                res_base = (p["folder"], mm, cfg_txt, extra)
                break
        if res_base:
            fld, mm13, cfg_txt, extra = res_base
            spec13 = [{"name": "T1", "taskXMLFile": "Build-Task1.xml",
                       "output_db": "BS-E13", "settings_preset": "", "position": 1000}]
            out13 = build_config(mm13["config.xml"], "E13", spec13).decode("utf-8")
            base_tags = [c.tag for c in ET.fromstring(cfg_txt)]
            out_tags = [c.tag for c in ET.fromstring(out13)]
            check(f"E13 config sections preserved in order ({fld}: {base_tags})",
                  out_tags == base_tags, f"got {out_tags}")
            verbatim = True
            for t in extra:
                seg = re.search(rf"<{t}\b[^>]*/>|<{t}\b.*?</{t}>", cfg_txt, re.S)
                verbatim &= bool(seg) and seg.group(0) in out13
            check("E13 extra sections (e.g. <Resources>) byte-verbatim", verbatim)
        else:
            print("       (E13 skipped: no base project with extra config sections)")

        # ---- E13b (P0-8): output_db colliding with a preserved databank -> ValueError --
        try:
            build_config(members["config.xml"], "E13b",
                         [{"name": "T1", "taskXMLFile": "Build-Task1.xml",
                           "output_db": "Results", "settings_preset": "", "position": 1000}])
            check("E13b output_db == system databank rejected (ValueError)", False,
                  "no error raised")
        except ValueError:
            check("E13b output_db == system databank rejected (ValueError)", True)

        # ---- E14 (P0-9): set_acceptance works on the real all-disabled donor -----------
        n14 = []
        o14 = set_acceptance(donor_bytes, keep_classes=("AvgTradesPerMonth",), notes=n14)
        rk14 = _rankings(o14).group(0)
        avg14 = [c for c in _conds(rk14) if b'class="AvgTradesPerMonth"' in c]
        oth14 = [c for c in _conds(rk14) if b'class="AvgTradesPerMonth"' not in c]
        check("E14 set_acceptance succeeds on all-disabled donor, keep enabled",
              bool(avg14) and _use(avg14[0]) == b"true")
        check("E14 set_acceptance: every other condition inactive",
              all(_use(c) == b"false" for c in oth14))
        m_in, m_out = _rankings(donor_bytes), _rankings(o14)
        check("E14 set_acceptance: bytes outside <Rankings> untouched (CrossChecks safe)",
              donor_bytes[:m_in.start()] == o14[:m_out.start()]
              and donor_bytes[m_in.end():] == o14[m_out.end():])
        try:
            set_acceptance(donor_bytes, keep_classes=("NoSuchClassXYZ",))
            check("E14 unknown keep-class -> clear ValueError", False, "no error raised")
        except ValueError as e:
            check("E14 unknown keep-class -> clear ValueError",
                  "NoSuchClassXYZ" in str(e) and "available" in str(e), str(e))
        # attribute-order-insensitivity: extra attribute before use= must not hide it
        blk = _rankings(donor_bytes)
        blk2 = blk.group(0).replace(b'<Condition use="false">',
                                    b'<Condition id="reorder-probe" use="false">', 1)
        synth14 = donor_bytes[:blk.start()] + blk2 + donor_bytes[blk.end():]
        o14b = set_acceptance(synth14, keep_classes=("AvgTradesPerMonth",))
        avg14b = [c for c in _conds(_rankings(o14b).group(0))
                  if b'class="AvgTradesPerMonth"' in c]
        check("E14 attribute-order-insensitive (reordered use= still found + enabled)",
              bool(avg14b) and _use(avg14b[0]) == b"true"
              and b'id="reorder-probe"' in avg14b[0])

        # ---- E15 (P0-14): friday_exit accepts exit_time (documented) AND time (legacy) -
        def _fx(b):
            return int(re.search(rb'<Param key="FridayExitTime"[^>]*>(\d+)</Param>', b).group(1))
        o15a = set_trading_options(donor_bytes, friday_exit={"enabled": True, "exit_time": "19:00"})
        o15b = set_trading_options(donor_bytes, friday_exit={"enabled": True, "time": "18:00"})
        o15c = set_trading_options(donor_bytes, friday_exit={"enabled": True,
                                                             "exit_time": "19:00", "time": "06:00"})
        check("E15 friday_exit exit_time key (documented) applied", _fx(o15a) == 19 * 3600)
        check("E15 friday_exit legacy time key still applied", _fx(o15b) == 18 * 3600)
        check("E15 friday_exit exit_time preferred when both present", _fx(o15c) == 19 * 3600)

        # ---- E17: template MODE, not just the template path ----------------------------
        # The defect this covers: both real Builder donors ship <StrategyType type="simple">,
        # under which SQX ignores templateFile entirely and builds generic random
        # strategies — silently, and with a run that looks completely successful. The
        # engine used to swap only the path, so every project it produced was templateless
        # and verify() still went green because it compared the path string alone.
        def _stype(b):
            return re.search(rb'<StrategyType\b[^>]*>', b).group(0)

        # force the donor into the exact broken state, whatever it ships as
        simple_donor = donor_bytes.replace(_stype(donor_bytes),
                                           re.sub(rb'\btype="[^"]*"', b'type="simple"',
                                                  _stype(donor_bytes), count=1), 1)
        c17 = clone_task(simple_donor, picks[0], "BS-E17")
        el17 = _stype(c17)
        check("E17 simple-mode donor is forced into type=\"template\"",
              b'type="template"' in el17, el17.decode("utf-8", "replace")[:160])
        check("E17 templateFile still swapped in the same element",
              picks[0].encode("utf-8") in el17)
        n17 = []
        clone_task(simple_donor, picks[0], "BS-E17b", notes=n17)
        check("E17 mode correction is reported, never silent",
              any("template" in m and "simple" in m for m in n17), str(n17))
        # the fix must normalize the mode and drift NOTHING else: cloning the same task
        # from a simple-mode donor and from a template-mode one is byte-identical
        tmpl_donor = donor_bytes.replace(_stype(donor_bytes),
                                         re.sub(rb'\btype="[^"]*"', b'type="template"',
                                                _stype(donor_bytes), count=1), 1)
        check("E17 clone from simple-mode donor == clone from template-mode donor",
              c17 == clone_task(tmpl_donor, picks[0], "BS-E17"))
        # and verify() must REJECT a simple-mode project, not pass it
        ok17 = os.path.join(tmp, "E17", "project.cfx")
        make_project(base["path"], "E17", [{"template": picks[0], "output_db": "BS-E17v"}],
                     out_cfx=ok17)
        with zipfile.ZipFile(ok17) as z:
            members17 = {n: z.read(n) for n in z.namelist()}
        t17 = members17["Build-Task1.xml"]
        members17["Build-Task1.xml"] = t17.replace(
            _stype(t17), re.sub(rb'\btype="[^"]*"', b'type="simple"', _stype(t17), count=1), 1)
        bad17 = os.path.join(tmp, "E17", "regressed.cfx")
        with zipfile.ZipFile(bad17, "w", zipfile.ZIP_DEFLATED) as zo:
            for n, d in members17.items():
                zo.writestr(n, d)
        try:
            verify(bad17, [{"name": "t1", "template": picks[0], "output_db": "BS-E17v"}])
            check("E17 verify() REJECTS a simple-mode task", False, "verify passed it")
        except AssertionError as e:
            check("E17 verify() REJECTS a simple-mode task", "template" in str(e).lower())

        # ---- E18: MTF wiring works on BOTH donor dialects -------------------------------
        # 177 of the 232 build tasks on the reference machine carry a task-level <Datas>
        # mapping; 55 (incl. the stock 144.2953 Builder) carry none. ensure_mtf_charts used
        # to hard-fail on the second shape, so every MTF template was unwireable there — and
        # the eval hid it by excluding MTF templates from the pick entirely.
        if not mtf_tpl:
            check("E18 MTF wiring (SKIPPED: no multi-stream template on this install)", True)
        else:
            m18 = mtf_tpl[0]
            streams = _extra_streams(m18)
            # (a) the real donor, whatever shape it is
            w18 = ensure_mtf_charts(donor_bytes, m18)
            rc = re.findall(rb'<Chart name="([^"]*)"', w18)
            check("E18 MTF: RulesComplexity gains a second chart",
                  len(rc) >= 2 and any(b"chart" in c for c in rc[1:]), str(rc[:3]))
            check("E18 MTF: Setup charts gain the extra timeframe",
                  len(set(re.findall(rb'<Chart symbol="[^"]*" timeframe="([^"]*)"', w18))) >= 2,
                  str(set(re.findall(rb'<Chart symbol="[^"]*" timeframe="([^"]*)"', w18))))
            check("E18 MTF: single-stream template is still a no-op",
                  ensure_mtf_charts(donor_bytes, single_tpl[0]) == donor_bytes
                  if single_tpl else True)
            # (b) the OTHER dialect, synthesised — whichever one the donor is not
            if donor_has_datas:
                other = re.sub(rb"<Datas>.*?</Datas>", b"", donor_bytes, count=1, flags=re.S)
                lbl = "no-<Datas> donor"
            else:
                other = donor_bytes.replace(
                    b"<RulesComplexity",
                    b"<Datas>\n            <data>\n              <id>0</id>\n"
                    b"              <symbol>NULL</symbol>\n"
                    b"              <chart>Main chart</chart>\n"
                    b"              <timeFrame>0</timeFrame>\n"
                    b"            </data>\n          </Datas>\n          <RulesComplexity", 1)
                lbl = "with-<Datas> donor"
            n18 = []
            w18b = ensure_mtf_charts(other, m18, notes=n18)
            check(f"E18 MTF: also wires the other dialect ({lbl})",
                  w18b != other and len(re.findall(rb'<Chart name="([^"]*)"', w18b)) >= 2)
            if donor_has_datas:
                # the no-<Datas> path must RECORD which route it took — build-confirmed
                # 2026-07-31, so this is a note, not a warning, but it must never be silent
                check("E18 MTF: no-<Datas> path records the route it took",
                      any("Datas" in x for x in n18), str(n18))
            else:
                check("E18 MTF: with-<Datas> path inserts the second data stream",
                      re.search(rb"<timeFrame>%d</timeFrame>" % streams[0], w18b) is not None)
            # (c) a malformed <Datas> must RAISE, never be guessed at
            bad18 = donor_bytes.replace(b"<RulesComplexity", b"<Datas><garbage/><RulesComplexity", 1)
            try:
                ensure_mtf_charts(bad18, m18)
                check("E18 MTF: malformed <Datas> rejected", False, "no error raised")
            except ValueError as e:
                check("E18 MTF: malformed <Datas> rejected", "Datas" in str(e))

        # ---- E19: THE ENABLED-CONTEXT MATRIX -------------------------------------------
        # The defect class that has bitten this engine three times: a value is written into
        # a field SQX does not read, because a sibling flag/mode leaves it inert. The run
        # then reports success.  avg_trades -> <Condition use="false">;  time_minutes ->
        # <StopCondition type="databank-full">;  templateFile -> <StrategyType type="simple">.
        # Each was fixed one at a time. This table is the generalisation: every value the
        # engine writes is listed WITH the gate that governs whether SQX reads it, and both
        # are asserted on a real generated project. Adding a new writable field means adding
        # a row here — that is the point.
        e19_cfx = os.path.join(tmp, "E19", "project.cfx")
        make_project(
            base["path"], "E19",
            [{"template": picks[0], "output_db": "BS-E19", "avg_trades": 5, "time_minutes": 9}],
            out_cfx=e19_cfx,
            overrides={"trading": {"time_range": {"from": "08:00", "to": "16:00"},
                                   "friday_exit": {"enabled": True, "exit_time": "21:00"}},
                       "generation": {"databank_cap": 12345}})
        with zipfile.ZipFile(e19_cfx) as z:
            r19 = z.read("Build-Task1.xml").decode("utf-8", "replace")
        rk19 = re.search(r"<Rankings\b.*?</Rankings>", r19, re.S).group(0)
        avg19 = [c for c in re.findall(r"<Condition\b[^>]*>.*?</Condition>", rk19, re.S)
                 if 'class="AvgTradesPerMonth"' in c]

        def _param19(key):
            m = re.search(r'<Param key="%s"[^>]*>([^<]*)</Param>' % key, r19)
            return m.group(1) if m else None

        MATRIX = [
            ("templateFile",            bool(re.search(r'templateFile="[^"]*\.sqx"', r19)),
             'StrategyType type="template"',
             'type="template"' in re.search(r'<StrategyType\b[^>]*>', r19).group(0)),
            ("AvgTradesPerMonth = 5",   '"5"' in (avg19[0] if avg19 else ""),
             'enclosing <Condition use="true">',
             bool(avg19) and 'use="true"' in re.match(r"<Condition\b[^>]*>", avg19[0]).group(0)),
            ("StopCondition minutes=9", 'minutes="9"' in re.search(r'<StopCondition\b[^>]*>', r19).group(0),
             'StopCondition type="time-limit"',
             'type="time-limit"' in re.search(r'<StopCondition\b[^>]*>', r19).group(0)),
            ("SignalTimeRange 08-16",   _param19("SignalTimeRangeFrom") == str(8 * 3600),
             'Param LimitTimeRange=true',  _param19("LimitTimeRange") == "true"),
            ("FridayExitTime 21:00",    _param19("FridayExitTime") == str(21 * 3600),
             'Param ExitOnFriday=true',    _param19("ExitOnFriday") == "true"),
            ("MaxStrategies 12345",     "<MaxStrategies>12345</MaxStrategies>" in r19,
             "no gate (plain value)",      True),
        ]
        for field, written, gate_desc, gate_ok in MATRIX:
            check(f"E19 {field}: written AND its gate is live ({gate_desc})",
                  written and gate_ok, f"written={written} gate_ok={gate_ok}")

        # ---- E16 (infra): legacy install migration validates before persisting ---------
        infra = os.path.join(tmp, "infra")
        state = os.path.join(infra, "state")
        os.makedirs(infra, exist_ok=True)
        legacy = Path(infra) / "legacy-sqx-install.txt"
        old_env = os.environ.get("SQX_LAB_HOME")
        old_legacy = sqx_common.LEGACY_INSTALL_FILE
        try:
            os.environ["SQX_LAB_HOME"] = state
            sqx_common.LEGACY_INSTALL_FILE = legacy
            legacy.write_text(tmp + "\n", encoding="utf-8")   # a real dir, NOT an SQX install
            r1 = sqx_common.load_shared_install()
            persisted = (Path(state) / "sqx-install.txt").exists()
            check("E16 junk legacy install: not returned, not persisted, file left alone",
                  r1 is None and not persisted
                  and legacy.read_text(encoding="utf-8").strip() == tmp)
            legacy.write_text(install + "\n", encoding="utf-8")   # the real install
            r2 = sqx_common.load_shared_install()
            migrated = (Path(state) / "sqx-install.txt")
            check("E16 valid legacy install: returned + migrated to the state dir",
                  r2 == install and migrated.is_file()
                  and migrated.read_text(encoding="utf-8").strip() == install)
        finally:
            sqx_common.LEGACY_INSTALL_FILE = old_legacy
            if old_env is None:
                os.environ.pop("SQX_LAB_HOME", None)
            else:
                os.environ["SQX_LAB_HOME"] = old_env

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    n_fail = sum(1 for r in results if r[0] == FAIL)
    print(f"\n{'='*54}\n{len(results) - n_fail}/{len(results)} passed"
          + (f"  ({n_fail} FAILED)" if n_fail else "  — all green"))
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
