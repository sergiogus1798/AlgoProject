"""One strategy's retest as the contract's tabs: the call, what breaks it, the stress, the eight."""

from typing import Any, cast

import pandas as pd

from core.study import blocks
from core.study import result as envelope
from studies.breakage.mcRetest.contract import criteria, words
from studies.breakage.mcRetest.inputs import tasks

COMPOSITE_HELP = (
    "Media ponderada de cuatro subnotas sobre 100 — producción 55%, ejecución "
    "20%, especificación 20%, datos 5% — cada una la PEOR de sus tareas, nunca "
    "una media entre ellas. Un veto (ver «qué falló») pone FAIL sin mirar la "
    "nota; un veto solo de datos pone INCONCLUSIVE: no midió mal, no se pudo "
    "medir."
)


def verdict_block(got: dict) -> dict[str, Any]:
    """The call, its composite, what limits it, one part per task group."""
    v = got["verdict"]
    block = blocks.verdict(
        v["verdict"],
        words.STATE[v["verdict"]],
        f"{words.VERDICTS[v['verdict']]} Limita: {words.GROUPS[v['binding']]}.",
        v["composite"],
        [
            {
                "label": words.GROUPS[k],
                "state": "fail"
                if k == v["binding"] and v["verdict"] == "FAIL"
                else "info",
                "value": x,
                "note": "",
            }
            for k, x in v["subscores"].items()
        ],
    )
    block["help"] = COMPOSITE_HELP
    return block


def verdict_tab(got: dict) -> dict[str, Any]:
    """Every check that fired, with what it measured, and the sub-scores."""
    rows = [
        [
            "Veto" if f["gate"] else "Aviso",
            words.test_name(f["test"]),
            f["value"],
            f["limit"],
            words.SENTENCES[f["veto"]],
        ]
        for f in got["flags"]
    ]
    table = blocks.table(
        "Qué comprobaciones saltaron",
        pd.DataFrame(
            rows, columns=pd.Index(["Tipo", "Prueba", "Midió", "Contra", "Qué dice"])
        ),
        "Qué comprobación descalificó la estrategia (Veto) o solo la marcó "
        "(Aviso), y contra qué límite. Un veto manda el veredicto a FAIL — o "
        "a INCONCLUSIVE cuando es sólo de datos, nunca de resultado."
        + ("" if rows else " No saltó nada."),
    )
    return envelope.tab(
        "verdict",
        "Veredicto",
        [
            table,
            {
                "kind": "bars",
                "title": "Subnotas por grupo de tareas",
                "unit": "sobre 100",
                "reference": None,
                "items": [
                    {
                        "label": words.GROUPS[k],
                        "value": x,
                        "error": None,
                        "state": "info",
                    }
                    for k, x in got["verdict"]["subscores"].items()
                ],
            },
        ],
    )


def cost_tab(got: dict, cfg: dict) -> dict | None:
    """Which perturbation cost most, in units of what the control moves on its own."""
    a = got["attribution"]
    if a is None:
        return None
    floor = cfg["attribution"]["min_control_sigma"]
    return envelope.tab(
        "cost",
        "Qué la rompe",
        [
            {
                "kind": "bars",
                "title": "Coste de cada tarea, en sigmas del control",
                "unit": "σ",
                "reference": floor,
                "help": f"El control (tarea `bar`, sólo mueve la vela de inicio) da la sigma del "
                f"ruido irreducible: {a['control_sigma']:,.0f} USD aquí. El desplazamiento de "
                f"cada perturbación se mide en esos sigmas. Por debajo de {floor:g} sigma es "
                f"ruido — no un hallazgo; a partir de {floor:g} sigma (la línea de "
                f"referencia) se colorea como hallazgo. Este umbral sólo pinta esta barra: no "
                f"veta nada por sí solo — los vetos de verdad (pestaña «Veredicto») usan sus "
                f"propios límites en fracción de beneficio, no en sigmas. Verde: dentro del ruido "
                f"o incluso mejor que el control (valor negativo = la perturbación no "
                f"cuesta, mejora); rojo: cuesta de {floor:g} σ en adelante. σ = sigma.",
                "note": f"El control mueve el resultado {a['control_sigma']:,.0f} USD por sí solo. "
                f"Menos de {floor:g} sigma es ruido, no un hallazgo.",
                "items": [
                    {
                        "label": tasks.TITLES[r["task"]],
                        "value": round(r["cost_in_sigmas"], 1),
                        "error": None,
                        "state": "fail" if r["cost_in_sigmas"] >= floor else "pass",
                    }
                    for r in a["ranking"]
                ],
            },
            blocks.table(
                "Clasificación de tareas por coste",
                pd.DataFrame(
                    [
                        [
                            tasks.TITLES[r["task"]],
                            r["cost"],
                            r["cost_in_sigmas"],
                            r["spread_vs_control"],
                        ]
                        for r in a["ranking"]
                    ],
                    columns=pd.Index(
                        [
                            "Tarea",
                            "Coste (USD)",
                            "Sigmas del control",
                            "Dispersión frente al control",
                        ]
                    ),
                ),
            ),
        ],
    )


def stress_tab(got: dict) -> dict | None:
    """The production task alone: its outcome, its equity fan and its tail; None if it did not run."""
    if "stress" not in got:
        return None
    entry, tail = got["stress"], got["stress"]["fragility"]
    fan = entry["fan"]
    return envelope.tab(
        "stress",
        "Estrés combinado",
        [
            blocks.distribution(
                f"Estrés combinado: {len(entry['_net'])} re-ejecuciones",
                "USD",
                entry["_net"],
                entry["original_net"],
                "Las seis perturbaciones a la vez, sobre "
                "muestra completa. La línea es el backtest que ocurrió.",
            ),
            _fan_cone("Abanico de equity bajo estrés", fan),
            blocks.table(
                "La cola de la distribución",
                pd.DataFrame(
                    [
                        [
                            "Net Profit p5",
                            tail["net_p5"]["point"],
                            tail["net_p5"]["lo"],
                            tail["net_p5"]["hi"],
                        ],
                        [
                            "Profit Factor p5",
                            tail["pf_p5"]["point"],
                            tail["pf_p5"]["lo"],
                            tail["pf_p5"]["hi"],
                        ],
                        ["Drawdown CVaR (%)", tail["drawdown"]["cvar"], None, None],
                        [
                            "Operaciones bajo el agua (mediana)",
                            tail["underwater_median"],
                            None,
                            None,
                        ],
                        [
                            "Simulaciones rentables (%)",
                            round(tail["positive_share"] * 100, 2),
                            None,
                            None,
                        ],
                    ],
                    columns=pd.Index(
                        ["Medida", "Valor", "Intervalo al 95 %: desde", "Hasta"]
                    ),
                ),
            ),
        ],
    )


def _fan_cone(title: str, fan: dict) -> dict[str, Any]:
    """A task's simulated equity as percentile bands 5-95 and 25-75, the median and the original."""
    block = {
        "kind": "cone",
        "title": title,
        "unit": "USD",
        "x": [round(float(p) * 100, 1) for p in fan["progress"]],
        "bands": {str(k): [float(x) for x in v] for k, v in fan["bands"].items()},
        "real": [None] * len(fan["progress"])
        if fan["original"] is None
        else [float(x) for x in fan["original"]],
        "split": None,
        "note": "Banda clara: del 5 al 95 % de las re-ejecuciones. Banda oscura: del 25 al "
        "75 %. Línea central: la mediana. El eje X es avance de 0 a 100 y no "
        "número de operación: cada re-ejecución tiene su propia cuenta de "
        "operaciones.",
    }
    if fan["original"] is not None:
        block["real_label"] = "backtest original"
    return block


def tasks_tab(got: dict) -> dict[str, Any]:
    """What each of the eight tasks did, then each perturbed outcome drawn."""
    present = [t for t in tasks.TASKS if t in got]
    rows = [
        [
            tasks.TITLES[t],
            got[t]["fragility"]["net_p5"]["point"],
            float(pd.Series(got[t]["_net"]).median()),
            got[t]["original_net"],
            got[t]["fragility"]["drawdown"]["cvar"],
        ]
        for t in present
    ]
    figs = [
        blocks.distribution(
            tasks.TITLES[t],
            "USD",
            got[t]["_net"],
            got[t]["original_net"],
            f"Perturba {words.PERTURBA[t]}. Deja fijo: {words.FIJA[t]}.",
        )
        for t in present
        if got[t]["modes"]["perturbed"]
    ]
    curves = [
        _fan_cone(f"{tasks.TITLES[t]}: abanico de equity", got[t]["fan"])
        for t in present
        if got[t]["modes"]["perturbed"]
    ]
    missing = [tasks.TITLES[t] for t in tasks.TASKS if t not in got]
    return envelope.tab(
        "tasks",
        "Las tareas",
        [
            blocks.table(
                "Qué hizo cada tarea",
                pd.DataFrame(
                    rows,
                    columns=pd.Index(
                        [
                            "Tarea",
                            "Net Profit p5 (USD)",
                            "Mediana Monte Carlo (USD)",
                            "Backtest original (USD)",
                            "Drawdown CVaR (%)",
                        ]
                    ),
                ),
                f"No corrieron: {', '.join(missing)}." if missing else "",
            ),
            criteria.table(got),
            *[b for pair in zip(figs, curves) for b in pair],
        ],
    )


def levels_tab(got: dict, levels: pd.DataFrame, cfg: dict) -> dict[str, Any]:
    """SQX's own confidence table at the levels the config names, with its trap named."""
    mine = cast(pd.DataFrame, levels[levels["strategy"] == got["strategy"]])
    show = cfg["scenario"]["show_levels"]
    keep = cast(
        pd.DataFrame,
        mine[
            mine["level"].isin(show)
            & mine["metric"].isin(
                ["NetProfit", "ProfitFactor", "DrawdownPct", "NumberOfTrades"]
            )
        ],
    )
    wide = keep.pivot_table(
        index=["task", "metric"], columns="level", values="value", observed=True
    ).reset_index()
    wide["task"] = wide["task"].map(tasks.TITLES)  # pyright: ignore[reportArgumentType]  # pandas stubs reject a dict mapper; pandas takes it (NaN for a missing key)
    wide = wide.rename(columns={"task": "Tarea", "metric": "Métrica"})
    wide.columns = [str(c) for c in wide.columns]
    return envelope.tab(
        "levels",
        "Tabla de confianza",
        [
            blocks.table(
                "Net Profit p5 y Drawdown CVaR, tarea a tarea",
                pd.DataFrame(
                    [
                        [
                            tasks.TITLES[t],
                            got[t]["fragility"]["net_p5"]["point"],
                            float(pd.Series(got[t]["_net"]).median()),
                            got[t]["original_net"],
                            got[t]["fragility"]["drawdown"]["cvar"],
                        ]
                        for t in tasks.TASKS
                        if t in got
                    ],
                    columns=pd.Index(
                        [
                            "Tarea",
                            "Net Profit p5 (USD)",
                            "Mediana Monte Carlo (USD)",
                            "Backtest original (USD)",
                            "Drawdown CVaR (%)",
                        ]
                    ),
                ),
            ),
            blocks.table(
                f"La tabla que SQX guardó, niveles {', '.join(map(str, show))}",
                wide,
                "Tablas con los rangos desplazados por un run cortado no aparecen.",
            ),
        ],
        note="Un nivel de confianza no es un escenario: el percentil 5 del beneficio y el del "
        "drawdown salen de simulaciones distintas, porque cada métrica se ordena por su "
        "cuenta. Leídos como pareja describen una re-ejecución que no existió.",
    )


SPARSE_MIN = (
    5  # feedback 2026-09-30 §6: fewer distinct outcomes than this reads as "all landed
)
# in the same place" (35-39k) even though the task did perturb something


def sparse_warnings(got: dict) -> list[dict]:
    """One warning per task whose perturbation barely moved the result at all.

    Args:
        got: What run.one() returned for one strategy.

    Returns:
        A `watch` warning per task that ran, changed something (`perturbed`), but produced
        fewer than `SPARSE_MIN` distinct NetProfit values across its simulations — the
        symptom of a `mc_retest.spread`/`mc_retest.slippage` range too narrow for SQX's own
        draw grain to place more than a handful of points in
        (`knowhow/costs/mc-retest-ranges.md`). `modes.outcomes` counts distinct RESULTS, not
        distinct inputs, but the two track each other closely enough here to warn on: a
        strategy that traded through a two-point spread band cannot produce five distinct
        net profits from it either.
    """
    out = []
    for t in tasks.TASKS:
        if t not in got or not got[t]["modes"]["perturbed"]:
            continue
        n = got[t]["modes"]["outcomes"]
        if n < SPARSE_MIN:
            where = (
                f" (revisa mc_retest.{t} del activo: puede que su rango no cubra ni "
                f"{SPARSE_MIN} pasos del paso con que SQX sortea)."
                if t in ("spread", "slippage")
                else "."
            )
            out.append(
                {
                    "code": f"sparse_{t}",
                    "state": "watch",
                    "text": f"{tasks.TITLES[t]}: sólo {n} valores distintos de beneficio en "
                    f"mil simulaciones — el rango que perturbó es casi un punto "
                    f"fijo, no una distribución" + where,
                }
            )
    return out


def summary(got: dict) -> dict[str, str | float | None]:
    """The flat row verdict.csv carries; the stress columns are empty when it did not run."""
    v, s = got["verdict"], got.get("stress", {}).get("fragility")
    return {
        "verdict": v["verdict"],
        "composite": v["composite"],
        "binding": v["binding"],
        "stress_net_p5": round(s["net_p5"]["point"], 2) if s else None,
        "stress_cvar_dd_pct": round(s["drawdown"]["cvar"], 2) if s else None,
        "vetoes": "; ".join(v["vetoes"]),
        "blocked_by": "; ".join(v["blocked_by"]),
        **criteria.summary(got),
    }
