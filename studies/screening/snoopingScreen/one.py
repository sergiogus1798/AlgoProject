"""One strategy against buy and hold at its own risk, and whether the StepM can name it."""

import time

import pandas as pd

from core.study import blocks, result as envelope

MODULE = "snoopingScreen"


def run(identity: str, got: dict, cfg: dict) -> dict:
    """What the screen says about one strategy, read off measure.run()'s table.

    Args:
        identity: The strategy's identity, the table's index.
        got: What measure.run() returned.
        cfg: What inputs.config() returned.

    Returns:
        The contract dict. SUPERIOR only when the StepM names it; a Sharpe above buy and
        hold's that the StepM does not name is `watch`, because one strategy beating the
        asset is what a search of K produces by chance.
    """
    started = time.time()
    r = got["table"].loc[identity]
    beats = r["sharpe"] > got["sharpe_bh"]
    state = "pass" if r["superior"] else "watch" if beats else "fail"
    fwer = cfg["stepm"]["fwer"]
    meaning = (f"El StepM la nombra: bate al buy & hold a igual riesgo con una probabilidad "
               f"de error de la familia entera de {fwer}." if r["superior"] else
               f"Su Sharpe supera al del buy & hold, pero entre {got['K']} probadas eso lo "
               f"da el azar: el StepM no la nombra." if beats else
               "Su Sharpe no llega al del buy & hold a igual riesgo.")
    said = blocks.verdict("SUPERIOR" if r["superior"] else "NO SUPERIOR", state, meaning, None, [
        {"label": "Sharpe", "state": "pass" if beats else "fail", "value": r["sharpe"],
         "note": f"buy & hold: {got['sharpe_bh']:.3f}"},
        {"label": "exceso diario", "state": "pass" if beats else "fail",
         "value": r["excess_day"], "note": "USD por día sobre el buy & hold a igual riesgo"},
        {"label": "puerta OOS", "state": "pass" if r["gate_survives"] else "fail",
         "value": None, "note": "la sobrevive" if r["gate_survives"] else "murió en ella"}])
    table = blocks.table("Contra el buy & hold", pd.DataFrame(
        [["Sharpe anual de la estrategia", r["sharpe"]],
         ["Sharpe anual del buy & hold", got["sharpe_bh"]],
         ["Lotes de buy & hold a igual riesgo", r["lots_bh"]],
         ["Exceso medio diario (USD)", r["excess_day"]]], columns=["qué", "valor"]),
        "El buy & hold se dimensiona para que su P&L diario sea tan volátil como el de la "
        "estrategia; entonces un exceso positivo es exactamente un Sharpe mayor.")
    name = r["strategy"] if isinstance(r["strategy"], str) else r["strategy_build"]
    return envelope.envelope(MODULE, name, identity, cfg, started,
                             [envelope.tab("benchmark", "Contra el buy & hold", [table])], said,
                             summary={"superior": bool(r["superior"]),
                                      "sharpe": float(r["sharpe"]),
                                      "excess_day": float(r["excess_day"])})
