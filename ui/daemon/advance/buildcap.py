"""The build's time cap: SQX stops a build on its strategy count only, so the minutes are ours."""

import re
import zipfile
from pathlib import Path

from core import worker

STOP = re.compile(r'<StopCondition\b[^>]*hours="(\d+)"[^>]*minutes="(\d+)"')


def minutes(cfx: Path) -> int:
    """The time cap the builder wrote into the Build task's StopCondition, 0 when none.

    Owner, 2026-10-01: a build stops on N strategies or M minutes, whichever comes first
    (`databank.caps` in assets/_build.yaml). Under `databank-full` SQX ignores `minutes=`.
    """
    with zipfile.ZipFile(cfx) as z:
        for name in (n for n in z.namelist() if n.startswith("Build-")):
            got = STOP.search(z.read(name).decode("utf-8", "replace"))
            if got:
                return int(got.group(1)) * 60 + int(got.group(2))
    return 0


def enforce(project: str, role: str, now: dict | None, top: Path) -> bool:
    """Stop the project once its running build has used its minutes.

    Args:
        project: The project running.
        role: Its worker.
        now: The running task's row of `progress.state`, or None.
        top: The worker's install folder; the cap is read from the project's own file.

    Returns:
        True when it sent the stop. A stopped project does not go on to its next active task
        (🔬 2026-10-01): the caller runs what is left (`pipeline.autopilot.run`).
    """
    if not (now and now["type"] == "Build"):
        return False
    cap = minutes(top / "user" / "projects" / project / "project.cfx")
    if not cap or (now["elapsed_s"] or 0) < cap * 60:
        return False
    worker.call(f"-project action=stop name={project}", role)
    print(f"{now['title']}: {cap} min cumplidos, se para el build", flush=True)
    return True
