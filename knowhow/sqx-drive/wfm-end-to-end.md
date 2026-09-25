---
q: how long does a Walk-Forward Matrix take on a worker, end to end? WFM progress, status, export_wfm --role, step 19 cost
tag: 🔬  date: 2026-09-25  see: export/wfm-export, conditions/wfm-acceptance, sqx-format/wfm-in-settings-xml
---
# A WFM runs headless in a custom project: ~4-5 min per mother, and no progress signal
Budget ~4-5 min per strategy for the 30-cell matrix (JVM peak 45 GB). While it runs there is no
progress anywhere — `action=status` and `In databank` move only when a whole mother finishes, the
project log is empty — so watch CPU and the JVM, not the API. Export with
`sqx.export.export_wfm --role <role>` (it used to read only the master).

## Evidence
`USDJPY_wfm` on the custodian, cloned from the donor (`Retest-Task2.xml` is its WFM), written with
`sqx.projects.wfm`, 3 USDJPY H1 mothers, map mode (`min_squares: 0`, that project only).

| phase | 3 mothers | note |
|---|---|---|
| the matrix in SQX (30 cells, 1,080 WF steps) | 790 s | JVM 45 GB peak |
| dump of databank `WFM` | 7 s | 3-10 MB per `.sqx` |
| `sqx.export.export_wfm --role custodian` | 20 s | 129,473 trades assigned to cell and step, 0 unassigned |
| `strategies.walkForwardMatrix.report` | 2 s | |

- `action=status` reports `Running time so far 0 ms` throughout.
- `Param Count` fails on every databank listing through the API
  (`Setting 'TradingSetup.StrategyClass' is not set`): noise from the custom column on the HTTP
  threads, not from the optimisation.
- Per-step parameters arrive as text; pandas 2.3 refuses to average them, so the pivot takes the
  first value and casts all-numeric columns to float.
