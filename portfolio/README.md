# portfolio — combining surviving strategies into accounts

Strategies that survive the generation and robustness pipeline are individually plausible; this folder
asks which of them should be traded **together**, and what that combination is worth. Two destinations
with different constraints: **funded** (prop-firm challenge accounts, built first) and **real** (the
owner's own capital). The funded question is economic as much as statistical: an account is bought,
can be failed, pays out a share of profit, and is bought again, so the objective is the owner's bank
balance, not a Sharpe ratio. Shared machinery lives in `common/`.

## Layout

| folder | what it holds |
|---|---|
| `common/construct/` | the construction engine: pool, M1 equity rebuild, pair measures, search, weights, verdict on `oos1` then `oos2` |
| `common/monteCarlo/` | trade-level Monte Carlo of one strategy or portfolio: how much of the result is luck, and of what kind |
| `funded/catalog/` | prop-firm plan database (price, rules per stage, add-ons, every add-on combination priced) |
| `funded/deals/` | daily scan of firm discounts, notification, and a worth-it verdict |
| `funded/rules/` | a challenge as a state machine over server days |
| `funded/sim/` | bank simulation over many accounts bought in sequence |
| `funded/decide/` | reads the bank tables and says which account to buy, with its cost |
| `real/` | the own-capital path |
| `testroot/` | a second data root so tests run the real code without touching real data |

Plans and decisions: `PLAN.md` (layout, data shapes, milestones, §14 the funded path), `DECISIONS.md`
(settled and open questions), `EXECUTION.md` (contracts between files), `BUILD_COMPENDIUM.md`
(practices and traps gathered before building), `CLAUDE.md` (rules for sessions working here).

## Method

### The funded path: "4D chess"

A funded account is not capital: a fee is paid — a premium — and payouts arrive until a rule breaks
the account. A strategy that is excellent on real capital can have negative expected value here (one
5 % day a year is enough to fail), and a dull, quiet one can be positive. Valuing that takes four
levels at once, each built on the results of the one below — the owner's name for it is *Ajedrez 4D*
(`docs/AgentPDFs/Ajedrez4D-2026-09-30.md`, in Spanish):

| level | the game | what it produces |
|---|---|---|
| 0 · the material | every trade's floating P&L, minute by minute, from M1 wicks — a trade list gives the size of an adverse excursion, the rules punish its *timing* | per server day: closed P&L, floating, lowest and highest equity; a portfolio's worst moment, which is not the sum of its members' |
| 1 · one game | one account as a state machine over those days, at a chosen risk per trade | P(pass), P(fail) and on which rule, over three kinds of resampled paths — the most pessimistic rules |
| 2 · the bank | accounts bought one after another on one long path, fees, re-buys and refunds included | the expected value of the owner's bank, not of the account |
| 3 · the choice | every firm × plan × add-on combination × portfolio × risk | which account to buy, or «none» when nothing beats a random-entry baseline |

The pieces, level by level:

**Selection discipline.** A combination is chosen reading only `build`, judged on `oos1`, then on
`oos2` once. Correlation is measured between equity curves, not between metrics, and a portfolio's
drawdown is computed on the aggregated curve, never summed from the parts. A strategy enters from a
frozen archive that carries the ledger count of strategies tried, which deflates its Sharpe.

**Floating equity from M1 wicks.** Prop-firm limits are breached by floating loss, which a closed-trade
list hides. `common/construct/equity/` rebuilds each strategy's floating equity from its trades and the
feed's M1 bars, cutting it into the firm's server days: closed P&L, floating at day end, the day's
lowest and highest equity. Per-trade MAE and MFE are rebuilt from the wicks and licensed against SQX's
own columns (PLAN §9, M1, on one archived strategy: MAE 100 %, MFE 99.9 %, SQX's daily low 100 % of
3,983 days).

**Rule machine.** `funded/rules/` walks that day table against a plan's rules read from the catalogue:
daily-loss and max-loss floors (static, trailing or end-of-day trailing), target, minimum days,
consistency, time limit. It returns pass, fail (and on which rule) or still open. Rules the catalogue
marks unconfirmed or in conflict are named in the result, not hidden. The sweep is numba-compiled.

**Search.** Stage A scores combinations by P(pass) of one plan under the machine (greedy and genetic
search; every trial is a ledger row); stage B re-judges finalists on resampled paths of three kinds
(`common/construct/mc/`): stationary bootstrap of the joint day table, whole-trade bootstrap with
members independent, and windows of history.

**Bank simulation.** `funded/sim/` optimises the bank account, not the funded one:
`VE_banco = E[Σ payouts received] − E[Σ prices paid]`, re-buys and fee refunds included. One long path
per draw; accounts are bought one after another on it. Edge is haircut or set to zero (a random-entry
baseline), and `funded/decide/` recommends a plan only if it passes its gates, the last being EV above
that baseline. Otherwise it answers «ninguno».

**Trade-level Monte Carlo** (`common/monteCarlo/`) runs after a strategy is accepted and does not ask
whether the edge is real. Five families: A and B resample order and composition (block bootstrap
for serial structure: `block_min` 5 trades, at least 20 blocks), C execution stress (skipped trades,
cost shocks, degraded fills), D calendar windows and volatility regimes (ATR or GARCH), E a
Probabilistic Sharpe Ratio against a same-footprint random trader. `n_sims` is 100,000 paths per
sub-test (`config.yaml`). Deliberately not done: no Deflated Sharpe or CSCV (they need the generation
trial count, which does not exist at that stage); no assumption the edge is real; **no seed** —
reproducibility is replaced by measuring how far the gate numbers move between independent runs.

**Firm catalogue and deals.** `funded/catalog/` stores plans in `AlgoData/funding/funding.sqlite`
(Hantec Trader and FTMO active; FundedNext and FundingPips candidates). `funded/deals/` finds offers
daily and judges them with the same bank tables.

## Commands

All verified to exist as modules; run from the repo root.

| command | does |
|---|---|
| `python3 -m portfolio.funded.catalog.show <firm or plan>` | print a plan's price, rules and add-on combinations |
| `python3 -m portfolio.funded.catalog.refresh` | re-read the firms' catalogues |
| `python3 -m portfolio.funded.sim.run` | bank simulation (refuses while owner inputs are `null`) |
| `python3 -m portfolio.funded.sim.frompool` | feed the bank simulation from a pool's portfolio |
| `python3 -m portfolio.funded.decide.run` | which account to buy, from the bank tables |
| `python3 -m portfolio.funded.deals.worth [deal_id]` | whether a discount is worth it |
| `python3 -m portfolio.funded.deals.scan` / `.notify` / `.add` | find, announce, record a deal |
| `python3 -m portfolio.common.construct.candidates` | list archivable survivors |
| `python3 -m portfolio.common.construct.funded` | funded search, stage A |
| `python3 -m portfolio.common.construct.funded_b` | funded search, stage B |
| `python3 -m portfolio.common.construct.universe` | build the daily equity matrix |
| `python3 -m portfolio.common.construct.real` | real-capital construction |
| `python3 -m portfolio.common.monteCarlo.report` | the Monte Carlo study |
| `python3 -m portfolio.testroot.build` | create the test root |

Tests: `tests/test_portfolio_*.py`.
