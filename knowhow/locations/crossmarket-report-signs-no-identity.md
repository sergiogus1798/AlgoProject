---
q: crossmarket verdict.csv identity empty, crossmarket JSON identity None, pair crossmarket result to a strategy, archive leaves crossmarket out, Strategy X(1) duplicate name in Retest Markets databank, export_retest identity.csv
tag: 🔬  date: 2026-09-28  see: sqx-format/identity-differs-across-databanks, locations/which-reports-pair-by-identity
---
# A crossmarket report signs identity only if its export kept identity.csv (export_retest does since 2026-09-28)
`crossmarket.load` resolves names through `identity.resolve` (installs → cosecha → the export's
`identity.csv`, written from the staged `.sqx` before they are deleted). The retest databank is never harvested, so an export made before 2026-09-28 of a
retired project gives every row `identity` empty and a `note`, and each `estrategias/*.json` an
`identidad` warning. Pairing by name is a guess: the databank can hold `Strategy 10.11.79` **and**
`Strategy 10.11.79(1)`. Re-export the databank to sign an old run.

## Evidence
USDJPY `Test_USDJPY_donchianUpperCrossUp_M30`, report of 2026-09-27: `verdict.csv` 0 of 208 rows with an
identity; `raw/.../Retest_Markets_-_Family/2026-09-27/` holds only `trades.parquet` and
`manifest.json`; the retired tarball holds `project.cfx` alone. 2026-09-28 `output.identify` on that
export → `{"Strategy 10.11.79(1)": None, "Strategy 10.11.79": None}` (`tests/test_identity.py`).
