"""One action of the tail's plan, run: the dispatch from its kind to the module that does it."""

from pathlib import Path

from pipeline.autopilot import blind, closing, finalists, kept, neighbours, survivors

# `neighbours` is not the tail's: step 13's T1 batch is dispatched here like the tail's batches.
KINDS = {"blind", "wfm", "kept", "ledger", "joint", "reading", "finalists", "mt5verify",
         "neighbours", "oos2read"}


def run(action: dict, project: str, role: str, out: Path, cfg: dict) -> str:
    """Run one action of `tail.walk`.

    Args:
        action: {n, kind, tests, …} with `redo` and `oos2`, `databank` or `params` where its
            kind has one.
        project: Project name.
        role: The worker holding the project.
        out: The autopilot run's folder; its name stamps the batches.
        cfg: `judge.settings()`.

    Returns:
        What it did, one line for resumen.md — never a number of 17, 18 or 19.

    Raises:
        survivors.Done: Nothing is left to walk: a clean stop, not a failure.
    """
    kind, n = action["kind"], action["n"]
    if kind == "mt5verify":
        return finalists.verify(project, action["params"], out)
    if kind == "neighbours":      # who ENTERS step 13, not who a later step's cut left
        return neighbours.run(project, role, neighbours.entering(project, role), out.name)
    # The finalists are who is left after step 26's own cut, the day it has one.
    mothers = survivors.mothers(project, role, cfg, "26" if kind == "finalists" else n)
    if kind == "blind":
        return blind.look(project, n, action["tests"][0], mothers, action["redo"],
                          action.get("oos2", True))
    if kind == "wfm":
        return blind.wfm(project, role)
    if kind == "ledger":
        return blind.register(project, mothers)
    if kind == "joint":
        return blind.joint(project)
    if kind == "reading":
        return closing.reading(project, action["tests"][0], action["databank"], mothers)
    if kind == "oos2read":
        return blind.oos2read(project)
    if kind == "kept":
        return kept.save(project, blind.bank(project))
    return finalists.write(project, mothers, out)
