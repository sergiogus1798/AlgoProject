"""The C5 ledger: one state.json per mother strategy, written atomically while stages run."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from core.datapaths import pipeline_dir

BRANCH = "pipeline"
FILE = "state.json"


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
    return pipeline_dir(project, safe(strategy))


def now() -> str:
    """The timestamp every ledger entry carries.

    Returns:
        Local time, seconds resolution, ISO 8601.
    """
    return datetime.now().isoformat(timespec="seconds")


def read(work: Path) -> dict[str, Any]:
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


def begin(work: Path, stage: str) -> None:
    """Record that a stage has started, before it has produced anything.

    Args:
        work: The strategy's work directory.
        stage: Stage name.

    A stage with no entry and a stage that is running are different situations, and a
    monitor has to be able to tell them apart from the file alone.
    """
    state = read(work)
    state["stages"][stage] = {
        "started_at": now(),
        "progress": 0,
        "status": "arrancando",
    }
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
