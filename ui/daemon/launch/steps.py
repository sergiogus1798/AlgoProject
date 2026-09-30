"""Which SQX tasks one workflow step launches from the window, and the SQX steps it cannot launch."""

import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from sqx.projects import stage
from ui.daemon.workflow.steps import STEPS

BY_N = {s["n"]: s for s in STEPS}
# SQX steps whose work is not a task start: each needs a preparation only the chat does.
ELSEWHERE = {
    "5": "el proyecto se crea con sqx.projects.builder (en el chat): no es una tarea de SQX",
    "10.5": "se hace sola al lanzar el paso 11: con el worker parado, las supervivientes de "
            "Cross Market se escalan y se cargan con sus hermanas en CrossTF_Input "
            "(sqx.projects.crosstfload), y enseguida corre «CrossTF»",
    "16.5": "el lote de variantes se fabrica y se carga con /variants en el chat "
            "(sqx.variants.make → execute): lanzar solo las tareas WFC retestearía lo que "
            "WFC_Variants tenga ahora",
}
# An MC Retest task its configurator skipped carries its Monte Carlo off (`perturbations.disable`).
SILENCED = re.compile(r'<MonteCarloRetest use="false"')


# The steps whose task only does its job once a configurator has written its cross-check:
# stage → (the cross-check element, the configurator module). Launched as it came from the
# donor, the task is a plain retest (🔬 2026-09-29: «WFM» done in 6 s, no matrix, 21
# strategies passed through). The window runs the configurator first, and only on a task
# whose cross-check is off (owner, 2026-09-29): a configured task is never rewritten.
CONFIGURE = {"crossmarket": ("RetestOnAdditionalMarkets", "sqx.projects.crossmarket"),
             "mcretest": ("MonteCarloRetest", "sqx.projects.mcretest"),
             "spp": ("OptProfileSysParamPermutation", "sqx.projects.spp"),
             "wfm": ("WalkForwardMatrix", "sqx.projects.wfm")}


def unconfigured(cfx: Path, titles: list[str]) -> dict[str, list[str]]:
    """The configurators these tasks need before they can run.

    Args:
        cfx: The project's project.cfx.
        titles: The task titles about to be launched.

    Returns:
        Configurator module → the titles of its stage whose cross-check is off.
    """
    with zipfile.ZipFile(cfx) as z:
        members = {name: z.read(name) for name in z.namelist()}
    out: dict[str, list[str]] = {}
    tags = list(ElementTree.fromstring(members["config.xml"]).find("Tasks"))
    for key, (element, module) in CONFIGURE.items():
        mine = [tag for tag in tags if tag.get("title") in stage.titles(key)]
        on = {tag.get("title") for tag in mine if re.search(
            rf'<{element}\b[^>]*\buse="true"',
            members.get(tag.get("taskXMLFile") or "", b"").decode("utf-8"))}
        # The MC Retest's configurator leaves some of its eight off on purpose (`silenced`):
        # the stage is configured once any of them carries its Monte Carlo.
        if key == "mcretest" and on:
            continue
        out.update({module: [t.get("title") for t in mine
                             if t.get("title") in titles and t.get("title") not in on]})
    return {m: ts for m, ts in out.items() if ts}


def silenced(members: dict[str, bytes], config: str) -> dict[str, str]:
    """The MC Retest tasks `sqx.projects.mcretest` left without their Monte Carlo.

    Args:
        members: The project.cfx's files.
        config: Its config.xml as text.

    Returns:
        Title → why it stays off.
    """
    out = {}
    for tag in ElementTree.fromstring(config).find("Tasks"):
        body = members.get(tag.get("taskXMLFile") or "", b"").decode("utf-8")
        if SILENCED.search(body):
            out[tag.get("title")] = ("su configurador la dejó sin Monte Carlo (no aplica a esta "
                                     "población): se queda apagada")
    return out


def of_step(n: str, cfx: Path) -> dict:
    """The titles an SQX step switches on in one project.

    Args:
        n: The step's number, as WORKFLOW.md writes it.
        cfx: The project's project.cfx.

    Returns:
        `titles` (to switch on, in the step's order) and `off` (title → why a task of the
        step stays off); or `refuse` with the one reason, plus `elsewhere: True` when the
        reason is that the step is not an SQX task at all (`ELSEWHERE`) — an expected state,
        never a failure, so the rail must not paint it red. Every title of the step must be
        in the project, as `stage.apply` demands.
    """
    spec = BY_N.get(n)
    if spec is None or spec["kind"] != "sqx":
        return {"refuse": f"el paso {n} no es un paso de SQX"}
    if n in ELSEWHERE:
        return {"refuse": ELSEWHERE[n], "elsewhere": True}
    if "stage" not in spec:
        # A new SQX step with no stage in `workflow.steps.STAGE` (25.5, 2026-09-29) raised
        # KeyError here and /api/launch/steps answered 500: every ▶ SQX of the rail went grey.
        return {"refuse": f"el paso {n} no tiene tareas de SQX que la ventana sepa lanzar"}
    wanted = stage.titles(spec["stage"])
    with zipfile.ZipFile(cfx) as z:
        members = {name: z.read(name) for name in z.namelist()}
    config = members["config.xml"].decode("utf-8")
    missing = [t for t in wanted if f'title="{t}"' not in config]
    if missing:
        return {"refuse": f"el proyecto no lleva {', '.join(missing)}: un proyecto de workflow "
                          "se crea con `sqx.projects.builder --workflow`"}
    # Only an MC Retest task carries the flag as a verdict: every other retest has it off; and
    # before its configurator ran, all eight have it off — to configure, not silenced.
    off = ({t: why for t, why in silenced(members, config).items() if t in wanted}
           if spec["stage"] == "mcretest" and not unconfigured(cfx, wanted) else {})
    on = [t for t in wanted if t not in off]
    if not on:
        return {"refuse": f"todas las tareas del paso {n} están apagadas por su configurador"}
    return {"titles": on, "off": off}
