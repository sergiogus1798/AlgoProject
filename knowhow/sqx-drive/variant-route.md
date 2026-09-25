---
q: retest an arbitrary parameter set; set strategy parameters no CLI verb; write variant .sqx; strip members disk cost; one retest gives IS and OOS; variant throughput; retested .sqx missing on disk synctofiles; harvest dailyEquity vs trades
tag: 🔬  date: 2026-09-22  see: sqx-format/writing-a-variant, sqx-format/five-member-sqx, sqx-drive/variant-chain-custom-project
---
# To score a parameter tuple, write it into a `.sqx` and retest the file
No CLI verb sets parameters. Values live only in `strategy_Portfolio.xml` `<variable><id>NAME</id>…<value>N</value>`;
rename per variant in `settings.xml` (`<ResultsGroup ResultName=…>` + `<StrategyName type="String">`).
One Retest with an `<OutOfSample>` range stores IS and OOS in the same `.sqx`.
After a retest run `-databank action=synctofiles` and wait before reading `.sqx` from disk (custodian only).

## Evidence
- Rule slots reference the variable by name (`<Param key="#Period#" …>DICrossPeriod1</Param>`);
  `settings.xml` has 0 hits for parameter names. Verified on `Strategy 17.9.39`: 8 substitutions, repack, read back.
- Disk per variant: all 8 members 5,215 KB (57 GB / 11,597); without `optimizationProfile.bin` 100 KB;
  only `META-INF` + `settings.xml` + `strategy_Portfolio.xml` + `lastSettings.xml` + `version.txt` = 15 KB (160 MB).
  Load/dedup of the 5-member form: see `sqx-format/five-member-sqx`.
- IS+OOS: `Setup` 2008–2022 + `<OutOfSample showGraph="false"><Range dateFrom="2018.01.01" dateTo="2022.12.31"/>`
  → samples 10 and 20 in one `.sqx` (how `XAUUSD` task 1 fills `OOS`); a paired `.vw` exports both on
  one row (`export/databank-metrics-is-oos`). A WFC needs one run.
- 📓 Throughput, master log 2026-09-19 (`totalCores: 95`):
  | job | work | wall |
  |---|---|---|
  | `SPP IS` | 5 strats × ~12,400 perms × 10 y ≈ 62,000 backtests | 369 s |
  | `SPP OOS` | same over 5 y | 187 s |
  | `MC Trades` | 757 whole `.sqx` retested 2008–2026 | 31 s |
  ≈ 24 strategies/s → 11,597 variants ≈ 8 min. Compute is not the constraint.
- 🔬 Lazy disk: run reported `Total tested 2000`, exported 2,000 rows, 962 `.sqx` on disk. Export reads memory.
  Sync wait: `sqx/variants/config.yaml: execute.sync_s` (20 s). `ran.json` records `n_on_disk` beside `n_returned`.
- 📓 Curves are cheap: `dailyEquity.bin` from 962 `.sqx`, no SQX running: 1.5 s, 5.9 MB Parquet.
  `orderstocsv` ≈ 4 min / 231 strategies → ~90 min for 5,000. For returns-per-period questions
  (CSCV, variant correlation, variant portfolio) use the curve, not trades.
