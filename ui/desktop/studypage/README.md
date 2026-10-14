# ui/desktop/studypage — one study, of one strategy or of the population

The generic page every study is read through: family tabs in `studies/CLAUDE.md` order, study
tabs each with the dot of its stored verdict, the result drawn by `blocks.ResultView`, the
configuration drawer, the run bar, the history and the two comparisons. It follows `SELECTION`
and talks to the daemon only (`/api/catalogue`, `/api/result`, `/api/history`, `/api/config`,
`/api/config/hash`, `/api/matrix`, `/api/presence`, `/api/projects`, `/api/study/run`, `/api/study/only`,
`/api/jobs`, `/api/jobs/{id}/cancel`). The strategy page opens on a fixed first tab «Ficha»
(`/api/tearsheet`), which is not a study: no run bar, no drawer, no history. Its «Salidas»,
«Contra el subyacente» and «Operaciones» sub-tabs were removed by the owner on 2026-09-28; the
routes and `ui.desktop.tradegallery` stay for PORTFOLIOS' archived sheets.

```
views.StrategyPage ─▶ ficha.Ficha ─▶ «Excluir top X% de trades» · «Drawdown en % | $»
                   │                 └ IS/OOS (ResultView, IS beside OOS; the switches ask again)
views.StrategyPage ─▶ page.StudyPage ─▶ blocks.ResultView
                                               ├ drawer.Drawer   (knobs, reset, hash match)
                                               ├ runbar.RunBar   (▶ ▶▶ ↻, one job, polling)
                                               ├ history.History (runs, compare, rival picker)
                                               ├ batchview.BatchTab («Lote», only on the WFC
                                               │  study of a mother — moved off the Ficha
                                               │  2026-09-29: a strategy can have no batch)
                                               └ dots · notes · compare ─▶ net ─▶ client
```

**Imports from:** `ui/desktop/blocks`, `selection`, `theme`, `client` · **Consumed by:** `ui/desktop/workspace/ficha.py` (the family tabs under Estrategia's basic panel)

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | The study page: one study of one strategy or of the population, its drawer, its runs and its history. | — | — |
| `compare.py` | The two results a comparison puts side by side: two runs of one strategy, or two strategies. | imported | where → results, titles |
| `dots.py` | The state dot on each study tab, and where the page reads those states from. | imported | cells → QIcon |
| `drawer.py` | The configuration drawer: every knob of a study, its sentence, and the hash the next run would sign. | imported | `/api/config` → `--set` list |
| `ficha.py` | The «Ficha» tab of the strategy page: IS/OOS side by side — P&L, drawdown, years. | imported | SELECTION → `/api/tearsheet` → page |
| `history.py` | The run history of one study here, and the two ways to put results side by side. | imported | `/api/history` → signals |
| `net.py` | The study page's calls to the daemon, with a daemon that does not answer turned into a sentence. | imported | path → JSON |
| `notes.py` | What the page says about a study around its result: its role, where it was looked for, what was passed over. | imported | entry → text |
| `offer.py` | Tests with no result anywhere in the project: their tabs greyed or hidden, the reason said, and a jump to where they run. | imported | place → marks, jump |
| `page.py` | The generic study page: family tabs, study tabs with their state dots, the result, the drawer, the runs. | imported | SELECTION → page |
| `picker.py` | The «Estrategia» dropdown of the study page: another strategy of the databank, same study. | imported | `page.where` → `picked(strategy, identity)` |
| `runbar.py` | The run bar: this strategy, the whole population, one sub-test alone — one job at a time, watched. | imported | press → job → `finished` |
| `sidepanel.py` | The buttons that open the study's side panel — configuración, historial, lote — folded by default. | imported | press → panel |
| `views.py` | The study page of one strategy, with its Ficha as the first tab — what the Estrategia zone embeds. | imported | — |
| `wfclote.py` | «Lote» beside the drawer: the mother's variant batch, only while the WFC study is open. | imported | `page.where`, `page.key` → tab |

Test: `python3 tests/test_ui_studypage.py` — the results, runner and job routers in-process
(TestClient, never port 8765), offscreen, on real reports, one real `edgeCost` run (~5 s all).
Grabs in `scratch/ui-plan/shots/E-*.png`. The Ficha: `python3 tests/test_ui_tearsheet.py`
(grabs `H1-*.png`).

## Contracts and traps

- **The side panel is folded by default** (owner, 2026-09-30: always open, the knobs took the
  width the result needs). `SideToggles` hides the panel's own tab bar; `wfclote.show` calls
  `toggles.sync()` so «Lote» gets and loses its button with its tab.
- **«· sin datos» is in the tab's text, not its colour**: the theme's sheet sets every tab's
  colour, so `setTabTextColor` never shows. Anything that finds a tab by its text strips
  `offer.OFF` first (`views.open_family`, `workspace/ficha.describe`).
- **«→ abrir en …» pairs by name, as a jump the owner chooses** — never a result borrowed in
  silence: inside one project the identity changes between databanks.
- **The Ficha is a family tab, not a study.** Its tab data is `"ficha"`; on it the study
  widgets (study tabs, headline, run bar, notes, result + side panel) hide. Following a new
  SELECTION there refills the Ficha and only records the study key, so the page does not load a
  study nobody is looking at; `open_study` (Ctrl+K, the shell) leaves the Ficha.
- **IS beside OOS by splitting, not by recomputing.** A result whose tabs are exactly «IS»,
  «OOS» is split into two one-tab results under one name and drawn with `ResultView.compare`;
  the tab notes move above the columns and compare's verdict header row is hidden (the Ficha
  judges nothing). A missing route (HTTP 404) reads «pendiente», any other refusal in red.

- **A strategy is one entity across the project** (owner, 2026-09-30). The page asks
  `/api/result` and `/api/presence` with the name and identity SELECTION holds; the daemon
  prefers the same XML anywhere, else the same name, and `notes.elsewhere` says «de <databank>»,
  the lote, and «versión de otro databank (XML distinto)» when the identity differs. A tab is
  hidden or marked «sin datos» only when no databank of the project has a result for it.
- **`meta.skipped` is shown**, in amber, day by day with its reason — «otra estrategia con el
  mismo nombre» is how a name collision becomes visible instead of silently drawn.
- **cloud, wfc, cscv write into the variant batch**, not `reports/`: the catalogue still marks
  them `source: "batch"`. On a mother's strategy page `ui.daemon.results.runs.result`/`.history`
  now read `<batch>/estudios/<study>.json` through `ui.daemon.databank.batches.batches`
  (OPEN #51, 2026-09-29), so the page shows the result like any other study and never reaches
  `notes.absent`. On the population page, or a strategy that is not a mother (or is the mother of
  two batches), there is still no result, and the page says «se lee desde el lote de variantes —
  aún no conectado» (`notes.absent`).
- **The drawer's edits reach only the next run**, as `--set`; they are kept per study while the
  page lives and forgotten by «restablecer». The hash shown is `POST /api/config/hash` of those
  edits; `entryQuality` gets extra `--set` from the runner (feed, timeframe),
  so their «coincide» compares the owner's knobs only.
- **The catalogue's `one`/`many`/`runnable`/`why_not` are the runner's** (`ui.daemon.runner.table`,
  wired 2026-09-26): a study the runner refuses (marketSurfaces, blindJoint…)
  shows its sentence instead of a button, and the headline says «se corre sobre» its scopes.
- **One job at a time per page.** The buttons wait while a job of this page runs; the bar polls
  `/api/jobs` only then, and when every job ended reloads the dots and the newest result. The
  last run's line stays on screen until another study or place is chosen.
- **⛔ and 👁 are in no installed font** (2026-09-26): the role is drawn as ⊘ elimina / ◉ describe.
- **One report button: ResultView's «Informe de lo que ves»** (`POST /api/study/screen`, F5).
  The old «abrir informe HTML», which opened the study's default `.html` rather than what the
  page shows, was removed on 2026-09-28 (F4).
