# ui/desktop — the window

PySide6. Draws what the daemon says, and asks the daemon for every change. **No view here opens a
file, reads a CSV or imports `core/` for anything but the port.**

```
launch ─▶ shell ─▶ nav (the sidebar in four groups) · contextbar (Proyecto › Población › Estrategia)
                   BIBLIOTECA
                   coverage  (la matriz, lo primero que se ve)
                   catalogue ─▶ detail   (la lista y la ficha)
                   chat                  (la entrevista → borrador + comando)
                   palettes ─▶ palettebar · blocktable   (la librería de paletas)
                   assets ─▶ assetlist · assetcard · assetspans · yamltree   (la librería de activos)
                   PROYECTO
                   workflow/ ─▶ WorkflowRail   (los pasos de WORKFLOW.md de un proyecto)
                   matrix/ ─▶ Matrix   (Población: estrategias × estudios)
                   studypage/ ─▶ PopulationStudy · StrategyPage ─▶ blocks/ResultView
                   studies ─▶ strategytable · resultspanel   (la zona anterior de estrategias)
                   gate ─▶ funnel · scorecard · gatedetail ─▶ equitychart   (la puerta IS/OOS)
                   OPERACIÓN
                   ops/ ─▶ Pulse · Ledger · JobsBar (en la barra de estado)
                   generation   (por dónde va el proyecto que corre, cada 3 s)
             all of them ─▶ client ─▶ the daemon · the study viewer also ─▶ selection
```

**Imports from:** `ui/daemon` never — only its HTTP surface · **Consumed by:** nobody

| file | what it does | run it | in → out |
|---|---|---|---|
| `launch.py` | Start the daemon if absent, then open the window | `bin/algoui` | — |
| `shell.py` | The single window: every zone built and wired (matrix → strategy page, headers → population study, rail → a step's study), the context bar, the stack, the status line with the jobs strip; `open_zone(name)` for the launchers | imported | — |
| `nav.py` | The sidebar: the four groups (BIBLIOTECA, PROYECTO, OPERACIÓN, CARTERAS), one checkable button per zone, the unbuilt ones included | imported | — |
| `contextbar.py` | The fixed bar on top: `Proyecto › Población › Estrategia (identidad)` from `SELECTION`, each crumb opening its zone | imported | selection → crumbs |
| `loadbar.py` | Beside the crumbs: the selected databank's metrics, trades and cosecha as three chips. Choosing a databank loads what it lacks; polls while loading; `loaded(piece)` makes the shell redraw; ↻ retries what failed | imported | selection → `/api/load` |
| `selection.py` | `SELECTION`: the one global project/databank/strategy/identity/asset, signal `changed(dict)`; a new project clears what hangs below it | imported | choose → signal |
| `cmdpalette.py` | The command palette on **Ctrl+K** — the app's first QShortcut, bound in `shell.py`. Fuzzy search over zones, projects, databanks, the chosen databank's strategies and the studies, read from the daemon when it opens; Enter goes through `Shell.go_to` (`open_zone`, `SELECTION`, `open_study`); the last ten choices first, in `QSettings`. A focused text field (the chat included) keeps Ctrl+K | Ctrl+K | projects/matrix/catalogue → navigation |
| `theme.py` | The one design system: the palette and the stylesheet | imported | — |
| `client.py` | The only way out to the daemon | imported | path → JSON |
| `coverage.py` | The matrix of what has been tried, and the counts above it | imported | — |
| `catalogue.py` | The list of templates and drafts, filtered | imported | — |
| `detail.py` | One template's page, and the two writes it makes | imported | — |
| `shape.py` | The panel saying which of a template's holes are free, which are bound to a group, and what it fixes | imported | — |
| `chat.py` | The interview that ends in a draft brief and a prompt | imported | — |
| `palettes.py` | The palette library: the open palette, its blocks by category, and the writes | imported | — |
| `palettebar.py` | The palette view's top bar: the picker, the policy, the search and the library actions | imported | — |
| `blocktable.py` | The table of blocks under one palette, and the override picker on each row | imported | — |
| `assets.py` | The asset zone: the library of instruments, the four shared files, and the three pages one can open | imported | — |
| `assetlist.py` | The column down the left: the instruments coloured by what they still need, the shared files, the retired shelf | imported | — |
| `assetcard.py` | One asset's costs, its chips and everything the preflight would complain about | imported | — |
| `assetspans.py` | The same asset's windows: the three segments, the MC Retest ranges and the retest universe | imported | — |
| `assetforms.py` | The three boxes the zone opens: a text, a cost with its `why`, a new asset | imported | — |
| `yamltree.py` | Any `assets/` file as a table of its values, each one beside its own comment | imported | — |
| `studies.py` | The strategies zone: the databanks as SQX groups them, one's strategies, one strategy's results | imported | — |
| `strategytable.py` | The table of one databank's strategies: the name and the handful of metrics that rank them | imported | — |
| `resultspanel.py` | One strategy's page: what every module already said about it, and the command for what none did | imported | — |
| `gate.py` | The IS/OOS gate zone: the cosechas, one gate's funnel and scorecard, one strategy in full, and the run | imported | — |
| `funnel.py` | The funnel: one bar per screen, passed and died to scale, the why on hover | imported | — |
| `scorecard.py` | The scorecard: one row per strategy, one column per screen, coloured by its pass | imported | — |
| `gatedetail.py` | One strategy after the gate: its curve, its IS/OOS pairs, each screen's value and note | imported | — |
| `equitychart.py` | One strategy's daily P&L, build and retest, the retest lifted to the build's last level | imported | — |
| `generation.py` | The generation zone: one install, one project, its tasks with their state, the running task's percentage and the log tail, refreshed every three seconds while on screen | imported | — |
| `durations.py` | How the generation zone prints a duration, a processed-over-total and a time per strategy | imported | — |
| `soon.py` | The page a zone shows before it is built (Datos, Carteras): what goes there, and how the job is done today | imported | — |

The study viewer's packages, each with its own README:

| folder | what it holds |
|---|---|
| `blocks/` | One widget per contract block kind, `ResultView` (a result, or two compared), the state → colour map every view imports |
| `matrix/` | «Población»: the strategies of one databank × the studies, cells in state colour, ⊘/◉ headers, batch run, the `/curate` line |
| `studypage/` | «Estrategia» and «Estudio de población»: family and study tabs, the result, config drawer, run bar, history, compare |
| `workflow/` | «Workflow»: the rail of WORKFLOW.md for one project, the oos2 gauge and the 17·18·19 envelope |
| `ops/` | «Custodio» (pulse), «Ledger» (read-only) and the jobs strip of the status bar |
| `tradegallery/` | The Ficha's «Operaciones»: five trades by P&L quantile, or five seeded at random, each on its bars |
| `batchview/` | The Ficha's «Lote»: a mother's variant batch in parallel coordinates, coloured by NetProfit oos1 or build; shown only when the batch exists |

## Contracts and traps

- **One colour, one meaning.** Every colour comes from `theme.C`; a view that hard-codes a hex is
  a view that will disagree with the next one. The verdict scale is discrete on purpose — a verdict
  is a decision, not a number to interpolate.
- **Every number explains itself on hover.** The counts, the cells and the statuses all carry the
  sentence that says what they count. A figure nobody can define is a figure nobody should act on.
- **A cell's colour is the best verdict inside it**, not an average. A cell is an invitation to
  open it; averaging would make it argue against being opened.
- **An unbuilt zone is reachable, not greyed out.** A disabled QPushButton never receives mouse
  events, so its tooltip never shows: five disabled entries would carry an explanation nobody can
  read. They open `soon.py` instead, which also states how the job is done today — a page that only
  promised something would be an advert.
- **The strategies zone wears the second look, `theme.T`.** A frame named `term` switches its
  whole subtree to the near-black, monospace, rule-separated style; the five colours keep their
  meanings from `C`. New zones are built inside a `term` frame; the two older zones migrate when
  they are next touched, never in passing.
- **The strategies zone runs Python through the daemon, never SQX.** A module's «correr» button
  posts to `/api/run`; the daemon owns the process and the view polls `/api/jobs` every two
  seconds only while one of its own runs, redrawing the strategy when it ends. A module that
  cannot run here says why on its own line, from `runs.py`, and shows no button.
- **The equity chart lifts the retest onto the build's last level.** On disk each side starts
  from zero because each was its own backtest; drawn from zero the retest is a flat line at the
  bottom of a chart the build filled. The lift is for reading the shape, and the legend says so.
- **The generation zone polls only while visible.** `showEvent` starts the three-second timer
  and `hideEvent` stops it: a hidden zone tailing a 40 MB log every three seconds would be paid
  by every other zone.
- **One project at a time.** The left column is a project picker over its databanks, not every
  databank of every project: the owner's decision of 2026-09-24.
- **A wrapped `QLabel` needs its height asked for.** It reports a one-line sizeHint and the layout
  believes it, clipping the paragraph. `soon.wrapped()` fixes the width and computes the height
  with `heightForWidth`.
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
  `instrument` are read from the files, which `sqx.inspect.instruments` refreshes. A window that
  queried the master would make opening a list a job that can block.
- **The sidebar is built last and inserted first.** It opens a zone, and opening one needs the
  stack to exist. Zones are addressed by name (`nav.ZONES`), never by index: a launcher's
  `--zone Estrategias` survives a regrouping.
- **The study viewer follows `SELECTION`; the older zones do not.** Workflow, Población, Estrategia
  and Estudio de población move together when the matrix pickers or a cell change the selection;
  Estrategias, Puerta IS/OOS and Generación keep their own pickers. The context bar shows the
  selection, so a crumb that reads «elige …» is the honest state of the viewer, not of those zones.
- **What the new zones duplicate.** Estrategias (`studies.py` + `resultspanel.py`) is Población +
  Estrategia for everything a module already wrote; it alone still shows the databank's metric
  table (net profit IS/OOS, trades). Puerta IS/OOS is the gate study on Estudio de población; it
  alone still shows a strategy's paired IS/OOS equity curve and runs the gate over a cosecha
  with typed thresholds. Neither is folded in until those pieces exist in the viewer.
