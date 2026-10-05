---
q: Why does a 5,000-variant WFC load end with fewer strategies in WFC_Build than in the OOS legs?
kw: variants missing, WFC_Build fewer files, files before sync 0 after sync 3952, batch too large, 3952 of 5010 on disk, Project finished but IS incomplete, synchronizeDatabank lost strategies
tag: 🔬  date: 2026-10-05  see: sqx-drive/variant-route, perf/variants-batch-size-and-flush
---
# One load of 5,000 variants loses ~21 % of the IS leg on the RESTART route; on a live session it holds
Trap: SQX says `Project finished` (15,032 retests counted) yet `WFC_Build` holds fewer files than `WFC_OOS1`/`WFC_OOS2`.
Not an acceptance filter: the loss is random. `execute.synced` catches it (SystemExit «3952 of 5010 on disk»).
Restart route (sqcli start/stop per batch): 2,500 is safe, 5,000 is not; keep its loads ≤ 2,500.
Live session (`sqx.projects.live`, the autopilot's default): 5,000 in one load is safe — twice 5,000/5,000/5,000 in
memory, and 15,000 files (3,649 MB) on disk in 206 s with the three legs flushed at once. Heap peaked at 53 GB of
80 during the run, never near the cap, so memory is NOT the restart route's cause; that cause stays unknown 🤔
(its flush runs at SQX's exit). Cost of one real mother live: load 11 s, run 1,564-1,709 s, flush 206 s, clear 11 s.
`live.sync` gives up after 120 s without a new file (a fixed 120 s was too short for this flush).

## Evidence
🔬 Custodian `SQX_w2` (80 GB), `Test_NIKKEI225_M30_simpleL_val`, 10 NIKKEI225 M30 mothers × 500, restart route
`python3 -m sqx.variants.execute`, 2026-10-05.
- 5,000 loaded: `synchronizeDatabank` WFC_Build «files before sync 0 / after sync 3952 / saved 3952 / removed 0 in 166.05 s»;
  WFC_OOS1 and WFC_OOS2 had 5,000 each. 1,048 missing.
- Missing ones spread evenly: 380-406 kept of 500 per mother; medians of NetProfit, trades, ProfitFactor (from the
  previous night's per-mother run) equal to the kept ones; every design stratum hit.
- Same experiment with 2,500 (5 mothers): 2,500 / 2,500 / 2,500.
