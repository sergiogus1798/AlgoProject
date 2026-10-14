"""«Correr workflow», before the press: whether the chain may start, what it would run, the sentence to confirm."""

from typing import Any

from ui.daemon.advance import preflight as advance
from ui.daemon.launch import chainplan, preflight
from ui.daemon.workflow import api as workflow


def check(project: str) -> dict[str, Any]:
    """Whether the chain may start now, what it would run and where it would stop.

    Args:
        project: Project name.

    Returns:
        `ok`, `reasons`, `plan` (`chainplan.plan`), `install`, `role`. Refused on the master,
        on a worker someone uses (`advance.busy`, the same preflight as every launcher),
        with nothing to run, and when the first SQX step cannot start as it stands; a later
        SQX step is only checked for its tasks now, and fully just before it starts.
    """
    plan = chainplan.plan(workflow.workflow(project))
    where = advance.where(project)
    if "refuse" in where:
        return {"ok": False, "reasons": [where["refuse"]], "plan": plan}
    reasons = advance.busy(where["role"], project)
    if not plan["do"]:
        reasons.append(
            f"nada que correr: se para ya en el paso {plan['stop']['n']} — "
            f"{plan['stop']['why']}"
            if plan["stop"]["n"]
            else plan["stop"]["why"]
        )
    filled: set[str] = set()  # outputs of the SQX steps planned before this one
    for action in [a for a in plan["do"] if a["kind"] == "sqx"]:
        pre = preflight.check(project, step=action["n"], filled=filled)
        action["titles"] = [t["title"] for t in pre.get("chosen", [])]
        filled |= {t["output"] for t in pre.get("chosen", [])}
        reasons += [
            f"paso {action['n']}: {r}" for r in pre["reasons"] if r not in reasons
        ]
    return {"ok": not reasons, "reasons": reasons, "plan": plan, **where}


def text(got: dict[str, Any], project: str) -> str:
    """The sentence the owner confirms: every step that runs, where, and where it stops."""
    who = preflight.ROLES.get(got["role"], got["role"])
    lines = [f"«Correr workflow» en {project} ({got['install']}), en este orden:"]
    for a in got["plan"]["do"]:
        lines.append(
            f"· paso {a['n']} · {a['title']} — "
            + (
                f"SQX en el {who}: {', '.join(a['titles'])}; el worker arranca, corre hasta "
                "«Project finished» y se para"
                if a["kind"] == "sqx"
                else f"Python: {', '.join(a['tests'])}"
            )
        )
    stop = got["plan"]["stop"]
    lines.append(
        f"Se para antes del paso {stop['n']} · {stop['title']}: {stop['why']}."
        if stop["n"]
        else f"Y termina: {stop['why']}."
    )
    return "\n".join(lines + ["", chainplan.RULE])
