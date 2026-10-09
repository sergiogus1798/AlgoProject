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

**Smoke mode** (`run --smoke`, `Test_` projects only, 2026-10-04): a functional test of the chain. A smoke run leaves an empty file `smoke` in its `AlgoData/autopilot/<P>/<run>/`; the store marks those steps `smoke: true`.
Only the rules on `judge.READABLE` facts judge (presence, sanity, trades per year), at every step,
so the dev draw always has someone to keep; `criteria.yaml` is not touched. 🔬 1,000 Simple
Strategy longs on NIKKEI225 M30 left 0 alive at step 8 under the real rules and the run ended there. Under `--smoke` the post-stop MC Retest ingest also gets
`--set recon.systematic_share=0.2` (`ui/daemon/loader/afterrun.py` SMOKE_SHARE): with ten strategies its guard
(max(2, 5 % of runs) misses = «wrong formula») tripped on 5 of 70 RecoveryFactor cells at 1.01-1.22× tolerance
and ended the run at step 14; the cells are still excluded and recorded.

**One automatic retry** (`call.py` `again`, 2026-10-05): SQX's transient abort («Error while running project»,
fastutil NullPointerException after «Task finished») reruns the action ONCE — in the SQX step (live or `--restart`
route), in the variants' make/execute and in the closing retests of 23-24. Before rerunning an SQX
step, `call.keeper` removes from the chosen tasks' output databanks every .sqx the aborted attempt added (a
retest does not clear its output: a plain rerun doubled 1,000 to 2,000, the copies named `Strategy X(1)`):
on the live route it stops the project and cuts the extra strategies from the output databank; on `--restart` it unlinks the extra .sqx. → `knowhow/sqx-drive/mcr-nullpointer-fastutil-transient.md`
**Step 24:** if a pass fails, `closing.py` moves the half-done batch to `<run>/paso-24-abortado`; otherwise
pass 1's report alone made the rail call 24 done and step 25 crashed on the missing `pass2/ran.json`.

**Cheap to watch.** Everything an agent needs is three small files in the run's folder; it never
reads SQX's log. `estado.txt` (one line, overwritten), `resumen.md` (one row per action, seconds
and what it did), `fallo.md` (only on failure: the step, the reason, the last lines of the trace).

Steps 7 → 16 are the population steps of one project. From 16.5 on (2026-10-02) every survivor of
16 walks 16.5 → 25, unfiltered (owner, 2026-09-29), and step 26 runs when its four parameters are
given: the tail (`tail.py`). 🤔 Built and tested with SQX stubbed; no real run yet (`OPEN.md`).

| file | what it does | run it | in → out |
|---|---|---|---|
| `variants.py` | Step 16.5 as an autopilot action: `wire` the three WFC legs (`sqx.projects.wfc`, on a pushed copy when a live session is up), then per design brief of step 16 `make` → `execute` → `equity` → `collect` → `execute --clear`. Live route (default): all mothers' pilots run first with the WFC legs wired without the 11 extra markets (the pilot reads only the main market's trade count: 81 s → 4 s each), then the legs are rewired with markets and each mother runs execute → equity → collect → clear; `--restart` keeps the pilot inside `make`, per mother. After each live step the export reads only the project that ran (`afterrun --project`). Last, with every batch on disk, each mother's parameter map (`studies.optimisation.cloud.report`: no rule, build and oos1 only) | imported | a project after step 16 → one batch per mother harvested and mapped, the four databanks empty |
| `resume.py` | Brings a retired project back from the strategy store: recreates it under its name, loads the chosen stored `.sqx` into its databanks, so `bin/workflow.sh run` continues at step 13 (the rail calls an SQX step done when its databank holds files; a project built with `--until` has no later tasks) | `python3 -m pipeline.autopilot.resume Test_X <identity or name>…` | store → project |
| `neighbours.py` | Step 13's T1 batch as an autopilot action (kind `neighbours`, dispatched by `tailrun`): `entering` — the mothers CrossTF holds after step 12's cut, never a scaled sibling — then `run`: rule 5, the WFC legs wired without extra markets and only `neighbours.legs` (WFC 1 IS, WFC 2 OOS1) switched on, `sqx.variants.neighbourbatch` make → retest (project copied aside) → trades exported under the tag `neighbours` → `studies.breakage.mcRetest.neighbours.t1` → the WFC databanks emptied. It leaves only those two legs active: the SQX step after it stages its own tasks | imported | the mothers in `CrossTF` → `AlgoData/neighbours/<P>/<stamp>/`, `raw/<P>/T1_Neighbours/<day>/neighbours.parquet` |
| `run.py` | The loop: `advance.where`/`busy` refusals, the plan, then per action an SQX step (`launch.preflight.check` + `launch.run.execute`: one start, «Project finished», one stop), a Python step (`chain.python_step`), a judge, the variants (only the survivors of 16), or — from 17 on — `tailrun.run`; a `survivors.Done` ends it cleanly (its reason is the stop in resumen.md), the first failure writes `fallo.md` | `python3 -m pipeline.autopilot.run --project P [--panel 21=D --panel 22=D] [--mt5-from … --mt5-to … --mt5-model … --mt5-firms a,b]` · `--plan` prints the plan and runs nothing | a project → `AlgoData/autopilot/<P>/<stamp>/{plan.json, estado.txt, resumen.md, fallo.md, fases.csv, tiempos.md, paso-<n>/, paso-24-abortado/, finalistas.json}`; `fases.csv` (began epoch, seconds, phase, detail, pid) is written by `core/phases.py` because the autopilot sets env `ALGO_PHASES`; `tiempos.md` is `timing.py`'s; `paso-24-abortado/` exists only after a failed pass (below) |
| `timing.py` | Where the wall clock went: `fases.csv` (every `core.phases` block of the run and its subprocesses — start, ready, sqx, stop, export per piece, sync, snapshot, each test, each variants module) folded into `tiempos.md`, one row per action with its seconds by column (`sqx` apart from arranque, parada, export, sync, copias, resto; a nested phase's seconds leave its parent) and the twelve longest phases; rewritten after every action | imported | `<run>/fases.csv` → `<run>/tiempos.md` |
| `plan.py` | The rail walked as `chainplan.plan` walks it up to 16.5, with a `judge` before the next SQX step that still has to run, and step 13's `neighbours` action right before its SQX tasks; an SQX step whose tasks the project does not carry (`bin/workflow.sh … --until`) ends the plan there, the pending judge done first; from 17 on it is `tail.walk`'s | imported | GET /api/workflow + the tail's inputs → `{do, stop}` |
| `tail.py` | The plan 17 → 26: 18.5's deciding reading without oos2 and its judge, the three blind looks (planned whenever any of 17-19 is open), 17, 18 and 18.5 judged as they close (18.5's judge action carries `segment: build+oos1+oos2`, which `judge.judge` writes into its ledger row instead of the criteria's `build+oos1`), `sqx` 19, its reading, 19 judged, the ledger rows, 20 and its judge (a judge only where `criteria.yaml` has rules), 21-22 on the databanks given, 23, 24, 25, the finalists, 26; clean stops without a family, without `--panel`, without every `--mt5-*`; and those flags | imported | rail steps + inputs → actions, stop |
| `tailrun.py` | One tail action run: its kind → the module that does it, with the mothers of that step; also step 13's `neighbours` (T1), with `neighbours.entering` | imported | action → one line for resumen.md |
| `pasos.csv` | (written by `run.py` next to `estado.txt`) one row per step start, end or failure — `paso, estado (empezó/hecho/falló), hora` — which the window's «En marcha» reads to show each Python step after a daemon restart | — | — |
| `survivors.py` | Who walks the tail: one row per identity of the databank the last judged step cut (`cut` of 16, later of 20-25), `about(project)` (symbol, timeframe, feed, family) and `Done`, the clean stop | imported | project, step → mothers |
| `blind.py` | 17, 18, 18.5 per mother (door asked first, a mother with her result skipped unless `redo`; with `oos2=False` — 18.5 before the block — the door is not asked and the study runs without its `OOS2` flag, `--oos2`; inside the block a result without `facts.oos2` is run again), the WFM reading, the ledger rows 17-19 still lack (per project, once per WFM reading) then `gate.allow_read`, and step 20 through the same door | imported | batches + WFM export → results, ledger rows |
| `kept.py` | after the WFM reading: per strategy in the WFM databank, joined **by name** to its step-8 scorecard row (identities do not survive the retest chain: 0 of 10 matched, 10 of 10 by name), its oos1 daily-low equity in R and `oos_worst_day_r`, `dd_esperado_r`, `oos_net_per_year_r`, for the funding module (encargo 45) | imported by `tailrun` (kind `kept`) | WFM verdict + gate scorecard + harvest → `KEPT/<project>/kept.csv`, `curves.parquet` |
| `closing.py` | 21-22 as the window builds them on the databank given; 23 (`structural.make` → retest → `keep` → export build+oos1 → `structure.report` → clear) and 24 (two `stopgrid` passes, each retested, exported and read) in the project's own three WFC legs, the project copied aside before each retest | imported | mothers → `structural/<P>/<stamp>/`, `atrCalculator/<P>/<stamp>/pass{1,2}/` |
| `traded.py` | The version that will be traded: each mother's step-24 variant at `ledger:portfolio.funded.stop_percentile`, grid step 0; its build and oos1 trades filed as the cosecha `Stop_p<P>` (keyed by the mother's identity); step 25's edgeCost per strategy on it; a mother without a stop is named and left out | imported | pass2 manifest + stopgrid export → `harvest/<P>/Stop_p<P>/<day>/`, edgeCost results |
| `finalists.py` | `finalistas.json` — `{strategy, identity, mother, sqx, symbol, timeframe, stop: {percentile, x}}`, `sqx` the fabricated grafted file — and step 26 handed to `mt5.verify.autopilot` (imported late); its `check` not ok is a clean stop | imported | mothers → `<run>/finalistas.json`, step 26's line |
| `call.py` | The one door every command of the tail goes through: `run(argv)` (a `chain.command`, output never shown) and `window(...)`, the argv `runner.table.jobs` builds | imported | argv → done, or SystemExit with its tail |
| `facts.py` | Every number of a step's studies **and its extras** (`steps.EXTRA`: step 8's monkey, entryQuality), from each one's newest result: per-strategy contract JSONs (summary, verdict parts, distribution stats, table cells, a tab's reading as `<tab>.verdict_pass`), one-row-per-strategy parquets (every column with a number, object-dtype pass flags included; a parquet indexed by identity joins by it), one-row-per-strategy-and-market parquets as `<stem>.<market>.<col>` (crossmarket's `markets.parquet`), and every number of `verdict.csv` and `nulls.csv` as `<study>.verdict_csv.<col>` / `nulls_csv.<col>` ("True"/"False" as 1/0), plus `verdict_csv.drop` and, for spread, `verdict_csv.state_pass`. Key = `<study>.<tab>.<block>.<row>.<column>`, accents dropped; a repeated key gets `#2`. Step 12 is shaped per MOTHER (`crosstf_rows`): `crossTF.cells.<role>.<tf>.<stat>`, `…_vs_original`, `crossTF.reading.<tf>.<reading>` and `reading.n_<reading>`, zeros included | `python3 -m pipeline.autopilot.facts --project P --step 8 [--grep gate.]` lists keys with count, median and range | study results → long frame `study, strategy, identity, key, value` |
| `batchfacts.py` | The facts of a result that is one FILE per mother (`<batch>/estudios/<study>.json`): its `facts` dict flattened with dots (`wfc.c1.estado`...), state words as numbers (`WORDS`), and `number`, the cell-to-float rule `facts.py` also uses; `flat`, the same flattening for the `facts` of a per-strategy page (the WFM's `estrategias/<name>.json`) | imported by `facts.py` (`file_rows`, `from_folder`) | the file → fact rows |
| `tffacts.py` | The redesigned step-12 facts (encargo 47): `crossTF.tf.state`, `.phase1`, `.t1`, `.t2a`, `.t2b`, `.t3` per mother and `crossTF.tf.<TF>.<column>` per mother and sibling timeframe, from `tf_mothers.csv` and `tf_siblings.parquet`. A state is a number — **pass 1, limbo 0, fail −1** — so a rule reads `pass: ">= 1", limbo: ">= 0"`; an empty state is no fact (limbo by `missing:`); no file, no facts. Written beside the old facts, not cutting yet | imported by `facts.py` | the study's two files → fact rows |
| `criteria.py` | The inference: one rule → pass/limbo/fail (a threshold, distance to the population's median, or — 2026-10-03 — a verdict, `is: pass`/`is: fail` on a 1/0 fact; `else: limbo` on any of them makes not-met a limbo instead of a fail); a compound `all: [...]` / `any: [...]` is its worst / its best part, nested freely (`judged`); `reads` lists every fact the rules name, parts included; a strategy's outcome is its worst rule; a missing fact is limbo. `resolved` folds a rule's `by` in first: `by: {H4: {pass: ">= 2.5"}}` replaces the fields it names when the project has that tag — its timeframe, symbol or asset class (`judge.tags`, from the project registry); several joined by `+` must all hold, the first matching entry wins, no match leaves the rule as written | imported | facts + rules → `{id: (outcome, reason)}` |
| `judge.py` | One judging step: facts to `hechos.parquet`, the databank's files by identity, the criteria, the dev draw (seed recorded), `verdict.csv` (`strategy, verdict, identity, outcome, reason`), the cut | imported | step → databank cut, `paso-<n>/` |
| `criteria.yaml` | The rules and the dev draw, commented. Also read and written by the window's «Criterios» zone (`ui/daemon/criteria/`): each change stamped in `ledger/criteria-history.jsonl`, and `frozen: {on, by, sha}` once the owner freezes them | edited, by hand or from the window | — |
| `offered.yaml` | Step → the facts a study publishes for a criterion the owner has not set yet (owner, 2026-10-04: «calculados y visibles, sin juzgar»), each with its name on screen and the knowhow card of its zero-edge null. Read by the window's «Criterios» zone only (`ui/daemon/criteria/read.offered`): listed under their step with an empty threshold and offered in the fact picker. `judge.py` never reads it — a fact judges only once a rule in `criteria.yaml` names it. A fact enters after its null told it apart from the real values; one the null covers stays a diagnostic of its panel | edited | — |

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
- **Step 14 cuts `MCR 7 OHLC`, step 16 cuts `SPP OOS`** (owner, 2026-10-07; 14 cut `MCR 8 Stress`
  until then): each is what the next task reads — SPP IS reads the last MC Retest task's
  databank (the builder's chain; `tests/test_autopilot_step13.py` pins it), and the WFM reads
  SPP OOS. Phase 2
  takes 16.5's mothers as those left in `SPP OOS`, each matched to her `SPP IS` counterpart, and
  designs the variants from the combined backtest's metrics (owner, 2026-10-01) — not every
  mother of the SPP export, as `pipeline.run.mothers` does today.
- **The median of a `near_median` rule is over the databank being cut**, not over every strategy
  the study read (the gate also reads the build's strategies that never reached `OOS`).
- **The chain's tests at step 8 include the readings outside the sequence** (`monkey`,
  `entryQuality`): their numbers are facts of step 8 too (`facts.gather` reads
  `studies` + `extra`). `entryQuality`, `monkey` and `monkeyExcess` (it reads the panel
  `monkey` writes, so the two never split) run AFTER step 8's cut, on its
  survivors only (`run.AFTER_CUT`, owner 2026-10-01: they were 200 of the step's 297 s on all
  571) — **unless a step-8 rule names them** (`entryQuality.…`): then they run before the judge,
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
  - feedQuality: `feedQuality.verdict_csv.p` (only with ≥ 10 flagged trades; < 0.01 is the
    alarm), `flagged`, `at_risk` (flagged share of net, lower better), `n`.
  - spread: `spread.verdict_csv.state_pass` (no segment broken at Darwinex's real spread),
    `neto_con_slippage_real_{is,oos}`, `pf_con_slippage_real_{is,oos}`, and SQX's own
    `neto_sqx_*`, `pf_sqx_*`, `spread_real_medio_puntos_*`.
  - monkey: `monkey.nulls_csv.p_<rung>_<stat>` (rung timing, timing_holds, timing_sizing, free;
    stat net, sharpe, pf, retdd, dd; lower = beats the random trader), `reconcile`, `real_*`.
  - entryQuality: `entryQuality.<eratio|delay>.verdict_pass` (signal, latency_robust),
    `entryQuality.eratio.en_algunos_horizontes.<k>.*`, and
    `entryQuality.delay.en_barras_de_la_estrategia.<d>.dcr` (share of gross edge given up by
    entering d bars late) — the row keyed by `d` only on results written after 2026-10-01.
- **Step 10's keys** (`--grep crossmarket.`; results written after 2026-10-07, encargo 46): one row
  per strategy of `crossmarket.verdict_csv.<col>`, the facts P1-P9 read: `invalid_fraction`
  (share of the listed markets §7.1 refuses), `fixed_distance` (P1), `freq_off` / `freq_off_fraction`
  (P2), `z_conj` (P3, all valid markets and every window V0+V1+V2 against the joint random runs, on
  gross R by default), `z_conj_v2` / `z_conj_v0` / `z_conj_v1` (P4 and its siblings),
  `z_minus_market` (P5, the worst all-but-one z), `p_breadth` / `breadth_count` (P6),
  `tau_half` / `e_principal` (P7), `worse` / `worse_fraction` (P8, markets at z <= `worse_z`),
  `z_beta` / `e_end` / `beta` / `e_end_ratio` (P9, the yearly edge's slope and last level),
  `net_t_pooled` (annotation: SQX's weekly pooled net t, judges nothing), `markets`,
  `markets_valid`, `trades`. A fact is empty when its data is: Limbo. Per market:
  `crossmarket.markets.<feed>.<col>` from `markets.parquet` (`valid`, `invalid_reason`, `z`,
  `trades`, ...) — the feeds differ by source asset, so a rule on one needs `by: <SYMBOL>`.
  Both sides are read; a market is read only on its own build..oos1 window.
- **Same-day reruns**: the gate clears their `estrategias/` before writing;
  the others write no per-strategy JSON in a population run, but a step-25 `--strategy` run of
  edgeCost lands its JSONs in step 8's folder of that day (hence `summary.*` for 3 strategies).
- **Which folder**: `sources.results` sorts by day only, not by databank; a study run on two
  databanks the same day gives `gather` either one.
- **It sets `ALGO_AUTONOMOUS=1`** (D4, owner 2026-10-04, in `run.main`; its subprocesses inherit
  it): the ledger's door refuses `oos2` to every step the policy does not list. 17, 18, 18.5 and 19
  are computed, judged by `criteria.yaml` without a number shown (below), registered, and only then is 20 read — a
  missing row of 17-19 is a `PermissionError` before any command starts. Step 20 (`BlindJoint`) is in
  `_policy.yaml`'s `reserved_for` since 2026-10-04 (owner): its StepM over oos2 is read, one look
  counted (`studies/closing/blindJoint/README.md`).
- **Batches are named by the brief's `strategy`**, not its file stem (dots, not dashes): batches
  made before 2026-10-02 under `Strategy_20-25-72` are not found by 17-20.

## Steps 11 → 11.5 → 11.7 → 12 (encargo 47, part P)

`plan.plan` walks the cascade in this order: **11** SQX on oos1, **11.5** the cross-TF study (phase 1:
only oos1 data exists, so T1 and T2b read «no data») and its judge, **11.7** SQX on the `build` window
for the twins (`CrossTF <TF> build`), **12** the same study again (now with build data) and its judge.
The study is one command at both steps, with no flag: it finds the build trades by itself
(`studies/transfer/crossTF/tf/inputs.build_banks`; `afterrun` exports the `CrossTF_<TF>_build`
databanks after 11.7 like any other).

- **11.5 cuts nobody** until the owner says «corta»: `criteria.yaml` › `"11.5"` has `rules: []`, and
  `cut: CrossTF_Input`, `siblings: follow`. With rules, a mother that fails leaves `CrossTF_Input` **with
  her siblings** and the siblings of the mothers that stay are kept (`judge.siblings`), because 11.7
  reads that databank. 11.7 does not refill it (`launch/preflight.judge`: `fed` is empty for step 11.7).
- **12** is as before: `crossTF.combined.z_new`, every sibling dropped, only the mother goes on.
- **A project without twins** (`derive.phase2` gives `titles: []`): `plan` returns the step in `skipped`
  (`run` prints «paso 11.7 saltado: …») and the 11.5 judge is flushed where 11.7 would have; 12 judges
  with «sin dato». The twins' titles are `sqx.projects.crosstfload.phase2_tasks`, and `launch/steps.of_step`
  gives them for step 11.7, which is deliberately not in `stages.yaml`.
- **Facts** `crossTF.tf.*` (`tffacts.py`): states are numbers, pass 1 / limbo 0 / fail −1.

## Steps 17 → 19 judged, 18.5 split (owner, 2026-10-07)

`tail.walk` gives, when any of 17-19 has to run: **18.5 `blind` with `oos2: false`** (the deciding
reading, build+oos1: no door asked, no `--oos2`) → **18.5 `judge`** → the looks **17, 18, 18.5**
(`oos2: true`; 18.5 recomputes with `--oos2`) → **`judge` 17, 18, 18.5** → 19 `sqx` → `wfm` → `kept`
→ **19 `judge`** → the ledger rows → 20. A judge is planned only for a step `criteria.yaml` gives
rules; all four are `cut: null` — facts, `verdict.csv` and a ledger row, nothing deleted in SQX.

- **Facts** are each study's `facts` dict, the study's key in front: `cscv.p_perdida`,
  `cscv.pbo_sobre_p95`; `marketSurfaces.orden.estado` (positivo 1, neutro 0, perverso −1; sin_dato
  = absent = Limbo), `.prima.bajo_p5`, `.oos2.perverso` (absent until the blind look: `missing:
  pass`); `wfm.l1.p_menos`, `wfm.l1.mediana_exceso`, and `wfm.reopt.centro_exceso` /
  `wfm.reopt.l2_p_menos` only with `modo_real: reoptimizado` (`missing: pass`: modo fijo is not
  hurt). The WFM's come from its page `estrategias/<name>.json` (`facts.from_folder`), joined to
  `SPP OOS` by name when the identity changed in the retest (`judge.resolve`).
- **The grammar says when a rule PASSES**: the specs' `fail: ">= 0.5"` is written `pass: "< 0.25",
  limbo: "< 0.5"` (not met = Fail, the default), and «can only give Limbo» is `else: limbo`.
- **18.5 is judged twice** and its ledger row says `build+oos1` both times; the look at oos2 is
  the study's own row (`engines.variants.look`). The second judgement can only add Limbo.
- **A judge's ledger row is a row of that step**: once 17, 18 and 19 are judged, `gate.allow_read`
  sees all three — 19's judge runs only after the WFM's reading, so the door still means «the
  three ran». `blind.register` writes the studies' own rows as before.
- **Step 20** reads each study's `verdict.state` under `joint.pieces: peor` — provisional, the
  worst state wins (`studies/closing/blindJoint/README.md`); `criteria.yaml` has no rules for 20.

## Steps 13 → 14 (MC Retest v2, owner 2026-10-07)

`plan.plan` gives, when step 13 has to run: **12's judge** (if pending) → **13 `neighbours`** (T1) →
**13 `sqx`** (`stages.yaml` › `mcretest`: MCR 1 Bar, MCR 7 OHLC, and MCR 4 MinDist only with
stop/limit orders) → **14 `python`** (mcRetest) → **14 `judge`** → 15.

- **T1 goes first.** Its mothers are who step 12's cut left in `CrossTF` — the files the SQX step
  then copies to `CrossTF_Mothers`. Its table is stored under the day it was measured, and the
  study looks for the newest one **up to its ingest's day**: measured after the ingest, a run past
  midnight would find none and judge everyone Limbo. And a run that dies inside T1 leaves step 13
  to do: the next run plans both again. A step 13 already done plans no T1.
- **The ingest is the SQX step's own stop** (`afterrun`: every databank's harvest, then `MCR_All`),
  so it is fresh and after the `Results` harvest whenever 13 ran in this run. T2 and T3 need an
  ingest written since 2026-10-07 (it stores the build's dated trades); an older one — step 13
  done before that date and resumed at 14 — reads «sin dato»: Limbo, said in the reason.
- **Facts** (`--grep mcRetest.fragilidad`): `mcRetest.fragilidad.t1.{build,oos1}.{ret_med, ret_p5,
  f_pos, ret_benef, beta_share, n}`, `t1.ambas.rho_vec`, `t2.build.{ret_med_aprox, ret_p5_aprox,
  f_pos, ret_benef, same_count_frac, count_dev_med, n}`, `t3.build.{ret_med, ret_p5, matched_frac,
  identical_frac, distinct, n}`. The rules read five of them (`criteria.yaml` › `"14"`,
  provisional); a strategy without a neighbour batch has no `t1.*` fact at all.
- **The study's own verdict judges nothing**: without the `stress` task it is INCONCLUSIVE and
  `mcRetest.stress.*` no longer exists.
- **A project built before 2026-10-07** still carries the eight MCR tasks: step 13 runs only the
  stage's three, but its `SPP IS` reads `MCR 8 Stress`, which nothing fills or cuts any more.
  Before its step 15, worker stopped: `python3 -m sqx.projects.spp <SYMBOL> --cfx <project.cfx>
  --input "MCR 7 OHLC"`. Its five idle MCR databanks, if an old run left strategies in them,
  still enter the `MCR_All` ingest.
- **The window's ▶ SQX of step 13 and «Correr workflow» do not run T1**: only the autopilot does.
