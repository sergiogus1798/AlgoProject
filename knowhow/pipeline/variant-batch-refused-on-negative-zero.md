---
q: Why does step 16.5 fail with «the batch on disk is not the batch that was planned; do not load it»?
kw: the batch on disk is not the batch that was planned; do not load it; tuple_mismatch; sqx.variants.make; -0.0; negative zero; tuple_hash; build.json; enum parameter MAMethod
tag: 🔬  date: 2026-10-10  see: pipeline/mother-names-differ-from-the-cosecha
---
# A design value of `-0.0` hashed apart from the `0` its file holds, and the factory refused the batch
Trap: `sqx.variants.manifest.verify` compares each variant's planned `tuple_hash` with the one read back
from its `.sqx`. `tuples.canonical` formats with `%g`, and `-0.0` prints `-0` while the file's `0` prints
`0`: same value, two hashes. The Latin hypercube leaves `-0.0` on a parameter whose range starts at 0 (an
enum such as `DidiIndexMAMethod1`), so about half of that mother's variants "mismatched" (500 of 1,004).
`build.json` shows it: `tuple_mismatch` large, `missing`, `unexpected` and `duplicate_tuples` all 0.
Fix (code): `canonical` adds `+ 0.0`, which folds `-0.0` into `0`; invariant in `tests/test_variants.py`.
A mismatch that survives this is a real one: read `plan.csv` against `manifest.parquet` column by column.

## Evidence
Test_USA500_H1_tendencia_wf1, run 20261010-173718, mother Strategy_7.11.427: every `param_*` column equal
within 1e-9 between `plan.csv` and `manifest.parquet`, only `tuple_hash` different; P00004 plan
`param_DidiIndexMAMethod1 = -0.0`, disk `0.0`. The other mother (20.17.293, no enum at 0) had 0 mismatches.
