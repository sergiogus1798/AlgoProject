#!/usr/bin/env python3
"""«Continuar workflow» switches on every task of the next step that reads the cut, or what
one of them writes (📓 2026-09-30: after a cut on CrossTF only «MCR 1 Bar» ever ran)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqx.projects.stage import titles
from ui.daemon.advance.preflight import next_task


def task(title: str, source: str, output: str) -> dict:
    """One retest of the chain, as `progress.tasks` reads it."""
    return {"title": title, "type": "Retest", "input": source, "output": output}


TASKS = ([task("CrossTF", "CrossTF_Input", "CrossTF")]
         + [task(t, "CrossTF_Mothers", t) for t in titles("mcretest")]
         + [task("SPP IS", "MCR 8 Stress", "SPP IS"), task("SPP OOS", "SPP IS", "SPP OOS")])


def test_all_eight_mc_retests_run_after_crosstf() -> None:
    """The eight read the same databank: none is skipped, and the fill comes first."""
    got = next_task(TASKS, "CrossTF")
    assert got["stage"] == "mcretest" and got["fill"] == "CrossTF_Mothers"
    assert got["skip"] == []


def test_spp_oos_chains_behind_spp_is() -> None:
    """SPP OOS reads what SPP IS writes: both run in the one start."""
    got = next_task(TASKS, "MCR 8 Stress")
    assert got["task"] == "SPP IS" and got["skip"] == []


if __name__ == "__main__":
    test_all_eight_mc_retests_run_after_crosstf()
    test_spp_oos_chains_behind_spp_is()
    print("ok")
