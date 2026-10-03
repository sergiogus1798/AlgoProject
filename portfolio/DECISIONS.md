# Portfolio — open decisions

Questions the owner has not settled yet. Nothing here is implemented; do not guess an answer.
Settled on 2026-09-29 and moved to the section «Settled by the owner» below: #1 (same pool), #3 (equal weight as the
baseline, pluggable weights), #7 (Monte Carlo of every kind), #8 (fixed fractional), #4 (every
correlation threshold 0.30 by default), #9 (siblings face the same filter, no special rule) and #11 (search `build`, test `oos1`+`oos2`). #10 (near-survivors enter, marked) was settled on 2026-09-30. #13 (the funded portfolio is chosen by the funded yardstick inside the engine) was settled on 2026-09-30 by the session, the owner having delegated it — `PLAN.md` §14.

| # | question | why it matters |
|---|---|---|
| 2 | How many strategies per portfolio, and per symbol? **Owner, 2026-09-29: undecided — maybe the funding economics or the portfolio's own risk should say.** Funded side (2026-09-30, `PLAN.md` §14.4): K is capped by the minimum lot on a 10k account; still open for the real account. | Decides whether correlation or capacity is the binding constraint |
| 5 | Rebalancing: never, on a schedule, or on degradation? | Changes what the backtest of the portfolio even means |
| 6 | Prop-firm rules to encode: daily loss, total drawdown, minimum days, consistency — and which firm (static or trailing DD, news windows). **Belongs to encargo 33 now** (owner, 2026-09-29): outright prohibitions filter the pool before the search, the rest is sizing after it | Encargo 33 (`docs/encargos/33-economia-del-fondeo.md`) answers it from data |
| 12 | Allow an "unexplained, on probation" category with small capital? | Renaissance did; the hypothesis-first protocol says no — dossier §1.20 |

Answer one, and it moves from here into `portfolio/CLAUDE.md` as a settled rule.

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
