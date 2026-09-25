# Skills — qué hay, para qué sirve cada una, y qué sobra

Las tablas de abajo **se generan**: `python3 tools/skillmap.py`. Un índice escrito a mano está mal
en dos semanas. Lo que está aquí arriba es lo único que se escribe a mano, porque es juicio y no
inventario.

## Cómo se paga una skill

Dos costes, y se confunden:

- **La descripción está siempre en contexto**, la invoques o no — unos **90 tokens** cada una. Tener
  quince skills cuesta ~1.350 tokens permanentes. Es ruido.
- **El cuerpo se carga entero al invocarla.** Ahí está el dinero, y es la columna `~tokens` de las
  tablas.

Corolario: el número de skills casi da igual. Lo que importa es **cuánto cuerpo irrelevante se carga
en la petición típica**. Una skill de 6.000 tokens que se invoca para hacer un 20 % de lo que
explica está tirando 4.800 tokens y, peor, atención.

## Las familias

| familia | qué cubre | cuándo se invoca |
|---|---|---|
| `strategy-template`, `template-run` | de una idea a una plantilla, y de una plantilla a una construcción en un mercado | autoría (gratis) y ejecución (horas de CPU) — partidas a propósito |
| _(retiradas)_ | las cuatro `analysis-*` — generación, retest MC, Monte Carlo, cross-market — se borraron el 2026-09-22 por decisión del dueño. **Los módulos de Python siguen ahí y funcionan** (`tasks/reports/`, `studies/breakage/mcRetest/`, `portfolio/common/monteCarlo/`, `studies/transfer/crossmarket/`); lo que se fue son las reglas de lectura. Recuperables: `git show <commit>:.claude/skills/analysis-<x>/SKILL.md` | — |
| `export`, `translate` | sacar datos de SQX, y traducir una estrategia a Python | puntual |
| `audit`, `doc`, `perf`, `sync` | mantenimiento del proyecto | puntual |
| `sqx-*` (globales, de sqx-lab) | producto genérico de autoría SQX | **candidatas a retirar, ver abajo** |

## Cobertura del workflow — qué paso tiene skill y cuál no

Los 20 pasos están en `docs/AgentPDFs/WORKFLOW.md`. Cada paso de SQX necesita **un custom project
y su tarea o tareas**; cada paso de Python necesita **leer el resultado y emitir un veredicto**.
Esto dice quién cubre qué, a 2026-09-23.

| # | paso | quién lo cubre | |
|---|---|---|---|
| 2-3 | vocabulario y plantilla | `/strategy-template` | ✅ |
| 4-6 | preflight, custom project, configuración del build | `/template-run` · `sqx/projects/builder.py` | ✅ |
| 7 | retest OOS en SQX | `/template-run`, misma cadena | ✅ |
| 8 | análisis IS/OOS | `/oos-gate` → `/curate` | ✅ |
| 9 | retest crossmarkets | `/crossmarket` · `sqx/projects/crossmarket.py` | ✅ |
| 10 | análisis crossmarkets | `studies/transfer/crossmarket/` | ❌ **sin skill** |
| 10.5-11 | variantes escaladas y retest crossTF | `/crosstf` · `sqx/projects/crosstf.py` | ✅ |
| 12 | análisis crossTFs | `studies/transfer/crossTF/` | 🟡 dentro de `/crosstf` |
| 13 | **MC Retest en SQX** | `/mcretest` · `sqx/projects/mcretest.py` | ✅ |
| 14 | análisis MC Retest | `studies/breakage/mcRetest/` | ❌ **sin skill** |
| 15 | **SPPs en SQX** | `/spp` · `sqx/projects/spp.py` | ✅ |
| 16 | análisis SPPs | `studies/breakage/spp/` | ❌ **sin skill** |
| 16.5 | variantes para el WFC | `/variants` · `sqx/variants/` | ✅ · ⚠️ ver abajo |
| 17 | el WFC | `walkForwardCorrelation/` | ❌ **sin skill** |
| 18 | CSCV | `walkForwardCorrelation/pbo.py` | ❌ **sin skill** |
| 19 | **Walk Forward Matrix en SQX** | `/wfm` · `sqx/projects/wfm.py`; el análisis sigue siendo `studies/optimisation/wfm/` | ✅ la tarea |
| 20 | análisis conjunto ciego de 17-18-19 | — | ❌ **no existe** |

### Los cuatro huecos de SQX eran el mismo hueco, y ya está tapado

`crossmarket.py` y `crosstf.py` hacían lo mismo con distinto crosscheck: **encender el suyo en una
tarea concreta y escribirle su configuración desde `assets/`**. Desde el 2026-09-23 ese patrón
existe también para `MonteCarloRetest` (13), `OptProfileSysParamPermutation` (15 — **el SPP, que NO
es `SequentialOptimization`**) y `WalkForwardMatrix` (19). La cirugía común vive en
`sqx/projects/crosschecks.py`: encontrar la tarea por su título, encenderla con su padre, callar su
aceptación y dejar sólo los parámetros recomendados.

Hacía falta porque la doctrina apaga **todos** los crosschecks fuera de la construcción, a
propósito: encender el que toca en la tarea que toca es un acto explícito, por diseño.

### ⚠️ El paso 16.5 sigue corriendo sobre el `Retester` de serie

`sqx/variants/config.yaml` lleva `execute.project: Retester`. Eso **incumple la regla dura 10**
(dueño, 2026-09-23). Es anterior a la regla, no una decisión contra ella. La migración —crear un
custom project de una sola tarea Retest y poner su nombre ahí— está escrita en la skill `/variants`
y en `OPEN.md` §38; no se ha cambiado el default para no romper en silencio una cadena que hoy
funciona.

### Lo que falta en Python es lo que se retiró

Los pasos 10, 14 y 16 no tienen skill porque sus `analysis-*` se borraron el 2026-09-22. Los
módulos funcionan; lo que falta son las reglas de lectura y, sobre todo, que **emitan el mismo
veredicto de dos columnas** que `/curate` ya sabe aplicar (acordado con el dueño, 2026-09-23).

## Candidatas a retirar

**Las cuatro globales de sqx-lab** (`sqx-custom-block`, `sqx-random-group`, `sqx-strategy-template`,
`sqx-strategy-project`). Son producto genérico: no conocen los defaults del dueño, ni el reparto
conductor/custodio, ni `registry.csv`. Pesan entre 2.700 y 6.000 tokens cada una.

El riesgo no es el gasto, es **el enrutado**: una petición de plantilla puede caer en
`sqx-strategy-template` en vez de en la nuestra, y salir una plantilla que no sigue las reglas de
esta casa. Lo único suyo que hoy se usa son los esqueletos, y esos viven dentro del repo en
`tools/sqx-lab/`, así que desinstalar las skills globales no pierde nada.

**Decisión pendiente del dueño.**

## Cómo leer las tablas

- `~tokens al invocar` — el cuerpo del `SKILL.md`. Si una skill pesa mucho y se usa para poco,
  pártela.
- `ficheros` — más de uno significa que tiene material de referencia que puede cargar a demanda.
  Eso es bueno: es cuerpo que no se paga salvo que haga falta.
- `último cambio` — una skill que lleva meses sin tocarse y describe un flujo que ya cambió es una
  trampa, no documentación.

<!-- generado por tools/skillmap.py — no editar debajo de esta linea -->

Regenerado 2026-09-25 con `python3 tools/skillmap.py`. El coste en tokens es el cuerpo del `SKILL.md`, que solo se carga al invocarla; la descripcion (~90 tokens) esta siempre en contexto.

## Skills de proyecto — `/home/sergioguslw/Desktop/AlgoProject/.claude/skills`

| skill | ~tokens al invocar | ficheros | último cambio | para qué |
|---|---:|---:|---|---|
| `crosstf` | 2,094 | 1 | 2026-09-25 | Test whether a strategy's edge survives being read on a slower timeframe — fabricate period-rescaled siblings, wire a cross-timeframe check into a custom project, run it on the custodian, and read each cell against its own timeframe's null |
| `curate` | 1,904 | 1 | 2026-09-25 | Apply a Python verdict back into SQX — move the strategies a filter, a test or an analysis rejected out of a databank, so the next task in the chain only sees the survivors. Works between any two tasks and with any module that can name what it drops |
| `wfm` | 1,889 | 1 | 2026-09-25 | Configure and run the Walk Forward Matrix task of a custom SQX project — the 30-cell grid over a window that ends in the reserved oos2, the ten per-cell conditions and the area rule that decide whether a strategy survives, and the two owner's rules it enforces (every look spends the window, and nothing is read until steps 17, 18 and 19 are all done) |
| `variants` | 1,857 | 1 | 2026-09-25 | Run the variant factory in SQX — turn one mother's SPP design brief into a batch of parameter variants, load and retest them on the custodian, and harvest the metrics panel and the per-day equity the WFC and the CSCV read |
| `template-run` | 1,779 | 1 | 2026-09-25 | Build an existing strategy template on a market — set up the project, run it on the custodian, check the strategies really carry the template's fixed block, and record the run. Touches live installs and burns CPU |
| `sync` | 1,550 | 1 | 2026-09-25 | Put the project's current state on GitHub and keep it there — check what changed, refuse to commit data or machine-specific files, run the mechanical checks, commit it grouped by theme, and push every branch. Also bootstraps the remote the first time |
| `crossmarket` | 1,341 | 1 | 2026-09-25 | Retest surviving strategies on other markets with SQX's Retest on additional markets cross-check — the markets from assets/_markets.yaml, each over its own window and at its own declared costs. Configures and runs a task on the custodian |
| `mcretest` | 1,340 | 1 | 2026-09-25 | Configure the eight MC Retest tasks of a custom SQX project — one perturbation each, the asset's own ranges, acceptance silenced, and the MinDistance task only when the population trades with stop or limit orders |
| `spp` | 1,325 | 1 | 2026-09-25 | Configure and run the two SPP tasks of a custom SQX project — the System Parameter Permutation grid over the in-sample and the out-of-sample window, at the owner's spread and steps, with every acceptance silenced so the profile is a map and not a filter |
| `oos-gate` | 1,068 | 1 | 2026-09-25 | Close the loop between an OOS retest and the next SQX task — harvest the two databanks into Python, run the gate's screens, and put the verdict back so the next task only sees the survivors. Stops and restarts installs and deletes rejected strategies |
| `perf` | 898 | 1 | 2026-09-20 | Measure what the project costs in time, memory and disk, find where it is worth making faster, and implement the improvement on a branch |
| `export` | 500 | 1 | 2026-09-25 | Export data out of StrategyQuant X — a databank's metrics with IS/OOS columns, every trade of every strategy, or OHLC bars |
| `translate` | 443 | 1 | 2026-09-12 | Turn a .sqx strategy into readable pseudocode and an executable Python backtest, reconciled against the trades SQX exported |
| `audit` | 401 | 1 | 2026-09-12 | Run the daily project audit — documentation against reality, code and data integrity, statistical rigour, and the three SQX failures that count (broken exports, oversized logs, corrupt blocks) |
| `doc` | 247 | 1 | 2026-09-25 | Record what a session discovered into the right knowhow, OPEN.md or CLAUDE.md file, and repair documentation that has drifted from the code. Use after work that found something non-obvious. |

15 skills, 18,643 tokens de cuerpo en total, 72 KB en disco.

## Skills de global — `/home/sergioguslw/.claude/skills`

| skill | ~tokens al invocar | ficheros | último cambio | para qué |
|---|---:|---:|---|---|
| `sqx-custom-block` | 6,488 | 50 | 2026-09-25 | Author StrategyQuant X / AlgoWizard custom blocks (trading rules) as importable XML, from a plain-English idea. Discovers the indicator vocabulary from the user's OWN install (config.xml + optional customBlocksExport.xml) and builds both Condition blocks (true/false rules) and Price-level blocks (that return a price — stops, targets, bands, breakout references), validating them before import |
| `sqx-strategy-template` | 5,657 | 53 | 2026-09-25 | Turn a trading idea into a StrategyQuant X strategy template for this project — ask the exact logic, check the block exists (authoring it with sqx-custom-block if not), emit the .sqx with the owner's defaults (his condition fixed plus one free random condition) or, when asked, one of the vendor's build-confirmed shapes, file it in the template library and install its blocks on both workers. Authoring only, no SQX run and no CPU burnt |
| `sqx-random-group` | 3,022 | 30 | 2026-09-25 | Author StrategyQuant X / AlgoWizard random groups (the pools the strategy builder samples from) as importable XML. Discovers what THIS install can pool from its own config.xml + customBlocks.xml, and builds both Condition groups (boolean rule pools) and Value groups (price/level pools), in two item modes — hybrid (re-export existing custom blocks by reference) and inline (fresh rules / value atoms / comparisons) — validating before import |

3 skills, 15,167 tokens de cuerpo en total, 2,895 KB en disco.
