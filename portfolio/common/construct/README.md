# portfolio/common/construct — the portfolio construction engine

Which strategies of a declared pool go together, chosen reading only `build` and judged on
`oos1`, then on `oos2` once (Q11 d: separately, in that order). The plan is `portfolio/PLAN.md` (what and why); `portfolio/EXECUTION.md` freezes
the signatures each file implements. Funded accounts first (PLAN §14): the engine calls
`portfolio/funded/rules/` to score a combination by P(pass) of one plan.

```
inputs ─▶ equity ─▶ pairs ─▶ search ─▶ weights ─▶ verdict ─▶ contract
 pool,     the M1      every     (M3, F2)   (M4)      (M5, F4)   (M5)
 sources,  rebuild,    measure
 calendar  daily and   on build
           intraday
```

| folder | the question it answers |
|---|---|
| `inputs/` | what is this run on — the knobs, the declared pool, each archived strategy, the portfolio calendar |
| `equity/` | what did each strategy's equity do, day by day and inside the day, on whose clock |
| `pairs/` | how alike are two strategies' P&L, by each measure |
| `search/` | which combinations are allowed (the admissible graph); the search itself comes with M3/F2 |
| `mc/` | what could the next six months of this combination look like — paths of server days by three Monte Carlos, and the rules over them |
| `weights/` | how much of each member — chosen on build, fixed for good; equal weight is the one selected, the others (M8) are candidates `wf.py` compares against it |
| `verdict/` | does the chosen combination beat chance on oos1, and is its Sharpe on oos2 above what luck gives everything ever tried |
| `incubation/` | M9: the chosen portfolio frozen with its pre-registered comparison, the contract of its fresh days, and the reading against the band of its own history — **incubation is NOT running** (nothing produces the rows) |
| `contract/` | the run as the window's blocks: Veredicto, Universo, Parejas, Búsqueda, Cartera |

| file | what it does | run it | in → out |
|---|---|---|---|
| `candidates.py` | Lists every archivable survivor and near-survivor of every step, with the exact archive command for each; runs none (M0) | `python3 -m portfolio.common.construct.candidates [--project P]` | reports' `verdict.csv` → printed commands |
| `universe.py` | Builds (or finds cached) a pool's universe, writes `screen.json` beside it (who was kept or excluded and why, for the window's Correlación) and prints, for the owner, who was kept or excluded and why, the reconciliation per member, the calendar and the clocks; `--firm` drops that firm's prohibited members first and names them | `python3 -m portfolio.common.construct.universe --pool <name> [--firm <firm>] [--set k=v]` | pool → `AlgoData/portfolio/universe/<hash>-<cfg>/` |
| `funded.py` | The funded search, stage A: universe → members sized at fixed risk (no step-24 stop → excluded, named) → pair screen → greedy seeds + GA scored by P(pass) of one plan within 126 days → `runs/`, ledger rows, the best 10 printed. `--firm` (the plan's own firm) drops the members that firm or that plan prohibits, named; without it the summary says none was applied. Refuses to start while `funded.open_risk_cap` is null (R5, the owner's): (combination, risk) pairs with K × r above the cap × the plan's daily loss are NaN, and the summary counts them. 🔬 2026-10-05 first run, `Test_nikkei_ref` in the test root, thresholds relaxed: 4,500 evaluations = 58 distinct combinations, 13.5 s, 1.1 GB | `python3 -m portfolio.common.construct.funded --pool <name> --plan hantec:enhanced:10000:USD [--firm hantec] --set funded.open_risk_cap=<fraction>` | pool, plan → `AlgoData/portfolio/runs/<stamp>_<pool>_<plan>/` |
| `funded_b.py` | Stage B and the funded verdict on an existing stage-A run (F3, F4) — a run that already holds a stage B is never overwritten: `target()` copies its stage A to a new run (`funded.new_run`, `stage_a_run` in the manifest) and the new stage B lands there: the diverse shortlist, each finalist under three Monte Carlos (D, T1, T2) at every block length and risk per phase, the winner and its stability — the winner's reported P(pass) is `p_fresh`, the stability re-draws' mean on fresh paths from an independent seed, never the selector's `p`; then, when the pool has days in oos1, `funded_verdict.judge`, and the hand-off package. The firm, the plan's prohibitions and the relaxed mark are inherited from the stage-A manifest (no `--firm` here); the open-risk cap applies per phase. 🔬 2026-10-05, `Test_nikkei_ref` in the test root (not a result): stage B 11 finalists × 10 risks in 18.5 s, 1.8 GB | `python3 -m portfolio.common.construct.funded_b --run <run folder> --set funded.open_risk_cap=<fraction> --set stageb.t1_gap=close_to_open_blocks` | stage-A run → `shortlist.parquet`, `stageb.parquet`, `verdict.json`, `handoff/` next to it |
| `funded_verdict.py` | The funded verdict (F4, Q11 d): the winner and each null search's winner judged on **oos1 alone** — `verdict.pass_measure` (`mc_p`, owner 2026-10-05) against `verdict.pass_percentile` of the selected null; while that percentile is null the verdict is «SIN CRITERIO (falta verdict.pass_percentile)» and oos2 stays shut — then `oos2.read`, and «did the diversification hold» on the segments opened. A ledger row per segment opened | imported | world, stage B, null winners → judged, nulls, verdict |
| `real.py` | The search by ranks (M3): universe → members sized at fixed risk, out if their smallest trade is under the minimum lot on the 10k account → pair screen → every admissible combination scored on build, start shifted 0-3 months, by the shifted minimum of the mean signed rank of RAR, R-cubed, gain-to-pain and P(losing year) → `runs/`, ledger rows, the chosen portfolio with what it leaves out (`manifest.json`: `best_members`); `--base` admits the outsiders to a run's portfolio in sequence (Q16 c) → `admission.csv`. A relaxed run says «AJUSTADO» on its second line; `--firm` drops that firm's prohibited members first, named. No verdict: that is `report.py` | `python3 -m portfolio.common.construct.real --pool <name> [--firm <firm>] [--base <run folder>]` | pool → `AlgoData/portfolio/runs/<stamp>_<pool>_real/` |
| `report.py` | THE COMMAND of the real path (M5): the search of `real.py` (or, with `--run`, the portfolio of a run already made — nothing is searched again) and its verdict by `many.run`; writes `verdict.json`, the manifest's `verdict`, the contract result (`cartera.json`, `.html`, `.md`) and `handoff/`, prints the decision. 🔬 2026-10-05, `Test_nikkei_ref` in the test root (relaxed, pseudo oos2: not a result): K=1 → «NO SE PUEDE JUZGAR» (10 admissible singles), a forced K=3 → «NO PASA (oos1)» against 37 trios; 3.6 s with the universe cached | `python3 -m portfolio.common.construct.report --pool <name> [--firm <firm>] [--run <run folder>]` | pool → the run folder's `verdict.json`, `cartera.*`, `handoff/` |
| `many.py` | The real path's verdict (Q11 d; owner 2026-10-05, R6-R7): on oos1 the chosen portfolio's rank score — the search's four metrics, worst over the shifted starts, ranks taken among the draws plus itself — against the 95th percentile of 10,000 random admissible combinations of its own size K; `no_discrimina` when the chosen one alone is ≥ 5 % of the draws (under 20 admissible combinations of that K); oos2 only if oos1 passed; a ledger row per look per segment; `run()` returns the contract dict | imported | `report.load()`'s inputs → verdict, sentence, population |
| `oos2.py` | The ONE read of oos2 per pool: asks the pool's ledger study whether a verdict already read it (same portfolio → the stored reading, never recomputed; another portfolio → refused), then the one-way door for every member's symbol, and only then calls for the path; deflates by `ledger.trials.overall`'s N (the whole project) and the spread of the build Sharpes the pool's study holds; writes the row whether it passes or not | imported | path callable, pool → reading |
| `segment.py` | A combination's daily path on one calendar segment at the weights build gave it — what both verdicts and the contract's Cartera tab read; kept out of `real.py`, which cuts the universe once, to build (`tests/test_portfolio_segments.py`) | imported | daily, calendar, members, segment → paths, days |
| `handoff.py` | The hand-off package of PLAN §2.2 in `<run>/handoff/`: `portfolio.json` (members with version, feed and clock, weights, the verdict's label and sentence, ledger study and N, relaxed, development), `daily.parquet` (long, every segment), `trades.parquet` | imported | run, pool, members → three files |
| `walkforward.py` | The weight walk-forward's maths (M8): test windows from the first test day then every `wf.step_years` on 1 January, each method's path held from the first window (`fixed`) and re-estimated at each (`reestimated`), each arm's Sharpe against equal weight's with a paired stationary-bootstrap interval, and `decide` — DECISIONS #5's reversal condition read literally | imported | unit daily frame, methods → paths, table, states |
| `wf.py` | THE COMMAND of M8: a portfolio's weights estimated on build and tested on oos1 (never oos2), every `weights.REGISTRY` method fixed and re-estimated against equal weight; asks `gate.allow` for both segments, logs one ledger row per segment (the oos1 row counts every arm), writes `weights_wf/<stamp>_<pool>_K<k>_<hash>/` and prints the decision. Reports only: `weights.method` stays `equal`; refuses without `wf.confidence` | `python3 -m portfolio.common.construct.wf --pool <name> (--run <run folder> \| --members a,b,c) --set wf.confidence=<c> [--firm F] [--set k=v]` | a pool and a portfolio → table.parquet, weights.parquet, result.json, ledger rows |
| `config.yaml` | Every knob; correlation thresholds as `ledger:<key>` | edited, or `--set section.key=value` | — |

**Layers import one way** (PLAN §3): `inputs/` → `equity/` → `pairs/` → `search/`; `weights/` imports
nothing of the engine; `verdict/` never imports `search/` or `equity/` — the orchestrators (`many.py`, `funded_verdict.py`) draw the null and hand it the figures. No `studies.*`, no `ui.*`.

## Traps
- **Only `equal` can be selected.** `inputs/config.load` refuses any other `weights.method`: a method must first pass `wf.py` and
  the owner selects it (PLAN §5.4). `wf.py` calls the methods through `weights.REGISTRY`, not through the knob.
- **The walk-forward's arms are not corrected for their number** and are compared on Sharpe alone; with a test segment shorter
  than `wf.step_years` (AlphaForge's 3) there is one window and the two arms are the same path — the output says so.
- **The walk-forward's ledger rows carry `score_unit: sharpe_weight_arm`**: they count in N and stay out of the pooled sigma
  the oos2 deflation reads (seven weightings of one portfolio would only narrow it).
- **oos2 is spent per pool, by whichever path gets there first.** The guard is the pool's ledger
  study (`PORTFOLIO_<hash>_construct`): after one verdict of either path has read oos2, every
  other portfolio of that pool — the real one, another plan's — is refused. A pool scoped by
  `--firm` hashes differently when a prohibition drops a member, so it has its own read.
- **`funded_b` overwrites its run folder and its winner is not stable.** 🔬 2026-10-05, `Test_nikkei_ref` (test root): three
  runs on one stage-A folder gave three winners (finalists within 0.003 of P(pass)); the run after the oos2 read chose
  another portfolio, was refused the segment, and its `verdict.json` and `handoff/` replaced the judged one's. The reading
  itself survives in the pool study's oos2 row (`thresholds`, with the members).
- **A second verdict re-reads oos1** (fresh draws, a new ledger row) and answers oos2 from the row.
- **The oos2 Sharpe is deflated by the spread of the pool's build Sharpes**, which only
  `real.py` writes: a pool searched by the funded path alone has none, and its verdict stops at
  «SIN VEREDICTO … no guarda Sharpes de build» without opening oos2.
- **«Deflated Sharpe > 0»** is the Sharpe minus the expected maximum of N trials (DSR > 0.5), not
  DSR > 0.95; the row keeps both (`verdict/deflate.py`).
