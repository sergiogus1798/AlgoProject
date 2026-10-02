"""Each step's state, funnel and Spanish why, from what the disk and the ledger hold."""

from core.assetcheck import pending, provisional, validate
from core.assetdata import load
from sqx.projects.stage import titles
from ui.daemon import jobs
from ui.daemon.workflow import sources

BLIND = ("17", "18", "19")


def step(state: str, why: str, n_in: int | None = None, n_out: int | None = None,
         day: str | None = None) -> dict:
    """The fields a step gets besides its row of `STEPS`."""
    return {"state": state, "why": why, "in": n_in, "out": n_out, "day": day}


def template(spec: dict, ctx: dict) -> dict:
    """Steps 1-3: done when a template is tied to the project, missing otherwise."""
    name, source = ctx["template"]
    if not name:
        return step("missing", "Ningún registro enlaza este proyecto con su plantilla "
                               "(runs.csv, projects/registry.csv, familia del ledger): sin ella "
                               "la idea, el vocabulario y la plantilla no se leen del disco.")
    return step("done", {"1": f"La idea es la de la plantilla {name}; su brief.md la guarda.",
                         "2": f"La plantilla {name} existe, así que sus bloques se instalaron; "
                              "el paso 2 no deja registro propio.",
                         "3": f"Plantilla {name}, enlazada por {source}."}[spec["n"]])


def preflight(spec: dict, ctx: dict) -> dict:
    """Step 4: `core.assetcheck` on the asset, as it stands today."""
    if not ctx["asset"]:
        return step("missing", "No se sabe el activo del proyecto: ni el ledger ni el nombre.")
    data = load(ctx["asset"])
    stop = validate(data) + pending(data)
    if stop:
        return step("blocked", f"El preflight de {ctx['asset']} se niega hoy: "
                               f"{', '.join(stop)} sin valor pactado. Del dueño.")
    soft = provisional(data)
    return step("done", f"El preflight de {ctx['asset']} pasa hoy: su ficha en Activos tiene "
                        "decididos los costes que exige su clase y sus tramos caben en sus datos"
                        + (f"; costes PROVISIONALES: {', '.join(soft)}" if soft else "") + ".")


def project(spec: dict, ctx: dict) -> dict:
    """Step 5: the project's folder in an install."""
    view = ctx["sqx"]
    if not view:
        return step("missing", "El proyecto no está en ninguna instalación (¿retirado?): "
                               "sus tareas no se pueden leer.")
    return step("done", f"Vive en {view['role']}: {view['folder']}.",
                day=sources.day_of(view["folder"] / "project.cfx"))


def sqx(spec: dict, ctx: dict) -> dict:
    """An SQX step: its tasks' output on disk, today's runs, the install log's current task."""
    view = ctx["sqx"]
    if not view:
        return step("missing", "El proyecto no está en ninguna instalación: no hay tareas.")
    names = titles(spec["stage"])
    tasks = [t for t in view["tasks"] if t["title"] in names]
    if not tasks:
        return step("missing", f"El proyecto no tiene las tareas {', '.join(names)}.")
    run = view["run"]
    cut = run["project"] == ctx["project"] and not run["finished"] and run["current"] in names
    # A run killed before «Project finished» leaves the log saying «started» all day: running
    # only while an SQX process of the install lives (as `advance.busy`, 2026-09-28).
    if cut and view["alive"]:
        return step("running", f"SQX corre «{run['current']}» en {view['role']}"
                               + (f", {run['percent']} %" if run["percent"] is not None else ""))
    killed = (f"El log dice que «{run['current']}» empezó y no terminó, y ningún proceso de SQX "
              f"vive en {view['role']}: se cortó. " if cut else "")
    held = {t["title"]: view["banks"].get(t["output"], 0) for t in tasks}
    runs = [r for r in view["runs"] if r["title"] in names and r["finished"]]
    tested = [r for r in runs if "tested" in r]
    listing = ", ".join(f"{t}: {n}" for t, n in held.items())
    if not any(held.values()) and not runs:
        armed = [t["title"] for t in tasks if t["active"]]
        return step("pending", f"{killed}Ninguna tarea ha dejado estrategias ({listing})"
                               + (f"; activas para el próximo start: {', '.join(armed)}"
                                  if armed else "") + ".")
    if tested:
        n_in, n_out = tested[-1]["tested"], tested[-1]["passed"]
        how = f"Hoy «{tested[-1]['title']}» probó {n_in} y pasaron {n_out}"
    else:
        n_in = view["banks"].get(tasks[0]["input"]) if spec["stage"] != "build" else None
        n_out = held[tasks[-1]["title"]]
        how = "Sin run de hoy en el log del proyecto: cuentas del databank"
    day = (runs[-1]["started"][:10] if runs else
           sources.day_of(view["folder"] / "databanks" / tasks[-1]["output"]))
    return step("done", f"{killed}{how}. En disco: {listing}"
                        + sources.curated(ctx["project"], tasks[-1]["output"]) + ".",
                n_in, n_out, day)


def running_job(ctx: dict, spec: dict) -> dict | None:
    """A job of this daemon still running one of the step's studies on this project; a job
    the rail started names its step, so edgeCost of step 8 does not light step 25."""
    return next((j for j in jobs.listing() if j["rc"] is None
                 and j.get("project") == ctx["project"]
                 and j.get("step", spec["n"]) == spec["n"]
                 and any(k in " ".join(j["argv"]) for k in spec["studies"])), None)


def study(spec: dict, ctx: dict) -> dict:
    """A Python step: the newest contract result of its studies, and its funnel."""
    only = spec.get("only_strategy", False) if "edgeCost" in spec["studies"] else None
    found = {k: sources.results(ctx["project"], k, only if k == "edgeCost" else None)
             for k in spec["studies"]}
    key = next((k for k in spec["studies"] if found[k]), None)
    if key is None:
        job = running_job(ctx, spec)
        if job:
            return step("running", f"La ventana corre {job['label']} desde {job['started']}.")
        return step("pending", f"Ningún resultado de {', '.join(spec['studies'])} "
                               "para este proyecto.")
    newest = found[key][0]
    if newest["databank"] is None:
        n = len(found[key])
        return step("done", f"{key}: {n} lote(s) con resultado, el último del {newest['day']}.",
                    n, n, newest["day"])
    n_in, n_out, words = sources.funnel(newest)
    also = [k for k in spec["studies"] if k != key and found[k]]
    return step("done", f"{key} sobre {newest['databank']} del {newest['day']}"
                        + (f": {words}" if words else "")
                        + (f". También: {', '.join(also)}" if also else "") + ".",
                n_in, n_out, newest["day"])


def variants(spec: dict, ctx: dict) -> dict:
    """Step 16.5: the mothers' batches, and the WFC legs while SQX runs them."""
    if ctx["sqx"]:
        live = sqx(spec, ctx)
        if live["state"] == "running":
            return live
    mothers, collected, day = sources.variants(ctx["project"])
    if collected:
        return step("done", f"{collected} de {mothers} madre(s) con su lote cosechado.",
                    mothers, collected, day)
    return step("pending", f"{mothers} madre(s) preparadas, ninguna cosechada." if mothers
                else "Sin lotes en strategyPermutations/ para este proyecto.")


def bank(spec: dict, ctx: dict) -> dict:
    """Step 10.5: the siblings waiting in their input databank."""
    held = ctx["sqx"]["banks"].get(spec["bank"], 0) if ctx["sqx"] else 0
    if not held:
        return step("pending", f"El databank {spec['bank']} está vacío o no existe.")
    return step("done", f"{held} estrategias escaladas en {spec['bank']}.", None, held,
                sources.day_of(ctx["sqx"]["folder"] / "databanks" / spec["bank"]))


def blind(spec: dict, ctx: dict) -> dict:
    """Step 20: blocked while the ledger's door is shut, else its own result."""
    if ctx["blind"]["sealed"]:
        return step("blocked", ctx["blind"]["text"])
    return study(spec, ctx)


def seal(spec: dict, row: dict, ctx: dict) -> dict:
    """Steps 17-19 while the door is shut: a finished one is shown as an envelope, no numbers."""
    if spec["n"] not in BLIND or not ctx["blind"]["sealed"]:
        return row
    logged = spec["n"] in ctx["blind"]["done"]
    if row["state"] != "done" and not logged:
        return row
    return step("sealed", ("Hecho y apuntado en el ledger" if logged else
                           "Hay resultado en disco pero ninguna fila en el ledger "
                           "(python3 -m ledger.backfill --blind)")
                + f". Sellado: {ctx['blind']['text']}", day=row["day"])


HOW = {"template": template, "preflight": preflight, "project": project, "sqx": sqx,
       "study": study, "variants": variants, "bank": bank, "blind": blind}
