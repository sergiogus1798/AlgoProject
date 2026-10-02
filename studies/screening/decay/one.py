"""One strategy's decay as the contract's data: its verdict, its numbers and its OOS years."""

import time

import pandas as pd

from core.study import blocks, result as envelope
from studies.screening.analysis import decay

MODULE = "studies.screening.decay"
STATE = {"MANTENER": "pass", "DUDOSA": "watch", "DESCARTAR": "fail"}
MEANING = {"MANTENER": "El Sharpe fuera de muestra es significativo, la mayoría de sus años "
                       "ganan y ningún trimestre concentra el beneficio.",
           "DUDOSA": "Le queda filo fuera de muestra, pero no basta: o no se distingue de cero, "
                     "o gana en pocos años, o un trimestre pesa demasiado.",
           "DESCARTAR": "Fuera de muestra no le queda filo, pierde en la mayoría de sus años o "
                        "debe su beneficio a un solo trimestre."}


def run(strategy: str, inputs: dict, cfg: dict) -> dict:
    """The decay of one strategy, the same row the population run gives it.

    Args:
        strategy: Its name as the databank spells it.
        inputs: {"curve": daily cumulative P&L, IS and OOS joined; "identity": str | None}.
        cfg: {"split", "end"}, YYYY-MM-DD.

    Returns:
        The contract dict, `summary` = its verdict.csv row. A one-strategy run drops no
        duplicates: that is a population fact.
    """
    started = time.time()
    row = decay.diagnose(inputs["curve"], cfg["split"], cfg["end"])
    word = decay.verdict(row)
    after = inputs["curve"].diff().dropna()[cfg["split"]:cfg["end"]]
    years = after.groupby(after.index.year).sum()
    numbers = pd.DataFrame(
        [["Sharpe IS", row["sharpe_is"]], ["Sharpe OOS", row["sharpe_oos"]],
         ["retención", row["retention"]], ["t del Sharpe OOS", row["t"]],
         ["años OOS positivos", f"{row['years_positive']} de {row['years']}"],
         ["peor año OOS", row["worst_year"]],
         ["concentración en el mejor trimestre", row["concentration"]],
         ["beneficio neto OOS", row["net_profit_oos"]]], columns=["", "valor"])
    return envelope.envelope(
        MODULE, strategy, inputs["identity"], cfg, started,
        [envelope.tab("decay", "Decaimiento", [
            blocks.table("Cuánto del filo sobrevivió", numbers,
                         f"Con t por debajo de {decay.SIGNIFICANT_T} el Sharpe fuera de muestra "
                         "no se distingue de cero. Concentración por encima de 1: pierde "
                         "dinero fuera de ese trimestre."),
            {"kind": "bars", "title": "Beneficio fuera de muestra por año", "unit": "USD",
             "reference": 0.0,
             "items": [{"label": str(y), "value": float(v), "error": None,
                        "state": "pass" if v > 0 else "fail"} for y, v in years.items()]}],
            note=f"IS hasta {cfg['split']} · OOS {cfg['split']} → {cfg['end']}.")],
        blocks.verdict(word, STATE[word], MEANING[word], row["t"]),
        summary={**row, "verdict": word})
