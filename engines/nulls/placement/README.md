# engines/nulls/placement — trades re-laid on another market's bars

The null models, and the resampling they are built from. Every module here answers "where else could
these trades have gone": another placement in the sample, another set of holds, another draw of the
same sequence. They take an envelope and produce **instructions** — an entry-index matrix and a hold
matrix, or a set of positions — and never a price, a statistic or a conclusion.

This is the layer the study can be wrong in **without crashing**, which is why it is kept apart from
the execution that runs it: a model can be swapped and the same numbers recomputed under both, which
is the only way to find out whether a conclusion depended on it. `POSSIBLE_IMPROVEMENTS.md` §1 is
about this layer and should be read before changing anything in it.

**Imports from:** nothing outside itself — numpy, pandas and scipy only
**Consumed by:** `studies/transfer/crossmarket` — its `simulate/`, `verdict/` and `contract/`
**Must not contain:** a price, a P&L, a percentile, a threshold, or any wording of a verdict

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Names what the package is; holds no code | — | — |
| `kernel.py` | A batch of random runs priced, measured and drawn as equity in one compiled pass | imported | draws + bars → statistics, curves |
| `trade_models.py` | **How random trades are drawn.** The registry, the Friday truncation every model gets, the re-cut at the next trade, and the two that randomise placement only — `block_shift` and `regime_strata` | imported | envelope → entries, holds |
| `free_models.py` | The free-placement family: the three that re-lay the whole run anywhere in the window | imported | envelope → entries, holds |
| `holdfit.py` | Fits a discrete distribution to the real holds and gaps, and says whether it fits | imported | counts → sampler, goodness |
| `bootstrap.py` | Block-bootstrap resampling, laid out by row blocks, and percentile confidence intervals | imported | a sequence → resampled positions, a CI |

## Adding a placement model — three things, and nothing else

1. Write the function in `trade_models.py` — or in `free_models.py` if it re-lays the whole run —
   with the shared signature, `(held, market, draws, rng, batch)` in and `(entries, holds)` out.
2. Add it to `MODELS`, and add a row to `RANDOMISES` saying **what it randomises**.
3. Name it in `config.yaml` under `nulls.models` (and `sweep.models` if it should be swept).

Nothing else changes: the config drawer picks it up, the panel gains an entry, and
`render/panel.NAMES` is the only other place a reader's name for it lives. `batch` is how many draws
were already produced, and only a model whose randomness must match across markets needs it:
`block_shift` keys its displacement on the calendar rather than on `rng`, and without `batch` every
chunk of the batched loop would redraw the same one.

**The `RANDOMISES` row is not documentation, it is the finding.** A model that randomises more than
one thing cannot attribute a low p-value to any single cause, so the report prints it next to every
p-value it produced.

| key | shown as | randomises | what it adds over the one above |
|---|---|---|---|
| `segment_permute` | Shuffled Sequence | placement, order, clustering and regime | the starting point: the real rhythm, re-laid anywhere in the sample |
| `resampled_holds` | Resampled Sequence | the above, plus which holds occur and time in market | drops the multiset, so total time in market varies between runs |
| `fitted_holds` | Fitted Distributions Sequence | the above, plus the holding times themselves | the holds no longer come from the real ones at all |
| `block_shift` | Calendar Shift | **only** placement, inside the regime block and the weekday-hour slot | not a member of that family: it is the one that changes exactly one thing |
| `regime_strata` | Regime Strata | placement, inside bars of the same ATR quantile and trend sign; frees weekday, hour and clustering | **off by default**, runs only when `nulls.models` lists it. Holds the regime by state rather than by a calendar block of arbitrary length |

**These are two families, not four points on a scale.** The first three lift the whole run and drop
it anywhere in the 22 years, so they change *when*, the *order*, the *calendar* and the *regime* all
at once — a low p under any of them cannot be attributed to any one of the four. `block_shift` moves
each trade separately, by whole weeks, inside its own semester and onto its own weekday and hour, so
the regime, the calendar and the clustering all survive. That is why `nulls.headline` names it and
why the summary table reports its p, whatever order the panel shows them in.

🔬 **`renewal` was retired on 2026-09-15.** It rebuilt the occupancy from scratch, walking the bars
and entering with the empirical hazard, so the trade count was random too. On paper that added
something; measured over 8 (strategy, market) pairs it added **nothing** — the same null width as
`resampled_holds` to within 2% and the same p to within 0.004, every time. Once placement is free
across the whole sample, which decade a run lands in dominates everything else, and the first three
already randomise that identically.

The registry keys are the contract — `config.yaml`, `MODELS` and every docstring share them.

## Why `block_shift` is shaped the way it is

Three properties, each of which was needed, and two of which were found by measuring:

- **Blocks**, because thirteen years of gold are not one regime. A strategy whose trades sit in a
  strong trending stretch would beat a null spread over the whole sample on drift alone.
- **Whole weeks, in the block's own weekday-hour groups**, so entries land on the weekday and hour
  they really used — an eight-bar hold entered late on a Friday spans the weekend gap and one entered
  on a Tuesday does not. `calendar_kept` must read 1.00; when the shift was written in bar space it
  read 0.05.
- **The wrap**, because a strategy's trades span nearly the whole of every block. Placing them end to
  end left one legal position in most blocks and none in nine of twenty-four, and the null then
  reproduced the real run — measured, it returned p ≈ 0.5 for everything.

On top of that, every model's holds are re-cut at the Friday close, because that is an exit rule the
strategies really have (5.4% of all trades in the sampled databank) and it is a rule of the calendar,
which a null can reproduce exactly. `Exit Signal` — 16.6% of trades — is not reproducible without the
`.sqx`, and that is why those strategies are reported as a joint entry-and-exit test.

## Contracts and traps

- **A random run must not overlap itself.** The strategies are single-position — flat to enter — so a
  run holding two at once is not a counterfactual of anything. Two separate defects were found here:
  - 🔬 **The three free models overlapped until 2026-09-15.** `_lay` offset each trade by its **own**
    hold instead of the previous trade's, so **1-7% of the trades of every random run overlapped
    another**, on every (strategy, market) pair measured — against a docstring saying non-overlap
    held by construction. Re-measured at 10,000 draws after the fix, p moved by at most **0.009**
    under `segment_permute`, 0.004 under `resampled_holds`, 0.005 under `fitted_holds`; σ by at most
    2%; `block_shift` was identical to the digit.
  - 🔬 **`block_shift` overlapped until 2026-09-17, and it is the headline model.** 5.38% of Brent's
    random trades and 2.82% of silver's opened before an earlier trade of the same run had closed.
    It moves each block's trades by whole weeks *inside the weekday-hour index*, which is not a rigid
    translation in bar space. **Repaired by cutting, not by dropping**: `cut_at_next()` caps every
    hold at the bar the next trade opens, exactly as the Friday close already caps one. Dropping the
    clashing trade removed 3-5% of every run and traded an exposure bias for a sample-size one.
    `tests/test_models.py` holds the property.
  - 🔬 **`block_shift` still overlaps** by 2.5% on XAGUSD and 1.7% on Brent (Strategy 1.10.80),
    because trades in different weekday-hour groups wrap by different numbers of weeks. Left as it is
    **on purpose** — the owner fixed it as the reference the window sweep is read against — and
    recorded rather than changed.
- **`bootstrap.block_rows` is a deliberate copy** of `engines.resample.draws`'s block bootstrap,
  laid out a few rows at a time: every block start is drawn first, so the draws do not depend on
  how many rows come out together, and a 20,000-trade market no longer holds a 650 MB index matrix.
  Three callers here need it, which under `CODESTYLE.md` rule 5 is not yet "shared"; crossmarket keeps its
  own rather than importing across studies. `simulate/portfolio.py` is the one place that does import
  monteCarlo, for the reordering family it owns.
- **`holdfit.MIN_HOLD` is 1**: a trade that opens and closes on the same bar is not a trade. Both the
  sampler and the goodness-of-fit check read their two moments from `holdfit.moments()`, so they
  cannot disagree about which distribution was fitted.
