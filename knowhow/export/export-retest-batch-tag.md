---
q: export_retest --batch same day overwrite, steps 23 24 25 same databank collide, structure report could not be rerun, export_dir batch tag, atrCalculator newest structure latest, KeyError variant_id structure rerun after WFC redone
tag: 🔬  date: 2026-09-30  see: export/data-all-crossmarket
---
# `export_dir(project, databank, day)` has no step in the path — tag same-day exports, and never trust "newest" alone across days either
Two steps retesting the same `WFC_*` databanks the same day overwrote each other's
`trades.parquet` (OPEN #74). Fixed: `export_dir(..., batch="")` nests under a tag,
`export_retest.py --batch <tag>` sets it; readers of the newest export prefer their own tag.

Same shape across DAYS (2026-09-30): a batch reported on `2026-09-27`, then an untagged WFC
re-run on `2026-09-29` left a newer `trades.parquet` with different `variant_id`s — `KeyError`
on the first mother. Fixed one level up: `structure.inputs.latest(..., required)` takes the
batch's `set(plan["variant_id"])`, keeps the first newest-first export that has them all.

## Evidence
- Stored `manifest.json` of `Test_USDJPY_donchianUpperCrossUp_M30/Retest_Markets_-_Family/2026-09-28`
  showed a step-24 command overwriting a step-23 export written the same day, same `raw/<P>/<D>/<day>/`.
- `export_dir("P", "WFC_Build", "2026-09-29", "structure")` and `..., "stopgrid")` resolve to
  distinct paths; `structure.inputs.latest`/`atrCalculator.inputs.newest` each prefer their own
  tag's `trades.parquet` when present.
- 2026-09-30: `structure.report --work .../Test_USDJPY_donchianUpperCrossUp_M30/2026-09-27
  --databank WFC_Build WFC_OOS1 ...` raised `KeyError: 'S00O00'` against the untagged
  `raw/.../WFC_Build/2026-09-29/trades.parquet`. Passing `required` into `latest()` falls back to
  `raw/.../WFC_Build/2026-09-27/trades.parquet` (has `S00O00`); the batch's 3 mothers process
  cleanly again. `Test_USDJPY_donchianUpperCrossUp_H1/batch1` (own `2026-09-30`-tagged export,
  newest and covers its 3 mothers) ran unaffected before and after.
- 2026-09-30: `structure.report --work .../Test_USDJPY_donchianUpperCrossUp_M30/2026-09-27
  --databank WFC_Build WFC_OOS1 ...` raised `KeyError: 'S00O00'` against
  `raw/.../WFC_Build/2026-09-29/trades.parquet` (no `structure` tag, an untagged WFC re-run).
  After passing `required` into `latest()`, the same command correctly falls back to
  `raw/.../WFC_Build/2026-09-27/trades.parquet`, which does carry `S00O00`, and the batch's 3
  mothers process cleanly again (`Test_USDJPY_donchianUpperCrossUp_H1/batch1`, whose own
  `2026-09-30`-tagged export is newest AND covers its 3 mothers, ran unaffected before and after).
