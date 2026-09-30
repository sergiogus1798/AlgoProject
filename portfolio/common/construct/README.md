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

| file | what it does | run it | in → out |
|---|---|---|---|
| `candidates.py` | Lists every archivable survivor and near-survivor of every step, with the exact archive command for each; runs none (M0) | `python3 -m portfolio.common.construct.candidates [--project P]` | reports' `verdict.csv` → printed commands |
| `universe.py` | Builds (or finds cached) a pool's universe and prints, for the owner, who was kept or excluded and why, the reconciliation per member, the calendar and the clocks | `python3 -m portfolio.common.construct.universe --pool <name> [--set k=v]` | pool → `AlgoData/portfolio/universe/<hash>-<cfg>/` |
| `funded.py` | The funded search, stage A: universe → members sized at fixed risk (no step-24 stop → excluded, named) → pair screen → greedy seeds + GA scored by P(pass) of one plan within 126 days → `runs/`, ledger rows, the best 10 printed | `python3 -m portfolio.common.construct.funded --pool <name> --plan hantec:enhanced:10000:USD` | pool, plan → `AlgoData/portfolio/runs/<stamp>_<pool>_<plan>/` |
| `config.yaml` | Every knob; correlation thresholds as `ledger:<key>` | edited, or `--set section.key=value` | — |

**Layers import one way** (PLAN §3): `inputs/` → `equity/` → `pairs/` → `search/`; `verdict/`
never imports `search/` or `equity/`. No `studies.*`, no `ui.*`.
