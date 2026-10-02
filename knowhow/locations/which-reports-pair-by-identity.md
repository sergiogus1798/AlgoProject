---
q: pair a study's result with a strategy of another databank; mcRetest crossTF identity equals Results identity; pre_mcr_identity; which reports carry identity; batch estudios wfc cscv cloud identity None; join reports across databanks; identity after the databank left every install; identify from harvest; structural atrCalculator lote estrategias not under reports; two passes same mother
tag: 🔬  date: 2026-09-30  see: locations/crossmarket-report-signs-no-identity, databanks/curate-verdict-identity-per-databank
---
# Studies resolve identity installs → cosecha → kept .sqx, so a retired project still signs; crossmarket and the batch studies still may not
`core.study.identity.resolve` (what `output.identify` calls) reads the `.sqx` on an install, then the
newest cosecha not newer than the export that paired THAT databank, then the `.sqx` the export kept
in `strategies/`. mcRetest, crossTF, edgeCost, spp, profitShape and monkey sign the build's identity.
`crossmarket` signs nothing once its databank is gone; a mother's batch studies
(`estudios/{cloud,wfc,cscv,marketSurfaces}.json`) sign `identity: None`. `structure`/`atrCalculator`
sign their own real identity from a one-off lote of several mothers (`structural/`/`atrCalculator/`,
never `reports/`) — `ui.daemon.results.lote.path` finds them by name, project-wide.

## Evidence
`Test_USDJPY_donchianUpperCrossUp_M30` (no install holds it), 2026-09-28, `tests/test_identity.py`:
`from_harvest(P,"OOS")` and `from_export(SPP_IS/2026-09-27/spp)` → `Strategy 10.11.79` = `4d679e0c…`,
same as `Results/gate/verdict.csv` and `MCR_All/mcRetest`. `python3 -m core.archive archive … --step
16.5 --note E5` froze edgeCost, spp, profitShape, monkey; only `Retest_Markets_-_Family/crossmarket`
«sin identidad». Earlier (2026-09-27): matrix Retest_Markets 0 of 208, SPP_IS 0 of 3 signed.
2026-09-30 (block G's audit, `Test_USDJPY_donchianUpperCrossUp_H1`/`_M30`): `structure` found by
name for all 6 real mothers (`structural/<P>/<lote>/estudios/structure/estrategias/<name>.json`);
H1's `atrCalculator` has the same 3 mothers in both `pass1` and `pass2` — refused, not guessed.
