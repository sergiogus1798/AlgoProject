---
q: Why does a 5,000-variant WFC load end with fewer strategies in WFC_Build than in the OOS legs?
kw: variants missing, WFC_Build fewer files, files before sync 0 after sync 3952, batch too large, 3952 of 5010 on disk, Project finished but IS incomplete, synchronizeDatabank lost strategies
tag: 🔬  date: 2026-10-05  see: sqx-drive/variant-route, perf/variants-batch-size-and-flush
---
# One load of 5,000 variants loses ~21 % of the IS leg; 2,500 does not — do not load a real mother's 5,000 at once
Trap: SQX says `Project finished` (15,032 retests counted) yet `WFC_Build` holds fewer files than `WFC_OOS1`/`WFC_OOS2`.
Not an acceptance filter: the loss is random. `execute.synced` catches it (SystemExit «3952 of 5010 on disk»).
Safe batch size lies between 2,500 and 5,000 and is NOT found; keep loads ≤ 2,500 until it is. 🤔 Cause: memory
(IS is the heaviest leg; heap was not sampled) — confirm by sampling heap during the flush or loading 3,500-4,000.

## Evidence
🔬 Custodian `SQX_w2` (80 GB), `Test_NIKKEI225_M30_simpleL_val`, 10 NIKKEI225 M30 mothers × 500, restart route
`python3 -m sqx.variants.execute`, 2026-10-05.
- 5,000 loaded: `synchronizeDatabank` WFC_Build «files before sync 0 / after sync 3952 / saved 3952 / removed 0 in 166.05 s»;
  WFC_OOS1 and WFC_OOS2 had 5,000 each. 1,048 missing.
- Missing ones spread evenly: 380-406 kept of 500 per mother; medians of NetProfit, trades, ProfitFactor (from the
  previous night's per-mother run) equal to the kept ones; every design stratum hit.
- Same experiment with 2,500 (5 mothers): 2,500 / 2,500 / 2,500.
