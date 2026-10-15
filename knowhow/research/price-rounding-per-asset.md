---
q: Does SQX round its fills to the tick, and which assets does the repricer round for?
kw: price_rounding; rounds to tick; descuadre_sqx; 18.5 skipped XAUUSD; gold oos1 0.043 USD per trade; fill split two ticks; DAX40 mixed
tag: 🔬  date: 2026-10-15  see: research/monkey-reprice-audit, costs/per-task-costs
---
# SQX fills sit on the tick grid, split over the two ticks around the cost: the card says which way the repricer goes
- Rule: card field `price_rounding: tick | none` (`core.assetwrite.set_price_rounding`), measured by `engines.market.rounding.measure(symbol, trades)` on any trades export; `reprice.costs` refuses a card without it. Measured 2026-10-15 over 29 batches of `strategyPermutations`: **`none`** XAUUSD, USA500, DAX40; **`tick`** NIKKEI225, USATEC (indistinguishable: 0 % both ways), USDJPY (2026-10-07 audit).
- Why `none` wins: where the cost is not a tick multiple SQX lands on both neighbours with mean = the declared cost (gold oos1 entry .23 86 % / .22 14 %, declared .2286), so rounding adds a bias (gold −0.24 USD/trade in build) and the unrounded fill has none.
- Off-share (variants off by more than max(1 USD, 1 % of NetProfit)), tick → none: gold build 0-25 % → 0-1 %, oos1 28-77 % → 7-22 %; USA500 oos1 15.5 % → 0.6-1.2 %; DAX40 oos1 1-16 % → 0.2-3.7 %, build equal (8 vs 10 of 941: the «mixed» reading of 2026-10-13 was noise); NIKKEI oos1 0 % → 0.2-1.0 %.
- Gold oos1 leftover −0.043 USD/trade: the exit lands at .0587 on average against .0593 declared, drifting .0573-.0596 by year, both neighbour ticks always: sub-tick noise in SQX's bars that the stored bars lack. Not reproducible; accepted. So gold oos1 stays above the 18.5 gate (0.01).
- Not measured, hence refused: every asset with no batch on disk (all other forex, indices, metals, crudes); crossmarket marks those markets `cost_card_pending: price_rounding`.
