---
q: step 20 blind door refuses, faltan [17, 18, 19], WFC CSCV WFM write no ledger row, allow_read never opens, backfill --blind, step 20 cannot read oos2, BlindJoint reserved_for, CSCV reads oos2 reserved_for, --family required wfc cscv, lote note
tag: 🔬  date: 2026-09-27  see: research/cscv-always-reads-oos2
---
# The WFC and the CSCV record their own look since 2026-09-27; the WFM (19) still does not
`wfc.report` and `cscv.report` take `--family`, ask `gate.allow` per segment before opening the
batch, and write one ledger row per segment read (WFC: its composition's segments, step 17; CSCV:
build, oos1, oos2, step 18 — the owner put `CSCV` in oos2's `reserved_for` on 2026-09-27). The WFM
writes none, so the blind door still needs `python3 -m ledger.backfill --blind <project> --symbol S
--timeframe TF --family F` (dry run, then `--write` once). `blind` skips a batch whose live rows
exist (note opens `lote <batch>`). Step 20's SPA on oos2 stays unread until `BlindJoint` is added.

## Evidence
- 2026-09-27, `Strategy_9.27.83` of `Test_USDJPY_donchianUpperCrossUp_M30`: two compositions + the
  `oos2_only` shortcut + the CSCV left 11 rows in `USDJPY_M30_Test_USDJPY_donchianUpperCrossUp_M30`;
  `ledger.report` then prints `17 hecho · 18 hecho · 19 pendiente`; `blind.from_batch` on that batch
  returns 0 rows with the ledger read, 6 with an empty one.
- Before (2026-09-26), `USDJPY_H1_crossAboveHMA_v1`: blindJoint raised `faltan [17, 18, 19]` although
  results existed; 15 backfilled rows opened it.
- ⚠️ The family is part of the study id: atrCalculator logged USDJPY under
  `USDJPY_H1_USDJPY_workflow_profiling_v1` (project as family), the rest under `…_crossAboveHMA_v1`.
- `pipeline/recipe.yaml` still calls both reports without `--family`. The window's runner passes it
  since 2026-09-28: the template folder from `projects/registry.csv` (`ui/daemon/runner/where.family`).
