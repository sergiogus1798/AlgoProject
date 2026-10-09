#!/usr/bin/env python3
"""Steps 11 -> 11.5 -> 11.7 -> 12 (encargo 47, part P): the autopilot's plan and the window's chain
with and without the build-window twins, a sibling leaving only with its mother, the `crossTF.tf.*`
facts and their state encoding, the rules' vocabulary, and where the build trades are looked for.
All on fakes: no SQX, no install."""

import json
import sys
import zipfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.autopilot import criteria, judge, plan, tffacts
from sqx.projects import cfxio, workflow as wf
from sqx.projects.workflow import CROSSTF_BUILD
from studies.transfer.crossTF.tf import inputs as tfinputs
from ui.daemon.launch import chainplan, steps as launchsteps
from ui.daemon.results import tfrows
from ui.daemon.workflow import derive
from ui.daemon.workflow.steps import STEPS

TWINS = ["CrossTF M15 build", "CrossTF H1 build"]
RULE = {"fact": "crossTF.tf.state", "pass": ">= 1", "limbo": ">= 0"}


def rail(titles: list[str] | None, last: str = "12") -> dict:
    """The rail from step 10.5 to `last` as GET /api/workflow gives it: all done up to the 10.5,
    the rest pending, 11.7 carrying its `titles`, every Python step with its one runnable test."""
    out = []
    for spec in STEPS[:[s["n"] for s in STEPS].index(last) + 1]:
        done = [s["n"] for s in STEPS].index(spec["n"]) <= [s["n"] for s in STEPS].index("10.5")
        row = {**spec, "state": "done" if done else "pending", "tests": [
            {"key": k, "runnable": True, "auto": True, "state": "pending"}
            for k in spec["studies"]]}
        out.append(row | ({"titles": titles} if spec["n"] == "11.7" and titles is not None else {}))
    return {"steps": out, "family": "fam"}


def kinds(todo: dict) -> list[tuple[str, str]]:
    """The plan's `do` as (step, kind)."""
    return [(a["n"], a["kind"]) for a in todo["do"]]


def test_the_cascade_runs_in_order_when_the_project_has_the_twins() -> None:
    """11 sqx, 11.5 python then its judge BEFORE 11.7, 11.7 sqx, 12 python and its judge."""
    todo = plan.plan(rail(TWINS))
    assert kinds(todo) == [("11", "sqx"), ("11.5", "python"), ("11.5", "judge"), ("11.7", "sqx"),
                           ("12", "python"), ("12", "judge")]
    assert todo["skipped"] == []


def test_a_project_without_twins_skips_11_7_with_one_line_and_still_judges_both() -> None:
    """No `titles` (an old project, or none at all): 11.7 is skipped, the 11.5 judge is not lost."""
    for titles in ([], None):
        todo = plan.plan(rail(titles))
        assert kinds(todo) == [("11", "sqx"), ("11.5", "python"), ("11.5", "judge"),
                               ("12", "python"), ("12", "judge")]
        assert [s["n"] for s in todo["skipped"]] == ["11.7"] and "fase 2" in todo["skipped"][0]["why"]


def test_the_windows_chain_stops_after_11_5_and_skips_11_7_when_there_are_no_twins() -> None:
    """With twins the window stops before 11.7 (11.5 judges); without, it walks on to 12."""
    with_twins = chainplan.plan(rail(TWINS))
    assert [(a["n"], a["kind"]) for a in with_twins["do"]] == [("11", "sqx"), ("11.5", "python")]
    assert with_twins["stop"]["n"] == "11.7"
    without = chainplan.plan(rail([]))
    assert [a["n"] for a in without["do"]] == ["11", "11.5", "12"]
    assert "11.7" not in {a["n"] for a in without["do"]}


def cfx_with(tmp_path: Path, titles: list[str]) -> Path:
    """A project.cfx whose config.xml carries these task titles."""
    cfx = tmp_path / "project.cfx"
    with zipfile.ZipFile(cfx, "w") as z:
        z.writestr("config.xml", "".join(f'<Task title="{t}" />' for t in ["CrossTF", *titles]))
    return cfx


def test_step_11_7_takes_its_titles_from_the_project_and_refuses_an_old_one(tmp_path: Path) -> None:
    """`of_step` lists the twins in config order; none -> a refusal, never an exception; the
    rail row says it does not apply and carries an empty `titles`."""
    (tmp_path / "new").mkdir()
    (tmp_path / "old").mkdir()
    new, old = cfx_with(tmp_path / "new", TWINS), cfx_with(tmp_path / "old", [])
    assert launchsteps.of_step(CROSSTF_BUILD["step"], new) == {"titles": TWINS, "off": {}}
    assert "no aplica" in launchsteps.of_step(CROSSTF_BUILD["step"], old)["refuse"]
    ctx = {"sqx": {"folder": old.parent, "tasks": [], "banks": {}, "runs": [], "run": {}}}
    got = derive.phase2({"n": "11.7"}, ctx)
    assert got["titles"] == [] and got["state"] == "done" and "fase 2" in got["why"]


def test_a_sibling_leaves_with_its_mother_at_11_5_and_always_at_12() -> None:
    """`siblings: follow`: a sibling takes its mother's outcome, «(1)» copies too; absent, every
    sibling is a fail — as at step 12 today."""
    pop = pd.DataFrame({"strategy": ["M1", "M1_ScaledH1", "M2", "M2_ScaledH1(1)"],
                        "who": ["M1", "M1_ScaledH1", "M2", "M2_ScaledH1(1)"]})
    is_sibling = pop["strategy"].str.contains("_Scaled")
    judged = {"M1": ("pass", ""), "M2": ("fail", "fail: x")}
    follow = judge.siblings(pop, is_sibling, judged, True)
    assert follow == {"M1_ScaledH1": ("pass", ""), "M2_ScaledH1(1)": ("fail", "fail: x")}
    assert {s for s, (st, _) in judge.siblings(pop, is_sibling, judged, False).items()} == set(follow)
    assert all(st == "fail" for st, _ in judge.siblings(pop, is_sibling, judged, False).values())


def write_run(folder: Path) -> None:
    """The two files the study writes, for two mothers: A measured, B never reached the build."""
    pd.DataFrame({"strategy": ["A", "B"], "identity": ["ia", "ib"], "source_tf": ["M30"] * 2,
                  "t1": ["pass", "limbo"], "t2a": ["pass", "fail"], "t2b": ["pass", ""],
                  "t3": ["pass", "pass"], "phase1": ["pass", "fail"], "state": ["pass", "fail"],
                  "why": ["", "t2a"], "seed": [7, 7], "draws": [5000, 5000]}
                 ).to_csv(folder / "tf_mothers.csv", index=False)
    pd.DataFrame({"mother": ["A", "A", "B"], "sibling": ["A_ScaledM15", "A_ScaledH1", "B_ScaledH1"],
                  "timeframe": ["M15", "H1", "H1"], "role": ["scaled"] * 3,
                  "clamped": [False, False, True], "t0": ["pass", "pass", "limbo"],
                  "z_delta": [0.4, -0.2, float("nan")], "z_build": [2.1, None, None],
                  "t2a_why": ["", "", "few_trades"]}).to_parquet(folder / "tf_siblings.parquet")


def test_the_tf_facts_encode_states_as_numbers_and_a_missing_file_gives_none(tmp_path: Path) -> None:
    """pass 1, limbo 0, fail -1; a state the study left empty and a NaN are no fact; text `why`
    columns are no fact; the keys are `tf.<col>` and `tf.<TF>.<col>`; no files, no facts."""
    assert tffacts.rows(tmp_path) == []
    write_run(tmp_path)
    got = {(r["strategy"], r["key"]): r["value"] for r in tffacts.rows(tmp_path)}
    assert got[("A", "tf.state")] == 1.0 and got[("B", "tf.state")] == -1.0
    assert got[("B", "tf.t1")] == 0.0 and ("B", "tf.t2b") not in got
    assert got[("A", "tf.M15.z_delta")] == 0.4 and ("B", "tf.H1.z_delta") not in got
    assert got[("B", "tf.H1.clamped")] == 1.0 and got[("A", "tf.H1.t0")] == 1.0
    assert not any(k.endswith("_why") for _, k in got) and all(isinstance(v, float) for v in got.values())


def test_the_pasted_rule_reads_the_encoded_states() -> None:
    """The «Paquete del corte» rule shape: 1 passes, 0 is limbo, -1 fails, no fact is limbo."""
    assert [criteria.one(v, RULE, 0.0) for v in (1.0, 0.0, -1.0)] == ["pass", "limbo", "fail"]
    wide = pd.DataFrame({"who": ["A"], "key": ["crossTF.tf.state"], "value": [-1.0]})
    assert criteria.outcomes(wide, ["A", "ghost"], [RULE])["A"][0] == "fail"
    assert criteria.outcomes(wide, ["A", "ghost"], [RULE])["ghost"][0] == "limbo"


def test_the_window_rows_gain_tf_columns_only_when_the_run_has_the_files(tmp_path: Path) -> None:
    """`tfrows.merge`: untouched without the files; with them each row of a mother and a timeframe
    gets her state and her sibling's numbers, empty where there is none."""
    rows = [{"mother": "A", "timeframe": "M15"}, {"mother": "B", "timeframe": "H1"}]
    assert tfrows.merge(rows, tmp_path) == rows
    write_run(tmp_path)
    got = tfrows.merge(rows, tmp_path)
    assert got[0]["tf_state"] == "pass" and got[0]["tf_z_delta"] == "0.4" and got[1]["tf_state"] == "fail"
    assert got[1]["tf_z_delta"] == "" and got[1]["tf_t0"] == "limbo"


def test_the_build_databanks_are_found_without_a_build_databanks_entry(tmp_path: Path) -> None:
    """blocks.json written at fabrication names the timeframes only: the twins' databanks come
    from `CROSSTF_BUILD`; an explicit entry wins; no file, none."""
    assert tfinputs.build_banks(tmp_path) == {}
    blocks = {"blocks": ["M30", "M15", "H1", "H4"]}
    (tmp_path / "blocks.json").write_text(json.dumps(blocks), encoding="utf-8")
    assert tfinputs.build_banks(tmp_path) == {tf: f"CrossTF_{tf}_build" for tf in ("M15", "H1", "H4")}
    (tmp_path / "blocks.json").write_text(json.dumps(blocks | {"build_databanks": {"H1": "X"}}),
                                          encoding="utf-8")
    assert tfinputs.build_banks(tmp_path) == {"H1": "X"}


def test_the_rail_row_and_the_criteria_know_the_new_steps() -> None:
    """11.5 judges (and cuts nothing: no rules, CrossTF_Input, siblings follow); 11.7 is the
    one SQX step with no stage, and is not in stages.yaml."""
    cfg = judge.settings()["steps"]["11.5"]
    assert cfg["rules"] == [] and cfg["cut"] == "CrossTF_Input" and cfg["siblings"] == "follow"
    assert "11.5" in chainplan.JUDGES and "stage" not in {s["n"]: s for s in STEPS}["11.7"]
    assert [s["n"] for s in STEPS if s["n"].startswith("11")] == ["11", "11.5", "11.7"]


def test_a_rerun_runs_the_tests_a_failed_step_8_left_before_its_judge() -> None:
    """Step 8 reads done by its evidence once the gate wrote, though a later test failed the
    run: the rerun runs what is still pending there, then judges (2026-10-07: it went straight
    to the judge)."""
    steps = []
    for spec in STEPS[:[s["n"] for s in STEPS].index("9") + 1]:
        state = lambda k: "done" if k == "gate" else "pending"
        steps.append({**spec, "state": "pending" if spec["n"] == "9" else "done", "stage": "x",
                      "tests": [{"key": k, "runnable": True, "auto": True, "state": state(k)}
                                for k in spec["studies"] + (["monkey"] if spec["n"] == "8" else [])]})
    todo = plan.plan({"steps": steps, "family": "fam"})["do"]
    assert [(a["n"], a["kind"]) for a in todo[:3]] == [("8", "python"), ("8", "judge"), ("9", "sqx")]
    assert "monkey" in todo[0]["tests"] and "gate" not in todo[0]["tests"]


def test_a_project_trimmed_to_crosstf_ends_at_the_12_judge(tmp_path: Path) -> None:
    """`workflow.trim` drops the tasks of the later steps, and the plan ends before the 13
    (state `missing`) with the 12 judged — no T1 neighbours, no MC Retest."""
    task = '  <Task type="Retest" active="false" taskXMLFile="{f}" title="{t}" />\n'
    kept, cut = ["OOS", "CrossTF", "CrossTF H1 build"], ["MCR 7 OHLC", "SPP IS", "WFM", "WFC 1 IS"]
    files = {t: f"Retest-Task{i}.xml" for i, t in enumerate(kept + cut)}
    config = "<Project><Tasks>\n" + "".join(task.format(f=f, t=t) for t, f in files.items()) + "</Tasks></Project>"
    cfx = tmp_path / "project.cfx"
    with zipfile.ZipFile(cfx, "w") as z:
        z.writestr("config.xml", config)
        for f in files.values():
            z.writestr(f, "<x/>")
    assert wf.trim(cfx, "crosstf") == cut
    left = cfxio.members(cfx)
    assert sorted(left) == sorted(["config.xml"] + [files[t] for t in kept])
    assert all(t not in left["config.xml"].decode() for t in cut)

    data = rail(TWINS, last="13")
    data["steps"][-1]["state"] = "missing"
    todo = plan.plan(data)
    assert kinds(todo)[-2:] == [("12", "python"), ("12", "judge")] and todo["stop"]["n"] == "13"
    assert all(kind != "neighbours" for _, kind in kinds(todo))
