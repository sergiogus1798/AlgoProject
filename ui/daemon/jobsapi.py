"""The routes every zone shares: the daemon's job list, and where an SQX project stands on disk."""

from fastapi import APIRouter

from ui.daemon import jobs, progress

ROUTER = APIRouter()


@ROUTER.get("/api/jobs")
def job_list() -> dict[str, object]:
    """Every job this daemon started and how each one stands.

    Returns:
        `jobs`, oldest first, each with its exit code and the end of its log.
    """
    return {"jobs": jobs.listing()}


@ROUTER.get("/api/progress/installs")
def progress_installs() -> dict[str, object]:
    """Every install by role, with the projects each one holds.

    Returns:
        Role → project names. Read off the folders: no install is asked anything.
    """
    return {role: progress.projects(path) for role, path in progress.installs().items()}


@ROUTER.get("/api/progress")
def progress_state(install: str, project: str) -> dict[str, object]:
    """Where one project of one install is right now.

    Args:
        install: A role from the installs listing.
        project: One of its projects.

    Returns:
        As `progress.state` builds it, from the project file, the databank folders and
        the tail of today's log.
    """
    return progress.state(install, project)
