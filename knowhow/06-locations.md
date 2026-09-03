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

🔬 Data coverage, from `-symbol action=list` on the worker: `XAUUSD_DukasM1_Infinox` runs
**2003.05.05 → 2026.01.16**. The XAUUSD build task's window stops at **2017.12.31**, leaving 8 years of
gold data unused.

## Tools built here

| tool | does |
|---|---|
| `1_sqx/inspect/index_sqx.py` | index every `.sqx` by inner-XML hash + symbol; 17.7k files in 1.5 s |
| `1_sqx/inspect/dump_project.py` | `project.cfx` → Markdown pipeline map (TL;DR, databank flow, per-task detail) |
| `1_sqx/inspect/keep_tasks.py` | emit a variant of a `.cfx` keeping only chosen task types |
| `1_sqx/export/export_metrics.py` | databank metrics with paired IS/OOS columns, via the worker |
| `1_sqx/export/export.py` | a databank's trades plus the bars they were traded on |

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
