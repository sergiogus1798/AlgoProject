---
q: same strategy name different identity across databanks of one project, pair results across databanks, Results vs OOS vs MCR_All vs WFM identity, MCR_All drops Strategy prefix, matrix pairing by identity, name collision
tag: 🔬  date: 2026-09-26  see: sqx-format/strategy-identity, databanks/curate-verdict-identity-per-databank, sqx-format/loaded-name-is-filename
---
# Inside one project, the identity a study records for a strategy changes between databanks — pair results only inside one databank
On `USDJPY_workflow_profiling_v1` the build databank `Results` shares its names with every retest
databank but **0 identities**; `WFM` shares none with anyone; `MCR_All` even drops the `Strategy `
prefix (`1.23.51`). A view, a verdict or a join that pairs by name — or by identity across
databanks — mixes different records. The window's matrix reads one databank at a time for this.

## Evidence
- `ui.daemon.results.matrix.matrix(P, D)` identities, pairwise shared (2026-09-26):
  `Results` 200 vs CrossTF / MCR_All / OOS / Retest_Markets_-_Family / SPP_IS / SPP_OOS / WFM → 0 each;
  those six retest banks share 8 (3 with OOS) among themselves; `WFM` 3 → 0 with all.
- `Strategy 1.23.51`: `Results/gate` and `snoopingScreen` verdict.csv `0b91ad2b2354…`;
  `OOS/exposure`, `CrossTF/crossTF`, `MCR_All/mcRetest` `8f9c864c1f46…`.
- 🤔 Cause not investigated. The gate keys by the BUILD identity by design (`studies/screening/gate/
  pairing.py` keeps an alias for a retest identity that changed); `wfm` signs `None` in its JSON and
  its verdict.csv carries another. Contrast `strategy-identity`: 115/115 normalised identities
  matched across one XAU retest — so "identity survives a retest" is not general. Confirm with
  `core.sqxfile.identity()` on the `.sqx` files of two databanks.
