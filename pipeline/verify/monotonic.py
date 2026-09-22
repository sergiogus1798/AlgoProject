"""Proof that progress only ever goes up, and that it is written while a stage runs."""

import threading
import time
from pathlib import Path

from pipeline.ledger import progress, state
from pipeline.stages import execute
from pipeline.verify import fixture

SLOW = ["--seconds", "4"]          # the stage the sampler needs time to watch
TICK = 0.02                        # how often the sampler reads the ledger
MARKER = "PROGRESS"
WATCHED = "build"


def watch(work: Path, stage: str, stop: threading.Event, seen: list[int]) -> None:
    """Read the ledger from outside the stage, the way a monitor would.

    Args:
        work: The fixture's work directory.
        stage: Stage name.
        stop: Set by the caller once the stage has returned.
        seen: Filled with every progress value observed, in order.

    This runs while the stage writes, which is also the proof that an atomic write is
    enough: a reader never catches a half-written file.
    """
    while not stop.is_set():
        got = state.read(work)["stages"].get(stage, {})
        if "progress" in got:
            seen.append(got["progress"])
        time.sleep(TICK)


def during(stage: dict, work: Path) -> list[int]:
    """Run one stage and return what a reader saw while it ran.

    Args:
        stage: A resolved recipe row.
        work: The fixture's work directory.

    Returns:
        Every progress value observed from outside, in order.
    """
    state.begin(work, stage["name"])
    seen, stop = [], threading.Event()
    watcher = threading.Thread(target=watch, args=(work, stage["name"], stop, seen))
    watcher.start()
    execute.stream(stage, work, MARKER)
    stop.set()
    watcher.join()
    state.finish(work, stage["name"], execute.recorded(stage) | execute.hashed(stage))
    return seen


def backwards(work: Path) -> list[str]:
    """Check that the ledger refuses a stage that reports less than it already had.

    Args:
        work: The fixture's work directory.

    Returns:
        A problem when the write was accepted. Monotonicity is only a contract if
        breaking it fails loudly; clamping would turn a stage repeating work it had
        already done into a bar that simply sat still.
    """
    state.begin(work, WATCHED)
    progress.say(work, WATCHED, 40, "prueba")
    try:
        progress.say(work, WATCHED, 39, "hacia atrás")
    except ValueError:
        return []
    return ["progress aceptó 40 -> 39; la monotonía no es un contrato"]


def check(ctx: dict) -> list[str]:
    """Run the whole chain under a reader and report what broke.

    Args:
        ctx: What `fixture.build()` returned.

    Returns:
        One line per problem, empty when the contract held.
    """
    work, problems = fixture.work(), backwards(fixture.work())
    for stage in fixture.chain(ctx):
        if stage["name"] == WATCHED:
            stage = stage | {"command": stage["command"] + SLOW}
        seen = during(stage, work)
        if seen != sorted(seen):
            problems.append(f"{stage['name']}: progress retrocedió: {seen}")
        if stage["name"] == WATCHED and len({v for v in seen if 0 < v < 100}) < 2:
            problems.append(f"{WATCHED}: solo se vio {sorted(set(seen))} desde fuera; "
                            "el estado se escribió al final, no durante")
        entry = state.read(work)["stages"][stage["name"]]
        if entry["progress"] != 100 or not entry.get("done_at"):
            problems.append(f"{stage['name']}: terminó sin cerrar su entrada: {entry}")
    return problems
