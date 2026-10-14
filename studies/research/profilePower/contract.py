"""The power study as the study contract: what the window and the page draw."""

from typing import Any
import pandas as pd

from core.study import blocks, result

GLOSSARY = [
    {"term": "efecto plantado", "text": "Ganancia media bruta por operación que se añade a las "
                                        "barras que siguen a la condición de la medida, en "
                                        "múltiplos del coste de ida y vuelta."},
    {"term": "significant", "text": "Parte de las réplicas en las que la prueba del perfil "
                                    "alcanza la p que hoy exige la corrección del mapa entero."},
    {"term": "passes", "text": "Parte de las réplicas que pasan los cuatro filtros del perfil."},
    {"term": "single", "text": "Parte de las réplicas con p ≤ 0,05 sin corregir: la regla "
                               "juzgada como si fuera la única que se mira."},
    {"term": "mde", "text": "Efecto mínimo detectable: el efecto plantado más pequeño que se "
                            "detecta 8 de cada 10 veces. Vacío: no se alcanza ni con el mayor."},
    {"term": "sees_2x", "text": "Parte de las pruebas del mapa cuyo efecto mínimo detectable "
                                "es de 2 costes o menos."}]


def build(tables: dict[str, pd.DataFrame], cfg: dict, started: float) -> dict[str, Any]:
    """The contract dict of the study.

    Args:
        tables: `mde` and `curve` (per family, measure and timeframe), `calibration`,
            `reach` (the whole map per family and timeframe) and `reach_class`.
        cfg: The parsed config.
        started: time.time() when the run began.

    Returns:
        A validated result; its summary carries the headline numbers.
    """
    mde, reach = tables["mde"], tables["reach"]
    cut = cfg["judge"]["cut"]
    tabs = [
        result.tab("mde", "Efecto mínimo detectable", [blocks.table(
            "Por familia, medida y marco: el efecto más pequeño que se detecta el "
            f"{cfg['judge']['power']:.0%} de las veces", mde,
            f"En múltiplos del coste de ida y vuelta, a p ≤ {cut:.5f}. alarm_*: detección sin "
            "efecto plantado (la tasa de falsa alarma).", 3)]),
        result.tab("curva", "Curva de potencia", [blocks.table(
            "Tasa de detección por efecto plantado", tables["curve"],
            "significant: al corte del mapa; passes: los cuatro filtros; single: 5 % sin "
            "corregir.", 3)]),
        result.tab("mapa", "Lo que el mapa entero puede ver", [
            blocks.table("Por familia y marco, sobre las pruebas reales del mapa", reach,
                         "mde_median: mediana del efecto mínimo detectable, en costes y en "
                         "ATR. sees_Nx: parte de las pruebas que verían un edge de N costes.", 3),
            blocks.table("Por clase de activo y marco", tables["reach_class"], "", 3)]),
        result.tab("calibracion", "La aproximación frente a la simulación", [blocks.table(
            "Detección simulada y la que predice la aproximación normal", tables["calibration"],
            "La tabla del mapa entero usa la aproximación: aquí se ve cuánto se le puede "
            "creer.", 3)])]
    return result.envelope(
        "studies.research.profilePower", None, None, cfg, started, tabs, glossary=GLOSSARY,
        summary={"cut": cut, "replications": int(tables["curve"]["runs"].sum()),
                 "tests_in_map": int(reach["tests"].sum()),
                 "share_sees_2x": float((reach["sees_2x"] * reach["tests"]).sum()
                                        / reach["tests"].sum())})
