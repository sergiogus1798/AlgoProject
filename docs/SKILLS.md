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
| _(retiradas)_ | las cuatro `analysis-*` — generación, retest MC, Monte Carlo, cross-market — se borraron el 2026-09-22 por decisión del dueño. **Los módulos de Python siguen ahí y funcionan** (`tasks/reports/`, `strategies/retest/`, `strategies/monteCarlo/`, `strategies/crossmarket/`); lo que se fue son las reglas de lectura. Recuperables: `git show <commit>:.claude/skills/analysis-<x>/SKILL.md` | — |
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
| 10 | análisis crossmarkets | `strategies/crossmarket/` | ❌ **sin skill** |
| 10.5-11 | variantes escaladas y retest crossTF | `/crosstf` · `sqx/projects/crosstf.py` | ✅ |
| 12 | análisis crossTFs | `strategies/crossTF/` | 🟡 dentro de `/crosstf` |
| 13 | **MC Retest en SQX** | sólo los rangos (`sqx/projects/ranges.py`) | ❌ **falta la tarea** |
| 14 | análisis MC Retest | `strategies/retest/` | ❌ **sin skill** |
| 15 | **SPPs en SQX** | `sqx/variants/spp.py` | ❌ sin skill · ⚠️ ver abajo |
| 16 | análisis SPPs | `strategies/sppUltra/` | ❌ **sin skill** |
| 16.5-17 | variantes para WFC, y el WFC | `sqx/variants/make.py`, `walkForwardCorrelation/` | ❌ sin skill · ⚠️ ver abajo |
| 18 | CSCV | `walkForwardCorrelation/pbo.py` | ❌ **sin skill** |
| 19 | **Walk Forward Matrix en SQX** | `strategies/walkForwardMatrix/` es sólo el análisis | ❌ **falta la tarea** |
| 20 | análisis conjunto ciego de 17-18-19 | — | ❌ **no existe** |

### Los tres huecos de SQX, y son el mismo hueco

`crossmarket.py` y `crosstf.py` hacen lo mismo con distinto crosscheck: **encender el suyo en una
tarea concreta y escribirle su configuración desde `assets/`**. Ese patrón no existe todavía para:

- `MonteCarloRetest` (paso 13) — los rangos sí se escriben, la tarea no se enciende
- `WalkForwardMatrix` (paso 19)
- `OptProfileSysParamPermutation` (paso 15) — **el SPP, que NO es `SequentialOptimization`**

Y hay una razón de fondo: la doctrina apaga **todos** los crosschecks fuera de la construcción, a
propósito. Encender el que toca en la tarea que toca es justo lo que hace falta escribir.

### ⚠️ Los pasos 15 y 17 corren sobre el `Retester` de serie

`sqx/variants/config.yaml` lleva `project: Retester`. Eso **incumple la regla dura 10** (dueño,
2026-09-23: todo run en un custom project, nunca el `Builder` ni el `Retester` de serie). Es
anterior a la regla, no una decisión contra ella, pero hay que migrarlo.

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

Regenerado 2026-09-23 con `python3 tools/skillmap.py`. El coste en tokens es el cuerpo del `SKILL.md`, que solo se carga al invocarla; la descripcion (~90 tokens) esta siempre en contexto.

## Skills de proyecto — `/home/sergioguslw/Desktop/AlgoProject/.claude/skills`

| skill | ~tokens al invocar | ficheros | último cambio | para qué |
|---|---:|---:|---|---|
| `curate` | 1,900 | 1 | 2026-09-23 | Apply a Python verdict back into SQX — move the strategies a filter, a test or an analysis rejected out of a databank, so the next task in the chain only sees the survivors. Works between any two tasks and with any module that can name what it drops |
| `crosstf` | 1,788 | 1 | 2026-09-23 | Test whether a strategy's edge survives being read on a slower timeframe — fabricate period-rescaled siblings, wire a cross-timeframe check into a custom project, run it on the custodian, and read each cell against its own timeframe's null |
| `template-run` | 1,667 | 1 | 2026-09-23 | Build an existing strategy template on a market — set up the project, run it on the custodian, check the strategies really carry the template's fixed block, and record the run. Touches live installs and burns CPU |
| `sync` | 1,553 | 1 | 2026-09-12 | Put the project's current state on GitHub and keep it there — check what changed, refuse to commit data or machine-specific files, run the mechanical checks, commit it grouped by theme, and push every branch. Also bootstraps the remote the first time |
| `strategy-template` | 1,140 | 1 | 2026-09-22 | Turn a trading idea into a StrategyQuant X strategy template — understand the logic, check whether the condition already exists, author the custom block if it does not, and emit the .sqx into the library. Authoring only, no SQX running and no CPU burnt |
| `crossmarket` | 1,108 | 1 | 2026-09-23 | Retest surviving strategies on other markets with SQX's Retest on additional markets cross-check — the markets from assets/_markets.yaml, each over its own window and at its own declared costs. Configures and runs a task on the custodian |
| `oos-gate` | 1,041 | 1 | 2026-09-23 | Close the loop between an OOS retest and the next SQX task — harvest the two databanks into Python, run the gate's screens, and put the verdict back so the next task only sees the survivors. Stops and restarts installs and deletes rejected strategies |
| `perf` | 898 | 1 | 2026-09-20 | Measure what the project costs in time, memory and disk, find where it is worth making faster, and implement the improvement on a branch |
| `export` | 449 | 1 | 2026-09-12 | Export data out of StrategyQuant X — a databank's metrics with IS/OOS columns, every trade of every strategy, or OHLC bars |
| `translate` | 443 | 1 | 2026-09-12 | Turn a .sqx strategy into readable pseudocode and an executable Python backtest, reconciled against the trades SQX exported |
| `audit` | 401 | 1 | 2026-09-12 | Run the daily project audit — documentation against reality, code and data integrity, statistical rigour, and the three SQX failures that count (broken exports, oversized logs, corrupt blocks) |
| `doc` | 224 | 1 | 2026-09-03 | Record what a session discovered into the right knowhow, OPEN.md or CLAUDE.md file, and repair documentation that has drifted from the code. Use after work that found something non-obvious. |

12 skills, 12,617 tokens de cuerpo en total, 49 KB en disco.

## Skills de global — `/home/sergioguslw/.claude/skills`

| skill | ~tokens al invocar | ficheros | último cambio | para qué |
|---|---:|---:|---|---|
| `sqx-custom-block` | 6,039 | 53 | 2026-09-18 | Author StrategyQuant X / AlgoWizard custom blocks (trading rules) as importable XML, from a plain-English idea. Discovers the indicator vocabulary from the user's OWN install (config.xml + optional customBlocksExport.xml) and builds both Condition blocks (true/false rules) and Price-level blocks (that return a price — stops, targets, bands, breakout references), validating them before import |
| `sqx-strategy-project` | 4,848 | 17 | 2026-09-18 | Create a StrategyQuant X / AlgoWizard build PROJECT (project.cfx) by cloning an existing project on THIS install and wiring a chosen set of strategy templates as N build tasks — each task its own output databank plus optional acceptance / time-cap settings. Inherits the donor project's data feed, symbol, timeframe, and exit/acceptance settings unchanged; only the strategy template + output databank (+ those two settings) vary per task. Install-bound and clone-based — never hand-builds a project from scratch. Fourth in the suite after sqx-custom-block, sqx-random-group, sqx-strategy-template |
| `sqx-strategy-template` | 4,674 | 54 | 2026-09-18 | Author StrategyQuant X / AlgoWizard strategy templates (.sqx) bound to THIS install's random groups + custom blocks. Discovers the install's CLEAN groups, a research agent designs thesis-driven entries (filter + trigger roles, order type, a falsifiable why), and a generator emits importable .sqx in proven signal-variable skeletons (market / stop / session-gated / multi-timeframe / role-structured shapes), self-validated. Install-only — never invents blocks or groups; correctness is carried by build-confirmed skeletons, varying only the typed holes |
| `sqx-random-group` | 2,692 | 34 | 2026-09-18 | Author StrategyQuant X / AlgoWizard random groups (the pools the strategy builder samples from) as importable XML. Discovers what THIS install can pool from its own config.xml + customBlocks.xml, and builds both Condition groups (boolean rule pools) and Value groups (price/level pools), in two item modes — hybrid (re-export existing custom blocks by reference) and inline (fresh rules / value atoms / comparisons) — validating before import |

4 skills, 18,255 tokens de cuerpo en total, 3,564 KB en disco.
