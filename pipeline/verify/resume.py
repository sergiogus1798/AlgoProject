"""Proof that killing the pipeline mid-stage neither corrupts the ledger nor loses work."""

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from core.paths import ROOT
from pipeline.ledger import state
from pipeline.stages import execute, gates
from pipeline.verify import fixture

MARKER = "PROGRESS"
TARGET = "build"
TIMEOUT, TICK = 20.0, 0.05


def partial(work: Path) -> int | None:
    """How far the target stage has got, if it has started and not finished.

    Args:
        work: The fixture's work directory.

    Returns:
        Its progress while it is strictly under way, else None.
    """
    got = state.read(work)["stages"].get(TARGET, {})
    if got.get("done_at") or not 0 < got.get("progress", 0) < 100:
        return None
    return got["progress"]


def kill_midway(work: Path) -> int:
    """Start the pipeline on the target stage and kill it once it is halfway through.

    Args:
        work: The fixture's work directory.

    Returns:
        The progress the ledger held at the moment of the kill.

    The child gets its own process group and the group is killed, so the stage's own
    subprocess dies with it. SIGKILL rather than SIGTERM: the claim being tested is that
    the ledger survives a machine losing power, not a polite shutdown.
    """
    child = subprocess.Popen([sys.executable, "-m", "pipeline.verify.selftest",
                              "--drive-stage", TARGET], cwd=ROOT, start_new_session=True)
    deadline = time.time() + TIMEOUT
    while time.time() < deadline:
        found = partial(work)
        if found:
            os.killpg(os.getpgid(child.pid), signal.SIGKILL)
            child.wait()
            return found
        time.sleep(TICK)
    child.kill()
    raise SystemExit(f"{TARGET} no llegó a informar progreso parcial en {TIMEOUT} s")


def check(ctx: dict) -> list[str]:
    """Interrupt a mother halfway and start it again. Report what broke.

    Args:
        ctx: What `fixture.build()` returned.

    Returns:
        One line per problem, empty when the pipeline resumed where it was.
    """
    work, problems = fixture.work(), []
    chain = fixture.chain(ctx)
    first = chain[0]
    execute.run(first, work, MARKER)
    before = state.read(work)["stages"][first["name"]]["done_at"]

    at = kill_midway(work)
    try:
        after_kill = state.read(work)
    except json.JSONDecodeError as broken:
        return [f"state.json quedó corrupto tras el kill: {broken}"]
    print(f"   | matado con {TARGET} al {at}%; el registro sigue siendo JSON válido")
    if after_kill["stages"][TARGET].get("done_at"):
        problems.append(f"{TARGET} figura terminada y nunca terminó")

    for stage in chain:
        if gates.done(state.read(work), stage):
            print(f"   | {stage['name']:<10} se salta, ya estaba hecho")
            continue
        print(f"   | {stage['name']:<10} se reanuda")
        execute.run(stage, work, MARKER)
        gates.leaving(stage)
        gates.must(stage)

    ledger = state.read(work)
    if ledger["stages"][first["name"]]["done_at"] != before:
        problems.append(f"{first['name']} se rehízo en vez de saltarse")
    unfinished = [n for n in (s["name"] for s in chain)
                  if not ledger["stages"].get(n, {}).get("done_at")]
    if unfinished:
        problems.append(f"sin terminar tras reanudar: {', '.join(unfinished)}")
    return problems
