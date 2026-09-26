---
q: equity.json splits windows two months early, leg curve starts before segment, warm-up zeros dailyEquity, equity.parquet duplicate dates, overlapping legs, oos2 boundary 2022-11-03, CSCV windows split leak
tag: 🔬  date: 2026-09-26  see: sqx-format/daily-equity-bin
---
# Each leg's curve opens ~2 months before its segment, with zero P&L; `equity.json` splits are those starts
A variant leg retested over `oos1` (2018-01-01…) has curve points from 2017-11-01; `oos2`'s from
2022-11-03; `build`'s from 2007-11-02 — all zero until the segment starts. So `equity.parquet`
carries **duplicate dates** where legs overlap, and `equity.json` `splits`/`windows` name the
warm-up start, not the segment start. Slice a leg by the policy's dates (`core.assetdata.window`),
never by `splits`; a date cut at `splits["oos2"]` puts two months of `oos1` P&L on the oos2 side.

## Evidence
- 🔬 2026-09-26, the three USDJPY batches of `profiling/variantes-2026-09-25/real/`: `splits` =
  `{oos1: 2017-11-01, oos2: 2022-11-03}`; `equity.parquet` has 83 duplicated dates; |P&L| before
  2008-01-01 sums to 0.0; `equity_markets.parquet` EURUSD `oos1` rows before 2018-01-01: 214,957,
  |P&L| 0.0. Rows 2022-11-03…12-31 carry non-zero P&L for 97–100 % of variants — the oos1 leg's.
- Consequence to check: `engines/variants/panel.split(work, "oos2_only")` returns 2022-11-03, and
  `windows()` cuts the CSCV's chronological IS/OOS there.
