---
q: export databank metrics IS OOS columns; sampleType 10 20 127; custom .vw view paired columns; which block (IS) (OOS) is filled single-window task; export_metrics header-only CSV empty; --role worker; databank table shows IS and OOS the same; window IS empty OOS filled
tag: 🔬  date: 2026-09-24  see: export/sequential-opt-not-wfc, databanks/no-spaces-in-names, databanks/sync-deletes-unloaded-files
---
# Paired IS/OOS metrics come from a custom `.vw`; read which block is filled off the data
- `sampleType`: 10 = IS · 20 = OOS · 127 = full period. View in `user/settings/views/databanks/<Name>.vw`, pass `view=<Name>`; project copies in `sqx/views/`.
- A single-window task fills ONE block, and SQX labels it either way → `studies/screening/gate/collect.py::measured()` picks the non-zero block over paired metrics only; both filled (internal split) → refuses.
- Use `sqx/export/export_metrics.py` (daemon worker, poll `-databank action=count` until `Records:`), with `--role` for custodian projects. Never `sqx-worker.sh run` for a databank export.
- The window's own plain-export reader had the same hole; fixed by `metrics.swap_block()` — see Evidence.

## Evidence
- **The window's plain-export reader had the same hole** (📓 2026-09-30, owner report: SPP
  databank showed the same figures under "In Sample" and "Out of Sample"; `Cierre › Exposición`
  showed IS empty, OOS filled). `ui/daemon/databank/metrics.py::export()` read a databank's
  `metrics.csv` with no `measured()` step, so `SPP OOS` and `CrossTF_Mothers` on
  `Test_USDJPY_donchianUpperCrossUp_H1` filed their real numbers as `(IS)` while `(OOS)` sat at
  zero — same quirk as the table below, on the CSV export path instead of the harvest one. Fixed
  by `metrics.swap_block()`: read which of a databank's own two blocks is non-zero (excluding
  `Param Count`, `TimeFrame`, `DoF Ratio`) and relabel it to match the databank's own name (its
  last word, `OOS` or else `IS`) when the two disagree.
- Column `name=` is free text: `"ProfitFactor (IS)"` at 10, `"ProfitFactor (OOS)"` at 20. 46 metric classes. Export prepends `Strategy Name`, `Filters result` (PASSED/FAILED).
  `Modo Sergiogus - OOS.vw` uses 20 for performance, 127 for Symbol/TimeFrame/indicators.

| databank | window | filled block | other |
|---|---|---|---|
| `XAUUSD/SPP IS` | 2007-12 → 2017-12 | 10 (DrawdownPct 6.57) | 20 zeros |
| `XAUUSD/SPP OOS` | 2017-11 → 2022-12 | 10 (7.27) | 20 zeros |
| `XAU_ISOOS_ejemplo/Results` | 2007-12 → 2017-12 | 10 (6.58) | 20 zeros |
| `XAU_ISOOS_ejemplo/OOS` | 2017-11 → 2022-12 | 20 (14.85) | 10 zeros |

  Types 11 and 127 repeat the filled one. Naive "Net profit (OOS)" = silent zero ~half the time. Both filled: `XAUUSD/OOS`, `XAUUSD/MC Trades`.
- ⚠️ Structural columns at one type only (`Param Count (IS)`, `DoF Ratio (IS)`, `TimeFrame (IS)`) always carry a number — exclude them from the detector.
- Route: `-databank action=export` works only on the instance holding the project; master CLI dead while GUI up → stage `.sqx` into worker `Retester/databanks/Results/` while stopped, start, export, stop.
- Silent header-only CSV: (1) `-databank action=load ... folder=` returns before loading (`count` in same `-run` says `Loaded 0 strategies`); (2) startup sync-from-files is async too.
  Port answers `Error: CLI not ready.` ~20 s; loading finishes later.
- A databank from `-databank action=create` is not picked up by startup sync — stage into an existing registered `Results`, not a new `MetricsTmp`.
- 🔬 2026-09-30, checked while rebuilding `studies/breakage/spp`: this bug is scoped to the
  `.vw`-paired `metrics.csv` export (`export_metrics.py`) and the window's `metrics.py` reader of
  it — **`sqx/export/export_spp.py`'s own `spp.parquet` is a different exporter and is not
  affected**: `Strategy 1.26.46` on `Test_USDJPY_donchianUpperCrossUp_H1` reads `NetProfit (IS
  export) = 36,373.8` and `NetProfit (OOS export) = 31,133.7` at permutation -1, correctly
  distinct, straight off each databank's own `spp.parquet`. A study reading the SPP grid directly
  does not need `swap_block()`.
- Silent 0 rows: `export_metrics` was fixed to `MASTER` until 2026-09-24 (only signal `worker saw 0 strategies`); now `--role` like `export_retest`, `export_trades`, `studies.screening.gate.harvest`.
  Also 0 rows when `.sqx` are memory-only: `synctofiles` over HTTP fails for names with spaces (API splits on whitespace) → stop the install; the shutdown sync writes them.
