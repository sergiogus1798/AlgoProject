#!/usr/bin/env python3
"""Known-answer test for the owner's rule 14: at most 2 entry and 2 exit conditions per strategy.

«What to build» counts per strategy in a Simple Strategy and per random hole in a template, so
`sqx.projects.buildrules.what_to_build` must write `complexity.simple` for the first and
`0..(cap − fixed)` per side for the second; `over_the_cap` must refuse two free holes on a side
and fixed conditions that leave a hole no room. The templates are built here, one signal each,
so every count is known by construction.
"""

import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.assetdata import doctrine
from sqx.projects import buildrules
from sqx.templates.holes import conditions

SKELETONS = (
    Path(__file__).resolve().parent.parent / "tools/sqx-lab/plugins/sqx-lab/skills/"
    "sqx-strategy-template/engine/skeletons"
)
COMPLEXITY = {
    "max_entry_conditions": 2,
    "max_exit_conditions": 2,
    "simple": {"entry": [1, 2], "exit": [1, 2]},
    "lookback_bars": 1,
}
FIXED = '<Block><Item key="CloseAboveEMA" categoryType="signals" /></Block>'
FREE = (
    '<Block><Item key="RandomCondition" categoryType="randomBlock">'
    '<Param key="#Group#" randomGroupType="Conditions" /></Item></Block>'
)
OTHER = FIXED.replace("CloseAboveEMA", "RSIBelowLevel")
BOUND = FREE.replace(" /></Item>", ">51a821f5-ed30</Param></Item>")
FAILURES: list[str] = []


def check(label: str, ok: bool, detail: object = "") -> None:
    """Record one assertion without stopping the run."""
    print(f"  {'ok ' if ok else 'FAIL'} {label}")
    if not ok:
        FAILURES.append(f"{label} {detail}")


def template(folder: Path, name: str, entry: str, exit_: str = "") -> Path:
    """A template .sqx whose long entry and long exit signals hold exactly these blocks."""
    exits = f'<Item key="AND">{exit_}</Item>' if exit_ else ""
    xml = (
        "<Strategy><Variables>"
        "<variable><id>e</id><name>LongEntrySignal</name></variable>"
        "<variable><id>s</id><name>ShortEntrySignal</name></variable>"
        "<variable><id>x</id><name>LongExitSignal</name></variable></Variables><signals>"
        f'<signal variable="e"><Item key="AND">{entry}</Item></signal>'
        f'<signal variable="s" /><signal variable="x">{exits}</signal>'
        "</signals></Strategy>"
    )
    path = folder / f"{name}.sqx"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("strategy_Portfolio.xml", xml)
    return path


def bounds(path: Path, exit_required: bool = False) -> dict:
    """`what_to_build` for a Build task pointed at this template."""
    task = f'<StrategyType type="template" templateFile="{path}" />'
    return buildrules.what_to_build(task, COMPLEXITY, exit_required)


def main() -> None:
    """Run every check and exit non-zero on any failure."""
    simple = (
        '<StrategyType type="simple" templateFile="SQ3StrategyTemplateExample.sq4" />'
    )
    got = buildrules.what_to_build(simple, COMPLEXITY, False)
    check(
        "Simple Strategy: entry 1..2 and exit 1..2",
        got == {"entry": (1, 2), "exit": (1, 2)},
        got,
    )
    check(
        "assets/_build.yaml declares those Simple Strategy bounds",
        doctrine()["complexity"]["simple"] == {"entry": [1, 2], "exit": [1, 2]}
        and doctrine()["complexity"]["max_entry_conditions"] == 2
        and doctrine()["complexity"]["max_exit_conditions"] == 2,
        doctrine()["complexity"],
    )

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        one = template(tmp, "one_fixed_one_hole", FIXED + FREE)
        check(
            "counts: 1 fixed + 1 free hole",
            conditions(one)["entry"] == {"fixed": 1, "bound": 0, "free": 1},
            conditions(one),
        )
        check(
            "1 fixed + 1 hole → entry 0..1", bounds(one)["entry"] == (0, 1), bounds(one)
        )
        check(
            "a template's exit stays optional, 0..2",
            bounds(one)["exit"] == (0, 2),
            bounds(one),
        )
        check(
            "…and 1..2 only when the doctrine requires the exit condition",
            bounds(one, True)["exit"] == (1, 2),
            bounds(one, True),
        )
        check(
            "1 fixed + 1 hole is accepted", not buildrules.over_the_cap(one, COMPLEXITY)
        )

        hole = template(tmp, "one_hole", FREE)
        check(
            "0 fixed + 1 hole → entry 1..2",
            bounds(hole)["entry"] == (1, 2),
            bounds(hole),
        )

        two = template(tmp, "two_fixed", FIXED + OTHER)
        check(
            "2 fixed, no hole → nothing left to draw (0..0), accepted",
            bounds(two)["entry"] == (0, 0)
            and not buildrules.over_the_cap(two, COMPLEXITY),
            bounds(two),
        )

        full = template(tmp, "two_fixed_one_hole", FIXED + OTHER + FREE)
        check(
            "2 fixed + 1 hole is refused",
            len(buildrules.over_the_cap(full, COMPLEXITY)) == 1,
        )

        twin = template(tmp, "twin_fixed_one_hole", FIXED + FIXED + FREE)
        check(
            "the same condition twice is one idea (owner, 2026-10-05): 1 fixed, hole 0..1, accepted",
            conditions(twin)["entry"]["fixed"] == 1
            and bounds(twin)["entry"] == (0, 1)
            and not buildrules.over_the_cap(twin, COMPLEXITY),
            conditions(twin),
        )

        free = template(tmp, "two_holes", FREE + FREE)
        check(
            "two free holes on a side are refused",
            len(buildrules.over_the_cap(free, COMPLEXITY)) == 1,
        )

        tied = template(tmp, "bound_plus_hole", BOUND + FREE)
        check(
            "counts: a hole tied to a group is `bound`, not free",
            conditions(tied)["entry"] == {"fixed": 0, "bound": 1, "free": 1},
            conditions(tied),
        )
        check(
            "1 bound + 1 hole → 1..1 (never 0: SQX fills the bound hole by the same range)",
            bounds(tied)["entry"] == (1, 1)
            and not buildrules.over_the_cap(tied, COMPLEXITY),
            bounds(tied),
        )

        exits = template(tmp, "exit_fixed_hole", FIXED + FREE, FIXED + FREE)
        check(
            "same arithmetic on the exit side: 1 fixed + 1 hole → 0..1",
            bounds(exits)["exit"] == (0, 1),
            bounds(exits),
        )
        over = template(tmp, "exit_two_holes", FIXED, FREE + FREE)
        check(
            "two free exit holes are refused, naming the side",
            ["exit" in line for line in buildrules.over_the_cap(over, COMPLEXITY)]
            == [True],
        )

    three = SKELETONS / "role_market_skeleton.sqx"
    check(
        "a real skeleton with three conditions on a side is refused",
        conditions(three)["entry"]["bound"] == 3
        and len(buildrules.over_the_cap(three, COMPLEXITY)) == 1,
        conditions(three),
    )

    if FAILURES:
        raise SystemExit("\n".join(["", f"{len(FAILURES)} FAILED"] + FAILURES))
    print("all ok")


if __name__ == "__main__":
    main()
