# 9. Diccionario — todo lo que se puede extraer, campo por campo

Esta página no explica cómo se corre nada: eso está en el capítulo 8. Aquí está el **inventario
completo** de lo que sale de una estrategia que ha pasado por el Sys. Param Permutation, con el
nombre exacto de cada campo y qué es. Es la página que se tiene abierta al lado mientras se escribe
el `pandas`.

Todo lo que aparece aquí se lee del `.sqx` directamente. No hace falta SQX abierto ni el worker.

### De dónde sale cada cosa

| fichero | una fila por | lo llena |
|---|---|---|
| `runs.csv` | estrategia | el resumen de la tirada de permutaciones |
| `metrics.csv` | estrategia × métrica | la tabla mediana / valor original del panel |
| `histograms.csv` | estrategia × métrica × bin | los histogramas que dibuja el panel |
| `permutations.csv` | estrategia × permutación | **solo si la casilla 3D estaba quitada** |
| `permutation_params.csv` | estrategia × permutación × parámetro | ídem |
| `trades/<estrategia>.csv` | operación | el backtest principal, vía `export_trades.py` |
| `bars/bars_<TF>.csv` | barra | las velas sobre las que operó |

---

## 1. `runs.csv` — la tirada entera en una línea

| campo | qué es |
|---|---|
| `strategy` | nombre de la estrategia, tal y como aparece en el databank |
| `permutations` | cuántas permutaciones se probaron |
| `profitable` | cuántas acabaron con beneficio positivo |
| `losing` | cuántas acabaron en pérdida |
| `zero` | cuántas acabaron exactamente en cero, normalmente porque no llegaron a operar |
| `profitable_pct` | `profitable` en porcentaje. **La cifra de cabecera del SPP**: cuánto del entorno de parámetros gana |
| `avg_profit` | beneficio medio de todas las permutaciones, en divisa de la cuenta |
| `top_profit` | el beneficio de la mejor permutación |
| `stdev` | desviación típica del beneficio entre permutaciones. Mide lo mucho que se mueve el resultado al mover los parámetros |
| `uniform_changes` | contador interno de SQX sobre lo uniforme que es la distribución. No está documentado qué escala usa |
| `parameters` | los nombres de los parámetros que se permutaron, separados por espacio |

Hay dos campos más que el lector de Python devuelve y que no se escriben al CSV porque no son
tabulares: `last_count` (repite `permutations`) y `stdev_computed` (siempre 0 en esta instalación).

## 2. `metrics.csv` — la tabla del panel

| campo | qué es |
|---|---|
| `strategy` | nombre de la estrategia |
| `metric` | nombre de la métrica; los 135 posibles están en la tabla grande de más abajo |
| `median` | el valor **mediano** de esa métrica entre todas las permutaciones |
| `orig` | el valor de la estrategia original, la que tú tienes guardada |
| `orig_over_median` | `orig / median`. **La columna que decide.** Cerca de 1 el resultado no depende de los parámetros; muy por encima, vive en un pico |

## 3. `histograms.csv` — la distribución tal y como la agrupó SQX

| campo | qué es |
|---|---|
| `strategy` | nombre de la estrategia |
| `metric` | métrica a la que pertenece el histograma |
| `bin` | número de bin, de 0 a 19. Siempre son 20 |
| `edge` | etiqueta del borde inferior del bin. **Puede venir vacía**: SQX se salta etiquetas para que quepan en el eje |
| `frequency` | cuántas permutaciones cayeron en ese bin |
| `is_median` | `True` en el bin donde cae la mediana |
| `is_orig` | `True` en el bin donde cae el valor original |

## 4. `permutations.csv` — una fila por permutación

| campo | qué es |
|---|---|
| `strategy` | nombre de la estrategia |
| `permutation` | número de permutación desde 0. **La fila `-1` es la estrategia original**, para comparar contra ella sin buscarla aparte |
| los otros 152 | los estadísticos, uno por columna. Los nombrados son los de la tabla grande; los demás salen como `stat:<tipo>:<índice>` |

## 5. `permutation_params.csv` — qué valores le tocaron a cada permutación

| campo | qué es |
|---|---|
| `strategy` | nombre de la estrategia |
| `permutation` | mismo número que en `permutations.csv`; se cruzan por `strategy` + `permutation` |
| `parameter` | nombre del parámetro, tal y como lo llama la estrategia (`LWMAPeriod1`, `ExitAfterBars1`...) |
| `value` | el valor que SQX le puso en esa permutación |

Los nombres de parámetro **cambian de una estrategia a otra**: son los de sus propios bloques. Por
eso van en formato largo y no en columnas.

---

## 6. Las 135 métricas

Esto es el catálogo entero de columnas de databank de tu instalación, que es exactamente lo que el
SPP guarda por métrica. Los nombres cortos son los que usan `metrics.csv` y `permutations.csv`; el
nombre en SQX es el que ves en la GUI.

- **unidad** — `€` divisa de la cuenta · `%` porcentaje · `pips` · `ratio` · `entero` · `texto` ·
  `fecha` · `—` no declarada en el código de la columna.
- **mejor** — hacia dónde considera SQX que es mejor: `↑` más alto, `↓` más bajo, `≈` ni una cosa ni
  otra, `—` no declarado.
- **por permutación** — si además aparece en `permutations.csv`, es decir si se puede mirar
  permutación a permutación y no solo como mediana.

| campo | nombre en SQX | qué es | unidad | mejor | por permutación |
|---|---|---|---|---|---|
| `AHPR` | AHPR | Rendimiento medio por periodo de tenencia (Arithmetic Holding Period Return), calculado sobre los retornos anuales. | ratio | ↓ | sí |
| `ActualDD` | Actual Drawdown | Drawdown que había abierto durante la ÚLTIMA operación del backtest. No es el máximo, es el del final. | — | — | sí |
| `ActualDrawdownPct` | Actual Drawdown / Max DD | El drawdown de la última operación dividido por el drawdown máximo. Cerca de 1 significa que el backtest termina en su peor momento. | — | — | sí |
| `AddMarketsNetProfitMedian` | AddMarketsNetProfitMedian | Mediana del beneficio neto en los mercados adicionales del retest cruzado. Vale 0 si la estrategia no se retesteó en otros mercados. | — | — | sí |
| `AddMarketsProfitFactorMedian` | AddMarketsProfitFactorMedian | Mediana del profit factor en los mercados adicionales del retest cruzado. | — | — | sí |
| `AddMarketsRetDDMedian` | AddMarketsRetDDMedian | Mediana del Ret/DD en los mercados adicionales del retest cruzado. | — | — | sí |
| `AddMarketsSharpeRatioMedian` | AddMarketsSharpeRatioMedian | Mediana del Sharpe en los mercados adicionales del retest cruzado. | — | — | sí |
| `AmbiguousTrades` | Ambiguous Trades | Operaciones que abren y cierran en la misma barra. Son ambiguas porque el backtest no puede saber qué pasó primero dentro de la barra. | entero | ↓ | sí |
| `AmbiguousTradesPct` | Ambiguous Trades % | Las anteriores como porcentaje del total de operaciones. Es la métrica de fiabilidad del backtest, no de rentabilidad. | % | ↓ | sí |
| `AnnualPctReturn` | Annual % Return | Rentabilidad porcentual anualizada sobre los años de datos. | % | ↑ | sí |
| `AnnualPctReturnDDRatio` | CAGR/Max DD % | CAGR dividido por el drawdown máximo en porcentaje. | ratio | ↑ | sí |
| `AvgAbsTrade` | Avg. Abs Trade | Beneficio absoluto medio por operación, contando las perdedoras en valor absoluto. | € | ↑ | sí |
| `AvgBarsInTrade` | Avg. Bars in Trade | Barras que dura una operación de media. | ratio | ↓ | sí |
| `AvgBarsLoss` | Avg. Bars Loss | Barras que dura de media una operación perdedora. | ratio | ↓ | sí |
| `AvgBarsWin` | Avg. Bars Win | Barras que dura de media una operación ganadora. | ratio | ↑ | sí |
| `AvgConsecLosses` | Avg Consec. Losses | Longitud media de las rachas de pérdidas. | ratio | ↓ | sí |
| `AvgConsecWins` | Avg Consec. Wins | Longitud media de las rachas de ganancias. | ratio | ↑ | sí |
| `AvgDrawdown` | Avg. Drawdown | Drawdown medio de todos los que hubo, no solo el máximo. | € | ↓ | sí |
| `AvgLoss` | Avg. Loss | Pérdida media de las operaciones perdedoras. | € | ↓ | sí |
| `AvgParametersStability` | Avg. Parameters Stability | Estabilidad media de los parámetros en el Walk Forward Matrix. Solo tiene valor si se corrió WF. | ratio | ↑ | no |
| `AvgPctDrawdown` | Avg. % Drawdown | Drawdown medio expresado en porcentaje. | % | ↓ | sí |
| `AvgPctProfitPerYear` | Avg. % Profit Per Year | Beneficio porcentual medio por año. | % | ↑ | sí |
| `AvgProfitPerDay` | Avg. Profit Per Day | Beneficio medio por día de trading. | € | ↑ | sí |
| `AvgProfitPerMonth` | Avg. Profit Per Month | Beneficio medio por mes. | € | ↑ | sí |
| `AvgProfitPerYear` | Avg. Profit Per Year | Beneficio medio por año. | € | ↑ | sí |
| `AvgTrStddevRatio` | Avg. trade / StdDev ratio | Operación media dividida por la desviación típica de las operaciones. Es el Sharpe por operación, sin anualizar. | — | — | sí |
| `AvgTrade` | Avg. Trade | Beneficio medio por operación (expectativa en dinero). | € | ↑ | sí |
| `AvgTradesPerDay` | Avg. Trades Per Day | Operaciones por día. | ratio | ↓ | sí |
| `AvgTradesPerMonth` | Avg. Trades Per Month | Operaciones por mes. | ratio | ↓ | sí |
| `AvgTradesPerYear` | Avg. Trades Per Year | Operaciones por año. | ratio | ↓ | sí |
| `AvgWin` | Avg. Win | Ganancia media de las operaciones ganadoras. | € | ↑ | sí |
| `BacktestDuration` | Backtest Duration (s) | Segundos que tardó el backtest en correr. Es un dato de la máquina, no de la estrategia. | texto | ↓ | no |
| `BestWF` | Best WF | Mejor resultado del Walk Forward. Vacío si no se corrió WF. | texto | ↑ | sí |
| `BiggestMAE` | Biggest MAE | La peor excursión adversa de todas las operaciones: cuánto llegó a estar en contra la operación que más sufrió. | € | ↑ | sí |
| `CAGR` | CAGR | Tasa de crecimiento anual compuesta. | % | ↑ | sí |
| `CalmarRatio` | CalmarRatio | Rentabilidad anualizada dividida por el drawdown máximo. | ratio | ↑ | sí |
| `Commission` | Commission/Swap ($) | Comisiones y swap pagados en total, en divisa de la cuenta. | € | ↓ | sí |
| `Complexity` | Complexity | Medida de complejidad de la estrategia que calcula SQX a partir de su estructura. | entero | ↓ | sí |
| `DateGenerated` | Date generated | Fecha en que SQX generó la estrategia. | fecha | ↓ | no |
| `DateLastModified` | Date last modified | Fecha del último cambio o retest de la estrategia. | fecha | ↓ | no |
| `DegreesOfFreedom` | Degrees of freedom | Grados de libertad: operaciones menos parámetros. Cuanto más bajo, más fácil es que el resultado sea casualidad. | entero | ↓ | sí |
| `DoFRatio` | DoF Ratio | Operaciones divididas por número de parámetros optimizados. Cuántos datos hay por cada grado de libertad. | ratio | ↑ | sí |
| `Drawdown` | Drawdown | Máxima caída desde un máximo de la curva de balance, en divisa de la cuenta. | € | ↓ | sí |
| `DrawdownPct` | Max DD % | El drawdown máximo en porcentaje. | % | ↓ | sí |
| `DrawdownPctOnInitial` | DD% of Initial | El drawdown máximo como porcentaje del depósito inicial, no del pico. | — | — | sí |
| `DrawdownPips` | Max DD pips | El drawdown máximo medido en pips. | pips | ↓ | sí |
| `EdgeDecayRatio` | Edge Ratio Decay | Puntuación 0-100 de calidad fuera de muestra construida sobre cuatro pilares. Columna propia, no estándar de SQX. | ratio | ↑ | sí |
| `EdgeRatioInPips` | Edge Ratio | Edge ratio en pips: relación entre excursión favorable y adversa. La definición exacta no viene documentada en esta instalación. | — | — | sí |
| `Efficiency` | Efficiency | Beneficio neto dividido por beneficio bruto: qué parte de lo que ganó se quedó después de las pérdidas. | — | — | sí |
| `EntryIndicators` | Entry indicators | Lista de indicadores que usan las condiciones de entrada. Texto. | texto | ↑ | no |
| `EquityAngle` | EquityAngle | Ángulo de la recta de regresión de la curva de equity. | ratio | ↑ | sí |
| `EquitySlope` | EquitySlope | Lo recta que es la curva de equity multiplicado por lo empinada que es. | ratio | ↑ | sí |
| `ExitIndicators` | Exit indicators | Lista de indicadores que usan las condiciones de salida. Texto. | texto | ↑ | no |
| `ExitQuality` | Exit quality | Beneficio total dividido por el MFE total: cuánto del movimiento favorable disponible llegó a capturar. | ratio | ↑ | sí |
| `Expectancy` | Expectancy | Expectativa por operación. | ratio | ↑ | sí |
| `Exposure` | Exposure | Barras con posición abierta dividido por barras totales de la muestra. | % | ↓ | sí |
| `ExposurePosition` | Exposure Position | Lo mismo que Exposure, en la versión que usa el motor Stockpicker considerando el número de posiciones abiertas. | % | ↓ | sí |
| `FiltersResult` | Filters result | PASSED o FAILED según los filtros de aceptación del databank. Texto. | texto | ↑ | no |
| `Fitness` | Fitness | Valor de fitness con el que el algoritmo genético ordenó la estrategia. | ratio | ↑ | sí |
| `GiniOOS` | Gini Coeff | Coeficiente de Gini del P&L por operación: 0 es que todas aportan lo mismo, 1 es que una sola se lo lleva todo. Columna propia. | ratio | ↓ | sí |
| `GrossLoss` | Gross loss | Suma de todas las operaciones perdedoras. | € | ↓ | sí |
| `GrossProfit` | Gross profit | Suma de todas las operaciones ganadoras. | € | ↑ | sí |
| `InitialDeposit` | Initial deposit | Depósito inicial del backtest. | ratio | ↑ | no |
| `KellyFormula` | Kelly formula | Fracción de Kelly: qué porcentaje del capital sugeriría arriesgar la fórmula con este win rate y payout. | — | — | sí |
| `LongestTrade` | Longest trade (days) | Duración en días de la operación más larga. | entero | ↓ | sí |
| `MagicNumber` | Magic number | Identificador que SQX pone a la estrategia para el broker. No es una métrica. | texto | ↓ | no |
| `MaxConsecLosses` | Max Consec. Losses | Racha más larga de pérdidas seguidas. | entero | ↓ | sí |
| `MaxConsecWins` | Max Consec. Wins | Racha más larga de ganancias seguidas. | entero | ↑ | sí |
| `MaxIntradayDrawdown` | Max Intraday Drawdown | Drawdown máximo mirando también dentro del día, no solo balances de cierre. | € | ↓ | sí |
| `MaxLoss` | Max Loss | La peor operación individual. | € | ↓ | sí |
| `MaxNewHighDuration` | Max Drawdown Duration | Días que tardó como mucho en hacer un nuevo máximo de equity. Es la duración del drawdown más largo. | entero | ↓ | sí |
| `MaxProfit` | Max Profit | La mejor operación individual. | € | ↑ | sí |
| `MaxTSIntradayDrawdown` | Max TS Intraday Drawdown | Drawdown intradía máximo en la versión TradeStation. | € | ↑ | sí |
| `MiniEquityChart` | Mini equity chart | La miniatura de la curva de equity que pinta la GUI. No es un número. | texto | ↓ | no |
| `NSymmetry` | NSymmetry | Simetría de beneficio entre largos y cortos, con la variante de que si un lado gana y el otro pierde devuelve −1 en vez de 0. | % | ↑ | no |
| `NetProfit` | Net profit | Beneficio neto total en divisa de la cuenta. Es la métrica de referencia del SPP. | € | ↑ | sí |
| `NetProfitInPct` | Net profit in % | El beneficio neto en porcentaje. | % | ↑ | sí |
| `NetProfitInPips` | Net profit in pips | El beneficio neto en pips. | pips | ↑ | sí |
| `Note` | Note | Nota escrita a mano en la estrategia. Texto. | texto | ↓ | no |
| `NumberOfCanceled` | # of canceled | Órdenes pendientes que se cancelaron sin llegar a ejecutarse. | entero | ≈ | no |
| `NumberOfLosses` | # of losses | Número de operaciones perdedoras. | entero | ↓ | sí |
| `NumberOfProfits` | # of profits | Número de operaciones ganadoras. | entero | ↑ | sí |
| `NumberOfTrades` | # of trades | Número total de operaciones. En el SPP es la métrica de control: si una permutación baja de golpe, es que la regla dejó de dispararse. | entero | ≈ | sí |
| `OpenDrawdown` | Open Drawdown | Drawdown calculado sobre el balance abierto más el MAE, es decir contando lo que se sufrió sin cerrar. | € | ↓ | sí |
| `OpenDrawdownPct` | Open Drawdown % | El anterior en porcentaje. | % | ↓ | sí |
| `Outlier` | Outlier1 | Peso de la operación atípica, SIN filtrar operaciones con el mismo P&L. | — | — | sí |
| `Outlier2` | Outlier1 | Peso de la operación atípica, filtrando las operaciones con el mismo P&L. | — | — | sí |
| `ParameterCount` | Param Count | Parámetros realmente buscados: periodos, constantes, niveles de entrada y salidas usadas. Excluye MagicNumber, variables de señal, Shift y salidas sin usar. Columna propia. | entero | ↓ | sí |
| `Parameters` | Parameters | Volcado en texto de los parámetros de la estrategia. | texto | ↑ | sí |
| `PayoutRatio` | Payout ratio | Ganancia media dividida por pérdida media. | ratio | ↑ | sí |
| `PriceIndicators` | Price indicators | Indicadores usados en los niveles de precio de entrada (stop o limit). Texto. | texto | ↑ | no |
| `ProbSharpeRatio` | PSR | Sharpe probabilístico (0-1): probabilidad de que el Sharpe verdadero sea mayor que cero. Columna propia. | ratio | ↑ | sí |
| `ProfitFactor` | Profit factor | Beneficio bruto dividido por pérdida bruta. | ratio | ↑ | sí |
| `ProfitableMonths` | Profitable Months | Meses cerrados en positivo. | entero | ↑ | sí |
| `ProfitableMonthsPct` | % Profitable Months | Porcentaje de meses en positivo. | % | ↑ | sí |
| `RExpectancy` | R Expectancy | Expectativa medida en R, es decir en múltiplos del riesgo por operación. | ratio | ↑ | sí |
| `RExpectancyScore` | R Expectancy Score | R Expectancy ponderada por el número de operaciones, para que una expectativa alta con pocas operaciones no gane. | ratio | ↑ | sí |
| `RSquared` | RSquared | R² de la regresión sobre la curva de equity: lo recta que es. | ratio | ↑ | sí |
| `RecoveryFactor` | RecoveryFactor | Beneficio neto dividido por el drawdown máximo. | ratio | ↑ | sí |
| `ResultsName` | Results Name | Nombre del resultado. Texto. | texto | ↑ | no |
| `ReturnDDRatio` | Ret/DD Ratio | Retorno dividido por drawdown. | ratio | ↑ | sí |
| `ReturnOpenDDRatio` | Ret/OpenDD Ratio | Retorno dividido por el drawdown abierto. | ratio | ↑ | sí |
| `SQN` | SQN | System Quality Number de Van Tharp. | ratio | ↑ | sí |
| `SQNScore` | SQN Score | SQN ponderado por el número de operaciones. | ratio | ↑ | sí |
| `SharpeRatio` | Sharpe Ratio | Ratio de Sharpe anualizado. | ratio | ↑ | sí |
| `SlippageInMoney` | Slippage ($) | Deslizamiento total pagado, en divisa de la cuenta. | € | ↑ | no |
| `SlopeRatio` | Slope Ratio | Pendiente fuera de muestra dividida por la pendiente en muestra (beneficio medio por operación OOS frente a IS). Columna propia. | ratio | ↑ | sí |
| `SortinoRatio` | Sortino Ratio | Ratio de Sortino: como el Sharpe pero castigando solo la volatilidad a la baja. | — | — | sí |
| `Stability` | Stability | Lo recta Y lo empinada que es la curva de equity, en una sola cifra. | ratio | ↑ | sí |
| `StabilitySQ3` | Stability SQ3 | La misma estabilidad calculada como la calculaba StrategyQuant 3. | ratio | ↑ | sí |
| `Stagnation` | Stagnation | Días que la equity pasó estancada sin hacer nuevo máximo. | entero | ↓ | sí |
| `StagnationPct` | % Stagnation | El estancamiento como porcentaje de los días totales. | % | ↓ | sí |
| `StandardDev` | StandardDev | Desviación típica del P&L de las operaciones. | ratio | ↓ | sí |
| `Symbol` | Symbol | Símbolo sobre el que se hizo el test. Texto. | texto | ↓ | no |
| `Symmetry` | Symmetry | Simetría del beneficio entre el lado largo y el corto. | % | ↑ | no |
| `TRLRatio` | TRL Ratio | Operaciones reales divididas por el mínimo de operaciones necesarias para afirmar con 95 % de confianza que el Sharpe es mayor que cero. Columna propia. | ratio | ↑ | sí |
| `TSIndex` | TS Index | Índice TradeStation. | ratio | ↑ | sí |
| `TSWinLossRatio` | TS Win/Loss ratio | Ratio ganadoras/perdedoras en la definición de TradeStation. | ratio | ↑ | sí |
| `TimeFrame` | TimeFrame | Timeframe del test. Texto. | texto | ↑ | no |
| `TotalDataDays` | Total Data Days | Días que abarcan los datos. | entero | ↓ | sí |
| `TotalDataMonths` | Total Data Months | Meses que abarcan los datos. | entero | ↓ | sí |
| `TotalDataYears` | Total Data Years | Años que abarcan los datos. | entero | ↓ | sí |
| `TotalMFE` | Total MFE | Suma del MFE de todas las operaciones: todo el movimiento favorable que hubo disponible. | € | ↓ | sí |
| `TotalTradingDays` | Total Trading Days | Días en los que hubo actividad. | entero | ↓ | sí |
| `TotalTradingMonths` | Total Trading Months | Meses en los que hubo actividad. | entero | ↓ | sí |
| `TotalTradingYears` | Total Trading Years | Años en los que hubo actividad. | entero | ↓ | sí |
| `TradesSymmetry` | Trades Symmetry | Simetría del NÚMERO de operaciones entre largos y cortos. | % | ↑ | no |
| `UlcerIndex` | Ulcer Index % | Ulcer Index: mide la profundidad y la duración de los drawdowns a la vez. | — | — | sí |
| `UlcerPerformanceIndex` | Ulcer Performance Index | Ulcer Performance Index anualizado: retorno por unidad de Ulcer Index. | ratio | ↑ | sí |
| `WinLossRatio` | Win/Loss ratio | Ganadoras dividido por perdedoras. | ratio | ↑ | sí |
| `WinningPct` | Winning Percent | Porcentaje de operaciones ganadoras. | % | ↑ | sí |
| `WorstParametersStability` | Worst Parameters Stability | La peor estabilidad de parámetros de todos los Walk Forward. Solo tiene valor si se corrió WF. | ratio | ↑ | no |
| `WorstYearProfit` | Worst Year Profit | Beneficio del peor año. | € | ↓ | sí |
| `ZProbability` | ZProbability | Probabilidad asociada al Z-Score: si las rachas son o no compatibles con el azar. | ratio | ↑ | sí |
| `ZScore` | ZScore | Z-Score de las rachas: mide si ganancias y pérdidas se agrupan más de lo que cabría esperar por azar. | ratio | ↑ | sí |

> **Aviso sobre `Outlier` y `Outlier2`:** SQX exporta las dos con la misma etiqueta, `Outlier1`. No
> es un fallo del exportador, es lo que trae la columna. Distínguelas por el nombre corto, nunca por
> la etiqueta.

### Las 21 que no aparecen por permutación

`AvgParametersStability`, `BacktestDuration`, `DateGenerated`, `DateLastModified`,
`EntryIndicators`, `ExitIndicators`, `FiltersResult`, `InitialDeposit`, `MagicNumber`,
`MiniEquityChart`, `Note`, `PriceIndicators`, `ResultsName`, `Symbol`, `TimeFrame`,
`WorstParametersStability` son metadatos o texto: describen la estrategia, no su resultado, así que
no cambian de una permutación a otra y SQX no los repite.

`NSymmetry`, `Symmetry`, `TradesSymmetry`, `NumberOfCanceled` y `SlippageInMoney` sí son numéricas y
sí tienen su hueco guardado — pero valen 0 en todas las estrategias de esta instalación, y por eso
quedaron entre las que no se pudieron nombrar (siguiente apartado). Están, no se sabe en qué hueco.

---

## 7. Lo que solo existe por permutación

Cuatro estadísticos aparecen en `permutations.csv` y no son columna de databank, así que no salen
en `metrics.csv`:

| campo | qué es |
|---|---|
| `DataLength` | número de barras que consumió el backtest de esa permutación |
| `MaxNewHighDurationFrom` | inicio del drawdown más largo, en **epoch de milisegundos** (`pd.to_datetime(v, unit="ms")`) |
| `MaxNewHighDurationTo` | fin de ese mismo drawdown, mismo formato |
| `MaxNewHighDurationPct` | ese drawdown como porcentaje del periodo total |

Y dos más llevan interrogación —`AnnualPctReturnDDRatio?` y `CalmarRatio?`— por el motivo del
apartado siguiente.

---

## 8. Lo que no tiene nombre, y por qué

SQX no guarda los nombres: guarda un hash del nombre de la clase (en la tabla de métricas) o la
posición en un array (en los estadísticos por permutación). El hash es `SQUtils.betterHashCode`, que
vive en un jar embebido en el ejecutable y no está en disco, así que no se puede deshacer.

Los nombres de esta página se reconstruyeron **cruzando valores**: exportando las 135 columnas de un
databank para 50 estrategias y viendo qué valor coincidía con cuál. Lo que no se pudo distinguir es
lo que vale lo mismo en todas partes.

| grupo | cuántos | qué son |
|---|---|---|
| verificados uno a uno | 101 de 135 métricas | nombre seguro |
| identificados hasta la pareja | 6 métricas | `Exposure?` / `ExposurePosition?`, `Outlier?` / `Outlier2?`, `CalmarRatio?` / `AnnualPctReturnDDRatio?`. Sabes de qué pareja es la columna, no cuál de las dos. Sus dos miembros valen lo mismo en los 225 perfiles de esta máquina |
| sin nombre, en `metrics.csv` | 28 métricas | salen como `id:<número>`. **Valen 0 en todas las estrategias de esta instalación** — que es justo por lo que no hubo con qué distinguirlas, y también por lo que no aportan nada |
| sin nombre, en `permutations.csv` | 34 estadísticos | salen como `stat:<tipo>:<índice>`, mismo motivo. `f` es un flotante, `i` un entero, `l` un long |

Los identificadores concretos, por si algún día aparecen con valor distinto de cero y se pueden
nombrar:

**Métricas sin nombre (`metrics.csv`)**

`id:-1032057831`  `id:-1401870665`  `id:-1558884181`  `id:-1679613218`  
`id:-1783525730`  `id:-1792934761`  `id:-1832811737`  `id:-184077012`  
`id:-1925735574`  `id:-2028835157`  `id:-2090795189`  `id:-2100959438`  
`id:-222360201`  `id:-301431951`  `id:-652428356`  `id:-833100900`  
`id:1041921791`  `id:1775062197`  `id:1876603141`  `id:1945540697`  
`id:195695425`  `id:2059656148`  `id:2133209636`  `id:40355801`  
`id:437767648`  `id:500275187`  `id:568822547`  `id:982587326`  

**Estadísticos sin nombre (`permutations.csv`)**

`stat:f:36`  `stat:f:47`  `stat:f:50`  `stat:f:53`  `stat:f:54`  `stat:f:55`  
`stat:f:58`  `stat:f:6`  `stat:f:62`  `stat:f:63`  `stat:f:64`  `stat:f:65`  
`stat:f:66`  `stat:f:67`  `stat:f:68`  `stat:f:69`  `stat:f:70`  `stat:f:71`  
`stat:f:72`  `stat:f:73`  `stat:f:74`  `stat:f:75`  `stat:f:76`  `stat:f:77`  
`stat:f:78`  `stat:f:83`  `stat:f:84`  `stat:f:88`  `stat:f:89`  `stat:i:7`  
`stat:l:0`  `stat:l:1`  `stat:l:2`  `stat:l:3`  

---

## 9. Lo que se extrae de la misma estrategia sin ser del SPP

### `trades/<estrategia>.csv` — las operaciones del backtest principal

Son las que sí existen. 16 columnas, tal y como las escribe `orderstocsv`:

| campo | qué es |
|---|---|
| `Ticket` | número de operación, empieza en 1 |
| `Symbol` | símbolo. Si el fichero trae varios mercados, **esta columna es el separador** |
| `Type` | `Buy` o `Sell` |
| `Open time` | fecha y hora de entrada |
| `Open price` | precio de entrada |
| `Size` | tamaño en lotes. **Varía operación a operación** porque el sizing es por riesgo |
| `Close time` | fecha y hora de salida |
| `Close price` | precio de salida |
| `Profit/Loss` | resultado en divisa de la cuenta, ya con costes dentro |
| `Balance` | balance acumulado después de esta operación |
| `Sample type` | `IST` en muestra, `OOS1` fuera. **No siempre está bien**: depende de cómo se retesteó la estrategia por última vez |
| `Close type` | por qué se cerró: `Exit Signal`, `Exit After X Bars`, `End Of Friday (Time)`, `EndTest`... |
| `MAE ($)` | máxima excursión adversa, **en divisa de la cuenta, no en puntos** |
| `MFE ($)` | máxima excursión favorable, ídem |
| `Time in trade` | duración en texto (`2h 0m`) |
| `Comment` | comentario de la orden |

La última fila puede ser una orden pendiente que nunca se ejecutó (`Close type=EndTest`, con precio
de cierre vacío). Se tira.

### `bars/bars_<TF>.csv` — las velas

`Date`, `Time`, `Open`, `High`, `Low`, `Close`, `Volume`. Es el fichero contra el que se reconcilian
los precios de las operaciones.

### Y del `.sqx`, sin exportar nada

| qué | cómo |
|---|---|
| las métricas guardadas por muestra (IS / OOS / periodo completo) | `core.sqxstats.stats()` |
| la curva de equity diaria, un punto por día natural | `core.sqxstats.equity()` |
| el perfil SPP entero | `core.optprofile.read()` |
| símbolo, timeframe, hash de identidad, parámetros | `core.sqxfile` |

---

## 10. Lo que no existe, por mucho que se busque

**Los trades de las permutaciones.** No es que falte el comando. Cada permutación se guarda como su
cadena de parámetros más un bloque `SQStats`, y ese bloque solo admite seis tipos de registro —
entero, long y flotante, cada uno con índice o con nombre — y nada más. La clase tiene un campo para
objetos, pero el serializador no lo escribe nunca. No hay ninguna ruta por la que una lista de
órdenes llegue al fichero.

**La equity de cada permutación.** Mismo motivo: `dailyEquity.bin` solo existe para el resultado
principal.

**Un percentil distinto de la mediana, si la casilla 3D estaba puesta.** Con el detalle tirado solo
quedan medianas e histogramas de 20 bins. Con el detalle guardado se puede pedir cualquier cosa.
