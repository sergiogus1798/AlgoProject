# walkForwardMatrix — where the design had real alternatives

## 1. The interval over cells is a floor, not a measure

`correlation.pooled` bootstraps cells because steps are clearly wrong. But cells are not
exchangeable either: all 30 re-split the same 10 to 14 years, so resampling them still treats
correlated things as independent. The interval it reports is **narrower than the truth**, by an
unknown amount.

Two ways to do better, neither taken: a block bootstrap over calendar time rather than over cells,
which is defensible but needs a block length nobody has measured here; or simply reporting the
per-cell correlations as a distribution and refusing to produce a single interval at all. The second
is more honest and much less useful, which is the whole tension.

What makes the current verdicts survivable is that `4.33.46` is negative in **28 of 30 cells** and
on all four metrics. That is robustness of sign, not a confidence interval, and it is the thing to
lean on.

## 2. Two strategies is not a population

The `WFM` export holds two. `WFM_Stability` on the same date holds 1.5 GB and has not been read yet
— the obvious next input, and the one that would say whether `perverse` is a property of
`Strategy 4.33.46` or of how these strategies are built. Until then no sentence here generalises.

## 3. The drift number counts changes, not distance to the plateau

`share_changed` says 70–78 % of parameters move every step. But a parameter moving one level inside
a wide plateau and one jumping across the range are the same event to that statistic. `move`
normalises by each parameter's spread and partly addresses it, and neither knows anything about the
shape of the surface the optimiser chose from — because SQX did not store it.

The variant study is what closes this: with 5,000 designed tuples the plateau is known, and drift
can be expressed as "how far out of the plateau did it jump". Here it cannot.

## 4. `perverse` has an innocent explanation this module cannot rule out

A negative walk-forward correlation is what you would also see if the market simply alternated
between two regimes at roughly the step length: optimise on regime A, run on regime B, repeatedly.
That is a property of the calendar, not of the strategy or the procedure.

Distinguishing them needs the step-level results lined up against a regime classification, or the
same measurement on a strategy known to be robust as a control. Neither exists yet. **The verdict
is about the procedure as run on this history, and the report should not be quoted as more.**

## 5. Nothing reads the trades

`trades/` and `check.csv` come out of the same export and are ignored here. `check.csv` reconciles
assigned against stored trade counts per step and is a ready-made integrity gate — cheap to wire in,
and it would catch a mis-cut export before any correlation is computed.
