---
q: master conductor custodian roles; why two workers; custodian sync rule only status between start and collect; which install exports a databank; opening a worker GUI syncs; core split elastic coreUsage
tag: 🔬  date: 2026-09-23  see: sqx-drive/install-ports-and-heap, databanks/sync-deletes-unloaded-files, sqx-drive/driving-a-role
---
# One master + two headless workers: conductor W1 answers, custodian W2 holds the one long job
M `~/Desktop/SQX` (owner's GUI) · W1 conductor `~/Desktop/SQX_w1` 5060 (queries, authoring) ·
W2 custodian `~/Desktop/SQX_w2` 5070 (large databank, one long job). Between "start" and
"collect" the custodian gets only `-project action=status` (owner, 2026-09-25) — never `count`
(it syncs from files, `databanks/databank-verbs`), a load or an export: that is what keeps hard rule 1 from tripping.
Only the install holding a databank can export it. Never open a worker's GUI with a big databank inside.

## Evidence
Decision: execution plan of 2026-09-21 §3 (retired, in git history). Ports/heap/settings: `sqx-drive/install-ports-and-heap`.

Why two workers, by value:
1. A busy worker cannot answer: one worker queues list/count/status/authoring behind a 3-hour retest.
2. Rule 1 is per install: any command to the install holding a 5,000-variant databank may trigger a
   sync that prunes disk to memory. A dedicated custodian removes the risk by construction.
3. Overlap: W1 exports mother N's trades while W2 retests mother N+1's variants.

⚠️ `-databank` verbs address the instance's own projects, so W2 exports the variants — why W1 stays small.
⚠️ Opening a worker's GUI triggers syncs and must never overlap its CLI daemon; with a big databank
inside it is the USDJPY log scenario (`before sync 248 / after sync 36 / removed 248`). Inspect before
fabricating or after collecting. 🤔 Inferred from master behaviour, not verified on a worker.
⚠️ A worker is cloned without `user/projects`: W2 starts with only the 5 stock projects
(`Builder`, `Optimizer`, `Retester`, `PortfolioMaster`, `PortfolioComposer`) — correct for a custodian.

Core split is elastic: master stays `coreUsage -1` (its `settings.xml` never edited — hard rule 3),
only workers capped (W1 8/2, W2 48/8 on 96c/16c). Linux CFS shares by runnable threads: idle workers →
master keeps the whole machine; W2 running (95 vs 48 threads) → master still ~66 %. A static split
would halve generation even on an empty machine.
