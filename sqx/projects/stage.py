#!/usr/bin/env python3
"""Switch on only one workflow step's tasks, so `action=start` runs that step and nothing else."""

import argparse
import re
import zipfile
from collections.abc import Sequence
from functools import lru_cache
from pathlib import Path

import yaml

from core.assetdata import doctrine
from sqx.projects import cfxio, charts
from core.xmlget import rx

STAGES = Path(__file__).with_name("stages.yaml")
TASK = re.compile(r"<Task\b[^>]*/>")


@lru_cache(maxsize=1)
def _parsed(mtime_ns: int) -> dict:
    """stages.yaml as of one modification time."""
    return yaml.safe_load(STAGES.read_text(encoding="utf-8"))


def _stages() -> dict:
    """stages.yaml, re-read when its mtime changes (the daemon is long-lived)."""
    return _parsed(STAGES.stat().st_mtime_ns)


def titles(step: str) -> list[str]:
    """The task titles one workflow step runs.

    Args:
        step: A key of stages.yaml, or "wfc".

    Returns:
        The titles, in the order the step names them.
    """
    if step == "wfc":
        return [t["title"] for t in doctrine()["wfc"]["tasks"]]
    return list(_stages()[step])


def only(config: str, wanted: list[str]) -> tuple[str, list[tuple[str, bool]]]:
    """Mark the wanted tasks active and every other task inactive.

    Args:
        config: The project's config.xml as text.
        wanted: Task titles to switch on.

    Returns:
        The config, and one (title, active) row per task in config order. A task with no
        title — a donor's `ClearDatabanks` or `GoToTask` — is always switched off: an active
        GoToTask loops forever under `action=start`.
    """
    rows = []

    def one(m: re.Match) -> str:
        """One <Task/> tag with its active flag rewritten."""
        title = re.search(r'title="([^"]*)"', m.group(0))
        on = title is not None and title.group(1) in wanted
        rows.append((title.group(1) if title else rx(r'name="([^"]*)"', m.group(0)).group(1), on))
        return re.sub(r'active="[^"]*"', f'active="{str(on).lower()}"', m.group(0))

    return TASK.sub(one, config), rows


def apply(cfx: Path, steps: list[str], skip: Sequence[str] = ()) -> list[tuple[str, bool]]:
    """Leave only these steps' tasks active in a project.cfx.

    Args:
        cfx: Path of a project.cfx. Must not be held by a running install (hard rule 4).
        steps: Workflow steps, e.g. ["build", "oos"].
        skip: Titles of those steps to leave off — a task its configurator could not write.

    Returns:
        One (title, active) row per task. Raises SystemExit when a step names a task the
        project does not carry: starting it then would run nothing, or the wrong thing.
    """
    wanted = [t for s in steps for t in titles(s)]
    return just(cfx, [t for t in wanted if t not in skip], wanted)


def just(cfx: Path, on: list[str], expected: list[str] | None = None) -> list[tuple[str, bool]]:
    """Leave only these task titles active in a project.cfx — a step's, or the one the owner
    chose in the window («Lanzar en SQX»).

    Args:
        cfx: Path of a project.cfx. Must not be held by a running install (hard rule 4).
        on: Titles to switch on.
        expected: Titles the project must carry, `on` by default.

    Returns:
        One (title, active) row per task. SystemExit when one of `expected` is missing.
        Every step passes through here on its way to `action=start`, so this is also where
        a task left active gets the extra charts its project's strategies read
        (`charts.ensure`) instead of aborting the run inside SQX.
    """
    held = cfxio.held(cfx)
    if held:
        raise SystemExit(f"el {held} tiene este proyecto abierto y reescribe el .cfx al salir. "
                         f"Paralo: bin/sqx-worker.sh --role {held} stop")
    wanted = expected if expected is not None else on
    members = cfxio.members(cfx)
    config, rows = only(members["config.xml"].decode("utf-8"), on)
    missing = sorted(set(wanted) - {title for title, _ in rows})
    if missing:
        raise SystemExit(f"{cfx.parent.name} no lleva la(s) tarea(s) {', '.join(missing)}. "
                         "Un proyecto de workflow se crea con `sqx.projects.builder --workflow`.")
    live = [rx(r'taskXMLFile="([^"]*)"', tag).group(1)
            for tag in TASK.findall(config) if 'active="true"' in tag]
    # Several configurators (crossmarket, SPP, WFC) write their <Setups> from scratch, with
    # one chart: the project's extra charts go back in here, where every one of them ends.
    extra = charts.streams(members)
    for name in live:
        if name in members:
            members[name] = charts.ensure(members[name].decode("utf-8"), extra)[0].encode("utf-8")
    members["config.xml"] = config.encode("utf-8")
    cfxio.write(cfx, members)
    return rows


def own(cfx: Path, step: str, skip: Sequence[str] = ()) -> str:
    """What a configurator does after writing its task: leave its step alone switched on.

    Args:
        cfx: The project just configured.
        step: The configurator's own workflow step.
        skip: Its tasks it left unconfigured, which must stay off.

    Returns:
        The line to print. A project without the workflow's tasks — one built for a single
        study — is left as it is, and the line says to check what is active before starting.
    """
    with zipfile.ZipFile(cfx) as z:
        config = z.read("config.xml").decode("utf-8")
    if not all(f'title="{t}"' in config for s in yaml.safe_load(STAGES.read_text())
               for t in titles(s)):
        return (f"⚠️ {cfx.parent.name} no es un proyecto de workflow: `action=start` corre TODAS "
                "sus tareas activas. Mira cuáles lo están antes de lanzarlo.")
    apply(cfx, [step], skip)
    return (f"el proximo `action=start` de {cfx.parent.name} corre solo `{step}`"
            + (f" (sin {', '.join(skip)})" if skip else ""))


def main() -> None:
    """Switch a project's tasks so that only the named steps run on the next start."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cfx", required=True, type=Path)
    ap.add_argument("--step", required=True,
                    help="uno o varios pasos separados por comas: "
                         f"{', '.join(list(yaml.safe_load(STAGES.read_text()))+['wfc'])}")
    a = ap.parse_args()
    rows = apply(a.cfx, a.step.split(","))
    print(f"{a.cfx.parent.name}: el proximo `action=start` corre {a.step}")
    for title, on in rows:
        print(f"  {'●' if on else '·'} {title}")


if __name__ == "__main__":
    main()
