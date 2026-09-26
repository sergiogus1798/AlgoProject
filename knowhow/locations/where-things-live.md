---
q: where are strategies templates outside SQX; WorkSQX AddonsSQX; Desktop/user only copy XAUUSD Results; Trash excluded from searches; SQX.zip; tools built here index_sqx dump_project keep_tasks project_health vocabulary export tools
tag: 🔬  date: 2026-09-22  see: locations/logs-and-data-coverage, authoring/block-vocabulary
---
# Strategy/template stores outside the installs, and the inspection tools that read them
`~/Desktop/user/` is NOT debris — the only copy of XAUUSD/Results (4,805 `.sqx`); never delete.
Exclude `~/.local/share/Trash/` from strategy searches (owner's request).
97 AlgoWizard templates across `WorkSQX/AlgoWizardTemplates/` and `AddonsSQX/Templates/`.

## Evidence
| path | contents |
|---|---|
| `~/Desktop/WorkSQX/` | 635 `.sqx` + `AlgoWizardTemplates/` (main template source) |
| `~/Desktop/AddonsSQX/` | 68 `.sqx`, `Templates/`, `CustomBlocks/`, `RandomGroups/` |
| `~/Desktop/StratsProblem/` | 6 `.sqx` |
| `~/Desktop/user/` | 12 Jun project tree, only copy of XAUUSD/Results |
| `~/Desktop/AlgoProject_Old/` | previous project, read-only, incl. 8.5 GB `snapshots/` |
| `~/.local/share/Trash/` | 11,440 `.sqx`, mostly June-tree duplicates |
| `~/Desktop/SQX.zip` | 1.28 GB June install backup, 32 example `.sqx` — not a strategy archive |
Template sets: `TemplatesSergiogus`, `TemplatesClaude`, `TemplatesLaCity`, `TemplatesBook`.

Seed material for the ~1,208 `SPP OOS` / ~1,142 `WFM` XAUUSD strategies lost 2026-09-02 (not
recoverable — owner's decision was to accept the loss and regenerate), still on disk and unique
(not in the master project):

| symbol | in master | elsewhere | main sources |
|---|---|---|---|
| XAUUSD | 461 | 5,746 | `~/Desktop/user` (June tree) 5,189 · `~/Desktop/StrategiesWFM/XAUUSD` 458 · `~/Desktop/WorkSQX` 148 |
| USDJPY | 409 | 592 | June tree 1,429 copies · WorkSQX 34 · Banquillo 21 |
| AUDJPY | 2,348 | 22 | June tree 12 · Banquillo 12 · WorkSQX 10 |

| tool | does |
|---|---|
| `sqx/inspect/index_sqx.py` | index every `.sqx` by inner-XML hash + symbol; 17.7k files in 1.5 s |
| `sqx/inspect/dump_project.py` | `project.cfx` → Markdown pipeline map |
| `sqx/inspect/keep_tasks.py` | `.cfx` variant keeping chosen task types |
| `sqx/inspect/project_health.py` | broken task refs, version drift, mangled fields per project |
| `sqx/inspect/template_check.py` | do built strategies carry their template's fixed blocks |
| `sqx/inspect/vocabulary.py` | blocks, groups, what pools what, gap vs another install |
| `sqx/export/archive_logs.py` | copy installs' logs to `AlgoData/logs/` before pruning |
| `sqx/export/export_metrics.py` | databank metrics, paired IS/OOS, via worker |
| `sqx/export/export_trades.py` | a databank's trades + bars traded on |
