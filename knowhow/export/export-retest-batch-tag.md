---
q: export_retest --batch same day overwrite, steps 23 24 25 same databank collide, structure report could not be rerun, export_dir batch tag, atrCalculator newest structure latest
tag: 🔬  date: 2026-09-29  see: export/data-all-crossmarket
---
# `export_dir(project, databank, day)` has no step in the path — tag same-day exports with `--batch`
Two steps retesting the same project's `WFC_*` databanks the same day overwrote each other's
`trades.parquet` — steps 23 (`sqx.structural`) and 24 (`sqx.variants.stopgrid`) both do (OPEN #74,
hit 2026-09-27: step 23's report could not be rerun after step 24 ran). Fixed: `export_dir(...,
batch="")` nests under a tag, `export_retest.py --batch <tag>` sets it (step 23 `structure`, step
24 `stopgrid`); the two readers that glob for the newest export
(`studies.readings.structure.inputs.latest`, `studies.closing.atrCalculator.inputs.newest`) look
for their own tag first, falling back to the old flat layout. No `--batch` is unaffected.

## Evidence
- Stored `manifest.json` of `Test_USDJPY_donchianUpperCrossUp_M30/Retest_Markets_-_Family/2026-09-28`
  showed a step-24 command overwriting a step-23 export written the same day, same `raw/<P>/<D>/<day>/`.
- After the fix: `export_dir("P", "WFC_Build", "2026-09-29", "structure")` and `..., "stopgrid")`
  resolve to distinct paths; `structure.inputs.latest`/`atrCalculator.inputs.newest` each prefer
  their own tag's `trades.parquet` when present.
