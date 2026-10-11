"""The autopilot's plan from step 17 on: the blind block, step 20 judged, the closing steps, the finalists."""

import argparse

FIRST = "17"
DONE = ("done", "sealed")       # sealed: 17-19 done, hidden by the ledger's door
# Computed per mother over her variant batch, one after another, and read only at step 20.
BLOCK = {"17": "wfc", "18": "cscv", "18.5": "marketSurfaces"}
# Split (owner, 2026-10-07): its deciding reading (build+oos1) is run and judged after 16.5,
# before any look at oos2; inside the block it is read again with oos2, which can only add Limbo.
SPLIT = "18.5"
# Their tests read «the databank the panel shows» (`workflow.steps`, feeds ()): the rail
# knows none, and the 2026-09-30 hand run used two (exposure on CrossTF_Mothers, the map on
# Results). Not chosen here (hard rule 11): `--panel 21=<databank>`, or a clean stop.
PANEL = {"21": "exposure", "22": "conditionalMap"}
BATCH = {"23": "structural", "24": "stop"}      # a batch retested on the three WFC legs
# Step 26's parameters and the flag each comes from: nothing is defaulted (owner).
MT5 = {"start": "--mt5-from", "end": "--mt5-to", "model": "--mt5-model", "firms": "--mt5-firms"}
NOTHING = {"panel": {}, "mt5": {}, "judged": set()}
NO_FAMILY = ("el proyecto no tiene plantilla en projects/registry.csv: sin familia las miradas "
             "de 17-20 no se apuntan en el ledger, así que no se corren")


def flags(ap: argparse.ArgumentParser) -> None:
    """The tail's inputs on `pipeline.autopilot.run`'s command line, none with a default."""
    ap.add_argument("--panel", action="append", default=[], metavar="PASO=DATABANK",
                    help="el databank que lee un paso de panel: 21 (exposición, su export con "
                         "OOS1) y 22 (mapa condicional, su cosecha); se repite")
    ap.add_argument("--until", choices=["wfm"],
                    help="el run acaba tras el paso 19 (la WFM, su lectura y las filas del ledger)")
    ap.add_argument("--mt5-from", help="paso 26: primer día del backtest, YYYY-MM-DD")
    ap.add_argument("--mt5-to", help="paso 26: último día, YYYY-MM-DD")
    ap.add_argument("--mt5-model", help="paso 26: el modelo del tester de MT5")
    ap.add_argument("--mt5-firms", help="paso 26: las empresas, separadas por comas")
    ap.add_argument("--mt5-real-ticks", action="store_true",
                    help="paso 26: además, una segunda pasada del tester en Real ticks")


def inputs(a: argparse.Namespace, cfg: dict) -> dict:
    """What `walk` needs beside the rail: the panel databanks, step 26's parameters as its
    agent takes them, and the steps `criteria.yaml` gives rules to."""
    return {"panel": dict(p.split("=", 1) for p in a.panel), "until": a.until,
            "mt5": {"start": a.mt5_from, "end": a.mt5_to, "model": a.mt5_model,
                    "firms": a.mt5_firms.split(",") if a.mt5_firms else [],
                    "ticks": a.mt5_real_ticks},
            "judged": {n for n, spec in cfg["steps"].items() if spec.get("rules")}}


def walk(steps: list[dict], do: list[dict], stale: bool, pending: str | None,
         family: str | None, given: dict) -> dict:
    """The rail from step 17 to 26, every survivor through every step (owner, 2026-09-29).

    Args:
        steps: The steps of GET /api/workflow.
        do: The plan so far; the tail's actions are appended to it.
        stale: An SQX step is planned before 17: what follows runs again entirely.
        pending: A judging step not yet judged (16), judged before the tail's first action.
        family: The template family the ledger rows are signed under, or None.
        given: `inputs()`.

    Returns:
        `do` and `stop` {n, why}, as `plan.plan`. In order: 18.5's deciding reading (`SPLIT`,
        `oos2: False`) and its judge; the blind looks 17, 18, 18.5 (a look skips a mother
        that has its result unless `redo`), then 17, 18 and 18.5 judged as the looks close; the
        WFM in SQX, its reading, what the funding module keeps of each that passed it (`kept`)
        and 19 judged — a judge only for a step `criteria.yaml` gives rules; the ledger rows
        of 17-19 and the door, step 20 and its judge, 21-22 on the
        databanks given, 23 and 24 in SQX, 25, the finalists, 26 — or, with `until: wfm`, a clean stop before 20. A step done is skipped;
        the block's looks are planned whenever any of 17-19 is not, because the rail calls a
        step done as soon as ONE mother has its result. 20, and any of 21-25 with rules, is
        judged right after it runs. It stops, cleanly, at a step in marcha, without a family, at 21 or 22 without their databank, and before 26
        without every one of its parameters.
    """
    by = {s["n"]: s for s in steps}

    def flush() -> None:
        """The judging step left pending, judged before what comes next."""
        nonlocal pending
        if pending:
            do.append({"n": pending, "title": "juicio", "kind": "judge", "tests": []})
        pending = None

    def judge(n: str, **more: object) -> None:
        """Step `n` judged here, when `criteria.yaml` gives it rules."""
        if n in given["judged"]:
            add(n, "judge", title="juicio", **more)

    def halt(n: str | None, why: str) -> dict:
        """The plan, ending before step `n`."""
        flush()
        return {"do": do, "stop": {"n": n, "why": why}}

    def due(n: str) -> bool:
        """Whether step `n` still has to run."""
        return stale or by[n]["state"] not in DONE

    def add(n: str, kind: str, **more: object) -> None:
        """One action of step `n`."""
        flush()
        do.append({"n": n, "title": by[n]["title"], "kind": kind, "tests": []} | more)

    def visit(n: str, kind: str, **more: object) -> None:
        """Step `n` planned when due, and judged where `criteria.yaml` (or step 20) says:
        right after it runs, or — done already — before the next step still to run."""
        nonlocal pending
        judged = n == "20" or n in given["judged"]
        if due(n):
            add(n, kind, **more)
            pending = n if judged else None
            flush()
        else:
            pending = n if judged else None

    running = next((n for n in (*BLOCK, "19", "20", *PANEL, *BATCH, "25")
                    if by[n]["state"] == "running"), None)
    block = any(due(n) for n in (*BLOCK, "19"))
    if (block or due("20")) and not family:
        return halt(FIRST if block else "20", NO_FAMILY)
    if block:
        if running == SPLIT:
            return halt(SPLIT, "está en marcha")
        add(SPLIT, "blind", tests=[BLOCK[SPLIT]], redo=stale, oos2=False)
        judge(SPLIT)
        for n, key in BLOCK.items():
            if n == running:
                return halt(n, "está en marcha")
            add(n, "blind", tests=[key], redo=stale, oos2=True)
        for n in BLOCK:         # each state is judged as the block's looks close, before the WFM
            judge(n, **({"segment": "build+oos1+oos2"} if n == SPLIT else {}))   # 18.5 read oos2 this time
        if running == "19":
            return halt("19", "está en marcha")
        ran = due("19")
        if ran:
            add("19", "sqx")
        if ran or not any(t["key"] == "wfm" and t["state"] == "done"
                          for t in by["19"].get("tests", [])):
            add("19", "wfm", title="lectura de la WFM")
            add("19", "kept", title="guardar para fondeo")
        judge("19")
        stale = True        # a piece of the block is new: 20 and what follows read it again
    if running == "20":
        return halt("20", "está en marcha")
    if due("20"):
        add("19", "ledger", title="filas de 17-19 en el ledger")
    if given.get("until") == "wfm":
        return halt("20", "--until wfm: el run acaba tras la WFM")
    visit("20", "joint", tests=["blindJoint"])
    for n, key in PANEL.items():
        if n == running:
            return halt(n, "está en marcha")
        if due(n) and not given["panel"].get(n):
            return halt(n, f"falta --panel {n}=<databank>: el databank que lee {key} no lo "
                           "sabe el raíl y no se elige por ti")
        visit(n, "reading", tests=[key], databank=given["panel"].get(n))
    for n, kind in BATCH.items():
        if n == running:
            return halt(n, "está en marcha")
        ran = due(n)
        visit(n, kind)
        stale = stale or ran
    if running == "25":
        return halt("25", "está en marcha")
    visit("25", "edge", tests=["edgeCost"])
    add("25", "finalists", title="finalistas para el paso 26")
    missing = [flag for key, flag in MT5.items() if not given["mt5"].get(key)]
    if not missing:
        add("26", "mt5verify", params=given["mt5"])
    elif due("26"):
        return halt("26", "el paso 26 no da nada por defecto: faltan " + ", ".join(missing))
    return halt(None, "no queda ningún paso")
