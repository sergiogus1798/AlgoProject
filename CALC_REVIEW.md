# CALC_REVIEW — revisión de corrección del código numérico

Fuentes: `scratch/cleanup/calc-engines.md`, `calc-studies-a.md`, `calc-studies-b.md`, `calc-portfolio.md` (fecha 2026-10-04); sondas (scripts desechables) en `scratch/cleanup/`: `calc_engines_probe.py`, `calc_a_real.py`, `calc_a_edgecost.py`, `calc_a_bh.py`, `calc_a_known.py`, `calcb_wfm.py`, `calcb_cloud.py`, `calcb_spp.py`, `calcb_mcr.py`, `calcb_transfer.py`, `calc_portfolio_probe.py`.

**Esta revisión no cambió ningún código**: es solo lectura (nada en el proyecto ni en AlgoData se modificó).

## Resumen

Recuento tras fusionar duplicados exactos (el defecto «el máximo drawdown ignora el balance inicial» aparece en tres informes y queda en un solo hallazgo, m1):

| Severidad | Hallazgos | Confirmado con experimento | Confirmado leyendo | Sospecha |
|---|---|---|---|---|
| CRÍTICO | 3 | 3 | 0 | 0 |
| MAYOR | 9 | 9 | 0 | 0 |
| MENOR | 36 | 20 | 4 | 12 |
| **Total** | **48** | **32** | **4** | **12** |

Notas sobre el recuento: (a) el recuento por estados es el de las etiquetas de cada hallazgo; los informes originales traen totales propios algo distintos (p. ej. `calc-portfolio.md` dice «5 confirmed, 5 suspected» pero etiqueta 6 confirmados y 4 sospechosos; `calc-studies-b.md` dice 14 por experimento y 3 por lectura o sospecha, pero etiqueta 4 por lectura/grep y 2 sospechosos). (b) Cada informe contaba por separado: engines 0 CRÍTICO · 2 MAYOR · 9 MENOR; studies-a 0 · 2 · 10; studies-b 2 · 2 · 13; portfolio 1 · 3 · 6; suma 3 · 9 · 38; menos 2 duplicados fusionados (T1 y el hallazgo 5 de portfolio dentro de m1) = 3 · 9 · 36. (c) En M1 la corrección del motor está confirmada; solo la alcanzabilidad desde `correlations.py` es sospecha. (d) Dos notas no contadas: la sospecha relacionada de M2 (N cuenta una repetición de la misma criba, decisión del dueño) y la nota fuera de alcance al final de «Menores».

Titulares:

- **C1 — mcRetest: el PSR se calcula sobre un total por simulación, no sobre las operaciones.** Con 1.000 simulaciones el PSR satura a 1.0000 / 0.0000 y el veto `edge_indistinguible_de_cero` no puede dispararse; 4.18.70 (PSR por operación 0.78, 27,5 % de sus runs estresados pierden) pasa.
- **C2 — SPP: la puerta de ruido compara el máximo sin centrar con σ·√(2 ln N) y no tiene suelo de operaciones.** Veredicto «proceed» en 41 de 41 estrategias reales; centrado, unas 14 leerían «noise» (decisión del dueño).
- **C3 — fondeo: un límite de pérdida diaria de 0 («la regla no existe») se simula como «ningún bajón intradía permitido».** Afecta hoy a 4 filas reales (`fundednext:stellar-instant:{2000,5000,10000,20000}:USD`, etapa `funded`); los planes instant salen con EV ≈ −precio por construcción.
- **M7 / M8 / M9 — búsqueda genética envenenada por NaN, tramo arrastrado que separa balance y equity, `spread_widen` que carga el spread entero otra vez.** Los tres confirmados con experimento; los dos primeros pegan justo en los planes pequeños (2.000-5.000 USD).
- **m1 — el máximo drawdown nunca cuenta la caída desde el balance inicial** (motores de nulos, crossmarket, Monte Carlo de operaciones): cifras mostradas sesgadas a la baja; el p apenas se mueve porque real y nulos comparten la convención.
- **Sharpe anualizado con 252 sobre series que no son de 252 filas/año** — hay dos defectos distintos con números distintos y los mantengo separados: M5 (SPP `combinado`, días naturales, ×0,845) y m11 (series de ~260,6 filas/año, ×0,983). Ver también m17 (wfm, cierres de fin de semana).
- **Pregunta del dueño sobre el factor 10 en los spreads: NO se encontró.** Evidencia (`calc-studies-a.md`, «Checked and correct»): todo spread de SQX está en unidades de `instrument.tick_size` en `measure.yearly` (`spread_open / tick`), `verdict.propose`, `onboard.plan`, `inputs._task_costs` (`spread × tick`) y `edgeCost/costs.py:93`; contrastado con fills reales: AUDJPY, spread de tarea 1,61 puntos × 0,01 = 0,0161, slippage 0,0081, y el offset de entrada medido de un long es 0,0240 = 0,0161 + 0,0081 a la fracción de pip; USDJPY `spread_is` 0,49 puntos = 0,49 pip. `calc-portfolio.md` confirma coste por operación = spread + 2 × slippage (puntos × tick) + comisión ida y vuelta en `marketProfile`. **Módulos de spread/feedQuality NO leídos línea a línea:** feedQuality `calibrate.py`, `inject.py`, `feed.py`, `scan.py`, `one.py`, `many.py`; spread `asset.py`, `band.py`, `bands.py`, `registry.py`, `one.py`, `report.py`. Test propuesto para cerrar la puerta: `_task_costs` con spread 1,61 puntos × tick 0,01 → 0,0161 en precio (tabla, fila «Reprecio del spread»).
- Motores: ninguna fórmula de las estadísticas de cabecera (PSR, MinTRL, DSR, BH, p empírico +1, SPA/StepM, generadores de bloques, ATR de SQX) está mal con entrada bien formada; lo malo está en los bordes (NaN que falla abierto, dos off-by-one, un look-ahead, una columna del ledger que acepta puntuaciones que no son Sharpe).

Etiquetas: «(decisión del dueño)» = las fuentes dicen que necesita su criterio; «(sesión de spread)» = vive en `studies/data/spread/` o `assets/`.

## Críticos

### C1 — mcRetest: el PSR se calcula sobre un total por simulación, no sobre las operaciones

- **Dónde:** `studies/breakage/mcRetest/run.py:129-130`; consumido por `studies/breakage/mcRetest/verdict/gates.py:64`; contrato en `studies/breakage/mcRetest/verdict/evidence.py:69-85`.
- **Qué pasa:** `evidence.analytic_sharpe(pnl.groupby("sim")["pnl"].sum().to_numpy(), benchmark)` entrega a `core.significance.psr` el NET PROFIT de cada simulación de la tarea de estrés (unos 1.000 valores), mientras que la docstring de la función y el README del veredicto dicen «el P/L por operación del backtest original», y `benchmark` es un Sharpe por operación. La media/sd de 1.000 totales de simulación es otra cantidad con n = 1.000, así que el PSR satura a 1.0000 o 0.0000 y deja de medir nada. El veto `edge_indistinguible_de_cero` necesita `p_positive < psr_gate and psr < psr_gate` (0.90); con el PSR clavado en 1.0 no puede dispararse para ninguna estrategia cuyas simulaciones sean en media positivas.
- **Estado:** confirmado con experimento. Sintético (1.000 runs × 500 operaciones, N(2, 100)): PSR por operación 0.440; como está codificado «sharpe» 0.480, n = 1.000, PSR 1.000000. Real, `Test_XAUUSD_donchianUpperCrossUp_H1/MCR_All/2026-10-01`:

  | estrategia | PSR como está codificado | PSR por operación de los re-runs (mediana / p5) | sims con net <= 0 |
  |---|---|---|---|
  | 20.25.72 | 1.0000 | 0.935 / 0.350 | 4.6 % |
  | 3.21.83 | 0.0000 | 0.231 / — | 82.2 % |
  | 4.18.70 | 1.0000 | 0.780 / 0.160 | 27.5 % |
  | 4.19.71 | 1.0000 | 0.848 / — | 15.7 % |
  | 9.10.57 | 1.0000 | 0.922 / — | 2.5 % |
- **A quién afecta:** estudio mcRetest (paso 13), su verdict/gates y el veto `edge_indistinguible_de_cero`. 4.18.70 (PSR por operación 0.78, 27,5 % de sus runs estresados pierden) pasa.
- **Cómo verificarlo:** `PYTHONPATH=. python3 scratch/cleanup/calcb_mcr.py`.
- **Corrección propuesta:** pasar a `analytic_sharpe` el P/L por operación del backtest ORIGINAL (el store ya carga los originales); conservar los totales por simulación solo para `p_positive`.
- **Test de regresión:** 500 operaciones N(2, 100), semilla fija, benchmark 0 → `analytic_sharpe(...)["psr"]` a ±0.02 del PSR de forma cerrada (≈ 0.67 para SR 0.02, n 500), y en particular `< 0.99`. (Tabla de tests, fila 1: igual a `core.significance.psr` de esas operaciones ±1e-9.)

### C2 — SPP: la puerta de ruido compara un máximo sin centrar con σ·√(2 ln N) y no tiene suelo de operaciones (decisión del dueño)

- **Dónde:** `studies/breakage/spp/verdict/noise.py:32-39`; `core/surface/plateau.py:41-54` (`expected_max`); rejilla montada en `studies/breakage/spp/run.py:42`.
- **Qué pasa:** la nula se enuncia «ningún parámetro hace nada»; bajo ella el máximo de la rejilla es ≈ `media + σ·√(2 ln N_eff)`. El código compara el `observed_max` CRUDO con `σ·√(2 ln N_eff)`: nunca resta la media. Para toda estrategia con media de rejilla positiva (todas: fueron seleccionadas) la puerta la supera solo la media. Además el máximo se toma sobre tuplas con cualquier número de operaciones, así que una tupla de 4 operaciones con un drawdown de 4 $ lo fija.
- **Estado:** confirmado con experimento, sobre 41 estrategias reales (XAUUSD H1 2026-10-01, USDJPY H1 2026-09-30, USDJPY M30 2026-09-29, `SPP_IS`). Veredicto como está: «proceed» 41 de 41. Centrado, `(max − mean)/sigma` frente a `√(2 ln N)`: unas 14 leerían «noise» — p. ej. XAUUSD 4.18.70 4.00 vs 4.25, 4.19.71 3.58 vs 4.25; USDJPY H1 10.1.79 3.65 vs 4.22, 15.9.45 3.49 vs 4.22, 22.11.70 3.57 vs 4.26. Suelo de operaciones: en 7 de 41 la tupla argmax tiene menos de 20 operaciones. XAUUSD 3.21.83: 4 operaciones, Ret/DD 16.9, frente a 2.41 entre tuplas con ≥ 100 operaciones; USDJPY 1.26.74: 5 operaciones, 19.8 frente a 1.63; 1.27.61: 13 operaciones, 19.9 frente a 1.44. Matiz de severidad (CRÍTICO con salvedad): cambia el veredicto de ruido en cerca de un tercio de la población, pero **si centrar es la nula pretendida es decisión del dueño** — la docstring dice que sí.
- **A quién afecta:** estudio SPP (paso 15), veredicto de ruido; el SPP alimenta la lectura de plateau.
- **Cómo verificarlo:** `PYTHONPATH=. python3 scratch/cleanup/calcb_spp.py`.
- **Corrección propuesta:** comparar `observed_max − mean` con el exceso esperado, y tomar el máximo sobre tuplas por encima del suelo de operaciones del propio estudio.
- **Test de regresión:** 10.000 valores iid N(5, 1) sin estructura → `"noise"` (hoy: «proceed», porque max ≈ 8.7 > 1·√(2 ln 10.000) = 4.29). Tabla de tests: más una cresta de 3 sigma con 200 vecinos → «proceed».

### C3 — fondeo: un límite de pérdida diaria de 0 se simula como «ningún bajón intradía permitido»

- **Dónde:** `portfolio/funded/rules/catalog.py:152` (`"daily_loss": (daily_loss_pct or 0) / 100`), consumido por `portfolio/funded/rules/floors.py:20-22` y todo caminante que lo llama (`rules/machine.py:54,159`, `sim/account.py:42`, `sim/kernel.py`, `construct/mc/judge.py`, `construct/search/stagea.py`).
- **Qué pasa:** `catalog/README.md:36` dice que 0 significa «la regla no existe» y NULL «aún no se sabe». Con `pct = 0` el suelo pasa a ser `b0` (base FTMO) o `max(b0, e0)` (el resto de firmas), así que la cuenta falla `daily_loss` el primer día en que su equity está un céntimo bajo el inicio del día. NULL se mapea al mismo 0, de modo que «desconocido» también se convierte en «muerte instantánea» en vez de en una negativa. `(max_loss_pct or 0)` tiene el mismo defecto (suelo estático = `size`), aunque hoy `max_loss_pct` nunca es 0/NULL.
- **Estado:** confirmado con experimento. Plan real `fundednext:stellar-instant:5000:USD`, 30 días de +20 USD cerrados, mínimo intradía −1 USD → `{'end': 0, 'rule': 'daily_loss', 'payouts': []}`. Mismo camino con la regla diaria neutralizada: viva, dos payouts de 280. Exposición viva: 4 filas actuales en `AlgoData/funding/funding.sqlite` — `fundednext:stellar-instant:{2000,5000,10000,20000}:USD`, etapa `funded`, `daily_loss_pct = 0`, pérdida máxima 6 % trailing; ninguna fila actual tiene NULL.
- **A quién afecta:** simulación del banco de fondeo y búsqueda de carteras (rules, sim, construct stage A, mc/judge). El EV del plan ≈ −precio para cualquier estrategia con un bajón intradía: los planes instant se puntúan como inútiles por construcción.
- **Cómo verificarlo:** sonda §6 de `calc_portfolio_probe.py`; o `python3 -m portfolio.funded.catalog.show fundednext:stellar-instant:5000:USD` y mirar la etapa funded.
- **Corrección propuesta:** en `floors.daily_floor`, `if pct <= 0: return -np.inf`; misma guarda en `max_floor`; reflejarla en los tres kernels numba. En `catalog.plan`, lanzar excepción ante NULL (como ya hace `days_ok` con un `min_days` desconocido) en vez de `or 0`.
- **Test de regresión:** `tests/test_funded_rules.py`: `_stage(daily_loss=0.0, daily_basis="max_be")`, un día con `low = -1` → el resultado no es `fail`; igual para `"balance"`; kernel igual a la referencia. Exacto.

## Mayores

### M1 — `fdr`: un p-valor NaN se nombra descubrimiento y arrastra a otros

- **Dónde:** `engines/inference/fdr.py:16-18` y `:31-35`.
- **Qué pasa:** ambas funciones hacen `sorted(rows, key=p)`. NaN compara False con todo, así que el orden queda indefinido a su alrededor y `r["p"] <= i/n*alpha` se evalúa sobre una lista mal ordenada; `adjusted` propaga `min(q, nan*…)` igual. Nada filtra ni rechaza un NaN.
- **Estado:** confirmado con experimento. Filas p = {a: 0.04, nan: NaN, b: 0.001, c: 0.9, d: 0.002}, alpha 0.05: `discoveries` → `['a', 'b', 'd', 'nan']`; sin la fila NaN → `['b', 'd']`. `adjusted` da a `a` y a `nan` q = 0.00167 (la q verdadera de a entre los cuatro tests finitos es 0.04·4/3 = 0.0533). La alcanzabilidad es sospecha: `studies/screening/analysis/correlations.py:18-21` alimenta `scipy.stats.spearmanr(x, y).pvalue`, NaN cuando una columna es constante (comprobado: `spearmanr(zeros, arange)` → `nan nan`); `predictors()` (`:61`) pasa todas las métricas IS sin filtrar, y `sorted(rows, key=-abs(spearman))` tiene el mismo problema de orden con NaN. Que exista una columna IS constante en un export dado depende de los datos.
- **A quién afecta:** `studies/screening/isOos/many.py:30`, `studies/screening/filters/report.py:81`, `studies/research/marketProfile/many.py:47`, `studies/research/pooledProfile/many.py:50,88`. Nombres falsos en una tabla de tests múltiples.
- **Cómo verificarlo:** bloque `[I]` de `scratch/cleanup/calc_engines_probe.py`.
- **Corrección propuesta:** primera línea de ambas funciones: `if any(r["p"] != r["p"] for r in rows): raise ValueError("fdr: NaN p")`; o, si un NaN debe significar «no testable», quitar esas filas **y mantener `len(rows)` de las testables como tamaño de familia**, dicho en la docstring. Lanzar es el cambio más pequeño y casa con el estilo de la casa («rechazar antes que adivinar»).
- **Test de regresión:** las cinco filas de arriba → `discoveries == {"b", "d"}` tras quitar, o `ValueError`; más `adjusted(rows)` igual a `scipy.stats.false_discovery_control(p, method="bh")` a 1e-12 sobre 48 p aleatorios (esta segunda mitad pasa hoy: diferencia máx 2.2e-16).

### M2 — ledger: las columnas «Sharpe» aceptan cualquier puntuación, y una fila así desactiva o corrompe para siempre el Sharpe deflactado de un estudio

- **Dónde:** `ledger/record.py:15-30`, `ledger/trials.py:37-52`.
- **Qué pasa:** `record.distribution()` escribe lo que reciba en `sharpe_mean`, `sharpe_std`, `n_scored`. `portfolio/common/construct/search/trials.py:31,36,77` registra las **probabilidades de pase** de la búsqueda genética (`score_unit: "p_pass"`) y `portfolio/funded/sim/trials.py:25` un valor esperado en USD (`"ev_bank_usd"`) — y la búsqueda de construct escribe esa fila **en el estudio de cada estrategia miembro** (`:34-37`). `trials.accumulated()` agrupa toda fila con `n_scored`, sea cual sea su unidad, y solo se niega cuando conviven dos unidades. El ledger es solo-anexar, así que la negativa es permanente.
- **Estado:** confirmado con experimento. (a) filas per_period + p_pass → `ValueError: … mezclan unidades`; (b) un estudio cuya única fila puntuada es p_pass (n 5000, media 0.4, std 0.2) → `accumulated` devuelve `sigma = 0.2, unit "p_pass"`, y `ledger/report.py:100-107` lo imprime como benchmark de Sharpe por día (`expected_max_sharpe(0.2, 5000)` ≈ 0.72 por día, es decir 11 anualizado — todo DSR 0); (c) ya ocurre con otro par: `XAUUSD_M30_DirectionalMomentum` tiene `gate/presencia` (anualizado, σ 0.3506) y dos filas `snoopingScreen/stepm` (per_period, σ 0.0184); `trials.accumulated(study.read(...))` lanza hoy, así que `ledger.report`, la vista de ledger de la ventana (`ui/daemon/ops/ledgerview.py:55`, capturado) y `core/archive/manifest.py:76` (**no** capturado) no pueden contar ese estudio. `report.py:100` tiene una rama `annualised → /sqrt(252)` que la excepción vuelve inalcanzable justo en el caso para el que existe. Ningún ledger real lleva aún una fila p_pass (86 ledgers inspeccionados: 257 per_period, 1 annualised).
- **A quién afecta:** `ledger.report`, `core.archive.manifest.ledger`, la zona de ledger de la ventana y, a través de ellos, la lectura del paso 20 de «lo que cuesta toda la búsqueda al Sharpe».
- **Cómo verificarlo:** sonda de `calc_engines_probe.py` (casos a-c); `trials.accumulated(study.read(...))` sobre `XAUUSD_M30_DirectionalMomentum`.
- **Corrección propuesta:** en `accumulated`, agrupar solo filas cuya unidad sea un Sharpe (`{"per_period", "annualised"}`), convirtiendo `annualised` por `/sqrt(252)` allí y no en el informe; las filas de cualquier otra unidad siguen sumando su `n_scored` a N (son miradas) pero no a sigma. No requiere reescribir ninguna línea de ledger.
- **Test de regresión:** frame de tres filas — per_period (n 100, m 0.01, s 0.05), annualised (n 40, m 0.0, s 0.05·√252), p_pass (n 5000, m 0.4, s 0.2) → `sigma` igual a la std ddof=1 agrupada de las dos primeras en escala por periodo (la identidad de pooling exacto ya testada en `tests/test_ledger.py`), `n == 5140`, sin excepción; tolerancia 1e-9.
- **Relacionado, sospecha, menor, no contado aparte (decisión del dueño):** N cuenta otra vez una repetición de la misma criba: el estudio de arriba tiene los mismos 115 candidatos puntuados tres veces (N = 345); 251 filas `snoopingScreen/stepm` en 86 ledgers. Conservador (deflacta más) y «cada mirada cuenta» puede ser la intención, pero entonces sigma también queda re-ponderada hacia la criba más repetida. Llamada del dueño; decir cuál en `ledger/README.md`.

### M3 — edgeCost mide solo el lado de entrada: el spread de un short no está en su «spread ida y vuelta»

- **Dónde:** `studies/readings/edgeCost/spread_share.py:45-56`, consumido en `costs.py:89-92`.
- **Qué pasa:** `measure()` toma la mediana de `(Open price − bar Open) × direction` y la llama spread ida y vuelta. SQX cotiza al bid y pone el spread en el lado ask: un long lo paga a la entrada, un short a la salida (`studies/data/spread/reprice.py:3-5`, afirmación del propio repo), y cobra slippage en ambos fills. La cifra es, pues, *spread + slippage de entrada* para un long (falta el slippage de salida) y *solo slippage de entrada* para un short (falta todo el spread). `gross = Profit/Loss + commission + spread_cost` queda subestimado, mucho más en shorts que en longs.
- **Estado:** confirmado con experimento. `calc_a_edgecost.py`, AUDJPY H1, la tarea declara spread 0.0161 / slippage 0.0081 por fill (IS), así que un ida y vuelta real cuesta 0.0161 + 2 × 0.0081 = 0.0323 en precio:

  | harvest | `measure()` IS | ida y vuelta real | offset de salida que nunca lee | subestimado en |
  |---|---|---|---|---|
  | momentumL (30.112 Buy) | 0.0240 | 0.0323 | 0.0080 | 25 % |
  | momentumS (19.816 Sell) | 0.0080 | 0.0323 | 0.0240 | 75 % |

  OOS lo repite (0.019 / 0.006 medido, lado de salida 0.006 / 0.019).
- **A quién afecta:** lectura edgeCost (el edge se lee en múltiplos de `cost_today`); sesga a la baja el múltiplo de un short hasta ~1 unidad frente a un long con la misma economía; puede cambiar veredictos cerca del listón.
- **Cómo verificarlo:** `python3 scratch/cleanup/calc_a_edgecost.py Test_Calib_AUDJPY_H1_momentumL Test_Calib_AUDJPY_H1_momentumS`.
- **Corrección propuesta:** en `measure()` añadir el lado de salida: `exit = bars.index.searchsorted(Close time)`, `offset += (bar_open[exit] − Close price) × direction` sobre las salidas que caen en una apertura de barra, y tomar la mediana de la suma. Llamarlo «spread + slippage embebido en los fills», que es lo que es.
- **Test de regresión:** barras sintéticas con Open = 100 en todas; un Buy llenado a 100.03 y cerrado a 99.99, un Sell llenado a 99.99 y cerrado a 100.03 (spread 0.02, slippage 0.01 por fill) → `measure` devuelve 0.04 para ambos, tolerancia 1e-9. Hoy devuelve 0.03 y 0.01.

### M4 — puerta del gate `familia`: Benjamini-Hochberg sobre los supervivientes de una criba por p-valor

- **Dónde:** `studies/screening/gate/monkey.py:99-101`.
- **Qué pasa:** BH corre sobre `mono_p` de las estrategias aún vivas, es decir tras la criba dura `mono` que solo dejó p ≤ `max_p`, con m = número de supervivientes. La familia testada era todo el que entró en `mono`; seleccionar por p y encoger m rompe la garantía. Con los umbrales congelados (`max_p` 0.50, alpha 0.05) el FDR realizado es ~el doble del nominal; si el dueño aprieta `max_p` a alpha o menos, se nombra a todo superviviente.
- **Estado:** confirmado con experimento. `calc_a_known.py` (1000 estrategias, 300 runs, max_p 0.50, alpha 0.05):

  | proporción con edge real | BH sobre supervivientes: FDR | BH sobre todos los testados: FDR |
  |---|---|---|
  | 0 % | 0.080 | 0.037 |
  | 5 % | 0.093 | 0.048 |
  | 20 % | 0.068 | 0.040 |

  `calc_a_bh.py`, todo nulo: max_p 0.05 → se nombran 49.6 de 50 supervivientes en el 100 % de los runs (BH sobre todos: 0.07 nombrados, 5.2 % de los runs); max_p 0.10 → alguien nombrado en el 52 % de los runs.
- **A quién afecta:** gate (cribado OOS, paso 14-15). Hoy la criba es blanda, así que sesga un recuento reportado sin cortar a nadie; pasaría a CRÍTICO el día que se haga dura o baje `max_p`.
- **Cómo verificarlo:** `python3 scratch/cleanup/calc_a_known.py` (bloque 1), `calc_a_bh.py`.
- **Corrección propuesta:** tomar la familia de todo lo que `mono` testó: `p = data["scores"]["mono_p"].dropna()`, correr `discoveries` sobre eso, luego `passed = alive.isin(named)`; decir «sobre los N que entraron al mono» en la nota.
- **Test de regresión:** 1000 p uniformes, semilla fija, `max_p` 0.05, alpha 0.05 → `familia` nombra 0 (tolerancia ≤ 1). Hoy nombra ~50.

### M5 — SPP `combinado`: Sharpe sobre días naturales anualizado con √252

- **Dónde:** `studies/breakage/spp/model/combine.py:95-102` (`real_from_trades`).
- **Qué pasa:** el P/L diario se reindexa con `freq="D"` (fines de semana incluidos como ceros) y se multiplica por √252; la docstring dice que es la base de SQX. Media y sd se encogen ambas; el cociente sale bajo por √(5/7) ≈ 0.845. (Distinto de m11, que son series de días hábiles con ~260,6 filas/año; se mantienen separados.)
- **Estado:** confirmado con experimento, sobre operaciones reales (SQX `SharpeRatio` / código / días hábiles × √252): XAUUSD 20.25.72 IS 1.150 / 0.976 / 1.156; 0.920 / 0.784 / 0.927; 0.630 / 0.537 / 0.635; USDJPY 0.530 / 0.457 / 0.541; 0.740 / 0.628 / 0.743; OOS 0.760 / 0.648 / 0.767.
- **A quién afecta:** SPP (paso 15): el marcador de la estrategia real queda ~15 % bajo frente a una población de Sharpes de SQX en la que se la ordena.
- **Cómo verificarlo:** `calcb_spp.py`, segundo bloque.
- **Corrección propuesta:** `pd.bdate_range(...)` como hace `wfm/measure/equity.py`, o llamar `core.significance.annual_sharpe`.
- **Test de regresión:** las operaciones exportadas de una estrategia → valor a ±2 % de su `SharpeRatio` de SQX; sintético: una operación por día hábil durante 52 semanas, P/L N(10, 100) → igual a media/sd·√252 de la serie de días hábiles a 1e-9.

### M6 — cloud: el cuadrático local se ajusta con menos puntos que coeficientes y aun así se emite veredicto

- **Dónde:** `studies/optimisation/cloud/one.py:44,63`; `model/surrogate.py:25-43`; `verdict/call.py:22-57`; `model/neighbourhood.py`.
- **Qué pasa:** un cuadrático en k parámetros tiene `1 + 2k + k(k−1)/2` coeficientes (29 con k = 6). El vecindario de radio 2 del origen suele tener menos puntos, así que el ajuste interpola (R² = 1.000) o tiene un solo punto (R² NaN). `NaN >= umbral` es False, lo que se lee como «smooth»; un vecindario de una variante tiene cuantil 1.0 y se lee «plateau» («tiene compañía»). R² sin ajustar sube con p/n sobre ruido puro.
- **Estado:** confirmado con experimento. 12 lotes USDJPY H1: vecindario = 1 en 1.26.46, 1.26.74, 1.27.61, 11.13.81; 2-9 puntos (bajo el número de coeficientes, R² = 1.000) en 10.9.72, 16.9.76, 21.9.59, 22.11.70, 4.3.53; solo 3 son determinados (10.1.79 n 66, 15.9.45 n 33, 4.17.74 n 70). Estrategia 1.27.61: n = 1 → punto «plateau», superficie `['smooth','off_centre']`, R² local NaN. Ruido puro, 7 parámetros: 20 puntos → R² 1.0; 60 puntos → 0.619. `knowhow/research/plateau-radius-degenerates-at-six-params.md` registra n = 1 como esperado, pero los veredictos emitidos desde él siguen mal.
- **A quién afecta:** estudio cloud (optimización): 9 de 12 lotes reales llevan un veredicto de plateau/suavidad sin información detrás.
- **Cómo verificarlo:** `PYTHONPATH=. python3 scratch/cleanup/calcb_cloud.py`.
- **Corrección propuesta:** cuando el vecindario tenga `n <= coeficientes` (o `n < 2`) devolver `sin_dato` / estado `none` para punto, superficie y curvatura; reportar R² ajustado.
- **Test de regresión:** vecindario de 1 → ningún veredicto «plateau»; 20 puntos de ruido en 7 parámetros → rugosidad indefinida, nunca «smooth». (Tabla: vecindario n = 1 y n = 20 con k = 7 → estado `none`.)

### M7 — la búsqueda genética se envenena con puntuaciones NaN (combinaciones infactibles)

- **Dónde:** `portfolio/common/construct/search/genetic.py:111-115` (`top = int(scores.argmax())`, `if scores[top] > best_score`) y `:46` (`np.argmax(scores[cand])` en `_tournament`). El NaN viene de `search/stagea.py:57` (`best` devuelve NaN para una combinación infactible a todo nivel de riesgo, lote mínimo) a través de `construct/funded.py:105-110`.
- **Qué pasa:** `np.argmax` devuelve el primer NaN. Cuando una generación contiene una combinación infactible, `top` es esa, `NaN > best_score` es False, `best` no se actualiza y `stagnant` sube: la búsqueda para tras `stagnation` generaciones diga lo que diga lo encontrado, y `run["best"]` puede quedarse en su `masks[0]` / `-inf` inicial. Los torneos también prefieren al padre NaN, así que las combinaciones infactibles se reproducen. El elitismo (`argsort(-scores)`) no se ve afectado.
- **Estado:** confirmado con experimento. 6 nodos, puntuación = NaN si el miembro 0 está dentro, si no el tamaño de la combinación, una de tres semillas contiene el miembro 0. Resultado: `best = {'members': [0, 1], 'score': -inf}`, `generations_run = 10` (de 40), mientras la mejor puntuación finita realmente evaluada fue 4.0. `np.argmax([nan, 5, 1]) == 0`.
- **A quién afecta:** búsqueda de carteras (construct) para fondeo; muerde en cuentas pequeñas y lotes gruesos (planes de 2.000-5.000 USD), donde muchas combinaciones caen bajo el lote mínimo — justo los planes que el dueño compra primero.
- **Cómo verificarlo:** sonda de `calc_portfolio_probe.py` (bloque de la genética).
- **Corrección propuesta:** primera línea tras puntuar: `scores = np.where(np.isnan(scores), -np.inf, scores)` (conservar el array crudo para `all_scores` si el NaN debe guardarse).
- **Test de regresión:** `tests/test_portfolio_search.py`: clique plantado más una puntuación que devuelve NaN para toda combinación con un nodo de fondo; afirmar que `best["score"]` iguala al del clique plantado y `generations_run > stagnation`. Exacto.

### M8 — un trade arrastrado a una etapa deja balance y equity separados el resto de la etapa

- **Dónde:** `portfolio/funded/rules/machine.py:43,52-53` (referencia) y `:144,159` (kernel); `sim/account.py:33,41`; `sim/kernel.py:91,103`; `construct/mc/judge.py:88,100`; kernel de la etapa A.
- **Qué pasa:** el equity usa el flotante neto de la base de la etapa (`float_end[d-1] − baseline`, como congela `EXECUTION.md:123`: «balance = equity = size; el flotante se mide desde el inicio»), pero el balance contabiliza **todo** el P&L cerrado del trade arrastrado (`b += closed·k`). Una vez cerrado ese trade, `e0 = b − baseline·k` todos los días restantes: el objetivo se juzga sobre un balance que incluye beneficio hecho antes de que existiera la cuenta, y cada chequeo de suelo corre sobre un equity desplazado igual. La frase congelada se respeta solo en el lado del equity; los dos lados discrepan.
- **Estado:** confirmado con experimento (size 100.000, inicio = 1, el día 0 termina con +3.000 flotantes, el trade cierra el día 1 al mismo precio): (a) +7.000 cerrados el día 2, objetivo 10 % → **pass** el día 2 con un beneficio real desde el inicio de 7.000. (b) FTMO 5 % pérdida diaria, cuenta plana, bajón intradía de 2.500 el día 4 → **fail daily_loss** (suelo `b − 5.000 = 98.000`, equity `100.000 − 2.500 = 97.500`); el mismo bajón sin trade arrastrado → sin ruptura.
- **A quién afecta:** cada día de inicio, inicio de etapa 2+ y re-compra que caiga en un día con posiciones abiertas; signo = signo del flotante al inicio. La etapa A promedia sobre *todo* día de inicio del build, así que no es una esquina: su peso es la parte de días que terminan con posiciones abiertas (cerca del 100 % en miembros swing, 0 en intradía).
- **Cómo verificarlo:** sonda de `calc_portfolio_probe.py` (los dos caminos a/b).
- **Corrección propuesta (mínima, mantiene la convención congelada):** arrancar la etapa con `b = size − baseline·k` y usar `e0 = b + float_end[d-1]·k` — o, equivalente, mantener `e0` y restar `baseline·k` del balance una vez. Ambos hacen que balance y equity coincidan tras cerrarse los trades arrastrados; objetivo y trail eod leen entonces beneficio ganado dentro de la etapa.
- **Test de regresión:** `tests/test_funded_rules.py`: los dos caminos de arriba → (a) `open`, (b) sin fail; más «tras cerrarse el trade arrastrado, `e0 == b`». Exacto, referencia y kernel.

### M9 — `spread_widen` cobra el spread entero otra vez más el ensanchamiento

- **Dónde:** `portfolio/common/monteCarlo/model/stress.py:77-79` (`return stream["pnl"] - stream["spread"] * factor`, `factor ~ U(spread_scale)`), con `config.yaml:32` `spread_scale: [1.0, 2.0]`.
- **Qué pasa:** el P&L ya contiene un spread (`inputs/costs.py:151-152`: «el coste extra que añadiría un spread más ancho, no un coste a restar dos veces»; tooltip: «multiplicador del spread»). Un multiplicador de 1.0 no debe cambiar nada; el código resta un spread completo extra a 1.0 y dos a 2.0, es decir simula un spread de 2×-3×, no 1×-2×. `cost_shock`, dos funciones más arriba, lo hace bien (`factor − 1.0`).
- **Estado:** confirmado con experimento. pnl `[100, −50]`, coste de spread 10, escala `[1, 1]` → `spread_widen` da `[90, −60]`; `cost_shock` a `[1, 1]` da `[100, −50]`.
- **A quién afecta:** Monte Carlo de operaciones, Familia C: la puerta `spread_widen` (`verdict/gates.py:241`, `net_5 <= 0 or pf_5 <= min_pf`) y la sub-puntuación C (el *mínimo* de los cuatro tests) se leen al doble del estrés previsto en media; estrategias con poco edge por operación frente al spread reciben FAIL que el test documentado no daría. Conservador, pero es un veto.
- **Cómo verificarlo:** sonda de `calc_portfolio_probe.py`.
- **Corrección propuesta:** `stream["spread"] * (factor - 1.0)`.
- **Test de regresión:** `spread_widen(stream, n, rng, {"spread_scale": [1.0, 1.0]}) == pnl` exactamente; a `[2.0, 2.0]` → `pnl − spread` exactamente.

## Menores

(Dentro de este nivel: primero confirmados con experimento, luego confirmados leyendo, luego sospechas.)

### m1 — el máximo drawdown nunca cuenta la caída desde el balance inicial (fusión de tres informes)

- **Dónde:** `engines/nulls/stats.py:25-26`, `engines/nulls/kernel.py:44`, `engines/nulls/placement/kernel.py:54` (el pico corriente se inicializa en el P/L acumulado del **primer trade**, no en 0: `np.maximum.accumulate(curve)`; `peak = curve if k == 0 …`; `peak = equity if k == 0 …`); `studies/transfer/crossmarket/simulate/metrics.py:76-79` (`paths`, `peak = maximum.accumulate(equity0 + cumsum(pnl))` arranca en el equity DESPUÉS del primer trade, reflejado por `engines/nulls/placement/kernel.py:54`); `portfolio/common/monteCarlo/simulate/kernel.py:21` (`peak = equity if k == 0 or equity > peak else peak`) y `portfolio/common/monteCarlo/simulate/metrics.py:45-47` (`equity = equity0 + cumsum`, `peak = maximum.accumulate(equity)`). Hermano no idéntico: m15 (mcRetest `underwater`).
- **Qué pasa:** una racha que abre con pérdida tiene esa pérdida excluida de su drawdown; SQX mide desde el balance inicial. Los dos kernels de nulos discrepan además en el valor degenerado: escalera `retdd = 0.0`, `pf = inf`; placement `retdd = NaN`, `pf = NaN`.
- **Estado:** confirmado con experimento. Motores: P/L (−100, +50, +10): `stats.drawdown` → 0, `kernel.runs` → dd 0 y retdd 0.0; `placement.kernel.batch` sobre (−100, +50, +60) → dd 0, dd_pct 0, retdd NaN; respuesta correcta 100. crossmarket: P/L [−100, 50, 30] → dd 0.0, Ret/DD NaN (verdadero 100 y −0.2); [−100, −200, 50] → 200 (verdadero 300). Monte Carlo de operaciones: pnl `[−100, −100, +50]`, equity0 10.000 → `dd = 100`, `dd_pct = 0.0101`; correcto 200 y 0.02.
- **A quién afecta:** monkey, gate, crossTF, WFM monkey (escalera); crossmarket (placement y su `simulate/metrics`, `realrun.reported` documentado como reconciliable con SQX pero que no lo hace en una racha así); Monte Carlo de operaciones (`dd_pct_99`, puerta de supervivencia, e `inflation` algo subestimada). Acotado por la pérdida del primer trade y compartido por la corrida real y cada nulo, así que el p de `dd`/`retdd` se mueve poco; las cifras de drawdown reportadas quedan sesgadas a la baja. En Monte Carlo la reordenación hace más frecuente el caso en la cola que en la ruta observada.
- **Cómo verificarlo:** bloque `[B]` de `calc_engines_probe.py`; `calc_portfolio_probe.py`; los casos de arriba.
- **Corrección propuesta:** motores: `curve = np.cumsum(pnl, 1); peak = np.maximum(np.maximum.accumulate(curve, 1), 0.0)`; en los kernels inicializar `peak = 0.0` (escalera) / `peak = equity0` (placement) y quitar la rama `k == 0`. crossmarket: `peak = np.maximum(np.maximum.accumulate(equity), equity0)` en los dos sitios. Monte Carlo: `peak = equity0` (kernel) y `np.maximum(peak, equity0)` (metrics).
- **Test de regresión:** (−100, +50, +10) → dd 100, retdd −0.4; (+10, −30, +5) → dd 30; exacto, y `kernel.runs` igual a `stats.measure` en ambos. crossmarket: `observed([-100, 50, 30], 10000)["dd"] == 100`. Monte Carlo: `[−100, −100, +50]` → `dd == 200`, `dd_pct == 0.02`, `kernel.priced` igual a `metrics.paths`; exacto.

### m2 — el p empírico falla abierto con NaN

- **Dónde:** `engines/nulls/verdict.py:27-28`.
- **Qué pasa:** `(drawn >= seen).sum()` es 0 cuando `seen` es NaN, así que p = 1/(draws+1): el valor **más significativo posible**. Los NaN entre las muestras se cuentan como «no superó», sesgando p a la baja.
- **Estado:** confirmado con experimento. `pvalue(nan, 2500 draws, "sharpe")` = 0.00039984 = 1/2501. Con 40 % de las muestras NaN, `pvalue(0.0, …)` = 0.295 frente a 0.481 limpio. `kernel.runs` devuelve sharpe NaN para una muestra de un trade (sonda `[B]`); una muestra de varianza cero hace lo mismo.
- **A quién afecta:** `studies/screening/gate/monkey.py:30` (el gate se queda con este p), `studies/readings/monkey/one.py:45,62,67,135`, `studies/transfer/crossTF/cells.py:78`, `studies/optimisation/wfm/measure/monkey.py:33`. En el gate hay una criba `min_trades` antes, así que ahí es caso borde; `distrust()` *dice* «no se calcula p» bajo `min_trades` pero nada impide que los llamantes lo calculen.
- **Cómo verificarlo:** sonda `[B]` de `calc_engines_probe.py`.
- **Corrección propuesta:** `if seen != seen: return float("nan")`, y comparar contra `drawn[np.isfinite(drawn) | np.isinf(drawn)]` (conservar ±inf: un profit factor infinito es un valor) con denominador = las muestras conservadas.
- **Test de regresión:** `pvalue(nan, arange(10.), "sharpe")` es NaN; `pvalue(4.5, arange(10.), "sharpe")` = 6/11; `pvalue(4.5, arange(10.), "dd")` = 6/11 por el lado bajo (`(drawn<=seen)` = 5 → 6/11); exacto. Con `seen` por encima de todas las muestras → `1/11`.

### m3 — `_place` nunca puede colocar un trade donde está el último real

- **Dónde:** `engines/nulls/model.py:31-32`.
- **Qué pasa:** `lo + U·(hi − hold − lo)` truncado da entradas en `[lo, hi − hold − 1]`; `hi` es la barra de **salida** del último trade de la corrida real, así que la última entrada admisible `hi − hold` (salida justo en `hi`) es inalcanzable. La docstring afirma que el límite por trade existe precisamente para que el final de la ventana sea alcanzable.
- **Estado:** confirmado con experimento. Ventana (0, 10), hold 3, 200.000 sorteos: las entradas 0…6 salen ≈ 28.500 cada una, la entrada 7 = 0.
- **A quién afecta:** nulos de colocación aleatoria (monkey y derivados). Una barra en una ventana de miles; despreciable sobre p, pero es exactamente la clase de bug que el chequeo de «p uniforme» del módulo debería cazar y no caza (juzga nulos contra nulos).
- **Cómo verificarlo:** sonda de `calc_engines_probe.py`.
- **Corrección propuesta:** `(hi - holds - lo + 1)`.
- **Test de regresión:** el caso de arriba: `entries.max() == 7`, y un chi-cuadrado sobre 0…7 con p > 0.001 con semilla fija.

### m4 — el régimen ATR de un trade incluye el día del propio trade

- **Dónde:** `engines/regimes/regime.py:37-42` con `:85-89`.
- **Qué pasa:** `atr()` devuelve el ATR de Wilder **al cierre** del día D; `tag()` lee `vol[D]` para un trade abierto durante D. La etiqueta contiene el rango de D — en parte hecho tras la entrada y en parte por el movimiento que cabalgó el propio trade. `garch()` no lo tiene: `conditional_volatility[D]` es σ(D | D−1). Los dos modelos responden preguntas distintas bajo un mismo nombre, y el README dice «el estado de volatilidad *en el que* se abrió el trade».
- **Estado:** confirmado con experimento. Días planos sintéticos (TR 2) con un día de 40 puntos: `vol` = 2.0 el día anterior, **4.71 el propio día del pico**. En XAUUSD (6.057 días) retrasar la serie un día cambia el tercil del **3.73 %** de los días; el rango medio de día del tercil alto es 43.59 como está codificado y 42.62 retrasado — la etiqueta del mismo día selecciona, ligeramente, sobre el resultado.
- **A quién afecta:** `portfolio/common/monteCarlo/simulate/family_d.py:72-73` (y `verdict/significance.py`). `studies/readings/conditionalMap/one.py:33` solo usa `daily()`.
- **Cómo verificarlo:** sonda de `calc_engines_probe.py` (caso del pico) y XAUUSD con la serie retrasada.
- **Corrección propuesta:** en `atr()`: `"vol": span.ewm(...).mean().shift(1)`.
- **Test de regresión:** el frame sintético de arriba: `atr(day)["vol"][día del pico] == 2.0` y `[día siguiente] ≈ 4.714`; tolerancia 1e-9.

### m5 — un solo ensayo da un benchmark de −∞ y un DSR de 1

- **Dónde:** `core/surface/plateau.py:68-70`.
- **Qué pasa:** `norm.isf(1/1) = −inf`; el máximo esperado de un sorteo es 0.
- **Estado:** confirmado con experimento. `expected_max_sharpe(0.05, 1)` = −inf; `deflated_sharpe(sharpe=-0.5, …, n_eff=1)` → `dsr = 1.0` para un Sharpe negativo. (N = 2 → 0.52σ frente al exacto 0.564σ; N = 10 → 1.575σ frente a un simulado 1.539σ: la aproximación en sí es la publicada.)
- **A quién afecta:** `ledger/report.py:105-116` cuando la última búsqueda puntuó un candidato; CSCV está a salvo (`FLOOR = 2`).
- **Cómo verificarlo:** sonda de `calc_engines_probe.py`.
- **Corrección propuesta:** `if n_eff <= 1: return 0.0`.
- **Test de regresión:** `expected_max_sharpe(s, 1) == 0.0`; `deflated_sharpe(x, s, 1, n, sk, ku)["dsr"]` igual a `psr(returns, 0.0)["psr"]` a 1e-12.

### m6 — una búsqueda que puntuó un único candidato vuelve NaN el sigma del estudio

- **Dónde:** `ledger/trials.py:44-51`.
- **Qué pasa:** `record.distribution` guarda `std(ddof=1)` de un valor = NaN; `sd**2*(n-1)/n` es NaN·0 = NaN; `max(nan, 0.0)` conserva el NaN. (Un `scores` vacío lanza en `.max()` en su lugar.)
- **Estado:** confirmado con experimento. Filas (n 100, σ 0.05) + (n 1, σ NaN) → `sigma: nan`.
- **A quién afecta:** `ledger.trials.accumulated` y todo lo que lo consume (informe de ledger, DSR del paso 20).
- **Cómo verificarlo:** sonda de `calc_engines_probe.py`.
- **Corrección propuesta:** `population = np.where(n > 1, sd**2 * (n-1)/n, 0.0)`; y en `distribution`, devolver `{}` para un `clean` vacío.
- **Test de regresión:** las dos filas de arriba → sigma igual a la std ddof=1 de los 101 valores agrupados (construirlos explícitamente), 1e-9.

### m7 — `curve_duplicates` hashea solo valores; la docstring dice «valores y fechas por igual»

- **Dónde:** `core/surface/dedupe.py:130`.
- **Qué pasa:** curvas (0, 1, 3) fechadas desde 2020-01-01 y desde 2021-06-01: la segunda se marca como clon. Dos estrategias con curvas planas (todo cero) de igual longitud también son clones entre sí.
- **Estado:** confirmado con experimento.
- **A quién afecta:** `studies/screening/decay/report.py:155` (descarta el «clon»).
- **Cómo verificarlo:** sonda de `calc_engines_probe.py`.
- **Corrección propuesta:** hashear `curve.index.asi8.tobytes() + curve.to_numpy().tobytes()`.
- **Test de regresión:** el par de arriba → `{a: False, b: False}`; una copia exacta → `{a: False, b: True}`.

### m8 — `excess.fdr` no es una tasa: supera 1

- **Dónde:** `engines/inference/excess.py:53`.
- **Qué pasa:** 100 tests, uno bajo alpha 0.05 → `fdr = 5.0`. Además `observed` usa `p < alpha` mientras `fdr.discoveries` usa `<=`; con p empírico en una rejilla de 1/(draws+1) los dos discrepan en los empates.
- **Estado:** confirmado con experimento.
- **A quién afecta:** estudios que leen el exceso de descubrimientos sobre lo esperado (marketProfile / pooledProfile vía `engines/inference`).
- **Cómo verificarlo:** sonda de `calc_engines_probe.py`.
- **Corrección propuesta:** `min(1.0, alpha*n/observed)`; elegir una sola desigualdad (`<=`, la de BH).
- **Test de regresión:** el caso de arriba → `fdr == 1.0`, `excess == -4.0`.

### m9 — `exposure.presence` empareja cada barra sostenida con el movimiento de la barra siguiente

- **Dónde:** `studies/closing/exposure/one.py:51` (`np.diff(closes, append=closes[-1])`) con `occupancy.py:25-35` y `occupancy.py:95-97`.
- **Qué pasa:** `held[i]` es la posición durante la barra i, cuyo movimiento es `close[i] − close[i−1]`; el código le da `close[i+1] − close[i]`. `captured` y `aligned` quedan desplazados una barra.
- **Estado:** confirmado con experimento. Un long sostenido exactamente durante la única barra que mueve 1 → 2: como está codificado `captured 0.0, aligned 0.0`; con `np.diff(closes, prepend=closes[0])` ambos 1.0.
- **A quién afecta:** estudio exposure (paso de cierre); alimenta solo el texto de razón de `timing`, nunca el veredicto; se diluye en tenencias largas, está mal en operaciones de una barra.
- **Cómo verificarlo:** el caso de arriba (sintético).
- **Corrección propuesta:** `np.diff(closes, prepend=closes[0])`.
- **Test de regresión:** el caso de arriba → `captured == 1.0 and aligned == 1.0`, exacto. Tabla: una operación sobre 3 de 10 barras → `share == 0.3`.

### m10 — `exposure.benchmark.daily` descarta el P&L cerrado en un día que el benchmark no tiene

- **Dónde:** `studies/closing/exposure/benchmark.py:102-103`; índice de `moves()` en `:82-83`.
- **Qué pasa:** `moves` descarta el primer día de la ventana (`diff().dropna()`), y `daily` reindexa el P&L de la estrategia sobre él, así que los trades cerrados el primer día, o en cualquier día sin barra, desaparecen de `net`, `return_pct`, el Sharpe y `equal_risk`.
- **Estado:** confirmado con experimento (sintético): operaciones de 100 + 50, la primera cerrada el día uno → `daily.sum()` = 50. No medido en datos reales cuántas veces ocurre.
- **A quién afecta:** estudio exposure: neto, rentabilidad, Sharpe y `equal_risk` del benchmark.
- **Cómo verificarlo:** el caso de arriba.
- **Corrección propuesta:** construir el índice de días desde los cierres antes de diferenciar y poner el movimiento del primer día a 0, o afirmar `daily.sum() == trades["Profit/Loss"].sum()` y lanzar.
- **Test de regresión:** el caso de arriba → `daily.sum() == 150`, exacto.

### m11 — Sharpe anualizado a 252 en series que llevan ~260,6 filas al año

- **Dónde:** `studies/screening/analysis/decay.py:6`, `studies/screening/snoopingScreen/measure.py:9`, `studies/closing/blindJoint/measure.py:9`, `studies/closing/exposure/compare.py:7`. (Distinto de M5, de m17 y del `/sqrt(252)` del ledger, que se mantienen aparte.)
- **Qué pasa:** la equity diaria de SQX tiene una fila por día laborable, festivos incluidos (harvests reales: 260.7 y 260.4 filas/año en AUDJPY, 255.9 / 260.4 en DAX40, 9 sábados en el OOS de DAX40). √252 sobre esas filas subestima todo Sharpe anual por ×0.983.
- **Estado:** confirmado con experimento sobre los recuentos de filas (`calc_a_real.py`); el 1,7 % se sigue de ahí.
- **A quién afecta:** decay, snoopingScreen, blindJoint, exposure. Ambos lados de cada comparación lo comparten y el t de Lo es invariante (YEAR se cancela en `decay.py:47-49`), así que ningún veredicto se mueve; una barra absoluta de Sharpe sería 1,7 % demasiado estricta. (Decisión del dueño: la fuente también propone dejar 252 y declararlo convención en el README.)
- **Cómo verificarlo:** `python3 scratch/cleanup/calc_a_real.py`.
- **Corrección propuesta:** anualizar por las filas por año que realmente tiene la serie (`len(after) / years`), o declarar 252 como convención en el README.
- **Test de regresión:** 2606 filas de días hábiles en 10 años, media 1, sd 10 → Sharpe `0.1 × √260.6 = 1.614`, tol 1e-3.

### m12 — `decay.diagnose` descarta el último día IS cuando `split` no es una fila de la curva

- **Dónde:** `studies/screening/analysis/decay.py:39` (`daily[:split][:-1]`); mismo idioma en `gate/measures.py:30`.
- **Qué pasa:** `[:-1]` está para quitar el día de corte que el slicing por etiqueta incluye. Cuando el corte es un día que la curva no tiene (fin de semana, `decay.report --split 2018-01-01` con el feed cerrado), no se incluyó nada y se descarta el último día IS.
- **Estado:** confirmado con experimento. Corte en sábado 2017-12-30: 520 filas IS frente a 521 reales. El gate en sí está a salvo: `inputs.load` toma `split` del índice.
- **A quién afecta:** `decay.report` por línea de comandos (un día de ~2600).
- **Cómo verificarlo:** el caso de arriba.
- **Corrección propuesta:** `daily[daily.index < split]`.
- **Test de regresión:** curva de días laborables, corte en sábado → `len(before) == (index < split).sum()`.

### m13 — `retention` y `concentration` cambian de signo con denominador negativo

- **Dónde:** `studies/screening/analysis/decay.py:49-51`; leído por la criba `degradacion`.
- **Qué pasa:** `retention = sharpe_oos / sharpe_is` es positivo cuando ambos son negativos y negativo cuando un IS perdedor se vuelve OOS ganador; `concentration = quarters.max() / total` es negativo cuando el total OOS lo es, lo que pasa `<= max_concentration`.
- **Estado:** confirmado con experimento. IS perdedor y OOS perdedor: retention +0.54, concentration −0.12, t −2.28.
- **A quién afecta:** la criba `degradacion`. `min_t: 0.0` frena hoy el caso ambos-negativos; el caso IS-negativo/OOS-positivo se rechaza por `min_retention` aunque el edge mejorase, y una regla solo sobre `concentration` dejaría pasar perdedores.
- **Cómo verificarlo:** el caso de arriba.
- **Corrección propuesta:** NaN en ambos cuando `sharpe_is <= 0` / `total <= 0`, y que la criba trate NaN como fallo con su propia nota.
- **Test de regresión:** el caso de arriba → `retention` y `concentration` son NaN.

### m14 — mcRetest: `reduceat` devuelve los valores de la simulación siguiente para una simulación con cero operaciones

- **Dónde:** `studies/breakage/mcRetest/model/recon.py:62-79`; `model/drawdown.py:57` (`_reduce`); sin guarda en `core/sqxretest.py:95-97`.
- **Qué pasa:** `reduceat` sobre offsets con duplicados devuelve el elemento siguiente en lugar de 0 para un segmento vacío.
- **Estado:** confirmado con experimento (sintético). P/L en centavos [10000, −5000, 20000], offsets [0, 2, 2, 3] → NetProfit [50, 200, 200] (esperado [50, 0, 200]); AvgTrade [25, inf, 200]; una ÚLTIMA simulación vacía lanza `IndexError`. No presente en los ingests reales leídos (mínimo de operaciones 172).
- **A quién afecta:** reconstrucción de mcRetest (latente hasta que aparezca una simulación sin operaciones).
- **Cómo verificarlo:** `calcb_mcr.py`.
- **Corrección propuesta:** enmascarar donde `n == 0` tras el reduce.
- **Test de regresión:** la entrada de arriba → [50, 0, 200], sin inf.

### m15 — mcRetest `underwater`: el pico deja fuera el balance inicial

- **Dónde:** `studies/breakage/mcRetest/verdict/fragility.py:92-93`. (Hermano de m1 pero otra métrica; `model/drawdown.py:26` sí incluye el cero inicial, así que ambos discrepan.)
- **Qué pasa:** el pico se toma desde el equity tras el primer trade.
- **Estado:** confirmado con experimento. P/L [−50, −10, 20] → 0.333; la cuenta está bajo su inicio en las tres operaciones, 1.0.
- **A quién afecta:** fragilidad de mcRetest.
- **Cómo verificarlo:** el caso de arriba.
- **Corrección propuesta:** `np.maximum.accumulate(np.maximum(equity, 0))`.
- **Test de regresión:** la entrada de arriba → 1.0.

### m16 — marketSurfaces: «sin filas» se lee como «la región viaja»

- **Dónde:** `studies/optimisation/marketSurfaces/verdict/call.py:62-66` (`mother`).
- **Qué pasa:** `all([])` es True. La docstring dice que un mercado ausente «cuenta como no pasa».
- **Estado:** confirmado con experimento. `mother(empty rows, declared=4, min_share=0.5)` → estado `pass`, etiqueta «la región viaja», `passed = {}`. Se alcanza cuando ningún mercado declarado está en el lote.
- **A quién afecta:** marketSurfaces (optimización de mercados).
- **Cómo verificarlo:** la llamada de arriba.
- **Corrección propuesta:** iterar sobre los segmentos configurados (ausente → 0 pasados), o devolver `fail` cuando no hay filas.
- **Test de regresión:** la llamada de arriba → `fail`.

### m17 — wfm: el Sharpe por celda descarta el P/L de los cierres en fin de semana

- **Dónde:** `studies/optimisation/wfm/measure/equity.py:54-56,61` (`per_cell`).
- **Qué pasa:** el P/L cerrado en domingo no entra en la serie diaria de días hábiles. También `daily.std() == 0` da inf.
- **Estado:** confirmado con experimento (sintético). Operaciones de 10, 500 (cierra en domingo), −20, 30: net profit 520, Sharpe 4.21 — idéntico al Sharpe sin la operación de 500; rodada al lunes sale 10.35. El export real de WFM de XAUUSD no tiene cierres en fin de semana; los paneles de equity de USDJPY tienen 97 filas de domingo en 19 años.
- **A quién afecta:** WFM (paso 19), Sharpe por celda (USDJPY).
- **Cómo verificarlo:** `calcb_wfm.py`.
- **Corrección propuesta:** usar `core.significance.annual_sharpe` (rueda el cierre de fin de semana al lunes, NaN si no hay dispersión).
- **Test de regresión:** las cuatro operaciones de arriba → 10.35 ± 0.01.

### m18 — crossTF rho: los meses en que ningún lado operó están ausentes, no a cero

- **Dónde:** `studies/transfer/crossTF/cells.py:216-224` (`correlations`), leído por `beyond` en `:167-169`.
- **Qué pasa:** la docstring dice que los meses ociosos cuentan 0, pero el outer join solo contiene meses en que al menos un lado cerró un trade. Descartar los meses ociosos conjuntos baja la correlación, y `z_new` divide por √(1 − rho²).
- **Estado:** confirmado con experimento (sintético, deliberadamente extremo: ambos ociosos en la mitad de 48 meses): rho 0.882 con los ceros, 0.424 como está; para z = z_mother = 2, `z_new` es 0.50 frente a 1.27. Con datos reales oos1 el efecto es probablemente pequeño (una madre con ≥ 30 operaciones cierra algo casi todos los meses). Ningún panel real lleva aún `z_new` (los seis son anteriores a 2026-10-02).
- **A quién afecta:** crossTF (`beyond`, `z_new`, z combinado).
- **Cómo verificarlo:** `calcb_transfer.py`.
- **Corrección propuesta:** reindexar ambas series sobre `period_range(inicio oos1, fin oos1)` con 0 antes de `.corr`.
- **Test de regresión:** dos series iguales en 6 meses y ociosas en 6 → mismo rho que en el frame de 12 meses. Tabla: z 2, madre 2, rho 0.5 → `z_new` 1.1547 ±1e-4; dos hermanas 1.0 y 2.0 → combinado 2.1213; rho 0.99 recortado a 0.95.

### m19 — crossmarket `summarise`: un estadístico observado NaN recibe el p más pequeño

- **Dónde:** `studies/transfer/crossmarket/simulate/metrics.py:125-133`.
- **Qué pasa:** toda comparación con NaN es False, así que `beaten = 0`.
- **Estado:** confirmado con experimento. Observado NaN frente a 4 sorteos → `p_value` 0.2 = 1/(n+1), `beats` 0.0. Se alcanza para `ret_dd` cuando dd = 0 (ver m1) y `pf` sin trade perdedor.
- **A quién afecta:** crossmarket.
- **Cómo verificarlo:** `calcb_transfer.py`.
- **Corrección propuesta:** devolver NaN para `p_value`, `beats` y `rank` cuando `seen` no es finito.
- **Test de regresión:** la llamada de arriba → NaN.

### m20 — `excursions.rebuild` se cae con un trade que abre y cierra dentro de una barra M1

- **Dónde:** `portfolio/common/construct/equity/excursions.py:40-41` (`low[a:b].min()`).
- **Qué pasa:** `a == b` → rebanada vacía → `ValueError: zero-size array to reduction operation minimum`. Se alcanza desde `equity/universe._reconcile_rows` para cada miembro, así que un trade así (stop alcanzado en el minuto de entrada) aborta la construcción del universo. Relacionado: la rebanada `[a:b)` deja fuera la barra de cierre y toma entera la de apertura (en un trade de dos barras solo se lee la de apertura; sonda: abre 00:01:05, cierra 00:02:10 → MAE leído solo de la barra 00:01).
- **Estado:** confirmado con experimento.
- **A quién afecta:** construcción del universo de carteras (construct/equity).
- **Cómo verificarlo:** `calc_portfolio_probe.py`.
- **Corrección propuesta:** `low[a:max(b, a + 1)]` (la propia barra del trade cuando no tiene otra).
- **Test de regresión:** `tests/test_portfolio_mtm.py`: un Buy abierto y cerrado dentro del mismo minuto → sin excepción, `mae == min(0, low_bar − open) × size × point_value`.

### m21 — cloud `origin_rank` cuenta variantes de Sharpe NaN en el denominador

- **Dónde:** `studies/optimisation/cloud/measure/stability.py:117-118`.
- **Qué pasa:** `frame.le(frame[origin]).mean(axis=1)`: un NaN compara False, así que el rank queda subestimado por la proporción de NaN, y un origen NaN rankea 0.
- **Estado:** confirmado leyendo.
- **A quién afecta:** cloud (estabilidad).
- **Cómo verificarlo:** el caso de abajo.
- **Corrección propuesta:** dividir por `frame.notna().sum(axis=1)`.
- **Test de regresión:** [1, 2, NaN, 3] con origen 3 → 1.0, no 0.75.

### m22 — wfc: el ancho Fisher-z de Pearson usado para un rho de Spearman

- **Dónde:** `studies/optimisation/wfc/measure/correlation.py:43`.
- **Qué pasa:** semianchura `1.96/√(n−3)`; para Spearman la varianza es ≈ `1.06/(n−3)`, así que el intervalo es un 3 % demasiado estrecho. Además las dos variantes canario (elegidas por NetProfit IS extremo) y el origen están dentro del rho: 3 de unos 499 puntos.
- **Estado:** confirmado leyendo.
- **A quién afecta:** wfc (paso 16.5).
- **Cómo verificarlo:** el caso de abajo.
- **Corrección propuesta:** `1.96·√(1.06/(n−3))`.
- **Test de regresión:** n = 103, rho 0 → semianchura 0.2018 en z. (Cubierto hoy: ni rho ni intervalo de wfc.)

### m23 — crossmarket breadth: el denominador son los mercados valorados, no los declarados

- **Dónde:** `studies/transfer/crossmarket/verdict/breadth.py:18`; filas ensambladas en `studies/transfer/crossmarket/many.py:170-179`.
- **Qué pasa:** `fraction = cleared / len(rows)`, siendo `rows` solo los mercados en que la estrategia operó Y cuyo análisis no lanzó (desde 2026-10-03 un mercado fallido «cuenta como missing»). Una estrategia valorada en 1 de 16 mercados que supera ahí lee 100 % → MANTENER.
- **Estado:** confirmado leyendo; ningún veredicto real se movió: en 14 `verdict.csv` reales (3.078 filas de estrategia) solo 2 son MANTENER y ambos tienen `missing = 0`. Severidad MENOR hoy, cambia el veredicto la primera vez que una estrategia delgada supere.
- **A quién afecta:** crossmarket (veredicto de amplitud).
- **Cómo verificarlo:** recorrer los `verdict.csv` reales (14).
- **Corrección propuesta:** dividir por `markets + missing`, o declarar en el README que los mercados silenciosos quedan fuera del denominador (decisión del dueño sobre cuál).
- **Test de regresión:** 1 fila superada con `missing = 15`, suelo 0.5 → DESCARTAR.

### m24 — crossTF: `usable.min_trades` es un mando muerto

- **Dónde:** `studies/transfer/crossTF/cells.py:73` lee `nullcfg["verdict"]["min_trades"]` (`engines/nulls/config.yaml:42`); `studies/transfer/crossTF/config.yaml:27` y su tooltip no los lee nadie.
- **Qué pasa:** ambos valen 30 hoy, así que ningún número está mal; `--set usable.min_trades=50` no hace nada en silencio, y `many.py:20` tiene fijo «menos de 30». También `cells.py:81`: una nula con `sd == 0` da z = ±inf.
- **Estado:** confirmado leyendo (grep).
- **A quién afecta:** crossTF (configuración por línea de comandos / ventana).
- **Cómo verificarlo:** grep de `usable.min_trades`.
- **Corrección propuesta:** leer el mando del propio estudio (o borrarlo).
- **Test de regresión:** `usable.min_trades=50`, celda de 40 operaciones → `p` NaN.

### m25 — el drawdown de una corrida de placement se lee en orden de columna, no en el tiempo (sospecha; decisión del dueño)

- **Dónde:** `engines/nulls/placement/kernel.py:37-56`.
- **Qué pasa:** `batch()` acumula `cum`, `peak`, `dd`, `worst_run` sobre `k` (el orden de los trades reales) mientras las entradas que valora fueron recolocadas: `_lay` (`free_models.py:30-34`) envuelve el círculo desde un inicio aleatorio, `block_shift` envuelve dentro de cada semestre, `regime_strata` dispersa. La misma función agrupa `curves` por **barra de salida** (`:59`), así que la trayectoria de equity de una corrida y su drawdown describen dos ordenaciones distintas.
- **Estado:** sospecha (por inspección, no medido). `engines/nulls/README.md` documenta el mismo defecto para el kernel de la escalera (y lo midió: p_dd 0.018 → 0.0084 en una estrategia), con la decisión del dueño «leer en orden de salida» aún sin implementar; el README de placement no lo menciona. MENOR como hallazgo (clase conocida), pero mueve `dd`, `dd_pct`, `retdd`, `worst_run` de todo nulo de crossmarket; `net`, `sharpe`, `pf`, `mean_r` no dependen del orden. **Decisión del dueño de 2026-09-25 pendiente de implementar.**
- **A quién afecta:** crossmarket (nulos de placement); y el kernel de la escalera ya documentado.
- **Cómo verificarlo:** para un (estrategia, mercado), recomputar `dd` desde `np.diff(curves)` con `steps` lo bastante grande para separar trades y comparar con `stats[:, 2]`.
- **Corrección propuesta:** `np.argsort` de las columnas de cada corrida por `entries + holds` antes del pase (uno por corrida), en ambos kernels — la decisión del dueño del 2026-09-25.
- **Test de regresión:** tres trades cuyo orden de columna es P/L (−60, +100, −60) y cuyas entradas los ponen en orden temporal (+100, −60, −60): dd esperado 120 y `worst_run == 2`; el orden de columna da 60 y 1.

### m26 — el gate coloca monkeys y mide la deriva sobre barras M30 salvo que se diga lo contrario (sospecha)

- **Dónde:** `studies/screening/gate/config.yaml:89` (`monkey.timeframe: M30`), leído en `gate/report.py:33`; `gate/measures.py:12` documenta `bars` como «el timeframe propio de las estrategias».
- **Qué pasa:** `ui/daemon/runner/screening.py:20` pasa `--set monkey.timeframe=<tf>`, pero `ui/daemon/runs.py:73` y una línea de comandos pelada no, así que un proyecto H1 se juzga sobre la rejilla M30: las entradas aleatorias caen en medias horas que una estrategia H1 nunca puede operar, y el hold de `drift` se cuenta en barras M30. Las aperturas H1 son también aperturas M30, así que los trades fijos siguen reconciliando y nada lo señala.
- **Estado:** sospecha — el tamaño del efecto sobre `mono_p` no se midió.
- **A quién afecta:** gate (monkey y drift) en proyectos que no sean M30 lanzados fuera de `ui/daemon/runner/screening.py`.
- **Cómo verificarlo:** correr el gate sobre `Test_Calib_AUDJPY_H1_momentumL` con y sin `--set monkey.timeframe=H1` y comparar el rango de `mono_p` y el recuento que pasa `mono`.
- **Corrección propuesta:** tomar el timeframe por defecto del manifiesto del harvest (`harvest.py:46` ya registra `timeframes`) y negarse cuando tenga más de uno.
- **Test de regresión:** un harvest cuyo manifiesto dice H1 y sin override → el espaciado de `data["bars"]` es de 60 minutos.

### m27 — `searchsorted` (side left) manda una entrada llenada dentro de una barra a la barra siguiente (sospecha)

- **Dónde:** `studies/readings/edgeCost/spread_share.py:45`, `studies/readings/entryQuality/inputs.py:50` (luego `atr[entry − 1]` en `:55`), `studies/closing/exposure/occupancy.py:25`.
- **Qué pasa:** una entrada sellada en la apertura de una barra se mapea a esa barra, correcto; una sellada dentro de una barra se mapea a la siguiente. edgeCost compara entonces el fill con la Open equivocada, entryQuality lee un ATR que contiene la barra de entrada (lo que su propia docstring prohíbe) y empieza la excursión una barra tarde, exposure pierde la barra de entrada. `atrCalculator/mae.py:20` y `feedQuality/touch.py:62` lo hacen bien (`side="right"` menos uno).
- **Estado:** sospecha. En los dos harvests comprobados el 100 % de las entradas están en una apertura de barra (solo órdenes a mercado, regla dura 15), así que ahí no muerde; `studies/CLAUDE.md` registra un 1,2 % de entradas de XAUUSD fuera de la apertura en proyectos antiguos.
- **A quién afecta:** edgeCost, entryQuality, exposure en proyectos con entradas intrabarra.
- **Cómo verificarlo:** contar entradas fuera de apertura de barra en un harvest antiguo de XAUUSD.
- **Corrección propuesta:** `searchsorted(..., side="right") − 1` para la barra que contiene la entrada, en los tres sitios.
- **Test de regresión:** barras a las 10:00 y 11:00, entrada a las 10:20 → índice de barra 0.

### m28 — edgeCost etiqueta el reloj del feed como UTC (sospecha)

- **Dónde:** `studies/readings/edgeCost/one.py:22` y `:44` («hora de entrada (UTC)»).
- **Qué pasa:** `Open time` está en el reloj del feed (EETUS desde 2026-10-01), a 2-3 horas de UTC.
- **Estado:** sospecha (leído, no ejecutado).
- **A quién afecta:** la lectura edgeCost mostrada al dueño (etiqueta).
- **Cómo verificarlo:** leer los dos sitios.
- **Corrección propuesta:** decir «hora del feed».
- **Test de regresión:** ninguno que valga la pena.

### m29 — el p bootstrap del barrido de filtros no alcanza los primeros peldaños de BH; `replication` elige un ganador (sospecha)

- **Dónde:** `studies/screening/analysis/improvement.py:111-118`; `analysis/replication.py` (`best_filters`, `hit_gap`).
- **Qué pasa:** con 2000 remuestreos el p mínimo es 1/2001, por encima del umbral del rango 1 de BH sobre ~210 tests (0.05 / 210 = 0.00024), así que un único filtro fuerte no puede nombrarse nunca — la propia advertencia del módulo lo dice. `best_filters` toma el máximo de ~210 sobre la muestra de referencia sin n mínimo, y `hit_gap` llama `rng.integers(0, 0)` sobre una muestra vacía.
- **Estado:** sospecha (solo aritmética).
- **A quién afecta:** barrido de filtros del cribado (`analysis/improvement.py`, `analysis/replication.py`).
- **Cómo verificarlo:** aritmética del suelo del p; llamar `hit_gap` con muestra vacía.
- **Corrección propuesta:** remuestreos ≥ 20 × tests / alpha, o reportar el suelo junto al recuento; guardar la muestra vacía.
- **Test de regresión:** un filtro con un lift verdadero de 5 sd entre 209 nulos → se nombra.

### m30 — sesión de spread: dos «puntos» distintos para el mismo segmento; el rango MC hereda el 1.25 (sospecha) (decisión del dueño) (sesión de spread)

- **Dónde:** `studies/data/spread/verdict.py:96` frente a `onboard.py:69-72`; `onboard.py:88-90`.
- **Qué pasa:** los `puntos equivalentes` del scan son `mean(rel) × factor × median(price) / tick`; el onboard escribe `mean(rel × price) / tick × factor`. Difieren cuando spread y precio se mueven juntos dentro de un segmento, así que el informe muestra una cifra y `assets/` recibe otra. Y `mc_range` multiplica los ratios de día 2.5-97.5 % por `spread_is`, que ya lleva el factor 1.25, así que la banda del MC Retest es la dispersión medida desplazada un 25 % hacia arriba: su extremo bajo es 1.25 × el cuantil 2.5 %, nunca los días baratos en sí.
- **Estado:** sospecha — leído, no ejecutado (la otra sesión está editando esos ficheros). Ambas cosas pueden ser intencionadas; el README dice «por el spread al que corre la tarea».
- **A quién afecta:** onboard de activos (`assets/`) y rango del MC Retest (paso 13).
- **Cómo verificarlo:** `python3 -m studies.data.spread.onboard --symbol XAUUSD --kind metal` (sin `--write`) frente a la propuesta del `summary.json` del scan para el mismo segmento.
- **Corrección propuesta:** una sola función para «puntos de un segmento», llamada por ambos.
- **Test de regresión:** un segmento donde el precio se dobla y rel se divide por la mitad → ambos caminos devuelven los mismos puntos. (Tabla: base 1.0, k {0.9, 1.1}, grano 0.1, min_steps 10 → (0.5, 1.5); base 0.2 → extremo bajo recortado a 0 y banda de 1.0 de ancho.)

### m31 — ratios sobre un original no positivo (sospecha)

- **Dónde:** `studies/breakage/mcRetest/verdict/scoring.py:50,75` y `gates.py:88`; `studies/breakage/spp/model/profile.py:96-97`; `studies/optimisation/wfm/measure/correlation.py:30,56-62`.
- **Qué pasa:** un ratio sobre `original_net <= 0` invierte su orden; `original·(1 ± min_span)` cae del lado equivocado para un original negativo; una celda constante da un rho NaN que se propagaría al agrupado (0 NaN en 150 celdas reales).
- **Estado:** sospecha.
- **A quién afecta:** mcRetest (scoring/gates), SPP (profile), WFM (correlación agrupada).
- **Cómo verificarlo:** buscar un caso con `original_net <= 0`.
- **Corrección propuesta:** devolver NaN / `sin_dato` para un denominador no positivo; `nanmean` o descartar en el agrupado.
- **Test de regresión:** original no positivo → NaN / `sin_dato`; celda constante en el agrupado → se descarta, el resto agrupa.

### m32 — crossTF: `survives` se decide antes que el signo del resultado (sospecha)

- **Dónde:** `studies/transfer/crossTF/verdict.py:69-74`.
- **Qué pasa:** `p < alpha and z_new > level` se prueba primero y `seen > 0` después. Bajo costes la media de Sharpe de la nula de timing es negativa, así que una hermana que PERDIÓ dinero en oos1 pero perdió menos que sus gemelas aleatorias lee `survives` (estado `pass`), aunque `MEANS` define `fails` como «perdió dinero en oos1».
- **Estado:** sospecha. No reproducible sobre los paneles guardados (sin `z_new`).
- **A quién afecta:** crossTF (veredicto).
- **Cómo verificarlo:** el caso de abajo con el veredicto directo.
- **Corrección propuesta:** exigir `seen > 0` en la rama `survives`.
- **Test de regresión:** seen −0.01, p 0.01, z_new 2.5 → `fails`.

### m33 — `time_limit_days` se compara contra días de trading (sospecha, latente)

- **Dónde:** `portfolio/funded/rules/catalog.py:156` → `rules/machine.py:75` (`d − stage_start + 1 >= stage["time_limit"]`).
- **Qué pasa:** la columna del catálogo está en días naturales; `d` indexa días de servidor (de trading). `sim/plans.cash` convierte `payout_days` con `days_per_year / 365`; el límite de tiempo no recibe esa conversión, así que un límite de 30 días se simularía como ~42 días naturales. La misma comparación también hace fallar la etapa el día límite aunque el objetivo se cumpla ese día solo si se comprueba después — no verificado.
- **Estado:** sospecha. Exposición hoy: ninguna — ninguna etapa actual tiene `time_limit_days` (consulta: 0 filas). Morderá el día que se dé de alta una firma con plazo.
- **A quién afecta:** simulación de etapas del fondeo.
- **Cómo verificarlo:** consulta de `time_limit_days` sobre `AlgoData/funding/funding.sqlite`.
- **Corrección propuesta:** convertir en `catalog.plan` (`round(time_limit × days_per_year / 365)`) como hace `cash`.
- **Test de regresión:** etapa con `time_limit` 30 días naturales en un camino de semana de 5 días → fallo `time_limit` en el día de trading 21 o 22, no 30.

### m34 — medidas mensuales de pares cortadas por etiqueta de mes, no por día (sospecha, latente)

- **Dónde:** `portfolio/common/construct/funded.py` (`matrix.segment(data["monthly"][usable], calendar, "build")`) y `funded_b.py` `load()`; las sumas mensuales vienen de `equity/matrix.py` sobre toda la historia.
- **Qué pasa:** un mes que cruza el fin del build se suma entero (lleva días oos1 a la correlación usada para elegir la cartera), y el primer y último mes parciales de un miembro entran como meses completos.
- **Estado:** sospecha. Exposición hoy: ninguna para la fuga — todo segmento `build` de `assets/_policy.yaml` acaba en límite de año. El primer mes parcial existe para los inicios de 2013-09-30 (un día; despreciable).
- **A quién afecta:** construcción de carteras (correlación de pares mensual).
- **Cómo verificarlo:** `assets/_policy.yaml`: confirmar que cada fin de build es límite de año.
- **Corrección propuesta:** sumar los meses desde la tabla diaria cortada al build, o afirmar límites de segmento alineados a mes.
- **Test de regresión:** un fin de build el día 15 con un pico de ±1.000 el día 20 → Pearson mensual sin cambios por el pico.

### m35 — el P(pass) reportado de la etapa B es el mejor de varios mínimos ruidosos (sospecha)

- **Dónde:** `portfolio/common/construct/search/stageb.py` / `stageb_run.py` (`decide`: por ajuste el menor P(pass) sobre sabores y longitudes, luego el mejor ajuste sobre shortlist × rejilla de riesgo).
- **Qué pasa:** el máximo sobre muchas estimaciones Monte Carlo está sesgado al alza por su error de muestreo (maldición del ganador); el re-sorteo de estabilidad se hace solo en el ajuste elegido y no se usa para sustituir la estimación seleccionada. La nula del veredicto (`verdict/null.py`) sí paga por la *búsqueda*, así que el percentil es justo; el P(pass) absoluto mostrado al dueño y alimentado al EV del banco es el optimista.
- **Estado:** sospecha.
- **A quién afecta:** construcción de carteras (etapa B), P(pass) mostrado y EV del banco.
- **Cómo verificarlo:** sobre un pool de ruido, comparar el `p` reportado del ganador con su `p` en caminos nuevos y semilla independiente, sobre ~50 semillas; la diferencia media es el sesgo.
- **Corrección propuesta:** reportar el P(pass) re-sorteado del ganador, no el selector.
- **Test de regresión:** pool de ruido, 50 semillas: media(p selector − p re-sorteado) dentro de ±1 error estándar MC tras la corrección.

### m36 — ratios cuyo denominador puede ser cero o negativo (sospecha)

- **Dónde:** `portfolio/funded/sim/haircut.py:9` — `closed.sum() / np.count_nonzero(closed)`; `portfolio/common/monteCarlo/verdict/scoring.py:369` (`b["net_5"] / observed["net"]`) y `:367` (`survival_dd_pct / dd_pct_99`); `portfolio/common/monteCarlo/simulate/family_d.py` (`"concentration": max(net) / total`).
- **Qué pasa:** haircut: 0/0 → NaN en un conjunto de caminos que nunca cierra un día, y el NaN se extiende a todo `closed` vía `apply`; un edge negativo hace que un haircut *añada* beneficio. scoring: para una estrategia perdedora ambos son negativos y el ratio puntúa 100 (enmascarado hoy solo porque la puerta B veta); `:367` divide por cero en un conjunto sin drawdown. family_d: el signo cambia cuando el total es negativo; alimenta una bandera, no una puerta.
- **Estado:** sospecha.
- **A quién afecta:** simulación de fondeo (haircut) y Monte Carlo de operaciones (scoring, Familia D).
- **Cómo verificarlo:** casos de abajo.
- **Corrección propuesta:** guardar cada uno (`edge` → lanzar si no hay día cerrado; puntuaciones → 0 cuando `observed.net <= 0`).
- **Test de regresión:** `closed` todo cero → error explícito; net observado −1.000, net_5 −2.000 → sub-puntuación B es 0.

### Nota fuera de alcance (no contada; sospecha, lado motores)

`engines/variants/panel.py:116-117` descarta solo el periodo final, aunque cada una de las tres patas termina con posiciones abiertas valoradas a mercado (suma de P/L diario menos NetProfit: media −73, sd 330 sobre unas 36.000 variantes). `calc-studies-b.md` lo dejó para la revisión de motores; `calc-engines.md` no lo recoge como hallazgo.

## Tests de regresión que faltan

Fusión de las cuatro secciones «Regression tests worth having». Los hallazgos entre paréntesis remiten a esta revisión.

| cálculo | fichero | ¿hay test de respuesta conocida? | test propuesto (entrada → salida esperada, tolerancia) |
|---|---|---|---|
| PSR, MinTRL, máximo esperado, DSR | `core/significance`, `core/surface/plateau` | Sí — `tests/test_inference_vs_jsharpe.py` (72 series contra salidas guardadas de jsharpe), `tests/test_significance.py` | Añadir el caso N = 1 (m5): `expected_max_sharpe(s, 1) == 0.0`; DSR = `psr(returns, 0.0)` a 1e-12 |
| Benjamini-Hochberg | `engines/inference/fdr.py` | No — ningún test lo importa (`discoveries` tampoco) | `adjusted` vs `scipy.stats.false_discovery_control` sobre 48 p fijos, 1e-12; `discoveries == {q <= alpha}`; empates; el caso NaN de M1; ejemplo de libro de 5 p |
| p empírico | `engines/nulls/verdict.pvalue` | Solo indirecto (`tests/test_nulls_seed.py` comprueba reproducibilidad, no el valor) | `pvalue(4.5, arange(10.), "sharpe") == 6/11`; lado `"dd"` `== 6/11`; `seen` sobre todas las muestras → `1/11`; NaN → NaN; exacto |
| Estadísticos por corrida | `engines/nulls/kernel.runs`, `stats.measure`, `placement/kernel.batch` | No hay test unitario (solo `monkey.verify`, que necesita un export real) | Caso a mano: precios con P/L = (−100, +50, +10), coste 0 → net −40, sharpe −40/3 / std(ddof=1) = −0.171656, pf 0.6, dd 100, retdd −0.4; `kernel.runs == stats.measure` a 1e-12; los mismos tres por `batch` con `equity0` 10.000 → dd_pct 0.01 (m1) |
| Colocación aleatoria | `engines/nulls/model._place` y los cuatro peldaños | No | Ventana (0, 10), hold 3, semilla fija: soporte exactamente 0…7 y uniforme; cada peldaño: `entries + holds <= hi`, tamaños de `timing_sizing` todos iguales a `size.mean()`, holds de `timing_holds` ⊂ los holds reales (m3) |
| Drawdown de placement en orden temporal | `engines/nulls/placement/kernel.py` | No | Tres trades con orden de columna (−60, +100, −60) y entradas en orden temporal (+100, −60, −60): dd esperado 120 y `worst_run == 2`; orden de columna da 60 y 1 (m25) |
| Generadores de índices | `engines/resample/draws.py`, `placement/bootstrap.block_rows` | No hay test directo | `block_shuffle(…, 23, bloque 5)`: cada fila es permutación de 0…22 y dentro de cada bloque las posiciones son consecutivas; `stationary(400, 2000, bloque 10)`: longitud media de racha 10 ± 0.5 (medido 9.91); `block_bootstrap`: todo bloque de 7 consecutivo mod tamaño; `block_rows` concatenado igual a `block_bootstrap` con la misma semilla |
| Pooling del ledger | `ledger/trials.accumulated` | Sí para dos filas de la misma unidad (`tests/test_ledger.py:87-98`) | Añadir la fila n = 1 (m6) y el frame de tres unidades (M2): sigma = std ddof=1 agrupada, `n == 5140`, sin excepción, 1e-9 |
| ATR | `engines/market/atr.sqx`; `calibrate.atr`; `regimes.atr` | `atr.sqx` sí (`tests/test_atr.py`, reproducido a mano: 1, 1.75, 1.833333, 1.722222) | `regimes.atr` + `tag`: el caso del día pico de m4 (2.0 / ≈ 4.714, 1e-9); `calibrate.atr(window 3)` sobre cuatro barras → NaN, NaN, mean(TR[0:3]), mean(TR[1:4]) |
| Remuestreo de barras | `core/barstore.read` | Comprobado una vez a mano contra el export M30 de SQX (docstring), sin test | Seis barras M1 09:58…10:03 → dos barras M5 etiquetadas 09:55 y 10:00 (hora de apertura, cerradas por la izquierda), H = max, L = min, C = último, un contenedor vacío descartado |
| edgeCost: spread embebido, long y short | `studies/readings/edgeCost/spread_share.measure` | No — `tests/test_edgecost.py` esconde `measure` con una constante; ningún caso Sell lo alcanza | Test de M3: Buy y Sell sobre barras planas → 0.04 ambos, 1e-9 |
| Gate `familia` (BH tras criba de p) | `studies/screening/gate/monkey.py` | No | Test de M4: 1000 p uniformes, `max_p` 0.05, alpha 0.05 → nombra ≤ 1; más `discoveries` sobre el ejemplo de libro de 5 p |
| Lo (2002) t, t de trade y su gemelo AR(1), deriva, riesgo flotante en R | `studies/screening/gate` (`measures`) | Sí — `tests/test_gate_measures.py` (cuatro tests) | Añadir el caso split-no-en-índice (m12) |
| Reprecio del spread: long paga en entrada, short en salida, slippage en ambos fills | `studies/data/spread` (`reprice`, `_task_costs`) | Parcial — `tests/test_spread.py` tiene un Buy y un Sell | Añadir `_task_costs`: spread 1.61 puntos × tick 0.01 → 0.0161 en precio (la guarda del factor 10) (sesión de spread) |
| Buy and hold de riesgo igual y panel SPA/StepM | `snoopingScreen`, `blindJoint` | Sí — `tests/test_snooping.py`, `tests/test_blindjoint.py` | Ninguno |
| Exposición: ocupación, `presence`, `daily`, `equal_risk` | `studies/closing/exposure` | No — ningún test lo importa | Tests de m9 y m10; una operación sobre 3 de 10 barras → `share == 0.3` |
| Stop ATR: barra anterior a la entrada, percentil X y su intervalo bootstrap | `studies/closing/atrCalculator` | Sí — `tests/test_atrcalculator.py` | Ninguno |
| p de alarma de feedQuality (+1, unilateral) y `touch.hits` | `studies/data/feedQuality` | Sí — `tests/test_feedquality.py` | Ninguno |
| Rango del MC Retest | `onboard.mc_range`, `verdict.mc_multiples` | No | Base 1.0, k {0.9, 1.1}, grano 0.1, min_steps 10 → (0.5, 1.5); base 0.2 → extremo bajo recortado a 0 y banda de 1.0 de ancho (m30) (sesión de spread) |
| PSR de mcRetest | `evidence.analytic_sharpe` tal como lo llama `run.py` | No — `test_mcretest_one.py` no fija su entrada | 500 operaciones N(2, 100), semilla 0, benchmark 0 → PSR igual a `core.significance.psr` de esas operaciones ±1e-9, y `< 0.99` (C1) |
| Puerta de ruido SPP | `studies/breakage/spp/verdict/noise.py` | No hay test | 10.000 iid N(5, 1) → "noise"; lo mismo más una cresta de 3 sigma con 200 vecinos → "proceed" (C2) |
| Sharpe `real_from_trades` de SPP | `studies/breakage/spp/model/combine.py` | No hay test | Operaciones por día hábil durante 52 semanas → media/sd·√252 de la serie de días hábiles, 1e-9; una estrategia real a ±2 % del `SharpeRatio` de SQX (M5) |
| Subdeterminación del sustituto local de cloud | `studies/optimisation/cloud` | No hay test | Vecindario n = 1 y n = 20 con k = 7 → estado `none`, sin «plateau»/«smooth» (M6) |
| CSCV PBO | `studies/optimisation/cscv` | Sí — `tests/test_cscv.py` | Añadir: N columnas idénticas → PBO 0.5 ± 0.02 en empates; una columna dominante → PBO 0 |
| Reconstrucción de mcRetest | `recon`, `drawdown._reduce` | Parcial — `test_mcretest_footprint.py`, `test_mcretest_one.py`, sin simulación vacía | Offsets [0, 2, 2, 3] → NetProfit [50, 0, 200], sin inf (m14) |
| crossTF `beyond` (`z_new`, z combinado) | `studies/transfer/crossTF/cells.py` | No — `test_crosstf_{facts,report,separate}.py` no lo fijan | z 2, madre 2, rho 0.5 → `z_new` 1.1547 ±1e-4; dos hermanas 1.0 y 2.0 → combinado 2.1213; rho 0.99 recortado a 0.95 (m18) |
| Drawdown y denominador de amplitud de crossmarket | `studies/transfer/crossmarket` | No — `test_crossmarket_*` cubren contrato, exceso, short, tarea | `observed([-100, 50, 30], 10000)["dd"]` → 100; 1 superada de 1 valorada con 15 missing → DESCARTAR (m1, m23) |
| wfc rho e intervalo; wfm Fisher-z agrupado y Sharpe por celda | `studies/optimisation/wfc`, `wfm` | No (sin cobertura) | Intervalo n = 103, rho 0 → 0.2018 en z (m22); cuatro operaciones de m17 → 10.35 ± 0.01 |
| Suelos diario y máximo, ruptura estrictamente por debajo | `portfolio/funded/rules/floors.py` | Sí para límites positivos (`test_funded_rules.py` 1-5); **No** para 0 / NULL | Test de C3 (`daily_loss=0.0` con `low = -1` no es `fail`, ambas bases) |
| Inicio de etapa con flotante abierto | `machine`, `account`, kernels | «phase2 starts fresh» (caso 10) solo con flotante plano; **No** hay caso de trade arrastrado | Los dos caminos de M8, referencia == kernel |
| Kernel == referencia, caja del banco (precio, reembolso, reparto, payouts, presupuesto) | `test_funded_sim.py` 1-7, `test_funded_bank.py` 1-2 | Sí | Mantener; añadir un camino con `daily_loss = 0` |
| Mejor GA / estancamiento | `portfolio/common/construct/search/genetic.py` | Clique plantado solo con puntuaciones finitas; **No** hay caso NaN | Test de M7 |
| Tabla de días de servidor: E0, low/high, Σ diaria = Σ P/L, corte EETUS, DST | `equity/days.py`, `clock.py` | Sí (`test_portfolio_mtm.py`, USDJPY dorado); **No** hay trade del mismo minuto | Test de m20 |
| Bootstrap estacionario de días y liquidación de costura | `mc/paths.py`, `lay.py` | Sí — `test_portfolio_mc_paths.py` (serie constante, longitud media de bloque, MTM conservado, ningún flotante sobrevive a su bloque) | Suficiente |
| Estadísticos de MC de operaciones y estreses de Familia C | `simulate/metrics.py`, `kernel.py`, `model/stress.py` | **Ningún test de respuesta conocida**: `test_montecarlo_one.py` revisa ficheros, `test_montecarlo_oos.py` solo que Familia E lee OOS | Nuevo `tests/test_montecarlo_known.py`: (a) pnl `[−100, −100, +50]` → net −150, dd 200, dd_pct 0.02, pf 0.25; `kernel.priced == metrics.paths`; (b) cada estrés en su mando neutro (`p_skip 0`, rangos `[1, 1]`, `fill_frac 0`) devuelve `pnl` exacto; (c) `cost_shock` a `[2, 2]` → `pnl − cost`, `spread_widen` a `[2, 2]` → `pnl − spread` (M9, m1) |
| Deals worth: barrera `p = b / (a + b)` y coste por 1.000 fondeados | `portfolio/funded/deals/worth.py` | No hay test | Objetivo 10 %, pérdida máx 10 % → p 0.5 por fase, 0.25 para dos; precio 100, size 10.000, sin reembolso → `_per_k = 100 / 0.25 × 1000 / 10000 = 40`; con reembolso → `(400 − 100) / 10 = 30`. Exacto |
| Perfil de mercado: fills en la siguiente apertura, D1 de día cerrado, solo build, espejo | `test_marketprofile.py` | Sí (orden de medias, familias, veneno de build, cuarto filtro, reloj); la simetría del espejo solo implícita | Una línea: toda medida long sobre `mirror(mirror(d))` igual a la de `d`, y long sobre `mirror(d)` de una serie igual a short sobre la serie negada |

## Comprobado y correcto

Motores y núcleo (`calc-engines.md`)
- **PSR / MinTRL** (`core/significance.py:94-143`): z = (SR − SR*)·√(n−1) / √(1 − γ₃SR + (γ₄−1)/4·SR²), kurtosis cruda, Sharpe ddof=1; reproducido a 16 dígitos contra la forma cerrada.
- **`annual_sharpe`** (`:146-164`): rejilla de días hábiles, relleno de ceros, cierres de fin de semana rodados al lunes, √252 sobre datos diarios; reproducido a mano (14.6969).
- **`footprint`**: ley de la varianza total como se documenta; unidades coherentes con la escala de sus llamantes.
- **Benjamini-Hochberg** sobre p finitos: step-up, regla del mayor k, q ajustada monótona; igual a scipy a 2e-16.
- **π₀ de Storey, `resolution`**: suelo 1/(draws+1), `draws_needed = ceil(1/bar) − 1` correcto.
- **SPA / StepM** (`snooping/superior.py`): signo de la pérdida (−exceso frente a benchmark cero), una longitud de bloque conjunta, misma semilla por ronda step-down que hace `arch`.
- **Máximo esperado / fórmula DSR** para N ≥ 2: Bailey–López de Prado con pesos de Euler–Mascheroni.
- **Clustering de ensayos** (`core/surface/trials.py`): distancia √((1−ρ)/2), silueta de singleton 0, regla de la mitad.
- **`shift.py`**: Hodges–Lehmann con la diagonal (i ≤ j), δ de Cliff = 2U/(nm) − 1 (0.5556 a mano), √(n_before/n_after) de la razón de dispersión del lado correcto.
- **Pooling exacto de momentos** (`ledger/trials.py`): igual a la std ddof=1 directa (0.0502203792…).
- **Corrección +1** en `verdict.pvalue` y `filter.benchmark`: (1 + #≥)/(draws + 1), lado bueno por estadístico (`dd` bajo).
- **Semillado** (`simulate.nulls`): `SeedSequence([root, blake2b(key), rung id, block])` — independiente del proceso, de la composición del lote y de `draws`; ningún flujo reutilizado entre estrategias o peldaños; raíz fresca de 32 bits registrada. `semester_shift` indexado por calendario y continuado entre chunks vía `batch`.
- **Sharpe de la escalera** ddof=1 en `kernel.runs` y `stats.measure`; `filter.py` usa ddof=0 en ambos lados de su propia comparación a n fijo — coherente.
- **Generadores de índices**: `block_shuffle` conserva el multiconjunto; `stationary` con probabilidad de reinicio 1/bloque y wrap (bloque medio 9.91 para 10); `block_bootstrap` marginal uniforme (χ² p 0.92).
- **`_lay`, `cut_at_next`, `_drop_overlaps`, `truncate`**: offsets con el hold del trade previo; wrap y overrun ponen el hold a cero; la dispersión de vuelta mantiene columna k = trade real k.
- **ATR de SQX** (`engines/market/atr.py`): el divisor crece 1…período y luego Wilder; el primer TR es high−low.
- **Calidad de feed** (`feed/scale.py`, `spikes.py`, `runs.py`, `session.py`): la escala semanal lee solo semanas [w−weeks, w) — sin look-ahead; los retornos a través de un minuto ausente son NaN; aritmética de rachas congeladas y gaps exacta; ORIGIN 2003-01-06 es lunes.
- **Barras** (`core/barstore.py`): el remuestreo etiqueta la barra por su hora de **apertura** (left/left de pandas por defecto para estas reglas), contenedores vacíos descartados; caché por la huella del M1. Las velas diarias de XAUUSD no tienen día de fin de semana (solo lun-vie).
- **Frontera IS/OOS** (`engines/variants/panel.py:174`): `< boundary` en muestra, `>= boundary` fuera, boundary = el primer día declarado del propio segmento, no el calentamiento de la pata; periodo final descartado.
- **`core/trades.cost`**, **`calibrate.charged`**: bruto menos P/L reportado con el lado aplicado.
- **`core/commission.commission_pct`**: $/lote sobre precio × valor del punto × 100.
- **`core/tickfile`**: spread ponderado en tiempo cierra cada minuto en su propio final; sin división por cero.

Estudios: cribado, lecturas, cierre, datos (`calc-studies-a.md`)
- **Ningún factor 10 en el camino del spread.** Todo spread de SQX está en unidades de `instrument.tick_size` en `measure.yearly` (`spread_open / tick`), `verdict.propose`, `onboard.plan`, `inputs._task_costs` (`spread × tick`), `edgeCost/costs.py:93`. Contrastado con fills reales: spread de tarea de AUDJPY 1.61 puntos × 0.01 = 0.0161, slippage 0.0081, y el offset de entrada medido del long es 0.0240 = 0.0161 + 0.0081 a la fracción de pip. USDJPY `spread_is` 0.49 puntos = 0.49 pip.
- `fundedswap`: USD por lote por noche desde puntos MT5, % anual sobre nocional (×36000), puntos SQX por `pointValue × tickStep`, y «peor» = el más negativo.
- La equity de harvest es densa: 0 celdas NaN interiores en 5.0 M y 17.1 M filas, así que el `diff` del pivot no pierde nada (el doble diff solo deja en blanco los dos primeros días, ambos planos: perdido 0.00).
- `sample` y `Sample type` coinciden exactamente (IS ↔ IST, OOS ↔ OOS1) en ambos harvests; `Type` es `Buy` / `Sell` como esperan los mapas de dirección.
- Error estándar de Lo (2002) y su invarianza a la constante de anualización; n efectivo AR(1) en `tradelevel.t`; `floating.table`.
- profitShape: momentos del test de rachas, CUSUM, p de `streak` con +1; Ljung-Box sobre días naturales con fines de semana planos mantiene su tamaño (iid de días hábiles: 4 % de rechazos al 5 %, igual que solo días hábiles).
- feedQuality: p de alarma `(1 + #≥) / (B + 1)`, subconjuntos sin reemplazo, semilla desde la identidad; aritmética de intervalos de `touch.bars` y `hits`; `summary.stability` y `episodes` (desplazados, sin look-ahead).
- atrCalculator: `before_entry` para entradas on-open e intrabarra, bootstrap percentil sobre sorteos compartidos, drawdown de `stats` desde cero, desplazamientos de barra de `proofs.atr`.
- blindJoint y snoopingScreen: dimensionado de riesgo igual, último día descartado, semilla fija 0, ventana `[start, end)` desde `core.assetdata.window`.
- conditionalMap: retardo de un día del régimen diario, conversión de sesión EETUS; structure: nula de subconjunto sin reemplazo, +1 en p.
- Modelos de spread: ajuste log con smearing, validación en dos sentidos, `reconstruct` medido-sobre-modelado.

Transferencia, rotura, optimización (`calc-studies-b.md`)
- **cscv:** C(16,8) = 12.870 particiones; Sharpe por momentos de bloque (ddof = 1) idéntico al por filas; omega = (rank + 1)/(n + 1) y su logit; empates rankean más bajo (conservador); PBO = P(λ ≤ 0); dirección de dominancia de segundo orden; DSR por periodo con kurtosis cruda y ddof = 1.
- **wfc:** Spearman con la guarda de varianza cero; composición del split leída de `engines/variants/config.yaml`.
- **wfm:** geometría de ventanas y descarte de pasos más allá del final de la historia; Spearman por celda agrupado por Fisher-z con bootstrap sobre celdas; regla de puerta (redondeo half-up, regla del área); `benchmark.daily_pnl` suma exactamente a las operaciones (67.907,13 = 67.907,13); beta, bootstrap estacionario pareado, semilla fija; `max_dd` con inicio cero.
- **marketSurfaces:** Spearman, rho neutral a la exposición, banda de azar hipergeométrica, `p_overlap = sf(x − 1)`, dedupe.
- **cloud:** índices de Sobol (Saltelli primer orden, Jansen total), persistencia y centroides.
- **mcRetest:** recuentos, drawdown y fórmulas de corrida cuadran con SQX; intervalo de estadístico de orden de cola; CVaR; δ de Cliff; step-up de Benjamini-Yekutieli.
- **spp:** eta², test de duplicado, plateau; signo de GrossLoss.
- **crossTF:** `z = (seen − media nula)/sd nula` con ddof = 1; álgebra de `z_new` y recorte [0, 0.95]; z combinado = suma/√n; corte oos1 sobre hora de apertura; clave de semilla por celda `strategy|block`.
- **crossmarket:** intervalo de Fieller (centro, semianchura, g ≥ 1 → no acotado); barras ocupadas `entry..exit−1` frente a retornos cierre-a-cierre bajo la convención apertura-a-apertura; bootstrap ponderado por hold de A; signo del lado short en retornos, deriva, benchmark y valoración; t con n efectivo AR(1); binning `weekly` de viernes (1970-01-01 es jueves); `daily_sharpe` igual a `annual_sharpe`; ratio de participación; `half` = el ceil(n/2)-ésimo mayor; p nulo conjunto con +1/+1; ventana recortada a primera entrada-última salida antes de cualquier nulo o deriva.

Fondeo, carteras, investigación (`calc-portfolio.md`)
- **Máquina de reglas:** suelos por firma, bloqueo del trailing en `size`, high-water subido antes de comprobar el low, ruptura estrictamente por debajo, objetivo sobre balance cerrado, días mínimos / días rentables, ambas fórmulas de consistencia; los kernels numba coinciden con la referencia y entre sí.
- **Banco:** precio, reembolso, reparto, colchón, ciclo de payout (`payout_days × dpy / 365`), parada por presupuesto, re-compra, bloqueo tras el primer payout, payouts denegados y cierre de firma como peligro geométrico diario; intervalo de EV. `haircut.apply` baja `low` solo donde el nuevo cierre cae bajo él.
- **Deals:** `p = Π b/(a+b)`; el reembolso acreditado al pasar está dicho en la nota impresa.
- **Reconstrucción de equity:** EETUS = Nueva York + 7 h con NaT de DST tratado; `E0`, `low`, `high` relativos al inicio del día; Σ diaria = Σ P/L; bloques M5 frente a lows M1 exactos.
- **Dimensionado:** álgebra de `f = atr_multiple / (risk_usd · x)`; escalado `r · size` de la etapa A y factibilidad de lote mínimo (`min_lot_unit · r · size < min_lot / 2`).
- **Pares / grafo admisible:** Pearson y Spearman, mensual y diario, co-pérdida, cola, 60 m móvil solo con ≥ 60 meses, mínimo de solape, regla |ρ| bilateral; fórmulas de N efectivo.
- **Monte Carlo de carteras:** índices de bootstrap estacionario, liquidación de costura, flotante arrastrado en `lay._lay`, colocación T1/T2, una semilla por camino y por worker (sin reutilización), percentil de rango medio de la nula, la nula busca tanto como la búsqueda real.
- **MC de operaciones:** sorteos vía `engines.resample`; ventanas en meses naturales, medias ventanas descartadas; Familia E solo sobre operaciones OOS, benchmark desde la ventana propia de las operaciones; las corridas sin semilla están documentadas y valoradas por `stability.py`; `cost_shock` resta solo el incremento; el crosscheck de comisión usa ida y vuelta (2 × por lado).
- **Segmentos:** todo fin de build en `assets/_policy.yaml` es límite de año, así que m34 no filtra hoy.
- **`studies/research/marketProfile`:** señales sobre la barra cerrada, ambos fills en la siguiente apertura (`trades.after`, `position.walk`: tope, trailing, stop); canales y ATR retardados una barra; valores D1 leídos un día cerrado tarde y `d1_open` desde la primera barra del día; `mirror` cubre toda serie con signo, los canales intercambiados, RSI e IBS; las comparaciones `d1_above` (SMA sobre SMA, banda 1 %) leen en el sentido correcto; la mejor hora/banda/día de semana paga su elección dentro de cada sorteo nulo; p cuenta el estadístico real; las medidas no testadas reciben p = 1 y permanecen en la familia BH; coste por operación = spread + 2 × slippage (puntos × tick) + comisión ida y vuelta (el valor por lote ya es ida y vuelta; % del nocional cobrado una vez), en unidades de precio; corte solo-build antes de remuestrear.
- **Barrido:** misma nula, su propio BH, cola normal solo bajo el suelo contado, vecinos de plateau.
- **`profilePower`:** el edge plantado suma exactamente `effect` costes por operación en barras `[entry, exit)`; la parada temprana no puede convertir una no-detección en detección; error analítico `|múltiplo / t| × sd_nula`.
- **`pooledProfile`:** suma de Stouffer sobre activos testados frente a sorteos remuestreados conjuntamente (semilla por grupo, no por activo); τ² de DerSimonian-Laird, I² y encogimiento; rangos de placebo.
- **`board` / `memory`:** posterior Beta encogido hacia la tasa agrupada, freno y factores de hueco, auto-chequeo Fisher unilateral, conteo de ensayos por fichero de idea (una vez por fichero).
- **Notas de `calc-engines.md` que no son hallazgos:** (1) el README de `engines/nulls` «la dirección no se modela … un short se valoraría con el signo equivocado» está **desactualizado en el sentido seguro**: `calibrate.point_value` es una pendiente ajustada, así que una estrategia todo-short recibe valor negativo (sonda `[M]`: −100.18) y `kernel.runs` la valora bien; solo una mezcla de ambos lados se rompería, lo que la regla 13 prohíbe. (2) Docstring de `calibrate.atr`: «los primeros `window` son NaN» — son `window − 1` (sonda `[L]`); `studies/readings/entryQuality/inputs.py:162` lee `scale[entry - 1]` y un trade en la barra 0 daría la vuelta al ATR de la **última** barra; fuera de alcance, inalcanzable en la práctica. (3) `ledger/report.py:14,100` convierte un Sharpe anualizado de SQX por `/sqrt(252)`; que SQX anualice retornos diarios por √252 se asume, no se demuestra; la única fila así en disco (σ 0.3506 → 0.0221 por día) concuerda con la σ por día de la misma población (0.0184), así que es plausible. (4) `core/significance.variance_factor` no puede ser negativo: para toda muestra, kurtosis ≥ skew² + 1 con los momentos poblacionales que usa `moments()`, así que el cuadrático en SR no tiene raíz real. (5) `core/study/config.fingerprint` hashea la semilla `nulls.seed` fresca ya resuelta, así que dos corridas de la misma config nunca comparten hash; contabilidad, no aritmética.

## No revisado

- **Spread / feedQuality, sin leer línea a línea** (`calc-studies-a.md`): feedQuality `calibrate.py`, `inject.py`, `feed.py`, `scan.py`, `one.py`, `many.py`; spread `asset.py`, `band.py`, `bands.py`, `registry.py`, `one.py`, `report.py`. De `studies/data/` solo se leyeron a fondo, en feedQuality, alarm, calendar, detect, inputs, summary, touch y, en spread, fundedswap, inputs, measure, model, onboard, reprice, scan, verdict. Por tanto la ausencia de un factor 10 no cubre esos módulos.
- **`engines/` en los informes de estudios y portfolio:** `calc-studies-b.md` y `calc-portfolio.md` no revisaron `engines/`, solo cómo lo llaman los estudios (`calc-engines.md` sí lo cubre).
- **Fuera del alcance de `calc-engines.md`:** todo salvo `engines/` (inference, market + feed, nulls + placement, regimes, resample, variants), `ledger/`, `core/surface/`, `core/study/` (blocks, clip, config, verdicts, blockcheck), `core/significance.py`, `core/bars.py`, `core/barstore.py`, `core/trades.py`, `core/commission.py`, `core/tickfile.py`, `core/sqxstats.py`. Todo fue de solo lectura.
- **Sin revisión en profundidad** (`calc-portfolio.md`; sin decisión numérica, o script de experimento): `studies/research/literature/` (búsqueda, dedupe y anclas); `marketProfile/blocklen.py`, `favourable.py` (texto de calificación), `familias.py`; módulos de informe y de store.
- **No medido en datos reales:** M2 (a/b: ningún ledger real lleva aún una fila p_pass); m10 (cuántas veces muerde); m26-m36 y las demás sospechas solo por lectura; m18 y m23 con efecto probablemente pequeño sobre datos reales; el cuerpo de datos de la sospecha de M1 (existencia de una columna IS constante en un export).
