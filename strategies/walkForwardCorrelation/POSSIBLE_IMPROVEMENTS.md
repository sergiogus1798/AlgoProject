# walkForwardCorrelation — the choices that had real alternatives

Every section here is a decision that moves the answer and was taken on an argument rather than on
a measurement. Argue with it in writing before changing it in code.

## 1. Weekly periods, not monthly or daily

`config.yaml: cscv.period` is `W`. Daily was never an option: at roughly sixty trades a year a
daily matrix is almost all zeros, and ranking variants by the Sharpe of a mostly-zero series ranks
their luck. Monthly would halve the noise per observation and leave 180 periods over 2008–2022,
which is 18 per block — thin but not absurd.

**What would settle it:** run both and compare the PBO's spread across seeds on the same mother. If
monthly moves the PBO by less than its own sampling error, weekly is free and keeps the resolution.

## 2. The score is a Sharpe, not Ret/DD

Every ranking inside the CSCV uses per-period Sharpe. The protocol's §4a is emphatic that Ret/DD is
biased by window length — total return grows with T and max drawdown with √T — which is exactly why
it is wrong for comparing in-sample against out-of-sample windows of different lengths.

**Inside the CSCV that objection is weaker than it looks**: every partition has five blocks on each
side, so every window is the same length and the bias is constant. Ret/DD would be legitimate here
and is closer to what the owner actually trades on. Sharpe was kept because `trials.deflated` needs
a Sharpe in the same unit as its benchmark, and because one score across the whole module is easier
to defend than two.

## 3. Ten blocks

C(10,5) = 252 partitions. Sixteen blocks gives 12,870 — fifty times the compute for a
third-decimal improvement on a statistic whose null standard deviation is 0.21. Eight gives 70,
which is too few to see the shape of the lambda distribution.

## 4. Neighbours are defined by the levels the design actually fabricated

`rules.coordinates` factorises each parameter's **distinct values present in the grid** rather than
reading the level list out of the design brief. The coverage stratum varies parameters the brief
pinned, and its values land between the brief's own levels, so brief levels would call two adjacent
fabricated points non-adjacent.

**The cost:** a design with uneven spacing has uneven "one step". A parameter sampled at 10, 11, 12
and 40 treats 12→40 as one step. Worth revisiting if a coverage stratum ever grows large.

## 5. Dominance is measured against the median variant of the same partition

The paper compares the chosen configuration's out-of-sample distribution against the pooled
distribution of every trial. This module compares it against the **median variant of the same
partition**, which makes the comparison paired: it asks whether the choosing was worth doing on
each history, rather than comparing two pools that never met. It also keeps memory flat instead of
holding n × 252 scores.

**The cost:** it cannot see a rule that beats the median reliably while losing to the upper half.

## 6. The independent-trial count is a clustering, not an eigenvalue count

`trials.independent` cuts an average-linkage tree on correlation distance and picks the silhouette
maximum among splits where no cluster holds half the variants. That last clause is doing real work
— see the README — but it is a rule, not a measurement.

**The obvious alternative** is the participation ratio of the correlation matrix's eigenvalues,
`(Σλ)² / Σλ²`: deterministic, no `k` to choose, no degenerate split to exclude, and it is the
standard way to count independent factors in a correlated set. It would remove the one genuinely
arbitrary constant in this module. It was not used because the owner asked for the clustering
approach by name, and because a cluster count is something a person can look at and argue with.

**What would settle it:** compute both on ten mothers. If they agree within a factor of two, take
the eigenvalue one and delete the rule.

## 7. The PBO has no interval

The report gives a point estimate. Its null spread is measured (0.21 at 60 variants) and written
into the README, the manual and the verdict's comment, but nothing computes an interval for a real
grid. A bootstrap over the 252 partitions would be wrong — they are heavily dependent — and a
block-jackknife over the ten blocks is the right shape but was out of scope for this batch.

**Until it exists, the 50 % gate is a coarse filter and the figure is the evidence.**

## 8. The final period is dropped, the first is not

`matrix.panel` drops the last period because an open position on the last bar is marked to market
in the equity curve and excluded from net profit — measured on 172 of 962 variants, by up to 332
dollars. The leading weeks before the backtest starts are left in: they are identical zeros across
every variant, so they cannot change a ranking, and dropping them would need a rule for where the
trading really begins.
