"""One strategy's trades, IS against OOS: return, MAE and MFE as two overlaid densities."""

import time

import numpy as np
from scipy.stats import ks_2samp

from core.study import blocks, result as envelope

MODULE = "studies.screening.isOos.report"
# The money columns read three ways, because the trades' size changes between samples (USDJPY
# 2026-09-27: median lot 3.3 IS, 4.6 OOS) and USD alone would call that a change of edge.
# Which reading the owner wants first is his question (closing of encargo 24 E3).
UNITS = {
    "USD": ("USD", lambda t, col: t[col]),
    "% del saldo": ("%", lambda t, col: 100 * t[col] / (t["Balance"] - t["Profit/Loss"])),
    "USD por lote": ("USD/lote", lambda t, col: t[col] / t["Size"]),
}
MONEY = {
    "Profit/Loss": ("retorno", "Retorno por operación"),
    "MAE ($)": ("mae", "MAE — lo peor que llegó a ir cada operación"),
    "MFE ($)": ("mfe", "MFE — lo mejor que llegó a ir cada operación"),
}
NOTE = ("Cada curva es una densidad —el área bajo cada una vale 1—, así IS y OOS se comparan "
        "aunque tengan distinto número de operaciones. Las colas más allá del eje se suman a "
        "la primera y la última barra.")
GLOSSARY = [
    {"term": "densidad", "text": "Altura de la barra = fracción de operaciones en ella dividida "
                                 "por su anchura. No depende de cuántas operaciones haya."},
    {"term": "desplazamiento de la mediana", "text": "Mediana OOS menos mediana IS, en la "
                                                     "unidad del gráfico."},
    {"term": "KS p", "text": "p de la prueba de Kolmogorov-Smirnov de dos muestras: la mayor "
                             "distancia entre las dos curvas acumuladas. Bajo, las dos muestras "
                             "no parecen salir de la misma distribución. Con duraciones que se "
                             "repiten (salida a X barras) el p es conservador."},
    {"term": "MAE / MFE", "text": "Máxima excursión adversa y favorable: lo peor y lo mejor que "
                                  "estuvo la operación abierta, en dinero de la cuenta."},
]


def compare(title: str, unit: str, is_: np.ndarray, oos: np.ndarray, cfg: dict) -> dict:
    """One per-trade metric of both samples on shared bins, with the shift between them.

    Args:
        title: What the block shows.
        unit: Its unit, as the contract writes it.
        is_, oos: One value per trade of each sample.
        cfg: The `trades` section of config.yaml.

    Returns:
        A distribution block with two series and its `shift`; `p` repeats the KS p.
    """
    both = np.concatenate([is_, oos])
    span = tuple(np.percentile(both, [cfg["tail_pct"], 100 - cfg["tail_pct"]]))
    ks = ks_2samp(is_, oos).pvalue
    return blocks.distribution(title, unit, both, None, NOTE, p=ks, bins=cfg["bins"],
                               series={"IS": is_, "OOS": oos}, span=span,
                               shift={"median": np.median(oos) - np.median(is_), "ks_p": ks})


def run(strategy: str, inputs: dict, cfg: dict) -> dict:
    """The per-trade distributions of one strategy, IS against OOS.

    Args:
        strategy: The strategy's name.
        inputs: `identity` and `trades` — its rows of a harvest's trades.parquet, `sample`
            only IS or OOS, with Open/Close time, Profit/Loss, Balance, Size, MAE ($), MFE ($).
        cfg: The study's config.

    Returns:
        The contract dict, verdict None: it describes. Never Net Profit or drawdown, which
        grow with the window; never the R multiple until the strategy carries a stop. The
        trade-duration distribution left on 2026-09-29 (owner): MAE and MFE stay.
    """
    started = time.time()
    t, c = inputs["trades"], cfg["trades"]
    side = {s: t[t["sample"] == s] for s in ("IS", "OOS")}
    shown, summary = [], {"n_is": len(side["IS"]), "n_oos": len(side["OOS"])}
    for col, (key, title) in MONEY.items():
        for option, (unit, read) in UNITS.items():
            b = compare(title, unit, read(side["IS"], col).to_numpy(),
                        read(side["OOS"], col).to_numpy(), c)
            shown.append({**b, "select": {"unidad": option}})
            if option == "USD":
                summary |= {f"{key}_shift": b["shift"]["median"], f"{key}_ks_p": b["shift"]["ks_p"]}
    unit = {"key": "unidad", "label": "Unidad del dinero", "options": list(UNITS),
            "default": next(iter(UNITS))}
    tab = envelope.tab("trades", "IS contra OOS, operación por operación", shown, [unit],
                       "Las mismas medidas por operación dentro y fuera de muestra. "
                       "Sólo medidas por operación: el beneficio neto y el drawdown crecen "
                       "con la longitud de la ventana y no se comparan así. El múltiplo R "
                       "espera a que la estrategia lleve stop (paso 24).")
    return envelope.envelope(MODULE, strategy, inputs["identity"], cfg, started, [tab],
                             glossary=GLOSSARY, summary=summary)
