#!/usr/bin/env python3
"""Switch on only one workflow step's tasks, so `action=start` runs that step and nothing else."""

import argparse
import re
import zipfile
from pathlib import Path

import yaml

from core.assetdata import doctrine
from sqx.projects.configure import running_install

STAGES = Path(__file__).with_name("stages.yaml")
TASK = re.compile(r"<Task\b[^>]*/>")


def titles(step: str) -> list[str]:
    """The task titles one workflow step runs.

    Args:
        step: A key of stages.yaml, or "wfc".

    Returns:
        The titles, in the order the step names them.
    """
    if step == "wfc":
        return [t["title"] for t in doctrine()["wfc"]["tasks"]]
    return yaml.safe_load(STAGES.read_text(encoding="utf-8"))[step]


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
        on = bool(title) and title.group(1) in wanted
        rows.append((title.group(1) if title else re.search(r'name="([^"]*)"',
                                                             m.group(0)).group(1), on))
        return re.sub(r'active="[^"]*"', f'active="{str(on).lower()}"', m.group(0))

    return TASK.sub(one, config), rows


def apply(cfx: Path, steps: list[str], skip: list[str] = ()) -> list[tuple[str, bool]]:
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
    """
    held = running_install(cfx)
    if held:
        raise SystemExit(f"el {held} tiene este proyecto abierto y reescribe el .cfx al salir. "
                         f"Paralo: bin/sqx-worker.sh --role {held} stop")
    wanted = expected if expected is not None else on
    with zipfile.ZipFile(cfx) as z:
        members = {n: z.read(n) for n in z.namelist()}
    config, rows = only(members["config.xml"].decode("utf-8"), on)
    missing = sorted(set(wanted) - {title for title, _ in rows})
    if missing:
        raise SystemExit(f"{cfx.parent.name} no lleva la(s) tarea(s) {', '.join(missing)}. "
                         "Un proyecto de workflow se crea con `sqx.projects.builder --workflow`.")
    members["config.xml"] = config.encode("utf-8")
    with zipfile.ZipFile(cfx, "w", zipfile.ZIP_DEFLATED) as z:
        for name, blob in members.items():
            z.writestr(name, blob)
    return rows


def own(cfx: Path, step: str, skip: list[str] = ()) -> str:
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
