---
q: Do step 14's T1/T2/T3 rules separate good strategies from unselected ones, and which should move?
kw: step 14, T1 build, f_pos, ret_med, beta_share, ret_med_aprox, T2, T3, drift over the build window, unselected reference, 0 of 9 pass step 14, aroonLong NIKKEI, circular oos1, planted edge
tag: 🤔  date: 2026-10-10  see: research/step8-gate-measured-on-six-populations, research/t1-optimistic-on-near-clones
---
# Step 14 follows the sign of the build window's drift, and T2 filters almost nothing (owner decision pending)
Rules: `pipeline/autopilot/criteria.yaml`, step "14". Measured 2026-10-09/10 (🔬 numbers, 🤔 conclusions, small n):
(a) T1 build's outcome follows the market drift over the build window (94 % of unselected fail on
NIKKEI H1, 10 % on DAX M30) more than any property of the strategy. (b) `ret_med` is a ratio over the
mother's excess: it explodes near zero (down to -44) and has no data in 58 % of cases; `f_pos` always
has data. (c) T2 passes 71-100 % of unselected strategies that have data: it filters almost nothing.
(d) T1 oos1 is circular for step-8 survivors, selected on oos1 excess. (e) Move no threshold before a
planted-edge population runs the chain; confirm (a) with unselected draws on a falling and a rising build window.

## Evidence
| population | result |
|---|---|
| NIKKEI225 H1 aroonLong, `Test_..._mc1b`, survivors | 10,000 → 17 (8) → 9 (10) → 9 (12) → 0 (14): all 9 fail «T1 build» |
| same 9 | `t1.build.f_pos` 0.01-0.51; 5 have no positive build excess, 4 have `ret_med` -0.09 to -1.56 |
| same 9 | `t1.oos1.f_pos` 0.69-0.97, `ret_med` 0.13-0.53 (9/9 pass) |
| NIKKEI `..._mc2`, 50 drawn at random from the 10,000 | T1 build ret_med pass 2 / limbo 2 / fail 17 / no data 29 |
| | T1 build f_pos pass 1 / limbo 2 / fail 47 (median 0.20) |
| | T1 oos1 ret_med>0 pass 17 / fail 14 / no data 19 |
| | T2 `ret_med_aprox` pass 15 / limbo 2 / fail 4 / no data 29; T3 pass 26 / no data 24 (ret_med always 1.0) |
| | only 21 of 50 have positive excess over drift in the build; `t1.build.beta_share` median 1.36 |
| DAX40 M30 momentumL, `..._mc3`, 10 drawn | `beta_share` build negative for all (-0.08 to -1.69) |
| | T1 build pass 6 / limbo 3 / fail 1 (f_pos 0.48-1.0, ret_med 0.61-0.98 in 9); T2 pass 10/10; T1 oos1 pass 3 / fail 4 / no data 3 |
Step 8 selects on oos1, so the build is the segment its survivors were not selected on: there they look like the unselected 50.
