# wfc/contract — the correlation as the contract's blocks

Nothing here computes: `measure/` and `verdict/` did. It turns their numbers into the result the
window paints and `core/study/render` draws into the batch's `estudios/` folder.

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Names what the package is; holds no code | — | — |
| `wfc.py` | The WFC: every partition the ledger's door offers, each as its own scatter and correlation table under one selector (feedback §8.2, 2026-09-30), the per-partition OOS/IS Sharpe histogram and IS/OOS overlay, one correlations table (Spearman, Pearson, Pendiente) over all partitions, the strata a point can belong to, and the glossary that says the PBO does not move with the composition | imported | kept points per partition → tab |
| `criteria.py` | The criteria metrics as two text tables of the tab («Métricas para criterios — sin umbral todavía»: the top's persistence per out-of-sample window with its chance value, excess and zero-edge range, and the median Sharpe ratio per partition) and as the summary's flat fields the databank table and the autopilot read (`wfc.summary.exceso_persistencia_*`, `mediana_ratio_Sharpe`) | imported | measures per window and partition → tables, summary |
