"""One strategy against its feed's anomalies, as the contract's data: the alarm and what it touched."""

import time

import pandas as pd

from core.study import blocks, result as envelope
from studies.data.feedQuality import alarm

MODULE = "feedQuality"
STATE = {alarm.ALARM: "fail", alarm.QUIET: "pass", alarm.SHORT: "none"}
GLOSSARY = [
    {"term": "Operación marcada", "text": "Una operación en cuya vela de señal, de entrada o de "
     "salida (en el timeframe de la estrategia) cae un pico-y-vuelta, un congelado o un hueco "
     "del feed; o, si la estrategia lleva stop, uno de ellos mientras está abierta."},
    {"term": "Columna que manda", "text": "Cierre para entradas a mercado y salida por señal; "
     "mecha si la estrategia entra con orden stop o límite, o sale por SL, PT o trailing: un "
     "tick malo en la mecha llena la orden sin mover el cierre. Se lee del .sqx."},
    {"term": "% del beneficio en riesgo", "text": "El beneficio neto de las marcadas entre el "
     "beneficio neto total. Si el total no es positivo, se da el importe de las marcadas."},
    {"term": "Alarma", "text": "Test de permutación unilateral: ¿ganan las marcadas más que "
     "10.000 grupos al azar del mismo tamaño? Salta con p < 0,01; con menos de 10 marcadas, "
     "«insuficiente». Es un aviso, no un descarte."}]
TOUCHED = ["cierre", "mecha", "extremo", "congelado", "hueco", "durante"]


def run(strategy: str, identity: str, marked: pd.DataFrame, rules: dict, cfg: dict) -> dict:
    """One strategy's attribution.

    Args:
        strategy: Its name in the retest databank.
        identity: SHA-256 of its normalised XML.
        marked: touch.mark()'s output for its trades, IS and OOS together.
        rules: template.rules() for the strategy.
        cfg: inputs.config()'s dict.

    Returns:
        The contract dict. It never recomputes a metric without the flagged trades
        (decision 13): it says how much of the profit is at risk and whether that share is
        more than chance would give.
    """
    started = time.time()
    pnl, flagged = marked["Profit/Loss"].to_numpy(), marked["marcada"].to_numpy()
    got = alarm.test(pnl, flagged, cfg, identity)
    risk = (f"{100 * got['at_risk']:.1f} % del beneficio neto" if got["at_risk"] is not None
            else f"{got['flagged_pnl']:.2f} de neto (el total no es positivo)")
    spike_share = marked.loc[flagged, "spike"].mean() if got["flagged"] else 0.0
    said = blocks.verdict(
        got["verdict"], STATE[got["verdict"]],
        f"{got['flagged']} de {got['n']} operaciones tocan una anomalía del feed y llevan "
        f"{risk}. " + (f"p = {got['p']:.4f} contra grupos al azar del mismo tamaño. "
                       if got["p"] is not None else "Menos de 10 marcadas: no se juzga. ")
        + f"De las marcadas, {100 * spike_share:.0f} % tocan un pico-y-vuelta (posible error "
        f"de precio) y el resto un congelado o un hueco. Columna que manda: {rules['column']}.",
        got["p"])
    head = pd.DataFrame([{"operaciones": got["n"], "marcadas": got["flagged"],
                          "beneficio de las marcadas": got["flagged_pnl"],
                          "% del beneficio en riesgo": None if got["at_risk"] is None
                          else 100 * got["at_risk"], "p": got["p"],
                          "columna": rules["column"], "lleva stop": rules["stop"]}])
    what = {"kind": "bars", "title": "Qué tocan las operaciones (en sus tres velas)",
            "unit": "operaciones", "reference": None,
            "items": [{"label": c, "value": float(marked[c].sum()), "error": None,
                       "state": "info"} for c in TOUCHED]}
    split = marked.groupby("sample").agg(operaciones=("marcada", "size"),
                                          marcadas=("marcada", "sum"))
    split["neto de las marcadas"] = marked[flagged].groupby("sample")["Profit/Loss"].sum()
    tabs = [envelope.tab("alarm", "Alarma", [blocks.table("Resumen", head,
                         "Nunca se recalculan las métricas sin las marcadas: sería limpiar "
                         "el backtest con otro nombre (decisión 13).")]),
            envelope.tab("touched", "Qué tocan", [what, blocks.table(
                "IS y OOS", split.fillna(0).reset_index(),
                "El test lee las dos muestras juntas; esto sólo reparte lo marcado.")])]
    if got["draws"] is not None:
        tabs[0]["blocks"].append(blocks.distribution(
            "Beneficio de grupos al azar del mismo tamaño", "USD", got["draws"],
            got["observed"], "La línea es el beneficio neto de las marcadas.", p=got["p"]))
    listed = marked[flagged][["Open time", "Close time", "sample", "Profit/Loss", *TOUCHED]]
    tabs.append(envelope.tab("list", "Operaciones marcadas", [blocks.table(
        "Operaciones marcadas", listed.head(500).astype({"Open time": str, "Close time": str}))]))
    return envelope.envelope(MODULE, strategy, identity, cfg, started, tabs, said,
                             glossary=GLOSSARY,
                             summary={"n": got["n"], "flagged": got["flagged"], "p": got["p"],
                                      "at_risk": got["at_risk"], "alarm": got["verdict"],
                                      "column": rules["column"]})
