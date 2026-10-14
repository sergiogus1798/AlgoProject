"""Save a project's gate survivors into the store: the .sqx once, then one file per set of tests."""

import csv
import hashlib
import tempfile
from pathlib import Path
from typing import TypedDict, cast

from core import sqxfile
from core.archive import collect, harvest, manifest as provenance
from core.manifest import code_version
from core.paths import DATA, ROOT
from core.store import extra, late, verify, write

GATE = "8"  # the step a strategy has to survive to be stored, limbo included (owner, 2026-10-08)
DEAD = "DESCARTAR"
CRITERIA = ROOT / "pipeline" / "autopilot" / "criteria.yaml"


def verdicts(project: str) -> dict[str, dict[str, dict]]:
    """What every workflow step said of every strategy of a project, the newest run winning.

    Args:
        project: SQX project name.

    Returns:
        identity -> step -> {strategy, verdict, outcome, reason, run}, read off
        `autopilot/<P>/<run>/paso-<n>/verdict.csv`, over the gate's own newest `verdict.csv`
        as step 8 for whoever no run judged.
    """
    out: dict[str, dict[str, dict]] = {}
    mother = late.mothers(
        project
    )  # the WFM judges a strategy under the identity it gave it
    # The gate's own newest verdict goes first and every run's judge over it: a rebuild cut
    # before its judge still has its survivors named, beside those of the runs that were judged.
    judged = sorted((DATA / "reports" / project).glob("*/*/gate/verdict.csv"))[
        -1:
    ] + sorted((DATA / "autopilot" / project).glob("*/paso-*/verdict.csv"))
    for path in judged:
        gate = path.parent.name == "gate"
        n, run = (
            (GATE, f"gate {path.parent.parent.name}")
            if gate
            else (path.parent.name.removeprefix("paso-"), path.parent.parent.name)
        )
        with path.open(encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                # lineage can name two identities each other's mother: the gate's one stays
                who = row["identity"]
                if not (gate and mother.get(cast(str, mother.get(who))) == who):
                    who = mother.get(who, who)
                out.setdefault(who, {})[n] = {
                    "strategy": row["strategy"],
                    "verdict": row["verdict"],
                    "outcome": row.get("outcome", ""),
                    "reason": row.get("reason", ""),
                    "run": run,
                    # a smoke run's word is the readability rules' alone, never a real verdict
                    **(
                        {"smoke": True}
                        if (path.parent.parent / "smoke").exists()
                        else {}
                    ),
                }
    return out


def survivors(project: str) -> dict[str, dict[str, dict]]:
    """The strategies of a project the gate left alive, with every step's word on them."""
    return {
        i: s
        for i, s in verdicts(project).items()
        if GATE in s and s[GATE]["verdict"] != DEAD
    }


def unsaved(project: str) -> list[str]:
    """The gate survivors of a project that are not whole in the store, by name.

    This is what `sqx.projects.retire` refuses on: deleting the project would lose them. Whole
    is not enough: the step's word is the last thing a save writes, so a save cut after the
    .sqx and before its tests is not saved.
    """
    return sorted(
        s[GATE]["strategy"]
        for i, s in survivors(project).items()
        if verify.check(i) or GATE not in write.manifest(i).get("steps", {})
    )


def cell_of(row: dict) -> str:
    """A project's cell from its registry row: asset, timeframe and the template's library name —
    `simple_long` / `simple_short` for a Simple Strategy (`simple:<side>` in the registry), so the
    two sides never share a cell (owner, 2026-10-13; cells saved before keep their old name)."""
    said = row["template"] or "simple"
    template = (
        said.replace(":", "_") if said.startswith("simple") else Path(said).parent.name
    )
    return f"{row['symbol']}_{row['timeframe']}_{template}"


def harvest_cut(
    project: str, identity: str, root: Path
) -> list[tuple[str, str, Path, dict]]:
    """One survivor's rows of every cosecha day of the project, written under `root`.

    Returns:
        (databank, day, folder, rows kept per table), days in name order.
    """
    out = []
    for day in sorted((DATA / "harvest" / project).glob("*/*/metrics.parquet")):
        databank, stamp = day.parts[-3:-1]
        folder = root / databank / stamp
        folder.parent.mkdir(parents=True, exist_ok=True)
        out.append(
            (
                databank,
                stamp,
                folder,
                harvest.harvest_rows(day.parent, identity, folder),
            )
        )
    return out


def harvest_all(project: str, identities: list[str], root: Path) -> dict[str, list]:
    """`harvest_cut` for every survivor with the days OUTSIDE: each cosecha parquet is read once,
    where survivor by survivor `collect` keeps only four tables and a project has three per day."""
    got: dict[str, list] = {i: [] for i in identities}
    for day in sorted((DATA / "harvest" / project).glob("*/*/metrics.parquet")):
        databank, stamp = day.parts[-3:-1]
        for i in identities:
            folder = root / i / databank / stamp
            folder.parent.mkdir(parents=True, exist_ok=True)
            got[i].append(
                (databank, stamp, folder, harvest.harvest_rows(day.parent, i, folder))
            )
    return got


def one(
    project: str,
    sqx: Path,
    steps: dict[str, dict],
    generated: int,
    mother: dict[str, str] | None = None,
    harvest: list | None = None,
) -> str:
    """Save one survivor: its file, every study that names it, its trades everywhere, its sisters, its
    cosecha rows and the cost card — what is the population's in a zip of its own, kept once.

    Args:
        project: SQX project name.
        sqx: Its strategy file.
        steps: What each step said of it (`verdicts`).
        generated: How many strategies the gate judged in that project — the denominator.
        mother: `late.mothers(project)`, when the caller has it (it walks every lineage.csv).
        harvest: This survivor's cosecha rows already cut by `harvest_cut`; None cuts them here.

    Returns:
        Its identity. Saving again adds only what is new.
    """
    row, name = provenance.registry(project), steps[GATE]["strategy"]
    identity = write.put_sqx(
        sqx,
        cell_of(row),
        {
            "project": project,
            "strategy": steps[GATE]["strategy"],
            "symbol": row["symbol"],
            "timeframe": row["timeframe"],
            "template": row["template"],
            "generated": generated,
            "code_version": code_version(),
            "criteria_sha256_at_save": hashlib.sha256(
                CRITERIA.read_bytes()
            ).hexdigest(),
        },
    )
    with tempfile.TemporaryDirectory() as tmp:
        entries, loose, skipped = collect.freeze(
            project,
            identity,
            Path(tmp) / "reports",
            late.aliases(project, identity, mother),
        )
        if loose:  # CSVs outside any study folder with rows of this identity
            sueltos = Path(tmp) / "sueltos"
            for rel in loose:
                (sueltos / rel).parent.mkdir(parents=True, exist_ok=True)
                (Path(tmp) / "reports" / rel).rename(sueltos / rel)
            write.add(
                identity, "sueltos", sueltos, {"study": "sueltos", "skipped": skipped}
            )
        for e in entries:
            stem = f"{e['study']}.{e['databank']}.{e['day']}"
            src = Path(tmp) / "reports" / e["databank"] / e["day"] / e["study"]
            about = {k: e[k] for k in ("study", "databank", "day", "config_hash")}
            took = extra.population(
                src, identity, e["names"] or [name], Path(tmp) / "pop" / stem
            )
            real = DATA / "reports" / project / e["databank"] / e["day"] / e["study"]
            if late.leftovers(real, src, Path(tmp) / "pop" / stem) or took:
                write.add(
                    identity,
                    f"{stem}.poblacion",
                    Path(tmp) / "pop" / stem,
                    about | {"population": True},
                )
            if any(src.rglob("*.*")):
                write.add(identity, stem, src, about)
        for stem, src, about in (
            extra.trades(
                project,
                name,
                identity,
                Path(tmp) / "raw",
                late.aliases(project, identity, mother),
            )
            + extra.sisters(
                project,
                name,
                identity,
                Path(tmp) / "sisters",
                late.aliases(project, identity, mother),
            )
            + extra.metrics(project, name, Path(tmp) / "metrics")
            + extra.neighbours(project, name, Path(tmp) / "neighbours")
            + late.unpaired(
                project,
                identity,
                {f"{e['databank']}/{e['day']}/{e['study']}" for e in entries},
                {s["path"] for s in skipped},
                Path(tmp) / "unpaired",
            )
            + late.exports(project, identity, Path(tmp) / "exports")
            + late.variants(project, name, identity, Path(tmp) / "variants")
        ):
            write.add(identity, stem, src, about)
        for databank, stamp, out, counts in (
            harvest_cut(project, identity, Path(tmp) / "harvest")
            if harvest is None
            else harvest
        ):
            if counts["metrics"]:
                write.add(
                    identity,
                    f"cosecha.{databank}.{stamp}",
                    out,
                    {"study": "cosecha", "databank": databank, "day": stamp},
                )
        card = provenance.asset(row["symbol"], Path(tmp) / "asset")
        write.add(
            identity,
            f"costes.{row['symbol']}",
            Path(tmp) / "asset",
            {"study": "costes", "asset_sha256": card["sha256"]},
        )
    for n, said in steps.items():
        write.step(identity, n, said)
    return identity


class Saved(TypedDict):
    """What `project` saved and what it could not."""

    saved: list[str]
    no_sqx: list[str]
    problems: dict[str, list[str]]


def project(name: str, sqx_dirs: list[Path]) -> Saved:
    """Save every gate survivor of a project whose .sqx can be found.

    Args:
        name: SQX project name.
        sqx_dirs: Folders to look for `<strategy name>.sqx` in, first hit wins — the project's
            databanks on its install, or wherever a copy was kept.

    Returns:
        `saved` (identities), `no_sqx` (names with no file of that identity anywhere: reported,
        never silent) and `problems` (identity -> what `verify.check` found after saving).
    """
    said = verdicts(name)
    mother = late.mothers(name)  # once for the save, not once per survivor and call
    generated = sum(GATE in s for s in said.values())
    try:
        return _project(name, sqx_dirs, said, generated, mother)
    finally:  # the daemon lives on: what the reports cost in RAM goes back
        collect.release()
        harvest.release()


def _project(
    name: str, sqx_dirs: list[Path], said: dict, generated: int, mother: dict
) -> Saved:
    """The body of `project`."""
    alive = {i: s for i, s in said.items() if GATE in s and s[GATE]["verdict"] != DEAD}
    if (
        not generated
    ):  # no step-8 row at all: nothing to save, and no run number to take the max of
        return {"saved": [], "no_sqx": [], "problems": {}}
    no_sqx, whole = [], []
    for identity, steps in sorted(
        alive.items(), key=lambda kv: kv[1][GATE]["strategy"]
    ):
        files = [d / f"{steps[GATE]['strategy']}.sqx" for d in sqx_dirs]
        # By identity, before anything is written: a name is reused from one build to the next.
        found = next(
            (f for f in files if f.exists() and sqxfile.identity(f) == identity), None
        )
        if found is None:
            no_sqx.append(steps[GATE]["strategy"])
            continue
        whole.append((identity, found, steps))
    with tempfile.TemporaryDirectory() as cut:
        cosecha = harvest_all(name, [i for i, _, _ in whole], Path(cut))
        saved = [
            one(name, found, steps, generated, mother, cosecha[identity])
            for identity, found, steps in whole
        ]
    write.run(
        cell_of(provenance.registry(name)),
        name,
        {
            "generated": generated,
            "survivors": len(alive),
            "saved": len(saved),
            "no_sqx": sorted(no_sqx),
            "run": max(s[GATE]["run"] for s in said.values() if GATE in s),
        },
    )
    return {
        "saved": saved,
        "no_sqx": no_sqx,
        "problems": {i: bad for i in saved if (bad := verify.check(i))},
    }
