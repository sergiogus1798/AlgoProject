#!/usr/bin/env python3
"""Step 13 since 2026-10-07: the autopilot plans T1's neighbour batch right before the MC Retest
tasks and after step 12's judge, hands it the mothers CrossTF holds (never a scaled sibling); the
stage runs only MCR 1, 4 and 7; and the databank step 14 cuts is the one a project built from the
frozen donor makes «SPP IS» read. All offline: no SQX, no install."""

import sys
import zipfile
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.autopilot import judge, neighbours, plan, survivors, tailrun
from sqx.inspect.keep_tasks import keep
from sqx.projects import builder, crosstfload, stage, workflow as wf
from sqx.projects.databanks import chain_databanks
from ui.daemon.workflow.steps import STEPS

NS = [s["n"] for s in STEPS]


def rail(done_to: str, last: str = "15") -> dict:
    """The rail up to `last` as GET /api/workflow gives it: done up to `done_to`, then pending."""
    out = [{**spec, "state": "done" if NS.index(spec["n"]) <= NS.index(done_to) else "pending",
            "tests": [{"key": k, "runnable": True, "auto": True, "state": "pending"}
                      for k in spec["studies"]]} for spec in STEPS[:NS.index(last) + 1]]
    return {"steps": out, "family": "fam"}


def kinds(todo: dict) -> list[tuple[str, str]]:
    """The plan's `do` as (step, kind)."""
    return [(a["n"], a["kind"]) for a in todo["do"]]


def test_t1_runs_after_step_12s_judge_and_before_the_mc_retest() -> None:
    """12 judged, then the neighbours, the MCR tasks, the study, its judge, and only then SPP."""
    assert kinds(plan.plan(rail("11.7"))) == [
        ("12", "python"), ("12", "judge"), ("13", "neighbours"), ("13", "sqx"),
        ("14", "python"), ("14", "judge"), ("15", "sqx")]


def test_a_step_13_already_done_plans_no_neighbours() -> None:
    """T1 belongs to step 13's run: with 13 done, 14 is studied and judged on what there is."""
    assert kinds(plan.plan(rail("13"))) == [("14", "python"), ("14", "judge"), ("15", "sqx")]


def test_the_dispatch_hands_t1_the_mothers_crosstf_holds(monkeypatch: pytest.MonkeyPatch,
                                                         tmp_path: Path) -> None:
    """`tailrun` runs the kind; a scaled sibling never enters; nobody left is a clean stop."""
    for name in ("Strategy 1.2.3", "Strategy 1.2.3_ScaledH4", "Strategy 4.5.6"):
        (tmp_path / f"{name}.sqx").write_bytes(b"")
    monkeypatch.setattr(neighbours, "databank_dir", lambda project, bank, install: tmp_path)
    monkeypatch.setattr(neighbours.apply_verdict, "install_of", lambda role: tmp_path)
    seen = {}
    monkeypatch.setattr(neighbours, "run", lambda project, role, mothers, stamp: seen.update(
        mothers=list(mothers["strategy"]), files=list(mothers["file"]), stamp=stamp) or "hecho")
    assert "neighbours" in tailrun.KINDS
    said = tailrun.run({"n": "13", "kind": "neighbours", "tests": []}, "P", "custodian",
                       tmp_path / "20261007-120000", {})
    assert said == "hecho" and seen["stamp"] == "20261007-120000"
    assert seen["mothers"] == ["Strategy 1.2.3", "Strategy 4.5.6"]
    assert all(f.exists() for f in seen["files"])
    for f in tmp_path.glob("Strategy [14]*.sqx"):
        f.unlink()
    with pytest.raises(survivors.Done):
        neighbours.entering("P", "custodian")


def test_the_stage_runs_three_tasks_and_step_14_cuts_what_spp_reads() -> None:
    """MCR 1, 4, 7 in the stage; from the frozen donor, «SPP IS» reads the last of them, which
    is criteria.yaml's `cut` of step 14; every MCR task reads the mothers and writes its own."""
    assert stage.titles("mcretest") == ["MCR 1 Bar", "MCR 4 MinDist", "MCR 7 OHLC"]
    with zipfile.ZipFile(builder.DONOR) as z:
        members = {n: z.read(n) for n in z.namelist()}
    members, _ = keep(members, {"Build", "Retest"},
                      only=wf.kept_members(members["config.xml"].decode("utf-8")))
    wf.complete(members)
    chain_databanks(members)
    wf.rewire(members)
    io = crosstfload.banks(members)
    cut = yaml.safe_load(judge.CRITERIA.read_text(encoding="utf-8"))["steps"]["14"]["cut"]
    assert io["SPP IS"]["Input"] == cut == "MCR 7 OHLC"
    assert [t for t in io if t.startswith("MCR")] == stage.titles("mcretest")
    for title in stage.titles("mcretest"):
        assert io[title] == {"Input": "CrossTF_Mothers", "Output": title}, io[title]
    assert io["SPP OOS"]["Input"] == "SPP IS"


if __name__ == "__main__":
    test_t1_runs_after_step_12s_judge_and_before_the_mc_retest()
    test_a_step_13_already_done_plans_no_neighbours()
    test_the_stage_runs_three_tasks_and_step_14_cuts_what_spp_reads()
    print("ok (the dispatch test needs pytest)")
