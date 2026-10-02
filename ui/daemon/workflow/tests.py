"""The tests of each step: which studies, their state on this project, their configuration in one line."""

from ui.daemon import jobs
from ui.daemon.results import catalogue, forproject, knobs
from ui.daemon.runner import table, where
from ui.daemon.workflow import sources

# The studies that sign their look in the ledger under the template family (owner, Q9 of
# plan 24): without a template in the registry they never start from the window.
SIGNED = {"wfc", "cscv", "marketSurfaces", "snoopingScreen", "blindJoint"}
# What a run of these costs beyond CPU: a look at the reserved oos2, or a ledger row. They are
# never ticked by default nor in «correr todo»; the window asks before each run.
SPENDS = {"wfc": "lee el oos2 y escribe su fila en el ledger",
          "cscv": "lee el oos2 y escribe su fila en el ledger",
          "marketSurfaces": "lee el oos2 y escribe su fila en el ledger",
          "wfm": "lee el oos2 de la Walk Forward Matrix",
          "blindJoint": "lee el oos2 del paso 20 y escribe su fila en el ledger",
          "snoopingScreen": "escribe una fila en el ledger (una búsqueda más de este estudio)"}
SQX_STEP = ("paso de SQX: su tarea se lanza con el ▶ SQX de la tarjeta; su análisis se corre "
            "después con «▶▶ toda la población» en la ficha de una de sus estrategias")
# Jobs that run SQX on a project (`ui/daemon/launch`, `advance`): no test starts on it meanwhile.
LAUNCHERS = ("launch", "advance")
SHOWN = 3   # knobs the one-line summary prints; the drawer shows them all


def keys(spec: dict) -> list[str]:
    """The tests a step offers, evidence first, in order and without repeats.

    Args:
        spec: A row of `steps.STEPS`.

    Returns:
        Study keys: the step's `studies`, then every catalogue study filed under its number,
        then its `extra` readings. Generated from the catalogue, never listed by hand.
    """
    filed = [k for k, row in catalogue.STUDIES.items() if row[3] == spec["n"]]
    if spec.get("only_strategy"):
        filed = []      # step 25 is edgeCost per strategy; step 8 owns the catalogue's row
    return list(dict.fromkeys(spec["studies"] + filed + spec["extra"]))


def summary(key: str, project: str) -> str:
    """A study's configuration in one line: the first knobs and how many there are, with the
    project's feed, symbol and timeframe where the runner puts them (`forproject`).

    Args:
        key: Study key.
        project: Project name.

    Returns:
        e.g. "null.draws=2000 · null.chunk=250 · seed=7 (+9)", or "sin configuración".
    """
    knob_list = [k for s in forproject.apply(key, knobs.sections(key)["sections"], project)
                 for k in s["knobs"]]
    if not knob_list:
        return "sin configuración"
    shown = " · ".join(f"{k['key']}={'⚠ ' if k.get('warn') else ''}{k['value']}"
                       for k in knob_list[:SHOWN])
    return shown + (f" (+{len(knob_list) - SHOWN})" if len(knob_list) > SHOWN else "")


def running(project: str) -> list[dict]:
    """The daemon's jobs on this project that have not ended, running or queued.

    Args:
        project: Project name.

    Returns:
        The public job records, oldest first.
    """
    return [j for j in jobs.listing() if j.get("project") == project and j["rc"] is None]


def one(spec: dict, key: str, ctx: dict, live: list[dict]) -> dict:
    """One test of one step, as the rail paints it.

    Args:
        spec: The step's row of `steps.STEPS`.
        key: Study key.
        ctx: What `api.context` gathered, plus `family`.
        live: What `running` returned.

    Returns:
        `key`, `title`, `state` (done|running|pending|blocked), `why`, `config`, `runnable`,
        `databank` (where its newest result lives, or None), `spends` (what a run costs in
        oos2 or ledger, '' for nothing) and `auto` (ticked by default, in «correr todo»). A
        test of an SQX step — the WFM analysis of 19, the cloud of 16.5 — is shown and never
        runnable from the rail: it is read after the SQX task, from the panel.
    """
    title = catalogue.STUDIES[key][2] if key in catalogue.STUDIES else key
    sqx = next((j for j in live if j["label"] in LAUNCHERS), None)
    refused = (SQX_STEP if spec["kind"] == "sqx" else
               f"SQX trabaja en este proyecto («{sqx.get('study') or sqx['label']}»): sus "
               "databanks cambian; espera a que acabe" if sqx else
               f"bloqueado: {ctx['blind']['text']}" if spec["n"] == "20"
               and ctx["blind"]["sealed"] else table.why_not(key)
               or (where.no_family(ctx["project"]) if key in SIGNED and not ctx["family"]
                   else None))
    only = spec.get("only_strategy", False) if key == "edgeCost" else None
    found = sources.results(ctx["project"], key, only)
    row = {"key": key, "title": title, "config": summary(key, ctx["project"]),
           "runnable": not refused,
           "databank": found[0]["databank"] if found else None, "spends": SPENDS.get(key, ""),
           # ticked by default and in «correr todo»: free to run, and the rail knows where
           "auto": not refused and key not in SPENDS and spec["feeds"] != ()}
    # A job the rail started names its step; one from elsewhere counts for every step.
    job = next((j for j in live if j["study"] == key and j.get("step", spec["n"]) == spec["n"]),
               None)
    if job:
        return row | {"state": "running",
                      "why": f"{job['state'] or 'en marcha'} desde {job['started'][11:16]}"}
    # A result says the test ran, even one the rail cannot launch itself (an SQX step's
    # analysis, a terminal-only study, the MT5 check): «bloqueado» beside it read as not done
    # (📓 2026-09-30, steps 19, 23 and 26 of a finished run).
    if found:
        return row | {"state": "done", "why": f"último resultado del {found[0]['day']}"
                      + (f" sobre {found[0]['databank']}" if found[0]["databank"] else "")}
    if refused:
        return row | {"state": "blocked", "why": refused}
    return row | {"state": "pending", "why": "sin resultado para este proyecto"}


def of_step(spec: dict, ctx: dict, live: list[dict]) -> list[dict]:
    """Every test of one step.

    Args:
        spec: The step's row of `steps.STEPS`.
        ctx: What `api.context` gathered, plus `family`.
        live: What `running` returned.

    Returns:
        One dict per test, as `one` builds it; empty for the steps no study proves.
    """
    return [one(spec, k, ctx, live) for k in keys(spec)]
