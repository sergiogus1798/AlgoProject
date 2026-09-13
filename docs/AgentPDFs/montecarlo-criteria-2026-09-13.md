# Monte Carlo — decision criteria

**What this is.** A decision procedure. Given the output of `strategies/monteCarlo` for one
strategy, it returns exactly one of three verdicts — **ADVANCE**, **KILL**, **HOLD** — together with
the rule that decided and the number that fired it. It is written to be executed by a reasoning
agent without further judgement calls: every threshold is a stated constant, every constant is
quoted with the rate at which it fires on a named reference population, and every formula is
closed-form or names the exact key of the result object it reads.

**Companion document.** `montecarlo-2026-09-13.md` in this folder defines every number the module
produces and takes no view on any of them. This document takes the view. Where the two disagree
about a formula, that one is the source of truth about what the code computes; this one is the
source of truth about what to do with it.

**Reference population.** Every firing rate, quantile and calibration claim below was measured on
the 36 strategies of databank `Results`, project `XAUUSD`, trade export `2026-09-03`
(`raw/XAUUSD/Results/2026-09-03/trades/`), whose Monte Carlo run of `2026-09-12` is in
`reports/XAUUSD/Results/2026-09-12/montecarlo/`. The per-scope statistics, permutation tests and
heterogeneity tests were computed directly from those 36 trade files for this document. One asset,
one generation run, one date: the *structure* of the rules is general, the *constants* are calibrated
here and must be re-measured when the asset or the generation regime changes. Appendix A is the whole
population, strategy by strategy; Appendix B is its quantiles.

**Pipeline note.** This study runs after the IS/OOS decay test and the cross-market retest.
What it may therefore assume, and how every firing rate below changes once that filter is
actually applied, is §11 — read it before using any rate in §3–§5 as a expectation.

**Scope note.** This is not a test of whether an edge exists. It is a test of what an edge rests on,
and of whether it survived the walk-forward. Statements about overfitting relative to the number of
strategies tried during generation cannot be made here and are not made: that needs the generation
population, which does not reach this stage.

---

## 0. The contract

**Input.** One of, in order of preference:

1. `derived/montecarlo/<asset>/<databank>/<strategy>.json` — `body.result` and `body.verdict`, the
   full result object. This is the only input that carries everything.
2. `reports/.../montecarlo/verdict.csv` plus `flags.csv` — one flat row per strategy. Sufficient for
   the Layer 0 and Layer 3 reads, **insufficient for Layers 1 and 2**, which need per-scope numbers
   these files do not carry (§9).
3. The per-strategy HTML report. Human-readable and complete, but the agent must parse it.

**Output.** For each strategy, one record:

```
decision   : ADVANCE | KILL | HOLD
score      : 0-100, meaningful only when no veto fired
binding    : the rule id that decided, e.g. "V2"
value      : the number that fired it
limit      : the constant it was compared against
evidence   : every rule that fired, not only the first
risk_scale : the per-trade risk that fits the drawdown budget (§6)
```

**Rules the agent may not break.**

- **Never report a decision without the rule id and the number.** A verdict whose arithmetic cannot
  be reproduced from this document is a bug in the agent, not a finding about the strategy.
- **Evaluate every rule, always.** Do not stop at the first veto. Which rules fired *together* is the
  diagnosis; which fired first is an accident of ordering.
- **A missing number is HOLD, never KILL.** Absence of evidence disqualifies the analysis, not the
  strategy.
- **Never invent a number that is not in the input.** If a rule needs a statistic the report does not
  carry, that rule's outcome is HOLD, and §9 names what must be added to the code.

---

## 1. The seven principles the rules encode

Read these before the rules. Each rule cites the principle it comes from, and a rule whose principle
the agent does not understand will be misapplied on the first strategy that does not resemble the
reference population.

### P1 — The study measures dependence, not existence

Every family perturbs a backtest that already happened. None of them can create evidence that an edge
is real; they can only show what it rests on. So the criteria are built to **disqualify** on
demonstrated fragility and to **rank** on everything else. They never certify.

### P2 — Only the out-of-sample scope is near-unbiased

These strategies were selected by StrategyQuant X out of a generation population. Selection happened
on in-sample behaviour, so `SR_IS` is inflated by an unknown amount and is not an estimate of
anything. `SR_OOS` is the near-unbiased estimate. It follows that:

- `SR_OOS < SR_IS` is the **expected** outcome for every selected strategy, not a finding. On the
  reference population the median retention is 0.136 and 34 of 36 strategies fall below 0.60 — a
  "warning" that fires on 94% of the population is not a warning (P7).
- The question is never "did it degrade" (it always did). It is **"where did it land, and was the
  drop larger than sampling noise can explain."** Those are two separate tests, and the rules keep
  them separate (V1 and V2).
- Any statistic used to *decide* must be computed on the OOS scope, or on both scopes compared
  correctly. A statistic computed on the pooled stream is dominated by the inflated IS side: with
  `n_IS / n_OOS ≈ 2.3` on the reference population, a pooled number is roughly 70% in-sample.

### P3 — Every cross-scope comparison must be scale-free

On the reference population `n_IS` spans 690–1312 and `n_OOS` spans 292–624. The two scopes are never
the same length, so any statistic whose value grows with the sample cannot be compared between them
without normalisation.

| statistic | how it scales with n | comparable across scopes? |
|---|---|---|
| per-trade Sharpe `μ/σ` | not at all | **yes, directly** |
| profit factor | not at all (only its sampling error shrinks) | yes, directly |
| per-trade expectancy in R | not at all | yes, directly |
| Ret/DD | weakly (numerator ∝ n, denominator ∝ √n … n) | only with care |
| net profit | **∝ n** | no — divide by n |
| max drawdown `dd_pct` | **grows with n**; → σ√(πn/2) at zero drift | no — see below |
| longest losing run | **∝ log n** | no |

Drawdown is the trap, because it is the number that looks most like a risk measure and is the least
comparable. For an additive equity curve with per-trade mean μ and standard deviation σ, the expected
maximum drawdown over n trades is `σ·√(πn/2)` at μ = 0, and tends to `σ²/(2μ)` once drift dominates
(Magdon-Ismail et al., 2004). Both limits depend on n, so a shorter scope draws down less for
arithmetic reasons alone.

**Consequence for the IS/OOS overlay figures** (`degrade.py`, §8 of the companion document): as the
code stands, the IS histogram is built from `n_IS` trades and the OOS histogram from `n_OOS` trades.
The OOS side is therefore handicapped *in its own favour* on `dd_pct` and *against itself* on `net`.
Reading the two histograms as a like-for-like comparison is wrong in opposite directions depending on
which family is on screen. Two ways out, and the agent must know which is in force:

- **Preferred, needs a code change (§9.4):** resample the longer scope at the shorter scope's length,
  so both distributions describe `min(n_IS, n_OOS)` trades. Then they are directly comparable and no
  normalisation is needed.
- **Available today:** ignore the raw overlay for decisions and use only the scale-free per-scope
  statistics of §7. Read the overlay as a picture, never as a measurement.

### P4 — Never put a near-zero quantity in a denominator

This is the single most likely way an agent will mis-kill a good strategy here, so it gets its own
principle. On the reference population the median OOS net profit is a small positive number, and
several are near zero or negative. Any ratio of the form `something / net_OOS` therefore explodes,
flips sign, or saturates, and its threshold stops meaning what it was calibrated to mean.

Four such ratios were tested for this document and **rejected on measurement**:

| rejected statistic | kills on the reference population | why it is meaningless |
|---|---|---|
| `best OOS trade / net_OOS > 0.25` | 50% | small denominator, not concentration |
| `net_OOS without its best 3 trades ≤ 0` | 69% | same |
| `trimmed SR_OOS / untrimmed SR_OOS < 0.5` | 67%, values spanning −94.7 to +0.64 | denominator near zero |
| `net_5 / net_OOS` as a score term | median 0.0, bimodal | same |

Their repaired forms are V6 and V7. The general repair: **measure concentration against gross profit,
and measure edges in absolute terms — never as a ratio to a near-zero net.**

### P5 — Drawdown is a sizing parameter, not a quality gate

*This is the owner's standing instruction and it overrides any statistical argument for gating on
drawdown.* A strategy is not disqualified for drawing down more than a prop-firm limit, because the
risk per trade is a free parameter chosen later.

Under additive fixed-USD risk, scaling `risk_per_trade` by λ scales every trade's P&L by λ, hence net
profit and dollar drawdown by λ, leaving **Ret/DD exactly invariant**. Ret/DD is therefore the
quality number that survives resizing, and `dd_pct` is not. The correct output is not a pass/fail on
drawdown but the risk level at which the strategy fits a stated budget (§6).

The existing `dd_99` veto (`dd_pct_99 > 10%`) fires on 21 of 36 strategies and contradicts this
principle. **It is removed**, and replaced by the §6 sizing output.

### P6 — Separate the distribution's own shape from this backtest's luck

`inflation = p95(dd_pct under reordering) / dd_pct(observed)` is meant to measure how lucky the real
ordering was. It does not, because it mixes two independent things. Factor it exactly:

```
inflation  =  p95 / dd_obs  =  (p95 / p50) × (p50 / dd_obs)
                               ^^^^^^^^^^^   ^^^^^^^^^^^^^^
                               skew_ratio     luck_ratio
```

Measured over all 36 strategies with a 5 000-draw exact permutation (`iid_shuffle`, which preserves
the trade multiset):

- `skew_ratio = p95/p50` spans **1.535 to 1.622**, mean 1.578, standard deviation 0.019. It is a
  constant. It is the right-hand skew of the maximum-drawdown distribution itself, and it carries
  **no information about any strategy**.
- `luck_ratio = p50/dd_obs` spans 0.739 to 1.662, median 1.137. This is the part that is about the
  strategy.

So `inflation ≈ 1.578 × luck_ratio`, which means the configured watch threshold of 1.5 fires whenever
`luck_ratio > 0.95` — on essentially any strategy whose real drawdown was no worse than the median of
its own reorderings. It fires on **36 of 36**. The veto threshold of 3.0 requires
`luck_ratio > 1.90`, above the population maximum of 1.662, so it fires on **0 of 36**. One threshold
is unreachable, the other unavoidable; neither has ever separated anything.

The statistic that does this job properly is the **permutation rank** (V3), which has a known null
distribution and needs no calibration at all.

### P7 — A threshold is not a threshold until its firing rate is known

Every constant in this document is quoted with the fraction of the reference population it
disqualifies. A rule that fires on everything and a rule that fires on nothing are the same rule:
neither decides. The same test applies to score terms — **no term of a composite may be constant
across the population.** The current system breaks this twice (§8): sub-score D is 0.0 on all 36
strategies and sub-score E is 100.0 on all 36, so 30% of the composite's weight carries zero
information, and the tiers built on top of it are unreachable by construction.

---

## 2. Notation and shared primitives

Three formulas recur. Define them once.

### 2.1 The Sharpe estimate and its standard error

For a set of trades with per-trade P&L `x`:

```
SR   = mean(x) / std(x, ddof=1)
g3   = skewness(x)                       # scipy.stats.skew
g4   = kurtosis(x, fisher=False)         # raw kurtosis; a normal gives 3
V    = 1 − g3·SR + ((g4 − 1)/4)·SR²      # Mertens / Lo variance factor
SE   = sqrt(V / n)
t    = SR / SE
```

`V` is **already computed by the module**, inside `significance.psr()`, as the `var` term of the
Probabilistic Sharpe Ratio. The PSR and the standard error of a Sharpe ratio are the same piece of
mathematics: `PSR(b) = Φ((SR − b)·√(n−1) / √V)`. Everything this document does with per-scope Sharpe
ratios reuses that one function, applied to a scope instead of to the pooled stream.

`V` corrects for the shape of the P&L distribution. On the reference population `g4` reaches 8.8, so
the correction is not cosmetic: fat tails inflate the uncertainty of a Sharpe estimate, and ignoring
them makes every test below look more certain than it is.

### 2.2 Annualisation

Per-trade Sharpe is the scale-free quantity, but it is unreadable. Annualise **per scope**, on that
scope's own trade rate:

```
tpy(scope)    = n(scope) / years(scope)     # years between that scope's first and last open time
ann_SR(scope) = SR(scope) × sqrt(tpy(scope))
```

Never annualise the OOS scope with the pooled trade rate. On the reference population `tpy` spans
66–129, so using the wrong rate misstates the annualised number by up to 40%. Every threshold below
that mentions an annualised Sharpe assumes this definition.

### 2.3 The score curve

```
curve(v, bad, good) = clip(100 · (v − bad) / (good − bad), 0, 100),   and 0 when v is NaN
```

Straight-line, clipped at both ends; `bad` may be above or below `good`. Identical to
`scoring.curve()` in the code, including the NaN rule: a missing number scores zero rather than
propagating.

---

## 3. Layer 0 — admissibility

These checks ask whether the *analysis* is fit to decide on. Every failure here returns **HOLD** and
names the remedy. **None of them may ever return KILL** — a strategy is not at fault for a thin
export or an unstable simulation.

| id | check | formula | threshold | remedy on failure |
|---|---|---|---|---|
| A1 | both scopes present | `stream.samples()` returns non-empty `IS` and `OOS` | both ≥ 1 | re-export with the OOS window attached |
| A2 | OOS large enough to decide | `n_OOS` | ≥ 200 to decide; 60–199 → decide with `HOLD-THIN`; < 60 → HOLD | extend the OOS window or retest |
| A3 | OOS percentiles readable | `confidence.percentile(n_OOS, 5)` | must be `reliable`, i.e. `n_OOS ≥ 200` | as A2 |
| A4 | block methods have blocks | `confidence.blocks(n, min(blocks), 20)` | `reliable` | shorten `block_min` or accept Family A only |
| A5 | simulation noise is below the decision margin | `stability.worst_spread` | ≤ 0.10 | raise `global.n_sims` and re-run |
| A6 | reordering models are sound | `A.invariant[label]` for every model in `KEEPS_MULTISET` | ≈ 0 (float error only) | **a bug in the model** — stop, do not decide |
| A7 | volatility data covers the trades | `D.regime.coverage` | ≥ 0.95 | re-export bars; Family D unusable below this |
| A8 | the asset file matches the backtest | `cost_check.diverges` | false | Family C and V4 → HOLD; the rest still decides |

**A2 in detail.** The threshold is not arbitrary. `confidence.percentile(n, q)` calls a percentile
reliable when the expected count in the tail, `n · min(q, 100−q)/100`, reaches 10. For the 5th
percentile that is `n ≥ 200`. Below 200 trades the OOS 5th percentile rests on fewer than ten
observations and V7's and S3's numbers are noise. On the reference population `n_OOS` is 292 at
minimum, so A2 never fires there — it exists for the strategies that will arrive with a shorter
retest window.

**A6 in detail.** `iid_shuffle` and `block_shuffle` only permute trades, so net profit is identical in
every path by construction and its standard deviation across paths must be zero to floating-point
error. A non-zero value is never a property of the strategy; it means the draw model is broken and
every number downstream of it is void. This is the one check that stops the analysis rather than
downgrading it.

---

## 4. Layer 1 — the seven vetoes

Each veto is defensible on its own, fires on a measured fraction of the reference population, and
comes with the false-kill risk it carries. A strategy that fires **any** veto is **KILL**.

Ordering is for reading only; the agent evaluates all seven and reports all that fired.

### V1 — There is no out-of-sample edge to begin with

> **Fires when:** `SR_OOS ≤ 0` **or** `PF_OOS ≤ 1.0`<br>
> **Reference population:** kills 10 of 36 (27.8%)<br>
> **Principle:** P2

This is a sign test, not a significance test. It asks only that the near-unbiased estimate sit on the
correct side of zero. If the out-of-sample Sharpe is negative there is no positive edge for
degradation to even be about, and no amount of robustness elsewhere repairs it.

The two conditions are near-equivalent by construction and are both stated so that a scope with an
unusual win/loss shape cannot slip through one of them. On the reference population they select the
same 10 strategies.

**False-kill risk, computed.** For a strategy whose *true* annualised OOS Sharpe is S, over `n_OOS`
trades at `tpy` trades per year, the estimate has standard error ≈ `1/√n_OOS` in per-trade units, so

```
P(SR_OOS ≤ 0) = Φ( −S / √tpy · √n_OOS ) = Φ( −S · √(years_OOS) )
```

With the reference population's 5 OOS years: a truly excellent strategy (S = 1.0) is wrongly killed
1.3% of the time; a good one (S = 0.75) 4.7%; a mediocre one (S = 0.30) 25%. **The rule is
deliberately harsh on mediocre strategies and nearly harmless to good ones**, which is the correct
asymmetry when the next stage costs real work.

**Why not a significance test here.** Requiring `t_OOS ≥ 1.645` instead would kill 34 of 36 (94.4%).
That is not a standards choice, it is a power failure: with `n_OOS ≈ 440`, reaching t = 1.645 demands
a true annualised Sharpe near 0.75 *and* good luck. The OOS sample cannot certify, so V1 does not ask
it to. Significance information is not discarded — it enters the score through S1 and S2, where being
short of certainty costs points instead of a life.

### V2 — The decay is larger than noise explains *and* it landed somewhere unusable

> **Fires when:** `z_decay > 2.326` (p < 0.01, one-sided) **and** `ann_SR_OOS < 0.60`<br>
> **Reference population:** kills 11 of 36 (30.6%)<br>
> **Principle:** P2, P3

This is the rule the owner's priority hangs on, so its construction matters more than any other.

```
Δ       = SR_IS − SR_OOS
SE_Δ    = sqrt( V_IS/n_IS + V_OOS/n_OOS )
z_decay = Δ / SE_Δ
p_decay = 1 − Φ(z_decay)
```

The two scopes are disjoint chronological blocks, so their estimates are independent and the variances
add. Each `V` is the §2.1 factor computed on that scope's own trades, so each side carries its own
skew and kurtosis rather than a shared assumption.

**Both conditions are required, and the reason is not a compromise.** A drop is only actionable if it
lands the strategy somewhere it cannot be used. A strategy going from annualised Sharpe 3.0 to 1.5
has retention 0.50 and an enormous `z_decay`, and is still excellent. **Vetoing on the size of the
drop alone punishes strong strategies for having been strong in-sample.** The landing condition is
what makes the rule about usability rather than about arithmetic.

Equally, the landing condition alone is not enough: a strategy can land low simply because it was
never strong, which is a level problem V1 and the score already handle. V2 exists for the specific
pathology of a strategy that *was* strong in-sample, *is* weak out-of-sample, and whose gap is too
large to be luck.

**On the reference population:** `z_decay` has median 1.99 and spans 0.46–2.99; `p_decay` has median
0.023. So the IS→OOS Sharpe drop is significant at the 5% level for more than half the population and
at the 1% level for about a third. This is exactly what P2 predicts from selection, and it is why the
threshold is set at p < 0.01 rather than p < 0.05 — at 5% the rule would fire on 67% of the
population and stop discriminating.

**Why not the retention ratio that the code uses today.** `oos_ratio = median(SR_OOS bootstrap) /
median(SR_IS bootstrap)` has four defects, in increasing order of seriousness:

1. It is a ratio of two noisy estimates, with no tractable sampling distribution. The *difference*
   has one, and `SE_Δ` above is it.
2. It explodes when `SR_IS` is near zero. (Not binding on the reference population, where `SR_IS`
   spans 0.095–0.200, but it will bind on a different generation run.)
3. Negative values — 10 of 36 here — are a categorically different failure from "OOS is 30% of IS",
   and putting both on one axis makes the axis meaningless in the middle.
4. **It ignores sample size entirely.** Retention 0.3 on 600 OOS trades and retention 0.3 on 100 OOS
   trades are very different pieces of evidence, and the ratio cannot tell them apart.

Retention is still worth reporting, and it is worth points in the score (S2), because it is the number
a human reads fastest. It is not worth a veto on its own.

**Sensitivity — and it runs the opposite way to intuition.** Measured on the reference population,
the landing floor is nearly inert and the significance threshold is what decides:

| landing floor (z held at 2.326) | V2 kills | | `z_decay` threshold (floor held at 0.60) | V2 kills |
|---|---|---|---|---|
| 0.40 | 10 / 36 | | 1.645 (p < 0.05) | 24 / 36 |
| 0.50 | 11 / 36 | | **2.326 (p < 0.01)** | **11 / 36** |
| **0.60** | **11 / 36** | | 2.576 (p < 0.005) | 4 / 36 |
| 0.70 | 11 / 36 | | | |
| 0.80 | 11 / 36 | | | |

The floor does nothing between 0.50 and 0.80 **on this population**, because `z_decay` and
`ann_SR_OOS` are themselves correlated at ρ = −0.66: the strategies whose decay is significant are
already the ones that landed low, so the second condition is almost implied by the first here. The
floor is still worth stating, and is set at **0.60**, because that correlation is a property of this
databank and not a law — a population containing strategies that were very strong in-sample and
merely good out-of-sample would separate the two conditions, and the floor is what stops V2 killing
them.

**The `z_decay` threshold is the constant to guard.** At p < 0.05 it fires on 24 of 36 and stops
discriminating; at p < 0.005 it fires on 4 and stops protecting. p < 0.01 is the setting, and it is
not a free parameter in the way the floor is.

### V3 — The backtest's comfort came from the order the trades arrived in

> **Fires when:** `rank(dd_pct | iid_shuffle) ≤ 0.05` **and** `rank(dd_pct | block_shuffle, largest
> block) ≤ 0.05`<br>
> **Reference population:** kills 3 of 36 (8.3%) on the first leg<br>
> **Principle:** P1, P6<br>
> **Reads:** `A.runs["iid_shuffle"]["dd_pct"]["rank"]` and `A.runs["block_shuffle/<max>"]["dd_pct"]["rank"]`
> — **both already in the result object, no code change needed**

`iid_shuffle` preserves the multiset of trades exactly: every path contains every trade once, only
the order differs. So

```
rank = (1/N) · Σ 1[ dd_pct(simulated path) ≤ dd_pct(observed) ]
```

is an **exact one-sided permutation p-value** for the null "the maximum drawdown does not depend on
the order the trades arrived in". Under that null it is Uniform(0,1). No calibration is required and
no threshold has to be invented: 0.05 means 0.05.

A low rank says the real sequence drew down less than almost any reshuffling of the very same trades.
That comfort is not a property the strategy will reproduce, because the ordering will not repeat.

**The second leg separates luck from structure**, and it is the reason the rule has two. A rank that
stays low under `block_shuffle` — which permutes blocks of consecutive trades and so preserves local
sequencing — means the favourable arrangement is *local and real* (losers genuinely cluster where
size is small, say, or the strategy genuinely stands down after a loss). A rank that is low under
`iid_shuffle` but rises toward 0.5 under `block_shuffle` means the advantage lived in fine-grained
ordering that live trading will not reproduce. Only the second case is luck, and requiring both legs
kills only that case.

**A population-level finding worth recording.** Across the 36 strategies the permutation rank is
significantly non-uniform: mean 0.330 against the null's 0.500, and a Kolmogorov–Smirnov test against
Uniform(0,1) gives p = 0.0003. Eight strategies fall in the lowest decile. The real trade sequences
drew down materially less than their reshufflings do, population-wide — consistent with the
generation stage having selected on drawdown or on Ret/DD, which preferentially keeps strategies whose
actual ordering happened to be kind. **This is a fact about the generation filter, not about any one
strategy**, and it is the main reason V3 is worth having at all.

### V4 — The result does not survive the costs it was actually charged

> **Fires when:** `cost_cushion < 1.5` **or** `spread_cushion < 2.0`<br>
> **Reference population:** `cost_cushion < 1.5` kills 4 of 36 (11.1%); `spread_cushion < 2.0` kills
> 0 of 36<br>
> **Principle:** P1

Define, on the whole stream:

```
cost_cushion   = net_observed / Σ cost_i        # cost_i recovered as gross − net, per trade
spread_cushion = net_observed / Σ spread_i      # spread_i at the asset's sqx_default spread
```

`cost_cushion` is the multiple by which commission and swap would have to rise before the strategy is
flat. It is the cleanest single statement of cost robustness available, and it is far more readable
than Family C's `keep`, which reports the effect of one particular multiplier draw.

**Both cushions are recoverable in closed form from Family C's existing output**, so this rule needs
no new numbers if `Σ cost` and `Σ spread` are not stored. From `cost_shock`, with `m ~ U(1,2)` applied
to the *increment* over the recovered cost:

```
E[net'] = net − C·(E[m] − 1) = net − 0.5·C
keep    = E[net']/net  ⇒  C/net = 2·(1 − keep)
cost_cushion = net/C = 1 / (2·(1 − keep_cost_shock))
breakeven cost multiple = 1 + cost_cushion
```

From `spread_widen`, with `m ~ U(1,2)` applied to the **whole** spread cost:

```
E[net'] = net − S·E[m] = net − 1.5·S
keep    ⇒  S/net = (1 − keep)/1.5
spread_cushion = net/S = 1.5 / (1 − keep_spread_widen)
```

> **A modelling asymmetry the agent must know about.** `cost_shock` subtracts only the *increment*
> over the cost SQX booked, because the P&L is already net of it. `spread_widen` subtracts the<br>
> **entire** modelled spread cost, on top of a P&L in which the spread is already inside the fill
> prices (`core.trades.cost`: "Spread is already inside the fill prices and does not appear here").
> So at a multiplier of 1.0 `spread_widen` is **not** the identity — it charges one full extra
> spread. This is deliberate (a fixed backtest spread is optimistic every single time), but it means
> `keep_spread_widen` is biased low by roughly `S/net` and **is not comparable to
> `keep_cost_shock`.** Compare cushions, which are on a common scale, never the two `keep`s.

On the reference population `cost_cushion` spans 1.08–3.57 with median 2.33, and `spread_cushion`
spans 2.70–6.12 with median 4.45. So the median strategy's entire net profit is only 2.3 times the
commission and swap it paid — thin, and worth knowing. The `spread_cushion < 2.0` leg fires on nothing
here; it is retained as a guard for assets with a wider relative spread than XAUUSD, and its firing
rate on this population is stated as zero so that nobody later mistakes it for an active filter (P7).

### V5 — The edge is not the same edge in every period

> **Fires when:** Cochran's `Q` gives `p < 0.05` **and** `I² > 0.50`<br>
> **Reference population:** kills 5 of 36 (13.9%)<br>
> **Principle:** P1, P7<br>
> **Needs:** per-block Sharpe and variance factor — §9.2

Treat each non-overlapping 24-month calendar block as one independent study of the same underlying
edge, with effect size its own per-trade Sharpe and variance from §2.1:

```
for each block w with n_w ≥ 10 trades:
    θ_w = SR_w,   v_w = V_w / n_w,   weight_w = 1 / v_w

θ̄  = Σ weight_w·θ_w / Σ weight_w          # inverse-variance pooled Sharpe
Q  = Σ weight_w·(θ_w − θ̄)²                # ~ χ²(k−1) under a constant true Sharpe
I² = max(0, (Q − (k − 1)) / Q)             # share of dispersion sampling noise cannot explain
```

`Q` tests whether the block-to-block variation exceeds what sampling noise alone would produce. `I²`
says how much of the variation is real. Requiring both a significant `Q` and `I² > 0.5` means: the
heterogeneity is detectable *and* it dominates the noise.

**This replaces the `dead_block` veto, which is mostly measuring noise.** `dead_block` fires when any
non-overlapping block has a negative resampled median, and it fires on **29 of 36 (80.6%)**. Here is
why that number is uninformative. Under the null that the true per-trade Sharpe is constant at the
population median 0.117, a block of ~200 trades has `SE ≈ 1/√200 = 0.071`, so

```
P(one block's estimate < 0) = Φ(−0.117/0.071) = Φ(−1.65) ≈ 5%
P(at least one of 7 blocks < 0) = 1 − 0.95⁷ ≈ 30%
```

and with the *out-of-sample* Sharpe rather than the pooled one the per-block probability is far
higher still. A genuinely stationary strategy is therefore expected to show a negative block
routinely. On the reference population the median number of negative blocks is 1 of 7 — exactly what
chance predicts — while the heterogeneity test says the dispersion is beyond noise for only 5
strategies. **`dead_block` converts an ordinary sampling fluctuation into a veto**, and it is the
single largest source of false kills in the current system.

On the reference population `I²` spans 0.00–0.71 with median 0.20, and Cochran's `p` spans
0.002–0.958 with median 0.275. Both have real variance, so both are usable (P7).

**Read together with the volatility terciles, not instead of them.** `Q` says *that* the edge moved;
`D.regime.buckets` says *what* it moved with. A strategy with high `I²` whose weakness sits entirely
in the high-volatility tercile has a describable, possibly fixable regime dependence. One with high
`I²` and no tercile pattern has an unexplained one. Both fire V5; the first is worth a note in the
kill record, because it is the kind of strategy worth revisiting with a volatility filter.

### V6 — The out-of-sample result rests on a handful of trades

> **Fires when:** `best_OOS_trade / gross_profit_OOS > 0.15` **or** `effective_winners_OOS < 25`<br>
> **Reference population:** kills 0 of 36 (0.0%)<br>
> **Principle:** P4

```
gross_OOS          = Σ max(pnl_i, 0)   over OOS trades
best_share         = max(pnl_i) / gross_OOS
effective_winners  = (Σ_{pnl>0} pnl_i)² / Σ_{pnl>0} pnl_i²      # 1/Herfindahl of the winners
```

The denominator is **gross profit, never net** (P4). `effective_winners` is the reciprocal
Herfindahl index of the winning trades: the number of equally-sized winners that would produce the
same concentration. It is the more robust of the two, because it does not depend on a single extreme
observation.

On the reference population `best_share` spans 0.021–0.046 and `effective_winners` spans 71–138. The
rule fires on nothing. **It is reported with its zero firing rate rather than quietly dropped**
(P7): concentration is a real failure mode for strategies with rarer, larger trades, and this
population simply does not have it — 66–129 trades per year with a 48% win rate produces broad-based
profit. An agent that sees this rule fire should treat it as a genuine anomaly relative to the
reference population and say so.

The module's own `outlier` check (`best trade / net`, threshold 0.25) also fires on nothing here, for
a different reason: it happens to use the pooled net, which is large. On the OOS scope alone the same
formula fires on 50% of the population from denominator collapse — the P4 trap, live.

### V7 — The out-of-sample edge does not survive a symmetric trim

> **Fires when:** `SR_OOS_trimmed ≤ 0`, where the trim removes the top and bottom 1% of OOS trades<br>
> **Reference population:** kills 11 of 36 (30.6%)<br>
> **Principle:** P4

```
sorted   = sort(pnl_OOS)
k        = max(1, round(0.01 · n_OOS))
trimmed  = sorted[k : n_OOS − k]           # k removed from EACH tail
SR_trim  = mean(trimmed) / std(trimmed, ddof=1)
```

**The trim must be symmetric.** Removing the best trades while keeping the worst mechanically drives
any Sharpe negative and measures nothing — that was the rejected form in P4's table, which killed 67%
of the population with values down to −94.7. Removing the same count from both tails asks the question
that was meant: *is the edge broad-based, or does it live in a few extreme observations?*

On the reference population the trim removes 6–12 trades of 292–624. After it, 25 of 36 strategies
keep a positive OOS edge and 5 change sign; the median annualised OOS Sharpe falls from 0.199 to
0.129. That shrinkage is the honest measure of how much of this population's out-of-sample
performance sits in its tails, and 11 strategies do not survive it at all.

The absolute form (`SR_trim ≤ 0`) is used rather than a retention ratio for the P4 reason: the
untrimmed OOS Sharpe is near zero for much of the population, so any ratio to it is uninterpretable.

---

## 5. Layer 2 — the score for what survived

Every strategy that fires no veto gets a score in 0–100. The score **ranks**; it does not certify
(P1). Its terms are all scale-free, all anchored out-of-sample, and all verified to have real
variance on the reference population (P7).

```
SCORE = 0.35·S1 + 0.25·S2 + 0.15·S3 + 0.15·S4 + 0.10·S5
```

| term | weight | what it measures | formula |
|---|---|---|---|
| **S1** persistence | 0.35 | how good the out-of-sample result actually is | `curve(ann_SR_OOS, 0.0, 1.0)` |
| **S2** retention | 0.25 | how much of the in-sample edge survived, and how resolvable the gap is | `0.6·curve(SR_OOS/SR_IS, 0.0, 0.8) + 0.4·curve(−z_decay, −2.326, 0.0)` |
| **S3** composition | 0.15 | whether the out-of-sample edge survives resampling and trimming | `0.5·curve(pf_5_OOS, 0.90, 1.20) + 0.5·curve(ann_SR_OOS_trimmed, 0.0, 0.8)` |
| **S4** cost cushion | 0.15 | how much worse execution can get | `0.5·curve(cost_cushion, 1.5, 4.0) + 0.5·curve(spread_cushion, 2.5, 6.0)` |
| **S5** uniformity | 0.10 | whether the edge is the same across periods, and free of order luck | `0.5·curve(1 − I², 0.3, 1.0) + 0.5·curve(−rank, −0.5, −0.05)` |

`pf_5_OOS` is the 5th percentile profit factor of a **block** bootstrap over the OOS trades only,
block length `round(n_OOS^(1/3))` (§9.3). The Politis–Romano block rule is used because OOS trades
are correlated inside a regime and an i.i.d. bootstrap reads more comfortably than the strategy can
actually suffer.

**Measured spread of each term on the reference population** — the P7 check that none is degenerate:

| term | min | p5 | median | p95 | max | std |
|---|---|---|---|---|---|---|
| S1 | 0.0 | 0.0 | 19.9 | 59.4 | 76.1 | 22.1 |
| S2 | 0.0 | 0.0 | 13.3 | 69.7 | 88.3 | 23.7 |
| S3 | 0.0 | 0.0 | 8.1 | 53.1 | 69.6 | 19.8 |
| S4 | 2.8 | 10.9 | 45.0 | 84.7 | 91.4 | 23.2 |
| S5 | 0.6 | 13.8 | 56.0 | 95.4 | 100.0 | 25.3 |
| **SCORE** | 4.3 | 5.3 | 25.4 | 58.9 | 75.5 | 19.0 |

Every term spans most of its range with a standard deviation above 19 points. Compare the current
system's sub-scores D (std 0.0) and E (std 0.0).

### 5.1 Why `pf_5_OOS > 1.0` is a score term and not a veto

It is tempting to demand that the 5th percentile profit factor of the OOS trades exceed 1.0 — in one
of twenty resamples the strategy must still be profitable. Measured, that rule kills **34 of 36
(94.4%)**, and the reason is arithmetic, not fragility. Net profit over `n` resampled trades is
positive at the 5th percentile only when

```
SR > 1.645 / √n
```

which at `n_OOS = 440` demands a per-trade Sharpe above 0.078 — reached by 2 of 36 strategies. So
`pf_5_OOS > 1.0` is the same 95% significance demand as `t_OOS ≥ 1.645` in different clothing, and it
fails for the same power reason (V1). As a *score* term on a curve from 0.90 to 1.20 it discriminates
usefully; as a veto it is a wall.

**This is the general lesson for the agent: before using any percentile-based floor as a veto, check
what Sharpe it implicitly demands at the sample size in hand.** A 5th-percentile floor is a
significance test wearing a robustness costume.

### 5.2 The cut, and how to choose it

After the vetoes, 16 of 36 strategies remain. Their scores and the resulting throughput:

| SCORE cut | advance | of population |
|---|---|---|
| ≥ 25 | 14 | 39% |
| ≥ 30 | 11 | 31% |
| ≥ 35 | 10 | 28% |
| ≥ 40 | 9 | 25% |
| ≥ 45 | 7 | 19% |
| ≥ 50 | 7 | 19% |
| ≥ 55 | 2 | 6% |

**The recommended default is 45**, giving 19% advance on the raw databank. The reasoning is not statistical — it cannot
be, because the score is a ranking and not a test. It is that the next stage costs real work per
strategy, so the cut should be set by what that stage can absorb. **If throughput is the binding
constraint, replace the absolute cut with a quota: take the top *k* by SCORE among the non-vetoed.**
A quota is more honest than a fixed number when the generation regime changes, because the score's
absolute level drifts with the population while its ordering does not.

Below the cut the verdict is **HOLD**, not KILL: nothing about these strategies is demonstrably
fragile, they are simply not the best of the batch, and a later batch may be worse.

### 5.3 What the score correlates with, and why that matters

| the score against | Spearman ρ |
|---|---|
| annualised OOS Sharpe | **+0.971** |
| the decay z-statistic | **−0.660** |
| the current system's composite | +0.612 |

Compare the current composite against the same quantities (§8.3): +0.690 with annualised OOS Sharpe
and **+0.050 (p = 0.77) with the decay z-statistic**. The new score is aligned with out-of-sample
persistence and with the absence of decay by construction; the old one is aligned with in-sample
quality and is blind to decay.

---

## 6. Layer 3 — drawdown as a sizing output

By P5, drawdown never vetoes. It produces a number instead.

```
risk_scale     = dd_budget / dd_pct_99
risk_per_trade = risk_scale × 1000        # 1000 USD is config global.risk_per_trade
```

`dd_pct_99` is `A.dd_pct_99`, the 99th percentile of the reordered drawdown distribution — the
appropriate input because the question is what the account must survive, not what it happened to
survive.

**This is a first-order estimate, and it is conservative.** Scaling `risk_per_trade` by λ scales every
P&L by λ, so dollar drawdown scales exactly by λ, but `dd_pct = max(drop/peak)` divides by a peak
that contains the unscaled starting equity. To first order `dd_pct ≈ λ·dd_$/equity0`, linear in λ.
The second-order term is favourable: a larger account cushion accumulates as profits do, so the true
`dd_pct` grows slightly more slowly than linearly. **For an exact answer, re-run `metrics.paths()` on
`λ · pnl` and read `dd_pct_99` again** — it costs one simulation pass and removes the approximation.

On the reference population, for a 10% budget at the 99th percentile, the implied risk per trade has
median $795 and spans $370–$1 908. Read: most of these strategies need to be sized *down* from the
$1 000 the study assumed to fit a 10% budget, and a few can be sized up.

Report alongside it the two numbers that are invariant under resizing and therefore describe the
strategy rather than the sizing choice: **Ret/DD** (exactly invariant) and **annualised OOS Sharpe**.

---

## 7. The degradation module, in full

The owner's stated priority is avoiding IS→OOS degradation, so this section collects everything
bearing on it in one place. Nothing here is new; it is §1–§5 re-indexed by that question.

### 7.1 The five numbers that answer it

Computed on the two scopes from `stream.samples()`, using §2.1 and §2.2:

| number | formula | what it tells you | reference population |
|---|---|---|---|
| `ann_SR_OOS` | §2.2 on the OOS scope | where it landed — the only near-unbiased level estimate | −0.519 … 0.761, median 0.199 |
| `retention` | `SR_OOS / SR_IS` | how much survived; readable, not decisive | −0.508 … 0.750, median 0.136 |
| `z_decay` | §4/V2 | whether the gap is bigger than noise | 0.46 … 2.99, median 1.99 |
| `PSR_OOS(b)` | `Φ((SR_OOS − b)·√(n_OOS−1)/√V_OOS)` | probability the true OOS Sharpe beats `b` | at b=0: 0.127 … 0.959, median 0.672 |
| `ann_SR_OOS_trimmed` | V7 | whether the landing survives a symmetric trim | −0.690 … 0.867, median 0.129 |

**The decision content is in `ann_SR_OOS` (level) and `z_decay` (excess decay).** Retention is for
reading. The trimmed version is the durability check. `PSR_OOS` is the same information as `z_decay`'s
numerator expressed as a probability, and is the number to quote to a human.

### 7.2 Relocating the PSR is the single highest-value change in this document

`family_e` computes the PSR on the **pooled** stream against a benchmark of 0. On the reference
population that gives 0.972–1.000 — sub-score E is exactly 100.0 on all 36 strategies. The reason is
arithmetic: at `n ≈ 1300` and a pooled per-trade Sharpe of 0.12, `z ≈ 0.12·√1299 ≈ 4.3`, so `Φ(z)` is
indistinguishable from 1. **The test is being asked whether an edge that was selected for being
positive in-sample is positive in-sample.** It is, always, and 10% of the composite's weight is spent
confirming it.

Move the same formula to the OOS scope and it becomes the sharpest single discriminator available:

| scope | PSR at benchmark 0, reference population |
|---|---|
| pooled (as configured today) | 0.972 – 1.000, median 0.9996 — **zero variance for decisions** |
| **OOS only** | **0.127 – 0.959, median 0.672 — full range** |

The exemplar `Strategy 17.18.29` illustrates it: pooled PSR 0.99999987, OOS PSR 0.887. The same
statistic, the same code, one scope change, and a number that saturated becomes a number that
separates.

**Do not then gate on `PSR_OOS ≥ 0.90`.** That is the 94%-kill wall of §5.1 again. Use it as the
human-readable form of S1 and S2, and keep V1's sign test as the veto.

### 7.3 How to read the overlay figures without being misled

`degrade.overlay()` draws, per family, the IS and OOS distributions of that family's headline
statistic on one axis. As built today they are **not** like-for-like (P3), and the direction of the
error differs by family:

| family | statistic | how the unequal lengths bias it |
|---|---|---|
| A | `dd_pct` | OOS is **flattered**: fewer trades, less opportunity to draw down |
| B, D | `net` | OOS is **penalised**: net profit scales with trade count, and OOS has ~43% as many |
| C (×4) | `net` | same as B |

So the exemplar's Family A overlay — OOS p95 drawdown 6.33% against IS 3.18%, twice as bad — is
**worse than it appears**, because the shorter OOS scope should have drawn down *less*. And every
Family B and C overlay showing OOS net below IS net is telling you mostly that the OOS window is
shorter.

Until §9.4 is implemented: **use the overlays to see shape and direction, and take every quantitative
IS/OOS claim from §7.1 instead.** After §9.4, both sides describe `min(n_IS, n_OOS)` trades and the
overlays can be read directly.

### 7.4 A structural caveat the agent must carry

On the reference population the split is a clean chronological walk-forward: in-sample is
2008-01 → 2017-12, out-of-sample is 2018-01 → 2022-12. Two consequences:

1. **The OOS scope is one regime draw, not 440 independent ones.** It contains the 2020 liquidity
   shock and the 2022 rate shock on gold. The trades inside it are correlated through the regime, so
   an i.i.d. reading of `n_OOS` overstates the evidence. This is why the block bootstrap is specified
   for `pf_5_OOS` (§5), and it is a second reason not to demand 95% significance of the OOS scope.
2. **Degradation and regime change are confounded here and cannot be fully separated.** V5's
   heterogeneity test and the volatility terciles are what partially separate them: a strategy whose
   weakness is confined to one volatility tercile has a regime dependence, while one that decayed
   uniformly has an overfitting signature. Report which of the two the evidence looks like, and never
   claim more than the data separates.

---

## 8. Diagnosis of the current verdict system

This section exists so that the change is auditable rather than asserted. Every number is from the
reference population's own `verdict.csv` and `flags.csv`.

### 8.1 The verdict tiers are unreachable by construction

Sub-score D is **0.0 on all 36 strategies**; sub-score E is **100.0 on all 36**. With
`weights = {A:0.25, B:0.25, C:0.20, D:0.20, E:0.10}` the attainable composite is therefore

```
composite = 0.25·A + 0.25·B + 0.20·C + 0.20·0 + 0.10·100
          = 0.25·A + 0.25·B + 0.20·C + 10
```

The observed maxima are A = 70.3, B = 83.6, C = 63.3, so the highest composite this population can
produce is `0.25·70.3 + 0.25·83.6 + 0.20·63.3 + 10 = 61.1` — **exactly the observed maximum.** The
tiers are 80 / 65 / 50, so `STRONG` and `ACCEPTABLE` cannot be reached by any strategy in this
databank, whatever it does. The observed verdicts follow mechanically: 33 FAIL, 3 MARGINAL, 0
anything else.

### 8.2 Why D is always 0 and E is always 100

**D** is `min` of three terms, the first of which is `curve(windows_ok, 0.70, 1.0)` where `windows_ok`
is the fraction of rolling 24-month windows whose 5th-percentile net profit is positive. That fraction
spans 9.6%–48.1% on this population, never reaching the 0.70 that scores anything above zero. The
reason is §5.1's arithmetic: `net_5 > 0` in a window of ~215 trades requires a per-trade Sharpe above
`1.645/√215 = 0.112`, which is *above the population's median pooled Sharpe of 0.117* — so it demands
that most windows individually beat the whole sample's central estimate. **The threshold asks for
something the population cannot supply**, and because D takes a `min`, one impossible term zeroes the
family.

**E** is `curve(psr, 0.90, 0.95)` and the PSR saturates at 1.0 for the reason in §7.2.

### 8.3 The composite measures in-sample quality, not robustness

Spearman rank correlations of the current composite against quantities computed independently for
this document:

| the composite against | ρ | p |
|---|---|---|
| cost cushion | **+0.858** | 0.000 |
| annualised IS Sharpe | **+0.825** | 0.000 |
| in-sample per-trade Sharpe | +0.810 | 0.000 |
| in-sample profit factor | +0.781 | 0.000 |
| annualised OOS Sharpe | +0.690 | 0.000 |
| retention | +0.582 | 0.000 |
| **the decay z-statistic** | **+0.050** | **0.772** |
| permutation rank of the drawdown | **−0.385** | 0.021 |

Two readings, both uncomfortable. First, the composite's strongest associations are with in-sample
quantities, and its association with the IS→OOS decay — the owner's stated priority — is
indistinguishable from zero. Second, the correlation with the permutation rank is **negative**:
strategies whose real ordering was luckier score *higher*. The `inflation` term intended to penalise
order luck is dominated by the `dd_pct_99` and `ret_dd` terms in the same sub-score, which a lucky
ordering improves. The net effect is that the system mildly rewards the thing it was built to punish.

### 8.4 Which current checks fire, and the verdict on each

| check | fires | disposition |
|---|---|---|
| `inflation_watch` | **36/36** | **remove.** `inflation = 1.578 × luck_ratio`; the threshold is below the population floor (P6) |
| `inflation` (veto) | 0/36 | **remove.** Requires `luck_ratio > 1.90`, above the population ceiling |
| `windows` | 36/36 | **remove.** Demands a per-window Sharpe above the sample's own median (§8.2) |
| `dead_block` | 29/36 | **replace with V5.** ~30% of stationary strategies show a negative block by chance (§4/V5) |
| `dd_99` | 21/36 | **remove.** Contradicts P5; becomes the §6 sizing output |
| `oos_red` | 30/36, warning only | **promote and reformulate.** The priority signal, currently unable to veto anything → V1, V2 |
| `oos_amber` | 4/36, warning only | folded into S2 |
| `pf_5` (B, pooled) | 13/36 | **re-scope.** Pooled is ~70% in-sample; use the OOS scope → S3 |
| `psr` | 0/36 | **re-scope to OOS** (§7.2), and keep as a score term, not a gate |
| `outlier` | 0/36 | **keep as V6**, with the gross-profit denominator (P4) |
| Family C `keep`/`pf_5` | 3–4/36 each | **keep, reformulated as cushions** → V4 |
| `high_vol` | 1/36 | keep as supporting evidence for V5; too rare to gate alone |
| `concentration` | 0/36 | keep as a reported diagnostic |
| `sample` | 0/36 | keep → Layer 0 |

### 8.5 What the two systems disagree about, concretely

The strategy the current system ranks **first** (`Strategy 17.18.29`, composite 61.1, the only one
above 55) has retention 0.35, `z_decay` 1.88 and `I²` 0.40. The strategy the new criteria rank first
(`Strategy 21.30.24`, SCORE 75.5) has annualised OOS Sharpe 0.76, retention 0.68, `z_decay` 0.66 and
`I²` 0.00 — the best out-of-sample profile in the databank on every axis — and the current system
rates it **FAIL** at composite 47.8, below 12 other strategies.

Conversely `Strategy 17.27.43` passes every current veto with composite 50.9, while having the
population's worst permutation rank (0.006 — its real ordering beat 99.4% of reshufflings), its
highest `luck_ratio` (1.616), significant heterogeneity (`p` = 0.018, `I²` = 0.607), retention 0.14
and `z_decay` 2.48. It fires V2, V3 and V5. It is the clearest single case of the two systems pointing
in opposite directions.

---

## 9. What must be added to the code

Five of the rules need numbers the module does not currently emit. Each is small, none needs a new
simulation family, and all are closed-form except §9.3. Until each is added, the rules that depend on
it return **HOLD** for that axis (§0).

### 9.1 Per-scope Sharpe with its variance factor — needed by V1, V2, V7, S1, S2, S3

`B.samples[scope]` today carries `n`, the *median bootstrap* Sharpe, `net` and `pf_5`. It does not
carry the point-estimate Sharpe, its skew, its kurtosis or its standard error. Add, per scope, the
output of the function that already exists:

```python
# in run._family_b, inside the loop over stream.samples()
cut = stream.restrict(source, positions)
parts[name] = {..., **significance.psr(cut["pnl"], cfg["family_e"]["psr_benchmark"]),
               "years": float((cut["open"].max() - cut["open"].min())
                              / np.timedelta64(1, "D")) / 365.25}
```

`significance.psr()` returns `sharpe`, `skew`, `kurtosis`, `n` and `psr` — every ingredient of §2.1
and §2.2. The `years` field is what §2.2 needs to annualise on the scope's own trade rate.

### 9.2 Per-block Sharpe and variance factor — needed by V5

`familyd._slices()` stores `median_net`, `net_5`, `pf_5` and `n` per window. Add the point estimates —
no simulation, so the cost is negligible:

```python
rows.append({..., **{f"sr_{k}": v for k, v in
                     significance.psr(source["pnl"][pos], 0.0).items()}})
```

Then compute Cochran's `Q` and `I²` over the **non-overlapping** blocks only (the rolling windows
overlap, so their estimates are not independent and `Q` is invalid on them). The formula is in V5.

### 9.3 OOS-scope block bootstrap — needed by S3

`B.samples[scope]["pf_5"]` uses `iid_bootstrap`. Add a `block_bootstrap` run on the same scope at
`config.stationary_block(n_scope)`, and read `pf_5` from it. The justification is §7.4: OOS trades are
correlated through the regime, and the i.i.d. bootstrap reads more comfortably than the strategy can
suffer. Keep the i.i.d. number too — the gap between them is itself informative.

### 9.4 Equal-length IS/OOS resampling — needed to make the overlays readable (§7.3)

`degrade.scope_shape()` resamples each scope at its own length. Give it a target length and use
`min(n_IS, n_OOS)` for both:

```python
def scope_shape(source, positions, kind, model, block, metric, cfg, size=None):
    ...
    got = engine.sequential(engine.payload(cut), kind, model, block,
                            cfg["global"]["n_sims"], cfg, size=size)
```

This requires `draws.*` to accept a `size` that differs from the number of trades available, which
`iid_bootstrap` and `block_bootstrap` already support naturally (they draw with replacement) and
`iid_shuffle` and `block_shuffle` cannot (they are permutations). **So the equal-length comparison is
available for the bootstrap families B, C and D, and not for A.** For Family A, compare instead on the
length-normalised statistic `dd_pct / √n`, which is the §P3 scaling, and say that is what is plotted.

### 9.5 Cost and spread totals — convenience for V4

`V4` can be recovered in closed form from Family C's `keep` (§4/V4), but storing the two sums removes
the algebra and the modelling asymmetry from the reading path:

```python
# in run.analyse
"costs": {"charged": float(source["cost"].sum()),
          "spread": float(source["spread"].sum()),
          "cushion": float(source["pnl"].sum() / source["cost"].sum()),
          "spread_cushion": float(source["pnl"].sum() / source["spread"].sum())}
```

### 9.6 One recalibration run

After §9.1–§9.5, re-run the whole reference databank and re-measure every firing rate in this
document. Four of the constants here were set by measuring candidate rules against this population
and rejecting the versions that killed 50–94% of it (P4, §5.1); the same measurement must be repeated
whenever the numbers feeding the rules change. The companion document's Appendix B notes that the
Family D columns of the last full run predate three configuration changes and were never re-measured —
that is exactly the gap this step closes.

---

## 10. The decision procedure

The whole document as one algorithm. The agent executes this and nothing else.

```
INPUT: result (the full result object for one strategy), cfg, dd_budget

# ---- Layer 0: is the analysis fit to decide on? ----------------------------
for check in [A1..A8]:
    if failed(check):
        record(check)
        if check == A6:  return HOLD, "A6", "draw model is broken - do not decide"
        if check in [A1, A2, A3]:  return HOLD, check, value
        # A4, A5, A7, A8 disable specific axes rather than the whole decision
        disable_axes(check)

# ---- compute the primitives (§2) ------------------------------------------
for scope in [IS, OOS]:
    SR, g3, g4, V, SE, n, years  <- §2.1, §2.2
    ann_SR[scope] = SR[scope] * sqrt(n[scope] / years[scope])

z_decay   = (SR[IS] - SR[OOS]) / sqrt(V[IS]/n[IS] + V[OOS]/n[OOS])
retention = SR[OOS] / SR[IS]
SR_trim   = symmetric 1% trim of OOS trades                      (§4/V7)
rank_iid  = result.A.runs["iid_shuffle"].dd_pct.rank             (§4/V3)
rank_blk  = result.A.runs["block_shuffle/<max>"].dd_pct.rank
Q, I2     = Cochran over result.D.nonoverlapping                 (§4/V5)
cushions  = from result.costs, or in closed form from Family C   (§4/V4)

# ---- Layer 1: the vetoes (§4) ---------------------------------------------
fired = []
if SR[OOS] <= 0 or PF[OOS] <= 1.0:                        fired += [V1]
if z_decay > 2.326 and ann_SR[OOS] < 0.50:                fired += [V2]
if rank_iid <= 0.05 and rank_blk <= 0.05:                 fired += [V3]
if cost_cushion < 1.5 or spread_cushion < 2.0:            fired += [V4]
if Q_pvalue < 0.05 and I2 > 0.50:                         fired += [V5]
if best_share_gross > 0.15 or eff_winners < 25:           fired += [V6]
if SR_trim <= 0:                                          fired += [V7]

if any axis needed by a veto was disabled at Layer 0 and that veto did not fire:
    that veto's outcome is HOLD, not PASS        # absence of evidence is not evidence

# ---- Layer 2: the score (§5) ---------------------------------------------
SCORE = 0.35*S1 + 0.25*S2 + 0.15*S3 + 0.15*S4 + 0.10*S5

# ---- Layer 3: sizing (§6) -----------------------------------------------
risk_scale     = dd_budget / result.A.dd_pct_99
risk_per_trade = risk_scale * cfg.global.risk_per_trade

# ---- the verdict --------------------------------------------------------
if fired non-empty:        return KILL,    binding = fired[0], evidence = fired
elif any HOLD outcome:     return HOLD,    binding = that check
elif SCORE >= 45:          return ADVANCE, evidence = SCORE and its five terms
else:                      return HOLD,    "below the batch cut, not fragile"
```

**Reporting.** For every strategy, output the decision, the binding rule with its value and limit,
every rule that fired, the five sub-scores, `risk_per_trade`, and the five degradation numbers of
§7.1. For a KILL, name **all** vetoes that fired, not the first — a strategy killed by V2 alone is a
candidate for revisiting with a regime filter, while one killed by V2, V3 and V5 together is not.

### 10.1 What this produces on the reference population

| decision | count | share |
|---|---|---|
| **ADVANCE** (no veto, SCORE ≥ 45) | 7 | 19% |
| **HOLD** (no veto, SCORE < 45) | 9 | 25% |
| **KILL** (≥ 1 veto) | 20 | 56% |

against the current system's 33 FAIL, 3 MARGINAL, 0 pass. The seven that advance, ranked:

| rank | strategy | SCORE | ann OOS SR | retention | z decay | I² | cost cushion | current verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | Strategy 21.30.24 | 75.5 | 0.76 | 0.68 | 0.66 | 0.00 | 2.50 | FAIL (47.8) |
| 2 | Strategy 21.28.44 | 72.8 | 0.76 | 0.75 | 0.46 | 0.03 | 2.51 | FAIL (48.2) |
| 3 | Strategy 20.5.40 | 54.3 | 0.54 | 0.53 | 0.90 | 0.00 | 2.21 | FAIL (43.4) |
| 4 | Strategy 1.17.44 | 52.5 | 0.52 | 0.54 | 0.84 | 0.06 | 2.11 | FAIL (38.8) |
| 5 | Strategy 24.17.35 | 52.2 | 0.44 | 0.41 | 1.15 | 0.00 | 2.68 | FAIL (42.9) |
| 6 | Strategy 17.18.29 | 51.9 | 0.53 | 0.35 | 1.88 | 0.40 | 3.57 | MARGINAL (61.1) |
| 7 | Strategy 21.35.36 | 50.4 | 0.49 | 0.47 | 1.03 | 0.10 | 2.24 | FAIL (44.3) |

**Read this honestly.** Seven strategies advance, and the best of them has an annualised
out-of-sample Sharpe of 0.76 over a single five-year regime — respectable, not remarkable, and not
statistically certified by that sample (`t_OOS` = 1.73). The criteria are not claiming these seven are
good. They are claiming these seven are the ones whose *out-of-sample* performance is positive,
broad-based, not order-luck, not regime-confined, and able to absorb worse costs — and that the rest
either fail one of those outright or rank below them. That is the strongest claim this data supports (P1).

---

---

## 11. What Monte Carlo may assume from upstream

The module's README places this study **after** the IS/OOS decay test and the cross-market retest.
That changes what the criteria are for, and it changes every firing rate quoted above — so it is
stated here explicitly rather than left implicit.

### 11.1 The reference population was not filtered, and the rates above reflect that

All firing rates in §3–§5 are measured on the **raw** 36-strategy databank. That databank was clearly
not pre-filtered: 30 of 36 arrive with retention below 0.40, and 10 arrive with a negative
out-of-sample Sharpe. **Every rate above is therefore an upper bound on what the rules will do to a
properly filtered input.**

### 11.2 What survives the decay test, reconstructed

The decay test, as the companion document describes it, keeps a strategy when its OOS Sharpe is
distinguishable from zero on its own standard error, it won in most OOS years separately, and no
single quarter carries the result. Reconstructing those three legs on the same 36 strategies:

| leg of the decay test | passes |
|---|---|
| OOS t-statistic ≥ 1.0 | 7 / 36 |
| majority of the 5 OOS years positive | 19 / 36 |
| no single quarter above 50% of OOS profit, **measured against gross** | 36 / 36 |
| **all three** | **7 / 36 (19%)** |

**The t-statistic leg is the only one that binds**, and where it is set decides everything
downstream:

| upstream cut | reach Monte Carlo | vetoes fire on | ADVANCE at SCORE ≥ 45 |
|---|---|---|---|
| t_OOS ≥ 0 (sign only) | 18 / 36 | 6 of 18 — V2×4, V5×3, V3×2, V7×1 | 7 of 18 (39%) |
| t_OOS ≥ 0.5 | 13 / 36 | 3 of 13 — V2×3, V5×2 | 7 of 13 (54%) |
| t_OOS ≥ 1.0 | 7 / 36 | **0 of 7** | 6 of 7 (86%) |
| t_OOS ≥ 1.645 | 2 / 36 | 0 of 2 | 2 of 2 (100%) |

**At t_OOS ≥ 1.0 the seven vetoes fire on nothing.** The decay test has already removed every
strategy they would have caught, and Monte Carlo's contribution collapses to the ranking score.

### 11.3 The recommended division of labour

The two stages should not both be level filters. They see different things:

- **The decay test sees the level and the calendar** — is there an out-of-sample edge at all, was it
  present across years. It cannot see order luck, cost cushion, regime heterogeneity or tail
  dependence, because those need the resampling this module does.
- **Monte Carlo sees the structure** — V3 (order luck), V4 (cost cushion), V5 (regime
  heterogeneity), V6 (concentration) and V7 (tail dependence) are questions no upstream stage
  answers, and they are why a strategy should still pass through here after being kept.

**Recommendation: cut upstream at `t_OOS ≥ 0.5`, not at 1.0.** Two reasons, both measured:

1. A cut at 1.0 discards 29 of 36 on a single statistic computed on one regime draw. By §4/V1's power
   arithmetic, `P(t_OOS < 1.0)` for a strategy whose *true* annualised OOS Sharpe is 0.75 is about
   28% — so roughly one good strategy in four is thrown away by that leg alone, with no chance to be
   seen by any of the structural tests.
2. At 0.5 the vetoes still do real work (3 of 13), so the two stages are complementary rather than
   nested. At 1.0 they are nested, and the second stage is decorative.

If instead the upstream cut stays at 1.0, then **V1 and V2 should be dropped from this document** —
they are dead weight on that input — and the criteria become V3–V7 plus the score. Keeping a veto
that provably cannot fire violates P7 as surely as keeping one that always fires.

### 11.4 A defect in the upstream test worth fixing

The quarter-concentration leg is the P4 trap (§1) in another module. Measured both ways on the same
36 strategies:

| best OOS quarter, as a share of… | min | median | max | fails a 50% rule |
|---|---|---|---|---|
| **net** OOS profit | 0.22 | 0.71 | **42.64** | 17 / 36 |
| **gross** OOS profit | 0.15 | 0.23 | 0.38 | 0 / 36 |

Over 20 quarters an even split gives 5% each, so a best quarter at 23% of gross is mild concentration
and 0 of 36 strategies are anywhere near a 50% rule. With the **net** denominator the same quantity
reaches 42.64 — a strategy whose best quarter is forty-two times its total out-of-sample profit,
which says only that its total is near zero. **A 50% rule on the net denominator rejects 17 of 36
strategies for having small net profit while calling it concentration.**

If the decay test uses the net denominator, it is rejecting on an artefact and the fix is one
division. This is a finding about that module, not this one, and it is recorded here because it was
measured here.

---

## Appendix A — the reference population, strategy by strategy

All 36 strategies of databank `Results`, project `XAUUSD`, export `2026-09-03`. Sorted by decision
then SCORE. `fired` lists the vetoes; `old tier`/`old comp` are the current system's verdict for
comparison. Retention, `z decay`, `perm rank`, `luck`, `I²`, `het p` and the cushions were computed
directly from the trade files for this document; `SCORE` and `decision` are §5 and §10.

| strategy | n IS | n OOS | SR IS | SR OOS | ann OOS | trim ann OOS | retention | z decay | perm rank | luck | I² | het p | cost cush | spread cush | OOS pf5 | SCORE | decision | fired | old tier | old comp |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Strategy 21.30.24 | 929 | 435 | 0.1191 | 0.0813 | 0.76 | 0.79 | 0.68 | 0.66 | 0.146 | 1.27 | 0.00 | 0.551 | 2.50 | 5.56 | 1.022 | 75.5 | ADVANCE | — | FAIL | 47.8 |
| Strategy 21.28.44 | 780 | 371 | 0.1169 | 0.0877 | 0.76 | 0.87 | 0.75 | 0.46 | 0.532 | 0.98 | 0.03 | 0.403 | 2.51 | 5.26 | 1.018 | 72.8 | ADVANCE | — | FAIL | 48.2 |
| Strategy 20.5.40 | 1,073 | 496 | 0.1018 | 0.0539 | 0.54 | 0.50 | 0.53 | 0.90 | 0.462 | 1.02 | 0.00 | 0.786 | 2.21 | 5.30 | 0.947 | 54.3 | ADVANCE | — | FAIL | 43.4 |
| Strategy 1.17.44 | 1,012 | 458 | 0.1001 | 0.0543 | 0.52 | 0.43 | 0.54 | 0.84 | 0.221 | 1.20 | 0.06 | 0.379 | 2.11 | 4.11 | 0.928 | 52.5 | ADVANCE | — | FAIL | 38.8 |
| Strategy 24.17.35 | 958 | 489 | 0.1083 | 0.0439 | 0.44 | 0.58 | 0.41 | 1.15 | 0.227 | 1.19 | 0.00 | 0.652 | 2.68 | 5.66 | 0.918 | 52.2 | ADVANCE | — | FAIL | 42.9 |
| Strategy 17.18.29 | 690 | 292 | 0.1997 | 0.0697 | 0.53 | 0.69 | 0.35 | 1.88 | 0.346 | 1.10 | 0.40 | 0.124 | 3.57 | 6.12 | 0.926 | 51.9 | ADVANCE | — | MARGINAL | 61.1 |
| Strategy 21.35.36 | 862 | 411 | 0.1151 | 0.0535 | 0.49 | 0.56 | 0.47 | 1.03 | 0.329 | 1.12 | 0.10 | 0.353 | 2.24 | 4.46 | 0.949 | 50.4 | ADVANCE | — | FAIL | 44.3 |
| Strategy 24.19.23 | 1,060 | 527 | 0.1499 | 0.0449 | 0.46 | 0.61 | 0.30 | 1.97 | 0.537 | 0.98 | 0.47 | 0.078 | 3.30 | 6.01 | 0.934 | 44.4 | ADVANCE | — | FAIL | 50.6 |
| Strategy 24.22.43 | 1,025 | 520 | 0.1087 | 0.0320 | 0.33 | 0.47 | 0.29 | 1.41 | 0.099 | 1.33 | 0.01 | 0.418 | 2.51 | 5.00 | 0.885 | 43.1 | ADVANCE | — | FAIL | 38.6 |
| Strategy 22.2.30 | 842 | 452 | 0.1090 | 0.0280 | 0.27 | 0.24 | 0.26 | 1.39 | 0.372 | 1.08 | 0.00 | 0.958 | 2.84 | 4.62 | 0.871 | 35.4 | HOLD-LOW | — | FAIL | 37.1 |
| Strategy 23.32.31 | 974 | 504 | 0.0989 | 0.0203 | 0.20 | 0.32 | 0.21 | 1.42 | 0.205 | 1.22 | 0.00 | 0.481 | 2.20 | 4.40 | 0.868 | 32.4 | HOLD-LOW | — | FAIL | 33.4 |
| Strategy 7.13.36 | 988 | 497 | 0.0981 | 0.0181 | 0.18 | 0.28 | 0.18 | 1.46 | 0.452 | 1.03 | 0.00 | 0.661 | 1.90 | 5.38 | 0.846 | 29.0 | HOLD-LOW | — | FAIL | 35.0 |
| Strategy 14.16.34 | 932 | 467 | 0.1075 | 0.0233 | 0.23 | 0.10 | 0.22 | 1.50 | 0.548 | 0.97 | 0.14 | 0.325 | 1.97 | 4.96 | 0.889 | 27.2 | HOLD-LOW | — | FAIL | 36.9 |
| Strategy 17.25.27 | 1,204 | 566 | 0.1132 | 0.0201 | 0.21 | 0.16 | 0.18 | 1.85 | 0.095 | 1.35 | 0.48 | 0.072 | 2.39 | 4.44 | 0.876 | 27.2 | HOLD-LOW | — | FAIL | 35.3 |
| Strategy 7.14.26 | 890 | 453 | 0.0970 | 0.0051 | 0.05 | 0.01 | 0.05 | 1.60 | 0.055 | 1.44 | 0.00 | 0.638 | 1.88 | 4.36 | 0.815 | 21.0 | HOLD-LOW | — | FAIL | 29.0 |
| Strategy 17.29.43 | 729 | 337 | 0.1436 | 0.0004 | 0.00 | 0.06 | 0.00 | 2.21 | 0.170 | 1.24 | 0.29 | 0.210 | 2.16 | 4.19 | 0.783 | 13.5 | HOLD-LOW | — | FAIL | 40.4 |
| Strategy 17.17.41 | 901 | 439 | 0.1757 | 0.0439 | 0.41 | 0.34 | 0.25 | 2.38 | 0.071 | 1.38 | 0.42 | 0.114 | 3.00 | 4.93 | 0.910 | 39.1 | KILL | V2 | MARGINAL | 55.9 |
| Strategy 19.21.30 | 725 | 336 | 0.1500 | 0.0269 | 0.22 | 0.29 | 0.18 | 1.89 | 0.029 | 1.49 | 0.00 | 0.430 | 2.49 | 4.99 | 0.838 | 34.0 | KILL | V3 | FAIL | 45.1 |
| Strategy 17.27.43 | 760 | 370 | 0.1761 | 0.0253 | 0.22 | 0.13 | 0.14 | 2.48 | 0.006 | 1.62 | 0.61 | 0.018 | 3.52 | 5.57 | 0.845 | 29.9 | KILL | V2,V3,V5 | MARGINAL | 50.9 |
| Strategy 18.28.28 | 892 | 425 | 0.1930 | 0.0249 | 0.23 | 0.12 | 0.13 | 2.99 | 0.218 | 1.18 | 0.63 | 0.013 | 3.37 | 5.23 | 0.876 | 26.7 | KILL | V2,V5 | FAIL | 58.8 |
| Strategy 16.20.43 | 863 | 424 | 0.1803 | 0.0248 | 0.23 | 0.25 | 0.14 | 2.70 | 0.144 | 1.26 | 0.64 | 0.011 | 2.66 | 4.09 | 0.864 | 24.2 | KILL | V2,V5 | FAIL | 53.7 |
| Strategy 21.19.37 | 1,165 | 557 | 0.1322 | 0.0158 | 0.17 | -0.06 | 0.12 | 2.35 | 0.006 | 1.66 | 0.30 | 0.197 | 2.42 | 4.17 | 0.862 | 22.2 | KILL | V2,V3,V7 | FAIL | 43.3 |
| Strategy 15.24.36 | 1,131 | 543 | 0.1248 | 0.0146 | 0.15 | -0.00 | 0.12 | 2.19 | 0.070 | 1.39 | 0.28 | 0.212 | 2.34 | 4.07 | 0.857 | 21.8 | KILL | V7 | FAIL | 42.9 |
| Strategy 18.27.27 | 1,312 | 624 | 0.1290 | 0.0173 | 0.19 | 0.15 | 0.13 | 2.35 | 0.182 | 1.24 | 0.49 | 0.069 | 2.33 | 3.97 | 0.878 | 21.4 | KILL | V2 | FAIL | 44.7 |
| Strategy 22.16.41 | 884 | 396 | 0.1453 | 0.0109 | 0.10 | 0.13 | 0.07 | 2.23 | 0.495 | 1.00 | 0.71 | 0.002 | 3.15 | 5.91 | 0.829 | 18.7 | KILL | V5 | FAIL | 46.4 |
| Strategy 18.22.27 | 737 | 349 | 0.1522 | -0.0044 | -0.04 | -0.06 | -0.03 | 2.47 | 0.275 | 1.15 | 0.04 | 0.399 | 2.55 | 4.92 | 0.768 | 15.6 | KILL | V1,V2,V7 | FAIL | 47.8 |
| Strategy 24.26.26 | 836 | 431 | 0.1056 | 0.0064 | 0.06 | -0.03 | 0.06 | 1.69 | 0.422 | 1.06 | 0.00 | 0.552 | 1.57 | 4.01 | 0.813 | 15.2 | KILL | V7 | FAIL | 29.3 |
| Strategy 22.13.34 | 809 | 384 | 0.1231 | -0.0013 | -0.01 | 0.08 | -0.01 | 2.01 | 0.702 | 0.86 | 0.52 | 0.053 | 2.99 | 5.31 | 0.805 | 13.9 | KILL | V1 | FAIL | 37.9 |
| Strategy 6.22.30 | 823 | 437 | 0.0995 | -0.0074 | -0.07 | -0.14 | -0.07 | 1.80 | 0.434 | 1.05 | 0.27 | 0.225 | 1.53 | 4.29 | 0.770 | 10.0 | KILL | V1,V7 | FAIL | 25.6 |
| Strategy 10.15.25 | 1,057 | 516 | 0.1025 | -0.0091 | -0.09 | 0.00 | -0.09 | 2.10 | 0.213 | 1.21 | 0.21 | 0.269 | 1.75 | 2.82 | 0.807 | 9.1 | KILL | V1 | FAIL | 31.1 |
| Strategy 6.13.33 | 837 | 430 | 0.0954 | -0.0249 | -0.23 | -0.36 | -0.26 | 2.03 | 0.500 | 1.00 | 0.17 | 0.301 | 1.08 | 3.32 | 0.759 | 6.8 | KILL | V1,V4,V7 | FAIL | 23.1 |
| Strategy 16.21.23 | 720 | 330 | 0.1331 | -0.0076 | -0.06 | -0.02 | -0.06 | 2.14 | 0.486 | 1.01 | 0.52 | 0.050 | 1.93 | 3.51 | 0.749 | 5.7 | KILL | V1,V5,V7 | FAIL | 39.3 |
| Strategy 20.23.30 | 768 | 370 | 0.1242 | -0.0520 | -0.45 | -0.40 | -0.42 | 2.82 | 0.462 | 1.03 | 0.20 | 0.281 | 1.59 | 3.17 | 0.675 | 5.7 | KILL | V1,V2,V7 | FAIL | 28.0 |
| Strategy 2.13.39 | 966 | 490 | 0.1030 | -0.0524 | -0.52 | -0.69 | -0.51 | 2.81 | 0.811 | 0.78 | 0.26 | 0.228 | 1.13 | 3.57 | 0.707 | 5.4 | KILL | V1,V2,V4,V7 | FAIL | 23.6 |
| Strategy 8.11.37 | 812 | 419 | 0.1167 | -0.0301 | -0.28 | -0.41 | -0.26 | 2.46 | 0.701 | 0.87 | 0.44 | 0.095 | 1.37 | 3.99 | 0.733 | 5.0 | KILL | V1,V2,V4,V7 | FAIL | 24.3 |
| Strategy 1.25.34 | 946 | 457 | 0.0976 | -0.0348 | -0.33 | -0.46 | -0.36 | 2.36 | 0.865 | 0.74 | 0.15 | 0.312 | 1.12 | 2.70 | 0.705 | 4.3 | KILL | V1,V2,V4,V7 | FAIL | 21.3 |

## Appendix B — population quantiles of every gated quantity

| quantity | min | p5 | p25 | median | p75 | p95 | max |
|---|---|---|---|---|---|---|---|
| `n_OOS` | 292 | 334 | 393 | 438 | 496 | 559 | 624 |
| `sr_IS` | 0.0954 | 0.0974 | 0.1029 | 0.1168 | 0.1440 | 0.1834 | 0.1997 |
| `sr_OOS` | -0.0524 | -0.0391 | -0.0020 | 0.0191 | 0.0350 | 0.0726 | 0.0877 |
| `ann_IS` | 0.873 | 0.913 | 1.012 | 1.095 | 1.338 | 1.671 | 1.824 |
| `ann_OOS` | -0.5189 | -0.3624 | -0.0175 | 0.1995 | 0.3489 | 0.5936 | 0.7614 |
| `oos_ann_sym` | -0.6904 | -0.4199 | -0.0270 | 0.1291 | 0.3640 | 0.7174 | 0.8667 |
| `t_OOS` | -1.142 | -0.806 | -0.039 | 0.445 | 0.781 | 1.341 | 1.733 |
| `hl` | -0.5084 | -0.3724 | -0.0149 | 0.1361 | 0.2660 | 0.5774 | 0.7504 |
| `z_degrade` | 0.464 | 0.793 | 1.446 | 1.991 | 2.354 | 2.811 | 2.986 |
| `p_degrade` | 0.0014 | 0.0025 | 0.0093 | 0.0233 | 0.0741 | 0.2146 | 0.3213 |
| `rank` | 0.006 | 0.023 | 0.146 | 0.302 | 0.488 | 0.729 | 0.865 |
| `luck_ratio` | 0.739 | 0.843 | 1.007 | 1.137 | 1.265 | 1.522 | 1.662 |
| `skew_ratio` | 1.535 | 1.547 | 1.568 | 1.578 | 1.585 | 1.604 | 1.622 |
| `het_I2` | 0.000 | 0.000 | 0.005 | 0.203 | 0.451 | 0.632 | 0.710 |
| `het_p` | 0.002 | 0.012 | 0.091 | 0.275 | 0.421 | 0.692 | 0.958 |
| `het_n_neg` | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 2.000 | 3.000 |
| `cost_cushion` | 1.083 | 1.125 | 1.895 | 2.334 | 2.666 | 3.405 | 3.568 |
| `spread_cushion` | 2.695 | 3.086 | 4.052 | 4.448 | 5.272 | 5.932 | 6.119 |
| `oos_pf5` | 0.675 | 0.707 | 0.800 | 0.859 | 0.894 | 0.966 | 1.022 |
| `oos_best_gross` | 0.0213 | 0.0220 | 0.0265 | 0.0278 | 0.0327 | 0.0374 | 0.0459 |
| `oos_eff_winners` | 71 | 73 | 92 | 105 | 115 | 135 | 138 |
| `oos_win_rate` | 0.407 | 0.433 | 0.450 | 0.483 | 0.491 | 0.514 | 0.528 |
| `pf_IS` | 1.307 | 1.334 | 1.353 | 1.403 | 1.526 | 1.729 | 1.804 |
| `pf_OOS` | 0.866 | 0.893 | 0.994 | 1.055 | 1.104 | 1.225 | 1.269 |
| `dd_pct_99` | 0.0524 | 0.0544 | 0.0908 | 0.1258 | 0.1715 | 0.2291 | 0.2701 |
| `tpy` | 66 | 71 | 82 | 89 | 99 | 116 | 129 |

## Appendix C — every constant in one place

| id | constant | value | fires on the reference population | tune? |
|---|---|---|---|---|
| A2 | minimum `n_OOS` to decide | 200 | 0/36 | from `confidence.percentile`, not free |
| A2 | minimum `n_OOS` to say anything | 60 | 0/36 | no |
| A5 | `stability.worst_spread` tolerance | 0.10 | — | existing config |
| A7 | volatility coverage floor | 0.95 | 0/36 | no |
| V1 | OOS Sharpe floor | 0.0 | 10/36 | **no — it is a sign test** |
| V1 | OOS profit factor floor | 1.0 | 10/36 | no |
| V2 | `z_decay` threshold | 2.326 (p<0.01) | 11/36 with the floor | **the sensitive one: 24/36 at p<0.05, 4/36 at p<0.005** |
| V2 | landing floor `ann_SR_OOS` | **0.60** | inert 0.50–0.80 here (§4/V2) | yes, but it does nothing on this population |
| V3 | permutation rank threshold | 0.05 | 3/36 | no — it is a p-value |
| V4 | `cost_cushion` floor | 1.5 | 4/36 | yes, with the asset |
| V4 | `spread_cushion` floor | 2.0 | 0/36 | yes, with the asset |
| V5 | Cochran `Q` p-value | 0.05 | 5/36 (with I²) | no — it is a p-value |
| V5 | `I²` threshold | 0.50 | 5/36 (with Q) | yes |
| V6 | best trade / gross profit | 0.15 | 0/36 | yes, with trade frequency |
| V6 | effective winners floor | 25 | 0/36 | yes, with trade frequency |
| V7 | symmetric trim fraction | 1% each tail | 11/36 | no |
| S1–S5 | weights | 0.35/0.25/0.15/0.15/0.10 | — | yes |
| §5.2 | SCORE cut | **45** | 7/36 advance | **yes — set by throughput** |
| §6 | drawdown budget | caller's choice | — | yes |

**Removed from the current system:** `dd_99` (P5), `inflation` and `inflation_watch` (P6), `windows`
(§8.2), `dead_block` (superseded by V5), pooled `psr` as a gate (§7.2).

## Appendix D — the traps, as a checklist

Run through this before trusting any number in a Monte Carlo report.

1. **Is the denominator near zero?** Any ratio to OOS net profit is suspect. Use gross profit, or an
   absolute form. (P4 — four rules were rejected on this.)
2. **Are the two samples the same length?** `n_IS ≈ 2.3 · n_OOS`. Net profit and drawdown are not
   comparable across them without normalisation. (P3)
3. **Is this percentile floor secretly a significance test?** A 5th-percentile floor on net or profit
   factor demands `SR > 1.645/√n`. Compute what that is at the sample size in hand before believing
   it measures robustness. (§5.1)
4. **Is the statistic pooled when it should be scoped?** A pooled number on this population is ~70%
   in-sample, and in-sample is selection-inflated. (P2)
5. **Does this threshold fire on everything, or nothing?** Check the firing rate before reading any
   meaning into the flag. (P7 — `inflation_watch` 36/36, `windows` 36/36, `inflation` 0/36)
6. **Is the number annualised on the right trade rate?** Per scope, never pooled. (§2.2)
7. **Is a negative period a finding, or arithmetic?** ~30% of stationary strategies show a negative
   24-month block by chance. Test the heterogeneity; do not count the negatives. (V5)
8. **Is a low drawdown skill, or the ordering?** Read the permutation rank, not the inflation ratio.
   (P6, V3)
9. **Are the two Family C `keep` values comparable?** No. `cost_shock` charges the increment,
   `spread_widen` charges the whole spread on top of a net P&L. Compare cushions. (V4)
10. **Is drawdown being used to disqualify?** It must not be. It sets the risk per trade. (P5, §6)
