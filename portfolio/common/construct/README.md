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
| `candidates.py` | THE COMMAND: list every archivable survivor and near-survivor of every workflow step; runs none. | `python3 -m portfolio.common.construct.candidates [--project P]` | reports' `verdict.csv` → printed commands |
| `funded.py` | THE COMMAND: build a funded portfolio -- universe, sizing, pair screen, greedy seeds + GA. | `python3 -m portfolio.common.construct.funded --seed N --pool <name> --plan hantec:enhanced:10000:USD [--firm hantec] --set funded.open_risk_cap=<fraction>` | pool, plan → `AlgoData/portfolio/runs/<stamp>_<pool>_<plan>/` |
| `funded_b.py` | THE COMMAND: stage B and the funded verdict on an existing stage-A run. | `python3 -m portfolio.common.construct.funded_b --seed N --run <run folder> --set funded.open_risk_cap=<fraction> --set stageb.t1_gap=close_to_open_blocks` | stage-A run → `shortlist.parquet`, `stageb.parquet`, `verdict.json`, `handoff/` next to it |
| `funded_verdict.py` | The funded verdict (F4, Q11 d): stage B's winner on oos1 against the selected null, then oos2 once. | imported | world, stage B, null winners → judged, nulls, verdict |
| `handoff.py` | The hand-off package encargo 33 receives (PLAN §2.2): the chosen portfolio, its daily P&L, its trades. | imported | run, pool, members → three files |
| `many.py` | The real path's verdict on a chosen portfolio (M5): oos1 against random portfolios, then oos2 once. | imported | `report.load()`'s inputs → verdict, sentence, population |
| `oos2.py` | The one read of `oos2` (PLAN §5.5, Q11 d): the door, the ledger's count, the row that spends it. | imported | path callable, pool → reading |
| `real.py` | THE COMMAND: choose a portfolio by ranks on build (M3) -- universe, sizing, pair screen, search. | `python3 -m portfolio.common.construct.real --seed N --pool <name> [--firm <firm>] [--base <run folder>]` | pool → `AlgoData/portfolio/runs/<stamp>_<pool>_real/` |
| `report.py` | THE COMMAND: a pool's portfolio by ranks and its verdict (M5) -- search, oos1, oos2 once, hand-off. | `python3 -m portfolio.common.construct.report --seed N --pool <name> [--firm <firm>] [--run <run folder>]` | pool → the run folder's `verdict.json`, `cartera.*`, `handoff/` |
| `segment.py` | A combination's daily path on one calendar segment, at the weights `build` gave it (the verdicts read it). | imported | daily, calendar, members, segment → paths, days |
| `universe.py` | THE COMMAND: build (or report the cache of) one pool's universe, in Spanish for the owner. | `python3 -m portfolio.common.construct.universe --pool <name> [--firm <firm>] [--set k=v]` | pool → `AlgoData/portfolio/universe/<hash>-<cfg>/` |
| `walkforward.py` | The weight walk-forward (M8): each method held fixed and re-estimated, against equal weight. | imported | unit daily frame, methods → paths, table, states |
| `wf.py` | THE COMMAND: the weight walk-forward (M8) -- does any method beat equal weight on oos1, fixed or only re-estimated. | `python3 -m portfolio.common.construct.wf --seed N --pool <name> (--run <run folder> \| --members a,b,c) --set wf.confidence=<c> [--firm F] [--set k=v]` | a pool and a portfolio → table.parquet, weights.parquet, result.json, ledger rows |
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

## Con supervivientes reales

The whole engine on a real pool, in order (each step reads the previous one's folder; real root, full defaults,
nothing here is `nice`d or shrunk). Rehearsed 2026-10-15 in the test root on `Test_nikkei_ref`
(`ALGO_DATA_ROOT=~/Desktop/AlgoData/portfolio/_test/root`, relaxed pairs, `search.seeds=20`,
`search.ga.population=20 generations=5`, `stageb.n_paths=300`, `verdict.null_draws=3`): every command below
ran and wrote its folder; M9 only registers (nothing produces fresh rows).

```bash
P=Trade_<ASSET>_<TF>_<idea>          # the project whose survivors enter; POOL=<pool name>, PLAN=hantec:enhanced:10000:USD
cd ~/Desktop/AlgoProject
python3 -m portfolio.common.construct.candidates --project $P      # prints one `core.archive archive …` per survivor; run them (SQX stopped)
python3 -m portfolio.common.construct.inputs.pool declare $POOL --added-by "<who>" --file <identities.txt>   # frozen: never re-pointed
python3 -m portfolio.common.construct.universe --pool $POOL                      # M0-M2: rebuild, licence MAE/MFE, pairs
python3 -m portfolio.common.construct.funded   --seed 1 --pool $POOL --plan $PLAN --set funded.open_risk_cap=0.5   # F1-F2, stage A
RUN=$(ls -d ~/Desktop/AlgoData/portfolio/runs/*_${POOL}_${PLAN//:/_} | tail -1)
python3 -m portfolio.common.construct.funded_b --seed 1 --run $RUN --set funded.open_risk_cap=0.5 --set stageb.t1_gap=close_to_open_blocks   # F3-F4, spends oos2 of the pool
python3 -m portfolio.common.construct.wf       --seed 1 --pool $POOL --run $RUN --set wf.confidence=0.95   # M8 (reads oos1 only)
python3 -m portfolio.common.construct.incubation.run register --run $RUN         # M9 (judged runs only)
# the real path (M3-M5) is `real` then `report --seed 1 --pool $POOL`; it needs its OWN pool or a pool whose oos2 is still unspent
```

**Sizing without a stop (2026-10-15, OPEN #113 (1), owner K1 = A):** `inputs/risk.py` sizes each member by
its worst build day of floating loss (`worst_day`: the sum of the MAE of the build trades closing that day,
SQX dollars at SQX's own money management) and `factor = 1 / worst_day`. So a level `r` of the risk grid
means «this member's worst build day costs `r` of the initial balance», and `funded.open_risk_cap` bounds the
SUM of those worst days, members × r, against the plan's daily-loss room (`search/stagea.open_cap`). The
grid's and the cap's comments in `config.yaml` still speak of stops: same numbers, new meaning. Not yet run on
the rehearsal pool (no engine run while the campaign holds the machine).
