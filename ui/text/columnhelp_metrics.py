"""The «?» of every SQX metric column, keyed by the metric's name without its sample suffix.

Each sentence follows the snippet SQX computes the column with (`internal/extend/Snippets/SQ/
Columns/Databanks/*.java`) or, for the project's own columns (PSR, TRL Ratio, DoF Ratio, Param
Count), `user/extend/…` and `knowhow/columns/`. The sample (IS, OOS, OOS1, IS+OOS1) is the
column header's, so no sentence names one.
"""

METRICS = {
    "Net profit": "Beneficio neto en la moneda de la cuenta, con los costes que cargó la tarea "
                  "de SQX (spread, comisión, slippage, swap), en el tramo de la cabecera.",
    "# of trades": "Operaciones cerradas en el tramo de la cabecera. Es la muestra de todas las "
                   "demás cifras: con pocas, cualquier ratio es frágil.",
    "Profit factor": "Beneficio bruto de las ganadoras entre la pérdida bruta de las perdedoras, "
                     "en dinero. 1 es quedar a cero; por debajo de 1, pierde.",
    "Sharpe Ratio": "Sharpe anualizado (×√252) de los rendimientos diarios en % de la cuenta, "
                    "días laborables sin operar incluidos y descontado un 5 % anual, como lo "
                    "calcula SQX. No se compara con el Sharpe por operación de otros estudios.",
    "Sortino Ratio": "Como el Sharpe de SQX (diario, anualizado), pero dividiendo sólo por la "
                     "dispersión de los días negativos: no castiga la volatilidad al alza.",
    "Ret/DD Ratio": "Beneficio neto entre el drawdown máximo en dinero del mismo tramo: cuántas "
                    "veces gana lo peor que llegó a caer.",
    "Drawdown": "La mayor caída del saldo de operaciones cerradas desde su pico, en dinero de la "
                "cuenta. No ve el flotante dentro de una operación.",
    "Max DD %": "La mayor caída del saldo (capital inicial más operaciones cerradas) desde su "
                "pico, en % de ese pico. No ve el flotante dentro de una operación.",
    "Winning Percent": "Operaciones ganadoras sobre ganadoras más perdedoras, en %. Se lee junto "
                       "al tamaño medio de lo que se gana y se pierde: sola no dice si gana.",
    "Win/Loss ratio": "Número de operaciones ganadoras entre número de perdedoras: cuenta "
                      "operaciones, no dinero.",
    "Avg. Win": "Beneficio medio de una operación ganadora, en dinero de la cuenta.",
    "Avg. Loss": "Pérdida media de una operación perdedora, en dinero de la cuenta.",
    "Avg. Bars Win": "Barras que dura de media una operación ganadora, en el timeframe de la "
                     "estrategia.",
    "Avg. Bars Loss": "Barras que dura de media una operación perdedora, en el timeframe de la "
                      "estrategia.",
    "Avg. Bars in Trade": "Barras que dura de media una operación, ganadora o perdedora, en el "
                          "timeframe de la estrategia.",
    "R Expectancy": "Beneficio neto por operación en múltiplos de la pérdida media: 0,2 es ganar "
                    "de media una quinta parte de lo que se lleva una perdedora típica.",
    "SQN": "System Quality Number de Van Tharp: resultado medio por operación, en múltiplos de "
           "la pérdida media, entre su desviación típica y por √N, con N tope de 100 "
           "operaciones.",
    "Annual % Return": "Suma del resultado de cada operación en % de la cuenta, dividida entre "
                       "los años de datos del tramo: retorno anual simple, sin capitalizar.",
    "CAGR/Max DD %": "Crecimiento anual compuesto (CAGR, %) entre el Max DD %: cuántos puntos "
                     "de crecimiento anual compra cada punto de caída máxima.",
    "CalmarRatio": "En SQX es la misma cifra que CAGR/Max DD %: el CAGR entre la caída máxima "
                   "en %.",
    "Ulcer Index %": "Profundidad y duración de las caídas a la vez, en %: raíz de la suma de los "
                     "DD % al cuadrado tras cada operación, dividida entre el número de "
                     "operaciones (la fórmula de SQX).",
    "Stability": "Cuánto se parece la curva de capital diaria a la recta que une su primer y su "
                 "último valor (correlación al cuadrado, de 0 a 1), en negativo si el neto es "
                 "negativo. Cerca de 1, sube recta, sin tramos planos ni caídas largas.",
    "RSquared": "R² de la curva de capital diaria contra la recta que une su inicio y su final, "
                "de 0 a 1: cómo de recta es, sin mirar si sube o baja.",
    "Symmetry": "Beneficio neto del lado menor (largos o cortos) en % del lado mayor cuando los "
                "dos tienen el mismo signo; 0 si opera un solo lado o si uno gana y el otro "
                "pierde. 100 % es que los dos lados aportan lo mismo.",
    "ZScore": "Test de rachas sobre la secuencia de ganadoras y perdedoras. Cerca de 0, rachas "
              "como las del azar; muy negativo, se agrupan en rachas; muy positivo, se "
              "alternan más de lo esperable.",
    "Exposure": "Parte del periodo del backtest con alguna posición abierta, contada por días "
                "por SQX.",
    "Fitness": "La puntuación de 0 a 1 con la que la tarea de SQX ordena sus estrategias según "
               "su criterio de fitness. Sólo compara estrategias de la misma tarea.",
    "PSR": "Probabilistic Sharpe Ratio (columna propia del proyecto): probabilidad, de 0 a 1, de "
           "que el Sharpe real por operación sea mayor que 0, corregida por el número de "
           "operaciones, la asimetría y la curtosis. Su snippet marca 0,95 como umbral.",
    "TRL Ratio": "Operaciones que tiene entre las mínimas (MinTRL) que necesitaría para un PSR "
                 "de 0,95 con su Sharpe, asimetría y curtosis. Por encima de 1 el historial "
                 "basta para fiarse del Sharpe; por debajo, todavía no.",
    "DoF Ratio": "Operaciones por parámetro optimizado (columna propia del proyecto; cuenta "
                 "periodos, shifts, constantes, otros parámetros y salidas usadas). Su autor "
                 "marca más de 10 cómodo, de 5 a 10 sospechoso y menos de 5 muy sospechoso.",
    "Param Count": "Parámetros que la búsqueda pudo mover: periodos, constantes, niveles de "
                   "entrada, otros parámetros y salidas usadas. El proyecto lo recalcula del "
                   "XML de la estrategia; no cuenta shifts ni el número mágico.",
}
