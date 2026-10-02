# ui/desktop — the window

PySide6. Draws what the daemon says, and asks the daemon for every change. **No view here opens a
file, reads a CSV or imports `core/` for anything but the port.**

```
launch ─▶ shell ─▶ nav (the sidebar in four groups) · contextbar (Proyectos › proyecto › estrategia)
                   BIBLIOTECA
                   coverage  (la matriz, lo primero que se ve)
                   catalogue ─▶ detail · shape   (la lista y la ficha de una plantilla)
                   chat                  (la entrevista → borrador + comando)
                   palettes ─▶ palettebar · blocktable   (la librería de paletas)
                   assets ─▶ assetlist · assetcard · assetspans · assetforms · yamltree
                   sqxconfig/ (Configuración SQX) · datazone/ (Datos)
                   PROYECTO
                   workspace/ ─▶ Gallery (Proyectos) · WorkspaceZone (Proyecto: lanzadores,
                                 «Continuar workflow», raíl, embudo) ─▶ DatabanksZone (Databanks:
                                 filtros, pestañas, tabla, equity agregada)
                   projectflow.StrategyZone (Estrategia) ─▶ workspace.Ficha ─▶ studypage/ · blocks/
                                                         └▶ portfolios.ImportedFicha (archivada)
                   OPERACIÓN
                   ops/ ─▶ Running (En marcha) · Ledger (Registro de búsquedas) · JobsBar (barra de estado)
                   PORTFOLIOS
                   portfolios/ ─▶ PortfoliosZone ─▶ «Importar» ─▶ Estrategia
             all of them ─▶ client ─▶ the daemon · labels and figures ─▶ ui/text
```

**Imports from:** `ui/text` (labels, figures); `ui/daemon` never — only its HTTP surface ·
**Consumed by:** nobody

The PROYECTO group was six zones, three since F13 of plan 24 (2026-09-28), and four since the
same day's split of Proyecto into Proyecto (the workflow) and Databanks (the databank panel). The five older
zones — the step rail, the strategies × studies matrix, the population's study page, the first
strategies zone and the step-8 gate zone — were retired with their files (`studies.py`,
`strategytable.py`, `resultspanel.py`, `gate.py`, `scorecard.py`, `gatedetail.py`,
`equitychart.py`, `funnel.py`, `soon.py`, `matrix/`, `workflow/`, and `generation.py`, which F11
folded into En marcha); their content lives in Proyecto
(the rail, the funnel), Databanks (the databank panel with every study's columns) and Estrategia (the ficha
and the study tabs). The mock on invented data (`workspace/mock.py`, `fake.py`) went with them.

| file | what it does | run it | in → out |
|---|---|---|---|
| `launch.py` | Start the daemon if absent (replacing an idle one on older code), then open the window; `--zone Z` opens on a zone, `--shot DIR` saves `DIR/<zone>.png` and exits, `--port P` talks to (or starts) the daemon on another port so a shot never touches the owner's | `bin/algoui` | — |
| `shell.py` | The single window: every zone built by name and wired (gallery → Proyecto, drawer's «→ ver en Databanks» → Databanks, panel → Estrategia, PORTFOLIOS' «Importar» → the archived ficha), the context bar, the stack, the read-only banner, the status line with the jobs strip; `open_zone(name)` for the launchers, `go_to(item)` for Ctrl+K | imported | — |
| `nav.py` | The sidebar: the five groups (BIBLIOTECA, PROYECTO, OPERACIÓN, PORTFOLIOS, MT5 BRIDGE), one checkable button per zone with its tooltip; «Recargar» at the foot, its tooltip naming what it reloads (`reload_tip`) | imported | — |
| `contextbar.py` | The fixed bar on top: `Proyectos › proyecto › estrategia` from `SELECTION`, each crumb opening its zone (the gallery when no project is chosen); databank and asset beside them; the identity only in the strategy crumb's tooltip | imported | selection → crumbs |
| `loadbar.py` | Beside the crumbs: the selected databank's metrics, trades and cosecha as three chips. Choosing a databank loads what it lacks; polls while loading; `loaded(piece)` makes the shell redraw; ↻ retries what failed | imported | selection → `/api/load` |
| `selection.py` | `SELECTION`: the one global project/databank/strategy/identity/asset, signal `changed(dict)`; a new project clears what hangs below it | imported | choose → signal |
| `projectflow.py` | Proyectos → Proyecto → Estrategia: `StrategyZone` (the live ficha, or `portfolios.ImportedFicha` for the version PORTFOLIOS imported: `show_archived(identity, version)` after `/api/archive/show`), a strategy found by identity (`/api/projects/find`, else the row the panel shows), and the two zones refilled when SELECTION moved on | imported | — |
| `cmdpalette.py` | The command palette on **Ctrl+K**, bound in `shell.py`: zones (with aliases: «ledger» finds Registro de búsquedas), projects and databanks from the gallery, the chosen databank's strategies, and — with a strategy chosen — the studies that speak per strategy, opened on its ficha; Enter goes through `Shell.go_to`. A focused text field keeps Ctrl+K | Ctrl+K | gallery/matrix/catalogue → navigation |
| `cmdrank.py` | What Ctrl+K lists and in which order: the accent-blind fuzzy match, the zones' `ALIASES`, and the last ten choices in `QSettings` (per viewer, never AlgoData) | imported | query → ranked items |
| `theme.py` | The one design system: the palette `C`, the terminal look `T`, the stylesheet, and the two smallest pieces every zone draws with (`rule()`, `kicker(text)`) | imported | — |
| `buttonstyle.py` | How a button looks in both looks (`qss(C, T, mono)`, appended by `theme`): lit when it can be pressed — accent edge over a fill brighter on top, a brighter edge and fill on hover, darker when pressed, accent fill when checked — and inert when it cannot (dim text, dashed dark edge); `#nav`, `#primary` and the «?» mark (`QLabel#helpmark`) | imported | — |
| `helpmark.py` | The «?» beside every button (owner, 2026-09-28): `install(app)` puts one application-wide event filter that, on a button's first show, sets the hand cursor and places a round mark whose tooltip is the button's `help` property or the registry sentence (`ui/text/buttonhelp`), merged with the button's own tooltip (a near-copy is said once). In a horizontal box the mark is inserted right after the button; anywhere else it floats (child of the button's parent, in no layout) right of the button when that strip is free, else over the button's spare right edge, else it hides — it never widens a button and never takes a grid cell. Each mark filters its own button: visibility, move, resize, reparent (re-placed in the new parent), destruction (it forgets the button at once). No mark for `#nav`, flat section heads, the breadcrumbs, Qt's internal buttons (tab bars, combos, dialog boxes, calendars) or `helpmark=False` | imported | — |
| `combofix.py` | Every `QComboBox` popup grows to every option the screen can hold, upwards when the space below runs out, and scrolls beyond (2026-10-01, §1): one application-wide event filter, `install(app)`. The «2 of 4» was Qt's menu-style popup reserving two scroll-arrow strips inside the rows' height; the theme now uses the plain list popup | imported | — |
| `background.py` | Daemon calls off the GUI thread: `run(work, done, key, owner)`, `get`, `post` on a 4-thread `QThreadPool`; the answer lands in `done` on the GUI thread through one relay object; `key` keeps only the newest answer per stream; a deleted `owner` drops it. Every poll and every reload uses it (owner, 2026-09-28: «la UI se congela») | imported | work → callback |
| `client.py` | The only way out to the daemon; `aim(port)` points it at another port (`launch --port`, `tools/uiwalk.py`) | imported | path → JSON |
| `coverage.py` | The matrix of what has been tried, and the counts above it | imported | — |
| `catalogue.py` | The list of templates and drafts, filtered | imported | — |
| `detail.py` | One template's page, and the two writes it makes | imported | — |
| `shape.py` | The panel saying which of a template's holes are free, which are bound to a group, and what it fixes | imported | — |
| `chat.py` | The interview that ends in a draft brief, a prompt and «▶ Crear la plantilla con Claude» (`jobbutton`, `POST /api/create/template`) | imported | — |
| `jobbutton.py` | `JobButton(text, path, body, confirm, ended)`: a confirmation, one POST that queues a daemon job, then `/api/jobs` every 4 s with the job's state and its log's last lines (the author's `PREGUNTA:`/`YA EXISTE:`/`PLANTILLA:` lifted out) under the button | imported | press → job |
| `palettes.py` | The palette library: the open palette, its blocks by category, and the writes | imported | — |
| `palettebar.py` | The palette view's top bar: the picker, the policy, the search and the library actions | imported | — |
| `blocktable.py` | The table of blocks under one palette, and the override picker on each row | imported | — |
| `assets.py` | The asset zone: one page per instrument (`AssetPage`), one per row at full width — costs and windows on the left, a `Características` tile on the right — the index down the left scrolling to them | imported | — |
| `assetlist.py` | The index down the left: the instruments coloured by what they still need | imported | — |
| `assetcard.py` | One asset's costs, its chips and everything the preflight would complain about — its cost table is just field/use/unit now (owner, 2026-10-01: the live-SQX column is gone from every asset table) | imported | — |
| `assetspans.py` | The same asset's windows: a tramo card per segment (its spread note and its two date selectors) beside what SQX actually has, and the MC Retest ranges | imported | — |
| `assetmarkets.py` | `CrossMarketCheck`: «Declarar como main» for an asset that is not one yet, «Añadir»/«Quitar» a market once it is, one coloured group per category | imported | — |
| `assetforms.py` | The boxes the zone opens: a text, a cost with its `why`, a Cross Market row, a new asset | imported | — |
| `assettable.py` | The read-only table helpers shared by `assetcard.py` and `assetspans.py`: `grid`, `cell`, `val`, `derived`, `fit`, `clear`, `send` | imported | — |
| `assettraits.py` | `TRAITS`: a one-paragraph, non-exhaustive note per symbol on how it tends to trade (trend, rango, carry) — a starting point for the `Características` tile, not a study | imported | — |
| `yamltree.py` | Any `assets/` file as a table of its values, each one beside its own comment | imported | — |
| `durations.py` | How «En marcha» prints a duration, a processed-over-total, a time per strategy, and the 0-100 share a task's bar shows (`share`) | imported | — |

The zones' packages, each with its own README:

| folder | what it holds |
|---|---|
| `workspace/` | «Proyectos», «Proyecto», «Databanks» and the live «Estrategia» (encargo 22 §3-§5): the gallery on `/api/projects/all`; the workspace zone (launchers, F7's «Continuar workflow», rail, funnel); the Databanks zone (databank panel, F6's filters); the ficha (curves, IS/OOS1/OOS2 statistics, «Archivar», the study tabs below, the metadata on a button) |
| `studypage/` | The study tabs the ficha embeds (`StrategyPage`): family and study tabs, the result, config drawer, run bar, history, compare; the «Ficha» sub-tabs (IS/OOS, Salidas, Contra el subyacente, Operaciones, Lote) |
| `blocks/` | One widget per contract block kind, `ResultView` (a result, or two compared), the state → colour map every view imports |
| `tradegallery/` | The Ficha's «Operaciones»: five trades by P&L quantile, or five seeded at random, each on its bars |
| `batchview/` | The Ficha's «Lote»: a mother's variant batch in parallel coordinates, coloured by NetProfit oos1 or build; shown only when the batch exists |
| `ops/` | «En marcha» (the custodian's pulse and one project's tasks on one screen), «Registro de búsquedas» (the ledger, read-only) and the jobs strip with a 0-100 % bar per job and per SQX run |
| `datazone/` | «Datos» (BIBLIOTECA): the catalogue of AlgoData, each asset's bars at D1/H4/H1, and its real spread, spread band and feed quality drawn with `ResultView`; `DataZone` is what the sidebar wires |
| `sqxconfig/` | «Configuración SQX» (BIBLIOTECA): every setting a new project is built and tested with, one foldable section per test, dropdowns where the values are fixed, writes through the daemon to `assets/`; `SqxConfigZone` is what the sidebar wires |
| `portfolios/` | «Portfolios» (PORTFOLIOS): the archived strategies and their versions; «Importar» emits `import_requested(identity, version)` and `ImportedFicha` shows the version as the Estrategia page, every read on `source=archive`, nothing computed; `PortfoliosZone` is what the sidebar wires |
| `research/` | «Investigar» (BIBLIOTECA): `ResearchZone` — the profile's map (asset × timeframe, colour = dominant passing family, three discrete intensities, a click for the measures each with its explanation), the memory, «▶ Proponer investigación» with the board and the director's steps, and the proposal: three ideas with a veto each, their open questions, «▶ Crear plantillas y lanzar en SQX» behind `/api/research/launch`'s sentence, and the queue (its own README) | imported by `shell.py` | daemon → four tabs |
| `mt5bridge/` | «Verificar» (MT5 BRIDGE): `VerifyZone` — the form (the strategy chosen in Proyecto or an archived one, the window as two typed dates, the tester's model and the firms, none of them defaulted), «▶ Verificar en SQX y en MT5» as a `JobButton` whose confirmation is `/api/mt5bridge/preflight`'s text or its reasons, every past check (`/api/mt5bridge/runs`) and the chosen one's result drawn by `blocks.result.ResultView` | imported by `shell.py` | daemon → form, list, result |

Dev-only: `QT_QPA_PLATFORM=offscreen python3 tools/uiwalk.py --port P` opens every zone against
the daemon on port P, drives its combos, tabs and tables with every write refused, and reports
each exception.

## Contracts and traps

- **One colour, one meaning.** Every colour comes from `theme.C`; a view that hard-codes a hex is
  a view that will disagree with the next one. The verdict scale is discrete on purpose — a verdict
  is a decision, not a number to interpolate.
- **Every number explains itself on hover.** The counts, the cells and the statuses all carry the
  sentence that says what they count. A figure nobody can define is a figure nobody should act on.
- **A cell's colour is the best verdict inside it**, not an average. A cell is an invitation to
  open it; averaging would make it argue against being opened.
- **Every zone built since 2026-09-25 wears the second look, `theme.T`.** A frame named `term`
  switches its whole subtree to the near-black, monospace, rule-separated style; the five colours
  keep their meanings from `C`. The library zones migrate when they are next touched, never in
  passing.
- **Studies run as Python through the daemon, never SQX.** «calcular» and the run bar post to
  `/api/study/run`; the daemon owns the process and the view polls `/api/jobs` only while one of
  its own runs, redrawing when it ends. A study that cannot run here says why on its own line and
  shows no button. The one exception that reaches SQX is «Continuar workflow» (see `ui/README.md`).
- **«En marcha» polls only while visible.** `showEvent` starts the three-second timer
  and `hideEvent` stops it: a hidden zone tailing a 40 MB log every three seconds would be paid
  by every other zone.
- **One project at a time.** Proyecto and Databanks show one project and its databanks, not every databank of
  every project: the owner's decision of 2026-09-24.
- **Every button explains itself on a «?».** Installed once where a `QApplication` is made
  (`launch.py`, the previews, `tools/uiwalk.py`): `helpmark.install(app)`. A new button needs a
  sentence — a `help` property, a row in `ui/text/buttonhelp_texts.py` keyed by its text, or at
  least a tooltip — or `tests/test_ui_helpmark.py --port P` fails naming it. A button's own
  `setStyleSheet` wins over `buttonstyle` property by property, so a local sheet that sets
  `border` or `padding` keeps its look; it should still leave a disabled state that reads inert.
  A floating mark (a button in a column or a grid) checks its strip against the siblings only
  when its button moves or resizes: a widget the code later puts in that strip without moving
  the button can sit under the mark until the next relayout.
- **A wrapped `QLabel` needs its height asked for.** It reports a one-line sizeHint and the layout
  believes it, clipping the paragraph: fix the width and ask `heightForWidth`, or give it an
  ignored horizontal size policy (`workspace/README.md`).
- **The palette view writes palettes, never the taxonomy.** `taxonomy.yaml` holds the labels and
  is somebody else's job (`docs/encargos/6-taxonomia-bloques.md`); the window only writes
  `sqx/blocks/palettes/<slug>.yaml`. Two writers on one file is how a column drifts.
- **A default palette cannot be deleted from the window.** It ships with the repository and is the
  thing every clone starts from; the button is disabled and says to clone instead.
- **A palette reaches a template's free holes and nothing else.** The template page says so per
  hole, from `sqx/templates/holes.py`. Without that panel the palette view would imply a control it
  does not have over a template whose holes are bound to groups.
- **A CSV column with a vocabulary is still free text on disk.** `runs.csv` is written by hand and
  by other sessions, and on 2026-09-24 one of them put a sentence in `verdict`. Indexing
  `VERDICT_COLOUR[...]` with it raised inside `Shell.__init__`, so the window did not open at all —
  clicking the icon did nothing. Verdicts and statuses go through `theme.verdict_colour` /
  `verdict_label`, which name the unknown value instead of dying on it.
- **A value is never edited straight in a cell, except in the raw file table.** The cost, the
  window and the market all open a box that says what the figure means, in which unit, and what
  leaving it undecided costs. A spread is not a number to nudge with the arrow keys.
- **The asset zone writes `assets/` and nothing else.** It reaches SQX for nothing: `sqx_now` and
  `instrument` are read from files: the custodian's `data.db` for «SQX hoy» (owner, 2026-09-30: never
  the master), the asset file for the rest. A window that queried an install would make opening a
  list a job that can block.
- **The sidebar is built last and inserted first.** It opens a zone, and opening one needs the
  stack to exist. Zones are addressed by name (`nav.ZONES`), never by index: a launcher's
  `--zone Proyectos` survives a regrouping, and a name no longer in `nav.ZONES` fails loudly.
- **Proyecto, Databanks and Estrategia follow `SELECTION`; the others do not.** `projectflow.catch_up`
  refills them (Databanks through Proyecto's fill: one project, one fill, both zones) when the selection moved on since they last painted. En marcha keeps its own
  pickers (falling back to the selected project when no worker runs one). The context bar shows
  the selection, so a crumb that reads «elige …» is the honest state of PROYECTO.
- **An imported strategy never changes `SELECTION`.** PORTFOLIOS' «Importar» shows the archived
  version on the Estrategia zone's second page; the crumbs still name the live selection, and
  opening a live strategy (panel, Ctrl+K) brings the live ficha back. An archived strategy may
  belong to no project on any install.
- **A panel row whose databank left every install still opens.** `/api/projects/find` answers
  «ninguna databank guarda esa estrategia» when the install kept only later databanks (the
  custodian held only WFM of the USDJPY project on 2026-09-28); the shell then takes the
  databank and name the panel shows, and the ficha reads the cosecha and the reports by identity.
- **Read-only mode is decided by the daemon, not guessed by the window.** `/api/health` carries
  `sqx.installs` (role → its folder exists). When none exists, `shell.guard` shows the banner
  «Esta máquina no tiene SQX: modo lectura» and disables the one button that reaches SQX, the
  load bar's ↻, with the reason in its own text — a disabled button shows no tooltip. No zone
  is greyed out. Linux only (plan 24 §10, Q2): nothing adapts to Windows.
- **Every label through `glossary.label`, every figure through `numbers.num`** (encargo 22 §10).
  Both live in `ui/text/` so the daemon can use them too. The identity is never printed: it
  lives in tooltips (the context bar's strategy crumb, the palette's rows, the archived ficha's
  origin) and underneath. `bin/algoui --shot DIR` (i.e.
  `python3 -m ui.desktop.launch --shot DIR [--zone Z]`) saves the window as `DIR/<zone>.png`
  and exits — run it with `QT_QPA_PLATFORM=offscreen` for every visual check.
