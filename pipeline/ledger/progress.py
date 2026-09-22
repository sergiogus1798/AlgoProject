"""How far a running stage has got, written into the ledger while it runs, never after."""

from pathlib import Path

from pipeline.ledger import state

FLOOR, CEILING = 0, 100


def say(work: Path, stage: str, progress: int, status: str) -> None:
    """Record a stage's advance and the line a human reads next to it.

    Args:
        work: The strategy's work directory.
        stage: Stage name.
        progress: 0 to 100.
        status: One short line in the owner's language, e.g. "1.850 de 5.000 escritas".

    Raises:
        ValueError: The stage went backwards, or reported outside 0..100. Monotonic
            progress is the contract a monitor reads, so a stage that breaks it is a bug
            to see immediately, not a number to quietly clamp -- a bar that slides back is
            indistinguishable from a pipeline that restarted work it had already done.
    """
    if not FLOOR <= progress <= CEILING:
        raise ValueError(f"{stage}: progress {progress} outside {FLOOR}..{CEILING}")
    got = state.read(work)
    before = got["stages"][stage]["progress"]
    if progress < before:
        raise ValueError(f"{stage}: progress went {before} -> {progress}, it is monotonic")
    got["stages"][stage] |= {"progress": progress, "status": status}
    state.write(work, got)


def note(work: Path, stage: str, status: str) -> None:
    """Record that the stage is alive without claiming it advanced.

    Args:
        work: The strategy's work directory.
        stage: Stage name.
        status: Whatever the stage last printed.

    A stage that reports no percentage still has to prove it is not hung, which is the
    whole reason the ledger is written during the stage rather than at its end.
    """
    got = state.read(work)
    got["stages"][stage] |= {"status": status}
    state.write(work, got)
