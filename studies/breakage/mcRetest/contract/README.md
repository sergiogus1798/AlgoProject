# retest/contract — the result read as the contract's blocks

`run.one()` returns numbers; this folder turns them into the result the window paints and the
batch page draws. It decides nothing — `verdict/` does — and computes nothing but the reshaping.

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Names what the package is; holds no code | — | — |
| `words.py` | The Spanish sentence behind every veto, what each task perturbs and holds fixed, each verdict word and its state, the shape of a task's outcome, and the cross-strategy facts | imported | codes → text |
| `tabs.py` | The tabs — verdict, what breaks it, the combined stress, the tasks that ran, SQX's confidence table — the verdict block and the summary row. `cost_tab` and `stress_tab` return None when the control or the production task did not run, and `one.contract` drops them | imported | result → tabs |
| `criteria.py` | The criteria metrics as the table «Métricas para criterios — sin umbral todavía» of the tab of the eight tasks (numeric cells: each task's percentile and gaps are facts the autopilot reads) and the stress task's three as columns of the summary row, hence of `verdict.csv` | imported | result → table, columns |
| `retention.py` | The tab «Fragilidad (T1, T2, T3)»: one table per test titled by its code alone, one row per window, one column per measure, so `pipeline.autopilot.facts` names each cell `mcRetest.fragilidad.<test>.<window>.<measure>` whatever the order — renaming a title, row or column renames a judged fact. `tab(got, t1)` takes T1's facts as the flat dict `neighbours.t1.facts()` returns (`t1.<window>.<measure>`, `t1.rho_vec`; `one.contract` reads it from `inputs["t1"][strategy]`, which nothing fills yet) and imports nothing of `neighbours/`; `warnings()` says when a test's task ran and it still has no data | imported | result + T1 rows → tab |

`report.py` refuses to start when `gates.VETOES` and `words.SENTENCES` name different vetoes: a
veto that fires with no sentence is a verdict nobody can argue with.
