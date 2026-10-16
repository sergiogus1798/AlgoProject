#!/usr/bin/env python3
"""Zero survivors end the autopilot cleanly, a missing fact goes where its rule says, the judge
signs its cut in the ledger with criteria.yaml's hash, and `live.wait` fails on an abort line
instead of returning it. All on fakes: no SQX, no install, no ledger on disk."""

import hashlib
import sys
import tempfile
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.autopilot import criteria, judge, run, selection
from sqx.projects import live
from tests.test_autopilot_tail import patched


def test_a_missing_fact_goes_where_its_rule_says() -> None:
    """No `missing:` is limbo as before; `missing: fail` and `missing: pass` are obeyed."""
    for said, want in ((None, "limbo"), ("fail", "fail"), ("pass", "pass")):
        rule = {"fact": "k", "pass": ">= 1"} | ({"missing": said} if said else {})
        assert criteria.judged(rule, {}, "a", {})[0] == want


def test_a_judged_step_with_cut_null_annotates_and_cuts_nothing() -> None:
    """`cut: null` with rules: the verdict is returned, the ledger row written, apply_verdict never called."""
    rows = []
    cfg = {
        "steps": {
            "17": {
                "cut": None,
                "segment": "oos2",
                "rules": [{"fact": "k", "pass": ">= 1", "else": "fail"}],
            },
            "16": {"cut": "SPP OOS"},
        }
    }
    pop = pd.DataFrame([{"strategy": "S1", "identity": "i1"}])
    found = pd.DataFrame(
        [{"strategy": "S1", "identity": "i1", "key": "k", "value": 0.0}]
    )
    about = {"symbol": "XAUUSD", "timeframe": "H1", "family": "mono"}

    def never(*a) -> None:
        """A cut: forbidden here."""
        raise AssertionError("cut called")

    with (
        tempfile.TemporaryDirectory() as tmp,
        patched(judge.facts, gather=lambda p, n: found),
        patched(judge, population=lambda *a: pop, tags=lambda p: set()),
        patched(judge.apply_verdict, apply=never),
        patched(judge.survivors, about=lambda p: about),
        patched(judge.record, log=lambda sid, row: rows.append(row)),
    ):
        got = judge.judge("Test_x", "17", "custodian", Path(tmp) / "p17", cfg)
        assert got["before"] == got["after"] == 1 and "anota" in got["corte"]
        assert (
            "fail" in (Path(tmp) / "p17" / "verdict.csv").read_text()
            and rows[0]["n_out"] == 1
        )


def test_a_step_without_rules_still_signs_a_row_that_cuts_nothing() -> None:
    """S4 A (owner, 2026-10-16): 11.5, 16 and 16.5 leave their ledger row, n_in == n_out."""
    rows = []
    cfg = {"steps": {"16": {"segment": "build"}}}
    found = pd.DataFrame(
        [{"strategy": s, "identity": s, "key": "k", "value": 0.0} for s in "AAB"]
    )
    about = {"symbol": "XAUUSD", "timeframe": "H1", "family": "mono"}
    with (
        tempfile.TemporaryDirectory() as tmp,
        patched(judge.facts, gather=lambda p, n: found),
        patched(judge, tags=lambda p: set()),
        patched(judge.survivors, about=lambda p: about),
        patched(judge.record, log=lambda sid, row: rows.append(row)),
    ):
        judge.judge("Test_x", "16", "custodian", Path(tmp) / "p16", cfg)
    assert [(r["step"], r["segment"], r["n_in"], r["n_out"]) for r in rows] == [
        (16.0, "build", 2, 2)
    ]


def test_the_judge_that_cuts_everybody_signs_the_ledger_and_the_run_ends_in_fin() -> (
    None
):
    """Zero left after the cut: one ledger row with the file's hash, then FIN, no fallo.md."""
    rows = []
    cfg = {
        "steps": {
            "8": {
                "cut": "OOS",
                "segment": "oos1",
                "rules": [{"fact": "k", "pass": ">= 1", "else": "fail"}],
            }
        }
    }
    pop = pd.DataFrame([{"strategy": "S1", "identity": "i1"}])
    found = pd.DataFrame(
        [{"strategy": "S1", "identity": "i1", "key": "k", "value": 0.0}]
    )
    about = {"symbol": "XAUUSD", "timeframe": "H1", "family": "mono"}
    with (
        tempfile.TemporaryDirectory() as tmp,
        patched(judge.facts, gather=lambda p, n: found),
        patched(judge, population=lambda *a: pop, tags=lambda p: set()),
        patched(judge.apply_verdict, apply=lambda *a: {"before": 1, "after": 0}),
        patched(judge.survivors, about=lambda p: about),
        patched(judge.record, log=lambda sid, row: rows.append((sid, row))),
    ):
        got = judge.judge("Test_x", "8", "custodian", Path(tmp) / "p8", cfg)
        assert got["after"] == 0
        assert (
            rows[0][0] == "XAUUSD_H1_mono"
            and rows[0][1]["n_in"] == 1
            and rows[0][1]["n_out"] == 0
        )
        assert (
            rows[0][1]["config_hash"]
            == hashlib.sha256(judge.CRITERIA.read_bytes()).hexdigest()
        )

        started = []
        todo = {
            "do": [
                {"n": "8", "title": "j", "kind": "judge", "tests": []},
                {"n": "9", "title": "s", "kind": "sqx", "steps": [], "tests": []},
            ],
            "stop": {"n": "26", "why": "x"},
        }
        out = Path(tmp)
        with (
            patched(
                run.advance, where=lambda p: {"role": "custodian"}, busy=lambda *a: []
            ),
            patched(run.workflow, workflow=lambda p: {"asset": "X"}),
            patched(run.plan, plan=lambda data, given: todo),
            patched(run.judge, judge=lambda *a: got, settings=lambda: cfg),
            patched(run, sqx_step=lambda *a: started.append(a)),
        ):
            run.autopilot("Test_x", out)
        assert started == [] and not (out / "fallo.md").exists()
        assert "no dejó ninguna superviviente" in (out / "resumen.md").read_text()
        assert (out / "estado.txt").read_text().split(" ", 1)[1].startswith("FIN")


def test_wait_fails_on_the_abort_line_instead_of_returning_it() -> None:
    """«Error while running project», «Exception in task» and «Project stopped» end the wait in SystemExit."""
    for line in (
        "Error while running project",
        "Exception in task X",
        "Project stopped",
    ):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "log_2026_01_01.log"
            log.write_text(f"10:00 {line}\n")
            began = time.monotonic()
            with patched(live, _up=lambda role: True, _log=lambda role: log):  # noqa: B023 called this iteration
                try:
                    live.wait("custodian", (log, 0))
                except SystemExit as e:
                    assert line in str(e)
                else:
                    raise AssertionError(line)
            assert time.monotonic() - began < 2


def test_resume_takes_only_whole_strategies_of_that_project() -> None:
    """`resume.chosen`: a word naming none or two, a torn strategy, another project's and two
    of one name are each refused before any project is rebuilt."""
    from pipeline.autopilot import resume

    store = {
        "a": ["A1"],
        "b": ["B1"],
        "two": ["A1", "B1"],
        "torn": ["T1"],
        "other": ["O1"],
    }
    origin = {
        "A1": ("P", "S 1"),
        "B1": ("P", "S 1"),
        "T1": ("P", "S 2"),
        "O1": ("Q", "S 3"),
    }
    was = resume.store.resolve, resume.verify.check, resume.write.manifest
    resume.store.resolve = lambda token: store.get(token, [])
    resume.verify.check = lambda identity: ["sin trades"] if identity == "T1" else []
    resume.write.manifest = lambda identity: {
        "origin": dict(zip(("project", "strategy"), origin[identity]))
    }
    try:
        assert resume.chosen(["a"], "P") == {"A1": "S 1"}
        for words, said in (
            (["none"], "nombra 0"),
            (["two"], "nombra 2"),
            (["torn"], "no está entera"),
            (["other"], "salió de Q"),
            (["a", "b"], "mismo nombre"),
        ):
            try:
                resume.chosen(words, "P")
            except SystemExit as e:
                assert said in str(e), e
            else:
                raise AssertionError(f"{words} was taken")
    finally:
        resume.store.resolve, resume.verify.check, resume.write.manifest = was


if __name__ == "__main__":
    test_a_missing_fact_goes_where_its_rule_says()
    test_the_judge_that_cuts_everybody_signs_the_ledger_and_the_run_ends_in_fin()
    test_wait_fails_on_the_abort_line_instead_of_returning_it()
    test_resume_takes_only_whole_strategies_of_that_project()


def test_largest_keeps_the_top_groups() -> None:
    """Five groups: the 4 largest keep their medoid; the size tie goes to the first group name."""
    card = pd.DataFrame(
        {
            "strategy": list("abcde"),
            "medoide": True,
            "redundancia_value": [3, 2, 2, 2, 2],
            "redundancia_grupo": list("abcde"),
        }
    )
    assert list(selection.largest(card, 4)["strategy"]) == list("abcd")
