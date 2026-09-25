---
q: decode SQStats blob, settings.xml base64 stats, 152 statistics, sqxstats KEYS, metric key mapping, read databank metrics off disk without SQX, sample type 10 20
tag: 🔬  date: 2026-09-10  see: sqx-format/result-sections, sqx-format/optimization-profile-bin, sqx-format/daily-equity-bin, columns/custom-columns-stored
---
# SQStats decodes completely: 152 stats, readable off disk with no SQX running
Each `<SQStats version="2" e="b64">` in `settings.xml` sits under
`stats_LQ1_direction_DD_<dir>_L1_pl_DD_10_L1_sample_DD_<sample>_L1__RQ1_`. Record stream: type byte,
then 1-byte id — or, if type > 100, a `writeUTF` name — then value (1 int, 2 long, 3 float; big-endian).
`core/sqxstats.records()` reads all; ids named by `core/sqxstats_columns.json` (shared with
`core/optprofile.py`). Values are frozen stored numbers; for another window use `dailyEquity.bin`.

## Evidence
- Every blob on this install: 116 id-keyed records + 36 self-naming (`SortinoRatio`, `RecoveryFactor`,
  `UlcerIndex`, `ProbSharpeRatio`, `EdgeDecayRatio`, `MaxNewHighDurationFrom/To`, `AddMarkets*` medians…).
  Not: "decoding stops at the first unknown type" — the old reader dropped the named tail (¼ of every blob).
- 79 of 116 ids named; calibrated by exporting XAUUSD/WFM through a generated 107-column view; agreed
  with the independent optprofile calibration on **76 of 76** shared slots. `?` on 4 ids whose pairs are
  always equal (`AnnualPctReturnDDRatio`/`CalmarRatio`, `AvgTrade`/`Expectancy`); 37 always-zero stay
  `stat:<f|i|l>:<id>`. Ties broken by arithmetic: `AnnualPctReturn = NetProfitPct / TotalDataYears`,
  `TotalDataYears = floor(TotalDataMonths/12)`, `ExposurePosition` is in the named tail so the id twin is `Exposure`.
- Mapping is independent of sample type. `core/sqxstats.py` maps every id through
  `core/sqxstats_columns.json` (checked 2026-09-25) — matched exactly on all 165 of `XAUUSD/SPP OOS`:

  | key | metric | key | metric |
  |---|---|---|---|
  | `(f,1)` | Sharpe | `(f,25)` | Ret/DD |
  | `(f,5)` | ZScore | `(f,27)` | Profit factor |
  | `(f,8)` | Calmar / CAGR-MaxDD | `(f,29)` | SQN |
  | `(f,9)` | Drawdown | `(f,34)` | R Expectancy |
  | `(f,10)` | Net profit | `(f,43)` | Winning % |
  | `(i,10)` | # of trades | `(f,56)` | RSquared |
  | `(f,11)` | Stability | `(f,21)` | Max DD % |
- ⚠️ `SPP OOS` strategies carry an all-zero sample-20 block (their OOS columns export 0; trades all `IST`,
  see `knowhow/export/`) — useless as OOS-side calibration.
- `core/sqxstats.py` (`stats()`, `equity()`) made `tasks/reports/decay.py` possible with the master GUI up
  and no worker started.
