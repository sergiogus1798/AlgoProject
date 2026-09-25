---
q: SPP headless on a worker progress; SPP silent no log is it hung; SPP memory cost; optprofile.read permutations count wrong; staged strategy already has optimizationProfile.bin; dontStoreOP3DChartsData
tag: 🔬  date: 2026-09-22  see: sqx-drive/spp-task-type, sqx-format/optimization-profile-bin
---
# A headless SPP persists fine; judge progress by JVM RSS, one SPP per install
Not: "the SPP runs headless but writes nothing" — that was `SequentialOptimization` (`sqx-drive/spp-task-type`).
`status` shows `Total tested 0` / `0 ms` throughout; log goes silent after the first seconds.
Climbing RSS = work; flat RSS + no log = hang. `sqx/variants/spp.py` reports elapsed vs cap, not %.
Count permutations with `len(results)`, never the `permutations` field.

## Evidence
- Measured on custodian, real XAUUSD mother (22 params), `Steps 40`, ±35 %, `testPrecision 1`, 2008–2017, M30:
  all 22 `… Optimizing parameter <name>...` lines within 3 s, next log line >30 min later; RSS
  23.6 → 25.7 → 32.5 → 36.9 GB over ~30 min on a 48 GB heap. ⚠️ This run was later found to have
  `SequentialOptimization` on; 🤔 the silence/RSS pattern is assumed to hold for the true SPP.
- ⚠️ Memory binds, not time: a profile ~20 MB on disk is tens of GB while built; 48 GB heap holds one; never two concurrently on one install.
- 🔬 `optprofile.read`: a 306 KB profile reports `permutations: 2533` whether or not `results` holds
  rows; usable = `permutation_results` + non-empty `results`. 📓 `runs.csv` of 2026-09-10 export: 3,940
  permutations for `Strategy 17.9.39` vs field 2,533.
- ⚠️ A strategy staged from `raw/…/strategies/` already carries the master's 306 KB
  `optimizationProfile.bin`; reading it after a worker SPP looks like success. Test on a 5-member
  variant (no profile member). But reconnaissance needs a strategy with real parameters and trades —
  an 8-param fabricated variant finished in seconds and misled.
- `dontStoreOP3DChartsData` in `user/settings/settings.xml` (per-permutation detail kept only when
  `false`): `false` on all three installs (read 2026-09-25).
  📓 `sqcli` has never rewritten `settings.xml` (W2's stamped at clone time across a dozen starts).
- `export_spp.py --role custodian` reads a worker profile.
