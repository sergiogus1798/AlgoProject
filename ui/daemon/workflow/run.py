"""The rail's run buttons: ticked tests into the runner's jobs, and the backfill of the blind steps' rows."""

import pandas as pd

from core.paths import DATA
from sqx.projects.stage import titles
from ui.daemon import jobs, runs
from ui.daemon.runner import batch, table, where
from ui.daemon.workflow import sources, tests
from ui.daemon.workflow.derive import BLIND
from ui.daemon.workflow.steps import STEPS

BY_N = {s["n"]: s for s in STEPS}
ROOTS = ("raw", "harvest", "metrics", "reports")


def databanks(spec: dict, key: str, ctx: dict) -> list[str]:
    """Where a test of this step may read, most likely first.

    Args:
        spec: The step's row of `steps.STEPS`.
        key: Study key.
        ctx: What `api.context` gathered.

    Returns:
        The databank of the study's newest result on this project, then the output
        databanks of the SQX stages the step `feeds` on, as the data root spells them
        (spaces become `_`) and only those the data root holds. Empty when the step reads
        the databank the panel shows.
    """
    found = [r["databank"] for r in sources.results(ctx["project"], key)[:1] if r["databank"]]
    tasks = ctx["sqx"]["tasks"] if ctx["sqx"] else []
    for stage in spec["feeds"]:
        names = titles(stage)
        found += [t["output"].replace(" ", "_") for t in tasks if t["title"] in names]
    held = [d for d in dict.fromkeys(found)
            if any((DATA / root / ctx["project"] / d).is_dir() for root in ROOTS)]
    return held


def population(project: str, databank: str, asset: str) -> list[str]:
    """Every strategy of a databank: its newest export's, else its newest cosecha's.

    Args:
        project, databank, asset: Where.

    Returns:
        Strategy names as SQX spells them; empty when neither input exists.
    """
    c = runs.context(project, databank, "", asset)
    if c["export"]:
        return where.distinct(c["trades"], "strategy")
    if c["harvest"]:
        return sorted(pd.read_parquet(c["harvest_dir"] / "metrics.parquet",
                                      columns=["strategy"])["strategy"].astype(str))
    return []


def mothers(project: str) -> list[str]:
    """The mothers with a variant batch folder, as `core.datapaths.variants_dir` names them."""
    root = DATA / "strategyPermutations" / project
    return sorted(d.name for d in root.iterdir() if d.is_dir()) if root.is_dir() else []


def plan(spec: dict, key: str, ctx: dict, databank: str, picked: list[str]) -> list[dict] | str:
    """The jobs one ticked test starts, or why none.

    Args:
        spec: The step's row of `steps.STEPS`.
        key: Study key.
        ctx: What `api.context` gathered.
        databank: The databank the panel shows, or '' when the rail pressed it.
        picked: Strategies chosen in the panel; empty means the whole population.

    Returns:
        What `runner.table.jobs` returned for the first databank where the study finds its
        input, or the sentence of the most likely one. A study with a population command
        runs once over the databank; a one-strategy study runs once per strategy, all of
        them queued at once so `jobs.py` runs them side by side.
    """
    if spec["n"] == "20" and ctx["blind"]["sealed"]:
        return f"bloqueado: {ctx['blind']['text']}"
    entry = table.STUDIES.get(key, {})
    if "plan" not in entry:
        return table.why_not(key) or "estudio desconocido"
    scope = ("one" if spec.get("only_strategy") or not entry["many"] or (picked and entry["one"])
             else "many")
    if spec["feeds"] == "batch":
        return table.jobs({"study": key, "scope": "one", "project": ctx["project"],
                           "databank": "", "asset": ctx["asset"], "overrides": [],
                           "only": None, "strategies": picked or mothers(ctx["project"])})
    candidates = [databank] if databank else databanks(spec, key, ctx)
    if not candidates:
        return ("elige en el panel el databank que lee" if not spec["feeds"] else
                "ningún databank de este proyecto en el disco tiene su entrada")
    first = None
    for bank in candidates:
        chosen = picked or (population(ctx["project"], bank, ctx["asset"])
                            if scope == "one" else [])
        got = table.jobs({"study": key, "scope": scope, "project": ctx["project"],
                          "databank": bank, "asset": ctx["asset"], "overrides": [],
                          "only": None, "strategies": chosen})
        if not isinstance(got, str):
            return got
        first = first or f"{bank}: {got}"
    return first


def refusal(n: str, key: str, ctx: dict) -> str | None:
    """Why the rail may not start this test, before any input is looked for.

    Args:
        n: The step's number, as the window sent it.
        key: Study key, as the window sent it.
        ctx: What `api.context` gathered.

    Returns:
        The sentence, or None. An unknown step, an SQX step (its task is SQX's, its analysis
        is read from the panel), a study that is not a test of that step, and a test
        `tests.one` does not mark runnable — one while SQX runs on the project — are refused.
    """
    spec = BY_N.get(n)
    if spec is None:
        return f"el paso {n} no existe en WORKFLOW.md"
    if spec["kind"] == "sqx":
        return tests.SQX_STEP
    if key not in tests.keys(spec):
        return f"{key} no es una prueba del paso {n}"
    got = tests.one(spec, key, ctx, tests.running(ctx["project"]))
    return None if got["runnable"] else got["why"]


def start(ctx: dict, ticked: list[dict], databank: str, picked: list[str]) -> dict:
    """Queue every ticked test.

    Args:
        ctx: What `api.context` gathered.
        ticked: `[{n, key}]`, a step number and a study key each.
        databank: The panel's databank, '' from the rail.
        picked: The panel's chosen strategies, [] for the population.

    Returns:
        `jobs` (the records `jobs.start` returned) and `refused` (`[{n, key, why}]`). An SQX
        step's own task is never among the tests: the window starts nothing in SQX.
    """
    out, refused = [], []
    for t in ticked:
        why = refusal(t["n"], t["key"], ctx)
        if why:
            refused.append({"n": t["n"], "key": t["key"], "why": why})
            continue
        got = plan(BY_N[t["n"]], t["key"], ctx, databank, picked)
        if isinstance(got, str):
            refused.append({"n": t["n"], "key": t["key"], "why": got})
            continue
        out += [jobs.start(p["label"], p["argv"], p["about"] | {"step": t["n"]},
                           weight=p.get("weight")) for p in batch.fold(got)]
    return {"jobs": out, "refused": refused}


def backfill(ctx: dict, on_disk: list[str]) -> dict:
    """Whether to offer «rehacer las filas de 17-19», and the command it runs.

    Args:
        ctx: What `api.context` gathered, plus `family`.
        on_disk: The blind steps whose result is on disk, whatever the ledger says.

    Returns:
        `offer`, `why` and `argv`. Offered when a result on disk has no ledger row and the
        WFM result `ledger.blind.rebuild` needs is there; `ledger.backfill` itself refuses
        to write a step twice, so a second press cannot count a look twice.
    """
    missing = [n for n in on_disk if n not in ctx["blind"]["done"]]
    row = where.enrolled(ctx["project"])
    wfm = sources.results(ctx["project"], "wfm")
    why = ("17, 18 y 19: ningún resultado en disco sin su fila" if not missing else
           where.no_family(ctx["project"]) if not ctx["family"] else
           "falta el resultado del WFM (paso 19), que ledger.backfill --blind necesita"
           if not wfm else f"resultados sin fila en el ledger: pasos {', '.join(missing)}")
    if not (missing and ctx["family"] and wfm):
        return {"offer": False, "why": why, "argv": []}
    return {"offer": True, "why": why, "argv": [
        "-m", "ledger.backfill", "--blind", ctx["project"], "--wfm-databank",
        wfm[0]["databank"], "--symbol", row["symbol"], "--timeframe", row["timeframe"],
        "--family", ctx["family"], "--write"]}


def blind_on_disk(rows: list[dict]) -> list[str]:
    """The blind steps whose own reader found a result, before the seal hid it."""
    return [r["n"] for r in rows if r["n"] in BLIND and r["state"] == "done"]
