# walkForwardCorrelation — the choices that had real alternatives

Every section here is a decision that moves the answer and was taken on an argument rather than on
a measurement. Argue with it in writing before changing it in code.

**Sections 1, 2, 3 and 8 were settled by the owner on 2026-09-23** and are kept here as the record
of what was decided and why, not as open questions. **4 to 7 stay open on purpose**: they are
choices he wants to re-read against a fully tested strategy before ruling on them.

## 1. Weekly periods, not monthly or daily — ✅ settled 2026-09-23

`config.yaml: cscv.period` is `W`. Daily was never an option: at roughly sixty trades a year a
daily matrix is almost all zeros, and ranking variants by the Sharpe of a mostly-zero series ranks
their luck. Monthly would halve the noise per observation and leave 180 periods over 2008–2022,
which is 18 per block — thin but not absurd.

**Settled: weekly stays**, and the owner's reason is that it is the aggregation the rest of the
study is built on — a daily matrix at sixty trades a year ranks luck, and monthly throws away
resolution the CSCV needs to cut twelve blocks. `config.yaml: cscv.period` still accepts `ME` for
anyone who wants to check.

## 2. The score is a Sharpe, not Ret/DD — ✅ settled 2026-09-23

Every ranking inside the CSCV uses per-period Sharpe. The protocol's §4a is emphatic that Ret/DD is
biased by window length — total return grows with T and max drawdown with √T — which is exactly why
it is wrong for comparing in-sample against out-of-sample windows of different lengths.

**Inside the CSCV that objection is weaker than it looks**: every partition has six blocks on each
side, so every window is the same length and the bias is constant. Ret/DD would be *arithmetically*
legitimate here.

**Settled: the score must be a rate per period, and Ret/DD is not one.** The owner ruled it out on
the general argument rather than the partition-level one — Ret/DD grows with elapsed time, so it
can never be compared across windows of different lengths, and a score used in only one place of
the module would be a trap waiting for the first person who reuses it.

**What was built instead:** `config.yaml: cscv.score` now chooses between `sharpe` and `sortino`,
both rates per period, and `cscv.SCORES` is where a third one would go. Measured 2026-09-23 on
`Strategy 17.9.39`, 12 blocks: the choice barely moves the answer — PBO 30.4 % against 28.9 % for
`argmax`, 3.6 % against 4.1 % for `plateau_centre`, and the same verdict on every rule.

⚠️ **The deflated Sharpe stays a Sharpe whatever the score is.** It is defined against the expected
maximum of n_eff draws of a Sharpe; ranking picks the variant, the DSR then judges that variant on
its Sharpe. `trials.deflated` says so in its docstring.

## 3. Twelve blocks — ✅ settled 2026-09-23

C(12,6) = 924 partitions, which is what López de Prado's own worked examples use. It was ten
(252 partitions) until the owner asked for the paper's recommendation to be the default.

**It is not free and it does not change the reading.** Measured on `Strategy 17.9.39`, 479
variants, 786 weeks: 6 s at ten blocks against 14 s at twelve, same 380 MB of RAM, and the PBO of
`argmax` moved from 41.3 % to 30.4 % while `plateau_centre` moved from 4.8 % to 3.6 %. Both
movements sit well inside the 0.21 null standard deviation of §7 — the verdict is the same one, and
neither number should be quoted to the decimal.

Sixteen blocks gives 12,870 partitions, fourteen times the compute of twelve for a third-decimal
improvement on that same statistic. Eight gives 70, too few to see the shape of the lambda
distribution. **`pbo.py --blocks N` overrides the default per run**, so the cheap setting is one
flag away and the expensive one needs no edit either.

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

## 8. The final period is dropped, the first is not — ✅ settled 2026-09-23

`inputs.panel.panel` drops the last period because an open position on the last bar is marked to
market in the equity curve and excluded from net profit — measured on 172 of 962 variants, by up
to 332 dollars. The leading weeks before the backtest starts are left in: they are identical zeros
across every variant, so they cannot change a ranking, and dropping them would need a rule for
where the trading really begins.

**Settled: confirmed by the owner, the last week goes.** The mark-to-market on an open position is
not a result the strategy delivered, and 172 of 962 variants carry one.
