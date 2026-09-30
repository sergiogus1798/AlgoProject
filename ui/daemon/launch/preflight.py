"""Whether «Lanzar en SQX» may start one task of a project now, and every reason it may not.

The worker checks are «Continuar workflow»'s own (`advance.preflight.where` and `busy`): the
master refused first, a worker already up refused and never stopped (the owner lock, its port
or a live SQX process — OPEN.md §32), the day's SQX log still moving with no sign it is this
job's own. Another project of the worker touched a while ago is not a refusal (OPEN.md §83):
one task at a time per worker, and the moment one finishes, launching another is fine. Read-only.
"""

from core.paths import databank_dir, project_dir
from sqx.projects import crosstfload
from ui.daemon import progress
from ui.daemon.advance import confirm, preflight as advance
from ui.daemon.launch import steps as launchsteps

BUILD = "Build"
ROLES = {"custodian": "custodio", "conductor": "conductor"}   # the owner's words for the workers
# What the run does to a databank `crosstfload` fills, said in the confirmation.
FILLS = {"CrossTF_Input": "· Antes de arrancar (paso 10.5), con el worker parado: las "
                          "supervivientes de Cross Market se escalan a los timeframes de "
                          "`crosstf.timeframes` y se cargan con sus hermanas en «CrossTF_Input», "
                          "que se vacía antes; «CrossTF» corre el timeframe de la madre, y cada "
                          "otro, su tarea «CrossTF <TF>» (D1 con el motor de MT4).",
         "CrossTF_Mothers": "· Antes de arrancar, con el worker parado: las madres que tiene "
                            "«CrossTF», sin sus hermanas escaladas, se copian a «CrossTF_Mothers» "
                            "(que se vacía antes): es lo que lee el MC Retest."}


def count(project: str, databank: str, role: str) -> int:
    """How many .sqx one databank holds on the worker's disk now."""
    folder = databank_dir(project, databank, advance.WORKERS[role]["path"])
    return len(list(folder.glob("*.sqx"))) if folder.is_dir() else 0


def tasks(project: str) -> dict:
    """A project's SQX tasks as the window lists them.

    Args:
        project: Project name.

    Returns:
        `role`, `install`, `row` and `tasks` — each {title, type, input, output, n_in,
        n_out}, in the project's order, the counts read off the worker's disk — or `refuse`
        with the one reason (the master's first).
    """
    got = advance.where(project)
    if "refuse" in got:
        return got
    cfx = project_dir(project, advance.WORKERS[got["role"]]["path"]) / "project.cfx"
    if not cfx.exists():
        return {"refuse": f"{project} no está en {got['install']}"}
    rows = [{"title": t["title"], "type": t["type"], "input": t["input"], "output": t["output"],
             "n_in": count(project, t["input"], got["role"]) if t["input"] else 0,
             "n_out": count(project, t["output"], got["role"]) if t["output"] else 0}
            for t in progress.tasks(cfx) if t["title"]]
    return {**got, "cfx": cfx, "tasks": rows}


def check(project: str, titles: str | list[str] = (), step: str = "",
          own_log: bool = False, filled: set[str] = frozenset()) -> dict:
    """Every precondition of launching one task, or every task of one workflow step, together.

    Args:
        project: Project name.
        titles: The task title(s), as SQX shows them; ignored when `step` is given.
        step: A workflow step's number: its tasks, as `steps.of_step` picks them.
        own_log: The chain has just run this project on the worker: the log it wrote itself
            in the last minutes is no sign of anyone else (every other check stays).
        filled: Databanks an earlier step of the same chain writes: empty now, not a refusal.

    Returns:
        `ok`, `reasons` (empty when ok), `elsewhere` (the one reason is the step not being an
        SQX task at all — not a failure) and what the confirmation and the run need: `role`,
        `install`, `row`, `cfx`, `chosen` (the rows of `tasks`, in order), `off` (a step's
        titles left off, and why), `step`.
    """
    got = tasks(project)
    if "refuse" in got:
        return {"ok": False, "reasons": [got["refuse"]]}
    reasons = advance.busy(got["role"], project, own_log)
    return judge(project, got, reasons, titles, step, filled)


def judge(project: str, got: dict, reasons: list[str], titles: str | list[str] = (),
          step: str = "", filled: set[str] = frozenset()) -> dict:
    """`check` once the project's tasks and the worker's state are read: the rail asks for
    every SQX step at once and reads them once.

    Args:
        project: Project name.
        got: What `tasks` returned, not a refusal.
        reasons: The worker's refusals (`advance.busy`), a copy this call may extend.
        titles, step, filled: As `check`.

    Returns:
        As `check`.
    """
    reasons = list(reasons)
    off = {}
    if step:
        picked = launchsteps.of_step(step, got["cfx"])
        if "refuse" in picked:
            return {"ok": False, "reasons": reasons + [picked["refuse"]],
                    "elsewhere": picked.get("elsewhere", False)}
        titles, off = picked["titles"], picked["off"]
    titles = [titles] if isinstance(titles, str) else list(titles)
    rows = {t["title"]: t for t in got["tasks"]}
    missing = [t for t in titles if t not in rows]
    if missing or not titles:
        return {"ok": False, "reasons": reasons + [f"{project} no lleva ninguna tarea «{t}»"
                                                   for t in missing or ["?"]]}
    chosen = [rows[t] for t in titles]
    made = {t["output"] for t in chosen} | set(filled)   # filled before this task reads it
    # CrossTF_Input and CrossTF_Mothers are no task's output: the run fills them from their
    # feeder just before the start (`crosstfload`), so an empty one is not a refusal.
    fed = crosstfload.feeders({t["title"]: {"Input": t["input"], "Output": t["output"]}
                               for t in got["tasks"]})
    fill = sorted({t["input"] for t in chosen if t["input"] in fed})
    for t in chosen:
        if t["type"] == BUILD and got["role"] != "custodian":
            reasons.append(f"un build va al custodio, y {project} vive en el "
                           f"{ROLES.get(got['role'], got['role'])} (CLAUDE.md, regla 3: el "
                           "conductor es para trabajos cortos)")
        src = fed.get(t["input"])
        if src and src not in made and not count(project, src, got["role"]):
            reasons.append(f"«{t['input']}» se llena desde «{src}», que no tiene ninguna "
                           f"estrategia en {got['install']}: «{t['title']}» no tendría nada "
                           "que probar")
        elif (not src and t["type"] != BUILD and t["input"] and t["input"] not in made
              and not t["n_in"]):
            reasons.append(f"«{t['input']}» no tiene ninguna estrategia en {got['install']}: "
                           f"«{t['title']}» no tendría nada que probar")
    return {"ok": not reasons, "reasons": reasons, **got, "chosen": chosen, "off": off,
            "step": step, "fill": fill,
            "configure": launchsteps.unconfigured(got["cfx"], titles)}


def text(pre: dict, project: str) -> str:
    """The sentence the owner confirms before anything is written or started.

    Args:
        pre: What `check` returned, ok.
        project: Project name.

    Returns:
        What runs, where, what each task reads and writes now, and that the worker stops.
    """
    chosen, who = pre["chosen"], ROLES.get(pre["role"], pre["role"])
    names = ", ".join(f"«{t['title']}»" for t in chosen)
    what = (f"el paso {pre['step']} ({names})" if pre["step"] else
            f"«{chosen[0]['title']}» ({chosen[0]['type']})" if len(chosen) == 1 else names)
    out = [f"Se va a lanzar {what} de {project} en {pre['install']}. Solo "
           f"{'esa tarea quedará activa' if len(chosen) == 1 else 'esas tareas quedarán activas'}"
           f"; el {who} arranca una vez, corre hasta «Project finished» y se para."]
    for t in chosen:
        if t["type"] == BUILD:
            out.append(f"· «{t['title']}»: un build ocupa todos los núcleos del custodio y puede "
                       f"durar horas. Escribe en «{t['output']}», que hoy tiene {t['n_out']} "
                       "estrategias.")
        else:
            out.append(f"· «{t['title']}»: lee «{t['input']}» ({t['n_in']} estrategias) y "
                       f"escribe en «{t['output']}» (hoy {t['n_out']})."
                       + (confirm.held_note(t["output"], t["n_out"]) if t["n_out"] else ""))
    out += [f"· «{t}» no se lanza: {why}" for t, why in pre["off"].items()]
    out += [f"· {', '.join(f'«{t}»' for t in ts)} sin configurar: antes de arrancar se configura "
            f"con `{module}` desde assets/ (lo mismo que su skill); una tarea ya configurada no "
            "se toca." for module, ts in pre.get("configure", {}).items()]
    out += [FILLS[bank] for bank in pre.get("fill", [])]
    return "\n".join(out) + ("\nLo que cada tarea borre al empezar lo decide su configuración "
                             "en SQX; antes se copia el proyecto y al acabar se comparan los "
                             "databanks.")
