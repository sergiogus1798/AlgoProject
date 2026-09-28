"""Where a databank's files live, which retest pairs with it, and whether SQX is writing it now."""

from functools import lru_cache
from pathlib import Path

from core import cfx, sqxfile, sqxstats
from core.paths import databank_dir
from ui.daemon import progress

# The retest the gate pairs a build databank with: the task that reads it and writes `OOS`,
# the name `sqx/projects/builder.py` gives the oos1 retest of every workflow project.
PARTNER = "OOS"


def install_of(project: str, databank: str) -> tuple[str, Path] | None:
    """The install that holds this databank, workers first.

    Args:
        project: Project name.
        databank: Databank name as SQX spells it (spaces, not underscores).

    Returns:
        (role, top folder), or None. A project the owner copied to the master to look at
        also sits on a worker; the worker's copy is the one the workflow writes.
    """
    for role, top in progress.installs().items():
        if databank_dir(project, databank, top).is_dir():
            return role, top
    return None


def spelled(project: str, databank: str) -> str:
    """The databank's name as SQX spells it, from either spelling the window may hold.

    Args:
        project: Project name.
        databank: `Retest Markets - Family` or `Retest_Markets_-_Family`.

    Returns:
        The folder name that exists on some install, or the input unchanged.
    """
    for top in progress.installs().values():
        folder = databank_dir(project, "x", top).parent
        if folder.is_dir():
            for d in folder.iterdir():
                if d.name.replace(" ", "_") == databank.replace(" ", "_"):
                    return d.name
    return databank


def partner(top: Path, project: str, databank: str) -> str | None:
    """The retest databank the gate harvests beside this one, when this one is a build.

    Args:
        top: The install holding the project.
        project: Project name.
        databank: The build databank.

    Returns:
        `OOS` when a task of the project reads `databank` and writes it, else None.
    """
    path = str(top / "user" / "projects" / project / "project.cfx")
    for task in cfx.tasks(path):
        xml = cfx.task_xml(path, task["file"])
        io = {d.get("name"): d.get("value") for d in xml.iter("Databank")}
        if io.get("Input") == databank and io.get("Output") == PARTNER:
            return PARTNER
    return None


def files(top: Path, project: str, databank: str) -> list[Path]:
    """The databank's strategy files, sorted.

    Args:
        top: The install holding it.
        project: Project name.
        databank: Databank name.

    Returns:
        Every `.sqx` in its folder.
    """
    return sorted(databank_dir(project, databank, top).glob("*.sqx"))


def cross_market(sqx: Path) -> bool:
    """Whether a strategy file carries cross-check markets, so its trades need `data=all`.

    Args:
        sqx: One strategy file of the databank.

    Returns:
        True when it holds an `AdditionalMarket` result besides its main one.
    """
    return any(r.startswith("AdditionalMarket") for r in sqxstats.results(sqx))


def feed(sqx: Path) -> str:
    """The SQX symbol a strategy ran on, without the timeframe: `USDJPY_DukasM1_the5ers`.

    Args:
        sqx: One strategy file.

    Returns:
        Symbol and feed from the file's result name, the `_LOM_<tf>` suffix cut off.
    """
    symbol, fed = sqxfile.symbol(sqx)
    return f"{symbol}_{fed.split('_LOM_')[0]}"


def writing(top: Path, project: str) -> bool:
    """Whether SQX on that install is running this project right now.

    Args:
        top: The install.
        project: Project name.

    Returns:
        True when today's log started it and has not seen it finish: its databanks are
        being written, and a file read now may be half a strategy.
    """
    state = progress.run_state(progress.log_lines(top)[0])
    return state["project"] == project and not state["finished"]


def roster(project: str, databank: str) -> dict[str, str]:
    """Every strategy the databank holds on disk, identity to name, whether or not any study
    has judged it — what makes a databank's page list its strategies the moment it opens.

    Args:
        project: Project name.
        databank: Either spelling.

    Returns:
        Identity to file stem; empty when no install holds the databank or SQX is writing it.
    """
    db = spelled(project, databank)
    where = install_of(project, db)
    if where is None or writing(where[1], project):
        return {}
    folder = databank_dir(project, db, where[1])
    return _roster(str(folder), folder.stat().st_mtime)


@lru_cache(maxsize=64)
def _roster(folder: str, stamp: float) -> dict[str, str]:
    """`roster()` for one state of a folder: its mtime changes when a file comes or goes."""
    return {sqxfile.identity(f): f.stem for f in sorted(Path(folder).glob("*.sqx"))}


def forget() -> None:
    """Drop every cached roster, so the next read lists the folders again.

    The cache is keyed by the folder's mtime, which a file added or removed moves; but a
    strategy SQX rewrote in place keeps the folder's mtime, and «Recargar databank» must
    see it too.
    """
    _roster.cache_clear()
