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
| `model.py` | The ladder of nulls — what each rung holds fixed and what it hands to chance | imported | located trades → entries, holds, sizes |
| `stats.py` | What a run is worth, for the real one and for thousands at once, each with its good side | imported | P/L matrix → statistics |
| `simulate.py` | The real run and its null runs, priced identically, in batches | imported | trades + bars + rung → statistics |
| `verdict.py` | The empirical p, the attribution across the ladder, and every reason to distrust them | imported | statistics → p, channels, warnings |
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

## Before reading any number from it

```bash
python3 -m nulls.verify --project XAUUSD --databank MC_Trades \
    --feed XAUUSD_DukasM1_Infinox --strategy "Strategy 1.10.80"
```

Three checks, and all three have to pass: the fill reconciles above 0.99; the vectorised barrier
scan agrees with an explicit loop on every trade; and null runs judged against other null runs
produce **uniform** p-values. The third is the one that catches a sampling bug — an unreachable
edge of the window, a reused generator — and it catches it before a real strategy is looked at.
