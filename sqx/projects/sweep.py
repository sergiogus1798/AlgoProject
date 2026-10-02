"""Which custom projects the weekly cleanup retires: the owner's rule, as code."""

import time
from collections.abc import Callable
from pathlib import Path

from core.datapaths import retire_queue
from sqx.projects import registry

# A workflow project carries 15 to 18 tasks; one with fewer than this is a loose test
# (owner, 2026-09-26: "aquellos que son simplemente unas poquitas tareas, elimínalos").
WORKFLOW_MIN_TASKS = 10
# Unattended nobody can say "I am still on it", so anything touched this recently waits a week.
QUIET_HOURS = 24


def queued() -> list[tuple[str, str]]:
    """The `(role, name)` pairs the owner named, in file order."""
    path = retire_queue()
    if not path.exists():
        return []
    return [tuple(line.split()[:2]) for line in path.read_text(encoding="utf-8").splitlines()
            if len(line.split()) >= 2 and not line.startswith("#")]


def dequeue(role: str, name: str) -> None:
    """Drop one retired pair from the queue, keeping comments and every other line."""
    path = retire_queue()
    if path.exists():
        keep = [line for line in path.read_text(encoding="utf-8").splitlines()
                if line.split()[:2] != [role, name]]
        path.write_text("\n".join(keep) + "\n", encoding="utf-8")


def candidates(installs: dict[str, Path], up: dict[str, bool], stock: set[str],
               describe: Callable[[Path], dict]) -> list[dict]:
    """Every project the rule would retire, and every one it held back and why.

    Args:
        installs: Role → install folder, the master included.
        up: Role → whether that install is running now; a running one is left alone whole.
        stock: Project names never touched.
        describe: `retire.describe`, passed in to avoid a circular import.

    Returns:
        One dict per project looked at: role, name, tasks, mb, action ("retire" or "keep")
        and reason, in Spanish because the owner reads it.
    """
    named = set(queued())
    out = []
    for role, inst in installs.items():
        folders = sorted(p for p in (inst / "user/projects").iterdir()
                         if p.is_dir() and p.name not in stock)
        for p in folders:
            if role == "master" and (role, p.name) not in named:
                continue   # the master is the owner's: only what he named is ever looked at
            d = describe(p)
            row = {"role": role, "name": p.name, "tasks": d["tasks"], "mb": round(d["mb"])}
            age_h = (time.time() - d["mtime"]) / 3600
            kind = registry.kind(p.name)
            if up[role]:
                row.update(action="keep", reason=f"el {role} está encendido")
            elif age_h < QUIET_HOURS:
                row.update(action="keep", reason=f"tocado hace {age_h:.0f} h")
            elif (role, p.name) in named:
                row.update(action="retire", reason="en la cola que nombró el dueño")
            elif kind == "trade":
                row.update(action="keep", reason="Trade_: se queda hasta que el dueño diga")
            elif kind == "research":
                row.update(action="keep", reason="Research_: sin decidir si se tira o se queda "
                                                 "(pregunta abierta al dueño)")
            elif kind == "test":
                row.update(action="retire", reason="Test_: ya respondió")
            elif isinstance(d["tasks"], int) and d["tasks"] < WORKFLOW_MIN_TASKS:
                row.update(action="retire", reason=f"{d['tasks']} tareas: no es un workflow")
            else:
                row.update(action="keep", reason=f"{d['tasks']} tareas: workflow entero")
            out.append(row)
    return out
