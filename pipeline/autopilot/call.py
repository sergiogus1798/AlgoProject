"""One command of the tail run to its end: a study's as the window builds it, or one given."""

from collections.abc import Callable
from typing import TypeVar

from core import proc
from ui.daemon.runner import table

# SQX's own transient crash (a fastutil NullPointerException right after «Task finished»,
# knowhow/sqx-drive/mcr-nullpointer-fastutil-transient.md): both launchers end on these words.
T = TypeVar("T")
ABORT = "SQX abortó"


def keeper(pre: dict) -> Callable[[], None]:
    """What undoes an SQX step of the restart route that aborted: it deletes from the chosen
    tasks' output databanks every `.sqx` that was not there now (the worker is stopped by then).

    A retest does not clear its output, and the abort comes after «Task finished»: the
    rerun of an OOS retest left 2,000 strategies where 1,000 were built, each twice
    (🔬 2026-10-05), and every later step ran on both copies.
    """
    banks = pre["cfx"].parent / "databanks"

    def names(bank: str) -> set[str]:
        """The strategies of one output databank on disk."""
        return {f.name for f in (banks / bank).glob("*.sqx")}

    had = {t["output"]: names(t["output"]) for t in pre["chosen"] if t["output"]}

    def undo() -> None:
        """Remove what the aborted attempt added."""
        for bank, before in had.items():
            for name in sorted(names(bank) - before):
                (banks / bank / name).unlink()

    return undo


def again(run: Callable[[], T], undo: Callable[[], None] | None = None) -> T:
    """`run()`, repeated ONCE when it ends on SQX's transient abort: the card's remedy is to
    rerun the step, and an unattended run died on it at step 24 (🔬 2026-10-05). Any other
    failure, and a second abort, end the step as before. `undo` runs before the rerun: what
    puts back the state `run` started from, for a `run` that does not clear its own output."""
    try:
        return run()
    except SystemExit as failed:
        if ABORT not in str(failed):
            raise
        print(
            f"{failed}\nfallo transitorio conocido de SQX: se repite una vez",
            flush=True,
        )
        if undo:
            undo()
        return run()


def run(argv: list[str]) -> None:
    """Run `python3 <argv>` from the repository root; its failure ends the step with its own words.

    Args:
        argv: What follows `python3`, e.g. ["-m", "studies.readings.edgeCost.report", "--project", …].

    Nothing the command printed is shown: under the ledger's door a blind step's numbers
    must not be read before 17, 18 and 19 are all registered. Held in `proc.CHILDREN` while
    it runs, so a cancel ends it at once.
    """
    rc, tail = proc.command(argv)
    if rc:
        raise SystemExit(f"{argv[1]}: {tail}")


def window(
    study: str, project: str, databank: str, symbol: str, strategies: list[str]
) -> list[list[str]]:
    """The commands the window's run button starts for one study (`runner.table.jobs`).

    Args:
        study: Study key, e.g. "wfc".
        project: Project name.
        databank: The databank it reads, '' for a study of a mother's variant batch.
        symbol: The project's asset.
        strategies: One command per strategy; empty runs the study once over the population.

    Returns:
        One argv per job. The sentence the window would show instead ends the step.
    """
    got = table.jobs(
        {
            "study": study,
            "scope": "one" if strategies else "many",
            "project": project,
            "databank": databank,
            "asset": symbol,
            "overrides": [],
            "only": None,
            "strategies": strategies,
        }
    )
    if isinstance(got, str):
        raise SystemExit(got)
    return [job["argv"] for job in got]
