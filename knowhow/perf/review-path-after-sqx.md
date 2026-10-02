---
q: how long does the review after an SQX run take; export harvest step 8 cost for 5,000 strategies; orderstocsv run three times; harvest --exports; tradepack slow write per strategy; snoopingScreen SPA twice; spread study single thread; afterrun sign fingerprint minutes; step 8 studies in parallel; which step-8 study depends on which
tag: 🔬  date: 2026-10-01  see: perf/autopilot-dead-time, sqx-drive/export-after-every-stop, sqx-drive/unselected-build-population, perf/python-parallelism
---
# Export + harvest + step 8 of 5,000 strategies is ~3.5 min, not 13: one `orderstocsv`, studies side by side
- `gate.harvest … --exports` writes the harvest AND both databanks' trade exports (what `export_trades`
  writes; not a side the pairing left strategies out of) from ONE `orderstocsv`, ~4.7 ms per `.sqx`.
- Step 8 has two chains only: `snoopingScreen` after `gate` (its scorecard), `monkeyExcess` after
  `monkey` (`nulls.csv`). `edgeCost`, `spread`, `monkey`, `gate` read the harvest or the export: at once.
- `afterrun` with no project marked walks every `Test_` project, then fingerprints every databank: 13 min.
- The monkey's nulls are seeded from OS entropy: two runs differ there and in the gate's `mono`/`familia`.

## Evidence
- `Test_Calib_USDJPY_H1_freeL` (5,059 × 2 databanks, 3.0 M trades, 96 cores), before → after, same day:
  metrics ×2 32 → 16 s (side by side) · trades ×2 + harvest 418 → 80 s · step 8 329 → 101 s (gate 31 →
  snoopingScreen 67; edgeCost 17, spread 112 → 19, monkey 32 → 17) · `pipeline.autopilot.facts` 8 s.
  Harvest parquet `equals()` the old one (metrics, trades, equity), raw export identical with its
  `identity.csv`/`timeframes.csv`; 201 of 231 facts lines byte-equal, the other 30 are the monkey's.
- Where it went (py-spy): `tradepack.pack` spilled, re-read and wrote one Parquet per strategy (57 of
  107 s) — now 64 strategies per spill; `sqxfile.identity` hashed 20,000 files in one thread (33 s) —
  now `collect.identities` over 8 processes; `tradestore.frame` parsed 10,260 CSVs in one (35 s);
  `Series.replace(dict)` on 20 M rows 11 s — `map().fillna()`; `superior.spa` and the first round of
  `superior.stepm` were the same bootstrap run twice (2 × 65 s) — `superior.screen`; spread's
  `one.run` per strategy in one thread (80 s) — `fanout`, 8 processes, only `summary` comes back.
- Under a custodian build on all 96 cores the same review takes ~1.4× (117 + 145 s for 5,130).
