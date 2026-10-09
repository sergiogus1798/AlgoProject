---
q: Why is step 12's z_build of scaled sisters not centred on 0, and why is the D1 sister empty?
kw: n_build inflated, sister trades pooled across timeframes, z_build H4 sister clamped, crosstf step 12 z_new never 2.33, D1 sister no trades, scaled sister timeframe, step 11.7 CrossTF build
tag: 🔬  date: 2026-10-09  see: pipeline/step10-p1-p7-never-have-data
---
# Step 12's `z_build` of ±10-19 was every phase-2 databank pooled under one sister name (fixed 2026-10-09)
Each `CrossTF <TF> build` databank holds EVERY strategy retested on that timeframe, not only that
timeframe's sisters. `crossTF.tf.inputs.build` concatenated them keeping only the name, so a sister's
build trades were her runs on all timeframes forced onto her own bars: 3-7 times her trades. Now each
databank gives only the sisters fabricated for its timeframe; the mother comes from `Results` alone.
The crossTF facts of runs before the fix (`n_build`, `e_build`, `z_build`, `ret_build`, `phi`, `z_frec`,
`t1`, `t2b`) are wrong; `z_delta`, `ret`, `t2a` and step 12's rule (`z_new`, oos1) were never touched.
The D1 sister (always `clamped`, ~30 oos1 trades) no longer exists: the owner removed D1 from crossTF on 2026-10-09.

## Evidence
- 🔬 Mean `z_build` by sister TF: M15 +0.7..+1.1, M30 +1.2..+1.7, H1 -2.1..+2.5, H4 -9.7 (cal2), +12 (cal1), +14.8 (cal3), +5.9 (cal5). Within-run ranges: -10..+13 (cal4 H4), -5..+16 (cal5 H4).
- 🔬 D1 sister clamped (and almost without trades) in every mother: cal1 8/8, cal3 2/2, cal4 17/17.
- 🔬 cal5 (DAX40 M30), median `n_build` per sister before → after the fix: M15 217 → 166, H1 788 → 166, H4 1,057 → 156.
- 🔬 `z_new` never reached 2.33 in five runs (max 1.95): a separate question, not this bug.
- 📓 Sister timeframes per mother timeframe: `assets/_build.yaml` (`H1: [M30, H4]`, D1 removed 2026-10-09).
