---
q: crossmarket verdict too optimistic; worst_pf above SQX's own profit factor; crossmarket wrong timeframe bars; _markets.yaml timeframe vs export timeframe; M30 export priced on H1 bars; cost_rate near zero; spread not subtracted in crossmarket trade_returns; entry offset above bar open
tag: 🔬  date: 2026-09-27  see: fill-and-pricing, data-all-crossmarket
---
# The cross-market study must price an export on the export's own bars, and charge the entry offset
Two faults, fixed 2026-09-27. (1) `inputs/markets.universe()` took the timeframe `_markets.yaml`
declares per asset (USDJPY: H1) whatever the export ran on; an M30 export was priced on H1 bars,
every trade at :30 matched the bar half an hour early, and losers read as winners. The timeframe now
comes from the export's `manifest.json`. (2) `cost_rate()` came from `core.trades.cost()`, gross from
the FILL prices, which leaves out the offset where SQX puts spread and slippage while the returns are
priced from the bar opens; it now comes from `setting()["charged"]` (gross from the bars − P/L).
Check after any change: PF of the study's returns vs PF of the export's `Profit/Loss` per `Symbol`.

## Evidence
`Test_USDJPY_donchianUpperCrossUp_M30`, `Retest Markets - Family`, 8 long-only market-entry M30
strategies, 9 FX pairs. SQX's net `Profit/Loss` by `Symbol`: PF 0.79–1.07, 8 of 9 markets < 1.

| `Strategy 10.18.56` | bars | cost | PF of returns | PF of SQX P/L | corr(rebuilt, P/L) |
|---|---|---|---|---|---|
| USDCHF, before | H1 | −7.8e-09 | 1.448 | 0.800 | 0.976 |
| USDCHF, after | M30 | 0.41 bp | 0.822 | 0.801 | 0.998 |
| EURUSD, after | M30 | 0.17 bp | 0.954 | 0.943 | 0.995 |
| CADJPY, after | M30 | 0.23 bp | 0.982 | 0.976 | 0.996 |

Report: 8/8 MANTENER with `worst_pf` 1.31–1.51 before; 0/8 after, 0 of 9 markets cleared each.
With only the cost fixed (still H1 bars) it said 5/8: the timeframe was the larger fault. Stored
verdicts are wrong wherever the export's timeframe differs from `_markets.yaml` (USDJPY at M30,
XAUUSD at H1); the spread omission is small and everywhere. `engines/nulls` recovers its cost the
same fill-based way (`calibrate.charged`), but prices real and random runs alike, so the monkey's
comparison stays fair — only its absolute levels are gross (OPEN.md §57).
