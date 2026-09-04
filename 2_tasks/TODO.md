# 2_tasks — next module: improvement

Not started. This file is the brief; everything it needs already exists.

---

## What it answers

The panel says *"Sharpe Ratio (IS) and Profit factor (OOS) move together, ρ = +0.223"*. That does not
tell the owner what to do. **Improvement** does:

```
population                     n = 10,000   median PF (OOS) = 0.950   PF > 1 = 41%
Sharpe Ratio (IS) top 20%      n =  2,034   median PF (OOS) = 0.990   PF > 1 = 47%
                                            improvement +0.040 median, +6 pp hit rate
                                            cost: 7,966 strategies discarded
```

That is the generation decision, stated in the terms it is actually made in: *for XAUUSD, filtering
on IS Sharpe raises the out-of-sample hit rate by 6 points and leaves 2,034 candidates.*

The two numbers in that block are already computed — the panel's header line shows the filtered and
unfiltered median. What is missing is doing it **systematically**, over many candidate filters, with
the two safeguards below.

## What it must add that the panel does not have

### 1. Confidence intervals

With n = 310 survivors a median out-of-sample outcome moves a long way on resampling. Without a band
around it, an improvement of +0.17 cannot be told apart from noise.

Use a **bootstrap**: resample the survivors with replacement 2,000 times, take the 2.5th and 97.5th
percentiles of the statistic. It makes no distributional assumption, which matters because these
metrics are heavy-tailed. `numpy.random.default_rng` with a fixed seed, so the report is reproducible.

The interval that matters is the one on the **difference** (filtered minus baseline), not two separate
intervals — two overlapping intervals do not mean the difference is insignificant.

### 2. Correction for the search

Sweeping 40 candidate filters and reporting the best one is the multiple-testing trap that
`2_tasks/CLAUDE.md` warns about, except the searcher is now the analyst. Apply Benjamini-Hochberg
across the whole sweep exactly as `analysis/correlations.py:discoveries` already does, and **report
how many filters were tried** in the output. A result that does not say what the search space was is
not a result.

## Suggested shape

```
2_tasks/analysis/improvement.py    the maths
2_tasks/reports/filters.py         entry point, writes improvement.md + a figure
```

`improvement.py` wants roughly:

| function | what it returns |
|---|---|
| `survivors(columns, clause)` | Boolean mask for one clause, evaluated against the full population |
| `outcome(columns, mask, target)` | median, mean, hit rate (share above a break-even), quartiles |
| `bootstrap(columns, mask, target, draws)` | 95% interval on the difference against the baseline |
| `sweep(columns, clauses, target)` | one row per candidate filter, sorted by improvement, BH-marked |

Candidate filters to sweep by default: **every in-sample metric at the 10/20/30/50% top and bottom
cut.** 21 metrics × 5 cuts × 2 directions = 210 tests, which is exactly why the correction is not
optional. Take the metrics from `metrics.measured(columns, metrics.IS)` so nothing is hard-coded.

## Things to decide with the owner before writing it

- **What "good" means out of sample.** Median profit factor? Share above PF 1.0? Share above some
  higher bar that survives costs? The hit rate needs a break-even and nobody has picked one.
- **Whether combinations are swept too.** Two clauses ANDed is 210² pairs. That is a different
  problem and needs a different correction; single clauses first.
- **Whether the survivor count has a floor.** A filter leaving 12 strategies can show a huge
  improvement and mean nothing. A minimum n — 100? 200? — should be a stated rule, not a judgement
  call made per report.

## Beyond that

The panel and improvement together only measure XAUUSD/OOS. The question the owner is actually
asking is *which filters for which asset*, so the next step after improvement is running both across
every project's databank and comparing. That comparison is where a filter that works on gold and
fails on indices becomes visible — and it is also where a filter that "works" everywhere by 2 points
should start looking like an artefact of the metric rather than an edge.
