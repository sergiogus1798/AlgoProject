#!/usr/bin/env python3
"""A Simple Strategy project straight out of `builder.build`: its shape, the owner's genetic block
verbatim, its random-generation twin, and the owner's rule 15 on its building blocks.

Built into a temp install from the frozen donor (no SQX install touched), then read back with
`sqx.projects.buildcensus.census` — the same count the calibration study runs on every population.
The genetic values are the owner's of 2026-10-02 (`sqx/projects/buildmode_model.xml`): this test
states them a second time on purpose, so a change to that file cannot pass unnoticed.
"""

import re
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.datapaths import projects_backup
from core.paths import TAXONOMY
from sqx.blocks import palette
from sqx.blocks.taxonomy import flat, read
from sqx.projects import buildcensus, builder, buildingblocks, tasksettings

DONOR = projects_backup("XAUUSD_base_2026-09-21") / "project.cfx"
OWNER = {
    "PopulationSize": "250",
    "MaxGenerations": "25",
    "CrossoverProbability": "89",
    "MutationProbability": "20",
    "Islands": "20",
    "MigrationModulo": "10",
    "MigrationRate": "3",
    "FreshBloodWeakestPct": "5",
    "FreshBloodWeakestGenerations": "10",
    "InitialPopulationConditions": 0,
    "EvoRestartOnFinish": "status=true",
    "EvoRestartOnStagnation": "status=true fitnessType=11 generations=5",
}
FAILURES: list[str] = []


def check(label: str, ok: bool, detail: object = "") -> None:
    """Record one assertion without stopping the run."""
    print(f"  {'ok ' if ok else 'FAIL'} {label}")
    if not ok:
        FAILURES.append(f"{label} {detail}")


def buildmode(cfx: Path) -> str:
    """The `<BuildMode>` block of a project's Build task, whitespace collapsed."""
    with zipfile.ZipFile(cfx) as z:
        text = z.read("Build-Task3.xml").decode("utf-8")
    return re.sub(r">\s+<", "><", tasksettings.BUILDMODE.search(text).group(0))


def switch_everything_on(cfx: Path) -> dict:
    """Ask `rewrite` for every block of the taxonomy, as a careless palette would."""
    wanted = {key: {"use": True, "weight": 1} for key in flat(read(TAXONOMY))}
    with zipfile.ZipFile(cfx) as z:
        members = {n: z.read(n) for n in z.namelist()}
    text, got = buildingblocks.rewrite(
        members["Build-Task3.xml"].decode("utf-8"), wanted
    )
    members["Build-Task3.xml"] = text.encode("utf-8")
    with zipfile.ZipFile(cfx, "w", zipfile.ZIP_DEFLATED) as z:
        for n, blob in members.items():
            z.writestr(n, blob)
    return got


def main() -> None:
    """Run every check and exit non-zero on any failure."""
    model = re.sub(
        r">\s+<",
        "><",
        tasksettings.BUILDMODE.search(
            tasksettings.BUILDMODE_MODEL.read_text(encoding="utf-8")
        ).group(0),
    )
    with tempfile.TemporaryDirectory(prefix="sqx-test-install-") as install:
        builder.worker_dir = lambda role: Path(install)
        common = dict(
            template=None,
            symbol="XAUUSD",
            role="conductor",
            timeframe="H1",
            strategies=50,
            minutes=5,
            donor=DONOR,
            tasks=("Build", "Retest"),
            acceptance="calibration",
        )

        print("a Simple Strategy project, long, genetic")
        done = builder.build(name="Test_fixture_simple_long", side="long", **common)
        cfx = Path(done["cfx"])
        c = buildcensus.census(cfx)
        check(
            "StrategyType simple, no template named, the gate does not call it ignored",
            c["strategy_type"] == "simple"
            and c["no_template_named"]
            and not done["template_ignored"],
            c["strategy_type"],
        )
        check(
            "one direction: long, both symmetries off",
            c["sides"] == "long"
            and c["symmetry"] == {"EntrySymmetry": "false", "ExitSymmetry": "false"},
            c["sides"],
        )
        check(
            "«What to build» entry 1..2 and exit 1..2",
            (c["entry"], c["exit"]) == ([1, 2], [1, 2]),
            (c["entry"], c["exit"]),
        )
        check(
            "market orders only",
            c["order_types"] == ["EnterAtMarket"],
            c["order_types"],
        )
        check(
            "exits: bars always, rule sometimes, nothing else",
            set(c["exit_types"]) == {"ExitAfterBars.ExitAfterBars", "_ExitRule_"}
            and c["exit_types"]["ExitAfterBars.ExitAfterBars"] == 100,
            c["exit_types"],
        )
        check(
            "the Build's <BuildMode> is the owner's model, verbatim",
            buildmode(cfx) == model,
        )
        wrong = {
            k: c["genetic"].get(k) for k, v in OWNER.items() if c["genetic"].get(k) != v
        }
        check(
            "…and carries his values: 250 × 20 islands, 25 generations, 89/20, migration 10/3, "
            "fresh blood 5/10, restarts, no initial-population condition",
            not wrong,
            wrong,
        )
        check(
            "genetic evolution, fitness Ret/DD",
            c["generation"] == "genetic-evolution" and c["fitness"] == "ReturnDDRatio",
            (c["generation"], c["fitness"]),
        )
        check(
            "calibration acceptance: trades >= 100 and net profit > 0, in sample",
            c["acceptance"]
            == ["NumberOfTrades >= 100 @sampleType 10", "NetProfit > 0 @sampleType 10"],
            c["acceptance"],
        )

        print("rule 15 on its building blocks")
        got = switch_everything_on(cfx)
        c = buildcensus.census(cfx)
        check(
            "asked for everything: no stop/limit level and no clock block comes on",
            c["blocks"]["level"]["on"] == 0 and c["blocks"]["clock"]["on"] == 0,
            c["blocks"],
        )
        check(
            "…the conditions and values do, and the refusals are reported",
            c["blocks"]["condition"]["on"] > 500
            and c["blocks"]["value"]["on"] > 100
            and len(got["refused"])
            == c["blocks"]["level"]["of"] + c["blocks"]["clock"]["of"],
            (c["blocks"], len(got["refused"])),
        )
        names = [
            p["name"]
            for p in palette.catalogue()
            if p["unlabelled"] == "off" and p["overrides"]
        ][:2]
        each = [
            {
                k
                for k, r in palette.resolve(
                    palette.load(n), flat(read(TAXONOMY))
                ).items()
                if r["use"]
            }
            for n in names
        ]
        both = {k for k, r in buildingblocks.union(names).items() if r["use"]}
        check(
            f"union of two palettes ({' + '.join(names)}) is on where either is",
            both == each[0] | each[1],
            (len(both), len(each[0] | each[1])),
        )
        applied = buildingblocks.apply(cfx, ",".join(names))["tasks"]["Build-Task3.xml"]
        c = buildcensus.census(cfx)
        check(
            "…and applied, the Build carries those blocks less what rule 15 refuses",
            sum(b["on"] for b in c["blocks"].values()) == applied["on"]
            and c["blocks"]["level"]["on"] == 0
            and c["blocks"]["clock"]["on"] == 0,
            c["blocks"],
        )

        print("its random-generation twin, short")
        twin = builder.build(
            name="Test_fixture_simple_short_rnd",
            side="short",
            generation="random-generation",
            **common,
        )
        c = buildcensus.census(Path(twin["cfx"]))
        check("one direction: short", c["sides"] == "short", c["sides"])
        check(
            "random generation", c["generation"] == "random-generation", c["generation"]
        )
        check(
            "nothing else of the owner's block changed",
            buildmode(Path(twin["cfx"]))
            == model.replace("genetic-evolution", "random-generation"),
        )

    if FAILURES:
        raise SystemExit("\n".join(["", f"{len(FAILURES)} FAILED"] + FAILURES))
    print("all ok")


if __name__ == "__main__":
    main()
