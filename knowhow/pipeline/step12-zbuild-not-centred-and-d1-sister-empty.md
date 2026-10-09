---
q: Why is step 12's z_build of scaled sisters not centred on 0, and why is the D1 sister empty?
kw: z_build H4 sister clamped, crosstf step 12 z_new never 2.33, D1 sister no trades, scaled sister timeframe, step 11.7 CrossTF build
tag: 🔬  date: 2026-10-09  see: pipeline/step10-p1-p7-never-have-data
---
# Step 12's `z_build` of scaled sisters is not centred on 0 and grows with the sister's timeframe (undiagnosed)
Many H4 sisters are `clamped`. With an H1 mother the D1 sister is clamped and has almost no trades.
`z_new` never reached 2.33 (max 1.95): step 12 gave only Limbo. Phase 2 (step 11.7, `CrossTF <TF> build`)
runs live and step 12 reads it. 🤔 Cause unknown; a planted-edge run on a sister would confirm whether
the scaling or the null is off.

## Evidence
- 🔬 Mean `z_build` by sister TF: M15 +0.7..+1.1, M30 +1.2..+1.7, H1 -2.1..+2.5, H4 -9.7 (cal2), +12 (cal1), +14.8 (cal3), +5.9 (cal5). Within-run ranges: -10..+13 (cal4 H4), -5..+16 (cal5 H4).
- 🔬 D1 sister clamped (and almost without trades) in every mother: cal1 8/8, cal3 2/2, cal4 17/17.
