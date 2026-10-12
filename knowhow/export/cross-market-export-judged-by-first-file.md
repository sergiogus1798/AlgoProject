---
q: Why did step 10 say the retest cross-market export is missing when the export exists?
kw: necesita el export del retest cross-market de este databank; step 10 crossmarket no se corrió; Automatic filter: no trades; trades.parquet without Symbol column; no block column; multimarket False; export_retest vs export_trades; find.cross_market first file
tag: 📓  date: 2026-10-12  see: export/data-all-crossmarket
---
# The loader judged a databank cross-market by its FIRST file; one no-trades strategy hid it
Trap: autopilot step 10 fails «crossmarket: no se corrió — Retest_Markets_-_Family: crossmarket: necesita el export del retest cross-market de este databank» although the export exists. Its `trades.parquet` is tiny and has no `Symbol` and no `block` column.
- Mechanism: SQX's retest keeps in the output databank a strategy that its «Automatic filter: no trades» failed, with `Results/Main…` only, no `Results/AdditionalMarket…`. If that file sorts first, `commands` chose `export_trades` (one market) instead of `export_retest` (`data=all`); `ui/daemon/runs.py` then reads `multimarket = len(distinct Symbol) > 1` = False and the runner refuses.
- Fix (commit 896fb8d): `ui/daemon/loader/find.py::cross_market(files)` is true when ANY file holds an AdditionalMarket result. Not server-specific: leaseWeb had the same bug, hidden by file order.
- Trap when resuming: the wrong export is newer than the databank, so the loader calls it fresh and never re-exports. Remove `AlgoData/raw/<P>/Retest_Markets_-_Family/<day>` by hand, then `bin/workflow.sh run`.

## Evidence
- 📓 gorilla, `Test_UK100_H1_tendencia_gorilla2`, 2026-10-11: `trades.parquet` 498 rows, no `Symbol`/`block` (that morning's good one: 23,253 rows with both). Project log: "Total tested: 3, Passed: 2, Failed: 1 … Backtests on additional markets: Count: 2". Offender: Strategy 13.16.281, 29 KB vs ~900 KB for the others.
- 🔬 test `tests/test_ui_loader.py::test_one_strategy_without_markets_does_not_hide_the_cross_market`; the resumed run passed step 10 (3 → 2 by criteria).
