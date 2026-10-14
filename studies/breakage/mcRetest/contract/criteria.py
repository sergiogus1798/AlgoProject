"""The retest's criteria metrics — the original among its own re-runs — as a table and as columns."""

from typing import Any

import pandas as pd

from core.study import blocks
from studies.breakage.mcRetest.inputs import tasks

TITLE = "Métricas para criterios — sin umbral todavía"
HELP = [
    None,
    "Porcentaje de re-ejecuciones de la tarea con un Net Profit menor que el del backtest "
    "original (los empates cuentan la mitad). 50 = el original está en el centro de lo que la "
    "tarea simuló; cerca de 100 = casi ninguna re-ejecución llegó a su resultado, el original "
    "es un caso extremo por arriba; cerca de 0, por abajo.",
    "(Mediana de las re-ejecuciones − original) / |original|, en %. −30 = la re-ejecución "
    "típica gana un 30 % menos que el backtest original. No se publica si el original está a "
    "menos de 0,25 IQR de cero: dividir por él no significa nada.",
    "La misma distancia, original − mediana, medida en rangos intercuartílicos (IQR) de las "
    "re-ejecuciones: no depende de lo grande que sea el beneficio. 1 IQR son unas 1,35 "
    "desviaciones típicas de una normal. Vacío si la tarea no movió nada.",
    "Entre qué valores cae, en IQR, el 90 % central de las propias re-ejecuciones: lo que "
    "leería un original que fuese una re-ejecución más. Un original fuera de este rango es un "
    "extremo de su distribución. No es el rango de una estrategia sin ventaja: ese no está "
    "medido todavía (haría falta un MC Retest de estrategias de entrada aleatoria).",
]
NOTE = (
    "Calculadas y visibles, sin juzgar: ninguna tiene umbral ni cambia el veredicto. "
    "Spread, slippage y estrés combinado sortean costes casi siempre peores que los del "
    "original, así que ahí el original queda por encima de la mediana por construcción "
    "(percentil 65–70 en spread y slippage aunque la estrategia sea robusta): compara cada "
    "tarea con ella misma entre estrategias, no con 50. Las re-ejecuciones comparten el "
    "mismo histórico: su número no es un tamaño de muestra y aquí no hay p-valores."
)


def table(got: dict) -> dict[str, Any]:
    """One row per task that ran; numbers stay numbers so each cell is a fact of the autopilot."""
    rows = []
    for task in tasks.TASKS:
        if task in got:
            p = got[task]["place"]
            own = (
                "—"
                if p["own"] is None
                else (f"{p['own'][0]:+.2f} a {p['own'][1]:+.2f}".replace(".", ","))
            )
            rows.append(
                [tasks.TITLES[task], p["percentile"], p["gap_pct"], p["gap_iqr"], own]
            )
    frame = pd.DataFrame(
        rows,
        columns=pd.Index(
            [
                "Tarea",
                "Percentil del original",
                "Brecha de la mediana (%)",
                "Distancia a la mediana (IQR)",
                "Una re-ejecución más (IQR)",
            ]
        ),
    )
    for col in frame.columns[1:4]:
        frame[col] = frame[col].astype(float)
    return blocks.table(
        f"{TITLE}: el original entre sus re-ejecuciones", frame, NOTE, 4
    ) | {"help": HELP, "compact": True}


def summary(got: dict) -> dict[str, float | None]:
    """The production task's three numbers: verdict.csv columns, hence the databank table's."""
    if "stress" not in got:
        return {}
    p = got["stress"]["place"]
    return {
        "percentil_original_estres": round(p["percentile"], 1),
        "brecha_mediana_pct_estres": None
        if p["gap_pct"] is None
        else round(p["gap_pct"], 1),
        "distancia_IQR_estres": None
        if p["gap_iqr"] is None
        else round(p["gap_iqr"], 2),
    }
