# engines/nulls — the null engine: what a random trader with the same opportunity set gets

Two families of null models live here, and they are different on purpose:

- **The ladder** (`model.py`, `simulate.py`, `kernel.py`, `barrier.py`): one strategy's own
  trades re-placed on its own bars, rung by rung, each rung handing one more channel to chance.
  The monkey study, the gate, crossTF and entryQuality read it.
- **Placement** (`placement/`): the trades re-laid on *another* market's bars — shuffled,
  resampled, fitted or shifted by calendar. The cross-market study reads it.

Since 2026-10-13 the four rungs of the ladder and of `windowed` read one random stream per strategy, so a gap between rungs is the rung's (`knowhow/research/rungs-share-random-entries.md`).

Both price with `engines/market/calibrate.py`: one ATR, one point value, one set of fill
conventions. Until 2026-09-25 each family carried its own copy. The two model registries were
not merged: they answer different questions and merging them would move every p.

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Names what the package is; holds no code | — | — |
| `inputs.py` | The knobs — `config()` draws a fresh 32-bit `nulls.seed` root from OS entropy when it is `null` (the default), and keeps an explicit one; `seeded()` turns a command's `--seed` into that override — the markets an export holds, the trades of one sample and market (read filtered; an export of several markets refuses without its feed), the bars, and where each trade sits on the bar grid | imported | export + feed → trades, bars, indices |
| `barrier.py` | The triple-barrier exit: stop, target and time limit, vectorised over thousands of runs at once | imported | entries → exit bar, exit price |
| `kernel.py` | The null runs priced and measured in one compiled numba pass — `ladder` places each trade from its uniform as it prices it, and exits are ordered by a stable bucket count, not a sort (encargo 66 §3.3, `tests/test_perf66_ladder.py`) — and the first-touch barrier scan that stops at the first touch; checked against the numpy definitions to 1e-12 | imported | draws + bars → five statistics per run |
| `model.py` | The ladder of nulls — what each rung holds fixed and what it hands to chance | imported | located trades → entries (or, `placed=False`, their uniforms), holds, sizes |
| `stats.py` | What a run is worth, for the real one and for thousands at once, each with its good side | imported | P/L matrix → statistics |
| `simulate.py` | The real run and its null runs, priced identically, in batches — the batches on threads when not inside a fanout worker, same numbers | imported | trades + bars + rung → statistics |
| `verdict.py` | The empirical p, the attribution across the ladder, and every reason to distrust them | imported | statistics → p, channels, warnings |
| `windowed.py` | The gate's monkey (level 3c): every trade re-entered at a uniform bar of the calendar window it opened in AND of the clock hour it opened at, sized `c / ATR` at the drawn bar and priced by `engines.market.reprice` at the declared costs — spread and slippage charged, which the ladder never does; `z()` is the real run among its monkeys in their standard deviations | imported | located trades + bars + costs → mean P/L per trade of every monkey |
| `lookup.py` | The windowed monkey as a table (encargo 66 §3.2, §3.9): `layout()` lists once every trade a draw can produce — an eligible bar of a (window, hour, side) at one clipped hold, shared by all the trades of that window and hour — `windowed.priced()` prices them, and `means()` reads `draws` monkeys off it with PCG64 in the compiled loop: the vector `draw()` + `price()` gave, bit for bit (`tests/test_perf66_kernel.py`) | imported, through `windowed.means` | located trades + priced table + generator → one mean per monkey |
| `pcg.py` | numpy's PCG64 inside numba: `load()` / `store()` read and write a `Generator`'s state, `step` / `word` / `uniform` are `rng.random` — same numbers, same state afterwards. The two kernels that inline it (`lookup._fill`, `permuted._shuffled`) are not `cache=True`: numba does not see a change to `pcg.py`; each is compiled once in the parent (`lookup.warm()`, `resample.warm()`) before a fork | imported | generator state → the draws numpy would give |
| `footprint.py` | A mother's footprint at random entries, same clock hours: the MEAN daily P&L (and its Monte Carlo error) of `draws` hours-null traders priced by the repricer; shared by step 20's benchmark (`studies/closing/blindJoint`) and the oos2 reading (`studies/optimisation/oos2Reading`) | imported | trades + bars + costs → daily series |
| `config.yaml` | The engine's knobs: draws, rungs, barriers, statistics, the p floor | edited, or `--set section.key=value` through the study | — |
| `placement/` | The cross-market placement models | imported | envelope → entries, holds |


Manual page, in Spanish, for whoever runs it: `docs/manual/06-lecturas.pdf` (cap. 26-nulos).

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

## The windowed monkey is a third family, and it leaves the ladder alone

`windowed.py` answers the gate's question (encargo 44, level 3c) and shares only the rung names
with the ladder. Three differences, each on purpose:

- **Where a draw lands**: inside the calendar window the real trade opened in (the gate's
  `drift.window`, R3's own), not anywhere in the sample — so it measures the entry inside its
  regime, not how long the strategy sat in the good years. The exit may cross the window; it never
  leaves the sample.
- **Which hours** (2026-10-12): the monkey of a trade that entered at 15:00 (the feed's clock, the
  hour of the entry bar's open) enters at 15:00 too, so every monkey has the strategy's own count per
  hour of day, uniform over the eligible bars of that hour in the trade's window and inside the
  feed's session (`grid(week_mask=)`; None = the bars of the file, already the session). Direction,
  hold, sizing and costs are untouched. It replaces the uniform draw in the gate; there is no flag.
  On USATEC H1 ruptura (169 alive) it moved the `z_mono >= 1.65` count from 65 to 98.
- **What it is sized with**: `atr_sized()` at the drawn bar, with the ATR known at that bar's open
  (the previous bar's). The rungs that strip the sizing use the strategy's mean lots.
- **What it is charged**: `reprice.pnl` from raw bar opens at `reprice.costs(feed, segment)`, so
  every draw pays spread, slippage, swap and commission. The ladder charges `calibrate.charged`,
  which holds swap and commission only (`knowhow/research/monkey-reprice-audit.md`).

Its random numbers come from the generator the caller hands it and from nothing else: `BLOCK`
only cuts the pricing into pieces, and `tests/test_gate_mono.py` proves a different block draws the
same monkeys. 🔬 2026-10-06, USA500 H1, one core: 60 ns per trade valuation — 0.24 s for a strategy
of 199 oos1 trades, four rungs, 5,000 draws; about 10 MB over the process's own memory.

## What is deliberately not handled

- **Random placements may overlap**, where real trades never do. At this corpus's occupancy —
  7.4 % of bars held — that is rare, and dropping the overlaps would change `n` and make the
  statistic incomparable to the real run.
- **The trade count is never randomised.** Varying it changes `n`, and with it the sampling
  distribution of every statistic. The cross-market study's `POSSIBLE_IMPROVEMENTS.md` (file gone, 2026-10-11) listed the same gap.
- **A matched size is the real trade's own size**, so it carries the ATR of the *real* entry and
  leaks a little of when the strategy chose to enter. Re-deriving it as `c / ATR(random entry)`
  needs the ATR period the strategy actually used, which is in its `.sqx` and is not fitted here:
  🔬 `CV(Size × ATR)` falls from 0.38 to 0.12 at ATR(50) but never to 0, so the family is
  identified and the parameters are not.

## Known defects, measured and not yet fixed

Owner's decisions of 2026-09-25: a null run's drawdown is read **in exit
order** (done, below); its swap follows **its own drawn hold** (for gold and indices a percentage of the notional
per night, with the asset's weekday multiplier; not yet); random entries are **restricted to the hours the
strategy trades** (**implemented 2026-10-12 in the gate's monkey only**, `windowed.draw`: encargo 65 §5.0; the ladder, placement and `falsePositives` still draw uniformly); and the test stays **per strategy**, with no population-wide null.

- 🔬 **A null run's drawdown is read in exit order** (fixed 2026-10-04, in `kernel.runs()`
  (and in the placement kernel, deleted 2026-10-13); the peak also starts at the starting balance, 0 cumulative P/L, so
  a run that opens with a loss counts it). Before, it accumulated each run's P/L in trade-index
  order, so `dd` and `retdd` read a shuffled sequence and lost the market's
  clustering; stored `dd`/`retdd` p-values from before are stale. On one strategy of `XAUUSD/MC_Trades` (632 trades, 2026-09-25), sorting each run
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
- 🔬 **Direction is not modelled, but a pure-short strategy still prices right**: P/L is
  `value × size × (exit − entry)` and `calibrate.point_value` is a fitted slope, so an all-short
  strategy gets a negative value (measured −100.18). Only a strategy mixing both sides would
  break, which rule 13 forbids.

## Before reading any number from it

```bash
python3 -m studies.readings.monkey.verify --project XAUUSD --databank Results \
    --feed XAUUSD_M1 --strategy "Strategy 1.17.44"
```

Three checks, and all three have to pass: the fill reconciles above 0.99; the vectorised barrier
scan agrees with an explicit loop on every trade; and null runs judged against other null runs
produce **uniform** p-values. The third is the one that catches a sampling bug — an unreachable
edge of the window, a reused generator — and it catches it before a real strategy is looked at.
