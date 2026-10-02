# studies/readings/conditionalMap — where on the market's state grid a strategy earns

Encargo 14, item 6 of the owner's `TRADE_LEVEL_TESTS.pdf`. Classifies each trade by the market
state **at entry**, using only information available then, and reads mean P&L, its bootstrap
interval and the hit rate cell by cell. **It is the only test of the PDF that fabricates
hypotheses instead of testing one** — descriptive, never a filter, never a verdict.

| file | what it does | run it | in → out |
|---|---|---|---|
| `report.py` | **The command**: one strategy's map, printed and written to `reports/<P>/<D>/<day>/conditionalMap/estrategias/` | `python3 -m studies.readings.conditionalMap.report --harvest ~/Desktop/AlgoData/harvest/<project>/<databank>/<day> --strategy "Strategy 14.19.58"` | harvest + bars → map |
| `one.py` | The measurements — trades located, tercile at entry, cell stats — as the contract's data, once per option of the «Muestra» selector (`samples`) | imported — the window calls it | harvest + bars → result |
| `contract.py` | The two tabs (volatilidad x tendencia; sesión y día de la semana), each with the «Muestra» selector, every floored cell written «< 30 ops», the multiple-comparisons warning and the glossary | imported | numbers → tabs |
| `sessions.py` | Each entry's session: feed clock → UTC → Tokyo, London and New York local hours | imported | entry times → session labels |
| `tooltips.py` | One sentence per `config.yaml` knob, for the window's configuration drawer | imported | — |
| `inputs.py` | The knobs, one strategy's trades (every harvested sample) located on the harvest, its identity | imported | harvest + bars → located trades |
| `regime.py` | Daily volatility (ATR) and trend (efficiency ratio), and the tercile edges frozen on the asset's build segment | imported | bars → terciles |
| `cells.py` | Per-cell trades, mean P&L with its bootstrap interval and hit rate, floored at `engines/nulls`'s own minimum cell size | imported | trades + terciles → cells |
| `config.yaml` | Every tunable, grouped by the layer that reads it | edited, or `--set section.key=value` | — |

Manual page, in Spanish: `docs/manual/06-lecturas.pdf` (cap. 53-mapa-condicional) — **read the warning at its top
before reading anything else in it.**

## The three rules, and how this module keeps them (encargo 14 §1)

1. **No look-ahead.** Two layers. First, `regime.volatility()` and `regime.efficiency()` are
   lagged one full day (`regime._shift`): a trade entering day D reads the value as it stood
   at D-1's close, never D's own candle — `engines.regimes.regime.daily()` folds a whole
   session into that candle, so D's own would otherwise include bars the entry could not
   have seen (found by review, 2026-09-26: 79% of one real entry day's bars postdated the
   trade). Second, the tercile edges of both series are measured once, on the asset's
   `build` segment (`assets/_policy.yaml`), and frozen. Every trade of every sample —
   `build`, `oos1`, whatever `run.sample` names — is compared against that one fixed pair of
   numbers, never against the distribution of the sample being described.
2. **Minimum cell size**, read from `engines/nulls/config.yaml#verdict.min_trades` rather than
   copied (`cells.MIN_CELL`), so the two floors cannot quietly drift apart. A cell below it
   shows no P&L and is left out of the table — but it says so (owner, 2026-10-01): the grid
   writes «< 30 ops» in it and a note under the map counts them, and a session or weekday
   bar under the floor is named, with its trades, in the note under its chart.
3. **No filter leaves here.** The result carries no `verdict` block; every block is `state:
   "info"`. A cell that looks striking is a question for the owner, and a filter built on it
   is a new entry in `ledger/thresholds.yaml`, revalidated on data this map has not touched.

## Two samples, one selector

**«Muestra»: OOS1 / Completa** (owner, 2026-10-01). `run.sample` (OOS1) is what the map opens
on; «Completa» is every trade the harvest holds for the strategy — `IST` (build) plus `OOS1`,
the whole backtest the gate harvested; `oos2` is never harvested. Both are computed in one run
and tagged `select: {"sample": ...}`, so the window switches without calling the study again.
On the 15 USDJPY H1 mothers, OOS1 alone clears the floor in 0–4 of the 30 session x weekday
cells and the full sample in 10–23 (🔬 2026-10-01). The tercile edges stay the build segment's
in both, so in the full sample the build segment's own days split a third per tercile by
construction, and whatever a cell shows there may be part of what the build fitted.

## Sessions — and the clock they are read in

The third cut (owner, 2026-09-26) splits the day by where Tokyo (09–18), London (08–17) and New
York (08–17) are open, each in its own local time: Asia · Asia-London overlap · London ·
London-NY overlap · New York · out of session (`sessions.py`). **Trade times are not UTC**: SQX
stamps a feed in the broker's zone — `EET` for Infinox, `Asia/Jerusalem` for the5ers, `EETUS`
(New York + 7 h, no IANA name) for Brent — read from SQX's data registry by
`sqx.inspect.feeds.timezone`, so each entry goes feed clock → UTC → city clock. An hour the feed's
clock repeats or skips at a change of time is left unassigned, not guessed. The weekday stays the
feed's own. The tab carries three views — session x weekday, sessions alone, weekdays alone — for
the window to switch between; the crossed grid is shown only when some cell clears the floor.

## What it reuses

- `engines/nulls/inputs.py` for the same minimum-cell floor, read not copied.
- `engines/regimes/regime.py` for the volatility model: daily ATR, zero fitted parameters, the
  same one `studies/breakage/mcRetest`'s family D reads.
- `core.barstore.read` for the bars, `core.surface.dedupe.bootstrap_ci` for every interval.
- The harvest the gate already wrote (`studies/screening/gate/harvest.py`): trades keyed by
  identity, joined to a strategy name in `metrics.parquet` — no live SQX install is touched.
