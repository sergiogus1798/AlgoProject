# tasks — improvement: BUILT 2026-09-04, and what is still open

Built as `analysis/improvement.py` + `reports/filters.py`, documented in
`docs/manual/02-filtros.md`. The three questions this brief left for the owner were decided on
2026-09-04:

- **What good means out of sample**: the target's own median plus the share above break-even, on
  `Sharpe Ratio (OOS)` and `Ret/DD Ratio (OOS)` by default. Break-even is 1.0 for profit factor and
  0.0 for the rest.
- **Minimum survivors**: 200. Below that a candidate is not judged at all.
- **Combinations**: not swept. Single clauses only.

A 5% cut was added the same day, on the owner's call, because the first sweep found the improvement
still rising at its tightest cut and so could not say where it stopped paying. It can now: on XAUUSD
the first cut buys 22 points of hit rate and going from 10% to 5% buys under 2 more for half the
survivors. The search space is 210 candidates.

**Still open, in the order they are worth doing:**

1. **Combinations**, with the correction that needs.
2. **Across every project's databank**, which is the section at the end of this file.

What follows is the original brief, kept because it explains why the module looks the way it does.

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
`tasks/CLAUDE.md` warns about, except the searcher is now the analyst. Apply Benjamini-Hochberg
across the whole sweep exactly as `analysis/correlations.py:discoveries` already does, and **report
how many filters were tried** in the output. A result that does not say what the search space was is
not a result.

## Suggested shape

```
tasks/analysis/improvement.py    the maths
tasks/reports/filters.py         entry point, writes improvement.md + a figure
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

**Comparing samples is built** — `analysis/replication.py` + `reports/compare.py`, page 3 of the
manual — but it compares databanks *of one project*. It was written for the owner's replication
study: generate again under the recommended filters, then check the promised uplift actually
arrives. Pointing it across projects is a naming and reporting job, not new maths.

The panel and improvement together only measure XAUUSD/OOS. The question the owner is actually
asking is *which filters for which asset*, so the next step after improvement is running both across
every project's databank and comparing. That comparison is where a filter that works on gold and
fails on indices becomes visible — and it is also where a filter that "works" everywhere by 2 points
should start looking like an artefact of the metric rather than an edge.
