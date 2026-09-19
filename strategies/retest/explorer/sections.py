"""The panel's content, rendered by the report's own functions and never by its own."""

from strategies.retest.inputs import tasks
from strategies.retest.render import charts, panel, text

# What the panel shows, in reading order. A tab is a name and a renderer, and adding one is
# a function plus a row.
TABS = [("verdict", "Veredicto"), ("cost", "Qué la rompe"), ("stress", "Estrés combinado"),
        ("tasks", "Las ocho tareas"), ("levels", "Tabla de confianza")]


def verdict(got: dict, cfg: dict) -> str:
    """The call, the subscores and every flag that fired.

    Args:
        got: What run.one() returned.
        cfg: The cfg this request ran with.

    Returns:
        HTML. Byte for byte the block the batch report writes, because both call
        render.panel.strategy() -- if the two ever disagreed one of them would be lying.
    """
    return panel.strategy(got["strategy"], got)


def cost(got: dict, cfg: dict) -> str:
    """Which perturbation cost most, in units of the control.

    Args:
        got: What run.one() returned.
        cfg: The cfg this request ran with.

    Returns:
        HTML: the bar chart plus the ranking as a table.
    """
    attrib = got["attribution"]
    rows = [[tasks.TITLES[r["task"]], f"{r['cost']:,.0f}", f"{r['cost_in_sigmas']:.1f}",
             f"{r['spread_vs_control']:.1f}"] for r in attrib["ranking"]]
    return (charts.cost(attrib["ranking"], attrib["control_sigma"], "Qué la rompe",
                        "Cada barra es una tarea contra lo que el control mueve por sí solo.")
            + panel.table(["tarea", "coste USD", "sigmas del control", "dispersión vs control"],
                          rows))


def stress(got: dict, cfg: dict) -> str:
    """The production task on its own: the outcome, the envelope and the tail.

    Args:
        got: What run.one() returned.
        cfg: The cfg this request ran with.

    Returns:
        HTML.
    """
    entry, tail = got["stress"], got["stress"]["fragility"]
    return (charts.distribution(entry["_net"], entry["original_net"],
                                "Estrés combinado: mil re-ejecuciones",
                                "Las seis perturbaciones a la vez, sobre muestra completa.",
                                "beneficio neto, USD")
            + charts.fan(entry["fan"], "El abanico de equity",
                         "Eje X: avance de 0 a 1, no número de operación.")
            + panel.table(["medida", "valor", "intervalo exacto 95%"],
                          [["Beneficio p5", f"{tail['net_p5']['point']:,.0f}",
                            f"{tail['net_p5']['lo']:,.0f} a {tail['net_p5']['hi']:,.0f}"],
                           ["Profit factor p5", f"{tail['pf_p5']['point']:.3f}",
                            f"{tail['pf_p5']['lo']:.3f} a {tail['pf_p5']['hi']:.3f}"],
                           ["Drawdown CVaR", f"{tail['drawdown']['cvar']:.2f}%",
                            f"percentil {tail['drawdown']['quantile']:.2f}%"],
                           ["Operaciones bajo el agua", f"{tail['underwater_median']:.0%}", "—"],
                           ["P(beneficio > 0)", f"{tail['positive_share']:.1%}", "—"]]))


def task_detail(got: dict, cfg: dict) -> str:
    """Every task's outcome, one figure each.

    Args:
        got: What run.one() returned.
        cfg: The cfg this request ran with.

    Returns:
        HTML: the summary table, then a distribution per task that produced one.
    """
    figures = []
    for task in tasks.TASKS:
        entry = got.get(task)
        if not entry or not entry["modes"]["perturbed"]:
            continue
        figures.append(charts.distribution(
            entry["_net"], entry["original_net"], tasks.TITLES[task],
            f"{text.PERTURBA[task]}. Deja fija: {tasks.HOLDS_FIXED[task]}.",
            "beneficio neto, USD"))
    return panel.task_table(got) + "".join(figures)


def levels(got: dict, cfg: dict) -> str:
    """The confidence table, with the trap named above it.

    Args:
        got: What run.one() returned.
        cfg: The cfg this request ran with.

    Returns:
        HTML: the production task's reconstructed quantiles for the headline metrics.
    """
    entry = got["stress"]
    rows = [[tasks.TITLES[t], f"{got[t]['fragility']['net_p5']['point']:,.0f}",
             f"{got[t]['fragility']['drawdown']['cvar']:.1f}%"]
            for t in tasks.TASKS if t in got]
    return ('<div class="card"><b>Un nivel de confianza no es un escenario.</b> El percentil 5 '
            'de beneficio y el percentil 5 de drawdown salen de simulaciones <i>distintas</i>: '
            'cada métrica se ordena por su cuenta. Leídos como pareja describen una '
            're-ejecución que no existió.</div>'
            + panel.table(["tarea", "beneficio p5", "drawdown CVaR"], rows))


RENDER = {"verdict": verdict, "cost": cost, "stress": stress,
          "tasks": task_detail, "levels": levels}


def section(name: str, got: dict, cfg: dict) -> str:
    """One tab's HTML.

    Args:
        name: One of TABS' keys.
        got: What run.one() returned.
        cfg: The cfg this request ran with.

    Returns:
        HTML.
    """
    return RENDER[name](got, cfg)
