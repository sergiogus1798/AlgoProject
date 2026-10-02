#!/usr/bin/env python3
"""The queue of a proposal's ideas: one after another on the custodian, each through five steps.

    python3 -m ui.daemon.research.queue --proposal <id>

The window queues it after the owner's confirmation; it is the only thing here that reaches SQX.
"""

import argparse
import signal
import sys
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from studies.research.board import proposal, store
from ui.daemon.research import steps

ORDER = ("activos", "plantilla", "proyecto", "paleta", "autopilot")
PREFIX = "Research_"       # owner, 2026-10-02: the research director's projects, no choice


def path(proposal_id: str) -> Path:
    """Where a proposal's queue state lives."""
    top = store.proposals_dir() / "queues"
    top.mkdir(exist_ok=True)
    return top / f"{proposal_id}.json"


def project_name(p: dict, template: str) -> str:
    """`Research_<SYMBOL>_<template>_<TF>`, the name `/workflow-start` gives a run."""
    return f"{PREFIX}{p['cell']['symbol']}_{template}_{p['cell']['timeframe']}"


def initial(p: dict) -> dict:
    """The queue before anything ran: launchable ideas wait, the rest say why they will not go."""
    ideas = []
    for i in p["ideas"]:
        ok, why = proposal.launchable(i)
        ideas.append({"name": i["name"], "step": "", "project": "", "error": "",
                      "state": "esperando" if ok else ("vetada" if i.get("vetoed") else "pregunta"),
                      "note": why})
    return {"proposal": p["id"], "state": "en marcha", "ideas": ideas,
            "started": datetime.now().isoformat(timespec="seconds"), "finished": ""}


def run(p: dict, runners: dict[str, Callable[[dict], None]],
        save: Callable[[dict], None]) -> dict:
    """Take every launchable idea through the five steps, in the proposal's order.

    An idea whose template or palette step comes back with a question (`steps.Question`, hard
    rule 11) is set aside and the next one goes on; any other failure halts the queue, the
    ideas behind it left waiting — as the window's other launchers stop at the first failure.

    Args:
        p: The stamped proposal.
        runners: Step name → the function that runs it on a context dict (`steps.RUNNERS`;
            fakes in the tests). A runner may set `ctx["template"]`.
        save: Called with the whole state after every change.

    Returns:
        The final state: `state` is `terminada` or `parada`, each idea `hecha`, `falló`,
        `pregunta`, `vetada` or still `esperando`.
    """
    q = initial(p)
    save(q)
    for row, idea in zip(q["ideas"], p["ideas"]):
        if row["state"] != "esperando":
            continue
        ctx = {"proposal": p, "idea": idea, "template": idea["name"],
               "symbol": p["cell"]["symbol"], "timeframe": p["cell"]["timeframe"],
               "ran_before": any(r["step"] == "autopilot" or r["state"] == "hecha"
                                 for r in q["ideas"])}
        row["state"] = "en marcha"
        try:
            for name in ORDER:
                ctx["project"] = row["project"] = project_name(p, ctx["template"])
                row["step"] = name
                save(q)
                print(f"PROGRESS {100 * q['ideas'].index(row) // len(q['ideas'])} "
                      f"{row['name']}: {name}", flush=True)
                runners[name](ctx)
            row["state"], row["step"] = "hecha", ""
        except steps.Question as asked:
            row["state"], row["note"] = "pregunta", str(asked)
        except steps.Failed as failed:
            row["state"], row["error"], q["state"] = "falló", str(failed), "parada"
            break
        finally:
            save(q)
    q["state"] = "terminada" if q["state"] == "en marcha" else q["state"]
    q["finished"] = datetime.now().isoformat(timespec="seconds")
    save(q)
    return q


def main() -> None:
    """Run a proposal's queue for real; a SIGTERM ends the running step's child first."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--proposal", required=True)
    a = ap.parse_args()
    signal.signal(signal.SIGTERM, steps.terminate)
    q = run(proposal.load(a.proposal), steps.RUNNERS,
            lambda state: store.write(path(a.proposal), state))
    print("PROGRESS 100 cola " + q["state"], flush=True)
    sys.exit(0 if q["state"] == "terminada" else 1)


if __name__ == "__main__":
    main()
