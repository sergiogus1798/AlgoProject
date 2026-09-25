# nulls — is this better than a monkey trading the same market?

One question, asked the same way everywhere it is asked: **how much of this result would a
random trader have got, given the same opportunity set?** A strategy's trades go in, thousands
of imaginary runs on the same bars come out, and each statistic gets an empirical p.

```
config.yaml ─▶ inputs ─▶ calibrate ─▶ model ─▶ simulate ─▶ verdict ─▶ report
 every knob    what it   what SQX     what      the         what there  the
               runs on   charged and  could     numbers     is to       panel
                         how it       have      under a     distrust
                         filled       happened  rung
```

| file | what it does | run it | in → out |
|---|---|---|---|
| `inputs.py` | The knobs, one strategy's trades on one sample, its bars, and where each trade sits on the bar grid | imported | export + feed → trades, bars, indices |
| `calibrate.py` | What SQX charged and which bar price it filled at, measured from the real trades, plus the reconciliation that licenses everything else | imported | trades + bars → point value, cost, fill |
| `barrier.py` | The triple-barrier exit: stop, target and time limit, vectorised over thousands of runs at once | imported | entries + levels → exit bar, exit price |
| `kernel.py` | The null runs priced and measured in one compiled numba pass, and the first-touch barrier scan that stops at the first touch; checked against the numpy definitions to 1e-12 | imported | draws + bars → five statistics per run |
| `model.py` | The ladder of nulls — what each rung holds fixed and what it hands to chance | imported | located trades → entries, holds, sizes |
| `stats.py` | What a run is worth, for the real one and for thousands at once, each with its good side | imported | P/L matrix → statistics |
| `simulate.py` | The real run and its null runs, priced identically, in batches | imported | trades + bars + rung → statistics |
| `verdict.py` | The empirical p, the attribution across the ladder, and every reason to distrust them | imported | statistics → p, channels, warnings |
| `filter.py` | The random-filter benchmark: a filter against dropping the same share of trades at random | imported | two trade lists → p |
| `one.py` | **One strategy against its monkeys, readable**: where it landed among them, where its edge came from, and the distribution drawn in text | `python3 -m nulls.one --project XAUUSD --databank MC_Trades --feed XAUUSD_DukasM1_Infinox --strategy "Strategy 1.10.80"` | one strategy → three readings |
| `report.py` | Every strategy of one export through every rung | `python3 -m nulls.report --project XAUUSD --databank MC_Trades --feed XAUUSD_DukasM1_Infinox` | export → `nulls.csv` |
| `verify.py` | The two checks that must pass before a p is read | `python3 -m nulls.verify --project XAUUSD --databank MC_Trades --feed XAUUSD_DukasM1_Infinox --strategy "Strategy 1.10.80"` | one strategy → three checks |

Manual page, in Spanish, for whoever runs it: `docs/manual/26-nulos.md`.

## Why this is a top-level module and not part of a study

Because `tasks/` and `pipeline/` both call it. The gate over a whole population (P1) lives in
`tasks/`, and the per-mother refusal inside the pipeline (P2) is a `must:` row in
`pipeline/recipe.yaml`. A module under `strategies/` that `pipeline/` had to import would point
the arrow the wrong way.

It is **not** in `core/`: that folder reads and drives SQX and does not analyse, with one
declared carve-out. This analyses.

## The three things this module exists to get right

**Whatever a rung holds fixed, it gives to the null.** A null does not measure edge, it
attributes it. Match everything and the null is the strategy itself — p is 0.5 and nothing was
measured. Match nothing and the null is a monkey with the same opportunity set. The gap between
two consecutive rungs is what that one channel was worth, which is why `model.RANDOMISES` is a
table and not a comment.

**The statistic moves the verdict more than the null does.** 🔬 Measured 2026-09-22 over 757
XAUUSD strategies from one simulation: **51.0 %** beat the null on `sharpe` and **21.5 %** on
`net`. `sharpe` is scale-free, so it divides out exactly what separates a real trade from a
random one — the real ones are **36 % less volatile** (551 $ against 720 $ per trade, skew +0.54
against −0.77, kurtosis 6.8 against 27.1). Being calmer than chance is an edge, and `sharpe`
rewards it while `net` does not. The report therefore prints every statistic and picks none.

**A p that has not reconciled is decoration.** `calibrate.convention()` prices the *real* trades
from the bars and compares against the P/L SQX reported, because a null run is priced by the same
two lines. 🔬 On this corpus `open-open` reconciles at **0.999985** and the runner-up at 0.9629 —
100 % of reported entry and exit prices are the open of their own bar. The fill is measured per
strategy, never assumed, and `verdict.distrust()` says so out loud when it fails.

## The filter benchmark is the same question asked of a rule

`filter.py` does not place any trade. It takes the trades of a strategy **without** one condition
and the trades of the same strategy **with** it, and asks whether the condition beat removing the
same number of trades at random — the cheap half of the ablation test (`D1` of
`docs/encargos/12-tests-estructurales.md`), which needs no SQX run at all. The statistics are per
trade, never total profit: a filter changes the trade count, and totals always flatter whichever
version traded more.

Its input today is a pair of exports that differ by a parameter hardened far enough to act as a
filter. The pair that would answer the question properly — the same strategy with a condition
replaced by TRUE — needs the strategy's logic edited, which is that encargo.

## What is deliberately not handled

- **Random placements may overlap**, where real trades never do. At this corpus's occupancy —
  7.4 % of bars held — that is rare, and dropping the overlaps would change `n` and make the
  statistic incomparable to the real run.
- **The trade count is never randomised.** Varying it changes `n`, and with it the sampling
  distribution of every statistic. `crossmarket/POSSIBLE_IMPROVEMENTS.md` §1 lists the same gap.
- **A matched size is the real trade's own size**, so it carries the ATR of the *real* entry and
  leaks a little of when the strategy chose to enter. Re-deriving it as `c / ATR(random entry)`
  needs the ATR period the strategy actually used, which is in its `.sqx` and is not fitted here:
  🔬 `CV(Size × ATR)` falls from 0.38 to 0.12 at ATR(50) but never to 0, so the family is
  identified and the parameters are not.
- **`barrier.intrabar` cannot be calibrated on a corpus with no barriers.** It ships as
  `pessimistic` and `verify.py` proves the scan is *correct*, not that the convention is SQX's.
  The day a strategy carries a stop and a target, calibrating it against SQX comes first.

## Known defects, measured and not yet fixed

Owner's decisions of 2026-09-25, not yet implemented: a null run's drawdown is read **in exit
order**; its swap follows **its own drawn hold** (for gold and indices a percentage of the notional
per night, with the asset's weekday multiplier); random entries are **restricted to the hours the
strategy trades**; and the test stays **per strategy**, with no population-wide null.

- 🔬 **A null run's drawdown is accumulated in the real trades' order, not its own.**
  `kernel.runs()` accumulates each run's P/L in trade-index order, but the entries were drawn
  at random, so `dd` and `retdd` read a shuffled sequence and lose the market's
  clustering. On one strategy of `XAUUSD/MC_Trades` (632 trades, 2026-09-25), sorting each run
  by exit bar raised the null's median drawdown from 27,442 to 29,038 and moved `p_dd` from
  0.018 to 0.0084. `net`, `sharpe` and `pf` do not depend on order.
- 🤔 **The cost follows the trade, not its drawn holding time.** `calibrate.charged()` folds swap
  into each trade's cost, and the rungs that redraw the hold keep the old trade's swap.
- 🔬 **`chunk` is a speed knob as well as a memory knob, and it should be set in trades, not
  runs.** Swept 2026-09-25 on an idle machine, one pinned core, 2,500 draws, three strategies
  (255 / 373 / 1,119 trades), every rung (`AlgoData/reports/perf-chunk-2026-09-25/`): the fastest
  block holds **~130–220 k trade valuations** (10–17 MB of temporaries), about 28–30 ns per
  trade. That is `chunk: 500` for 255–373 trades and 200 for 1,119. At 2,500 it is 1.5–2.2x
  slower; below 50 the Python overhead per block shows. The shipped 500 is within 0–13 % of
  the best on all three. An earlier single reading (36 ns at 50, 105 at 500) was taken while
  another run held 12 cores and is not representative of an idle machine; it suggests that
  under shared-L3 load the optimum moves smaller, which is untested. For `timing` and
  `timing_sizing` the draws are identical at any chunk; for the two rungs that draw holds and
  entries per block, changing it changes the stream.
- 🔬 **Direction is not modelled**: P/L is `value × size × (exit − entry)`, long only. The whole
  XAUUSD export is `Type = Buy`; a short strategy would be priced with the wrong sign.

## Before reading any number from it

```bash
python3 -m nulls.verify --project XAUUSD --databank MC_Trades \
    --feed XAUUSD_DukasM1_Infinox --strategy "Strategy 1.10.80"
```

Three checks, and all three have to pass: the fill reconciles above 0.99; the vectorised barrier
scan agrees with an explicit loop on every trade; and null runs judged against other null runs
produce **uniform** p-values. The third is the one that catches a sampling bug — an unreachable
edge of the window, a reused generator — and it catches it before a real strategy is looked at.
