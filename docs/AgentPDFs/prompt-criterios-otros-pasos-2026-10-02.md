# Prompt — calibrate the Pass / Limbo / Fail criteria of another workflow step

Outbound brief: paste everything below the line into a fresh session, replacing `<STEP>` with the
step to calibrate (10, 12, 14, 16, or the 17-20 block). It is in English because an agent reads
it; it reports to the owner in Spanish. It encodes how steps 6 and 8 were done on 2026-10-02
(`docs/AgentPDFs/criterios-pasos-6-y-8-2026-10-02.md`) and the traps that work hit.

---

You are the lead of a team of agents. Goal: design the **Pass / Limbo / Fail criteria of workflow
step `<STEP>`** of this project, calibrated on fresh data, written as rules in
`pipeline/autopilot/criteria.yaml`, and explained to the owner in a Spanish dossier. Talk to the
owner in Spanish. Read `CLAUDE.md` first and obey its hard rules.

## What the owner wants

Criteria that make sense and rest on statistics, each threshold with **its gain and its cost in
strategies next to it**. He accepts the world is imperfect: where the data cannot fix a number,
say so and take the prudent one. Statistical significance comes first. The three verdicts mean:
**Pass** = proven with the data available; **Limbo** = could not be proven yet, goes on marked;
**Fail** = almost surely chance, or a risk a funded account cannot take. A missing fact is Limbo
(owner, 2026-10-01) — do not change that; write an explicit rule that fails what must fail.

## Read before anything

1. `docs/AgentPDFs/WORKFLOW.md` — the step, which segment it reads (`build`, `oos1`, `oos2`) and
   what it hands to the next one.
2. `docs/AgentPDFs/criterios-pasos-6-y-8-2026-10-02.md` — the finished example. Reuse its
   structure, its vocabulary and its conclusions; do not re-derive them.
3. `pipeline/autopilot/README.md`, `criteria.yaml`, `facts.py` — how a rule names a fact, the
   `by:` override per timeframe / symbol / asset class, worst rule wins.
4. The step's study folders (`studies/…/README.md`, `config.yaml`) and `ledger/thresholds.yaml`.
5. `knowhow/research/gate-t-scales.md`, `step6-floor-vs-step8-yield.md`,
   `post-selection-bias.md`, `knowhow/sqx-drive/unselected-build-population.md`,
   `knowhow/perf/review-path-after-sqx.md`.
6. `~/Desktop/AlgoData/scratch/calib_queue/HANDOFF.md` — the unattended queue that builds
   populations at ~10 minutes each, and how to extend it to the step's SQX task.

## Method — in this order

1. **Research, in parallel, read-only** (one agent each, each writes a report file other agents
   read): (a) what the step's SQX task and Python studies compute — exact formulas, nulls, and
   every fact key they emit per strategy; (b) the project's own knowledge and the owner's dated
   decisions that constrain the step; (c) the literature. Verify the formulas against the code:
   step 8's central statistic had a units bug nobody had noticed.
2. **Wire the facts first.** A rule on a number the autopilot cannot see is always Limbo. List
   the step's facts with `python3 -m pipeline.autopilot.facts --project P --step <STEP>`; expose
   what is missing as numeric columns before calibrating anything.
3. **Fresh, unselected populations.** Never calibrate on old databanks. Feed the step with what
   the previous step lets through under its *approved* criteria **plus an unselected sample**
   (strategies the previous step failed): without the dead ones you cannot measure what a rule
   costs or whether it discriminates. Cover long and short, genetic and random generation, at
   least two templates, M30 / H1 / H4, and every asset that can be built. One custodian job at a
   time; the queue does the rest without an agent in the loop.
4. **A null on the same statistic.** Simulate strategies with no edge under the doctrine and the
   asset's costs, plus a zero-cost twin (the break-even strategy — the honest benchmark for
   "has an edge"). Compute on the nulls *exactly* the statistic the pipeline computes on the real
   ones: same booking (mark-to-market or closed trades), same drift adjustment, same effective N.
   A false-positive rate measured on a different statistic is worthless.
5. **Calibrate each candidate rule** with: what it keeps, what share of the good it loses, the
   lift, a confidence interval clustered by strategy structure, its false-positive rate on the
   nulls, and its **sole effect** (strategies it alone demotes). Drop rules that never fire alone
   unless they are cheap safety nets; say which facts are one axis.
6. **Define "good" from data the rule does not read**, and check the conclusion under two or
   three alternative labels. Report **rates, not counts**: a floor that removes 70 % of any
   population "loses 70 % of the good" by construction.
7. **Red team.** A fresh agent with a clean context recomputes the proposal independently and
   returns CONFIRMED / WRONG / OVERSTATED / UNSUPPORTED per claim. Expect it to change numbers.
8. **Validate through the real code path** (`facts.per_strategy` → `criteria.resolved` →
   `criteria.outcomes`) on every population: the funnel, per population and pooled.
9. **Test in SQX what was measured after the fact.** A filter applied inside an SQX task changes
   what the task produces; an A/B (same box, one arm per setting) is the only evidence.
10. **Deliver**: the rules in `criteria.yaml` (marked as an agent's proposal, provisional until
    the owner approves), a Spanish dossier in `docs/AgentPDFs/` with its PDF, knowhow cards for
    every non-obvious fact, the manual chapter of any command that changed, and the list of
    files changed. Do not commit; end with «¿Quieres hacer el commit?».

## What steps 6 and 8 established — build on it

- **Only one cell showed edge: USDJPY long.** Everywhere else the populations passed at the rate
  of random entry. A step that "passes" strategies where the previous one found no enrichment
  is reading luck. Compare every population against its random-generation twin.
- **No strategy is individually significant after the search** (largest trade t 3.57 against a
  family-wise ~3.7). Each step enriches; the chain proves. Count the evidence a step adds as
  *independent* of what selected its input: a step that reads `oos1` again adds little.
- **The window decides.** One-direction strategies ride the segment's trend. Always subtract the
  market's own drift over each holding period (`gate.scorecard.drift_excess_t`). With it, one
  threshold line serves all 17 assets and both sides (1.65 ≈ 4 % and 2.33 ≈ 0.6 % false
  positives on H1 and M30; H4 is noisier: 1.9 / 2.5).
- **Trades per year**: under 20 chance dominates; 20-40 cannot prove itself in one segment
  (Limbo); 40 is the owner's floor and the Pass line. Power, not preference: a per-trade net
  Sharpe of 0.15 reaches the Pass line 18 % of the time at 20 trades/yr and 50 % at 50.
- **Floating risk is its own axis** (correlation 0.06 with the t): worst day, worst trade MAE
  and max drawdown over yearly net, in R (the sizing's risk per trade). The funded accounts are
  judged on floating equity; a step that can see it must carry it.
- **Profit factor is a floor, not a selector**; its luck level depends on the trade count, not
  on the asset. The Kaufman efficiency ratio of the equity curve *is* the profit factor; the
  market's ER before entry does not persist from IS to OOS.
- **Filters inside the Build lose good strategies**; select after, in Python.

## Traps this work hit — do not repeat them

- **Sessions.** Only XAUUSD and USDJPY can be built: every other asset's `<SYM>_ftmo` session is
  defined in no project. The builder refuses; never invent market hours. Ask the owner.
- **A full databank is a selection.** At the cap SQX replaces by in-sample Ret/DD. Stop the task
  before it fills.
- **The worker's stop triggers the window's exporter**, which walks every project on the
  install. The queue bypasses it (`ALGO_NO_EXPORT=1`) and exports only its own project.
- **RAM.** A 64-wide fan-out of per-strategy readings (1.7 GB each) killed the session and the
  custodian mid-stop. At most 8-12 processes, at least 25 GB free.
- **`pgrep -f` / `pkill -f` match your own shell.** Kill by PID.
- **The monkey seeds from OS entropy**: its p is not reproducible; do not hang a rule on it.
- **A long-lived agent burns tokens** re-reading its history. Turn any repeated chain into a
  script that runs detached, and wake on its marker file. Research and synthesis agents get a
  clean context and read reports from disk.
- **`/tmp` is 3.9 GB.** Big files go to `~/Desktop/AlgoData/scratch/`.
- **Two readings of one word** (rule 11): "the Kaufman ER" was the equity curve's or the
  market's at entry — ask, do not pick.
- **Thresholds chosen after reading a segment spend it.** Say which segment each step's
  calibration used, freeze the numbers before the next build, and never touch `oos2` for this.

## What is the owner's, not yours

Whether a criterion is adopted; switching `dev.on` off; anything on the master install; the
sessions; the risk per trade. Bring him the decision with its cost, in Spanish, and stop.
