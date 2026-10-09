---
q: What does exporting every variant's trades cost, and why is it no longer only the mother's?
kw: variant_trades.parquet export_retest --batch variants varianttrades 90 minutes per batch mothertrades only the mother's trades E3 reverted equity 1.5 s
tag: 📓  date: 2026-10-07  see: variant-route
---
# Every variant's trades cost ~90 min per batch; the reference run measured it
Decision E3 (owner, 2026-10-04) kept only the mother's trades (`sqx/variants/mothertrades.py`). Encargo 48
reverts it for the batch: the WFC and the cloud price each variant's trades as step 14's excess, which
the per-day equity (962 variants in 1.5 s) cannot give. The autopilot exports the three legs after
`collect` and before `execute --clear` (`pipeline/autopilot/variants.py`), `sqx.variants.varianttrades`
reunites them into `variant_trades.parquet` and deletes the per-leg exports. `mothertrades` stays for step 20.

## Evidence
`sqx/variants/README.md` (equity line); no real batch with the file exists yet: the ~90 min is the
reference run's export time, not a measurement of the new chain (OPEN.md, part V of encargo 48).
