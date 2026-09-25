# Acceptance conditions — reading them correctly

🔬 **Three shapes exist, not two.** A parser must handle all of them — `core/cfx.py` does:

```xml
<!-- acceptance conditions -->
<Condition use="true">
  <Left-Side><Column-Value column="ProfitFactor" resultType="WalkForwardMatrix" subresult="30"/></Left-Side>
  <Comparator value="&gt;"/>
  <Right-Side><Numeric-Value value="1.20"/></Right-Side>
</Condition>

<!-- GoToTask conditions - completely different -->
<Condition type="ResultsCount">
  <Field type="databank">Retest Markets - OOS</Field>
  <Field type="comparator">&lt;</Field>
  <Field type="number">1000</Field>
</Condition>
```

**Third shape, found 2026-09-03**: 🔬 the right side can be a `Column-Value` too, not only a
`Numeric-Value`. SPP tasks use it to compare a permuted result against the strategy's own main result:
`NetProfit(OptProfileSysParamPermutation) >= NetProfit(main)`. A parser that assumes `Numeric-Value`
on the right crashes on the XAUUSD WFM and SPP tasks.

- 🔬 **`use="false"` conditions stay in the file.** Always check the attribute — a threshold in a
  disabled condition gates nothing.
- 🔬 Counted 2026-09-03 with `core/cfx.py` across the whole XAUUSD project: **138 `Condition` elements
  in 16 tasks, 101 of them active**, counting every nested crosscheck block. The Build task alone
  holds 49, of which 24 are active. An earlier note claiming 13 conditions in the Build task was
  counting only one block of them.
- 🤔 **`subresult=30` is the raw metric; `subresult=31` appears to be a percentage of matrix
  combinations passing.** Inferred from its pairing with `format` (`Decimal2` vs `Decimal2Pct`). It is
  what makes `ProfitFactor >= 60` sensible rather than absurd. **Not confirmed** against SQX's enum
  table.
- 🔬 `sampleType` **is** decoded: **10 = IS, 20 = OOS, 127 = full period** (see `04-export.md`).
  `plType` (10, 20) is still undecoded.
- 🔬 Watch for a condition reading `resultType="WalkForwardOptimization"` inside a task where that
  cross-check is `use="false"` — XAUUSD's WFM task does exactly this.

### 🔬 Every active condition of a donor task lives inside `<CrossChecks>` (2026-09-23)

Counted on the frozen donor with `ElementTree`, per task: **13 active in the WFM task, 19 in each
SPP task, 20 in an MC Retest task — and in all three, every single one is inside the
`<CrossChecks>` element.** The task's own top level carries none.

Two consequences for anything that configures a task:

- Silencing a study's acceptance means silencing `<Condition use="true">` across the **whole task**,
  not only inside the cross-check being enabled. Several of those conditions belong to cross-checks
  the task does not even run (a `WalkForwardMatrix` condition sits inside `WalkForwardOptimization`,
  which is `use="false"`), and nothing says whether SQX evaluates them. `sqx/projects/crosschecks.py`
  turns them all off and reports the count.
- A count of `0` silenced on a freshly cloned project is a **tell**, not a success: the clone did not
  come from the donor, or someone already edited it.

🔬 **What makes it a matrix is the ELEMENT, not `type`.** A `<WalkForwardMatrix>` writes
`value="undefined"` plus `start/stop/step` on both `Param1` and `Param2`, and the cell count is the
product of the two ranges — 5 × 6 = 30 on the owner's task; the `<WalkForwardOptimization>` beside
it carries a single `value` each.

⛔ **Corregido 2026-09-24: `type` NO significa "matriz contra walk-forward suelto".** Eso estuvo
escrito aquí y era falso — la prueba está en el propio install, donde un `<WalkForwardMatrix>` de un
proyecto stock lleva `type="1"` **con rangos**. `type` es el desplegable "Walk-Forward type" de la
GUI, y su enum sale de `OptimizationConst.wfTypeToString`:

| `type` | lo que dice la GUI | qué hace (🔬 `OptimizationEngineWF`) |
|---|---|---|
| 0 | Simulated IS, Simulated OOS (fastest) | ni IS ni OOS se vuelven a correr: las órdenes se recortan de un único backtest ya calculado (`runSimpleSimulationRun`) |
| 1 | Simulated IS, Exact OOS (slower) | cada pasada fuera de muestra se vuelve a backtestear de verdad con los parámetros de ese paso (`testStrategy(..., runFrom, runTo)`); la optimización sigue recortando. **Default de SQX** |
| **2** | **Exact IS, Exact OOS (slow)** | también la optimización de cada paso es real sobre su ventana, así que el ganador no sale de recortar una tanda única. **El del proyecto** (dueño, 2026-09-24), y lo que ya llevaba la WFM corrida del maestro |

🔬 Lo que cambia el lado IS no son los decimales: es **quién elige los parámetros de cada paso**.
Con `simulated`, el ganador sale de recortar a la ventana del paso una única tanda de backtests
sobre el rango entero, y ese recorte arrastra el camino de la equity —con sizing por ATR sobre el
balance corriente no es neutro— y los trades abiertos antes del borde. Con `exact`, cada paso
optimiza de verdad sobre su ventana, que es lo que se haría en vivo. Leído en el `lastSettings.xml`
de `XAUUSD/databanks/WFM`: la WFM del maestro corrió con `type="2"`, `MaxTests` 500, precisión 2,
30 celdas sobre cinco años, y terminó.

`period` y `optimization`, en el mismo elemento, tampoco están sin decodificar: son el tipo de
periodo (`percent=10`, `days=20`, `bars=30`) y el de optimización (`floating=15`, `fixed=25`).

### Which window a strategy was selected on — read it before calling anything out of sample

🔬 Measured 2026-09-17 on `XAUUSD/project.cfx`, `Build-Task3.xml`, counting only `use="true"`
conditions: selection touches **every** window of the sample, not just the in-sample one.

| resultType | sampleType | active conditions |
|---|---|---|
| `main`, `WhatIf`, `RetestWithHigherPrecision`, `MonteCarloRetest` | 127 (full 2008–2022) | 8 |
| `WalkForwardOptimization`, `MonteCarloManipulation` | 10 (IS) | 10 |
| `WalkForwardMatrix` | 20 (OOS) | 2 — `NetProfit > 0` |
| `RetestOnAdditionalMarkets` | 127 | 1 — `ProfitFactor > 1.5` |

Two consequences for any study that wants a clean out-of-sample test:

- The 2018–2022 stretch is **not virgin data** for a databank built by this task. It enters selection
  twice: inside every `sampleType=127` condition, since the full period contains it, and explicitly
  through the walk-forward matrix's OOS net profit. 🔬 Measured on the 30-strategy sample of
  `Retest Markets - Family`: **30 of 30 are profitable on gold over 2018–2022** — the shape a
  selected window has, not the shape an unseen one has.
- The additional markets of a retest can be a selection filter too, through
  `RetestOnAdditionalMarkets`. Check which task wrote the databank being analysed before reading a
  cross-market result as untouched evidence.

🔬 **Where the untouched data starts: 2023-01-01.** Every `dateTo` in the build and retest tasks is
`2022.12.31`, so no condition in the project has ever read a bar after it, while the bar files run to
2026-01-16 (XAUUSD, XAGUSD) and 2026-06-01 (BRENT). A retest over 2023-01-01 → today is the only
window of this project that is out of sample in the strict sense, for the base asset and for the
additional markets at once.

A p-value computed inside a selected window is still a valid statement *about that window's
mechanics* — e.g. "the entry timing beats a random placement here" — but it is not a statement about
unseen data, and across a population of selected strategies it is biased low.

### `RetestOnAdditionalMarkets` — one `Setup` per market, each with its own costs and its own timeframe

🔬 Read 2026-09-23 from `Retest-Task4.xml` of the frozen donor
(`AlgoData/projectsBackup/XAUUSD_base_2026-09-21/project.cfx`; a `.cfx` is a zip of per-task XML).

`<CrossChecks><RetestOnAdditionalMarkets>` holds `<Settings><Setups>` with **one `<Setup>` per extra
market**, and a `Setup` is a full test definition, not just a symbol:

```xml
<Setup dateFrom="2008.01.01" dateTo="2022.12.31" testPrecision="2" session="No Session"
       slippage="0" minDist="10" engine="MetaTrader5 (hedged)">
  <Chart symbol="XAUUSD_DukasM1_Infinox" timeframe="M30" spread="8" />
  <Commissions>…</Commissions>
  <Swap use="false" … />
  <MainTestValues timeframe="true" dates="true" precision="true" spread="true" slippage="true"
                  commissions="true" swap="false" session="false" subcharts="false" />
</Setup>
```

Three consequences:

- **A `Setup` can carry a different `timeframe` on the same symbol.** So a cross-timeframe retest
  (H1 built, H4 checked) needs no second project and no second build — one retest task, one extra
  `Setup`. It runs the strategy **exactly as built**: SQX does not rescale indicator periods, so
  this is the *bars-constant* comparison, never the *constant-wall-clock* one. Rescaled parameters
  require fabricating variants, not a cross-check.
- 🔬 **`<MainTestValues>` is the inheritance mask** — confirmed by running it 2026-09-23, one boolean per field: `true` means *take the main
  test's value and ignore the one written in this `Setup`*. The donor has `timeframe="true"`, so its
  `timeframe="M30"` is inert. **Flipping the attribute is what enables the override** — editing
  `<Chart timeframe=…>` alone changes nothing. `swap` and `session` are the two already set to
  `false` here, i.e. the `Setup`'s own values are the live ones.
- **`<AcceptanceSettings>` turns the cross-check into a selection filter**: `<Check>all</Check>`,
  `<MinConditions>`, `<MinMarkets>`, and conditions whose `market="1"` picks *which* `Setup` is
  scored. Leave it `use="false"` when the cross-check is meant as evidence rather than as a gate —
  otherwise the result is no longer untouched (see the section above).


### The cross-market / cross-timeframe check carries no conditions (owner, 2026-09-24)

📓 What the frozen donor actually brings in `Retest-Task3.xml` ("Retest Markets - Family"):

```xml
<AcceptanceSettings>
  <Check>all</Check>
  <MinConditions>2</MinConditions>      <!-- with ONE condition defined: never satisfiable -->
  <MinMarkets>1</MinMarkets>            <!-- one of the extra markets is enough -->
  <Condition use="true"> ReturnDDRatio > 1  (market="0", subresult="30") </Condition>
</AcceptanceSettings>
```

`DeleteFailedStrategies` is already `false` there, but that only protects the INPUT databank; a
live condition still keeps the failing strategy out of the OUTPUT one — the same `Cross Check
filter` mechanism documented for the WFM in `assets/_build.yaml`.

**The decision:** `crossmarket.conditions: []` and `crosstf.conditions: []` in
`assets/_build.yaml`. SQX runs the backtests and nothing else; the verdict is taken in Python and
applied with `/curate`. The reason is not taste: an analysis that never sees the strategies SQX
dropped cannot say which market killed which strategy, and cannot compute a p-value against
anything. `sqx/projects/crosschecks.silence_block()` enforces it on the one cross-check and reports
the count; both commands refuse to run if the doctrine's list stops being empty.

🤔 With zero live conditions `<MinConditions>` and `<MinMarkets>` are left untouched, on the WFM
precedent (zero conditions → score 100 → everything passes). **Unverified for this cross-check** —
check on the first real run that the output databank holds as many strategies as the input, and
write the answer here.

### 🔬 Running a cross-timeframe check — two things measured 2026-09-23

Run on `XAU_crosstf_probe` (custodian, M30 project, 6 strategies, 17 ms each), with two extra
`<Setup>` elements on the **same symbol** at H1 and H4.

- **`<MainTestValues timeframe="false">` is honoured, and SQX names the blocks by timeframe.**
  The retested `.sqx` carries `Results/Main: <feed>_LOM_M30`, `Results/AdditionalMarket:
  <feed>_LOM_H1: …` and `…_LOM_H4: …`, and their daily equity curves differ — one strategy
  returned −1,653 on M30, −8,574 on H1 and −758 on H4. Different backtests, not three readings
  of one.
- ⚠️ **A `<Setup>` without `dateFrom`/`dateTo` fails the whole task**, even when
  `MainTestValues` says the dates are inherited: `Cannot start project … Cannot load settings of
  Cross check 'RetestOnAdditionalMarkets'. Cannot invoke 'String.length()' because 'text' is
  null`. SQX parses the attributes before it reads the mask, so **every field a Setup inherits
  must still be present as an attribute**. The mask decides which value wins, not which exist.
- 🤔 The three blocks report different daily-curve lengths over one declared window (1,312 M30 /
  1,334 H1 / 1,458 H4). Probably first-to-last-trade spans rather than the window, but it is not
  measured; check it before comparing two blocks on anything length-sensitive.

### `MonteCarloRetest` — anatomía de la tarea, y la doctrina que la apaga sin decirlo

🔬 Leído y reescrito 2026-09-23 sobre el `XAUUSD` del maestro (ocho tareas, `Retest-Task5..12`) y
verificado escribiéndolas con `sqx/projects/mcretest.py`.

```xml
<CrossChecks use="true" evaluateAll="false">
  <MonteCarloRetest use="true">
    <Settings>
      <Methods><Method use="true" type="RandomizeSpread">
        <Params><Param key="Min">5</Param><Param key="Max">30</Param></Params></Method> …</Methods>
      <NumberOfSimulations>1000</NumberOfSimulations>
      <MCUseFullSample>false</MCUseFullSample>
      <MCBacktestPrecision>2</MCBacktestPrecision>
    </Settings>
    <AcceptanceSettings>…</AcceptanceSettings>
  </MonteCarloRetest>
```

- 🔬 **`doctrine.apply_doctrine()` apaga este crosscheck en toda tarea sin generador**, porque
  `_build.yaml` lleva `crosschecks.default: []` y `tasksettings.set_crosschecks()` recorre todos los
  hijos de `<CrossChecks>` poniendo `use="false"` al que no esté en la lista. Consecuencia medida: un
  proyecto salido de `sqx.projects.builder` tiene las ocho tareas MCR presentes, con sus nombres y
  sus databanks, **corriendo un retest normal**. No falla nada, no avisa nada, y el databank se llena
  de resultados que no son Monte Carlo de nada. Por eso `mcretest.py` enciende el crosscheck él
  mismo, después de la doctrina, y nunca antes.
- 🔬 **`MCBacktestPrecision` y el `testPrecision` del `<Setup>` son dos cosas distintas.** El del
  Setup es el backtest principal; éste es la fidelidad de las mil simulaciones. El maestro lleva
  Setup 2 y MC 1 en `MCR 1 Bar` y `MCR 5 Params`, y 2/2 en las otras seis.
- 🔬 **`MCUseFullSample` decide la muestra, no la ventana.** Las siete tareas aisladas del maestro
  llevan `false` y un `<OutOfSample showGraph="false" />` vacío sobre una ventana 2008–2017; la de
  estrés lleva `true`, ventana 2008–2022 y `<OutOfSample><Range dateFrom="2018.01.01" …>`.
  `strategies/retest/` lee ese booleano para etiquetar la corrida, así que tiene que decir la verdad
  sobre la ventana que lleva al lado.
- 🔬 **Los ocho títulos son un contrato con Python.** `strategies/retest/inputs/tasks.py` busca los
  databanks por `MCR 1 Bar` … `MCR 8 Stress` y verifica qué métodos corrió cada uno antes de
  escribir nada. Renombrar una tarea en SQX rompe el paso 14 aguas abajo.
- 🤔 **`RandomizeMinDistance` sobre una población a mercado no perturba nada.** La distancia mínima
  es la que separa una orden **pendiente** del precio; sin `EnterAtStop` ni `EnterAtLimit` en la
  población no hay ninguna. Regla del dueño 2026-09-23: esa tarea se configura únicamente cuando el
  build produjo estrategias con stop o limit. Sin confirmar contra el motor de SQX que el parámetro
  sea literalmente inerte — lo que está medido es que la población no lleva esas órdenes.
- 🔬 **Leer qué órdenes lleva una población cuesta 0,2 ms por estrategia** (231 estrategias, 36 MB,
  45 ms): abrir el `.sqx`, leer `strategy_Portfolio.xml` y buscar `key="EnterAt…"`. Diez mil
  estrategias son dos segundos, así que no hace falta muestrear.

🔬 **`tasksettings.set_crosschecks()` apaga de rebote TODA condición de aceptación de todo
crosscheck.** Medido 2026-09-23 comparando el donante congelado (1 condición activa en
`MonteCarloRetest`) con el mismo proyecto recién clonado por `sqx.projects.builder` (0). La causa
es su propio patrón: recorre `re.findall(r"<(\w+) use=\"(?:true|false)\">", bloque)` para encontrar
los crosschecks, y `<Condition use="true">` **también casa** — así que cada condición acaba con
`use="false"` por no llamarse como un crosscheck de la lista. Dos consecuencias:

- Para el MC Retest es justo lo que se quiere, y por eso `mcretest.py` informa de `0 condiciones
  apagadas` en un proyecto nuevo: llega y ya estaban apagadas. Su `silence()` sigue haciendo falta
  para un proyecto que NO haya pasado por la doctrina.
- Para el `RetestWithHigherPrecision` de la tarea Build, que la doctrina sí enciende, significa que
  corre **sin ninguna condición de aceptación**: es evidencia, no un filtro. Puede ser lo que se
  quiere o puede no serlo, pero hoy no es una decisión escrita en ningún sitio — es un efecto
  colateral de un regex.

## La aceptación de la Walk Forward Matrix, decodificada entera (2026-09-24)

Estaba anotado como "no decodificado". Ya lo está: sale del propio install, de
`internal/plugins/CrossCheckWalkForwardMatrix/` (la interfaz) y de `internal/libs/SQTradingLib.jar`
descompilado con el `javap` que trae SQX en `j64/bin`. Lo que sigue es lo que el motor hace, no lo
que parece que hace.

### Dónde viven las condiciones de la matriz

🔬 En `<WalkForwardMatrix><AcceptanceSettings><Conditions …>`, y **sólo ahí**. En el proyecto del
maestro ese elemento está VACÍO (`<Conditions thresholdPct="80" robCombRows="2" robCombCols="2"
robMinComb="0" />`) y las nueve condiciones que parecen suyas cuelgan del `WalkForwardOptimization`
de al lado, que está `use="false"`. La prueba de cuál manda está en el propio `.sqx` que la tarea
produjo: su `SpecialValuesMap` guarda `WalkForwardConditions`, y en las cinco estrategias de
`XAUUSD/databanks/WFM` es el elemento vacío. **Aquella WFM del maestro se corrió sin criterio
ninguno**, y su `FiltersResultFailedReason` dice `Passed` porque con cero condiciones se aprueba
todo — ver la fórmula de abajo.

### Cómo se puntúa una casilla, y cómo aprueba la estrategia

🔬 `WalkForwardResult.computeRobustnessScore` y
`WalkForwardMatrixResult.findBestGroupOfPassedCombinations`:

```
score de la casilla = round(condiciones cumplidas / condiciones use="true" * 100)
casilla aprobada    = score >= thresholdPct
estrategia aprobada = existe un rectángulo robCombRows x robCombCols, deslizado por toda la
                      matriz, con al menos robMinComb casillas aprobadas
```

- Las condiciones `use="false"` **no cuentan en el denominador**. Con cero condiciones activas
  `testedConditions` es 0, el score se queda en su valor inicial **100** y todas las casillas
  aprueban.
- Las filas son los NÚMEROS DE PASADAS (Param2) y las columnas los PORCENTAJES OOS (Param1)
  (`createMatrix`). Un rectángulo 4x4 sobre 6x5 cabe en 6 posiciones.
- Si el rectángulo NO cabe, SQX no avisa: se queda con la casilla de mejor score y la cuenta como
  una sola, así que sólo pasa quien pida `robMinComb <= 1`.
- La casilla central del mejor rectángulo es la "Recommended combination: reoptimizing every X days
  on history of Y days" que enseña la GUI.
- ⚠️ **Con condiciones activas esto FILTRA**: `WalkForwardCrossCheckMethod.checkConditions` pone
  `dismissalReason` y descarta la estrategia (`Cross Check filter in 'WF matrix': Robustness score
  didn't pass.`). Es independiente de `DeleteFailedStrategies`. Para volver al modo mapa,
  `robMinComb: 0` — siempre hay "0 o más" casillas aprobadas.
- 🔬 Bug cosmético de SQX: al imprimir sus ajustes, `MinResults:` lee `robCombCols` en vez de
  `robMinComb`. Sólo afecta al texto del log.

### De dónde sale el número de cada condición

🔬 `WalkForwardCrossCheckMethod.getStatsValue` lee `subresult` (default 30), `direction` (0),
`sampleType` (**default 127**) y `plType` (10), y despacha:

| `subresult` | familia | de dónde sale | ¿mira `sampleType`? |
|---|---|---|---|
| 30 | `WF <métrica>` | el resultado de la celda: `stats(direction, plType, sampleType)`. **20 = las pasadas OOS concatenadas**, 10 = la primera optimización, 127 = todo | **sí** |
| 31 | `WF Stability <métrica>` | `statsStability` | no |
| 32 | `WF Score of <métrica>` | `statsScore` | no |
| 33 | `WF Special …` | `statsSpecial`, y SQX **fuerza** 33 si la columna es una de las suyas | no |

- 🔬 **Stability** (`WalkForwardStability.compute`) = suma de la métrica en los tramos OOS dividida
  por la suma en los tramos de optimización, x100, **excluyendo el último paso** (el que no tiene
  OOS). Si la columna es `dependentOnTradingPeriod` —NetProfit, # de trades, Drawdown absoluto,
  Stagnation— cada suma se divide antes por los días de su tipo, así que compara ritmos, no totales.
  La GUI lo llama "performance in run vs in optimization part".
- 🔬 **Score** (`WalkForwardScore.compute`) = métrica de la WF entera / métrica del backtest
  original (portfolio, sample 127) x100. Responde a "¿reoptimizar mejora o estropea lo que había?".
- ⚠️ **`WFScore` (la columna especial) NO es el Score de la tabla**: devuelve `wfResult.scorePerc`,
  o sea el porcentaje de CONDICIONES cumplidas de esa celda. Dos cosas distintas con el mismo
  nombre.
- 🔬 `resultType` **no es decoración**: `ProjectConfigHelper.getConditions` construye un
  `CrossCheckConditionValue` cuando el nombre es un crosscheck, y ése busca el plugin por ese
  nombre. Ha de ser `WalkForwardMatrix` (o cualquier walk-forward: comparten clase base y todos
  leen el mismo `WalkForwardResult`).

### Lo que NO se guarda

🔬 Ni `scorePerc` ni `passed` se serializan en el `.sqx`: el `MatrixResult` guarda por celda sólo
`param1`, `param2`, `testParams`, `resultName` y los blobs de estadísticas. El mapa de aprobados se
RECALCULA cada vez que se pide (por eso el panel de la GUI manda las condiciones al backend). Como
las cuatro fórmulas están aquí arriba, Python puede reconstruirlo desde `core/wfmatrix.py` sin SQX
— y `WalkForwardConditions` dentro del `.sqx` dice con qué criterio se juzgó aquella vez.

### Calibración: los defaults de SQX no valen sobre esta clase de población

🔬 Medido 2026-09-24 replicando las fórmulas sobre las 150 celdas reales (5 estrategias x 30) de
`XAUUSD/databanks/WFM`, ventana 2018–2022:

| condición recomendada por SQX | casillas que la cumplen |
|---|---|
| `Stability NetProfit > 60` | **1 %** (mediana 8,6 %, máximo 73) |
| `WFPctOfProfitableRuns > 70` | 9 % |
| `WFMaxProfitByRunInPct < 50` | 11 % |
| `WFMinTradesInRun > 20` | 55 % (84 % con 6 pasadas, 36 % con 16) |
| `Stability Drawdown < 130` | 57 % |
| `WFMaxPctDDbyRun <= 25` | 100 % |

La estabilidad del beneficio neto es baja por construcción: el tramo de optimización es justo el
que se eligió por ser el mejor. La del profit factor aguanta mucho mejor (mediana 69 %), que es por
lo que el criterio de `_build.yaml` pide PF donde SQX pedía NetProfit. Los umbrales elegidos y el
porqué de cada uno están en el bloque `wfm:` de `assets/_build.yaml`.
