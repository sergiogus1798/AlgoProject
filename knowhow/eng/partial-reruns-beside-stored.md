---
q: only re-run one sub-test partial result overwrites stored crossmarket --only monteCarlo _rerun no selectors parciales merge fuse beside OPEN 54, report --only same file, partial tab draws nothing
tag: 🔬  date: 2026-09-28  see: eng/qt-painting-traps
---
# A sub-test re-run goes beside the stored result, never through the study's own `report --only`
- `crossmarket.report --strategy S --only F` rewrites the full run's `estrategias/S.json` (OPEN §54). The window runs `ui.daemon.results.rerun`: `one.run(only=…)` into `<study>/parciales/<stamp>_<only>/estrategias/S.json`; `store.load` attaches them as `result["partials"]`.
- **A partial tags its blocks but writes no `selectors`** (monteCarlo `_rerun`): honouring only the tab's selectors draws nothing. `blocks/pick.selectors` derives them from the tags.
- Merge is on screen only (`blocks/fuse.merge`): tagged blocks replaced, untagged ones and the verdict stay stored.

## Evidence
- 🔬 2026-09-28: `only` of `EURUSD_DukasM1_the5ers` on `Test_USDJPY_donchianUpperCrossUp_M30 / Retest_Markets_-_Family /
  Strategy 9.18.85(1)`: the stored JSON kept its 4 465 741 bytes and `computed_at 2026-09-27T08:38:42`; `/api/result`
  returned it with one partial (tabs random, sweep, stress, fingerprint; verdict None).
- `portfolio/common/monteCarlo/one.py` `_rerun` calls `envelope.tab("explorer", …, body)` without `selectors`.
