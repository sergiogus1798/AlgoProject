---
q: Why does edgeCost.report read only a harvest of the traded version at step 25?
kw: step 25 edgeCost on the stop grafted version, edgeCost only reads a harvest, traded version trades, Stop_p90 harvest, stop_percentile p90 variant step 0, which segments step 25 reads, facts.gather step 25 reads step 8 edgeCost
tag: 🔬  date: 2026-10-02  see: sqx-format/fabricated-variant-identity-differs-from-retest, sqx-format/grafting-a-stop-loss
---
# Step 25 needs a harvest of the traded version: `edgeCost.report` reads nothing else
⚠️ Historical: step 24 (the stop grid) and `pipeline.autopilot.traded` were deleted 2026-10-11 and step 25 no longer runs in the chain; only the standalone `edgeCost.report --strategy` mode survives. What follows is the record of how it worked.
`edgeCost.report --strategy` opens `harvest/<P>/<databank>/<day>/` only. The version to trade — the
mother with step 24's stop at the ledger's `portfolio.funded.stop_percentile` — exists only as a
variant (`S00V014`) of the stop grid's export, three legs, every market. `pipeline.autopilot.traded
.harvest` files it as the cosecha `Stop_p<percentile>`: grid `step` 0, the main feed, build → `IS`,
oos1 → `OOS` (what `edgeCost.costs` prices; oos2 is not step 25's), keyed by the MOTHER's identity.
Until 2026-10-02 «step 25» was run by hand on the gate's harvest: the strategy WITHOUT its stop.

## Evidence
- `facts.gather(P, "25")` still reads step 8's population result (`sources.results(…, False)`).
- The shape read: trades with `identity` and `sample`, metrics with `strategy`, `TimeFrame [IS]`.
- Built from `raw/Test_USDJPY_donchianUpperCrossUp_H1/WFC_{Build,OOS1}/2026-09-30/stopgrid/` into
  a scratch folder: 3,337 trades, three mothers (746/434, 655/335, 783/384 IS/OOS);
  `costs.per_trade` → `one.run` on `Strategy 10.9.72`: n 1,180, reconcile 0.99964.
- `facts.gather(P, "25")` on that project: 60 strategies of the 2026-09-30 population folder.
