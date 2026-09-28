---
q: pair a study's result with a strategy of another databank; mcRetest crossTF identity equals Results identity; pre_mcr_identity; which reports carry identity; batch estudios wfc cscv cloud identity None; join reports across databanks; identity after the databank left every install; identify from harvest
tag: 🔬  date: 2026-09-28  see: locations/crossmarket-report-signs-no-identity, databanks/curate-verdict-identity-per-databank
---
# Studies resolve identity installs → cosecha → kept .sqx, so a retired project still signs; crossmarket and the batch studies still may not
`core.study.identity.resolve` (what `output.identify` calls) reads the `.sqx` on an install, then the
newest cosecha not newer than the export that paired THAT databank (`strategy_build` for its build
databank, `strategy` for its OOS one — both keyed by the build identity), then the `.sqx` the export
kept in `strategies/` (export_spp). mcRetest (`pre_mcr_identity.csv`) and crossTF sign the build's
identity; edgeCost, spp (`strategies.csv`), profitShape and monkey (`nulls.csv`) now do too.
`crossmarket` signs nothing once its `Retest Markets` databank is gone (no cosecha, export_retest keeps
no `.sqx`); a mother's batch studies (`estudios/{cloud,wfc,cscv}.json`) sign `identity: None`.

## Evidence
`Test_USDJPY_donchianUpperCrossUp_M30` (no install holds it), 2026-09-28, `tests/test_identity.py`:
`from_harvest(P,"OOS")` and `from_export(SPP_IS/2026-09-27/spp)` → `Strategy 10.11.79` = `4d679e0c…`,
same as `Results/gate/verdict.csv` and `MCR_All/mcRetest`. `python3 -m core.archive archive … --step
16.5 --note E5` froze edgeCost, spp, profitShape, monkey; only `Retest_Markets_-_Family/crossmarket`
«sin identidad». Earlier (2026-09-27): matrix Retest_Markets 0 of 208, SPP_IS 0 of 3 signed.
