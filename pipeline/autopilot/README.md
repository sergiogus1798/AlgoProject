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
| `run.py` | The loop: `advance.where`/`busy` refusals, the plan, then per action an SQX step (`launch.preflight.check` + `launch.run.execute`: one start, «Project finished», one stop), a Python step (`chain.python_step`) or a judge; the first failure writes `fallo.md` and ends it | `python3 -m pipeline.autopilot.run --project P` · `--plan` prints the plan and runs nothing | a project → `AlgoData/autopilot/<P>/<stamp>/{plan.json, estado.txt, resumen.md, fallo.md, paso-<n>/}` |
| `plan.py` | The rail walked as `chainplan.plan` walks it, with a `judge` before the next SQX step that still has to run instead of a stop; halts at 1-5 not done, 16.5, 19, anything running, an SQX step with no stage (25.5) — judging a pending step first | imported | GET /api/workflow → `{do, stop}` |
| `facts.py` | Every number of a step's studies, from each one's newest result: per-strategy contract JSONs (summary, verdict parts, distribution stats, table cells), one-row-per-strategy parquets, the study's own `verdict.csv` as `verdict_csv.drop`. Key = `<study>.<tab>.<block>.<row>.<column>`, accents dropped; a repeated key gets `#2`. Step 12 is shaped per MOTHER (`crosstf_rows`): `crossTF.cells.<role>.<tf>.<stat>`, `…_vs_original`, `crossTF.reading.<tf>.<reading>` and `reading.n_<reading>`, zeros included | `python3 -m pipeline.autopilot.facts --project P --step 8 [--grep gate.]` lists keys with count, median and range | study results → long frame `study, strategy, identity, key, value` |
| `criteria.py` | The inference: one rule → pass/limbo/fail (a threshold, or distance to the population's median); a strategy's outcome is its worst rule; a missing fact is limbo | imported | facts + rules → `{id: (outcome, reason)}` |
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
  `profitShape`, `entryQuality`…): they are what «correr todo» runs. Their numbers are facts too,
  and they cost time — the first thing to measure (`OPEN.md`).
- **Not `ALGO_AUTONOMOUS`** (owner, 2026-10-01): the ledger's oos2 door is not forced on it yet.
