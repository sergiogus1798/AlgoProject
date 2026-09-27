---
q: export SPP system parameter permutation results; SPP trades; permutation table 152 statistics; Don't store data for 3D charts; spp.parquet; export_spp
tag: 🔬  date: 2026-09-23  see: export/spp-pairing-for-wfc, export/storage-format, sqx-format/optimization-profile-bin
---
# SPP has no CLI export and no trades — read the permutation table from `optimizationProfile.bin`
`python3 -m sqx.export.export_spp --project XAUUSD --databank "SPP IS"` → one wide `spp.parquet` (parameters as columns, stats beside).
Requires *"Don't store data for 3D charts in Optimization profile"* OFF before the SPP run; ticked = only medians/histograms, re-run needed.
Each permutation = parameter string + numeric stats blob; no order list is ever written. Trades that exist = main backtest (`data=main`).
In-sample surface only: a permutation does not pair an IS with an OOS result.
Layout: `<date>/spp/` (tables) and sibling `<date>/strategies/` (mother `.sqx`); each carries its own `manifest.json`.

## Evidence
- `sqcli -help` has nothing for optimisation/cross-check results; `orderstocsv data=all` covers only `settings.xml` `Results` (main + AdditionalMarket).
- No-trades is from `SQStats.serialize`, not inferred → `knowhow/sqx-format/`.
- 📓 `XAUUSD/SPP IS`: 21,205 permutations, five strategies, 3,940–4,523 each, 152 statistics per row.
- Former `permutations.csv` + `permutation_params.csv` merged into `spp.parquet` (49 MB → 6 MB); a reader needing 4 columns reads 4.
- 🔬 2026-09-27: until then `strategies/` had no manifest in its ancestor chain, so `tools/daily_audit.py` flagged every `SPP_IS`/`SPP_OOS` export (a real gap, not the checker's blind spot). Exports before that date still lack it.
- Gives more than the SQX panel: arbitrary percentiles, cross-metric joins, parameter surface (`NetProfit` by one parameter's value).
