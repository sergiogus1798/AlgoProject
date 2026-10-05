# portfolio/funded/sim — the bank simulation: what leaves the owner's bank against what comes back

Encargo 33 deliverable 3 (and the mechanics of 4), milestone F5, stage C of `portfolio/PLAN.md` §14.3.
What is optimised is the **bank account**, not the funded account:
`VE_banco = E[Σ payouts received] − E[Σ prices paid]`, every re-buy included, the fee refund included.

```
config.yaml ─▶ inputs ─▶ plans ─▶ haircut / monkey ─▶ bank (kernel) ─▶ measures ─▶ table ─▶ report
 every knob    owner's   catalogue   which paths        the draws       what they    §4 as     what he
               inputs    + add-ons   (h, zero edge)                     say          data      reads
```

**One long path per draw; accounts are bought one after another on it.** A draw is one row of the
path set (the server-day table D of `portfolio/EXECUTION.md` §1, unit risk). Day 0: buy → the
challenge stages (the rule machine's loop, `portfolio/funded/rules/`) → the funded stage, a payout
every cycle → a rule breaks → the next account is bought **the day after**, on the same path, so
consecutive accounts share the regime — until the path or the cash ends. Nothing here generates a
market path: the path set is an argument. `frompool.py` writes the real one — the portfolio a funded
run's verdict names, drawn with the Monte Carlo that decided stage B and recentred on the OOS edge
(encargo 33 §3.2); stage B's generators (`portfolio.common.construct.mc.paths`) are imported lazily
by it and by `run.py --days`.

**Imports from:** `portfolio.funded.rules`, `core.study`, `core.datapaths`, `ledger.record`, numpy, numba, pandas
**Consumed by:** `portfolio/funded/decide/` (the tables it writes) and `portfolio.funded.deals.worth` through it

| file | what it does | run it | in → out |
|---|---|---|---|
| `config.yaml` | Every knob. A `null` under `owner:` or `gaps:` is the owner's decision: the command refuses until it is given | — | — |
| `inputs.py` | The config with `--set` applied, the list of owner inputs still missing (Spanish), and the path set read from its `.npz` (its `source` included) | imported | file → arrays, meta |
| `plans.py` | A plan as the simulation reads it: `catalog.plan()` + one add-on set from the `combos` table + the funded stage's cash terms (split, payout days, refund) with every unconfirmed reading flagged; `Gap` names what the catalogue lacks; the risk-per-phase grid | imported | plan key, options → plan, terms |
| `frompool.py` | **The real path set**: the members and risk of a funded run's `verdict.json`, stage B's deciding flavour and block length at the bank's horizon, the edge moved to the pooled edge of `--edge-from`; `source` in the `.npz` says all of it | `python3 -m portfolio.funded.sim.frompool --run <run> --horizon N --n-paths N --edge-from oos1,oos2 --set …` | funded run → `AlgoData/portfolio/bank/paths/<run>_s<seed>.npz` |
| `haircut.py` | `h` of the edge taken off every closing day; the break-even `h` of a curve | imported | paths, h → paths |
| `monkey.py` | The zero-edge twin of a path set (`MODELS`: `demean`) | imported | paths → paths |
| `account.py` | **The reference**: one account from purchase to end — `machine.challenge`, then the funded stage and its payouts — in plain Python | imported | one path, start → life |
| `kernel.py` | The same walk in numba over every draw (`prange`), one row of `COLS` per draw | imported | arrays → matrix |
| `bank.py` | The reference walk of one draw (`walk`), the numba run (`simulate`), the denied-payout and firm-closure draws (`hazards`) | imported | paths, plan, risk, terms → matrix |
| `measures.py` | A matrix of draws as one flat row: EV with its Monte Carlo standard error (`ev_se`) and 90 % interval, per purchase / dollar / month, fees paid, payouts received, refunds, the worst draw (`net_min`), P per phase, P(first payout), purchases to it, payouts and life per funded account, cash drawdown p50/p90/p99, the rule that fails most | imported | matrix → row |
| `table.py` | Every universe plan × add-on set × re-buy policy: the risk per phase searched at the deciding `h`, the monkey at its best risk, the curve EV(h), each add-on's ΔEV | imported | paths, cfg → rows |
| `report.py` | The Spanish printed tables, the two re-buy policies side by side with their error, the decision-shaped sentence, the study-contract result | imported | rows → text, dict |
| `trials.py` | The ledger row: every configuration scored, `score_unit: ev_bank_usd` | imported | search → row |
| `run.py` | **THE COMMAND** | `python3 -m portfolio.funded.sim.run --paths <set.npz> --study <id> --symbol <A+B> --segment <seg> --set owner.eurusd=… …` | path set → `AlgoData/portfolio/bank/<stamp>_<label>/` |

## The path set (`inputs.paths`)

An `.npz` with `closed`, `float_end`, `low`, `high` (float64 `[n_paths, horizon]`), `opened` (int32),
and two scalars: `unit_risk` — the account currency risked per trade at which the arrays are written
(1.0 = R multiples) — and `days_per_year` (path days in a year: payout days are calendar days and
become path days at `days_per_year / 365`). A risk level r scales a path by `r · size / unit_risk`.
`synthetic: true` marks a path set that is not a look at data: no ledger row, and the output says so.
`source` (a JSON string, `frompool` only) names where the paths come from: `run`, `pool`, `plan`,
`members`, `risk`, `verdict_pass`, `verdict_label`, `flavour`, `length`, `edge_build`, `edge_oos`,
`edge_from`, `seed`, `relaxed`, `study`, `symbol` — it travels into `manifest.json`, and
`decide` reads it to know whose portfolio a table is.

## What is the owner's (the command refuses without it)

Answered and committed (owner, 2026-10-05, encargo 33 §6.4 and §6.7): `owner.rebuy: [same_plan,
none]` — **both, compared**: the policy is a searched dimension, every plan gets one row per policy
and the trial count doubles — `owner.haircuts: [0, 0.25, 0.5, 0.75, 1]`, `owner.haircut_decides: 0.5`.
Still `null`: `owner.eurusd` (never fetched), `owner.payout_cushion`, `owner.tax_rate`, `owner.payout_fee`,
`owner.p_payout_denied`, `owner.p_firm_closes_year`, and every `gaps.*` the catalogue does not hold
(today `hantec_endurance_payout_days` and `<firm>_<family>_floor_after_payout`
for the two families whose funded max loss trails: Hantec Express and FTMO 1-Step;
`gaps.hantec_fee_refund` is asked only if the catalogue loses its answer — it holds «no refund», confirmed, since 2026-10-04). No pass criterion lives here: the table
is ranked at the given `h`, and the sentence says so.

## Semantics

- **Budget**: a purchase happens only if `price ≤ budget + received − paid` — the bank account holds
  the budget and every payout returns to it. `outlay_before_first` is the cash out before the first
  payout of the draw (all of it when none came).
- **Funded stage**: the stage's own floors, checked as the machine checks them. A payout is due one
  cycle after the stage starts and one cycle after each payout; it is paid on the first day from
  then on with a closed profit above the cushion, a positive profit in the cycle, and the stage's
  minimum days and consistency met **since the previous payout**. It withdraws
  `balance − size − cushion·size`; the bank gets `share × (1 − fee) × (1 − tax)` of it, plus the
  price back with the account's first payout where the plan refunds. The eligibility window and
  the first payout's timing are assumptions, flagged in every result (`plans.ASSUMED`).
- **The max-loss floor after a payout** matters only where it trails, and is the owner's reading
  (`gaps.<firm>_<family>_floor_after_payout`, flagged): `stays` — a withdrawal lowers the balance
  and leaves the high-water marks, so the floor is wherever the trailing rule put it (the
  catalogue's `trailing_lock`: at the initial balance once +max-loss was reached); `initial` — from
  the account's first withdrawal the floor **is** the initial balance (encargo 33 §3.5.4), so
  withdrawing everything leaves no room and the cushion is the lever. A static floor does not move.
- **Denied payout**: nothing is paid and the account ends. **Firm closes**: the draw ends that day.
- **Haircut**: `h × edge` comes off the closed P&L of every day that closed any; edge = mean closed
  P&L per closing day of the whole path set. **Monkey** `demean` = `h = 1`: the strategy's days and
  volatility with zero drift — it pays no costs, so it flatters the lottery.
- **EV** is USD per bank draw **over the horizon of the path set**; `ev_se` and the 90 % interval
  are Monte Carlo error only. The risk shown is the best of the grid at the deciding `h` — a maximum
  over noisy means. `ev_h100` is the zero edge at THAT risk, `ev_monkey` the zero edge at its own
  best risk, so `ev_h100 ≤ ev_monkey` always.
- **The horizon is a first-order knob** (🔬 Nikkei test pool, 2026-10-05): `same_plan` pays a full
  fee for accounts bought late whose life the horizon cuts, and a costless zero-edge trader on a
  static max loss withdraws on average the whole max-loss allowance if given time (optional
  stopping; `tests/test_funded_decide.py`), so EV(h = 1) turns positive on static-floor plans as
  the horizon grows (≤ 0 everywhere at 504 days, three plans > 0 at 1,008).
  → `knowhow/research/funded-bank-ev-read-against-the-monkey.md`
- **Add-ons**: sets up to `addons.max_set` whose members each move something the simulation reads;
  `delta_ev` is against the bare plan and already net of the add-on's price (paid at every purchase).
