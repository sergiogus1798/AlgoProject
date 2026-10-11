---
q: How many mothers do steps 17, 18, 18.5 and 19 stop, and what does each step cost in time?
kw: step 17 wfc limbo p_nivel never passes; step 18 cscv pbo 0.82 passes; step 18.5 marketSurfaces orden neutro; step 19 wfm mediana_exceso; unfiltered smoke mothers pass; reapertura 577 s; 16.5 variants time per mother; wf1 wf2 wf3 wf4s
tag: 🔬  date: 2026-10-11  see: research/step8-gate-measured-on-six-populations, pipeline/variant-batch-refused-on-negative-zero, pipeline/bar-library-behind-sqx-kills-the-oos2-reading
---
# Steps 18 and 18.5 stopped none of 8 mothers, 3 of them unfiltered; step 17 passed none; step 19 passed all 3 unfiltered
Measures, not a change (thresholds are the owner's; 8 mothers is a small sample). 17 WFC: 0 pasa, 7 limbo,
1 no pasa. 18 CSCV: 8 pasa (PBO up to 0.82 passes, never over its null's p95). 18.5: 8 pasa, order always
«neutro». 19 WFM: 6 pasa, 2 limbo — and the 3 unfiltered `--smoke` mothers pass all of 18, 18.5 and 19.
Cost: 16.5 = 260-380 s a mother; 17, 18, 18.5 under 1 min each; 19 = 16-25 min, ~10 of them SQX's reopen.

## Evidence
Four runs of 10,000 Simple Strategy longs, 30 min build, dev draw of 3 (2026-10-10/11): USA500 H1 trend
(2 mothers reached the tail), DAX40 H1 reversion (1), NIKKEI225 M30 volatility (2) under the real rules,
and XAUUSD H1 breakout under `--smoke` (3 mothers no rule filtered — the nearest thing to a null the tail
has seen; under the real rules that run kept 1 of 10,000 at step 8 and 0 at step 10).

| step | pasa | limbo | no pasa | of the 3 unfiltered |
|---|---|---|---|---|
| 17 WFC (`wfc.c1.estado`) | 0 | 7 | 1 | 3 limbo |
| 18 CSCV | 8 | 0 | 0 | 3 pasa |
| 18.5 market surfaces | 8 | 0 | 0 | 3 pasa (orden neutro) |
| 19 WFM | 6 | 2 | 0 | 3 pasa |

- 17: `p_nivel` ranged 0.07-0.80; the top's out-of-sample median was positive in 7 of 8 and never
  significant at `wfc.level_alpha` 0.05. As written the step is a limbo stamp, not a separator.
- 18: PBO 0.28-0.82, never over its null's p95 (`pbo_sobre_p95` = 0 in all 8); `p_perdida` 0.002-0.32.
  A PBO of 0.73 and of 0.82 pass. 18.5: `orden.rho` −0.06..+0.18, always «neutro»; `prima.bajo_p5` = 0 in all.
- 19: the two limbos are filtered mothers (`l1.mediana_exceso` −4,153 and −5,730, `p_menos` 0.15 and
  0.067); the three unfiltered gold longs pass with +143..+1,563 and `p_mas` 0.29-0.45 (not significant):
  the «mediana > 0» rule passes what its own null does not distinguish from noise.
- Facts: no NaN in any step of any run (198 wfc, 108 cscv, ~275 marketSurfaces, ~244 wfm facts a mother).

Cost (s): 16.5 = 260-380 per mother of 1,004 variants (export of the variants' trades ≥ their execution);
17 = 2-4 per mother; 18 = 9-11; 18.5 = 16-46 without oos2 and 30-60 with it; 19 = 980-1,510 a run, of
which 574-594 is `liverun`'s deliberate SQX reopen (`AGED`) and only 196-343 the WFM for 1-2 mothers.
Whole run 6→19: 132-164 min; step 8's studies over 10,000 are 48-58 min, more than the build (40).

`AlgoData/autopilot/Test_{USA500_H1_tendencia_wf1,DAX40_H1_reversion_wf2,NIKKEI225_M30_volatilidad_wf3,XAUUSD_H1_ruptura_wf4,XAUUSD_H1_ruptura_wf4s}/*/` — `resumen.md`, `tiempos.md`, `paso-<N>/{verdict.csv,hechos.parquet}`; the smoke run's 17-19 are not judged (no `paso-17..19`): its facts are in `AlgoData/strategyPermutations/<P>/<mother>/estudios/*.json` and `AlgoData/reports/<P>/WFM/2026-10-11/wfm/verdict.csv`.
