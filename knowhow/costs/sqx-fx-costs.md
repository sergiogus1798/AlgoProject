---
q: SQX default FX costs the5ers pairs spread commission zero; fallback costs cross-market; CADJPY GBPJPY spread; use SQX defaults for correlation N_eff
tag: 🔬  date: 2026-09-23  see: costs/where-the-spread-is, conditions/crossmarket-crosstf-no-conditions
---
# SQX's own FX costs are factory defaults — not a fallback for pricing, only for correlation
- ~10× too cheap and implausibly ordered between pairs: a build or cross-market verdict at these costs partly measures where SQX undercharged.
- Usable only to measure cross-market equity correlation (barely cost-sensitive) → sizes `N_eff = N / (1 + (N−1)ρ)`; never to decide if an edge is real.
- The ten asset files say so in every `why:` and `notes:`.

## Evidence
`sqx.inspect.instruments` over every master `project.cfx`: ten `the5ers` pairs, `commission: SizeBased 0.00`, `defaultSpread` (no disagreement between projects):

| 0.1 | 0.2 | 0.6 | 1.2 |
|---|---|---|---|
| USDJPY, EURUSD, GBPUSD, AUDUSD, CADJPY | USDCAD, USDCHF | EURJPY, AUDJPY | GBPJPY |

- 🤔 the5ers ~8 $/lot round turn; `point_value` 100000 → pip = 10 $/lot → 0.8 pips of commission vs modelled total 0.2 (spread 0.1 + slippage 0.05/side).
- 🤔 CADJPY 0.1 vs GBPJPY 1.2 (same `point_value` 653.92, 12× apart); CADJPY 6× cheaper than EURJPY despite lower liquidity.
  `/crossmarket` refuses a market without an `assets/symbols/` file; a file of these defaults passes straight through.
- 🔬 Correlation between curves barely moves with cost level; profitability moves a lot.
