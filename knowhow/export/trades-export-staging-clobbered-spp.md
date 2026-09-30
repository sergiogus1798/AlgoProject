---
q: export_spp strategies folder missing; variants make FileNotFoundError raw SPP_IS strategies Strategy.sqx; export_trades deletes strategies; two exports same day folder; _trades_sqx staging
tag: 🔬  date: 2026-09-30  see: export/export-retest-batch-tag, export/spp-export
---
# `export_trades` stages in `_trades_sqx/` and `_trades_csv/`; `strategies/` belongs to `export_spp`
Both write `raw/<P>/<D>/<day>/`. `export_spp` leaves the mothers in `strategies/` — what
`sqx.variants.make` opens — and `export_trades` used `strategies/` as its own scratch, deleting it at
the end: after the post-stop export of `SPP IS`'s trades, step 16.5 failed with `FileNotFoundError
…/SPP_IS/<day>/strategies/Strategy 10.1.79.sqx`. Since 2026-09-30 it stages under its own names.

## Evidence
- 🔬 2026-09-30, `Test_USDJPY_donchianUpperCrossUp_H1/SPP OOS`: `export_spp` then `export_trades` the
  same day → `strategies/` keeps its 15 mothers, `trades.parquet` 5,577 rows.
