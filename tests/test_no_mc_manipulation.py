#!/usr/bin/env python3
"""MonteCarloManipulation is never switched on: the writer refuses it, the gate sees it, the fix flips only `use=`."""

import zipfile
from pathlib import Path

import pytest

from sqx.projects import cfxio, rankings, tasksettings
from sqx.projects.crosschecks import mc_manipulation_on

ON = '<CrossChecks use="true"><MonteCarloManipulation use="true"><X/></MonteCarloManipulation></CrossChecks>'


def test_set_crosschecks_refuses_it() -> None:
    """The writer refuses the name."""
    with pytest.raises(SystemExit):
        tasksettings.set_crosschecks(
            ON, {"precision": 1}, 0.0, ["MonteCarloManipulation"]
        )


def test_the_gate_helper() -> None:
    """The helper tells an XML with it on from one with it off."""
    assert mc_manipulation_on(ON)
    assert not mc_manipulation_on(
        ON.replace('Manipulation use="true"', 'Manipulation use="false"')
    )


def test_mc_off_flips_only_the_attribute(tmp_path: Path) -> None:
    """Same member list, only `use=` changes."""
    cfx = tmp_path / "project.cfx"
    with zipfile.ZipFile(cfx, "w") as z:
        z.writestr("config.xml", "<Project/>")
        z.writestr("Build-Task1.xml", ON)
        z.writestr("Retest-Task2.xml", "<T/>")
    before = cfxio.members(cfx)
    assert rankings.mc_off(cfx) == 1
    after = cfxio.members(cfx)
    assert list(after) == list(before)
    assert after["Build-Task1.xml"] == before["Build-Task1.xml"].replace(
        b'Manipulation use="true"', b'Manipulation use="false"'
    )
    assert after["Retest-Task2.xml"] == before["Retest-Task2.xml"]
