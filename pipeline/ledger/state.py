"""The C5 ledger: one state.json per mother strategy, written atomically while stages run."""

import json
import os
from datetime import datetime
from pathlib import Path

from core.assets import REQUIRED, load as load_asset
from core.paths import DATA

BRANCH = "pipeline"
FILE = "state.json"
PROVISIONAL = "PROVISIONAL"


def safe(strategy: str) -> str:
    """The strategy name as it is spelled inside a path.

    Args:
        strategy: Name as SQX shows it, e.g. "Strategy 17.9.39".

    Returns:
        Spaces as underscores and dots as hyphens, the same spelling sppUltra already uses
        for its brief filenames, so the two spellings agree without either module importing the other.
    """
    return strategy.replace(" ", "_").replace(".", "-")


def work_dir(project: str, strategy: str) -> Path:
    """Where one mother strategy's ledger and stage outputs live.

    Args:
        project: Project name on the master.
        strategy: Name as SQX shows it.

    Returns:
        Path under the data root. It holds kilobytes of ledger next to gigabytes of
        variant data, and outlives the data: the ledger is what makes the deletion
        auditable instead of a loss.
    """
    return DATA / BRANCH / project / safe(strategy)


def now() -> str:
    """The timestamp every ledger entry carries.

    Returns:
        Local time, seconds resolution, ISO 8601.
    """
    return datetime.now().isoformat(timespec="seconds")


def read(work: Path) -> dict:
    """The ledger as it stands on disk.

    Args:
        work: The strategy's work directory.

    Returns:
        The parsed state.json.
    """
    return json.loads((work / FILE).read_text(encoding="utf-8"))


def write(work: Path, state: dict) -> None:
    """Replace the ledger in one indivisible step.

    Args:
        work: The strategy's work directory.
        state: The whole ledger.

    A temporary file plus `os.replace`, which is atomic on the same filesystem. This is
    the one place in the module that guards against something going wrong, and it is not
    defensive coding: the contract says another process reads this file while a stage
    writes it, and that a kill mid-write must not corrupt it.
    """
    work.mkdir(parents=True, exist_ok=True)
    tmp = work / (FILE + ".tmp")
    tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, work / FILE)


def costs_provisional(asset: str) -> bool:
    """Whether the trading costs this run assumes are still the owner's placeholders.

    Args:
        asset: Asset name as assets/<asset>.yaml is called.

    Returns:
        True while any required cost override still says PROVISIONAL. Every report built
        on this run inherits the stamp, so a number produced with SQX defaults can never
        be mistaken later for one produced with the broker's real figures.
    """
    data = load_asset(asset)
    return any(PROVISIONAL in data[field]["why"] for field in REQUIRED)


def open_run(work: Path, strategy: str, project: str, databank: str, asset: str) -> dict:
    """The ledger for this mother, created on first sight and reused afterwards.

    Args:
        work: The strategy's work directory.
        strategy: Name as SQX shows it.
        project: Project name on the master.
        databank: Databank the SPP export came from.
        asset: Asset name for the cost stamp.

    Returns:
        The ledger. An existing one is returned untouched, which is what makes a rerun
        continue instead of starting over.
    """
    if (work / FILE).exists():
        return read(work)
    state = {"strategy": strategy, "project": project, "databank": databank,
             "stage": None, "opened_at": now(), "stages": {},
             "costs_provisional": costs_provisional(asset)}
    write(work, state)
    return state


def begin(work: Path, stage: str) -> None:
    """Record that a stage has started, before it has produced anything.

    Args:
        work: The strategy's work directory.
        stage: Stage name.

    A stage with no entry and a stage that is running are different situations, and a
    monitor has to be able to tell them apart from the file alone.
    """
    state = read(work)
    state["stages"][stage] = {"started_at": now(), "progress": 0, "status": "arrancando"}
    write(work, state)


def finish(work: Path, stage: str, facts: dict) -> None:
    """Close a stage: full progress, the time, and whatever it wants recorded.

    Args:
        work: The strategy's work directory.
        stage: Stage name.
        facts: Fields merged into the stage entry, e.g. the files collect hashed.
    """
    state = read(work)
    state["stages"][stage] |= {"done_at": now(), "progress": 100} | facts
    state["stage"] = stage
    write(work, state)


def is_done(state: dict, stage: str) -> bool:
    """Whether a stage already finished in an earlier run.

    Args:
        state: The ledger.
        stage: Stage name.

    Returns:
        True when the ledger recorded a completion. The runner also checks that the
        stage's outputs are still on disk, because the ledger outlives the data it
        describes and a swept mother must not be read as an unfinished one.
    """
    return bool(state["stages"].get(stage, {}).get("done_at"))
