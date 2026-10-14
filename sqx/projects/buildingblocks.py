#!/usr/bin/env python3
"""Write a palette into a project's Build task: which blocks the builder may draw for the free holes, and at what weight."""

import argparse
import json
import re
from pathlib import Path

from core.paths import TAXONOMY, project_dir, worker_dir
from sqx.projects import cfxio
from sqx.blocks import palette
from sqx.blocks.taxonomy import flat, read
from sqx.projects import buildcensus
from typing import Any, TypedDict

BLOCKS = re.compile(r"<BuildingBlocks>.*?</BuildingBlocks>", re.S)
BLOCK = re.compile(r'<Block key="([^"]+)" weight="\d+" use="(?:true|false)"([^>]*)>')


def union(names: list[str]) -> dict[str, dict]:
    """Several palettes resolved as one: a block is on when any of them switches it on.

    Args:
        names: Palette slugs, e.g. ["tendencia_base_v3", "reversion_base_v3"] for a pullback.

    Returns:
        `palette.resolve`'s shape; a block on in several carries the heaviest weight.
    """
    blocks = flat(read(TAXONOMY))
    out = {}
    for name in names:
        for key, r in palette.resolve(palette.load(name), blocks).items():
            if key not in out or (r["use"], r["weight"]) > (
                out[key]["use"],
                out[key]["weight"],
            ):
                out[key] = r
    return out


class Applied(TypedDict):
    """A palette written into a project: its name, the tasks touched and how wide it leaves the search."""

    palette: str
    tasks: Any
    summary: dict[str, Any]


def rewrite(task: str, resolved: dict[str, dict]) -> tuple[str, dict]:
    """Set `use` and `weight` on every `<Block>` of a Build task's `<BuildingBlocks>`.

    Args:
        task: The Build task XML.
        resolved: `palette.resolve` — block key to its `use` and `weight`.

    Returns:
        The task and a count: `on`, `off`, `outside` — the keys the taxonomy does not
        list, switched off: it holds every block the builder can sample, so a key outside it
        is a block no palette was ever asked about — and `refused`, the keys the palette
        asked for and the owner's rule 15 keeps off whatever a palette says: every
        `stopLimitBlocks` entry (the price of a stop or limit ENTRY order, which a build at
        market never places) and every block that reads the clock or the calendar. The task
        namespaces the value blocks (`Indicators.ATR`, `Stop/Limit Price Levels.ATR`) and the
        taxonomy holds the one `ATR`: a palette that switches it on gets the indicator only.
    """
    got = {"on": 0, "off": 0, "outside": [], "refused": []}

    def one(m: re.Match) -> str:
        """One block's opening tag, switched as the palette says."""
        r = resolved.get(m.group(1).rsplit(".", 1)[-1])
        if r is None:
            got["outside"].append(m.group(1))
        use = bool(r and r["use"])
        if use and buildcensus.kind(m.group(1), m.group(2)) in ("level", "clock"):
            got["refused"].append(m.group(1))
            use = False
        got["on" if use else "off"] += 1
        return (
            f'<Block key="{m.group(1)}" weight="{r["weight"] if r else 1}" '
            f'use="{"true" if use else "false"}"{m.group(2)}>'
        )

    section = BLOCKS.search(task)
    assert section is not None
    body = BLOCK.sub(one, section.group(0))
    return task[: section.start()] + body + task[section.end() :], got


def apply(cfx: Path, name: str) -> Applied:
    """Write palette `name` into every Build task of a project, install stopped (hard rule 4).

    Args:
        cfx: The project.cfx.
        name: A palette slug, or several joined by commas — their `union`.

    Returns:
        `palette`, the per-task counts, and the palette's `summary` (condition blocks on,
        inside the owner's band or not). SystemExit when the install holding the file is up.
    """
    up = cfxio.held(cfx)
    if up:
        raise SystemExit(
            f"el {up} está encendido: SQX reescribe {cfx.name} al salir y el "
            f"cambio se perdería. Páralo: bin/sqx-worker.sh --role {up} stop"
        )
    resolved = union(name.split(","))
    members = cfxio.members(cfx)
    tasks = {}
    for n in [n for n in members if n.startswith("Build-")]:
        text, tasks[n] = rewrite(members[n].decode("utf-8"), resolved)
        members[n] = text.encode("utf-8")
    if not tasks:
        raise SystemExit(f"{cfx} no tiene ninguna tarea Build")
    cfxio.write(cfx, members)
    return {"palette": name, "tasks": tasks, "summary": palette.summary(resolved)}


def say(got: Applied) -> None:
    """Print what one `apply` switched."""
    s = got["summary"]
    for task, n in got["tasks"].items():
        print(
            f"{task}: {n['on']} encendidos, {n['off']} apagados"
            + (
                f" ({len(n['outside'])} fuera de la taxonomía, apagados)"
                if n["outside"]
                else ""
            )
            + (
                f" · regla 15: {len(n['refused'])} pedidos y dejados apagados (niveles "
                f"stop/limit, reloj): {', '.join(n['refused'])}"
                if n["refused"]
                else ""
            )
        )
    print(
        f"paleta {got['palette']}: condiciones {s['signal']['on']}/{s['signal']['of']} "
        f"({'dentro' if s['conditions_ok'] else 'FUERA'} de la banda {palette.CONDITIONS}), "
        f"indicadores {s['indicator']['on']}/{s['indicator']['of']}, "
        f"niveles {s['level']['on']}/{s['level']['of']}"
    )


def main() -> None:
    """Apply a palette to a worker's project and say what the builder may now draw."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument(
        "--palette", help="nombre en sqx/blocks/palettes/; varios con comas = su unión"
    )
    ap.add_argument(
        "--count", action="store_true", help="contar lo que la tarea Build lleva"
    )
    ap.add_argument("--json", action="store_true", help="el recuento como JSON")
    ap.add_argument("--role", default="custodian", choices=["conductor", "custodian"])
    a = ap.parse_args()
    cfx = project_dir(a.project, worker_dir(a.role)) / "project.cfx"
    if a.palette:
        say(apply(cfx, a.palette))
    if a.count or not a.palette:
        counted = buildcensus.census(cfx)
        print(
            json.dumps(counted, indent=1, ensure_ascii=False)
            if a.json
            else "\n".join(buildcensus.lines(counted))
        )


if __name__ == "__main__":
    main()
