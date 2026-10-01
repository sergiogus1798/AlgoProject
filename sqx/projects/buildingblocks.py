#!/usr/bin/env python3
"""Write a palette into a project's Build task: which blocks the builder may draw for the free holes, and at what weight."""

import argparse
import re
import zipfile
from pathlib import Path

from core.paths import TAXONOMY, project_dir, worker_dir
from sqx.blocks import palette
from sqx.blocks.taxonomy import flat, read
from sqx.projects.configure import running_install

BLOCKS = re.compile(r"<BuildingBlocks>.*?</BuildingBlocks>", re.S)
BLOCK = re.compile(r'<Block key="([^"]+)" weight="\d+" use="(?:true|false)"')


def rewrite(task: str, resolved: dict[str, dict]) -> tuple[str, dict]:
    """Set `use` and `weight` on every `<Block>` of a Build task's `<BuildingBlocks>`.

    Args:
        task: The Build task XML.
        resolved: `palette.resolve` — block key to its `use` and `weight`.

    Returns:
        The task and a count: `on`, `off`, and `outside`, the keys the taxonomy does not
        list, switched off — the taxonomy holds every block the builder can sample, so a
        key outside it is a block no palette was ever asked about. The task namespaces the
        value blocks (`Indicators.ATR`, `Stop/Limit Price Levels.ATR`); the taxonomy holds
        the one `ATR`, so a palette switches a value block in both roles at once.
    """
    got = {"on": 0, "off": 0, "outside": []}

    def one(m: re.Match) -> str:
        """One block's opening tag, switched as the palette says."""
        r = resolved.get(m.group(1).rsplit(".", 1)[-1])
        if r is None:
            got["outside"].append(m.group(1))
        use = bool(r and r["use"])
        got["on" if use else "off"] += 1
        return (f'<Block key="{m.group(1)}" weight="{r["weight"] if r else 1}" '
                f'use="{"true" if use else "false"}"')

    section = BLOCKS.search(task)
    body = BLOCK.sub(one, section.group(0))
    return task[:section.start()] + body + task[section.end():], got


def apply(cfx: Path, name: str) -> dict:
    """Write palette `name` into every Build task of a project, install stopped (hard rule 4).

    Returns:
        `palette`, the per-task counts, and the palette's `summary` (condition blocks on,
        inside the owner's band or not). SystemExit when the install holding the file is up.
    """
    up = running_install(cfx)
    if up:
        raise SystemExit(f"el {up} está encendido: SQX reescribe {cfx.name} al salir y el "
                         f"cambio se perdería. Páralo: bin/sqx-worker.sh --role {up} stop")
    p = palette.load(name)
    resolved = palette.resolve(p, flat(read(TAXONOMY)))
    with zipfile.ZipFile(cfx) as z:
        members = {n: z.read(n) for n in z.namelist()}
    tasks = {}
    for n in [n for n in members if n.startswith("Build-")]:
        text, tasks[n] = rewrite(members[n].decode("utf-8"), resolved)
        members[n] = text.encode("utf-8")
    if not tasks:
        raise SystemExit(f"{cfx} no tiene ninguna tarea Build")
    with zipfile.ZipFile(cfx, "w", zipfile.ZIP_DEFLATED) as z:
        for n, blob in members.items():
            z.writestr(n, blob)
    return {"palette": name, "tasks": tasks, "summary": palette.summary(resolved)}


def main() -> None:
    """Apply a palette to a worker's project and say what the builder may now draw."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--palette", required=True, help="nombre en sqx/blocks/palettes/")
    ap.add_argument("--role", default="custodian", choices=["conductor", "custodian"])
    a = ap.parse_args()
    got = apply(project_dir(a.project, worker_dir(a.role)) / "project.cfx", a.palette)
    s = got["summary"]
    for task, n in got["tasks"].items():
        print(f"{task}: {n['on']} encendidos, {n['off']} apagados"
              + (f" ({len(n['outside'])} fuera de la taxonomía, apagados)" if n["outside"] else ""))
    print(f"paleta {got['palette']}: condiciones {s['signal']['on']}/{s['signal']['of']} "
          f"({'dentro' if s['conditions_ok'] else 'FUERA'} de la banda {palette.CONDITIONS}), "
          f"indicadores {s['indicator']['on']}/{s['indicator']['of']}, "
          f"niveles {s['level']['on']}/{s['level']['of']}")


if __name__ == "__main__":
    main()
