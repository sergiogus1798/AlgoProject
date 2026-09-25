"""One strategy's retest as the contract's tabs: the call, what breaks it, the stress, the eight."""

import pandas as pd

from core.study import blocks, result as envelope
from studies.breakage.mcRetest.contract import words
from studies.breakage.mcRetest.inputs import tasks


def verdict_block(got: dict) -> dict:
    """The call, its composite, what limits it, one part per task group."""
    v = got["verdict"]
    return blocks.verdict(
        v["verdict"], words.STATE[v["verdict"]],
        f"{words.VERDICTS[v['verdict']]} Limita: {v['binding']}.", v["composite"],
        [{"label": k, "state": "fail" if k == v["binding"] and v["verdict"] == "FAIL"
          else "info", "value": x, "note": ""} for k, x in v["subscores"].items()])


def verdict_tab(got: dict) -> dict:
    """Every check that fired, with what it measured, and the sub-scores."""
    rows = [["VETO" if f["gate"] else "aviso", f["test"], f["value"], f["limit"],
             words.SENTENCES[f["veto"]]] for f in got["flags"]]
    return envelope.tab("verdict", "Veredicto", [
        blocks.table("Qué saltó", pd.DataFrame(rows, columns=["tipo", "prueba", "midió",
                                                            "contra", "qué dice"]),
                     "" if rows else "No saltó nada."),
        {"kind": "bars", "title": "Subnotas por grupo de tareas", "unit": "sobre 100",
         "reference": None, "items": [{"label": k, "value": x, "error": None, "state": "info"}
                                      for k, x in got["verdict"]["subscores"].items()]}])


def cost_tab(got: dict, cfg: dict) -> dict:
    """Which perturbation cost most, in units of what the control moves on its own."""
    a = got["attribution"]
    floor = cfg["attribution"]["min_control_sigma"]
    return envelope.tab("cost", "Qué la rompe", [
        {"kind": "bars", "title": "Coste de cada tarea, en sigmas del control",
         "unit": "sigmas", "reference": floor,
         "note": f"El control mueve el resultado {a['control_sigma']:,.0f} USD por sí solo. "
                 f"Menos de {floor:g} sigma es ruido, no un hallazgo.",
         "items": [{"label": tasks.TITLES[r["task"]], "value": r["cost_in_sigmas"],
                    "error": None, "state": "fail" if r["cost_in_sigmas"] >= floor else "none"}
                   for r in a["ranking"]]},
        blocks.table("La clasificación", pd.DataFrame(
            [[tasks.TITLES[r["task"]], r["cost"], r["cost_in_sigmas"], r["spread_vs_control"]]
             for r in a["ranking"]],
            columns=["tarea", "coste (USD)", "sigmas del control", "dispersión vs control"]))])


def stress_tab(got: dict) -> dict:
    """The production task alone: its outcome, its equity fan and its tail."""
    entry, tail = got["stress"], got["stress"]["fragility"]
    fan = entry["fan"]
    return envelope.tab("stress", "Estrés combinado", [
        blocks.distribution("Estrés combinado: mil re-ejecuciones", "USD", entry["_net"],
                            entry["original_net"], "Las seis perturbaciones a la vez, sobre "
                            "muestra completa. La línea es el backtest que ocurrió."),
        {"kind": "cone", "title": "El abanico de equity bajo estrés", "unit": "USD",
         "x": [round(float(p) * 100, 1) for p in fan["progress"]],
         "bands": {str(k): list(v) for k, v in fan["bands"].items()},
         "real": [None] * len(fan["progress"]), "split": None,
         "note": "El eje X es avance de 0 a 100 y no número de operación: cada re-ejecución "
                 "tiene su propia cuenta de operaciones."},
        blocks.table("La cola", pd.DataFrame(
            [["Beneficio p5", tail["net_p5"]["point"], tail["net_p5"]["lo"],
              tail["net_p5"]["hi"]],
             ["Profit factor p5", tail["pf_p5"]["point"], tail["pf_p5"]["lo"],
              tail["pf_p5"]["hi"]],
             ["Drawdown CVaR (%)", tail["drawdown"]["cvar"], None, None],
             ["Operaciones bajo el agua", tail["underwater_median"], None, None],
             ["P(beneficio > 0)", tail["positive_share"], None, None]],
            columns=["medida", "valor", "intervalo 95 % desde", "hasta"]))])


def tasks_tab(got: dict) -> dict:
    """What each of the eight tasks did, then each perturbed outcome drawn."""
    present = [t for t in tasks.TASKS if t in got]
    rows = [[tasks.TITLES[t], words.PERTURBA[t], got[t]["fragility"]["net_p5"]["point"],
             got[t]["fragility"]["drawdown"]["cvar"],
             got[t]["modes"]["trades"]["median_share"], words.shape(got[t])] for t in present]
    figs = [blocks.distribution(tasks.TITLES[t], "USD", got[t]["_net"], got[t]["original_net"],
                                f"Perturba {words.PERTURBA[t]}. Deja fijo: "
                                f"{words.FIJA[t]}.")
            for t in present if got[t]["modes"]["perturbed"]]
    missing = [tasks.TITLES[t] for t in tasks.TASKS if t not in got]
    return envelope.tab("tasks", "Las ocho tareas", [
        blocks.table("Qué hizo cada tarea", pd.DataFrame(
            rows, columns=["tarea", "qué perturba", "beneficio p5 (USD)", "drawdown CVaR (%)",
                           "operaciones vs original", "forma"]),
            f"No corrieron: {', '.join(missing)}." if missing else ""), *figs])


def levels_tab(got: dict, levels: pd.DataFrame, cfg: dict) -> dict:
    """SQX's own confidence table at the levels the config names, with its trap named."""
    mine = levels[levels["strategy"] == got["strategy"]]
    show = cfg["scenario"]["show_levels"]
    keep = mine[mine["level"].isin(show) & mine["metric"].isin(
        ["NetProfit", "ProfitFactor", "DrawdownPct", "NumberOfTrades"])]
    wide = (keep.pivot_table(index=["task", "metric"], columns="level", values="value",
                             observed=True)
            .reset_index())
    wide["task"] = wide["task"].map(tasks.TITLES)
    wide.columns = [str(c) for c in wide.columns]
    return envelope.tab("levels", "Tabla de confianza", [
        blocks.table("Beneficio p5 y drawdown CVaR, tarea a tarea", pd.DataFrame(
            [[tasks.TITLES[t], got[t]["fragility"]["net_p5"]["point"],
              got[t]["fragility"]["drawdown"]["cvar"]] for t in tasks.TASKS if t in got],
            columns=["tarea", "beneficio p5 (USD)", "drawdown CVaR (%)"])),
        blocks.table(f"La tabla que SQX guardó, niveles {', '.join(map(str, show))}", wide,
                     "Tablas con los rangos desplazados por una corrida cortada no aparecen.")],
        note="Un nivel de confianza no es un escenario: el percentil 5 del beneficio y el del "
             "drawdown salen de simulaciones distintas, porque cada métrica se ordena por su "
             "cuenta. Leídos como pareja describen una re-ejecución que no existió.")


def summary(got: dict) -> dict:
    """The flat row verdict.csv carries."""
    v, s = got["verdict"], got["stress"]["fragility"]
    return {"verdict": v["verdict"], "composite": v["composite"], "binding": v["binding"],
            "stress_net_p5": round(s["net_p5"]["point"], 2),
            "stress_cvar_dd_pct": round(s["drawdown"]["cvar"], 2),
            "vetoes": "; ".join(v["vetoes"]), "blocked_by": "; ".join(v["blocked_by"])}
