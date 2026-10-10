---
q: Why did a stored strategy lack its crossmarket and its step-12 sisters, which sat under another identity?
kw: second identity, dos identidades, lineage.csv mutual mother, crossmarket missing in store, hermanas missing, late.aliases, 655ae1f0 0cccd976, 03c8814a 10849db5, core.store save
tag: 🔬  date: 2026-10-10  see: sqx-format/identity-differs-across-databanks, sqx-format/strategy-identity
---
# A strategy SQX gave a second identity is saved whole under the gate's one
SQX retests (crossmarket, the step-12 mother copy) can hand a strategy another identity M. `lineage.csv`
then names each of the two the other's mother: `late.mothers` holds `G -> M` and `M -> G`. `store save`
looked for G only, so crossmarket.* and `hermanas.*` (the mother `.sqx` carries M) were never stored.
Fix: `late.aliases(project, G)` returns M **only for a mutual pair** (a variant's mother does not point
back, so a variant is never an alias); `collect.freeze(..., also)` and `extra.sisters(..., also)` match
on any of them. One folder, G's; no folder for M. Measured: mc4 1 mutual pair, mc3 5, all with the same
strategy name. A store saved before the fix needs one re-save (adds only the new zips).

## Evidence
- `tests/test_store_late.py::test_a_second_identity_is_an_alias_only_when_the_two_name_each_other_mother`
- Re-save of `Test_DAX40_M30_momentumL_mc4` from copies of its stored `.sqx` (`--sqx-dir`): 655ae1f0
  gained `crossmarket.*` (17 distributions) and `hermanas` (3 sisters); store still holds 3 for mc4.
