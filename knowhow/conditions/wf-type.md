---
q: walk-forward type attribute 0 1 2 simulated exact IS OOS; WalkForwardMatrix type meaning; period optimization attribute codes floating fixed
tag: 🔬  date: 2026-09-24  see: conditions/active-conditions-in-crosschecks, conditions/wfm-acceptance
---
# WF `type` is the GUI's "Walk-Forward type": 0 sim/sim, 1 sim IS/exact OOS (default), 2 exact/exact (the project's)
Project uses `type="2"` (owner, 2026-09-24). What changes on the IS side is who picks each step's parameters, not decimals.
`period`: percent=10, days=20, bars=30. `optimization`: floating=15, fixed=25.
Not: `type` = "matrix vs single walk-forward" — a stock `<WalkForwardMatrix>` carries `type="1"` with ranges.

## Evidence
Enum `OptimizationConst.wfTypeToString`; behaviour from `OptimizationEngineWF`:

| `type` | GUI | what it does |
|---|---|---|
| 0 | Simulated IS, Simulated OOS (fastest) | neither re-run; orders cut from one backtest (`runSimpleSimulationRun`) |
| 1 | Simulated IS, Exact OOS (slower) — SQX default | each OOS step re-backtested with that step's params (`testStrategy(..., runFrom, runTo)`); optimisation still cut |
| 2 | Exact IS, Exact OOS (slow) | each step's optimisation runs for real on its window |

- Simulated: the winner comes from cutting one full-range batch to the step window; the cut drags the equity path (ATR sizing on running balance is not neutral) and trades open before the edge. Exact = what live would do.
- Master WFM (`lastSettings.xml` of `XAUUSD/databanks/WFM`): `type="2"`, `MaxTests` 500, precision 2, 30 cells over five years, completed.
