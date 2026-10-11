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
| `sqx-strategy-template`, `template-run` | de una idea a una plantilla, y de una plantilla a una construcción en un mercado | autoría (gratis) y ejecución (horas de CPU) — partidas a propósito |
| _(retiradas)_ | las cuatro `analysis-*` — generación, retest MC, Monte Carlo, cross-market — se borraron el 2026-09-22 por decisión del dueño. **Los módulos de Python siguen ahí y funcionan** (`tasks/reports/`, `studies/breakage/mcRetest/`, `portfolio/common/monteCarlo/`, `studies/transfer/crossmarket/`); lo que se fue son las reglas de lectura. Recuperables: `git show <commit>:.claude/skills/analysis-<x>/SKILL.md` | — |
| `export`, `translate` | sacar datos de SQX, y traducir una estrategia a Python | puntual |
| `audit`, `doc`, `perf`, `sync` | mantenimiento del proyecto | puntual |
| `sqx-wait`, `open-close`, `manual-chapter`, `ui-shot`, `dossier-pdf` | oficios que cada sesión reescribía a mano (2026-10-02): la espera de SQX y el vistazo previo a los workers, cerrar issues de `OPEN.md`, el capítulo del manual con su captura, la captura de la ventana, el PDF de un dossier. Llevan su script dentro de la carpeta de la skill | en casi cada tarea |
| `handoff`, `encargo`, `new-study`, `cron-agent` | listas de pasos que estaban repartidas por seis sitios: el prompt para la sesión siguiente, un encargo, un estudio nuevo completo, un agente nuevo en cron | puntual |
| `sqx-*` (globales, de sqx-lab) | producto genérico de autoría SQX | **candidatas a retirar, ver abajo** |

## Cobertura del workflow — qué paso tiene skill y cuál no

Los 26 pasos (más 10.5, 16.5, 18.5 y 25.5) están en `docs/AgentPDFs/WORKFLOW.md`. Cada paso de SQX
necesita **un custom project y su tarea o tareas**; cada paso de Python necesita **leer el
resultado y emitir un veredicto**. Esto dice quién cubre qué, a 2026-09-23 salvo las filas de
2026-10-02 (las tres skills nuevas y el tramo 20-26).

| # | paso | quién lo cubre | |
|---|---|---|---|
| 1 | idea, y dónde investigar | `/research-direct` (el director de investigación elige la celda y propone tres ideas con su paleta) · `/workflow-start` (idea → plantilla → paleta de bloques → proyecto, con los tres agentes expertos) | ✅ |
| 2-3 | vocabulario y plantilla | `/sqx-strategy-template` | ✅ |
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
| 7-16 | la cadena entera, sin humano en medio | `/autopilot` — cada tarea de SQX y cada estudio de Python, juzgando cada paso por `pipeline/autopilot/criteria.yaml` | 🟡 fase 1 (OPEN.md #90) |
| 20 | análisis conjunto ciego de 17-18-19 (y 18.5) | `studies/closing/blindJoint/` | ❌ **sin skill** |
| 21-25 | exposición, mapa condicional, estructura, stop ATR, edge por coste por estrategia | `studies/closing/`, `studies/readings/`, `sqx/structural/` | ❌ **sin skill** |
| 26 | validación en MT5 con la feed de cada empresa de fondeo | la ventana (MT5 BRIDGE › Verificar) · `mt5/verify/`; `/ea-news` para el filtro de noticias del EA | 🟡 sin skill de pasos |

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

**Las tres globales de sqx-lab** (`sqx-custom-block`, `sqx-random-group`, `sqx-strategy-template`)
**se quedan** (dueño, 2026-09-29, `docs/OPEN-closed.md` §73): llevan el overlay de AlgoProject y la
ventana («Crear la plantilla con Claude») las llama desde `ui/daemon/create/author.py`,
`sqx/templates/build.py` y `sqx/blocks/install.py`; desinstalarlas la rompería. Pesan entre 3.000 y
6.500 tokens cada una; `~/.claude/skills/sqx-*` son enlaces simbólicos a `tools/sqx-lab/`. Sin otras
candidatas a retirar a 2026-10-04: todas las skills de proyecto cambiaron en las últimas semanas.

## Cómo leer las tablas

- `~tokens al invocar` — el cuerpo del `SKILL.md`. Si una skill pesa mucho y se usa para poco,
  pártela.
- `ficheros` — más de uno significa que tiene material de referencia que puede cargar a demanda.
  Eso es bueno: es cuerpo que no se paga salvo que haga falta.
- `último cambio` — una skill que lleva meses sin tocarse y describe un flujo que ya cambió es una
  trampa, no documentación.

<!-- generado por tools/skillmap.py — no editar debajo de esta linea -->

Regenerado 2026-10-11 con `python3 tools/skillmap.py`. El coste en tokens es el cuerpo del `SKILL.md`, que solo se carga al invocarla; la descripcion (~90 tokens) esta siempre en contexto.

## Skills de proyecto — `/home/sergioguslw/Desktop/AlgoProject/.claude/skills`

| skill | ~tokens al invocar | ficheros | último cambio | para qué |
|---|---:|---:|---|---|
| `crosstf` | 3,356 | 1 | 2026-10-09 | Test whether a strategy's edge survives being read on a slower timeframe — fabricate period-rescaled siblings, wire a cross-timeframe check into a custom project, run it on the custodian, and read each cell against its own timeframe's null |
| `variants` | 3,053 | 1 | 2026-10-07 | Run the variant factory in SQX — turn one mother's SPP design brief into a batch of parameter variants, load and retest them on the custodian, and harvest the metrics panel, the per-day equity and every variant's trades that the WFC, the parameter cloud and the CSCV read |
| `wfm` | 2,020 | 1 | 2026-10-07 | Configure and run the Walk Forward Matrix task of a custom SQX project — the 30-cell grid over the whole window build..oos2, with the ten per-cell conditions and the area rule SQX marks a strategy with (a mark, never a judge: the analysis judges in oos2) |
| `curate` | 1,977 | 1 | 2026-10-03 | Apply a Python verdict back into SQX — move the strategies a filter, a test or an analysis rejected out of a databank, so the next task in the chain only sees the survivors. Works between any two tasks and with any module that can name what it drops |
| `template-run` | 1,937 | 1 | 2026-10-03 | Build an existing strategy template on a market — set up the project, run it on the custodian, check the strategies really carry the template's fixed block, and record the run. Touches live installs and burns CPU |
| `sync` | 1,902 | 1 | 2026-10-09 | Put the project's current state on GitHub and keep it there — check what changed, refuse to commit data or machine-specific files, run the mechanical checks, propose the commits grouped by theme and make them only after the owner's yes, and push master. Also bootstraps the remote the first time |
| `firm-onboard` | 1,754 | 1 | 2026-09-29 | Add a prop firm to the funding studies by the owner's admission protocol — register it as a candidate, check the admission gates on the firm's own pages (self-built EAs on MT5, Spain served, track record, modelable rules, EA traps), build its catalogue reader or typed catalogue, seed its rules file, find its offer surfaces, record its MT5 facts, and hand the owner an admission sheet; only the owner makes a firm active. Also re-runs the gates on a firm whose rules changed |
| `mcretest` | 1,741 | 1 | 2026-10-07 | Configure the eight MC Retest tasks of a custom SQX project — one perturbation each, the asset's own ranges, acceptance silenced, and the MinDistance task only when the population trades with stop or limit orders |
| `crossmarket` | 1,536 | 1 | 2026-10-03 | Retest surviving strategies on other markets with SQX's Retest on additional markets cross-check — the markets from assets/_markets.yaml, each over its own window and at its own declared costs. Configures and runs a task on the custodian |
| `oos-gate` | 1,401 | 1 | 2026-10-03 | Screen a population after its OOS retest — harvest the two databanks (build and OOS) into Python, run the gate's screens and write the survivors list and verdict.csv. Stops the install to harvest. Moving the verdict back into SQX (deleting the rejected strategies) is `/curate`, which this skill hands over to |
| `spp` | 1,367 | 1 | 2026-10-03 | Configure and run the two SPP tasks of a custom SQX project — the System Parameter Permutation grid over the in-sample and the out-of-sample window, at the owner's spread and steps, with every acceptance silenced so the profile is a map and not a filter |
| `workflow-template` | 1,366 | 1 | 2026-10-10 | Run the WHOLE workflow (steps 5 to 25) from an already authored strategy template (.sqx) with one command that creates the project, applies the palette to its random hole and runs every SQX task and study unattended. Fully mechanical, any model can run it |
| `workflow-simple` | 1,335 | 2 | 2026-10-10 | Run the WHOLE workflow (steps 5 to 25) for a Simple Strategy — no template, one side — with one command that creates the project, applies the palette and runs every SQX task and study unattended. Fully mechanical, any model can run it |
| `asset-onboard` | 1,287 | 1 | 2026-10-06 | Add a new asset to assets/ with its whole cost card worked out from data — Darwinex's real spread per segment (measured, modelled back where there are no ticks), slippage at half of it, the owner's default commission and swap for its kind, the triple-swap night, and the MC Retest spread range from the real dispersion. Also refreshes the spreads of an existing asset |
| `perf` | 1,249 | 1 | 2026-09-26 | Measure what the project costs in time, memory and disk, find where it is worth making faster, and implement the improvement, left uncommitted for the owner |
| `literature-scout` | 1,171 | 1 | 2026-10-02 | Run the literature scout by hand — search arXiv and OpenAlex for published trading research, let the literatureScout agent reject each paper by the owner's hard filters or extract its rules as entries anchored to verbatim quotes, record what the run cost, measure the new entries on `build` with the market profile, and show the owner the rejections, the entries, the open questions and which cells reach the board. Touches no SQX |
| `encargo` | 1,037 | 1 | 2026-10-09 | Write an encargo — one self-contained brief in docs/encargos/ that a single agent instance executes without reading anything else — in the house shape, numbered, registered in the folder's README, with the owner's decisions listed as questions |
| `store-open` | 924 | 1 | 2026-10-08 | Read a strategy back from the strategy store — find it by name or identity, unpack its folder (the .sqx under its own name, every test's results, distributions, trades per market and timeframe) and read any number or histogram without rerunning a test |
| `store-save` | 843 | 1 | 2026-10-08 | Save the strategies of a project that passed the gate (step 8, limbo included) into the strategy store — the .sqx once, every test's results, distributions, trades in every market and timeframe, the step-12 sisters — and verify the store is whole |
| `research-direct` | 839 | 1 | 2026-10-03 | Ask the research director where to investigate next — refresh the results memory, print the board of cells (asset × timeframe × direction × family) the owner's prior rates Alta or the market profile's measurements admit, run the researchDirector agent to pick one cell and bring three ideas with their block palettes, and show the proposal. Costs one Opus session with its subagents (the ideaExpert and the ideaReviewer) per proposal; launches nothing in SQX |
| `ui-shot` | 809 | 1 | 2026-10-04 | See a change to the desktop window (ui/) before saying it is done — shoot the zone offscreen on a scratch daemon, look at the PNG, have the uiCritic agent critique it, walk every zone for exceptions — and the checklist for a new zone or view. Use after editing anything under ui/, when the owner gives feedback on how the window looks, asks for a critique of a zone, or asks for a new view, zone or panel. |
| `autopilot` | 761 | 1 | 2026-10-07 | Run a project's whole workflow unattended — every SQX task and Python study from the build (step 6's task, chained with 7) to 16, then the tail 16.5 to 25 for every survivor (26 when its four parameters are given), judging each judging step by criteria.yaml and cutting in SQX instead of stopping, cheap in tokens (reads only a status line and a short summary, never SQX's log) |
| `new-study` | 720 | 1 | 2026-10-02 | Add a study to studies/ complete in one pass — the module in the contract's shape, its rows in the window's catalogue, its thresholds in the ledger, its perf target, its test, its manual chapter and the closing checks |
| `cron-agent` | 710 | 1 | 2026-10-02 | Add an unattended agent that runs from cron — its agent file, its bin/ script with lock, dry-run and headless `claude -p` on Sonnet, a crontab minute no other job uses, its report folder and its manual chapter |
| `workflow-start` | 691 | 1 | 2026-10-03 | Start a new workflow run from nothing — the three expert agents for the idea, the template and the building blocks (spending what they need), then the custom project, the palette written into its Build task, and the autopilot from the build (step 6) on |
| `store-resume` | 677 | 1 | 2026-10-08 | Bring strategies back from the strategy store into StrategyQuant and carry on their workflow from step 13 (MC Retest) — recreates the retired project under its own name, loads the chosen stored .sqx into its databanks and hands it to the one workflow command |
| `sqx-wait` | 661 | 3 | 2026-10-03 | Look at who holds the three SQX installs before touching a worker, and wait for an SQX run in ONE background command that exits on `Project finished`, an aborted run, a dead sqcli, low RAM or a time bound (rule 18). Use before starting, stopping or querying a worker, and right after any `action=start`, instead of writing an `ss`/`OWNER`/`until grep` loop by hand. |
| `handoff` | 650 | 1 | 2026-10-02 | Write the prompt that hands this session's unfinished work to a fresh session — self-contained, in Spanish, with the state, the exact next step, the model to use and what not to touch |
| `ea-news` | 581 | 1 | 2026-10-02 | Make SQX-exported MetaTrader 5 EAs obey a prop firm's news rule — per strategy one EA with the firm's news filter (close before a high-impact release, no entries around it) and one without, both compiled |
| `manual-chapter` | 566 | 2 | 2026-10-02 | Write or update a chapter of the owner's manual for a command — the Spanish chapter in AlgoData/manual-fuentes from the template, screenshots of the command's REAL output, its family in tools/manual.py, and the rebuilt PDF |
| `rebuild-sister` | 526 | 1 | 2026-10-08 | Write again the .sqx of a step-12 scaled sister (a stored strategy moved to M15, H1, H4…) from the strategy store — the store keeps the mother's file and each sister's parameters, never the sister's file |
| `export` | 515 | 1 | 2026-10-01 | Export data out of StrategyQuant X — a databank's metrics with IS/OOS columns, every trade of every strategy, or OHLC bars |
| `open-close` | 446 | 2 | 2026-10-02 | Close issues of OPEN.md or add a dated note to one — move each closed section verbatim to docs/OPEN-closed.md in numeric order, flip its emoji and its index row |
| `audit` | 427 | 1 | 2026-10-03 | Launch the `auditor` agent (model sonnet) to run the daily project audit — documentation against reality, code and data integrity, statistical rigour, and the three SQX failures that count (broken exports, oversized logs, corrupt blocks) |
| `dossier-pdf` | 410 | 2 | 2026-10-02 | Turn a dossier written for the owner into the PDF he reads — the Spanish .md in docs/AgentPDFs/, rendered with the manual's style through headless Chrome, and its row in the folder's README |
| `doc` | 267 | 1 | 2026-10-03 | Launch the `documenter` agent (model sonnet) to record what a session discovered into the right knowhow, OPEN.md or CLAUDE.md file, and repair documentation that has drifted from the code. Use after work that found something non-obvious. |

36 skills, 41,525 tokens de cuerpo en total, 179 KB en disco.

## Skills de global — `/home/sergioguslw/.claude/skills`

| skill | ~tokens al invocar | ficheros | último cambio | para qué |
|---|---:|---:|---|---|
| `sqx-custom-block` | 6,488 | 57 | 2026-10-04 | Author StrategyQuant X / AlgoWizard custom blocks (trading rules) as importable XML, from a plain-English idea. Discovers the indicator vocabulary from the user's OWN install (config.xml + optional customBlocksExport.xml) and builds both Condition blocks (true/false rules) and Price-level blocks (that return a price — stops, targets, bands, breakout references), validating them before import |
| `sqx-strategy-template` | 5,744 | 75 | 2026-10-04 | Turn a trading idea into a StrategyQuant X strategy template for this project — ask the exact logic, check the block exists (authoring it with sqx-custom-block if not), emit the .sqx with the owner's defaults (his condition fixed plus one free random condition) or, when asked, one of the vendor's build-confirmed shapes, file it in the template library and install its blocks on both workers. Authoring only, no SQX run and no CPU burnt |
| `sqx-random-group` | 3,022 | 38 | 2026-10-04 | Author StrategyQuant X / AlgoWizard random groups (the pools the strategy builder samples from) as importable XML. Discovers what THIS install can pool from its own config.xml + customBlocks.xml, and builds both Condition groups (boolean rule pools) and Value groups (price/level pools), in two item modes — hybrid (re-export existing custom blocks by reference) and inline (fresh rules / value atoms / comparisons) — validating before import |

3 skills, 15,254 tokens de cuerpo en total, 3,099 KB en disco.
