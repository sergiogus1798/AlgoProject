---
q: How does SQX stamp and fill a stop-loss exit and a trade whose bar starts late, and how is each repriced?
kw: an oos1 trade is stamped off the bar grid; sellada fuera de la rejilla de barras; Close time 00:31; first M1 minute missing; SL stamped on the bar grid; stop priced at bar open; repricer inflated; Close type SL; reprice.real; reprice.located; get_indexer -1; edgeCost SystemExit; level1a assert
tag: 🔬  date: 2026-10-07  see: research/monkey-reprice-audit, export/fill-and-pricing
---
# A stamp off the bar grid is a bar that starts late, not a stop; a stop is ON the grid and was priced at its bar's open
- **Off-grid stamp** (0.01-0.15 % of oos1 trades, 35 in 11 harvests; opens too): the timeframe bar's first M1 minutes are missing, SQX opens the bar at its first minute (00:31 for the 00:30 bar) and fills there. That minute's open IS the resampled bar's `Open` (35/35 exact). All are `Exit After X Bars`; none is a stop.
- **Stop-loss exit**: stamped with the OPEN TIME of the bar the stop was hit in (always on the grid), `Close price` = stop level − side × slippage, inside that bar (100 % below its open and above its low; 6 % reach the previous bar's low).
- Until 2026-10-07 the common repricer filled it at that bar's open — before the fall: +290 to +370 USD per stopped trade, 30-37 % of the trades of a population with stops. oos1 mean P/L per trade: NIKKEI225 simpleL 148.55 vs SQX 45.29; USDJPY doubleROC +122.13 vs −2.46.
- Rule, in `engines.market.reprice.real` only: locate by containing bar, accept an off-grid stamp only when no M1 minute precedes it in its bar; a `Close type` of `AT_PRICE` fills at raw = `Close price` + side × slippage. Then SQX is reproduced to 0.02 USD (NIKKEI225, 834 SL). Unknown `Close type` or price outside the bar: raise.
- Every step-8 number of a stop population computed before this date is inflated; populations without stops (donchian, emaCloseCross, timeRangeBreakout, squeezeBB) did not move.
- Not measured: shorts, PT (none harvested), a stop under M1-precision stamps (would be refused, not mispriced).

## Evidence
🔬 2026-10-07: the USDJPY residue below (−0.61 vs SQX −2.46) was the repricer rounding forex fills to the pip (`tick_size` 0.01) instead of the price step (`tick_step` 0.001); fixed in `reprice.pnl`, 973 trades now within 0.01 USD of SQX. The card was right.

Newest harvest of each of 18 projects under `AlgoData/harvest/`, bars `core.barstore.read`, costs `reprice.costs` of today's card.

| population, oos1 | trades | stops | repriced before | now | SQX |
|---|---|---|---|---|---|
| Test_NIKKEI225_M30_simpleL_fin | 1,047 | 384 | 148.55 | 45.29 | 45.29 |
| Trade_NIKKEI225_M30_volatilidadL | 1,274 | 450 | 159.72 | 53.03 | 53.03 |
| Test_USA500_H1_indicesIBS | 464 | 148 | 139.27 | 44.23 | 44.30 |
| Test_USDJPY_M30_doubleROCLong | 1,099 | 365 | 122.13 | −0.61 | −2.46 |

Build segments move alike (simpleL_fin 290.02 → 204.16, SQX 204.16). USDJPY's residue is its card's `tick_size` 0.01 against 3-decimal
prices (fills rounded to the cent of a yen), not this rule. Off-grid stamps: USDJPY donchian M30 12, XAUUSD donchian2 H1 6 closes + 3 opens,
emaCloseCross2 H1 3, timeRangeBreakout2/3 M30 2 + 9; build segments 0 in 466,000 trades. Mean of (next bar's open − stop price) over the
stopped trades, in USD per trade: −7, +13, −34, +69, +35, −6, +7, −8 (s.e. 8-27) — moving a stop to the next open is noise, not a penalty.
