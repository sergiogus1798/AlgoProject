# ui/desktop/workspace — Proyectos → Proyecto → Databanks → Estrategia

The project workspace of encargo 22 §3-§5: the four PROYECTO zones of the sidebar. Proyecto and
Databanks were one zone until the owner split them (2026-09-28): rail, funnel and databank panel
together did not fit a 1080-px screen. Every widget
reads the daemon; the phase-1 mock on invented data (`mock.py`, `fake.py`) and its desktop
shortcut were retired by F13 of plan 24 (2026-09-28): the owner wants only the real window on
this machine.

```
Gallery (gallery) ──click a card──▶ WorkspaceZone (zone)            Proyecto
                                    ├ Launcher (launch) · Advance (advance, its own databank chooser)
                                    ├ Rail (rail)      the workflow, map + play + state
                                    └ Funnel (funnel)  the population's cascade
                                    DatabanksZone (databanks)        Databanks, built and filled by zone
                                    └ FiltersStrip + Panel (panel)  two rows of tabs ─▶ table + aggregate
                                          ──double-click a row──▶ Ficha (ficha)   Estrategia
         every widget ─▶ the daemon · tabs for the rounded-box bars · texts for the families' lines
```

**Imports from:** `ui.desktop.theme`, `ui.text` (`numbers`, `glossary`), `selection`, `client`, `blocks` (the histogram), `studypage` (the ficha's family tabs) · **Consumed by:** `ui/desktop/shell.py`, `projectflow.py`, `portfolios/imported.py`

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Package marker | — | — |
| `gallery.py` | Proyectos: one card per project, as many per row as the viewport holds (1-4); `load` asks `/api/projects/all` off the GUI thread; `opened(name)` on click; `choose(name)` confirms, then loads every databank with strategies and selects the first; `fill` clears the grid first | imported | `/api/projects/all` → cards |
| `zone.py` | Proyecto: `WorkspaceZone` — title and facts, `Launcher`, `Advance`, then the rail (in a `QScrollArea`, `scrolled`) over the funnel in a vertical splitter, the rail given its cards' height up to 70 %; builds the Databanks zone (`databanks`) and exposes its `panel`, so the rail runs on the panel's databank and rows; `fill(name)` fills both zones; `show_tab(tab, sub)` (a card click) selects the panel's tab without switching zone; `see(tab, sub)`, the drawer's «→ ver en Databanks», selects it and emits `databanks_wanted`; `strategy_chosen(identity)` on a double click | imported | `/api/projects/all`, rail/funnel/panel → strips |
| `databanks.py` | Databanks: `DatabanksZone(funnel)`, the title line (project · symbol · TF) and the `Panel` on the whole height with F6's `FiltersStrip` under its header (the strip reloads Proyecto's funnel); `fill(name, symbol, timeframe)` | imported | project → panel |
| `newproject.py` | «+ Nuevo proyecto» under Proyectos' header: template, asset, timeframe, name (`Test_<SYMBOL>_<template>_<TF>` suggested), strategies (500) and minutes (180) of the build, the purpose; its `JobButton` queues `POST /api/create/project` (rule 5, then `builder --workflow` on the custodian) and reloads the gallery when it ends well | imported | form → job |
| `rail.py` | The rail, served by `GET /api/workflow` and, for the ▶ SQX, `GET /api/launch/steps` (`load(project)`, `fill(data)`): header «correr marcados», «todas las pruebas Python pendientes» (once «correr todo»), «rehacer las filas de 17-19»; a second row with the filled «▶▶ Correr workflow (hasta la próxima decisión)» and the plan it would run beside it; cards in rows of ten, the oos2 and blind lines; a card click shows its tests in the drawer and its tab through the workspace's `show_tab(tab, sub)` (else `opened(tab, sub)`); `run_panel(tab, databank, strategies)` is the panel header's «correr los marcados de este panel»; reads both routes off the GUI thread (`landed`, then `loaded(project)`, which sizes the zone's split once per project); its job polling is `railwatch` | imported | project → cards |
| `railwatch.py` | The rail's watch over its project's jobs: `/api/jobs` off the GUI thread every 3 s while visible and something runs; the jobs that ended are gathered and repainted — ONE `finished(study, databank)` and one rail reload — at most every `REPAINT_S` (20 s) while others run and once when the last ends. 🔬 2026-09-28: one repaint per ended job (panel 3.4 s + funnel 0.6 s, 16 per poll) froze the window for a minute | imported | jobs → one repaint |
| `railrun.py` | The run buttons' actions: `tests` (POST /api/workflow/run, asking before what spends oos2 or the ledger), `step` (a card's ▶ PY: its ticked tests, else its free ones; 21-25 on the Databanks panel's databank and rows, after a question naming the databank and the row count), `sqx_step` (preflight → the sentence → only «Sí» posts /api/launch/run with the step), `chain` (GET /api/launch/chain → the plan → only «Sí» posts it), `plan_line`; `configure` (a card's ⚙: opens the «Configuración SQX» section or the «Activos» page `texts.SETTINGS` names and says there whether the change reaches this project; a step without an editing screen opens in the drawer with `texts.NO_SCREEN`) | imported | press → daemon |
| `railgrid.py` | `reflow(grid, cards, width, per_row)`: the step cards in rows of as many as the rail's width holds (3 to 10, `CARD_W` px each), called on fill and on every resize — ten fixed columns ran off a narrower window (owner, 2026-09-28) | imported | cards + width → grid |
| `railrow.py` | `off_reason` (why a step's run button is off, and whether that is a real failure — red only for one, 2026-09-29: a step done elsewhere or simply busy is not); `StepCard`, one step (box, number, «▶ PY» in the accent or «▶ SQX» in amber — dashed grey when off, a real failure in red on the card and in the tooltip, an expected state in the dim colour —, TÚ for the owner's steps, ⚙ left of the run button — `configured(n)`, no «?» of its own —, title, tab › sub, configuration, state) | imported | step → card |
| `railwords.py` | The state and kind words and colours (`STATE`, `KIND`), and the small pieces `railrow.py` and `railconfig.py` both draw a step with: `word`, `ink`, `small`, `runnable`, `run_button`, `gear`; `readable` turns a test's one-line config into labelled knobs with numbers in full (`value_words`) | imported | step → words/widgets |
| `railconfig.py` | The drawer under the rail: the chosen step's tests, each with box, state, one-line configuration, «configuración» (every knob from `/api/config?study&project`, off the GUI thread: the project's feed/symbol/timeframe where the runner puts them, ⚠ where it keeps the donor's) and ▶; «▶ Lanzar todos (N)» above them when more than one can run; the step's note (`texts.STEP_NOTES`: what the preflight checks on 4, what the WFC reads on 17); at the bottom what must run first (`needs`, the missing in red); «correr los marcados de <tab>» and «→ ver en Databanks» (`seen(tab, sub)`: the zone opens Databanks on that tab); for an SQX step «▶ SQX · lanzar el paso N» (step 6: «Activar el builder») with its tasks or why not, in a row of its own so the «?» sits between | imported | step → rows |
| `funnel.py` | The funnel, scrolled so it never sets the window's height: bars to the build's scale, passed green, died red, soft grey, a sealed or running step with no bar; labels through `glossary`, figures through `numbers`; a header row («Criba (pasos del workflow) · Entran → pasan · Razón»), each row's steps in brackets (`name_steps`, from the rail's steps: Build 6, 7; the gate's screens 8; later rows by title), every sentence of a why capitalised; appends `/api/filters/state` (F6) when it answers | imported | `/api/databank/funnel` → bars |
| `panelreload.py` | «Recargar databank»: `POST /api/databank/reload` off the GUI thread, then drop that databank's table, views and curve and read them again, and say what the daemon found | imported | click → repaint |
| `panel.py` | The Databanks zone's panel: «⚙ Métricas» (named «Columnas» until 2026-09-28, when the owner did not find it; its tooltip says the choice is kept per databank), «Recargar databank», «Correr marcados de este panel» (`run_tab` → the rail); two rows of tabs from `/api/databank/panels`; a locked sub-panel shows only its reason; `select(tab, sub)`, `set_hidden`; one table and equity fetch per databank, both off the GUI thread (`fill` → `filled`, `open_sub` → `landed` → `show_payload`); «Recargar databank» is `panelreload`. The table and the aggregate equity share a horizontal `QSplitter` (`body`) the owner drags both ways: the equity keeps half (`SIDE`) of the width until he drags, then Qt keeps his split for the window's session. No fold since the split: the panel has the zone's whole height. Puerta IS/OOS (`TABLE_ONLY`) shows the table alone, no aggregate (owner, 2026-09-28) | imported | `/api/databank/*` → table + aggregate |
| `columns.py` | What one table can show, without Qt: `choices` (today's default columns, then every metric of the databank × IS, OOS, OOS2, IS+OOS1, each with its payload index, the IS+OOS1 metric the daemon computes, or `why` it has no data: «leyendo…», «no se pudo calcular: …», not computed), `shown_ids` (defaults − hidden + added, in the saved order; new defaults at the end) and `diff` (the change to save, unknown ids kept), `resolve`, `value`, `note` (a «–»'s tooltip, «sin operaciones OOS» included), `merged`, `is_metric`, `unprofitable` (the red rule: a profit factor under 1, a profit-signed metric — net, Sharpe, Sortino, expectancy, Ret/DD, CAGR, Calmar, SQN, return — or a study figure below 0; never a drawdown, a loss, a count, % ganadoras or ZScore) | imported | payload + segments → choices |
| `columnsmenu.py` | `ColumnsMenu`, the chooser: a search box (accent-blind), a checkable list grouped by the study's columns and the four segments (the OOS group titled with the span the cosecha's trades name, else «OOS (tramo de la tarea…)»), «— sin datos» with its reason on hover, «Restaurar vista por defecto» / «Cancelar» / «Aplicar columnas»; titled «Métricas · databank D» and says the metrics hold in all its tabs; `answer` is the ids or None | imported | choices → ids |
| `columnsview.py` | `Views(panel)`, the panel's `columns`: GET `/api/databank/columns` and `/segments` in threads (`fetched` lands them, the table repaints; the chooser opens once both landed), a failure said and not kept (asked again on the next paint after `forget`, the chooser or «Recargar»); `offer`, `view`, `keep` (POSTs of the diff: the metrics under `WIDE` for the whole databank, the study columns under «tab › sub»; refused → kept for the session only, and said), `choose` («⚙ Métricas») | imported | panel ↔ `/api/databank/columns`, `/segments` |
| `curves.py` | Two cumulative equity curves (SQX, real spread and slippage), each switchable, with the IS/OOS1 boundary; the y axis as wide as its widest figure (`numbers.num`), taken over by F4 (`Curves`, the databank's aggregate). `SampleCurves`, the Estrategia page's: each curve in its IS tone then its OOS tone (`blocks.states.CURVE`: violet SQX, orange → red real), round money ticks and one tick per calendar year | imported | series → painting |
| `tabs.py` | The tab bars; the rounded box is theme.py's rule, the second row a step smaller | imported | labels → QTabBar |
| `table.py` | The databank table: `pick`, today's default columns of one sub-panel (name, base SQX metrics IS then OOS, the study's own columns); `paint` draws the chosen ones (`columns.resolve`), a missing metric as a grey «–» (a missing study value stays blank), keeping only the rows the sub-panel's own study judged even when its columns are hidden; sorting on values; verdict states in colour and, in red, a figure that says the strategy loses (`columns.unprofitable`: PF < 1, net / Sharpe / Ret/DD… < 0 — never a drawdown); only a study's last column stretches; headers dragged to a new place emit `reordered(ids)` (the name is put back in front); double click → identity | imported | payload → QTableWidget |
| `aggregate.py` | The databank's aggregate equity beside the table, as wide as the panel's splitter gives it (300 px at least) and the curve taking the whole width and height left: the two curves with switches, the IS/OOS boundary and stats — no source line under them since 2026-09-28 (owner); why the real curve is missing is its switch's tooltip; `load` posts `/api/databank/equity` with the visible identities when a filter hid rows and says «de todas las filas» or «N visibles»; `ask`, the panel's GET that turns a silent daemon into an `error` | imported | `/api/databank/equity` → painting |
| `ficha.py` | Estrategia: head with «Archivar», the fold and the small «metadatos» button; the basic panel (curves + stats) and, under a splitter, the study page's family tabs on the whole width (`studypage.views.StrategyPage`, opened on the origin panel's study or family, `fichaorigin.default_study`, each with its one-line description). `jump` follows a study's «→ abrir en …» to the same name in that study's databank. Reads `/api/strategy/{costcurve,stats,meta}` off the GUI thread, passing the name so a databank without a cosecha borrows the project's; the borrowed one is named in the top-right line | imported | SELECTION → page |
| `fichaorigin.py` | `ORIGIN_FAMILY` and `ORIGIN_STUDY`/`default_study`: which family tab, and which study inside it, a strategy page opens on by the databank panel (and sub-panel) it was opened from — a Cross Market strategy opens on Cross Market, a Mapa condicional one on the conditional map, never a sibling sharing the family (owner, 2026-09-30 §4.3/§9.4) | imported | (tab, sub) → study key |
| `fichacurves.py` | The two curves (`SampleCurves`) with their switches and a key naming the four tones (SQX · IS, SQX · OOS1, spread y slippage · IS, · OOS1), the nets and DDs, the source; without a `spread` report the real one says «no calculado» with its two buttons | imported | `/api/strategy/costcurve` → painting |
| `fichastats.py` | IS / OOS1 / IS+OOS1 / OOS2 (disabled with its reason while `blocked`), the unit (USD por lote by default), the figures — Operaciones, both nets and Profit Factor one step larger — and the return's mean, std, skew and kurtosis in short units («20.98 $/lote»), and the trade histogram drawn by `blocks.kinds.draw` on the wider side | imported | `/api/strategy/stats` → grid + chart |
| `fichameta.py` | The metadata, in `MetaWindow` — a window of its own opened by «metadatos», no longer a column (owner, 2026-09-30): direction, each signal and condition, orders, money management, Friday close, asset, the last test and its costs, an amber line per task whose costs differ, E2's notes, where the .sqx came from | imported | `/api/strategy/meta` → rows |
| `fichajobs.py` | `Compute`: «calcular» / «todo el databank» → `POST /api/study/run` (scope one/many), polls `/api/jobs`, `done` redraws the ficha; `uncomputed(study, compute)` builds the cell | imported | press → jobs |
| `fichaarchive.py` | The «Archivar» dialog: the step (no default: the rail's last «hecho» can be a reading past a sealed 17-19) and the note | imported | — → `{step, note}` |
| `filters.py` | F6: `FiltersStrip(panel, funnel)`, the strip under the panel's header — AND rows, «▶ Aplicar» (replaces the filter in force, judged on the whole databank: loosening brings rows back), «Quitar filtros», «Descartar seleccionadas» (kept across re-filters), the saved list; a live count under the rows (`/api/filters/preview`, 350 ms after the last edit, hides and logs nothing); on the table's `modelReset` it reads the databank's state and shows its conditions in force, calls `panel.set_hidden(ids)` (which re-aggregates the visible ids) and `funnel.load`. Mounted with one line in `databanks.py`: `self.panel.layout().insertWidget(1, FiltersStrip(self.panel, funnel))` | imported | `/api/filters/*` → hidden rows |
| `filterrow.py` | One condition of the strip: metric (from `/api/filters/metrics`, never OOS2), operator by the metric's kind, value (two for «entre», an interval % for a distribution), «×»; `changed` on every edit, `filled` false for an empty row | imported | metrics → one row |
| `filtersaved.py` | The strip's saved filters: dropdown, «Cargar» (fills the rows, does not apply), «Guardar con nombre…» | imported | `/api/filters/saved` ↔ rows |
| `texts.py` | The owner's one-line description of each family of studies (`FAMILIES`), shown above the ficha's tabs; moved out of the retired `fake.py` by F13. `PREFLIGHT` (both preflights' real checks, in plain Spanish), `STEP_NOTES`, `SETTINGS` (step → the zone and section its ⚙ opens), `NO_SCREEN`, `NOT_YET`, `STUDY_NOW` | imported | — |
| `launch.py` | `Launcher`, «▶ Lanzar en SQX»: every task of the project in a dropdown with its input and output counts, the button, and why it is off; re-checks every 20 s; off until a preflight passes (on `aim`, on showing, every 20 s); a click re-runs `/api/launch/preflight` for the project and task on screen, shows that fresh sentence and only «Sí» posts `/api/launch/run` (owner, 2026-09-28) | imported | `/api/launch/*` → button |
| `advance.py` | F7: `Advance`, in Proyecto under «Lanzar en SQX»: «CONTINUAR SOBRE» and its own databank chooser (the project's live databanks, from the panel's unlocked sub-panels; the default is the first with discards, else the one Databanks shows, and it is pinned once on screen or picked — dropped only on a project change, `repoint` from `zone.fill` even while hidden, or a queued Continuar), «▶▶ Continuar workflow» and every reason it is off (a disabled button shows no tooltip); `attach(panel, funnel)` re-aims on each table the panel paints, on showing and every 20 s; a click re-runs the preflight, shows its fresh literal §7.2 sentence in a `QMessageBox` and only «Sí» posts `/api/advance/run`. `ui/daemon/advance` unchanged | imported | `/api/advance/*` → button |

## What each strip reads

| strip | routes (each package's README has the shapes) |
|---|---|
| gallery | `GET /api/projects/all` (`ui/daemon/projects/`) |
| rail | `GET /api/workflow`, `POST /api/workflow/run`, `/backfill`, `GET /api/jobs` (`ui/daemon/workflow/`); `GET /api/launch/steps`, `/preflight?step`, `/chain`, `POST /api/launch/run`, `/chain` (`ui/daemon/launch/`) |
| funnel | `GET /api/databank/funnel`, `/api/filters/state` |
| panel | `GET /api/databank/panels`, `/table`, `/columns`, `/segments`, `POST /api/databank/equity`, `/columns`, `/reload` (`ui/daemon/databank/`) |
| ficha | `GET /api/strategy/costcurve`, `/stats`, `/meta`, `POST /api/strategy/archive`, `/api/study/run` (`ui/daemon/strategy/`) |
| filters, «Continuar» | `/api/filters/*`, `/api/advance/*` (`ui/daemon/filters/`, `ui/daemon/advance/`) |

## Traps

- **Step 20's panel exists and is locked.** Its sub-panel under Cierre is listed from the start
  and paints only «BLOQUEADO — …» with the reason: no table, no curve, no figure, so nothing of
  oos2 is read before 17, 18 and 19 are done (encargo 22 §4.1).
- **A grid is emptied before it is refilled.** Without `takeAt` + `deleteLater`, opening a second
  project stacked its 28 cards on top of the first project's.

- **A disabled button never shows its tooltip.** OOS2 and the blocked step 20 write their reason
  as a visible line beside them; the tooltip would be unreadable.
- **The rail's lines have an ignored width.** Ten cards share one row; a long line is cut rather
  than widening every card and the window past the screen.
- **A long status line wraps, never widens.** The panel's line under its header and the zone's
  facts line are word-wrapped with an ignored horizontal size: unwrapped, the ledger's sealing
  sentence (~3,000 px) set the whole window's minimum width to 3,867 px. Since the split
  (2026-09-28) Proyecto's minimum is 628 × 353 px and Databanks' 1,191 × 534 px (set by the
  filters strip's head row; the table ↔ equity splitter needs only 667 px: 360 + 300 + the
  handle); both fit a 1600 × 1000 window, checked on offscreen grabs at 1600 × 1000 and
  1920 × 1050.
- **A rail card click does not switch zone.** It selects the step's tab in Databanks, so opening
  Databanks shows it; the drawer's «→ ver en Databanks» is the one that switches. Switching on
  every click would throw the owner out of the rail while he reads the steps.
- **«Continuar workflow» acts on its own chooser, not on the panel on screen.** It sits in
  Proyecto, where no databank is visible: the chooser says which databank loses its discards,
  and the confirmation sentence names it again.
- **The metric choice is per databank, the study columns per table, and both live in
  AlgoData.** `columns.json` beside the databank's filter log: the metrics under «métricas»
  (`columnsview.WIDE`), shown in every tab of that databank (owner, 2026-09-28: «se guarda por
  databank»); each table's study columns under «tab › sub», so hiding the gate's verdict in
  «Build + OOS1» does not blank «Cribas». Each a diff against today's default:
  `{hidden, added, order}`; metrics are painted before the study's columns. A default column that appears later (a new study) shows by
  itself; an id the databank does not offer now is kept in the file and not shown. Ids are
  `Metric|SAMPLE` (IS, OOS, OOS2, IS+OOS1) or a study column's key. «OOS» is never called
  OOS1 unless the cosecha's trades say so. Blanks and «–» sort last both ways (`Cell.__lt__`
  reads the header's sort order). Hidden
  columns change nothing of what a filter or the funnel reads: they work on the daemon's
  whole payload, by identity. OOS2 columns read only what a cosecha carries (none today) and
  write no Ledger row.
- **A step's ⚙ edits the doctrine, not this project's tasks.** «Configuración SQX» writes
  `assets/_build.yaml` and friends, read when a project is built or a step's configurator runs;
  «▶ SQX» only switches tasks on (`stage.just`) and never rewrites them. The zone says so on
  arrival (`texts.NOT_YET`). WFC and CSCV study values (17, 18) are read again on the next run.
  Steps 5, 8, 10, 12, 14, 16, 18.5 and 20-25 have no editing screen: their ⚙ says so.
- **Table figures sort as numbers.** `table.Cell` keeps the value and compares on it; sorting
  on the text would put 9.292 after 10.123.
- **Labels through `ui.text.glossary.label`, figures through `ui.text.numbers.num`**, never
  formatted locally.
