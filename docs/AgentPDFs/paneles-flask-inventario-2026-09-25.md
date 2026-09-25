# Los tres paneles Flask — inventario de lo que ofrecen, para trasplantarlo a la ventana

**Qué es.** Un inventario, no un juicio. Los paneles de `portfolio/common/monteCarlo/explorer/`,
`studies/breakage/mcRetest/explorer/` y `studies/transfer/crossmarket/explorer/` están «mal» por su forma —tres
aplicaciones en el navegador, tres puertos, sin memoria compartida— y el dueño lo sabe. Lo que
quiere que se conserve es **su profundidad**: elegir estrategia, configurar cada test, ver todos
los resultados y todos los dibujos, en muchas pestañas. Este documento lista eso, panel por
panel, para que la zona «Estudios» de la ventana lo reproduzca y no lo empobrezca. Escrito el
2026-09-25 leyendo el código y los README, sin correr ninguno.

**La regla que ya cumplen los tres y que la ventana hereda:** cada sección es una función de
`render/` que devuelve HTML con SVG escrito a mano, y el informe por lotes escribe byte a byte lo
mismo que el panel. **Ningún panel calcula nada**; mira. QtWebEngine está disponible en esta
máquina, así que ese HTML puede pintarse dentro de la ventana tal cual.

---

## Lo que los tres tienen en común — el esqueleto de cualquier zona de estudio

| pieza | qué hace | hoy |
|---|---|---|
| **selector de estrategia** | un desplegable con todas las del export; marca las ya analizadas (`· analizada`, `*`) | los tres |
| **botón por estrategia** y **botón para todas** | analizar una en profundidad, o el databank entero en cola | MC, retest |
| **cajón de configuración** | TODOS los mandos de `config.yaml` del módulo, agrupados por sección, con una frase por mando al pasar el ratón (`tooltips.py`), botón «restablecer valores de fábrica». Cambia **la próxima ejecución**, nunca el fichero | los tres (46, 18 y 51 mandos) |
| **un trabajo a la vez** | el segundo se rechaza; el botón se desactiva; progreso continuo con la línea de «qué está corriendo ahora» | los tres |
| **pestañas** | una por pregunta; la primera es la que abre | 7, 5 y 12 |
| **botón de informe** | escribe la página del lote, idéntica a lo que se ve | MC, retest |
| **estado de frescura** | un resultado guardado bajo otra configuración se declara caducado en rojo, nunca se reutiliza en silencio | MC |
| **error visible** | un fallo sale en la página, no en un log que nadie tiene abierto | los tres |

Tres decisiones distintas sobre memoria, cada una razonada: MC cachea en disco con huella de la
configuración (medio minuto de 96 núcleos por estrategia); retest guarda en memoria (un segundo por
estrategia); cross-market no guarda nada (decisión 2026-09-15, revertida en parte el 09-24 por
`report.py`). La ventana tendrá que elegir una política, y la huella de configuración de MC es la
única que impide leer un número como respuesta a una pregunta que no se hizo.

---

## 1 · Monte Carlo de operaciones — «cuánto de esto es suerte»

`python3 -m portfolio.common.monteCarlo.explorer.serve --project P --databank D --asset A --export FECHA`

**Pestañas (7):** Veredicto · Familia A · B · C · D · E · Explorador de pruebas.

**Las cinco familias de suerte**, cada una con su pregunta y sus dibujos:

| familia | la suerte que aísla | la pregunta | qué dibuja |
|---|---|---|---|
| **A · orden** | la secuencia en que llegaron las operaciones | mismas operaciones, otro orden: ¿cuánto peor pudo ser el drawdown? | cono de equity con la real encima; reordenación por bloques (`block_min`, `min_blocks`, `n_block_sizes`) |
| **B · composición** | qué operaciones ocurrieron | remuestrear: ¿lo sostienen un puñado? | comparación de nivel IS/OOS (`oos_amber_frac`, `oos_red_frac`), pérdida al quitar la mejor (`outlier_frac`) |
| **C · ejecución** | cómo se llenaron y cobraron | peores fills, más coste, entradas perdidas: ¿cuánto filo sobrevive? | cuatro estreses contra sus suelos: `p_skip`, `cost_shock_range`, `fill_frac`/`fill_depth`, `spread_scale` |
| **D · régimen** | cuándo y en qué estado de mercado vivió | ¿estaba el filo en cada ventana y cada tercil de volatilidad, o en uno? | ventanas móviles (`window_months`, `window_step_months`, `window_pass_frac`), terciles por ATR o GARCH (`vol_model`), dos series temporales, cosido de malos tramos (`stitch_quantiles`) |
| **E · significancia** | la muestra misma | dado N y la forma de los retornos, ¿el filo verdadero podría ser cero? | PSR contra `psr_benchmark`, con su cross-check bootstrap |

**Veredicto:** compuesto con pesos por familia (`scoring.weights`), tres tiers (`tiers: [80, 65,
50]`), banderas de inflación de drawdown (`dd_inflation_flag`, `_watch`), suelo de PF, y una
prueba de **estabilidad** (`n_stability_runs`, `stability_tol`): repetir el análisis y ver si el
percentil que decide se mueve.

**Explorador de pruebas** — la parte más «profunda»: elegir **cualquier subprueba de cualquier
familia** y **cualquier métrica** (beneficio neto, DD %, DD $, Ret/DD, Sharpe, PF, racha perdedora,
retorno) y ver su distribución con la real marcada, el percentil de comparación (`report_percentile`)
y el conjunto de percentiles (`percentile_set`). Botón **«Re-ejecutar esta prueba»**: corre esa
subprueba otra vez y la muestra AL LADO de la guardada, marcada como re-ejecución, con una casilla
para ver una u otra. Nunca sobrescribe ni mueve el veredicto: «un veredicto sale de un análisis
entero o de ninguno».

**Mandos del cajón (46):** capital, riesgo por operación, `n_sims` (100.000), paralelismo
(`chunk`, `tile_bytes`, `max_workers`) y todos los de arriba.

---

## 2 · MC Retest — «qué la rompe», leyendo las ocho tareas de SQX

`python3 -m studies.breakage.mcRetest.explorer.serve --project P`

**Pestañas (5):** Veredicto · Qué la rompe · Estrés combinado · Las ocho tareas · Tabla de confianza.

- **Veredicto:** compuesto por grupos de tarea (`production`, `execution`, `specification`,
  `data`, con pesos), tiers STRONG / ACCEPTABLE / MARGINAL, y las puertas (`min_pf` al p5 de la tarea
  de producción, `survival_dd_pct` como CVaR, `collapse_frac` de operaciones, `exec_keep_frac` de
  beneficio bajo la peor ejecución, `psr_gate`).
- **Qué la rompe:** atribución de efectos entre tareas **en unidades de la dispersión de la tarea
  de control** (`bar`, la reordenación de barra de inicio), Brown-Forsythe centrado en mediana,
  y un umbral de ruido (`min_control_sigma`).
- **Estrés combinado:** el abanico de equity (`band_levels`, `fan_points`), la cola del drawdown
  como media condicional (`cvar_alpha`), intervalos BCa (`n_resamples`, `confidence`).
- **Las ocho tareas:** cada perturbación por separado (barra de inicio, spread, slippage,
  skip de operaciones, histórico, precio, parámetros, MinDistance), con sus cuantiles de SQX
  y la reconciliación métrica a métrica (`recon.tolerance`) contra lo que SQX dice.
- **Tabla de confianza:** los once niveles que SQX produce (50…100), con la métrica que ordena
  las simulaciones (`ordering_metric`) y los niveles destacados (`show_levels`).
- **Evidencia:** corrección por multiplicidad Benjamini-Yekutieli (`evidence.method`, `alpha`),
  Kendall tau entre rankings solo con ≥ 20 estrategias.

**Lo que enseña el README:** solo 30 de las 148 métricas son reconstruibles por simulación; sin
p-valores donde el tamaño de muestra es un mando. Sin caché a propósito: la parte cara ya pasó en
`ingest`.

---

## 3 · Cross-market — «¿transfiere el filo?», una estrategia sobre cada mercado

`python3 -m studies.transfer.crossmarket.explorer.serve --project P --databank "Retest Markets - Family" --asset A --export FECHA`

**Dos botones de correr:** «Run analysis» (todos los mercados, todos los modelos, todos los tests)
y **«run» al lado de cada mercado** en la lista, que corre solo ese con lo que diga el cajón en
ese momento y **se fusiona** con lo ya calculado (re-correr un mercado a 50.000 corridas no tira
los demás). Un mercado en el que la estrategia nunca operó sale en gris como `sin operaciones`,
sin botón: la ausencia es un resultado.

**Pestañas (12), y qué hay dentro:**

| pestaña | qué enseña |
|---|---|
| **Backtest** (abre primero) | cada mercado real **a riesgo igual** (`risk_target_dd`), sus curvas de equity, y qué sostiene los números; absorbió Resumen, Significancia y Correlación |
| **Entrada aleatoria (1a)** | por mercado: cono de equity con la real encima, y un histograma por estadístico (neto, Ret/DD, DD, Sharpe, PF) con mediana simulada, banda p5–p95 y valor real, sobre la tabla completa de percentiles. **Tres selectores**: mercado × modelo nulo × estadístico; cambiar uno no recalcula nada |
| **Entrada aleatoria · OOS principal** | la misma prueba sobre el tramo fuera de muestra del propio activo (`assets/_markets.yaml`), aparte a propósito, y la advertencia de que ese tramo no es virgen |
| **Modelos** | comparación de los cuatro modelos nulos (`segment_permute`, `resampled_holds`, `fitted_holds`, `block_shift`) para un estadístico, con desplegable |
| **Barrido de ventana** | rejilla mercados × tamaños de bloque (`full`, 3y, 1y, 6m) con la p y la tendencia en cada celda; al pulsar una fila, ese mercado debajo: tres modelos en una curva de p con el de referencia plano, tabla de potencia, un histograma por tamaño, cono del tamaño elegido, y los bloques. Chips de modelo y desplegable de estadístico |
| **Pareado (1b)** | las operaciones contra un largo pasivo en las mismas barras, unilateral, con **sensibilidad** a la ventana de referencia (3, 6, 12 meses, bloque) todas a la vez |
| **Exposición (1c)** | captura del recorrido a favor, intervalo de Fieller por bootstrap por bloques de barras |
| **Coste y ejecución** | el estrés de bróker por mercado: múltiplos de coste, desplazamiento de barra, fracciones de slippage, skip, con los supuestos nombrados por mercado y calibrados desde `execution.yaml` |
| **Huella** | la firma de la estrategia: horas, duraciones, lo que la identifica |
| **Portfolio** | la cuenta combinada de todos los mercados, qué aporta o quita cada uno, y dos formas de preguntar cuánto es suerte (remuestreo por bloques de calendario y reordenación) |
| **Avisos** | las nueve advertencias diagnósticas por mercado (`min_trades`, `min_on_open`, `fill_tolerance`, `max_fill_error`, `min_on_grid`, `selected_window`…): colorean, **no eliminan nunca** |
| **Glosario** | cada término con su frase |

No hay pestaña de veredicto **porque no hay veredicto**: el panel describe. El veredicto de
población llegó después por `report.py` (OPEN.md §36).

**Mandos del cajón (51):** corridas por mercado y modelo (`draws`, 25.000), semilla compartida,
bloques de régimen, modelo titular, todos los del barrido, el nulo conjunto (`pool`), estratos
ATR/tendencia, la cuenta y sus bandas, bootstrap, exposición, pareado, portfolio, estrés y
diagnósticos.

---

## Lo que la zona «Estudios» de la ventana tiene que conservar, en una lista

1. **Una estrategia elegida una vez, compartida por todos los estudios** — es el motivo del demonio.
2. **El cajón de configuración completo por módulo**, con la frase de cada mando, que afecta a la
   siguiente ejecución y nunca al fichero; y que lo ejecutado quede firmado con su configuración.
3. **Selectores que no recalculan**: mercado × modelo × estadístico, tamaño de bloque, métrica del
   explorador. Un resultado guarda todas las distribuciones; cambiar el selector solo redibuja.
4. **La distribución con la real marcada** como dibujo base de todo: histograma, mediana, banda,
   valor real, percentil de comparación, y la tabla de percentiles debajo.
5. **El cono de equity con la real encima**, en A, en 1a, en el estrés y en el portfolio.
6. **Re-ejecutar una sola subprueba y verla al lado**, sin tocar el veredicto.
7. **Correr un mercado suelto y fusionar**, y mostrar la ausencia como resultado.
8. **Los avisos que colorean y no eliminan**, y el glosario, en la misma vista.
9. **Un trabajo a la vez con progreso continuo** y el error en pantalla.
10. **El botón de informe** que escribe lo mismo que se ve.

Y lo que puede cambiar sin perder nada: el navegador, los tres puertos, las tres copias de
`jobs.py`/`scope.py`/`tooltips.py`, y las tres políticas de memoria, que pasan a ser una.
