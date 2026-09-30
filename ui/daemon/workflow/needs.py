"""Which earlier steps each step needs first: the producer of its input, the judge of that input, the row before."""

from sqx.projects.stage import titles
from ui.daemon.workflow.derive import BLIND
from ui.daemon.workflow.steps import STEPS

ORDER = [s["n"] for s in STEPS]
BY_N = {s["n"]: s for s in STEPS}
BY_STAGE = {s["stage"]: s["n"] for s in STEPS if "stage" in s}
BANK = {s["bank"]: s["n"] for s in STEPS if "bank" in s}      # 10.5 fills CrossTF_Input
VARIANTS = next(s["n"] for s in STEPS if s["how"] == "variants")


def producer(databank: str, tasks: list[dict]) -> str | None:
    """The step that fills a databank: the one whose task writes it, or whose prepared bank it is.

    Args:
        databank: As the project's tasks spell it.
        tasks: The project's tasks, as `sources.sqx_view` reads them.
    """
    if databank in BANK:
        return BANK[databank]
    task = next((t for t in tasks if t["output"] == databank), None)
    return next((n for stage, n in BY_STAGE.items() if task and task["title"] in titles(stage)),
                None)


def judge(made_by: str, before: str) -> str | None:
    """The Python step between the producer and this one whose tests read the producer's output:
    the verdict the next task should run on (WORKFLOW.md, «el contrato que une los pasos pares»)."""
    stage = BY_N[made_by].get("stage")
    between = ORDER[ORDER.index(made_by) + 1:ORDER.index(before)]
    return next((n for n in between if BY_N[n]["kind"] == "python"
                 and isinstance(BY_N[n]["feeds"], tuple) and stage in BY_N[n]["feeds"]), None)


def of(spec: dict, ctx: dict) -> list[str]:
    """The steps one step needs done before it, earliest first.

    Args:
        spec: The step's row of `steps.STEPS`.
        ctx: What `api.context` gathered; `sqx` holds the project's tasks, or None.

    Returns:
        Step numbers: for an SQX task step, the steps that fill its tasks' inputs and the
        Python step that judges each; for a Python step, the SQX step whose output it reads
        (its first `feeds` stage), the variant batch (17-18.5) or the sealed three (20); for
        21-25, the last step that does not read the panel's databank; always the row before it
        in WORKFLOW.md's table, the order the chain walks.
    """
    n, feeds = spec["n"], spec["feeds"]
    at = ORDER.index(n)
    out = []
    if spec["how"] == "sqx" and ctx["sqx"]:
        tasks = ctx["sqx"]["tasks"]
        mine = [t for t in tasks if t["title"] in titles(spec["stage"])]
        made = {producer(t["input"], tasks) for t in mine if t["input"]} - {None, n}
        for m in sorted((m for m in made if ORDER.index(m) < at), key=ORDER.index):
            out += [m, judge(m, n)]
    elif spec["how"] == "blind":
        out += list(BLIND) + [BY_STAGE[f] for f in feeds]
    elif isinstance(feeds, tuple) and feeds and spec["kind"] == "python":
        out.append(BY_STAGE[feeds[0]])
    elif feeds == "batch" and n != VARIANTS:
        out.append(VARIANTS)
    elif feeds == () and spec["kind"] == "python" and at > ORDER.index(BLIND[-1]):
        out.append(next(m for m in reversed(ORDER[:at])
                        if BY_N[m]["feeds"] != () or BY_N[m]["kind"] != "python"))
    if at:
        out.append(ORDER[at - 1])
    return sorted({m for m in out if m and m != n}, key=ORDER.index)
