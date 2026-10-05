# Portfolio — open decisions

Questions the owner has not settled yet. Nothing here is implemented; do not guess an answer.
Settled on 2026-09-29 and moved to the section «Settled by the owner» below: #1 (same pool), #3 (equal weight as the
baseline, pluggable weights), #7 (Monte Carlo of every kind), #8 (fixed fractional), #4 (every
correlation threshold 0.30 by default), #9 (siblings face the same filter, no special rule) and #11 (search `build`, test `oos1`+`oos2`). #10 (near-survivors enter, marked) was settled on 2026-09-30. #13 (the funded portfolio is chosen by the funded yardstick inside the engine) was settled on 2026-09-30 by the session, the owner having delegated it — `PLAN.md` §14. #2 (size), #5 (rebalancing) and #12 (no «on probation» category) were decided on 2026-10-04 by the Council on the owner's delegation, and #11 was amended the same day (how the two out-of-sample segments are read) — section «Decided by the Council» below. The readings those answers left open (R1-R4, Q16's sequence) were settled by the owner on 2026-10-05 — section below, `real.shift_minimum: metric` included.

| # | question | why it matters |
|---|---|---|
| 6 | Prop-firm rules to encode: daily loss, total drawdown, minimum days, consistency — and which firm (static or trailing DD, news windows). **Belongs to encargo 33 now** (owner, 2026-09-29): outright prohibitions filter the pool before the search, the rest is sizing after it | Encargo 33 (`docs/encargos/33-economia-del-fondeo.md`) answers it from data |

Answer one, and it moves from here into a settled section below.

## Settled by the owner — 2026-10-05 (the readings the Council's answers left open)

`PLAN.md` §12 «Readings the Council's answers leave open», items 1-7. Knobs in
`common/construct/config.yaml`, section `real`.

- **R1 — the GA's ranks are taken in the greedy seeds**: `real.rank_reference: seeds`.
- **R2 — P(losing year) is the share of calendar years of `build` that lose**: `real.losing_year: calendar`.
- **R3 — the search scores the shifted minimum**: each combination on `build` with its start
  shifted 0, 1, 2 and 3 months (`real.shift_months: 3`), the minimum kept; the whole window once
  is no longer a reading. **The minimum of what: `real.shift_minimum: metric`**
  (owner, the same day) — each metric takes its worst value over the four windows, then the ranks
  are taken once. The other reading (the lowest of the four windows' rank scores) is not built.
- **R4 — the increment of an admission is finite**: `real.increment: finite` (Sharpe of the K+1 minus
  Sharpe of the K).
- **R5 — the open risk is capped per plan, funded path**: number of members × risk per trade ≤
  a fraction of the plan's maximum daily loss; no per-symbol cap. **The fraction is not decided**:
  `funded.open_risk_cap: null`, and the funded commands refuse to start without it. What the
  code reads as «maximum daily loss» and which phase binds: `PLAN.md` §12, reading 5.
- **Stage B's shortlist — «no two finalists share more than half their members» is half of the
  LARGER one**: `stageb.shared_of: larger`.
- **Q16 — several candidates enter in sequence**: the best increment first, the base grows, the
  rest are re-judged against the new base (pair filters and increment) until none adds.
- **R6 — the oos1 figure is the rank score, against random admissible combinations of the same
  size K**: no search per draw; 10,000 draws, 95th percentile (`real.null_draws`,
  `real.null_percentile`, both `ledger:portfolio.verdict.*`). `PLAN.md` §5.5, §12 reading 6.
- **R7 — the N that deflates the oos2 Sharpe is `ledger.trials.overall`** (the whole project).
  `PLAN.md` §12 reading 7, with the readings the code took.
- **F4 — the funded verdict's measure on oos1 is `mc_p`** (the Monte Carlo P(pass)):
  `verdict.pass_measure: mc_p`. **Its percentile is not decided**: `verdict.pass_percentile: null`;
  the funded verdict says «SIN CRITERIO (falta verdict.pass_percentile)» and does not open oos2.
  The funded verdict no longer pools oos1 and oos2: it follows #11 as amended below.
- **Encargo 33 §6.4 — after a failed account, both re-buy policies are compared**: `same_plan` and
  `none` side by side in the bank table, the policy a searched dimension, the trial count doubled
  (`funded/sim/config.yaml` `owner.rebuy: [same_plan, none]`).
- **Encargo 33 §6.7 — the haircuts shown are 0, 25, 50, 75 and 100 %, and 50 % decides**
  (`owner.haircuts`, `owner.haircut_decides`). The other half of §6.7 — the unseen data that
  validates the chosen combination — is not answered.

## Decided by the Council on the owner's delegation — 2026-10-04

The owner delegated the pending calls («Confío en el criterio de la comunidad, hacedlo todo»); five
members, confidence-weighted tally, threshold 2/3. Questions and options:
`docs/AgentPDFs/decisiones-pendientes-2026-10-04.md`. The owner reverses any of them by saying so.

- **#2 — strategies per portfolio and per symbol: set by the funding economics** (the 10k account at
  the minimum lot), on the real side as on the funded one (`PLAN.md` §14.4). Decided 2026-10-04 by
  the Council on the owner's delegation. There is no K typed by hand: a member whose smallest
  trade cannot be placed at 0.01 lot inside the risk grid is out, and K runs from 1 to the largest
  admissible combination of the rest (`real.py`). No cap per symbol exists in the funding economics
  today — open reading, `PLAN.md` §12 «Readings the Council's answers leave open». **Reversed by:** a
  portfolio traded on an account where the minimum lot does not bind (a larger account, a
  broker with micro-lots), or the owner fixing K or a per-symbol cap by hand.
- **#5 — rebalancing: never.** The portfolio backtest is fixed weights from the first day to the
  last. Decided 2026-10-04 by the Council on the owner's delegation. It unblocks M8 only as far
  as static weights go: a weight method is estimated once on `build` and held. **Reversed by:**
  a weight method that beats equal weight out of sample only when re-estimated (M8's
  walk-forward would show it), or a member degrading in live incubation — then the question is
  retiring a member, which is not rebalancing and is not decided here.
  *2026-10-05:* M8's walk-forward is built (`common/construct/wf.py`) and prints the reversal
  condition when it meets it; on the Nikkei test pool (test root, relaxed — a code test) no
  method beat equal weight in either arm. Nothing is reversed; `weights.method` stays `equal`.
- **#11, amended — search on `build`; judge on `oos1` and on `oos2` separately, not pooled.**
  The 2026-09-29 rule («test on `oos1`+`oos2` together») stands for the search side and is
  replaced on the verdict side by `PLAN.md` Q11 (d), decided 2026-10-04 by the Council on the
  owner's delegation: on `oos1`, the chosen portfolio must beat the 95th percentile of 10,000
  admissible random portfolios drawn by the same search; on `oos2`, its deflated Sharpe with the
  ledger's N must be above 0, read **once**, on the chosen portfolio only. **Reversed by:** the
  owner; or a pool too small for the null to discriminate (a null that keeps drawing the chosen
  portfolio reads ~50 % whatever the edge, `knowhow/research/selected-null-same-pool.md`).
- **#12 — no «unexplained, on probation» category.** A strategy is in the pool or it is not; the
  verdict's words gain no third label. Decided 2026-10-04 by the Council on the owner's
  delegation. **Reversed by:** the owner opening a small-capital sleeve for unexplained edges —
  it would be its own pool, never a label inside this one.
- **After `oos2` is spent, what validates the chosen combination is live incubation** (Council's
  F5, same date): `PLAN.md` §14.5, milestone M9. No further backtest segment is carved.

## Settled by the owner — moved verbatim from `portfolio/CLAUDE.md` on 2026-10-03

These were rules in `CLAUDE.md`; they live here now. Later answers: `PLAN.md` §12 «Answered» and §14.

**Settled by the owner, 2026-09-29** (moved out of `DECISIONS.md`):

- **The construction engine comes first**, before encargo 33: the funding economics evaluates a
  portfolio, so it needs one to exist. The engine's layers: universe (daily equity from the
  archive) → pairwise filters → combination search → weights → verdict.
- **Sizing and the prop-firm constraints belong to the funding economics (encargo 33), not to the
  construction engine.** The engine chooses combinations and weights; risk per trade, P(pass) and
  the firm's rules are encargo 33's — which also hands the engine each firm's pool with its
  outright prohibitions already removed (below).
  **Amended 2026-09-30** (`DECISIONS.md` #13, delegated by the owner to the session): the
  **funded** portfolio is chosen by the funded yardstick inside the engine — P(pass) of one plan
  on `build`, from floating equity (MAE and MFE, intraday, on the firm's server day), judged on
  `oos1`+`oos2`. The rule functions stay encargo 33's; the engine calls them. Encargo 33 keeps the
  bank-level economics and no longer chooses the portfolio. → `PLAN.md` §14.
- **Correlation thresholds default to 0.30, every one** (Pearson, Spearman, co-loss, tail, and
  the rolling 60-month one in both its whole and recent windows), as config knobs. Development may
  relax them to get a portfolio out of a small pool; a relaxed run says so.
- **No same-asset conflict filter.** AlphaForge's "two strategies open on one symbol within 8 h"
  matrix is not ported.
- **Weights are a pluggable submodule; equal weight is the first and the baseline.** Every other
  method (min-variance, risk parity, HRP, …) is added later behind the same interface and must beat
  equal weight out of sample to be used.
- **Search on `build` (IS), test on `oos1`+`oos2`** — the segments of `assets/_policy.yaml`. The
  combination and its weights are chosen reading only `build`, and judged on `oos1`+`oos2` together;
  every combination evaluated is counted in the ledger.
  **Amended 2026-10-04** (Council, on the owner's delegation): the real path's verdict reads
  `oos1` and `oos2` separately — section «Decided by the Council» above, #11.
- **Same pool for funded and real** (`DECISIONS.md` #1).
- **Fixed fractional risk, never Kelly** (#8), and **Monte Carlo of every kind** (#7): trade
  bootstrap, joint-daily block bootstrap, start-date distributions, rolling windows, worst-day
  injection — `BUILD_COMPENDIUM.md` §7. Both are used by encargo 33's sizing.
- **Development reads the archive before the validated pool exists**: until step 26 produces a
  pool (it waits on `OPEN.md` #78), the engine is developed and tested on the workflow's survivors
  **of any step**, archived without step 26 and marked as development — no portfolio built from
  them is tradeable.
- **Siblings get no special rule** (#9): variants of one mother — parameter siblings and crossTF
  siblings alike — enter the pool and face the same correlation filter as any strategy. The owner
  expects parameter siblings to fail it (ρ ≥ 0.30) and crossTF siblings to be the ones worth a try.

**Only validated strategies enter** (owner, 2026-09-29): a strategy that passed steps 1-25 and
whose MT5 backtest on a prop firm's feed matched SQX's (step 26, encargo 34) joins that firm's
**validated pool**, and the portfolio reads only from it. `oos2` is spent by then.

A funded account's rules split in two (owner, 2026-09-29): what a firm **forbids outright** (holding
over the weekend, trading news windows…) removes strategies from that firm's pool **before** the
search — encargo 33 supplies the filter, the engine searches what is left; what can be met by
sizing (daily loss, total drawdown, minimum days) is encargo 33's, after the engine.
