---
q: export cross-market retest trades; data=all additional markets one CSV per strategy; Symbol separator; where OOS starts in retest export; missing market file; export_retest --limit sample; long-only fleet
tag: 🔬  date: 2026-09-21  see: export/data-all-blocks, export/fill-and-pricing, conditions/retest-additional-markets
---
# `data=all` writes main + every AdditionalMarket into one CSV per strategy; `Symbol` splits them
- `sqx/export/export_retest.py` does the split; `orders.bin` never needs parsing. `Ticket` restarts per block — not a key across markets.
- The export carries no OOS boundary (all rows `IST`): read it from the project and declare it.
- No trades on a market → no file for it. Treat absence as a result (`missing`), not a missing input.
- Both export commands drive the worker, never the master — safe with the master GUI open.

## Evidence
- In the `.sqx`: `Results/AdditionalMarket: <feed>: <feed>/dailyEquity.bin`, `<Result resultKey="AdditionalMarket: ...">`
  in `settings.xml`, one `orders.bin` (`SQOrderFileFormat:11`) with all results' orders tagged by result key.
  Verified on `EURUSD/databanks/RetestMarkets - Structural/Strategy 10.11.23.sqx` (EURUSD + USDJPY, USATEC, XAUUSD):
  301 / 256 / 193 / 393 rows, own date ranges, all `Sample type=IST`.
- Block order = result order (main first). ⚠️ Contiguity is not guaranteed in general (crossTF interleaves) → `export/data-all-blocks`.
- No OOS: `XAUUSD / Retest Markets - Family`, `Strategy 24.14.35`: 1,124 gold, 913 silver, 842 Brent rows all `IST`, incl. 351 gold
  trades inside the OOS. Boundary: `<OutOfSample><Range dateFrom="2018.01.01" dateTo="2022.12.31"/>` in `Build-Task3.xml`
  inside `XAUUSD/project.cfx`; declared as `out_of_sample` in `strategies/crossmarket/assets/_markets.yaml`.
- Missing files: 30-strategy sample, 2 have no `XAGUSD_DukasM1_Infinox` file (all have gold, Brent); expect ~50 on 757.
  `crossmarket/explorer/analysis.py` records `missing`.
- `export_retest.py --limit 30`: reproducible random sample (seed 20260914) — a databank is in build order, first N = one generation run.
- Exit mix (92,329 trades, 30-strategy sample): `Exit After X Bars` 78.0%, `Exit Signal` 16.6%, `End Of Friday (Time)` 5.4%;
  Friday close at Friday 21:00 (832 of 838; rest 21:02, 21:16) — reproducible by a null; `Exit Signal` is not without the `.sqx`.
- All 92,329 trades `Type=Buy`: `log(exit/entry)` code is wrong on a short — assert, don't assume.
