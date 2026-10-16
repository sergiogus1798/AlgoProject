---
q: Does SQX round its fills to the tick, and which assets does the repricer round for?
kw: price_rounding; rounds to tick; descuadre_sqx; 18.5 skipped XAUUSD; gold oos1 0.043 USD per trade; fill split two ticks; DAX40 mixed
tag: 🔬  date: 2026-10-16  see: research/monkey-reprice-audit, costs/per-task-costs
---
# SQX fills sit on the tick grid: with bars at the feed's full precision every measured asset reprices exactly with `tick`
- Rule: card field `price_rounding: tick | none` (`core.assetwrite.set_price_rounding`), measured by `engines.market.rounding.measure(symbol, trades, segment)`; `reprice.costs` refuses a card without it, step 8 (`gate.inputs.ensure_rounding`, owner R1 = A) measures a missing one on the build's trades (first 300) and a tie writes `tick`. Family/structural markets (steps 10/18.5) still refuse until measured by hand.
- 🔬 2026-10-16: the `none` verdicts (XAUUSD, USA500, DAX40, AUS200) were an artefact of the bar library rounded to 2 decimals by SQX's export (R3e A, `e9cf09e`: library now decoded from the `.dat`, 3 decimals). Re-measured on the fine bars over every local batch, 40 variants each: XAUUSD 28 batch-legs tick 0 % everywhere vs none 0.3/10/3.4 % (build/oos1/oos2); USA500 tick 0 % vs none ≤ 1.5 %; DAX40 tie within noise. All four now `tick` (AUS200 inferred, unmeasured).
- The old «SQX lands on both neighbour ticks, mean = declared cost» reading was the 2-decimal bars, not SQX: on the 3-decimal bars the fills sit on one tick.
- Ties: SQX rounds a half tickStep UP; `np.round` (half to even) put half the fills a tick off wherever spread+slippage is an exact half (GBPJPY oos1, AUDUSD build, AUDNZD oos1 — fixed 2026-10-15, OPEN #124 closed; AUDNZD none → tick). `measure(symbol, trades, segment)` takes the task's cost profile: `Sample type` IST says nothing.
- Not measured, hence refused: every asset with no batch on disk (other forex, metals other than gold); crossmarket marks those markets `cost_card_pending: price_rounding`. Family-retest exports label `Sample type` IST: pass `segment="oos1"` to `measure`, SQX ran them on oos1.
