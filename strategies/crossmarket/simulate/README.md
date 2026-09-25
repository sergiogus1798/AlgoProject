# crossmarket/simulate — what are the numbers, under a given model?

The execution layer: it prices runs, real and random, and computes every statistic the study
reports. It **chooses no model** — the model arrives as a key from `config.yaml` — and it **judges
nothing**: every number here is handed on with no threshold applied to it.

**Imports from:** `inputs/`, `mechanics/`, `engines/nulls/placement`, itself, and `verdict/fieller` (one declared
exception, below)
**Consumed by:** `views.py`, `render/`, `explorer/`
**Must not contain:** a threshold, a warning's wording, a pass/fail, or any HTML

| file | what it does | run it | in → out |
|---|---|---|---|
| `backtest.py` | Prices the real run and N random ones identically, in dollars, in batches | imported | fixed + bars + model → table, shapes, cone |
| `realrun.py` | The real backtest's own statistics — over **everything SQX reported** and over the grid-locatable subset, which are not the same population — and the mechanical checks | imported | fixed + bars → stats, checks |
| `metrics.py` | **What a run is worth.** Net, drawdown, Ret/DD, Sharpe, PF and the losing run of thousands of runs at once, each with its own good side | imported | P&L matrix → statistics |
| `sweep.py` | **The window sweep.** Calendar blocks of each size, the trades and free room in each, and a free-placement model confined to them | imported | bars + trades + model → blocks, entries, holds |
| `stress.py` | Cost gradient, breakeven cost multiple, and decay under a bar shift or range slippage | imported | fixed + bars → cost/slippage curves |
| `exposure.py` | **Test 1c.** Drift-neutral excess A with a hold-weighted bootstrap CI, its risk-normalised form, and concentration E with a Fieller interval | imported | fixed + bars → A, E |
| `paired.py` | **Test 1b.** Each trade against the exact mean of every window of its own length, near it in time — a centered window or the regime block, and the test is run under both | imported | fixed + bars → alpha, Wilcoxon p |
| `portfolio.py` | **The Portfolio tab.** Every market as one account, what each one adds to it, how often they overlapped, and two ways of asking how much is luck | imported | streams → account, marginal |
| `joint.py` | **The joint null.** One a-priori statistic over the out-of-sample markets and one p, pooled from draws that displace every market together | imported | runs → joint p |
| `fingerprint.py` | Behavioural fingerprint against the base asset: holding-time KS, MAE/MFE by ATR, return shape, MFE capture, and the four overlaid histograms | imported | trades + bars → fingerprint |
| `correlation.py` | Weekly equity curves and their correlation matrix across a strategy's markets plus the base asset | imported | curves → correlation |

`correlation.py` and `fingerprint.py` are here and not in `verdict/` on one test: **neither reads a
threshold from `cfg` and neither emits a named warning.** They produce statistics — a matrix, a KS
statistic, an excursion profile — and hand them on. `fingerprint.py` says so in its own first line:
descriptive, against the base asset, never against chance.

**The one declared import exception** is `exposure.py → verdict/fieller`. `fieller.interval()` is the
primitive with which `exposure` produces its own headline number E; it is the same carve-out
`monteCarlo/simulate` declares for `verdict/confidence`. It is the only arrow out of this layer that
points backwards, and a `grep` proves it:

```bash
grep -rn "from strategies.crossmarket" simulate/ | grep -vE "crossmarket\.(inputs|mechanics|model|simulate)"
```

## What a random run is worth, and in what unit

`metrics.py` computes the same eight statistics for the real backtest and for every random one, plus
`mean_r` — the mean log return per trade over the market's median ATR, which is the one figure that
compares across markets. Each carries its own direction: for `dd` and `losing_run` a **small p means
the real run suffered less** than chance, the opposite of how `net` reads, and the tables say so on
every row.

Column k of a random run reuses real trade k's **size and charged cost**. So a random run is the same
money at risk, paying the same broker, differing only in when it entered. The wrap-around in
`backtest.price()` is there for a model that draws more trades than there really were; none ships
today, and `POSSIBLE_IMPROVEMENTS.md` §1 still lists varying the trade count as worth trying.

**Every random run is priced in dollars, with the real trades' own sizes and costs.** That is what
lets the study report net profit, drawdown, Ret/DD, Sharpe and profit factor rather than one abstract
statistic: measured, the P&L reconstructed from the bars correlates **0.9996** with the P/L SQX
itself reported, so the real equity curve on the panel is SQX's own.

## The panel reports more trades than the tests use, on purpose

🔬 Found 2026-09-16 by the owner, comparing `Strategy 24.7.38` against SQX: the panel showed 2,089
trades on gold where the databank had 2,142. `envelope.occupancy()` keeps a trade only when
`exit > entry`, and **1,695 of the databank's 92,329 trades open and close inside one bar** —
zero-duration `Exit Signal` exits, `Time in trade` of `0s`. Five more fall before the first bar of
their file. 1.84% overall; 9.8% on the worst pair, `Strategy 8.16.41(1)` on silver.

Dropping them from the **tests** is right and stays. Dropping them from the **reported backtest** was
a defect — their P&L is real, so net profit, drawdown, profit factor and the trade count were all
quietly short of what SQX said. Both are now computed and both are shown:

| what | from | used by |
|---|---|---|
| `realrun.reported()` | **every** trade SQX reported, in close-time order | the master table, the equal-risk table, the equity curves, the portfolio |
| `realrun.real()` | the trades the bar grid can hold | the null comparison, where the real run and its random counterparts must be the same trades |

🔬 Verified on `Strategy 24.7.38`: the panel's net equals the sum of the export's own `Profit/Loss`
column to the cent on all three markets. The master table prints both counts, a note under it says
why they differ, and `diagnostics.min_on_grid` (0.95) raises the `off_grid` warning when the gap is
large enough to change how a p-value should be read.

## Which null is hardest to beat, measured

🔬 With the window bounded, `block_shift` returns the **lowest p in 7 of 8** (strategy, market) pairs
and the **narrowest null in 5 of 8**. So it is usually, but not always, the one that flatters a
strategy most — and it is never the reason to trust a result. It is the *attributable* model: the
only one whose low p can be read as "the entry timing carried information" rather than "the run
happened to land somewhere kinder".

An earlier measurement, taken before the window was bounded, made the gap look far larger and
systematic (σ 0.073 against 0.095, lowest p everywhere). Most of that was the artefact: the other
three were roaming a third more sample than the real backtest ever touched. **Both readings are
recorded because the first one was published and acted on.**

The practical rule is unchanged: **a strategy that survives all four says more than one that survives
only `block_shift`**, and a lone `block_shift` pass is the weakest of the cases, not the strongest.

## The window sweep — how much of a free-placement p is regime

The three free-placement models destroy three things at once: the **regime** a trade lands in, its
**calendar**, and the **clustering**. `sweep.py` re-draws those three inside consecutive calendar
blocks of shrinking size (`sweep.windows`, default `full, 3y, 1y, 6m`): each block's real trades are
handed to the model as if the block were the whole window, and no trade may leave its block.
Shrinking the block hands back the regime and nothing else, so p against block size is a
decomposition:

| null | regime | calendar | clustering |
|---|---|---|---|
| free placement, full window | destroyed | destroyed | destroyed |
| free placement, shrinking window | ← restored | destroyed | destroyed |
| `block_shift` (reference, untouched) | kept | kept | kept |

p that stays low as the block shrinks is timing; p that climbs is a pass the regime was carrying.
**The curve never converges on `block_shift`**, which also keeps calendar and clustering: that is
another axis, drawn as a flat reference line, not a destination.

- **`full` is the model itself, draw for draw.** `sweep.confine()` with one block calls the model on
  the same arrays with the same generator. `tests/test_sweep.py` checks the arrays are identical, and
  on real data the swept p and σ matched `backtest.run()` to the last digit on 6 of 6 (model, market)
  pairs, so the panel reads the full point from the model's own run instead of drawing it twice.
- **Blocks are `envelope.blocks()`**, so `6m` is exactly the partition `block_shift` moves trades
  inside. The first and last block are usually partial. A trade's hold is capped at its block's end.
  Sizes are calendar durations; the tables print them in H1-equivalent bars, since the bars are M30.
- **Power is checked, not assumed** (`verdict/inference.sweep_power`). A block with fewer than
  `sweep.min_trades` real trades, or less than `sweep.min_free_share` of its bars free, is weak. A
  size whose weak blocks hold more than `sweep.max_weak_share` of the trades is **withheld** — drawn
  as a cross, never as a number — and a size under `sweep.min_months` is never computed.
- 🔬 **The live trade count moves with the size under two of the three models.** `resampled_holds` and
  `fitted_holds` draw a total time in market that can overflow a block, and what overflows is
  dropped; more blocks, more drops. Measured on XAGUSD, Strategy 1.10.80: 98.4% of trades live at
  full, 96.7% at 3y, 95.3% at 1y, 94.1% at 6m. `segment_permute` keeps its multiset and stays above
  99.6%. It is the one thing besides the regime that changes along the curve, which is why the count
  is printed beside every p.
- **The caption is not the reading.** `verdict/inference.sweep_trend()` compares the widest and the
  narrowest computed p: `regime` when p climbs more than `sweep.evidence_drop` orders of magnitude,
  `timing` otherwise, `no_pass` when no size reaches alpha, `unassessable` with fewer than two points.
- 🔬 **Measured**, 6 strategies × 2 markets × 3 models at 10,000 draws: 7 curves `timing`, 29
  `no_pass`, 0 `regime`. The one clear pass, Strategy 2.29.29 on XAGUSD, holds p between 0.0009 and
  0.0030 at every size. Strategy 14.15.26(2) climbs steadily as the block shrinks on both markets —
  Brent 0.075 → 0.117, silver 0.105 → 0.139 — which is the regime shape, just never under alpha.
  Strategy 15.17.41 on silver was withheld at 6m: 13% of its trades sit in weak blocks.
- **Every point is a full null, and every statistic is swept.** Each sweep point goes through the
  same `backtest.drawn()` + `backtest.summary()` as a null model, so it keeps the whole metric table,
  a histogram per metric and an equity cone.
- **It costs time**: nine more nulls per market, at full price. 🔬 Strategy 24.14.35 over two markets
  at the default 25,000 draws: **107 s**, against 36-52 s when the sweep priced one statistic, and
  about 25 s before there was a sweep at all.

`regime_strata` is the alternative the owner asked for alongside, built apart and off by default. It
shares nothing with the sweep and never runs inside it.

## What the tests compare, and what they cannot

The statistic is the **mean log return per trade, net of cost**, divided by one constant per market
(the median ATR as a fraction of price) so markets compare. That constant is identical for the real
run and every random run, so it cannot move a p-value — it only puts gold, silver and Brent on one
axis.

The earlier design divided each trade by the ATR **of its own entry bar**. That is wrong here and was
removed: real entries are chosen by the rule and random ones are not, so any filter that favours
compressed bars divides the real trade by a small number while the move that follows reverts to
normal volatility. It inflates the real statistic with no directional edge at all, in the direction
of passing. `atr_ratio` in every row is the diagnostic that would have caught it.

**Test 1b is the one that needs nothing.** No null model, no cost assumption — cost appears on both
sides of the difference and cancels. It is also the only test here whose reference is exact rather
than sampled: the mean of *every* window of that length near the trade, not a sample of them. The
source note's literal version — each trade against a passive long over the identical window — is
degenerate for this family: these strategies carry no stop and no target, so their trade return *is*
that passive long, and the difference would be zero by construction.

**What "near the trade" means, and why it is swept.** The reference used to be the fixed semester
partition `block_shift` moves trades inside. That partition has a defect nobody had written down: a
trade entering three days before a block ends is measured against a stretch that is almost entirely
past, and two trades a week apart across a boundary get *disjoint* references. `paired.reference`
now defaults to a **centered window** — every blind trade of the same length starting within
`±3 months` of the entry, by running mean, one pass per distinct hold. It reads bars after the entry
as well as before, which is fine: the reference is "what this market was paying around then", not a
rule anyone could have traded. Because the choice is a modelling decision and not a fact, **the test
is run under all of `paired.sensitivity` and the panel prints every one**: ±3m, ±6m, ±12m and the
block partition. 🔬 Measured on `Strategy 1.10.80`, Brent: p 0.749 / 0.677 / 0.667 / 0.753 and alpha
−5.3 / −4.7 / −4.7 / −5.2 bps across the four — the choice moves nothing on that pair, which is the
outcome to hope for and not the one to assume.

## Does it generalise? The joint null

The per-market tests ask whether the timing carried information *on that market*; the retest exists
to ask whether it carries **across** markets, and counting how many markets came in under alpha does
not answer that. Those p-values are dependent — same draws, markets that move together — so a vote,
a Fisher combination or a Stouffer one is anti-conservative exactly where it matters.

`joint.py` computes **one a-priori statistic and one p**: the equal-weight mean of `mean_r` over the
out-of-sample markets, against the same pooled mean on every draw. Equal weight because each market
is one vote that the edge generalises; weighting by trade count lets the busiest market decide alone.
The base asset is not in the pool — there a strategy beats its null by construction. 🔬 Measured on
`Strategy 24.14.35` at 3,000 draws over Brent and silver: pooled real `mean_r` **+0.1757** against a
null median of −0.0860, **p = 0.0010**, z = +3.36.

**What makes it correctly sized is the coupling, not the pooling.** 🔬 Until 2026-09-17 the draws
were independent across markets — the correlation between draw *d*'s `mean_r` on Brent and on silver
was **−0.0016** — because sharing `nulls.seed` couples nothing: every market builds its own generator
and consumes it at its own shape. `engines/nulls/placement/trade_models.semester_shift()` now draws the displacement of
each **calendar semester** from a generator keyed by that semester, so draw *d* moves 2013H1 the same
way everywhere. Measured after the change, 83.5% of draws displace a shared semester by exactly the
same number of weeks in both markets.

🔬 And the honest part: the per-draw correlation between the two markets' `mean_r` is still about
**−0.035** even coupled. These two markets' null statistics simply do not co-move much at the horizon
of these trades. That is not a reason to skip the joint null — its whole point is to be correctly
sized *whatever* the correlation turns out to be — but it does mean the joint p here is close to what
independence would have given, and saying otherwise would be selling it.

`joint.pool` chooses the scale. The default `mean_r` averages the raw statistic and is right while
the markets' null spreads sit within a small factor of each other — 🔬 measured 0.1236 against
0.1026, a factor of 1.20. Switch it to `z` when one market's spread is several times another's, or
that market decides the verdict on scale alone.

## Does adding a market break the portfolio?

The retest asks whether the edge transfers; `portfolio.py` asks the question that follows from it —
*oil and the Nasdaq need not be brilliant, but they must not wreck what gold does.* One account of
`equity.starting` for every market at once, the base asset included as the core position, and the
drawdown computed on the **combined** curve, never summed from the parts, as `portfolio/CLAUDE.md`
requires.

The table it exists for is **marginal contribution**: the whole portfolio, the portfolio without each
market, and the difference on every statistic. A market whose Δ Ret/DD is negative is costing the
combination more than it brings, however good its own p-value was. 🔬 Measured on `Strategy 2.29.29`:
gold +2.70, silver −0.19, Brent **−4.55**.

Two different ways of asking how much of it is luck, because they are not the same question:
**calendar-block resampling** (`portfolio.block_weeks`, default four weeks) draws whole weeks, so
every market's trades inside a block travel together and a week that was bad for two markets at once
stays bad for both — resampling single trades would destroy exactly the dependence being measured;
and **reordering**, delegated to `engines.resample.draws`, which leaves composition
untouched so net profit is invariant by construction and only the path statistics move.

It is one strategy in N markets, **not** N strategies: building the owner's real portfolio is
`portfolio/`, where `DECISIONS.md` still has the design open.

## Contracts and traps

- **`backtest.py` never chooses a model and never judges one.** The model arrives as a key; the
  verdict is `verdict/`'s and the owner's. That is what lets the same runs be re-judged, or the same
  judgement re-run under another model, without editing either.
- **`metrics.HIGHER_IS_BETTER` is not decoration.** For `dd` and `losing_run` a real run sitting high
  in its null means it drew down *worse* than chance, which reads the opposite way round from `net`.
  Anything that colours a cell has to read this, never assume it.
- **`metrics.TABLED` drops `trades` on purpose.** Every shipped model draws the real number of
  trades, so its "distribution" is one value and any pass/fail colouring on it would be noise.
- **`correlation.pca()` was removed on 2026-09-16 and is not to be reinstated from scratch**: with
  two or three streams PC1 is close to a function of the mean pairwise correlation, so it added an
  axis the matrix did not carry. It is recorded as *discarded with a reason* in
  `POSSIBLE_IMPROVEMENTS.md`.
- **`fingerprint.capture_ratio` measures the exit, not the entry**, which is why it lives there and
  not in `exposure.py`. A trade that never moved favourably has an undefined capture ratio, not an
  infinite one: 7 of 844 silver trades are such, and keeping them makes the mean ±inf while the
  median silently ignores the problem.
