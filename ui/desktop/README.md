# ui/desktop — the window

PySide6. Draws what the daemon says, and asks the daemon for every change. **No view here opens a
file, reads a CSV or imports `core/` for anything but the port.**

```
launch ─▶ shell ─▶ nav (the sidebar in four groups) · contextbar (Proyectos › proyecto › estrategia)
                   BIBLIOTECA
                   coverage  (la portada: la matriz, la propuesta del director, las acciones de una celda)
                             └▶ shell.open_library ─▶ catalogue · palettes · chat · research/  (names: un solo nombre por familia)
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
strategytable.py, resultspanel.py, gate.py, scorecard.py, gatedetail.py,
equitychart.py, funnel.py, soon.py, `matrix/`, `workflow/`, and generation.py, which F11
folded into En marcha); their content lives in Proyecto
(the rail, the funnel), Databanks (the databank panel with every study's columns) and Estrategia (the ficha
and the study tabs). The mock on invented data (workspace/mock.py, fake.py) went with them.

| file | what it does | run it | in → out |
|---|---|---|---|
| `assetcard.py` | One asset's costs: what it applies, what SQX carries, and what leaving it undecided costs. | imported | — |
| `assetforms.py` | The boxes the asset zone opens to change something: a text, a cost, a market, a new asset. | imported | — |
| `assetlist.py` | The column down the left of the asset zone: every instrument, coloured by what it still needs. | imported | — |
| `assetmarkets.py` | One asset's Cross Market check: declare it a main, then add or drop the markets it retests on. | imported | — |
| `assetpage.py` | One instrument's page of the asset zone: costs, windows, Cross Market check, traits, raw file. | imported | `/api/asset/<S>` → page |
| `assets.py` | The asset zone: every instrument as a page of its own, one per row, full width. | imported | `/api/assets` → pages |
| `assetspans.py` | One asset's windows: its data, the three segments and the MC Retest ranges. | imported | — |
| `assettable.py` | The read-only tables the asset zone draws from — cells, formatting, the shared grid. | imported | — |
| `assettraits.py` | A starting-point note per asset on how it tends to trade — trend, rango, carry, volatilidad. | imported | — |
| `background.py` | Daemon calls off the window's thread: the answer lands in a callback on the GUI thread. | imported | work → callback |
| `blocktable.py` | The table of blocks under one palette: what each one is, and the override the reader may set. | imported | — |
| `buttonstyle.py` | How a button looks: lit and clickable when it can be pressed, inert when it cannot, in both looks of the window, and the round «?» mark `helpmark` puts beside it. | imported | — |
| `catalogue.py` | The catalogue: the list of templates and drafts on the left, one page of detail on the right. | imported | — |
| `chat.py` | The chat that turns an idea into a draft brief and the command that authors it. | imported | — |
| `chatparts.py` | Two helpers of the interview: empty a layout, and one message bubble. | imported | text → widget |
| `client.py` | The window's only way to reach the daemon. No view opens a file or a CSV itself. | imported | path → JSON |
| `cmdpalette.py` | Ctrl+K: type a few letters, Enter opens that zone, project, databank, strategy or study. | Ctrl+K | gallery/matrix/catalogue → navigation |
| `cmdrank.py` | What Ctrl+K lists and in which order: the fuzzy match, the aliases and the recent choices. | imported | query → ranked items |
| `combofix.py` | Every QComboBox in the app shows all the options that fit on screen, application-wide, one filter. | imported | — |
| `contextbar.py` | The bar on top: Proyectos › proyecto › estrategia, bound to SELECTION; each crumb goes back. | imported | selection → crumbs |
| `coverage.py` | The library's front page: what has been tried by family and timeframe, and where to go from a cell. | imported | — |
| `coveragecells.py` | The coverage matrix's parts that need no table: its scale and legend, the headline tiles. | imported | totals → tiles |
| `detail.py` | One template's page: what it is, what is on disk, where it ran, and the two writes. | imported | — |
| `durations.py` | How «En marcha» prints a duration, a processed-over-total and a time per strategy. | imported | — |
| `helpmark.py` | The «?» beside every button: one application-wide event filter that, the first time a button is shown, puts a small round mark after it whose tooltip says what the button does. | imported | — |
| `jobbutton.py` | A button that queues one daemon job after a confirmation, and follows it to its end. | imported | press → job |
| `jobsfeed.py` | GET /api/jobs shared by every poller of the window: the answer one of them just got serves the rest. | imported | `/api/jobs` → pollers |
| `launch.py` | Start the app: bring the daemon up if it is not, then open the window. | `bin/algoui` | — |
| `loadbar.py` | The data of the selected databank: loaded the moment it is chosen, and how far it has got. | imported | selection → `/api/load` |
| `names.py` | The one table of family names the window shows: every stored spelling in, one English name out. | imported | — |
| `nav.py` | The sidebar: every zone in its group, one checkable button each. | imported | — |
| `palettebar.py` | The palette view's top bar: which palette is open, what it is, and the library actions. | imported | — |
| `palettes.py` | The palette view: the library of block selections, and what the open one lets the builder draw. | imported | — |
| `palettetext.py` | The line under the palette bar: what the open palette is, and whether it does anything. | imported | palette → rich text |
| `projectflow.py` | Proyectos → Proyecto → Estrategia in the shell: the Estrategia zone (a live ficha, or an archived version PORTFOLIOS imported), a strategy found by its identity, and the two zones kept on the global selection. | imported | — |
| `selection.py` | The one global selection: project, databank and strategy, shared by every zone. | imported | choose → signal |
| `shape.py` | The panel that says which parts of a template the builder fills, and which a palette reaches. | imported | — |
| `shell.py` | The window itself: grouped side navigation, the context bar, one zone inside, one status bar. | imported | — |
| `shellopen.py` | How the window hops between zones: what a palette row, a card or a cell hands on and where it lands. | imported | click → zone |
| `theme.py` | The one design system: the palette every view reads, the stylesheet it becomes, and the two smallest pieces every zone draws with (a rule, a kicker). | imported | — |
| `yamltree.py` | Any assets/ file as a table of its values, each one beside what the file says about it. | imported | — |

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
| `research/` | «Investigar» (BIBLIOTECA): `ResearchZone` — the profile's map (asset × timeframe, colour = dominant passing family, three discrete intensities, a click for the measures each with its explanation), the memory, the board (read-only), and the proposal: three ideas with a veto each, their open questions, «▶ Crear plantillas y lanzar en SQX» behind `/api/research/launch`'s sentence, and the queue (its own README) | imported by `shell.py` | daemon → four tabs |
| `mt5bridge/` | «Verificar» (MT5 BRIDGE): `VerifyZone` — the form (the strategy chosen in Proyecto or an archived one, the window as two typed dates, the tester's model and the firms, none of them defaulted), «▶ Verificar en SQX y en MT5» as a `JobButton` whose confirmation is `/api/mt5bridge/preflight`'s text or its reasons, every past check (`/api/mt5bridge/runs`) and the chosen one's result drawn by `blocks.result.ResultView` | imported by `shell.py` | daemon → form, list, result |
| `criteria/` | «Criterios» (PROYECTO): `CriteriaZone` — the pass criteria of every workflow step from `criteria.yaml`, step 6's Build filters read only, the `dev` warning, a dialog to add, change or delete a rule (SQX metric, app test, verdict, compound), «Congelar» and the history of changes |

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
  is somebody else's job (labelled by commit `a694e67`); the window only writes
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
