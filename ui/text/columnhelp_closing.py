"""The «?» of the closing studies' columns: exposure's fixed fields, and the two families that
come one column per percentile (atrCalculator) or per buy-and-hold sizing (exposure).

Grounded in `studies/closing/exposure/{compare,occupancy,benchmark,verdict}.py` and
`studies/closing/atrCalculator/{threshold,noreturn,transfer,one}.py`.
"""

import re

WINDOW = "en la ventana del estudio (oos1 por defecto)"

EXPOSURE = {
    "n": f"Operaciones de la estrategia {WINDOW}.",
    "days": "Días de calendario de la ventana, tomada de la política del activo y no de la "
            "primera y la última operación.",
    "equity_start": "Saldo antes de la primera operación de la ventana. El OOS continúa la "
                    "cuenta del IS: no es el depósito inicial.",
    "exp_share": "Fracción de las barras de la ventana (rejilla M30) con alguna posición "
                 "abierta, de 0 a 1.",
    "exp_hours_per_week": "Horas por semana con alguna posición abierta, de media en la "
                          "ventana.",
    "exp_avg_notional_pct": "Nocional abierto medio en % del saldo inicial, promediado en toda "
                            "la ventana, también cuando está fuera.",
    "exp_notional_when_in_pct": "Nocional abierto medio en % del saldo inicial, sólo en las "
                                "barras con posición: el apalancamiento con que opera cuando "
                                "está dentro.",
    "exp_tilt": "Lotes con signo entre lotes totales, de −1 a 1: +1 siempre largo, −1 siempre "
                "corto, 0 tan a menudo de un lado como del otro.",
    "return_per_exposure_pct": "Retorno de la estrategia en la ventana (%) dividido por su "
                               "fracción de tiempo expuesta: lo que rendiría dentro todo el "
                               "tiempo a su ritmo. Extrapolación: mide la calidad del tiempo, "
                               "no un retorno alcanzable.",
    "efficiency": "Ese retorno por tiempo expuesto como múltiplo del retorno del buy & hold a "
                  "igual riesgo. 1 es tan productivo por hora como tener el activo; el estudio "
                  "aprueba desde 2.",
    "return_ratio": "Retorno de la estrategia entre el del buy & hold a igual riesgo, en la "
                    "misma ventana y sin ajustar por exposición.",
    "dd_ratio": "Max DD % de la estrategia entre el del buy & hold a igual riesgo. Por debajo "
                "de 1, cae menos que tener el activo.",
    "hours_off": "Horas por semana sin ninguna posición (168 menos las expuestas): horas sin "
                 "hueco, noticias ni drawdown.",
    "captured": "Fracción del movimiento absoluto total del mercado que ocurrió en barras en "
                "las que la estrategia estaba dentro.",
    "aligned": "Fracción de ese movimiento total que tuvo a favor, neta de la que tuvo en "
               "contra. Mucho capturado con alineación de 0 o menos se parece más a estar "
               "presente en los buenos tramos que a una ventaja propia.",
    "reasons": "Los motivos que decidieron el veredicto o que impiden leerlo: pocas "
               "operaciones, ventana corta, pierde, el buy & hold pierde, eficiencia baja, "
               "parece timing de mercado.",
}

SIZING = {"one_lot": "buy & hold de un lote fijo",
          "avg_size": "buy & hold del tamaño medio de las operaciones de la estrategia",
          "equal_risk": "buy & hold del tamaño que iguala su volatilidad diaria a la de la "
                        "estrategia (la convención que juzga)"}
STAT = {"net": "Beneficio neto, en dinero de la cuenta,",
        "return_pct": "Retorno sobre el saldo inicial, en %,",
        "cagr_pct": "Crecimiento anual compuesto (CAGR), en %,",
        "maxdd_pct": "Mayor caída desde el pico del saldo, en %,",
        "vol": "Volatilidad (desviación típica de la P&L diaria en dinero, días sin posición "
               "incluidos)",
        "sharpe": "Sharpe anualizado (×√252) de la P&L diaria, días sin posición incluidos,"}

BENCH = re.compile(r"bench_(one_lot|avg_size|equal_risk)_(net|return_pct|cagr_pct|maxdd_pct|"
                   r"vol|sharpe)$")
STRAT = re.compile(r"strat_(net|return_pct|cagr_pct|maxdd_pct|vol|sharpe)$")
LOTS = re.compile(r"lots_(one_lot|avg_size|equal_risk)$")

ATR = re.compile(r"(x|low|high|unreliable|zone|effective_oos1|effective_oos2)_p(\d+(?:\.\d+)?)$")
WINNERS = re.compile(r"n_winners_(build|oos1|oos2)$")
SEGMENT = {"build": "build (IS)", "oos1": "oos1", "oos2": "oos2"}
PERCENTILE = {
    "x": "X del p{p}: el percentil {p} del MAE/ATR de las ganadoras del IS, en múltiplos de "
         "ATR(20). Un stop a X·ATR(20) de la entrada deja intacto el {p} % de esas ganadoras.",
    "low": "Extremo inferior del intervalo al 95 % de la X del p{p}, en ATR, al remuestrear las "
           "ganadoras del IS 9.999 veces: otra muestra de ganadoras daría otra X.",
    "high": "Extremo superior del intervalo al 95 % de la X del p{p}, en ATR, al remuestrear "
            "las ganadoras del IS 9.999 veces: otra muestra de ganadoras daría otra X.",
    "unreliable": "Verdadero si el intervalo de la X del p{p} es más ancho que la mitad de X: "
                  "«poco fiable», otro puñado de ganadoras daría otra X.",
    "zone": "Dónde cae la X del p{p} en la curva del IS: «ruido» (muchas operaciones que llegan "
            "ahí acaban ganando: cortar es cortar ruido), «sin retorno» (casi ninguna se "
            "recupera y acaban peor que −X) o «pocas operaciones».",
    "effective_oos1": "Qué percentil de las ganadoras de oos1 es la X del p{p} del IS, en %. "
                      "Cerca de {p} se transfiere; por debajo, en oos1 ese stop cortaría más "
                      "ganadoras que en el IS.",
    "effective_oos2": "Qué percentil de las ganadoras de oos2 es la X del p{p} del IS, en %. "
                      "Cerca de {p} se transfiere; por debajo, en oos2 ese stop cortaría más "
                      "ganadoras que en el IS.",
}


def exposure(field: str) -> str | None:
    """Exposure's sentence for one field, the sizing and statistic families included."""
    if field in EXPOSURE:
        return EXPOSURE[field]
    if got := BENCH.match(field):
        return f"{STAT[got[2]]} del {SIZING[got[1]]}, {WINDOW}."
    if got := STRAT.match(field):
        return f"{STAT[got[1]]} de la estrategia, {WINDOW}: lo que se compara con el buy & hold."
    if got := LOTS.match(field):
        return f"Lotes que mantiene toda la ventana el {SIZING[got[1]]}."
    return None


def atr(field: str) -> str | None:
    """atrCalculator's sentence for one per-percentile or per-segment field."""
    if got := ATR.match(field):
        return PERCENTILE[got[1]].format(p=got[2])
    if got := WINNERS.match(field):
        return (f"Operaciones ganadoras (neto mayor que cero) en {SEGMENT[got[1]]}: las que "
                f"miden la X y su transferencia. Con menos de 30 fuera de muestra, la "
                f"transferencia sólo se enseña.")
    return None
