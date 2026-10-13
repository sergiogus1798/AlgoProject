---
q: Which blind steps (WFC, CSCV, WFM) record their own look in the ledger?
kw: step 20 blind door refuses, faltan [17, 18, 19], WFC CSCV WFM write no ledger row, allow_read never opens, backfill --blind, step 20 cannot read oos2, BlindJoint reserved_for, CSCV reads oos2 reserved_for, --family required wfc cscv, lote note
tag: 🔬  date: 2026-10-04  see: research/cscv-always-reads-oos2
---
# The WFC and the CSCV record their own look since 2026-09-27; the WFM (19) does since 2026-10-04
`wfc.report` and `cscv.report` take `--family`, ask `gate.allow` per segment before opening the
batch, and write one ledger row per segment read (WFC: its composition's segments, step 17; CSCV:
build, oos1, oos2, step 18 — the owner put `CSCV` in oos2's `reserved_for` on 2026-09-27). The WFM
writes its three rows live since 2026-10-04 (`wfm.report` → `ledger.steprows.log_wfm`, once per export folder); `backfill --blind` is for runs before that: `python3 -m ledger.backfill --blind <project> --symbol S
--timeframe TF --family F` (dry run, then `--write` once). `blind` skips a batch whose live rows
exist (note opens `lote <batch>`). ⚠️ Since 2026-09-28 the door binds only under
`ALGO_AUTONOMOUS=1`; for a human it is open (`pipeline/oos2-door-binds-only-autonomous`).

## Evidence
- 2026-09-27, `Strategy_9.27.83` of `Test_USDJPY_donchianUpperCrossUp_M30`: two compositions + the
  `oos2_only` shortcut + the CSCV left 11 rows in `USDJPY_M30_Test_USDJPY_donchianUpperCrossUp_M30`;
  `ledger.report` then prints `17 hecho · 18 hecho · 19 pendiente`; `blind.from_batch` on that batch
  returns 0 rows with the ledger read, 6 with an empty one.
- Before (2026-09-26), `USDJPY_H1_crossAboveHMA_v1`: blindJoint raised `faltan [17, 18, 19]` although
  results existed; 15 backfilled rows opened it.
- ⚠️ The family is part of the study id: atrCalculator [deleted 2026-10-11, step 24] logged USDJPY under
  `USDJPY_H1_USDJPY_workflow_profiling_v1` (project as family), the rest under `…_crossAboveHMA_v1`.
- The window's runner passes `--family`
  since 2026-09-28: the template folder from `projects/registry.csv` (`ui/daemon/runner/where.family`).

## Step 6 (2026-10-04) 🔬
SQX's project log `log/global_log_*.log` ends a Build task with one line, `Strategies generated: G, ...,
Accepted: A, Rejected: R` (not the multi-line `Status of project` block, which has no count of accepted).
`ledger.steprows.log_build` writes it as step 6: `n_in`=G, `n_out`=A, `n_scored`=G with `score_unit`
"generated". `trials.accumulated` adds that unit to N and keeps it out of sigma (no Sharpe was kept), so a
build's millions raise N without poisoning sigma. A = SQX's "Accepted", before its similarity filter (e.g.
4600 accepted, 4238 in databank). `trials.overall` is the N over every study; `ledger.report` prints it.
