---
q: monkey random-entry null what it measures, studies/readings/monkey/ statistic choice sharpe net dd pf retdd, sizing channel ATR, monkey bar set by cost not drift, MinTRL vs monkey, PSR approximation tail, nulls seed reproducible hash PYTHONHASHSEED, PSR benchmark 0 wrong null OPEN.md #71 crossmarket monteCarlo mcRetest
tag: 🔬  date: 2026-09-29  see: research/hardest-null, research/entry-vs-chance, research/post-selection-bias
---
# A monkey verdict depends on the statistic far more than on the null: report all five
`engines/nulls/config.yaml` lists five statistics and chooses none; never report one. Sharpe is scale-invariant, so
being calmer than chance counts as edge under `sharpe` but not under `net`. Beating the monkey is a lower bar
than beating zero (its mean is cost-negative). Use fill `open-open` (reconciled). Normal approximation (PSR/MinTRL)
is fine for a gate at p≈0.05, not for the extreme tail after multiplicity — BH on the short list uses the simulation.

**2026-09-29 (OPEN.md #71):** `benchmark=0` was the wrong null. `crossmarket` and `monteCarlo` now
pass this same monkey mean, closed form (occupancy × drift − cost); `mcRetest` has no bars for it
and stays at 0 (`mcRetest/POSSIBLE_IMPROVEMENTS.md` #10).

## Evidence
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
