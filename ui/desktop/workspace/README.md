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
| `__init__.py` | The project workspace: the gallery, one project's three strips and one strategy's page. | — | — |
| `advance.py` | «Continuar workflow»: the one button of the window that deletes in SQX, behind its preflight. | imported | `/api/advance/*` → button |
| `aggregate.py` | The databank's aggregate equity beside the table: SQX's curve, with stats. | imported | `/api/databank/equity` → painting |
| `card.py` | One project's card in the Proyectos gallery. | imported by `gallery.py` | a `/api/projects/all` row → widget |
| `columns.py` | Which columns one databank table can show: today's default, and every metric per segment. | imported | payload + segments → choices |
| `columnsmenu.py` | The column chooser of one databank table: a checkable list by segment, with a search box. | imported | choices → ids |
| `columnsview.py` | The panel's column views: the metric choice per databank, read off the GUI thread and kept. | imported | panel ↔ `/api/databank/columns`, `/segments` |
| `curves.py` | SQX's cumulative equity curve, switchable, with the IS / OOS1 boundary. | imported | series → painting |
| `databanks.py` | Databanks: the project's databank panel on the whole height, with its filters strip. | imported | project → panel |
| `ficha.py` | Estrategia: the fixed basic panel and the family tabs of one strategy (22 §5); its metadata on a button. | imported | SELECTION → page |
| `fichaarchive.py` | «Archivar»: the dialog that asks the step and the note before the ficha freezes the strategy. | imported | — → `{step, note}` |
| `fichacurves.py` | The ficha's equity: SQX's curve, IS and OOS1 in two tones. | imported | `/api/strategy/costcurve` → painting |
| `fichajobs.py` | The ficha's «calcular» buttons: one study queued for this strategy or the whole databank, then watched. | imported | press → jobs |
| `fichameta.py` | The ficha's metadata column: what the strategy is built from and how it was backtested (E2's fields). | imported | `/api/strategy/meta` → rows |
| `fichaorigin.py` | Which family tab, and which study, a strategy page opens on by the databank it came from. | imported | (tab, sub) → study key |
| `fichastats.py` | The ficha's basic statistics: IS / OOS1 / IS+OOS1 / OOS2 (behind its door), the figures and the trade distribution. | imported | `/api/strategy/stats` → grid + chart |
| `filterrow.py` | One condition of the filters strip: metric, operator, value, and «×». | imported | metrics → one row |
| `filters.py` | The databank panel's filters strip: AND rows over real columns, discards, and the ledger (22 §7.1). | imported | `/api/filters/*` → hidden rows |
| `filtersaved.py` | The filters strip's saved list: keep the rows on screen under a name, and bring one back. | imported | `/api/filters/saved` ↔ rows |
| `funnel.py` | The middle strip of a project: the population's funnel, and why the fallen fell (22 §4.2). | imported | `/api/databank/funnel` → bars |
| `gallery.py` | Proyectos: one card per project — symbol, timeframe, strategies, template, state (22 §3). | imported | `/api/projects/all` → cards |
| `launch.py` | «Lanzar en SQX»: pick any task of the project and run it on its worker, behind a confirmation. | imported | `/api/launch/*` → button |
| `newproject.py` | «+ Nuevo proyecto»: the form under Proyectos' header that creates a workflow project. | imported | form → job |
| `panel.py` | The Databanks zone's panel: one project's databanks, SQX-style, with two rows of tabs. | imported | `/api/databank/*` → table + aggregate |
| `panelreload.py` | «Recargar databank»: the daemon relists the databank's folder off the GUI thread, then a repaint. | imported | click → repaint |
| `rail.py` | The top strip of a project: the workflow rail as map, automation panel and state (22 §4.1). | imported | project → cards |
| `railconfig.py` | The rail's drawer: one step's tests, each with its box, state, configuration and run button. | imported | step → rows |
| `railgrid.py` | The rail's step cards laid in rows as wide as the rail holds. | imported | cards + width → grid |
| `railrow.py` | One card of the rail: a step's box, number, kind, title, target tab, configuration and state. | imported | step → card |
| `railrun.py` | The rail's buttons: Python tests, one SQX step, «Correr workflow» — each behind its question — and each step's ⚙. | imported | press → daemon |
| `railwatch.py` | The rail's watch over its project's jobs: polled off the GUI thread, repaints grouped. | imported | jobs → one repaint |
| `railwords.py` | Words, colours and small widgets the rail and its drawer both draw a step's card with. | imported | step → words/widgets |
| `table.py` | The databank panel's table: the columns one sub-panel shows, sortable and movable, losers in red. | imported | payload → QTableView |
| `tablemodel.py` | The databank table's model: one sub-panel's cells read off the payload, sorted and filtered. | imported | payload → cells |
| `tabs.py` | The workspace's tab bars: the active tab as a rounded box, not an underline (encargo 22 §5). | imported | labels → QTabBar |
| `texts.py` | The owner's words the workspace shows: each family's line, the preflight, step notes, where each ⚙ goes. | imported | — |
| `zone.py` | Proyecto: one project's workflow — launchers, rail and funnel; its databanks live in Databanks. | imported | `/api/projects/all`, rail/funnel/panel → strips |

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
