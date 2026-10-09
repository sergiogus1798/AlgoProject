---
q: What counts as a period (bar length) to rescale when building a cross-timeframe sibling?
kw: crossTF scale periods, ParamTypePeriod, lengths.yaml, custom block length, regex name missed length 64.8 %, MACD fast slow signal, Stochastic slowing, WaveTrend QQE Int1 Int2 Int3, WAE Sensetive multiplier, BBStdev, unusable sibling
tag: 🔬  date: 2026-10-02  see: sqx-format/declared-parameters, sqx-drive/crosstf-one-task-per-timeframe, research/crosstf-mother-sibling-dependence
---
# A period is what SQX types `ParamTypePeriod`, plus `sqx/variants/lengths.yaml` for custom blocks — not a name regex
Rescale a variable when its `<paramType>` is `ParamTypePeriod`; a custom block's variables are ruled by
`lengths.yaml` only (73 blocks of the six v3 palettes, 181 parameters). The name regex missed a length in **64.8 %**
of strategies (MACD fast/slow/signal, Stochastic slowing, WaveTrend, QQE, custom `Int1/2/3`). Two rulings against
SQX's typing: WAE `Sensetive` (a multiplier) and `BBStdev` (a deviation) are NOT lengths. Unverified or unlisted
custom-block lengths stay unscaled and the sibling is `unusable`. Floor 2 (block sources declare minimum 2 in 151
cases). Whoever authors a custom block adds it to `lengths.yaml`.

## Evidence
- 📓 `AlgoData/scratch/calib_step12/report_addendum.md` §A, §J; census `coverage_v3.csv` (600 samples): unscaled 64.8 % → 0 %.
- Code `sqx/variants/lengths.py`, `scale.py`; golden test `tests/test_scale_lengths.py`. Tag format: `sqx-format/declared-parameters`.
- Rounding/clamped (> 15 %) is recorded, never a gate (owner, 2026-10-02): H1→H4 22.7/36.7 %, M30→H4 52.8/77 % (M30 simulated on H1 files).
- 🤔 `Int1` (`NoBars`) of `CBlock_WAEPosAboveExplosion_2_2_3` is unverified: a source read would settle it.
