---
q: step 20 blind door refuses, faltan [17, 18, 19], WFC CSCV WFM write no ledger row, allow_read never opens, backfill --blind, step 20 cannot read oos2, BlindJoint reserved_for, CSCV reads oos2 not in reserved_for
tag: 🔬  date: 2026-09-26  see: research/cscv-always-reads-oos2
---
# Steps 17, 18 and 19 write no ledger row, so step 20's door never opens by itself
`ledger.gate.allow_read` opens only on rows for 17, 18 and 19, and the WFC, CSCV and WFM reports
record none. After they run: `python3 -m ledger.backfill --blind <project> --symbol S --timeframe TF
--family F` (dry run), then `--write` once — a second write is refused. Then step 20 reads the four
pieces. Its SPA on oos2 stays unread until the owner adds `BlindJoint` to oos2's `reserved_for` in
`assets/_policy.yaml`: the policy lists neither step 20 nor the CSCV, which reads oos2 anyway.

## Evidence
- `grep -rn "record.log" studies/` — only snoopingScreen (8), marketSurfaces (18.5), atrCalculator (24).
- `USDJPY_H1_crossAboveHMA_v1` before the backfill: `studies.closing.blindJoint.report` raised
  `faltan [17, 18, 19]` although wfc/cscv/wfm results existed for 2026-09-26; after 15 backfilled
  rows `ledger.report` prints "los tres están".
- `gate.allow(20, "oos2", "USDJPY")` raises; `cscv.json` has `periods: 982` weeks = 2008–2026.
- ⚠️ The family is part of the study id: atrCalculator logged USDJPY under
  `USDJPY_H1_USDJPY_workflow_profiling_v1` (project as family), the rest under `…_crossAboveHMA_v1`.
