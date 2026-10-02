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

Phase 1 covers steps 7 → 16 (the population steps of one project). It stops at 16.5, where the
mother-by-mother work begins (`pipeline/run.py`), and never runs the 19 (reads oos2).

| file | what it does | run it | in → out |
|---|---|---|---|
| `variants.py` | Step 16.5 as an autopilot action: `wire` the three WFC legs (`sqx.projects.wfc`, on a pushed copy when a live session is up), then per design brief of step 16 `make` → `execute` → `equity` → `collect` → `execute --clear` | imported | a project after step 16 → one batch per mother harvested, the four databanks empty |
| `run.py` | The loop: `advance.where`/`busy` refusals, the plan, then per action an SQX step (`launch.preflight.check` + `launch.run.execute`: one start, «Project finished», one stop), a Python step (`chain.python_step`) or a judge; the first failure writes `fallo.md` and ends it | `python3 -m pipeline.autopilot.run --project P` · `--plan` prints the plan and runs nothing | a project → `AlgoData/autopilot/<P>/<stamp>/{plan.json, estado.txt, resumen.md, fallo.md, paso-<n>/}` |
| `plan.py` | The rail walked as `chainplan.plan` walks it, with a `judge` before the next SQX step that still has to run instead of a stop; halts at 1-5 not done, 16.5, 19, anything running, an SQX step with no stage (25.5) — judging a pending step first | imported | GET /api/workflow → `{do, stop}` |
| `facts.py` | Every number of a step's studies **and its extras** (`steps.EXTRA`: step 8's monkey, profitShape, entryQuality), from each one's newest result: per-strategy contract JSONs (summary, verdict parts, distribution stats, table cells, a tab's reading as `<tab>.verdict_pass`), one-row-per-strategy parquets (every column with a number, object-dtype pass flags included; a parquet indexed by identity joins by it), and every number of `verdict.csv` and `nulls.csv` as `<study>.verdict_csv.<col>` / `nulls_csv.<col>` ("True"/"False" as 1/0), plus `verdict_csv.drop` and, for spread, `verdict_csv.state_pass`. Key = `<study>.<tab>.<block>.<row>.<column>`, accents dropped; a repeated key gets `#2`. Step 12 is shaped per MOTHER (`crosstf_rows`): `crossTF.cells.<role>.<tf>.<stat>`, `…_vs_original`, `crossTF.reading.<tf>.<reading>` and `reading.n_<reading>`, zeros included | `python3 -m pipeline.autopilot.facts --project P --step 8 [--grep gate.]` lists keys with count, median and range | study results → long frame `study, strategy, identity, key, value` |
| `criteria.py` | The inference: one rule → pass/limbo/fail (a threshold, or distance to the population's median); a strategy's outcome is its worst rule; a missing fact is limbo. `resolved` folds a rule's `by` in first: `by: {H4: {pass: ">= 2.5"}}` replaces the fields it names when the project has that tag — its timeframe, symbol or asset class (`judge.tags`, from the project registry); several joined by `+` must all hold, the first matching entry wins, no match leaves the rule as written | imported | facts + rules → `{id: (outcome, reason)}` |
| `judge.py` | One judging step: facts to `hechos.parquet`, the databank's files by identity, the criteria, the dev draw (seed recorded), `verdict.csv` (`strategy, verdict, identity, outcome, reason`), the cut | imported | step → databank cut, `paso-<n>/` |
| `criteria.yaml` | The rules and the dev draw, commented | edited | — |

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
- **Same-day reruns**: the gate and snoopingScreen clear their `estrategias/` before writing;
  the others write no per-strategy JSON in a population run, but a step-25 `--strategy` run of
  edgeCost lands its JSONs in step 8's folder of that day (hence `summary.*` for 3 strategies).
- **Which folder**: `sources.results` sorts by day only, not by databank; a study run on two
  databanks the same day gives `gather` either one.
- **Not `ALGO_AUTONOMOUS`** (owner, 2026-10-01): the ledger's oos2 door is not forced on it yet.
