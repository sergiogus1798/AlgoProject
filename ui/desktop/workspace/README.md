# ui/desktop/workspace — Proyectos → Proyecto → Estrategia

The project workspace of encargo 22 §3-§5: the three PROYECTO zones of the sidebar. Every widget
reads the daemon; the phase-1 mock on invented data (`mock.py`, `fake.py`) and its desktop
shortcut were retired by F13 of plan 24 (2026-09-28): the owner wants only the real window on
this machine.

```
Gallery (gallery) ──click a card──▶ WorkspaceZone (zone) ──double-click a row──▶ Ficha (ficha)
                                    ├ Rail (rail)      the workflow, map + play + state
                                    ├ Funnel (funnel)  the population's cascade
                                    └ Panel (panel)    databanks, two rows of tabs ─▶ table + aggregate
         every widget ─▶ the daemon · tabs for the rounded-box bars · texts for the families' lines
```

**Imports from:** `ui.desktop.theme`, `ui.text` (`numbers`, `glossary`), `selection`, `client`, `blocks` (the histogram), `studypage` (the ficha's family tabs) · **Consumed by:** `ui/desktop/shell.py`, `projectflow.py`, `portfolios/imported.py`

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Package marker | — | — |
| `gallery.py` | Proyectos: one card per project, as many per row as the viewport holds (1-4); `load` asks `/api/projects/all` off the GUI thread; `opened(name)` on click; `choose(name)` confirms, then loads every databank with strategies and selects the first; `fill` clears the grid first | imported | `/api/projects/all` → cards |
| `zone.py` | Proyecto: `WorkspaceZone`, the header and the three strips in a vertical splitter; `fill(name)` reads the daemon; `show_tab(tab, sub)` for the rail, `set_hidden(identities)`, F6's `FiltersStrip` mounted under the panel's header, `strategy_chosen(identity)` on a double click; folds the panel's height into the funnel | imported | `/api/projects/all`, rail/funnel/panel → strips |
| `rail.py` | The rail, served by `GET /api/workflow` (`load(project)`, `fill(data)`): cards in rows of ten, the oos2 and blind lines, «correr marcados», «correr todo», «rehacer las filas de 17-19»; a card click shows its tests in the drawer and its tab through the workspace's `show_tab(tab, sub)` (else `opened(tab, sub)`); `run_panel(tab, databank, strategies)` is the panel header's «correr los marcados de este panel»; polls `/api/jobs` only while visible and something of the project runs, and emits `finished(study, databank)` per ended job | imported | project → cards |
| `railrow.py` | One step card (box, number, SQX/PY/TÚ, ▶ only for Python steps, title, tab › sub, configuration, state) and the state words and colours; `readable` turns a test's one-line config into labelled knobs with numbers in full | imported | step → card |
| `railconfig.py` | The drawer under the rail: the chosen step's tests, each with box, state, one-line configuration, «configuración» (every knob from `/api/config`) and ▶; «correr los marcados de <tab>» | imported | step → rows |
| `funnel.py` | The funnel, scrolled so it never sets the window's height: bars to the build's scale, passed green, died red, soft grey, a sealed or running step with no bar; labels through `glossary`, figures through `numbers`; appends `/api/filters/state` (F6) when it answers | imported | `/api/databank/funnel` → bars |
| `panel.py` | The databank panel: fold, «Recargar databank», «correr marcados de este panel» (`run_tab` → the rail); two rows of tabs from `/api/databank/panels`; a locked sub-panel shows only its reason; `select(tab, sub)`, `set_hidden`; one table and equity fetch per databank | imported | `/api/databank/*` → table + aggregate |
| `curves.py` | Two cumulative equity curves (SQX, real spread and slippage), each switchable, with the IS/OOS1 boundary; the y axis as wide as its widest figure (`numbers.num`), taken over by F4 | imported | series → painting |
| `tabs.py` | The tab bars; the rounded box is theme.py's rule, the second row a step smaller | imported | labels → QTabBar |
| `table.py` | The databank table: the columns one sub-panel shows (`pick`: name, base SQX metrics IS then OOS, the study's own columns), sorting on values, negatives and verdict states in colour, double click → identity | imported | payload → QTableWidget |
| `aggregate.py` | The databank's aggregate equity beside the table: the two curves with switches, the IS/OOS boundary, stats and source; `load` posts `/api/databank/equity` with the visible identities when a filter hid rows and says «de todas las filas» or «N visibles»; `ask`, the panel's GET that turns a silent daemon into an `error` | imported | `/api/databank/equity` → painting |
| `ficha.py` | Estrategia: head with «Archivar» and the fold; the basic panel (curves + stats) and, under a splitter, the study page's family tabs (`studypage.views.StrategyPage`, opened on the origin panel's family, each with its one-line description) beside the metadata column. Reads `/api/strategy/{costcurve,stats,meta}` off the GUI thread | imported | SELECTION → page |
| `fichacurves.py` | The two curves with their switches, the nets and DDs, the source; without a `spread` report the real one says «no calculado» with its two buttons | imported | `/api/strategy/costcurve` → painting |
| `fichastats.py` | IS / OOS1 / OOS2 (disabled with its reason while `blocked`), the unit (USD por lote by default), the figures and the return shape, and the trade histogram drawn by `blocks.kinds.draw` | imported | `/api/strategy/stats` → grid + chart |
| `fichameta.py` | The metadata column: direction, each signal and condition, orders, money management, Friday close, asset, the last test and its costs, an amber line per task whose costs differ, E2's notes, where the .sqx came from | imported | `/api/strategy/meta` → rows |
| `fichajobs.py` | `Compute`: «calcular» / «todo el databank» → `POST /api/study/run` (scope one/many), polls `/api/jobs`, `done` redraws the ficha; `uncomputed(study, compute)` builds the cell | imported | press → jobs |
| `fichaarchive.py` | The «Archivar» dialog: the step (no default: the rail's last «hecho» can be a reading past a sealed 17-19) and the note | imported | — → `{step, note}` |
| `filters.py` | F6: `FiltersStrip(panel, funnel)`, the strip under the panel's header — AND rows (metric from `/api/filters/metrics`, never OOS2; operator by the metric's kind; value, two for «entre», an interval % for a distribution), «▶ Aplicar», «Quitar filtros», «Descartar seleccionadas», the saved list; follows the panel's databank on the table's `modelReset`, calls `panel.set_hidden(ids)` (which re-aggregates the visible ids) and `funnel.load`. Mounted with one line in `zone.py`: `self.panel.layout().insertWidget(1, FiltersStrip(self.panel, self.funnel))` | imported | `/api/filters/*` → hidden rows |
| `filtersaved.py` | The strip's saved filters: dropdown, «Cargar» (fills the rows, does not apply), «Guardar con nombre…» | imported | `/api/filters/saved` ↔ rows |
| `texts.py` | The owner's one-line description of each family of studies (`FAMILIES`), shown above the ficha's tabs; moved out of the retired `fake.py` by F13 | imported | — |
| `advance.py` | F7: `Advance`, «▶▶ Continuar workflow» and, beside it, every reason it is off (a disabled button shows no tooltip); `attach(panel)` re-aims on each table the panel paints and every 20 s; a click shows the literal §7.2 sentence in a `QMessageBox` and only «Sí» posts `/api/advance/run`. Mounted with one line in `zone.py`: `self.panel.layout().itemAt(0).layout().addWidget(Advance().attach(self.panel))` | imported | `/api/advance/*` → button |

## What each strip reads

| strip | routes (each package's README has the shapes) |
|---|---|
| gallery | `GET /api/projects/all` (`ui/daemon/projects/`) |
| rail | `GET /api/workflow`, `POST /api/workflow/run`, `/backfill`, `GET /api/jobs` (`ui/daemon/workflow/`) |
| funnel | `GET /api/databank/funnel`, `/api/filters/state` |
| panel | `GET /api/databank/panels`, `/table`, `POST /api/databank/equity`, `/reload` (`ui/daemon/databank/`) |
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
  sentence (~3,000 px) set the whole window's minimum width to 3,867 px. The zone's minimum
  width is now 978 px, set by the rail.
- **Table figures sort as numbers.** `table.Cell` keeps the value and compares on it; sorting
  on the text would put 9.292 after 10.123.
- **Labels through `ui.text.glossary.label`, figures through `ui.text.numbers.num`**, never
  formatted locally.
