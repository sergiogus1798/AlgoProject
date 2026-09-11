# strategies/monteCarlo — how much of this result is luck, and of what kind?

One study, one folder. It runs **after** the strategy has already been accepted — it survived the
OOS decay test and the cross-market retest — and it does not ask whether the edge is real. It asks
what the edge depends on: the order the trades arrived in, which trades occurred at all, how they
were filled, and the regime they lived in.

Read `POSSIBLE_IMPROVEMENTS.md` before extending any of this, and `docs/manual/07-montecarlo.md`
before running it.

```
config.yaml ─▶ stream ─▶ draws / stress ─▶ engine ─▶ run ─▶ gates ─▶ scoring ─▶ panel
 every knob    the input   how a run is      the        the       what        how good   the
               contract    made different    numbers    result    vetoes      otherwise  report
```

The four boundaries of rule 5 of `CODESTYLE.md`, in the order the data flows: **configuration**
(`config`, `costs`), **modelling** (`draws`, `stress`, `regime`, `windows`), **execution**
(`engine`, `sweeps`, `run`, `stability`) and **inference** (`confidence`, `gates`, `scoring`).
`run.py` produces numbers and judges none of them; `gates.py` owns every threshold in the study and
computes none of the numbers it judges.

| file | what it does | run it | in → out |
|---|---|---|---|
| `config.py` | Reads `config.yaml` and scales the block sweep to the trade count | imported | overrides → config |
| `costs.py` | The asset's cost facts, the cost SQX really charged per trade, and the cross-check | imported | symbol + trades → USD |
| `stream.py` | **The input contract.** Any time-ordered trade list — one strategy or a portfolio — as the arrays every family runs on | imported | CSV → arrays |
| `metrics.py` | Net, drawdown, Ret/DD, Sharpe, profit factor and the longest losing run, on thousands of paths at once | imported | paths → statistics |
| `draws.py` | **How a stream is reordered or resampled.** Five models behind one signature, with what each preserves | imported | N → index matrix |
| `stress.py` | **Family C.** Missed entries, worse costs, degraded fills toward each trade's own MAE, wider spread | imported | stream → P&L matrix |
| `engine.py` | Runs one sub-test across every core, with a live progress bar | imported | model → statistics |
| `sweeps.py` | Which reordering and resampling runs a stream of this size gets | imported | N → runs |
| `windows.py` | The calendar slices: rolling windows, non-overlapping blocks, and the calendar split | imported | times → positions |
| `regime.py` | Daily volatility — ATR or GARCH — and the tercile each trade was opened into | imported | bars → buckets |
| `stitch.py` | The adversarial path: a bad draw from every period, concatenated | imported | stream → worst path |
| `fan.py` | The equity envelope of the reordered paths | imported | stream → bands |
| `confidence.py` | Whether the sample can hold up a number | imported | N, q → tier |
| `significance.py` | **Family E.** Probabilistic Sharpe Ratio and its cross-check against the bootstrap | imported | P&L → PSR |
| `gates.py` | **Every threshold in the study.** What vetoes, what only warns | imported | result → flags |
| `scoring.py` | Sub-scores, composite, verdict tier and the binding constraint | imported | result → verdict |
| `stability.py` | The same gate numbers computed again, to price the noise in them | imported | stream → spread |
| `run.py` | Puts one stream through all five families | imported | stream → result |
| `text.py` | The Spanish sentences: one per check that can fire, plus `montecarlo.md` | imported | result → words |
| `charts.py` | The figures as inline SVG: distributions, the equity cone, the scores, signed bars | imported | numbers → SVG |
| `panel.py` | The databank page and the shared table and shell helpers | imported | rows → HTML |
| `familypage.py` | The five family sections of one strategy's page | imported | result → HTML |
| `strategypage.py` | One strategy's page: verdict, what failed, then the families | imported | result → HTML |
| `explorer/` | The interactive panel: one strategy at a time, any test on demand. Its own README | `python3 -m strategies.monteCarlo.explorer.serve --project XAUUSD --databank Results --asset XAUUSD --export 2026-09-03` | export → `http://127.0.0.1:8765` |
| `report.py` | The command: every strategy of one databank | `python3 -m strategies.monteCarlo.report --project XAUUSD --databank Results --asset XAUUSD --export 2026-09-03` | `raw/<P>/<D>/<date>/trades/` → `reports/<P>/<D>/<date>/montecarlo[_portfolio]/` |

## What it does not do, by design

- **It does not measure overfitting.** No Deflated Sharpe, no CSCV, and there will be none here:
  both need the population of strategies tried during generation, which does not exist at this
  stage. Fabricating a trial count would produce a credible, false number. That question belongs to
  the generation study.
- **It does not validate the edge.** It assumes it and measures what it rests on.
- **It is not reproducible, on purpose.** No seed anywhere: every run draws fresh entropy.
  `stability.py` replaces reproducibility by measuring how far the gate-driving numbers move
  between independent runs — which is the question a seed hides.

## The input contract is the only contract

Every family takes a time-ordered trade list and nothing else. That is why a **portfolio** needs no
separate code: `stream.portfolio()` concatenates several strategies' trades, sorts by time, and the
same families run unchanged (`--portfolio`). `stream.overlap()` measures how often two positions
were open at once, and the report says so when they were: the additive equity curve is still valid,
but the longest losing run means something different at portfolio level.

## Costs come from the backtest, not from a guess

The trade export carries no cost column, so the cost of each trade is **recovered** as
`gross − net` (`core.trades.cost`), which is commission and swap exactly as SQX booked them. The
asset file supplies the spread and the point value, from its `sqx_default` side rather than its
`use:` side: this study stresses a backtest SQX already ran, so the costs that belong in it are the
ones that were charged in it. `costs.crosscheck()` compares the modelled commission against the
recovered one and warns when they diverge — the warning travels with the report and invalidates
Family C only, not the rest.

## Adding a way of randomising

Write a function in `draws.py` with the shared signature — `(n, size, rng, block)` in, an index
matrix out — add it to `DRAWS`, say what it preserves in `PRESERVES`, and put it in `FAMILY`. A
Family C perturbation is the same: a function in `stress.py`, a row in `MODELS`, and a floor in
`gates.py`. Nothing else changes.

The rule that keeps it honest is `KEEPS_MULTISET`: the two models that only reorder must leave net
profit identical to the last decimal. `sweeps.invariant()` measures it and every report prints it.
A non-zero there is a bug in the model, never a property of the strategy.
