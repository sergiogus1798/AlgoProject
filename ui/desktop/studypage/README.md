# ui/desktop/studypage — one study, of one strategy or of the population

The generic page every study is read through: family tabs in `studies/CLAUDE.md` order, study
tabs each with the dot of its stored verdict, the result drawn by `blocks.ResultView`, the
configuration drawer, the run bar, the history and the two comparisons. It follows `SELECTION`
and talks to the daemon only (`/api/catalogue`, `/api/result`, `/api/history`, `/api/config`,
`/api/config/hash`, `/api/matrix`, `/api/projects`, `/api/study/run`, `/api/study/only`,
`/api/jobs`, `/api/jobs/{id}/cancel`). The strategy page opens on a fixed first tab «Ficha»
(`/api/tearsheet`), which is not a study: no run bar, no drawer, no history. Its «Salidas»,
«Contra el subyacente» and «Operaciones» sub-tabs were removed by the owner on 2026-09-28; the
routes and `ui.desktop.tradegallery` stay for PORTFOLIOS' archived sheets.

```
views.StrategyPage ─▶ ficha.Ficha ─▶ «Excluir top X% de trades» · «Drawdown en % | $»
                   │                 ├ IS/OOS (ResultView, IS beside OOS; the switches ask again)
                   │                 └ Lote (batchview.BatchTab, only for a mother)
views.StrategyPage ─▶ page.StudyPage ─▶ blocks.ResultView
                                               ├ drawer.Drawer   (knobs, reset, hash match)
                                               ├ runbar.RunBar   (▶ ▶▶ ↻, one job, polling)
                                               ├ history.History (runs, compare, rival picker)
                                               └ dots · notes · compare ─▶ net ─▶ client
```

**Imports from:** `ui/desktop/blocks`, `selection`, `theme`, `client` · **Consumed by:** `ui/desktop/workspace/ficha.py` (the family tabs under Estrategia's basic panel)

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Names the package; holds no code | — | — |
| `views.py` | `StrategyPage` (scope one, the «Ficha» as its first family tab, `open_family(name)` for Estrategia's origin). The population page (`PopulationStudy`) and its zone were retired by F13 of plan 24: a population's result lives in Proyecto's databank panel. `StudyPage(strategy_page=False)` stays only because its branches run through `page`, `notes`, `dots`, `runbar` and `history`: no zone builds it, `tests/test_ui_studypage.py` keeps it working, and removing it is a refactor of this package, not a cut | imported | — |
| `ficha.py` | `Ficha`: the harvest's sheet of the selected strategy — «IS/OOS» (P&L acumulado, Drawdown, P&L por año) and «Lote» only for the mother of a variant batch —, each filled on first opening; above them «Excluir top X% de trades» (X 5 by default) and «Drawdown en % / $», which ask `/api/tearsheet` again with `top` and `dd`; `sides` is also PORTFOLIOS' | imported | SELECTION → `/api/tearsheet` → page |
| `page.py` | `StudyPage`: tabs, dots, the result, drawer + history on the right, `open_study(key)` | imported | SELECTION → page |
| `drawer.py` | Every knob by section, in the glossary's words (`glossary.knob`; the raw key `--set` takes in its tooltip), its sentence visible and on hover, typed editors, reset, the next run's hash against the shown result's | imported | `/api/config` → `--set` list |
| `runbar.py` | ▶ esta estrategia · ▶▶ toda la población · ↻ solo …; one job at a time, percent/state every 2 s while it runs, cancel, errors | imported | press → job → `finished` |
| `history.py` | The runs newest first (day, state, hash, caducado), two chosen → compare, a picker of the databank's other strategies | imported | `/api/history` → signals |
| `compare.py` | The two results a comparison needs: two days, or two strategies of one databank | imported | where → results, titles |
| `dots.py` | The dot icon per state and where states come from (matrix for a strategy, history for the population) | imported | cells → QIcon |
| `notes.py` | Every sentence the page says around a result: role, breadcrumb, why absent, days passed over | imported | entry → text |
| `net.py` | `fetch`/`send`: a daemon that does not answer becomes `{"error"}`, never a crash | imported | path → JSON |

Test: `python3 tests/test_ui_studypage.py` — the results, runner and job routers in-process
(TestClient, never port 8765), offscreen, on real reports, one real `edgeCost` run (~5 s all).
Grabs in `scratch/ui-plan/shots/E-*.png`. The Ficha: `python3 tests/test_ui_tearsheet.py`
(grabs `H1-*.png`).

## Contracts and traps

- **The Ficha is a family tab, not a study.** Its tab data is `"ficha"`; on it the study
  widgets (study tabs, headline, run bar, notes, result + side panel) hide. Following a new
  SELECTION there refills the Ficha and only records the study key, so the page does not load a
  study nobody is looking at; `open_study` (Ctrl+K, the shell) leaves the Ficha.
- **IS beside OOS by splitting, not by recomputing.** A result whose tabs are exactly «IS»,
  «OOS» is split into two one-tab results under one name and drawn with `ResultView.compare`;
  the tab notes move above the columns and compare's verdict header row is hidden (the Ficha
  judges nothing). A missing route (HTTP 404) reads «pendiente», any other refusal in red.

- **A result is paired by identity inside one databank, never borrowed.** The strategy page asks
  `/api/result` with the identity SELECTION holds; the same name in another databank is another
  strategy (measured 2026-09-26). No result here says so; it never falls back elsewhere.
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
  edits; `entryQuality` and `conditionalMap` get extra `--set` from the runner (feed, timeframe),
  so their «coincide» compares the owner's knobs only.
- **The catalogue's `one`/`many`/`runnable`/`why_not` are the runner's** (`ui.daemon.runner.table`,
  wired 2026-09-26): a study the runner refuses (snoopingScreen, marketSurfaces, blindJoint…)
  shows its sentence instead of a button, and the headline says «se corre sobre» its scopes.
- **One job at a time per page.** The buttons wait while a job of this page runs; the bar polls
  `/api/jobs` only then, and when every job ended reloads the dots and the newest result. The
  last run's line stays on screen until another study or place is chosen.
- **⛔ and 👁 are in no installed font** (2026-09-26): the role is drawn as ⊘ elimina / ◉ describe.
- **One report button: ResultView's «Informe de lo que ves»** (`POST /api/study/screen`, F5).
  The old «abrir informe HTML», which opened the study's default `.html` rather than what the
  page shows, was removed on 2026-09-28 (F4).
