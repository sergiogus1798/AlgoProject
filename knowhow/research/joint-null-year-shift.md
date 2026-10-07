---
q: Why must a cross-market null share one shift across markets, and how do I test it?
kw: joint null, cross-market null, year shift, week shift, 53 weeks wrap, z_conj sd 2.17, z inflated, zero-fill missing market-year, NaN vs 0, paso 10 travel, no-edge battery, config hash stale, gross vs net, judge_on, ATR-conditioned cost in R, placebo not centred, high ATR entries, conditional drift, path-level se, shared path
tag: 🔬  date: 2026-10-07
---
# One seed for all markets makes the null joint; a battery of independent entries cannot tell
Draw ONE shift per cell and run, keyed by the cell's date, never by market. Test it with a battery whose
strategies enter at the SAME stamps in every market: with independent entries, joint and per-market
shifts both read sd(z_conj) ≈ 1.01 (🔬); with coinciding entries, per-market shifts read ≈ 2.17, z inflated ×2 (🔬).
- A year is not a whole number of weeks: weekdays with 53 dates in the year wrap one week later than those
  with 52, so the year-block shift is rigid only away from the wrap (🔬).
- With totals, zero-filling a missing market-year and skipping NaN give the same z_conj; the bug shows only
  in per-market and per-cell z, p and trade counts. Do not validate NaN handling on z_conj (🔬).

## Evidence
- No-edge synthetic population (300 strategies, 11 correlated markets, drift and costs, losing 58.7 R each
  on average): z_conj mean −0.02, sd 1.08, rejection 7.3 % at z ≥ 1.65 and 1.0 % at z ≥ 2.33 — costs cancel
  between the real and the random runs (🔬).
- Real data (📓): ten NIKKEI225 M30 strategies × eleven markets, 2026-10-04 export: mean z_conj +1.72
  (sd 1.70); by window V0 +0.14, V1 +1.63, V2 +0.75. **UNRESOLVED**: era-fitting in the build years or a
  bias on real data (encargo 46, decisión 8). Confirm: same run on a market-shuffled or pre-build control.
- 🤔 Adding a section to a study's `config.yaml` changes its config hash, so the window shows every stored
  result of that study as stale. Seen: `ui/daemon/results/stale.py:79-83` marks stale any result whose hash
  is not a current one; not confirmed that the hash covers the whole file (read `fresh()`).
- `studies/transfer/crossmarket/travel/README.md:73-77` (same shift everywhere, 53/52 wrap), `:61-65` (NaN vs 0).
- `tests/test_crossmarket_travel.py:63-67` (same stamps; "sd of z 2.1" with per-market shifts), `:84-102`
  (centred, sd 1 ± 0.1, nominal rejection), `:226-248` (missing year is NaN, not 0).
- Real run output: `AlgoData/scratch/paso10_travel/2026-10-07/`; `docs/encargos/46-paso-10-otros-mercados-la-logica-viaja.md:12`.
- Gross vs net: cost in R does not cancel against the shifted copies when entries are ATR-conditioned
  (cost / ATR at entry moves with the shift). No-edge population entering on the top third of ATR,
  200 strategies: z_conj on net reads +0.98 (centre should be 0), on gross +0.30 (full), and per window
  V0 −0.56, V1 +0.45, V2 +0.14 on gross (se 0.06). Hence `travel.judge_on: gross`.
- The gross +0.30 is the realised history, not the apparatus (🔬, `scratch/d2/residuo.py`, `synth_vol.py`,
  output `AlgoData/scratch/paso10_travel/2026-10-07-residuo/`). The 200 placebos share ONE path, so se 0.06
  is not the se of a bias: by year the residual is +1.39 R/yr, se 1.40, t = 1.0 (16 years, 8 positive).
  V0 is 2008 alone (−5.8 of −7.8 R; only EURUSD, USDJPY and gold have bars then), V1 is 2014-15 (+21.6 of +23.9 R,
  +18.3 of it on the indices), V2 is 2021 +10.3 against 2020 −5.5.
  - At FIXED lots the pattern stays (full +0.39, V0 −0.45, V1 +0.54, V2 +0.25): it is the price move after
    a high-ATR entry, not the R denominator, which alone is worth −0.10 z (🤔 scaled from the ATR ratio
    1.64 real / 1.27 shifted).
  - Not the shift mechanics: trades per run 3242.5 real / 3242.6 shifted; V0 has 0.01 % of shifted entries
    off the week grid and the largest |z|; by market the sign follows the asset class (USA500 +0.54,
    DJ30 +0.50, UK100 +0.48, DAX +0.40; gold −0.49, EURUSD −0.25), not the share of holes (HK50 0.25:
    +0.27, AUS200 0.18: 0.00).
  - Synthetic, volatility clustering, 200 independent worlds × 10 strategies, production tensor: zero
    conditional mean −0.03 (se 0.04); constant drift −0.39 (se 0.04, the denominator: a long sized on a
    high ATR collects fewer R of drift than its copies — a SHORT reads +0.39 with no edge); drift ∝
    variance +0.18; uniform entries with drift 0.00 (se 0.02). The mean z of one world's population has
    sd 0.5 between worlds: a template's whole population carries a common offset of that size.
  - On gross, short is the exact mirror (|z_long + z_short| < 2e-5): a short placebo discriminates nothing.
  - Consequence: for a template with a fixed state condition the no-edge reference is the placebo that
    keeps that condition, not z = 0: its 95th percentile here is 1.60 full, 1.82 V1, 0.88 V0, 1.36 V2
    (sd of z 0.79, below 1), so z ≥ 1.65 rejects 4.0 % full and 9.5 % in V1.
