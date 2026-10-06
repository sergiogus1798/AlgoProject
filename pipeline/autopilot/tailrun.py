"""One action of the tail's plan, run: the dispatch from its kind to the module that does it."""

from pathlib import Path

from pipeline.autopilot import blind, closing, finalists, survivors, traded

KINDS = {"blind", "wfm", "ledger", "joint", "reading", "structural", "stop", "edge",
         "finalists", "mt5verify"}


def run(action: dict, project: str, role: str, out: Path, cfg: dict) -> str:
    """Run one action of `tail.walk`.

    Args:
        action: {n, kind, tests, …} with `redo`, `databank` or `params` where its kind has one.
        project: Project name.
        role: The worker holding the project.
        out: The autopilot run's folder; its name stamps the batches of 23 and 24.
        cfg: `judge.settings()`.

    Returns:
        What it did, one line for resumen.md — never a number of 17, 18 or 19.

    Raises:
        survivors.Done: Nothing is left to walk: a clean stop, not a failure.
    """
    kind, n = action["kind"], action["n"]
    if kind == "mt5verify":
        return finalists.verify(project, action["params"], out)
    # The finalists are who is left after step 25's own cut, the day it has one.
    mothers = survivors.mothers(project, role, cfg, "26" if kind == "finalists" else n)
    if kind == "blind":
        return blind.look(project, n, action["tests"][0], mothers, action["redo"])
    if kind == "wfm":
        return blind.wfm(project, role)
    if kind == "ledger":
        return blind.register(project, mothers)
    if kind == "joint":
        return blind.joint(project)
    if kind == "reading":
        return closing.reading(project, action["tests"][0], action["databank"], mothers)
    if kind == "structural":
        return closing.structural(project, role, mothers, out.name)
    if kind == "stop":
        return closing.stop(project, role, mothers, out.name)
    if kind == "edge":
        return traded.edge(project, mothers)
    return finalists.write(project, mothers, out)
