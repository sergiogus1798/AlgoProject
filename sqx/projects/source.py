"""Find a project SQX itself wrote that defines an asset's session and feed, to borrow both from."""

import zipfile
from pathlib import Path

from core.paths import MASTER, WORKERS
from core.symbols import current
from sqx.projects.resources import SYMBOL
from sqx.projects.tasksettings import session_block


def defines(cfx: Path, session: str, feed: str) -> bool:
    """Whether one project.cfx carries both the session and the feed's <Symbol> block.

    Args:
        cfx: A project.cfx. Read only — a live install may hold it open.
        session: Session name, from the asset's file.
        feed: SQX symbol name, from the asset's file.
    """
    with zipfile.ZipFile(cfx) as z:
        texts = [current(z.read(n).decode("utf-8", "replace")) for n in z.namelist()
                 if n.endswith(".xml") and n != "config.xml"]
    return (any(session_block(t, session) for t in texts)
            and any(m.group(1) == feed for t in texts for m in SYMBOL.finditer(t)))


def pick(donor: Path, session: str, feed: str) -> Path | None:
    """The project to borrow the session and feed from, when the donor does not carry them.

    Args:
        donor: The frozen donor's project.cfx.
        session: Session name, from the asset's file.
        feed: SQX symbol name, from the asset's file.

    Returns:
        None when the donor already defines both. Otherwise the newest project.cfx on any
        install that does — the hours and the instrument are still copied from a definition
        SQX produced, never invented; `builder` refuses as before when none exists.
    """
    if defines(donor, session, feed):
        return None
    installs = [w["path"] for w in WORKERS.values()] + [MASTER]
    found = sorted((c for i in installs for c in (i / "user/projects").glob("*/project.cfx")),
                   key=lambda c: c.stat().st_mtime, reverse=True)
    return next((c for c in found if defines(c, session, feed)), None)
