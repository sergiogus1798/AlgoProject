---
q: monkey random-entry null what it measures, studies/readings/monkey/ statistic choice sharpe net dd pf retdd, sizing channel ATR, monkey bar set by cost not drift, MinTRL vs monkey, PSR approximation tail, nulls seed PYTHONHASHSEED, PSR benchmark 0 wrong null OPEN.md #71 crossmarket monteCarlo mcRetest, footprint noise bug total variance, random trader only vs OOS never vs build IS owner 2026-09-29
tag: 🔬  date: 2026-09-29  see: research/hardest-null, research/entry-vs-chance, research/post-selection-bias, research/mintrl-explosion-is-correct
---
# A monkey verdict depends on the statistic far more than on the null: report all five
`engines/nulls/config.yaml` lists five statistics and chooses none; never report one. Sharpe is scale-invariant, so
being calmer than chance counts as edge under `sharpe` but not under `net`. Beating the monkey is a lower bar
than beating zero (its mean is cost-negative). Use fill `open-open` (reconciled). Normal approximation (PSR/MinTRL)
is fine for a gate at p≈0.05, not for the extreme tail after multiplicity — BH on the short list uses the simulation.

**2026-09-29 (OPEN.md #71):** `benchmark=0` was the wrong null; `footprint()` now prices a same-footprint random trader against the market's own bar-to-bar noise (law of total variance), shared by `crossmarket`, `monteCarlo` and `mcRetest` — see Evidence.
**Same day, second rule (owner):** the random trader may only be read on OOS or on an additional market, never the main market's build — it already selected the strategy. Enforced in `monteCarlo`, `mcRetest`, `readings/monkey` (IST refused on the own market); `crossmarket`, `gate.monkey` already were. Audit below Evidence.

## Evidence

**Footprint fix, 🔬 2026-09-29.** mcRetest, `Test_USDJPY_donchianUpperCrossUp_M30` (real ingest, read-only, session algoproject-36's data): before, benchmark +2.0 to +2.2/strategy, `p_positive` 1.0→0.0 for all five checked; after, benchmark +0.004 to +0.006, `p_positive` back to 1.0. `analytic_sharpe`'s own `psr` stays ≈1.0 either side — a separate scale mismatch (summed, not per-trade, `returns`), still open.
crossmarket, real USDJPY M30 bars 2018–2022 through the study's own `backtest.setting()`/`exposure.run()` (no XAUUSD trade harvest on disk to run the real pipeline on): before, benchmark **-11.18** (mu_m≈+2e-6/bar, near-zero drift, so a near-constant series driven to an extreme Sharpe by holding-time alone), `psr=1.000000`; after (sigma_m≈7.1e-4/bar), benchmark **-0.070**, `psr=0.556` against an observed Sharpe of -0.062 — plausible instead of saturated.

`studies/readings/monkey/` on `raw/XAUUSD/MC_Trades/2026-09-19, deleted 2026-09-25/`: 757 strategies, 960,705 trades, sample `OOS1` (2018–2022, 320,423 trades),
2,500 draws per rung, fill `open-open` reconciled (median 0.999983, min 0.99945). XAUUSD costs PROVISIONAL.
- ⚠️ Not: close-close fill — 4–13 % lost correlation moved percentages by 10–26 pp with no alarm.
- Sizing channel of *return* empty: median `corr(Size, P/L per unit)` +0.001; |corr| > 0.05 in 10.7 % vs ~7 % by chance (n≈1,270).
  Does not rule out the *variance* channel (vol-normalising raises Sharpe without the mean) — only rung `timing_sizing` measures it.
- Sizing is pure ATR, no equity compounding: `CV(Size × ATR)` 0.384 raw → 0.200 ATR(14) → 0.119 ATR(50); dividing by `Balance` worsens it (0.220 / 0.157).
  ATR period lives in the `.sqx`, not fitted. → no sequential dependence, embarrassingly parallel: 757 × 4 rungs × 2,500 draws in 2m37s.
- Monkey bar: occupancy 7.4 % (366 trades × 12 M30 bars / 59,112) captures ~2,867 $ of gold's rise (1307→1822), pays ~7,756 $ cost;
  mean negative in 100 % of 757 (median −4,698 $).

Pass rate, one simulation, rung `timing`, p < 0.05: `dd` 84.5 % · `sharpe` 77.4 % · `retdd` 76.9 % · `pf` 55.2 % · `net` **39.5 %**.

Per-trade, fill open-open, 120 strategies: std 491 $ strategy vs 661 $ monkey (+36 %); skew +0.53 vs −0.78; kurtosis 6.4 vs 27.0.

MinTRL on SQX P/L passes 202/757 (26.7 %). Crossed with the monkey:

| monkey statistic | pass MinTRL, not monkey | pass monkey, not MinTRL |
|---|---|---|
| `sharpe` | 0 | 384 |
| `retdd` | 0 | 380 |
| `pf` | 5 | 221 |
| `dd` | 15 | 453 |
| `net` | 48 | 145 |

`sharpe`: MinTRL ⊂ monkey; null spread × √n = 1.006 (iid), `psr(returns, benchmark=monkey_mean)` reproduces the simulation (p corr 0.9956).
`net`: the tests cross both ways (different things); screening MinTRL before the monkey drops 48 the monkey passes on profit.

Seed: fixed 2026-09-25. Each block draws from `SeedSequence([seed, blake2b(strategy), fixed rung id, block])` (`engines/nulls/simulate.py`).
Not: `default_rng([seed, abs(hash(rung)) % 2**32])` — `hash()` of a str is per-process randomised (3 runs: 810825080, 1328569471, 751024716),
so `nulls.seed` fixed nothing; two `studies.screening.gate.report` runs gave 227 vs 229 survivors (identical with `PYTHONHASHSEED=0`).
p-values stored before the fix came from other monkeys; vs new ones over 15,140 p, difference within Monte Carlo error.

**OOS-only audit, 2026-09-29 (owner).** `monteCarlo.run._family_e()` restricts to
`stream.restrict(source, stream.samples(source)["OOS"])` before `footprint()`/`psr()` (was: whole
IS+OOS); < `confidence.MEAN_PROVISIONAL` OOS trades → NaN + `data`/`oos_thin` veto, never IS.
`mcRetest.measure.originals.read()` keeps `sample == "OOS"` only from the harvest (was: both
sides); < `run.MIN_OOS_TRADES` (5) → printed warning, still computed. KAT:
`tests/test_montecarlo_oos.py`. `crossmarket` already compliant: additional markets run their
whole window (never selected on); the main market's full backtest shows only as "referencia",
excluded from the verdict; the OOS reading is `orchestrate/stretch.py`'s `oos_tab`.
`gate.monkey` already filters `sample == "OOS"`. `monkey.report --sample` defaults `OOS1`; not a
hard refusal — an additional market legitimately reads `IST` too (never selected on either
sample), so its help text spells out the distinction. `crossTF` reads a retest task's own
window, never a build task's — no mixing found.
