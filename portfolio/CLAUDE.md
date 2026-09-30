# portfolio — combining strategies

**The implementation plan is `PLAN.md`** (2026-09-30): module layout, data shapes, every knob, the
AlphaForge port, tests, milestones and the owner's open questions (§12). **Order: M0-M2 (shared
universe and pairs) → F1-F5 (the funded path, §14 — the owner's priority) → M3-M8 (the real-account
path) → M9 (paper OOS).** A milestone blocked by an open question does not start on a guessed default.

**Before building anything here, read `BUILD_COMPENDIUM.md` end to end** (owner, 2026-09-28). It
holds every practice, test and trap gathered for this module: what to port from the owner's
AlphaForge repo and what to redo, and every portfolio idea of the books-and-internet dossier
(`docs/AgentPDFs/ideas-de-internet-y-libros-2026-09-27.md` §5). None of it is accepted yet; its
§13 lists what the owner must decide first.

Two destinations with different constraints: `funded/` for prop-firm accounts, `real/` for the
owner's own capital. `common/` holds what both need.

The design is not settled. `DECISIONS.md` is where the open questions live; add to it rather than
inventing an answer. What is agreed so far:

- Correlation is measured between **equity curves**, not between metrics.
- A portfolio's drawdown is computed on the aggregated curve, never summed from the parts.

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

**Where a strategy comes from: the archive.** A strategy enters from `AlgoData/archive/<identity>/<version>/`
(`core/archive/`, encargo 23), frozen with its `.sqx`, its cosecha rows, every study result, the
asset card of that day and the ledger count (N strategies tried) that deflates its Sharpe. The
window's PORTFOLIOS zone lists it and «Importar» shows it as the Estrategia page, read from the
archive with nothing recomputed (`ui/desktop/portfolios/`). Importing from a live databank waits
for the owner. The portfolio maths itself is not built yet.

A funded account's rules split in two (owner, 2026-09-29): what a firm **forbids outright** (holding
over the weekend, trading news windows…) removes strategies from that firm's pool **before** the
search — encargo 33 supplies the filter, the engine searches what is left; what can be met by
sizing (daily loss, total drawdown, minimum days) is encargo 33's, after the engine.
**What each firm sells and under which rules is already a database**: `funded/catalog/`
(`AlgoData/funding/funding.sqlite`, Hantec and FTMO, every add-on combination priced), refreshed
every Sunday by the `fundingWatcher` agent. The economics on top of it is encargo 33.
