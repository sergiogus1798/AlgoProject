# portfolio/common/construct — the portfolio construction engine

Which strategies of a declared pool go together, chosen reading only `build` and judged on
`oos1`+`oos2`. The plan is `portfolio/PLAN.md` (what and why); `portfolio/EXECUTION.md` freezes
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
| `verdict/` | where does the chosen combination sit, out of sample, among searches run on random combinations |

| file | what it does | run it | in → out |
|---|---|---|---|
| `candidates.py` | Lists every archivable survivor and near-survivor of every step, with the exact archive command for each; runs none (M0) | `python3 -m portfolio.common.construct.candidates [--project P]` | reports' `verdict.csv` → printed commands |
| `universe.py` | Builds (or finds cached) a pool's universe and prints, for the owner, who was kept or excluded and why, the reconciliation per member, the calendar and the clocks | `python3 -m portfolio.common.construct.universe --pool <name> [--set k=v]` | pool → `AlgoData/portfolio/universe/<hash>-<cfg>/` |
| `funded.py` | The funded search, stage A: universe → members sized at fixed risk (no step-24 stop → excluded, named) → pair screen → greedy seeds + GA scored by P(pass) of one plan within 126 days → `runs/`, ledger rows, the best 10 printed | `python3 -m portfolio.common.construct.funded --pool <name> --plan hantec:enhanced:10000:USD` | pool, plan → `AlgoData/portfolio/runs/<stamp>_<pool>_<plan>/` |
| `funded_b.py` | Stage B and the funded verdict on an existing stage-A run (F3, F4): the diverse shortlist, each finalist under three Monte Carlos (D, T1, T2) at every block length and risk per phase, the winner and its stability — the winner's reported P(pass) is `p_fresh`, the stability re-draws' mean on fresh paths from an independent seed, never the selector's `p` (the best of shortlist × risks noisy figures reads high: +0.025 on a pool of clones at 400 paths); then, when oos1 and oos2 exist, the winner against the selected null and «did the diversification hold». No pass bar until the owner sets one (Q11). 🤔 synthetic pools only so far | `python3 -m portfolio.common.construct.funded_b --run <run folder> --set stageb.shared_of=smaller --set stageb.t1_gap=close_to_open_blocks` | stage-A run → `shortlist.parquet`, `stageb.parquet`, `verdict.json` next to it |
| `config.yaml` | Every knob; correlation thresholds as `ledger:<key>` | edited, or `--set section.key=value` | — |

**Layers import one way** (PLAN §3): `inputs/` → `equity/` → `pairs/` → `search/`; `verdict/`
never imports `search/` or `equity/`. No `studies.*`, no `ui.*`.
