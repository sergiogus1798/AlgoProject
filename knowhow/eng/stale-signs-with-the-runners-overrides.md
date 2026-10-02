---
q: false Caducado right after a run; stale cloud results; config_hash vs current_hash with --set overrides; forproject.SET run.symbol; split_mode drop-down makes WFC stale; which hash a result is compared with; stale.fresh
tag: 🔬  date: 2026-10-01  see: eng/population-signs-a-different-config-than-strategy
---
# A result is stale only when no way the window could run it today signs its hash
The window runs several studies with per-project `--set` overrides (`ui/daemon/results/forproject.py`
`SET`: cloud's `run.symbol`, the gate's `monkey.timeframe`, exposure, conditionalMap,
entryQuality), and the run signs the config WITH them. Comparing against the bare config
(`knobs.signed(study, [])`) marked 14 of 15 freshly run H1 clouds «Caducado». `ui/daemon/results/
stale.fresh` now builds every hash a run could sign today — the runner's overrides, or those the
run recorded in its `manifest.json` — each under every value of a per-run choice
(`knobs.CHOICES`, the WFC's `split_mode`), and a result is stale only when its hash is none of them.

## Evidence
`Test_USDJPY_donchianUpperCrossUp_H1`, 2026-10-01: cloud stale 14/15 → 1/15 (the one left,
`Strategy 16.9.76`, really ran with the donor's XAUUSD symbol); gate matrix on Results 300/300
stale → 0. `knobs.signed('wfc', ['split_mode=oos1_oos2'])` = e000e7f0 vs bare a046d42.
