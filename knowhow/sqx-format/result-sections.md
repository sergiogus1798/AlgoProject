---
q: settings.xml result sections, per-market metrics from sqx, AdditionalMarket SQStats, stats mixing across markets, ProfitFactor 0 or 5.0 stored, profit factor capped
tag: 🔬  date: 2026-09-24  see: sqx-format/sqstats-blob, sqx-format/daily-equity-bin
---
# settings.xml has one SQStats section per result — scope them or they mix
Sections: `Portfolio`, `Main: <feed>/<TF>`, one `AdditionalMarket: <feed>/<TF>: …` per cross-check
market, each with 12 blobs (3 directions × 4 samples). `core.sqxstats.stats(path, result)` slices one;
`core.sqxstats.results` lists keys. Per-market sums/ratios-of-sums come free, no trade export.
`ProfitFactor` stored `0.0` with no trades and capped `5.0` with no losses — neither is sortable;
`sqx.variants.united.combine` writes NaN / infinity instead.

## Evidence
- `XAUUSD/Retest Markets - Family/Strategy 10.16.41.sqx`: regexing the whole file mixes sections,
  last wins. Scoped `NetProfit` reproduces each result's own `dailyEquity.bin` to the cent: Main
  4,974.86, silver −14,352.24, Brent −14,977.61; `Portfolio` = their sum (−24,354.99).
- Over 2,271 (strategy × market) rows of that databank: 38 rows `NumberOfTrades = 0` → PF `0.0`;
  `Strategy 9.6.29` on Brent (3 trades, all winners, `GrossLoss = 0`) → `5.0`. A 0 ranks like the
  worst result when it is an absence; 5.0 lies once segments are summed.
