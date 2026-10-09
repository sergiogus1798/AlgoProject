---
q: Why does the autopilot not run monkeyExcess after step 8's cut?
kw: necesita el panel del mono de toda la población; monkeyExcess refused; strict python step ended run at step 8; after_cut; nulls.csv picked list; KeyError 'strategy' monkey report
tag: 🔬  date: 2026-10-09  see: eng/monkeyexcess-needs-oos-partner, pipeline/monkey-after-cut-has-no-cap
---
# The autopilot does not run `monkeyExcess` after the cut: `monkey` on a picked list writes no population panel
`monkey` on a picked list of survivors reads one strategy at a time and writes no `nulls.csv`, so
`monkeyExcess` was refused every time («necesita el panel del mono de toda la población») and, being a
`strict` python step, ended the run at step 8. Since 2026-10-08 `after_cut` in `pipeline/autopilot/run.py`
moves it out of the step and does not run it. No rule of `criteria.yaml` reads it. It returns when
`monkey` writes a panel for a picked list, or if the owner wants the whole population through the monkey
(owner's decision, pending).

## Evidence
- 🔬 Six calibration runs cal1-cal6 (2026-10-08/09, `AlgoData/autopilot/Test_<...>_calN/`): refusal in each, before the fix.
- 🔬 `studies/readings/monkey/report.py` raised `KeyError: 'strategy'` (~line 55): it read the strategy from the JSON `where` column, while `draws.record` stores it in its own `strategy` column. Fixed.
