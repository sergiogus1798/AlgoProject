"""Find a project SQX itself wrote that defines an asset's feed, and its session when one does."""

import zipfile
from pathlib import Path

from core.paths import MASTER, WORKERS
from core.symbols import current
from sqx.projects.resources import SYMBOL
from sqx.projects.tasksettings import session_block


def carries(cfx: Path, session: str, feed: str) -> tuple[bool, bool]:
    """Whether one project.cfx carries the feed's <Symbol> block, and the session.

    Args:
        cfx: A project.cfx. Read only — a live install may hold it open.
        session: Session name, from the asset's file.
        feed: SQX symbol name, from the asset's file.

    Returns:
        (has the feed, has the session).
    """
    with zipfile.ZipFile(cfx) as z:
        texts = [
            current(z.read(n).decode("utf-8", "replace"))
            for n in z.namelist()
            if n.endswith(".xml") and n != "config.xml"
        ]
    return (
        any(m.group(1) == feed for t in texts for m in SYMBOL.finditer(t)),
        any(session_block(t, session) for t in texts),
    )


def pick(donor: Path, session: str, feed: str) -> Path | None:
    """The project to borrow the session and feed from, when the donor does not carry them.

    Args:
        donor: The frozen donor's project.cfx.
        session: Session name, from the asset's file.
        feed: SQX symbol name, from the asset's file.

    Returns:
        None when the donor already defines both. Otherwise the newest project.cfx on any
        install that defines both, else the newest that defines the feed alone — the
        session then comes from SQX's database (`doctrine.borrow_session`). None too when
        no project defines the feed: the instrument is never invented.
    """
    if all(carries(donor, session, feed)):
        return None
    installs = [w["path"] for w in WORKERS.values()] + [MASTER]
    found = sorted(
        (c for i in installs for c in (i / "user/projects").glob("*/project.cfx")),
        key=lambda c: c.stat().st_mtime,
        reverse=True,
    )
    have = [(c, carries(c, session, feed)) for c in found]
    return next(
        (c for c, (f, s) in have if f and s), next((c for c, (f, _) in have if f), None)
    )
