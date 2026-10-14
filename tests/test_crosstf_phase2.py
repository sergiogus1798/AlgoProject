#!/usr/bin/env python3
"""Cross TF's phase 2 (encargo 47, part S): M15 from the doctrine, and a `build`-window twin of
every sibling timeframe, declared once in `workflow.CROSSTF_BUILD`."""

import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.assetdata import load
from sqx.projects import crosstfload, crosstfsolo
from sqx.projects.setups import set_span
from tests.test_crosstf_separate import CONFIG, TASK

DOCTRINE = {
    "engine": "MetaTrader5 (hedged)",
    "crosstf": {"timeframes": {"M30": ["M15", "H1", "H4"], "H1": ["M30", "H4"]}},
}


def test_m15_falls_out_of_the_doctrine() -> None:
    """`CrossTF M15` -> `CrossTF_M15` with no code of its own."""
    rows = {s["timeframe"]: s for s in crosstfsolo.planned("M30", d=DOCTRINE)}
    assert (
        rows["M15"]["title"] == "CrossTF M15"
        and rows["M15"]["databank"] == "CrossTF_M15"
    )
    assert rows["M15"]["engine"] == "MetaTrader5 (hedged)"


def test_no_mother_timeframe_lists_d1() -> None:
    """D1 was removed from Cross TF (owner, 2026-10-09): the live doctrine names it nowhere."""
    from core.assetdata import doctrine

    study = doctrine()["crosstf"]
    assert (
        all("D1" not in tfs for tfs in study["timeframes"].values())
        and "engines" not in study
    )


def test_phase2_names_one_twin_per_sibling_and_leave_phase1_alone() -> None:
    """One build twin per sibling; the old task regex does not see them."""
    twins = crosstfsolo.phase2("H1", d=DOCTRINE)
    assert [s["title"] for s in twins] == ["CrossTF M30 build", "CrossTF H4 build"]
    assert [s["databank"] for s in twins] == ["CrossTF_M30_build", "CrossTF_H4_build"]
    assert [s["title"] for s in crosstfsolo.phase2("M30", d=DOCTRINE)][
        0
    ] == "CrossTF M15 build"
    assert crosstfsolo.present('title="CrossTF H4 build"') == []


def test_phase2_task_is_written_over_build(tmp_path: Path) -> None:
    """The twin reads CrossTF_Input, writes its own databank, sits on `build` at build costs,
    and is listed by `phase2_tasks`; a project without twins lists none."""
    data = load("USDJPY")
    twin = set_span(TASK, data, "build")[0]
    build = data["segments"]["build"]
    members = {"config.xml": CONFIG.encode(), "Retest-Task15.xml": TASK.encode()}
    for solo in crosstfsolo.phase2("H1", d=DOCTRINE):
        crosstfsolo.write(members, twin, solo)
    cfx = tmp_path / "project.cfx"
    with zipfile.ZipFile(cfx, "w") as z:
        z.writestr("config.xml", CONFIG)
    assert crosstfload.phase2_tasks(cfx) == []  # an old project: empty, no raise
    with zipfile.ZipFile(cfx, "w") as z:
        z.writestr("config.xml", members["config.xml"])
    got = crosstfload.phase2_tasks(cfx)
    assert [(g["timeframe"], g["databank"]) for g in got] == [
        ("M30", "CrossTF_M30_build"),
        ("H4", "CrossTF_H4_build"),
    ]
    config = members["config.xml"].decode()
    assert '<Databank name="CrossTF_H4_build"' in config
    assert crosstfsolo.present(config) == []  # step 11 never lists them
    task = members[crosstfsolo.member_of(config, "CrossTF H4 build")].decode()
    assert 'name="Input" value="CrossTF_Input"' in task
    assert 'name="Output" value="CrossTF_H4_build"' in task
    assert 'timeframe="H4"' in task and '<RetestOnAdditionalMarkets use="false"' in task
    year = build["from"] if isinstance(build["from"], int) else str(build["from"])[:4]
    assert f'dateFrom="{year}.' in task


if __name__ == "__main__":
    import tempfile

    test_m15_falls_out_of_the_doctrine()
    test_no_mother_timeframe_lists_d1()
    test_phase2_names_one_twin_per_sibling_and_leave_phase1_alone()
    with tempfile.TemporaryDirectory() as tmp:
        test_phase2_task_is_written_over_build(Path(tmp))
    print("ok")
