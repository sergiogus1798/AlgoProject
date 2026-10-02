---
q: Build task acceptance filters; Rankings Conditions; filtering conditions of the builder; _study.yaml; donor NumberOfTrades 500 SortinoRatio Stagnation; first Conditions is BuildMode initial population; sampleType 10 IS in a Build; calibration filters
tag: 🔬  date: 2026-10-02  see: conditions/condition-xml-shapes, conditions/selection-window, research/post-selection-bias, sqx-drive/unselected-build-population
---
# A Build accepts by `<Rankings><Conditions>`; the FIRST `<Conditions>` of the task is not it
A Build task's first `<Conditions>` is `<BuildMode>`'s (initial population): `acceptance.CONDITIONS.search(task)`
and `crosschecks.silence(task)` hit it. Write acceptance only through `sqx.projects.rankings` (slices
`<Rankings>`), values from `assets/_study.yaml`; `builder` does it for every new project and refuses on a
missing value. Read `resultType="main" subresult="30" sampleType="10"` (IS): 127 equals 10 only while the
Build has no `<OutOfSample><Range>`; 11 ≡ 10 and 40 is never stored.

## Evidence
- Before 2026-10-02 every project carried the frozen donor's `NumberOfTrades > 500`, `SortinoRatio > 0.6`,
  `Stagnation < 540` (sampleType 127), which no repo file stated.
- Trade bounds are totals: trades/yr × build years (XAUUSD 10.0, DAX40 6.25) — the donor's 500 was 50/yr on FX and 80/yr on DAX40. The compact one-line `<Condition>` shape `acceptance.condition` writes is honoured.
- Donor `AlgoData/projectsBackup/XAUUSD_base_2026-09-21/project.cfx`, `Build-Task3.xml`: 33 `<Condition `; `<BuildMode>` conditions at
  offset < `<Rankings>`. `tests/test_build_acceptance.py`: golden XML, `<BuildMode>` byte-equal after the write.
- sampleType codes from SQX's JS bundle: in 10 · ist 11 · isv 40 · out 20 · oos1..10 21-30 · full 127.
- `--acceptance calibration`: `NumberOfTrades >= 100 & NetProfit > 0`, build MonteCarloManipulation off
  (its conditions are off after `set_crosschecks`; it only costs CPU). Replaces `calib_queue/calib_filters.py`.
- 🔬 2026-10-02 A/B, 3 cells × 4 arms, 6-min GA builds (`AlgoData/scratch/calib_final/ab_build.md`): a real floor in the
  Build (30-75 trades/yr & PF ≥ 1.20) yields fewer OOS-good per accepted than calibration filters (4.8→2.0 %, 13.6→8.9 %,
  0.48→0.07 %) and no more than the same cut applied after the build; 40-75 and 50-100 are worse. SQX honoured the
  written bounds exactly (accepted IS trades 300–748, PF ≥ 1.20). One build per arm.
