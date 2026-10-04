# pipeline/autopilot — the whole workflow of one project, unattended, judging instead of stopping

The window's «Correr workflow» (`ui/daemon/launch/chain.py`) already runs every SQX step and
every Python test in WORKFLOW.md's order — and **stops on purpose** at each judging step (8, 10,
12, 14, 16) so the owner decides the cut. The autopilot is that chain with a judge in place of the
stop: it reads every number the step's studies wrote, applies `criteria.yaml`, writes a
`verdict.csv`, cuts the databank the next SQX task reads (`sqx.curate.apply_verdict`, worker
stopped) and goes on. Owner, 2026-10-01: rules are binary, three outcomes — pass / limbo / fail —
and a limbo goes on, marked; a step without criteria lets everyone through.

**Development mode** (`dev` in `criteria.yaml`, on today): at step 8 only, keep 5 strategies drawn
at random among those that pass. The point is a fast run that proves the chain, not a filter.

**Cheap to watch.** Everything an agent needs is three small files in the run's folder; it never
reads SQX's log. `estado.txt` (one line, overwritten), `resumen.md` (one row per action, seconds
and what it did), `fallo.md` (only on failure: the step, the reason, the last lines of the trace).

Steps 7 → 16 are the population steps of one project. From 16.5 on (2026-10-02) every survivor of
16 walks 16.5 → 25, unfiltered (owner, 2026-09-29), and step 26 runs when its four parameters are
given: the tail (`tail.py`). 🤔 Built and tested with SQX stubbed; no real run yet (`OPEN.md`).

| file | what it does | run it | in → out |
|---|---|---|---|
| `variants.py` | Step 16.5 as an autopilot action: `wire` the three WFC legs (`sqx.projects.wfc`, on a pushed copy when a live session is up), then per design brief of step 16 `make` → `execute` → `equity` → `collect` → `execute --clear` | imported | a project after step 16 → one batch per mother harvested, the four databanks empty |
| `run.py` | The loop: `advance.where`/`busy` refusals, the plan, then per action an SQX step (`launch.preflight.check` + `launch.run.execute`: one start, «Project finished», one stop), a Python step (`chain.python_step`), a judge, the variants (only the survivors of 16), or — from 17 on — `tailrun.run`; a `survivors.Done` ends it cleanly (its reason is the stop in resumen.md), the first failure writes `fallo.md` | `python3 -m pipeline.autopilot.run --project P [--panel 21=D --panel 22=D] [--mt5-from … --mt5-to … --mt5-model … --mt5-firms a,b]` · `--plan` prints the plan and runs nothing | a project → `AlgoData/autopilot/<P>/<stamp>/{plan.json, estado.txt, resumen.md, fallo.md, paso-<n>/, finalistas.json}` |
| `timing.py` | Where the wall clock went: `fases.csv` (every `core.phases` block of the run and its subprocesses — start, ready, sqx, stop, export per piece, sync, snapshot, each test, each variants module) folded into `tiempos.md`, one row per action with its seconds by column (`sqx` apart from arranque, parada, export, sync, copias, resto; a nested phase's seconds leave its parent) and the twelve longest phases; rewritten after every action | imported | `<run>/fases.csv` → `<run>/tiempos.md` |
| `plan.py` | The rail walked as `chainplan.plan` walks it up to 16.5, with a `judge` before the next SQX step that still has to run; from 17 on it is `tail.walk`'s | imported | GET /api/workflow + the tail's inputs → `{do, stop}` |
| `tail.py` | The plan 17 → 26: the three blind looks (planned whenever any of 17-19 is open), `sqx` 19, its reading, the ledger rows, 20 and its judge, 21-22 on the databanks given, 23, 24, 25, the finalists, 26; clean stops without a family, without `--panel`, without every `--mt5-*`; and those flags | imported | rail steps + inputs → actions, stop |
| `tailrun.py` | One tail action run: its kind → the module that does it, with the mothers of that step | imported | action → one line for resumen.md |
| `survivors.py` | Who walks the tail: one row per identity of the databank the last judged step cut (`cut` of 16, later of 20-25), `about(project)` (symbol, timeframe, feed, family) and `Done`, the clean stop | imported | project, step → mothers |
| `blind.py` | 17, 18, 18.5 per mother (door asked first, a mother with her result skipped unless `redo`), the WFM reading, the ledger rows 17-19 still lack (per project, once per WFM reading) then `gate.allow_read`, and step 20 through the same door | imported | batches + WFM export → results, ledger rows |
| `closing.py` | 21-22 as the window builds them on the databank given; 23 (`structural.make` → retest → `keep` → export build+oos1 → `structure.report` → clear) and 24 (two `stopgrid` passes, each retested, exported and read) in the project's own three WFC legs, the project copied aside before each retest | imported | mothers → `structural/<P>/<stamp>/`, `atrCalculator/<P>/<stamp>/pass{1,2}/` |
| `traded.py` | The version that will be traded: each mother's step-24 variant at `ledger:portfolio.funded.stop_percentile`, grid step 0; its build and oos1 trades filed as the cosecha `Stop_p<P>` (keyed by the mother's identity); step 25's edgeCost per strategy on it; a mother without a stop is named and left out | imported | pass2 manifest + stopgrid export → `harvest/<P>/Stop_p<P>/<day>/`, edgeCost results |
| `finalists.py` | `finalistas.json` — `{strategy, identity, mother, sqx, symbol, timeframe, stop: {percentile, x}}`, `sqx` the fabricated grafted file — and step 26 handed to `mt5.verify.autopilot` (imported late); its `check` not ok is a clean stop | imported | mothers → `<run>/finalistas.json`, step 26's line |
| `call.py` | The one door every command of the tail goes through: `run(argv)` (a `chain.command`, output never shown) and `window(...)`, the argv `runner.table.jobs` builds | imported | argv → done, or SystemExit with its tail |
| `facts.py` | Every number of a step's studies **and its extras** (`steps.EXTRA`: step 8's monkey, profitShape, entryQuality), from each one's newest result: per-strategy contract JSONs (summary, verdict parts, distribution stats, table cells, a tab's reading as `<tab>.verdict_pass`), one-row-per-strategy parquets (every column with a number, object-dtype pass flags included; a parquet indexed by identity joins by it), one-row-per-strategy-and-market parquets as `<stem>.<market>.<col>` (crossmarket's `markets.parquet`), and every number of `verdict.csv` and `nulls.csv` as `<study>.verdict_csv.<col>` / `nulls_csv.<col>` ("True"/"False" as 1/0), plus `verdict_csv.drop` and, for spread, `verdict_csv.state_pass`. Key = `<study>.<tab>.<block>.<row>.<column>`, accents dropped; a repeated key gets `#2`. Step 12 is shaped per MOTHER (`crosstf_rows`): `crossTF.cells.<role>.<tf>.<stat>`, `…_vs_original`, `crossTF.reading.<tf>.<reading>` and `reading.n_<reading>`, zeros included | `python3 -m pipeline.autopilot.facts --project P --step 8 [--grep gate.]` lists keys with count, median and range | study results → long frame `study, strategy, identity, key, value` |
| `criteria.py` | The inference: one rule → pass/limbo/fail (a threshold, distance to the population's median, or — 2026-10-03 — a verdict, `is: pass`/`is: fail` on a 1/0 fact; `else: limbo` on any of them makes not-met a limbo instead of a fail); a compound `all: [...]` / `any: [...]` is its worst / its best part, nested freely (`judged`); `reads` lists every fact the rules name, parts included; a strategy's outcome is its worst rule; a missing fact is limbo. `resolved` folds a rule's `by` in first: `by: {H4: {pass: ">= 2.5"}}` replaces the fields it names when the project has that tag — its timeframe, symbol or asset class (`judge.tags`, from the project registry); several joined by `+` must all hold, the first matching entry wins, no match leaves the rule as written | imported | facts + rules → `{id: (outcome, reason)}` |
| `judge.py` | One judging step: facts to `hechos.parquet`, the databank's files by identity, the criteria, the dev draw (seed recorded), `verdict.csv` (`strategy, verdict, identity, outcome, reason`), the cut | imported | step → databank cut, `paso-<n>/` |
| `criteria.yaml` | The rules and the dev draw, commented. Also read and written by the window's «Criterios» zone (`ui/daemon/criteria/`): each change stamped in `ledger/criteria-history.jsonl`, and `frozen: {on, by, sha}` once the owner freezes them | edited, by hand or from the window | — |

## Traps

- **A step's own verdict is a fact, not a cut.** The gate's `MANTENER/DESCARTAR`, crossmarket's
  breadth floor: they land as `<study>.verdict_csv.drop` and `<study>.verdict.pass`, and cut only
  when `criteria.yaml` names them in a rule.
- **Step 12 judges mothers and cuts `CrossTF`** (owner, 2026-10-01): a mother passes or not by
  her siblings' facts; then only she goes on, on her own timeframe, unscaled. Every scaled
  sibling in any cut databank is dropped. The cut is on `CrossTF` because step 13's own run
  refills `CrossTF_Mothers` from it (`crosstfload.load_mothers`) — cutting `CrossTF_Mothers`
  would be undone. The baseline cell (the mother on her own timeframe) had 0 trades on every
  mother of the 2026-09-30 run (`OPEN.md` §89), so `_vs_original` facts are absent until it is fixed.
- **Step 14 cuts `MCR 8 Stress`, step 16 cuts `SPP OOS`** (owner, 2026-10-01): each is what the
  next task reads — SPP IS reads only the eighth MCR databank, and the WFM reads SPP OOS. Phase 2
  takes 16.5's mothers as those left in `SPP OOS`, each matched to her `SPP IS` counterpart, and
  designs the variants from the combined backtest's metrics (owner, 2026-10-01) — not every
  mother of the SPP export, as `pipeline.run.mothers` does today.
- **The median of a `near_median` rule is over the databank being cut**, not over every strategy
  the study read (the gate also reads the build's strategies that never reached `OOS`).
- **The chain's tests at step 8 include the readings outside the sequence** (`monkey`,
  `profitShape`, `entryQuality`): their numbers are facts of step 8 too (`facts.gather` reads
  `studies` + `extra`). `profitShape` and `entryQuality` run AFTER step 8's cut, on its
  survivors only (`run.AFTER_CUT`, owner 2026-10-01: they were 200 of the step's 297 s on all
  571) — **unless a step-8 rule names them** (`profitShape.…`): then they run before the judge,
  on everyone, and pay those seconds. Not named, their facts in `hechos.parquet` are whatever
  their newest folder holds (an earlier run's survivors) and judge nothing.
- **Missing is limbo, and the gate is a cascade**: a strategy that died at `estaticas` has no
  `forma_*`, `mono_*`, `familia_*` fact, so a rule on `gate.scorecard.mono_p` alone leaves it in
  limbo. Pair late-screen rules with `gate.verdict.pass` or the screen's `<s>_passed`.
- **Step 8's keys** (`--grep` them; 🔬 Test_USDJPY_donchianUpperCrossUp_H1, 2026-10-01):
  - gate: `gate.verdict.pass` (survived every hard screen), `gate.verdict_csv.drop`,
    `gate.scorecard.<screen>_value` and `<screen>_passed` for presencia, sanidad (OOS trades),
    estaticas (net OOS), degradacion (Sharpe retention), forma (DD OOS/IS), mono (p), familia
    (p; `_passed` = survives BH), redundancia (group size); `gate.scorecard.degradacion_t`
    (Lo's t on OOS), `degradacion_years_positive`, `degradacion_concentration` (best quarter /
    total OOS, lower better), `mono_corr` (reconciliation) — the last four only on a scorecard
    written after 2026-10-01. ⚠️ `degradacion_t` changed scale on 2026-10-02 (units bug fixed,
    `knowhow/research/gate-t-scales.md`): old 1.3 / 1.65 / 2.0 are new 1.42 / 1.92 / 2.55 on a
    5-year oos1; a rule written against an older scorecard reads a different test.
  - gate, measured for EVERY strategy of the OOS databank (no cascade hole; scorecards from
    2026-10-02): `gate.scorecard.trade_t` (t of the mean OOS trade), `drift_excess_t` (the same
    after taking the market's drift over each hold out, AR(1) n — the one to judge on),
    `oos_trades_per_year`, `is_trades_per_year`, and in R (1,000 USD):
    `{oos,is}_max_dd_r` (> 0, on SQX's daily-low equity: floating in), `{oos,is}_worst_day_r`
    (< 0, low to low),
    `{oos,is}_worst_trade_mae_r` (< 0), `{oos,is}_net_per_year_r`, and
    `{oos,is}_dd_over_net_year` (max DD / net per year; **+inf when net ≤ 0**, so a `<=` rule
    fails it instead of reading «sin dato»; scorecards written after 2026-10-02 02:30).
  - edgeCost: `edgeCost.verdict_csv.edge_mean`, `edge_median` (gross edge per trade in units of
    today's spread + commission, IS+OOS pooled, higher better), `n`. Its `summary.*` exist only
    for strategies read one by one (step 25) — never write a rule on them at 8.
  - snoopingScreen: `snoopingScreen.summary.sharpe` (OOS daily Sharpe), `excess_day` (USD/day
    over equal-risk buy & hold, > 0 beats it), `verdict.pass` (StepM names it).
  - feedQuality: `feedQuality.verdict_csv.p` (only with ≥ 10 flagged trades; < 0.01 is the
    alarm), `flagged`, `at_risk` (flagged share of net, lower better), `n`.
  - spread: `spread.verdict_csv.state_pass` (no segment broken at Darwinex's real spread),
    `neto_con_slippage_real_{is,oos}`, `pf_con_slippage_real_{is,oos}`, and SQX's own
    `neto_sqx_*`, `pf_sqx_*`, `spread_real_medio_puntos_*`.
  - monkey: `monkey.nulls_csv.p_<rung>_<stat>` (rung timing, timing_holds, timing_sizing, free;
    stat net, sharpe, pf, retdd, dd; lower = beats the random trader), `reconcile`, `real_*`.
  - profitShape: `profitShape.<concentration|dependence|breaks>.verdict_pass` (1 = spread,
    independent, stable) and every table cell, e.g. `…concentration.cuanto_pesan_los_mejores.*`.
  - entryQuality: `entryQuality.<eratio|delay>.verdict_pass` (signal, latency_robust),
    `entryQuality.eratio.en_algunos_horizontes.<k>.*`, and
    `entryQuality.delay.en_barras_de_la_estrategia.<d>.dcr` (share of gross edge given up by
    entering d bars late) — the row keyed by `d` only on results written after 2026-10-01.
- **Step 10's keys** (`--grep crossmarket.`; results written after 2026-10-02): the study's own
  breadth call is `crossmarket.verdict_csv.drop` / `fraction` / `cleared` / `markets` (0 when the
  strategy never fired on any other market — a silent strategy has no other fact, so pair any
  rule with `markets >= 1` or it reads Limbo). Measured, no level applied:
  `verdict_csv.excess_t_pooled` (step 8's `drift_excess_t` on the weekly excess P/L of every
  additional market summed: cost-inclusive, and two markets that are one trade count once),
  `excess_t_stouffer` (assumes the markets independent), `excess_t_max` / `_2nd` / `_3rd` /
  `_q75` / `_median` / `_min` («≥ x in at least k markets» is `excess_t_<k-th> >= x`),
  `excess_t_half` (the value at least half of the markets reach),
  **`excess_blind_t_pooled` and `excess_blind_t_half`** (the same two with the unbiased drift term — the
  blind trade of the same hold; a break-even long and short are both centred on zero, so ONE line
  serves both sides: put the pooled rule on this one),
  `markets_effective`, `trades_total`, `trades_min`, `net_total` (USD), `net_positive`,
  `p_median`, `p_min`, `z_median` (the block-shift null: against random entries paying the SAME
  cost, so a strategy can clear it and lose money), `a_cleared`, `expectancy_positive`. Beside
  the original (the export's main block — the step-9 task's main test, `oos1` today):
  `main_<stat>` and `<stat>_vs_main_half` for stat in `excess_t`, `trade_t`, `pf_sqx`,
  `net_per_trade`, `sharpe_sqx` — the ratio market / original that at least half of the markets
  reach, so «half of them at x times the original» is `>= x`; no fact (Limbo) when the
  original is not above zero, where `excess_t_minus_main_half` (a difference) still exists. By
  category of `_markets.yaml`: `family_` / `structural_` + `markets`, `net_positive`,
  `excess_t_pooled`, `excess_t_half`, `excess_t_vs_main_half`, `excess_blind_t_pooled`,
  `excess_blind_t_half`, `net_per_trade_vs_main_half`; absent for a category with no
  market. Per
  market: `crossmarket.markets.<feed>.<col>` from `markets.parquet` (`excess_t`, `trade_t`,
  `trades`, `net_sqx`, `p`, `z`, `pf`, …) — the feeds differ by source asset, so a rule on one
  needs `by: <SYMBOL>`. Both sides are read (short support 2026-10-02); a market is read only on
  its own build..oos1 (`markets.<feed>.window_*`, `traded_*` are in `markets.parquet` as text).
- **Same-day reruns**: the gate and snoopingScreen clear their `estrategias/` before writing;
  the others write no per-strategy JSON in a population run, but a step-25 `--strategy` run of
  edgeCost lands its JSONs in step 8's folder of that day (hence `summary.*` for 3 strategies).
- **Which folder**: `sources.results` sorts by day only, not by databank; a study run on two
  databanks the same day gives `gather` either one.
- **It sets `ALGO_AUTONOMOUS=1`** (D4, owner 2026-10-04, in `run.main`; its subprocesses inherit
  it): the ledger's door refuses `oos2` to every step the policy does not list. 17, 18, 18.5 and 19
  are computed without any of their numbers read, registered, and only then is 20 read — a
  missing row of 17-19 is a `PermissionError` before any command starts. ⚠️ Step 20 is not in
  `_policy.yaml`, so its SPA half is not read (`studies/closing/blindJoint/README.md`).
- **Batches are named by the brief's `strategy`**, not its file stem (dots, not dashes): batches
  made before 2026-10-02 under `Strategy_20-25-72` are not found by 17-20.
