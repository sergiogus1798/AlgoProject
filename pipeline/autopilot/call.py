"""One command of the tail run to its end: a study's as the window builds it, or one given."""

import contextlib
from collections.abc import Callable

from sqx.projects import live
from ui.daemon.launch import chain
from ui.daemon.runner import table

# SQX's own transient crash (a fastutil NullPointerException right after «Task finished»,
# knowhow/sqx-drive/mcr-nullpointer-fastutil-transient.md): both launchers end on these words.
ABORT = "SQX abortó"


def keeper(pre: dict, restart: bool = True) -> Callable[[], None]:
    """What undoes an SQX step that aborted: it takes out of the chosen tasks' output
    databanks every strategy that was not there now.

    A retest does not clear its output, and the abort comes after «Task finished»: the
    rerun of an OOS retest left 2,000 strategies where 1,000 were built, each twice
    (🔬 2026-10-05), and every later step ran on both copies. `restart`: the worker is
    stopped by then and the `.sqx` are deleted; else the live session holds them and they are
    cut through it (`live.cut`), after a stop sent to the project the abort left hung.
    """
    role, project = pre["role"], pre["cfx"].parent.name
    banks = pre["cfx"].parent / "databanks"

    def names(bank: str) -> set[str]:
        """The strategies of one output databank: on disk, or in the session's memory."""
        if restart:
            return {f.name for f in (banks / bank).glob("*.sqx")}
        return set(live.call(role, "listStrategies", projectName=project,
                             databankName=bank)["strategies"])

    had = {t["output"]: names(t["output"]) for t in pre["chosen"] if t["output"]}

    def undo() -> None:
        """Remove what the aborted attempt added."""
        if not restart:
            with contextlib.suppress(Exception):      # hung or already idle: either way
                live.call(role, "stop", projectName=project)
        for bank, before in had.items():
            extra = sorted(names(bank) - before)
            if restart:
                for name in extra:
                    (banks / bank / name).unlink()
            elif extra:
                live.cut(role, project, bank, extra)
    return undo


def again(run: Callable[[], object], undo: Callable[[], None] | None = None) -> object:
    """`run()`, repeated ONCE when it ends on SQX's transient abort: the card's remedy is to
    rerun the step, and an unattended run died on it at step 24 (🔬 2026-10-05). Any other
    failure, and a second abort, end the step as before. `undo` runs before the rerun: what
    puts back the state `run` started from, for a `run` that does not clear its own output."""
    try:
        return run()
    except SystemExit as failed:
        if ABORT not in str(failed):
            raise
        print(f"{failed}\nfallo transitorio conocido de SQX: se repite una vez", flush=True)
        if undo:
            undo()
        return run()


def run(argv: list[str]) -> None:
    """Run `python3 <argv>` from the repository root; its failure ends the step with its own words.

    Args:
        argv: What follows `python3`, e.g. ["-m", "sqx.structural.keep", "--work", …].

    Nothing the command printed is shown: under the ledger's door a blind step's numbers
    must not be read before 17, 18 and 19 are all registered. Held in `chain.CHILDREN` while
    it runs, so a cancel ends it at once.
    """
    rc, tail = chain.command(argv)
    if rc:
        raise SystemExit(f"{argv[1]}: {tail}")


def window(study: str, project: str, databank: str, symbol: str,
           strategies: list[str]) -> list[list[str]]:
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
    got = table.jobs({"study": study, "scope": "one" if strategies else "many",
                      "project": project, "databank": databank, "asset": symbol,
                      "overrides": [], "only": None, "strategies": strategies})
    if isinstance(got, str):
        raise SystemExit(got)
    return [job["argv"] for job in got]
