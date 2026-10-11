---
q: Why does a run that died mid step 16.5 die again on resume, at step 18.5?
kw: marketSurfaces no hay lote de variantes con metrics.parquet segments.parquet variant_trades.parquet; 16.5 done with one mother collected.json; derive.variants; plan.reopen OPEN #111; 2 de 3 madres con su lote; OutOfMemoryError 16.5 resume
tag: 🔬  date: 2026-10-11  see: pipeline/variant-batch-refused-on-negative-zero, pipeline/study-partial-evidence-counts-as-done, sqx-drive/second-server-gorilla
---
# Step 16.5 counted as done with ONE mother's batch, so the lane went on to 17-19 and failed at 18.5
Trap: resume skipped 16.5 and failed later: `marketSurfaces: no hay lote de variantes con metrics.parquet, segments.parquet, variant_trades.parquet para <mother>` (18.5).
Cause: `derive.variants` said `done` on `if collected:` (any ONE mother's `collected.json`); `plan.reopen` (OPEN #111)
checks only the previous run, which had failed at 18.5, and tested `kind == "python"` while 16.5 is `sqx` in the step table.
Fix: `derive.variants` needs ALL mothers, else `pending` («2 de 3 madres con su lote: el paso se rehace entero»);
`reopen` reopens 16.5 by number. Step 13 left out on purpose (its MC Retest tasks would come along). Redoing 16.5
repeats every mother (~5 min each; `variants.run` does not skip harvested ones).

## Evidence
🔬 gorilla, 2026-10-11: the OOM left 2 of 3 mothers harvested. Commits `2c973de` (derive) and `4532b88` (`plan.reopen`).
Reproduce: count `collected.json` under `AlgoData/strategyPermutations/<P>/<mother>/` against the mothers of the plan.
