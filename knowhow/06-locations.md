# Where things actually live

🔬 These hold real content and are easy to miss:

| path | contents |
|---|---|
| `~/Desktop/WorkSQX/` | 635 `.sqx`, plus `AlgoWizardTemplates/` (a main template source) |
| `~/Desktop/AddonsSQX/` | 68 `.sqx`, `Templates/`, `CustomBlocks/`, `RandomGroups/` |
| `~/Desktop/StratsProblem/` | 6 `.sqx` |
| `~/Desktop/user/` | ⚠ NOT debris — a 12 Jun project tree, the ONLY copy of XAUUSD/Results (4,805 `.sqx`). Do not delete |
| `~/Desktop/AlgoProject_Old/` | the previous project. Read-only archive, incl. 8.5 GB of `snapshots/` |
| `~/.local/share/Trash/` | 11,440 `.sqx` — mostly June-tree duplicates. **The owner has asked that Trash be excluded from strategy searches** |
| `~/Desktop/SQX.zip` | 1.28 GB **June install backup**, only 32 example `.sqx`. Not a strategy archive |

🔬 97 AlgoWizard templates across `WorkSQX/AlgoWizardTemplates/` and `AddonsSQX/Templates/`
(`TemplatesSergiogus`, `TemplatesClaude`, `TemplatesLaCity`, `TemplatesBook`).

## Logs

🔬 `<install>/user/log/StrategyQuant/log_YYYY_MM_DD.log` keeps **14 days**; SQX prunes the rest on
start. A single day reaches multi-GB — `log_2026_08_18.log` alone is **4.66 GB**, and the master's
whole log tree was 4.4 GB. It gzips to 102 MB, so archiving is cheap and there is no reason not to.
`AlgoData/logs/<install>/` holds them (`SQX/projects/<P>/` the projects' own logs, condensed — see
`07-practices.md`, log retention); `sqx/export/archive_logs.py` refreshes it and must run more
often than every 14 days. First full archive taken 2026-09-04, back to 2026-06-13.

🔬 Data coverage, from `-symbol action=list` on the worker: `XAUUSD_DukasM1_Infinox` runs
**2003.05.05 → 2026.01.16**. The XAUUSD build task's window stops at **2017.12.31**, leaving 8 years of
gold data unused.

## The building-block vocabulary

🔬 The **whole AlgoWizard block vocabulary** is one file:
`<install>/internal/web/SQWIZARD/branding/global/config.xml` (1.19 MB). Its single `<Blocks>`
element holds four sections, each a list of `<Category>` of `<Item key= name= display= returnType=>`:
**Comparisons 23 · Conditions 500 (63 categories) · Actions 23 · Values 303 (8 categories,
190 of them indicators)** = 849 built-ins. `display` is the block's written form with its
`#Param#` holes; `key` is what a template or a group references.

⚠ Do not confuse it with `<install>/internal/ctemplate/config.xml` (18 KB) — that one is the
*editor's* defaults, a `<UsedBlocks>` shortlist of ~14 keys, not the catalogue.

🔬 The owner's own blocks are separate: `<install>/user/settings/customBlocks.xml` (1.3 MB,
**171 `<Item>`**, flat, each with `category`, `type` and `oppositeBlockKey`). Backups sit beside it
in `customBlocks-backups/`; the same folder pattern holds for `blockGroups.xml`.
Total on the master today: **1,020 blocks**.

🔬 `tools/sqx-lab/.../sqx-custom-block/catalog.json` is a derived index of the *value* atoms only
(235 = 178 native + 57 the owner's), not of the conditions — regenerate it, don't hand-edit it.

### 🔬 The builder's block switches live in the Build task, not in the install (2026-09-24)

The catalogue (`config.xml` + `customBlocks.xml`) says what the install *knows*. What the builder
may *sample* is a separate, per-task list: `<Blocks><BuildingBlocks>` inside the Build task XML —
**844 `<Block key= weight= use= category=>` entries**, which is why `Build-Task3.xml` is 2.9 MB
while a Retest task is 40 KB. Measured on the frozen donor
`AlgoData/projectsBackup/XAUUSD_base_2026-09-21`.

Three categories, and they are **three switches over the same vocabulary, one per role**:

| `category` | entries | keys look like | what the switch gates | on in the donor |
|---|---|---|---|---|
| `signals` | 588 | `ADXCrossUp`, `CBlock_BBBreakoutUp` | the block as an entry/exit condition | 400 |
| `indicators` | 171 | `Indicators.ADX`, plus the 23 comparators bare | the block as a value to compare | 26 |
| `stopLimitBlocks` | 85 | `Stop/Limit Price Levels.EMA`, `…Ranges.ATR` | the block as the price of a stop/limit order | 10 |

🔬 The prefixes are a namespace, not other blocks: `Indicators.ATR` and
`Stop/Limit Price Ranges.ATR` both resolve to the single `ATR` of `config.xml`, and every one of
the 844 keys resolves into the 1,020-block catalogue. All 171 of the owner's blocks are present.
**253 native blocks appear in no category at all** — the Actions, the Functions, the Bar/Time
values, the Strategy Control values and all 158 `talib_*`: they exist for a hand-built strategy and
are unreachable from generation.

🔬 `weight` is `1` on all 844 today, so nothing in this install has ever used the soft knob.

#### 🔬 A group-bound hole IGNORES the switches; a free hole obeys them (tested 2026-09-24)

Measured, not inferred. Project `blocktest_grupoA` on the custodian: donor cloned untouched,
template `TrendRegimeFilters_EntryOnly.sqx`, whose entry is
`AND(RandomCondition(group=TrendRegimeFilters), RandomCondition(free))`. All six members of
`TrendRegimeFilters` are `use="false"` in the donor's `<BuildingBlocks>`. 30 strategies, 21 s.

| hole | bound to | what it produced |
|---|---|---|
| `RandomConditionFilter1` | `TrendRegimeFilters` | **30/30 `CBlock_CSSARegimeAbove50`, `use="false"`** |
| `RandomCondition2` | nothing | 98 fills, 28 distinct blocks — **97 of 98 `use="true"`** |

So the two mechanisms are genuinely independent and the switch is not a global gate:

- **A `RandomCondition` bound to a group samples the group and nothing else.** `use="false"` does
  not remove a block from a pool. Turning a block off cannot stop a template that points a hole at
  a group holding it.
- **A free `RandomCondition` obeys the switches.** Of 408 `use="false"` blocks, the only one that
  ever appeared in the free hole was the one the bound hole had already forced into the strategy
  (once out of 98, evolution copying it across slots).

#### 🔬 A template's FIXED block is outside the switches too (2026-09-24)

Stronger than `use="false"`: `CBlock_CloseCrossesAboveKCUpper` is **not in the donor's
`<BuildingBlocks>` at all** — it was authored on 2026-09-22, the donor was frozen on 2026-09-21 —
and the `smoke_keltnerUpperCrossUp` build carried it in 29 of 29 strategies. A block written into
the template is part of the skeleton, not drawn from a pool, so nothing in that list can remove it.

Which leaves the list governing exactly one thing: **what a free `RandomCondition` may draw.**
Fixed blocks and group-bound holes are both outside it.

⚠️ **A frozen donor's `<BuildingBlocks>` goes stale.** It is a stored settings overlay, not the
install's vocabulary: every block authored after the freeze is missing from it, and SQX builds with
that block anyway. Anything deriving "what the builder can sample" from a donor must add the
install's own blocks back — `sqx/blocks/taxonomy.py` does, by block type.

⚠️ Consequence for anything that filters the builder's vocabulary: **`<BuildingBlocks>` governs
free holes and generic generation only.** Narrowing what a group-bound template may sample is done
by choosing or authoring the **group**, never by the switches. A system that offers only the
switches will silently do nothing on exactly the templates that bind their holes.

🔬 The 85 `indicators` entries that carry `indicatorMin/Max/Step` are calibrated ranges, and
`<Calibration calibrateBeforeStart="true" maxSteps="50"/>` sits beside them: SQX recalibrates
before each run, so the ranges a cloned donor carries are not stale on a new asset.

Nothing in this repo reads or writes `<BuildingBlocks>` as of 2026-09-24 — `sqx/projects/` touches
costs, windows, templates, databanks and cross-checks, never the block switches.

### 🔬 A RandomCondition needs no group, and a fixed block beside it is already proven (2026-09-22)

Read out of `highest_breakout_template_daily_filter.sqx`, the template this install ships and the
one the `session_market` shape was derived from. Its entry signal is:

```xml
<Item key="AND">
  <Block><Item key="RandomCondition" ...>
           <Param key="#Group#" name="Random group" randomGroupType="Conditions" />   <!-- empty -->
  <Block><Item key="BarDayOfWeekIsNot" ...>                                           <!-- concrete -->
```

Two facts, both load-bearing for authoring templates from a plain-English idea:

🔬 **`#Group#` is empty and the template builds.** A `RandomCondition` left without a group samples
the whole Conditions vocabulary — 500 blocks — rather than a pool. Binding it to a group narrows the
search; it is an option, not a requirement. Anything claiming a hole needs a group is wrong.

🔬 **`AND(RandomCondition, <concrete block>)` is build-confirmed** on this install. The shape the
owner asks for — one fixed condition that states the idea, plus one random condition — needs no new
skeleton. Only which concrete block sits in the fixed slot varies.

Consequence for the pooling note below: **a group matters only for a hole.** A block that no group
pools is unreachable from a `RandomCondition`, and perfectly usable as the fixed half.

### 🔬 A block no group pools is unreachable from a template's HOLE (2026-09-22)

A template's **hole** references a random group, never a block — the fixed half of a signal is the opposite case, see above. So the install knowing a block is
necessary and not sufficient: if no group contains it, no template can point a hole at it. Measured
with `sqx/inspect/vocabulary.py` on the conductor, which reports exactly this.

The Keltner channel is the worked case. SQX ships a whole native category, `Conditions/Keltner
Channel`, with **16 ready-made conditions** — `KCBarClosesAboveUpper` is literally "the bar closes
above the upper band". **None of the 16 is in any group.** The indicator is reachable only as a
*value*, through `BollingerBands_Lower`, a Value group whose name misleads: it pools eleven band
indicators, `KeltnerChannel` and `MTKeltnerChannel` among them. So a Keltner **price level** is
available today and a Keltner **entry condition** is not, until a group is authored for it.

⚠️ **An empty group is a silent failure.** `RandConditions` on this install has zero items, and the
`catalog.json` of `sqx-strategy-template` lists it among the clean condition groups. A template
pointing a hole at it does not fail: it builds, and samples nothing. `vocabulary.py` prints those
groups on their own `EMPTY, unusable` line for that reason.

🔬 **The three installs carry the same vocabulary today** — 849 native + 171 own blocks, 20 groups,
identical on master, `SQX_w1` and `SQX_w2` (`--diff` reports no gap either way). That stops being
true the moment anything is authored on only one of them, which is why a template authored on the
conductor and built on the custodian has to be diffed first.

## Tools built here

| tool | does |
|---|---|
| `sqx/inspect/index_sqx.py` | index every `.sqx` by inner-XML hash + symbol; 17.7k files in 1.5 s |
| `sqx/inspect/dump_project.py` | `project.cfx` → Markdown pipeline map (TL;DR, databank flow, per-task detail) |
| `sqx/inspect/keep_tasks.py` | emit a variant of a `.cfx` keeping only chosen task types |
| `sqx/inspect/project_health.py` | every project's broken task references, version drift and mangled fields |
| `sqx/inspect/template_check.py` | whether built strategies carry the blocks their template fixes |
| `sqx/repair/graft_tasks.py` | heal a project archive missing task files, with SQX closed |
| `sqx/inspect/vocabulary.py` | what an install can express: blocks, groups, what pools what, and the gap against another install |
| `sqx/export/archive_logs.py` | copy both installs' logs to `AlgoData/logs/` before SQX prunes them |
| `sqx/export/export_metrics.py` | databank metrics with paired IS/OOS columns, via the worker |
| `sqx/export/export_trades.py` | a databank's trades plus the bars they were traded on |

## The XAUUSD generated corpus — what it actually is

🔬 Contradicts a common assumption: **these strategies have no stop loss, no take profit and no
trailing stop.** All 231 carry `SQ.Formulas.SLPT.None`. The build task explains it —
`<SLRequired>false</SLRequired>`, `<SLATR>false</SLATR>`, `<PTRequired>false</PTRequired>`. The ATR
machinery is configured (`MinSLATRMultiple 2`, `MaxSLATRMultiple 8`, period 20 fixed) but the toggle is
**off**, so none of it reaches a generated strategy.

- 🔬 Long-only, from `<MarketSides type="long">`. 231/231 have a long entry order, zero short.
- 🔬 `ExitAfterBars` is **uniformly 8** across all 231, though the generator range is 5–20.
- 🔬 Two structurally different populations share the pool: ~129 **bar-cap** strategies (100% of exits
  at the 8-bar cap, median MAE 1.37×ATR) and ~11 **signal-exit** strategies (exit on a rule after 1–3
  bars, median MAE 0.95×ATR, some near 0.01). Any pooled exit statistic hides this.
- 🔬 In-sample window is `2008.01.01–2017.12.31` (`<Setup dateFrom= dateTo=>` in `Build-Task3.xml`).

## Un clon del donante congelado sigue operando el mercado del donante (2026-09-24)

🔬 Medido montando el primer proyecto de un activo que NO es XAUUSD. `sqx.projects.builder` clonaba
el donante, le escribía la sesión, las fechas y el timeframe del activo pedido — y **dejaba el feed
del donante**. El log lo dice sin que nada falle:

```
CONSTRUCCION : Loading backtest data for Higher backtest precision - XAUUSD_DukasM1_Infinox / H1
```

La causa está en `setups.py`: `set_costs` sólo reescribe un `<Setup>` cuyo `<Chart symbol=…>` **ya
es** el del activo. Con el donante en XAUUSD y el activo en USDJPY no casa ninguno, así que el
proyecto salía con el oro en el `<Chart>`, `spread="0"`, la comisión apagada… y la ventana y la
sesión de USDJPY. Un resultado así es peor que un error: es interpretable y está mal.

- 🔬 La reparación es `sqx/projects/resources.py`: trae el `<Symbol>`, su `<InstrumentInfo>` y su
  `<Broker>` de un proyecto que ya opere ese feed (el mismo mecanismo que `borrow_session`), y
  cambia el `<Chart>` **sólo** del feed del donante — los mercados extra de un cross-check conservan
  el suyo. El feed del donante se lee del primer `<Chart>` de su tarea de Build.
- 🔬 El guardia que faltaba: `builder` ya se niega cuando una tarea acaba con **cero** `<Setup>`
  sobre el feed del activo. Ese número lo calculaba desde el 2026-09-23 y no lo miraba nadie.
- 🤔 Todo proyecto creado con este builder para un activo distinto de XAUUSD **antes** de esta fecha
  construyó sobre oro. En `runs.csv` sólo hay corridas de XAUUSD, así que probablemente no hay
  resultado contaminado; conviene comprobarlo antes de creer uno.

## Un bloque nativo fijo en una plantilla no admite un parámetro generado (2026-09-24)

🔬 Fijar `MABarClosesAbove` en el hueco concreto de `market_long` y poner
`generate="random" randomValue="default"` en su `#Period#` hace que el builder se niegue:

```
GenerateException: Bad configuration - Identification not found in item 'MABarClosesAbove'
```

Sin el `generate` construye: **50 de 50** llevaron el bloque (`template_check -n 50`). El bloque
nativo fijo de la plantilla de serie (`highest_breakout_template_daily_filter.sqx`, `BarDayOfWeekIsNot`)
tampoco lleva ningún `generate`, así que la forma confirmada es **parámetros congelados en el hueco
fijo**, y lo que varía de verdad es el hueco aleatorio y las salidas.

- 🔬 Eso NO deja el parámetro fuera del estudio: aparece como parámetro de la estrategia
  (`MABarClosesPeriod1`, `MABarClosesType1`) y por tanto el SPP lo permuta y `variants.scale` lo
  escala. Congelado en el build ≠ invisible después.
- 🤔 Queda sin averiguar si añadir un `#Identification#` al Item lo desbloquea. No se probó: la forma
  congelada es la que está confirmada por un build.

## Un `feed:` en un config.yaml es una bomba de relojería (2026-09-24)

🔬 `strategies/crossTF/config.yaml` llevaba `run.feed: XAUUSD_DukasM1_Infinox` fijo. Al correr el
crossTF sobre USDJPY, **las doce celdas se puntuaron contra barras de ORO**. El síntoma no fue un
error: fue una reconciliación de −0,20 a −0,34 contra el P/L de SQX, y doce veredictos escritos
debajo. Con el feed correcto sube a **0,98–0,99**.

- 🔬 El módulo se salvó a sí mismo: el aviso `RECONCILIACION ... por debajo de 0.99` salía en las
  doce celdas y decía literalmente «nada de lo que sigue describe el backtest que SQX corrio». La
  puerta funcionaba; lo que faltaba era que el feed no fuese una constante.
- 🔬 El mismo `config.yaml` nombraba XAUUSD en el aviso de costes provisionales, así que cualquier
  activo heredaba la advertencia del oro. Ahora sale de `assetdata.symbol_for(feed)` y
  `assetcheck.provisional()`, así que nombra el activo que de verdad se leyó.
- 🤔 Regla para el resto: **un `config.yaml` puede declarar umbrales y modelos, no de qué activo se
  está hablando.** Eso es propiedad de la corrida y va por la línea de comandos. Quedan por revisar
  los demás: `strategies/sppUltra/`, `strategies/retest/` y `strategies/crossmarket/` toman el
  proyecto por `--project`, pero conviene mirar si alguno guarda un feed.

## 🔬 Every per-strategy report CSV names the strategy in a `strategy` column (2026-09-24)

Checked over every CSV under `reports/` on 2026-09-24: `gate`, `curate`, `crossmarket`, `retest`,
`montecarlo`, `nulls`, `exposure`, `wfc` and `wfm` all write `strategy`; the two exceptions are
the SQX exports copied by `curate` (`Strategy Name`) and `decay.csv` (`name`). The decision word
sits in `verdict` (or `tier` for Monte Carlo) and is one of `MANTENER · DESCARTAR · DUDOSA ·
NO EVALUABLE · FAIL · MARGINAL · worth_it · not_worth_it`. `ui/daemon/studies.py` relies on this
to find what any module said about one strategy without knowing the module: a new report joins the
window by writing that column, and its verdict is coloured by `ui/desktop/theme.state_colour`,
which names any word outside that list instead of hiding it. Report folders are per **project**,
not per databank: a strategy built in `Results` is judged under `OOS`, `SPP_IS` or `MC_Trades`.
