# studies/readings/conditionalMap — where on the market's state grid a strategy earns

Encargo 14, item 6 of the owner's `TRADE_LEVEL_TESTS.pdf`. Classifies each trade by the market
state **at entry**, using only information available then, and reads mean P&L, its bootstrap
interval and the hit rate cell by cell. **It is the only test of the PDF that fabricates
hypotheses instead of testing one** — descriptive, never a filter, never a verdict.

| file | what it does | run it | in → out |
|---|---|---|---|
| `report.py` | **The command**: one strategy's map, printed and written to `reports/<P>/<D>/<day>/conditionalMap/estrategias/` | `python3 -m studies.readings.conditionalMap.report --harvest ~/Desktop/AlgoData/harvest/<project>/<databank>/<day> --strategy "Strategy 14.19.58"` | harvest + bars → map |
| `one.py` | The measurements — trades located, tercile at entry, cell stats — as the contract's data | imported — the window calls it | harvest + bars → result |
| `contract.py` | The two tabs (volatilidad x tendencia, día de la semana), the multiple-comparisons warning and the glossary | imported | numbers → tabs |
| `tooltips.py` | One sentence per `config.yaml` knob, for the window's configuration drawer | imported | — |
| `inputs.py` | The knobs, one strategy's trades located on the harvest, its identity | imported | harvest + bars → located trades |
| `regime.py` | Daily volatility (ATR) and trend (efficiency ratio), and the tercile edges frozen on the asset's build segment | imported | bars → terciles |
| `cells.py` | Per-cell trades, mean P&L with its bootstrap interval and hit rate, floored at `engines/nulls`'s own minimum cell size | imported | trades + terciles → cells |
| `config.yaml` | Every tunable, grouped by the layer that reads it | edited, or `--set section.key=value` | — |

Manual page, in Spanish: `docs/manual/53-mapa-condicional.md` — **read the warning at its top
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
   copied (`cells.MIN_CELL`), so the two floors cannot quietly drift apart. A cell below it is
   left out of the grid and out of the table — not shown at zero, not shown at all.
3. **No filter leaves here.** The result carries no `verdict` block; every block is `state:
   "info"`. A cell that looks striking is a question for the owner, and a filter built on it
   is a new entry in `ledger/thresholds.yaml`, revalidated on data this map has not touched.

## What is not built, and why

**Session (Asia / Londres / Nueva York / solape) is not one of the two cuts.** The asset's
`session` field (`assets/symbols/<SYMBOL>.yaml`) names an SQX session — `USDJPY_ftmo`,
`XAUUSD_ftmo` — and what that resolves to inside the project (`<Resources><Sessions>`, read
2026-09-26 off the frozen XAUUSD donor) is the broker's trading week: Monday to Friday,
01:05–23:50, not a partition of the day into Asia/London/New York/overlap. Building that
partition needs UTC hour boundaries this repository does not hold anywhere, and CLAUDE.md rule
11 forbids inventing them. **Weekday is built in its place**, from the same field's week; the
session cut is flagged on `_coord/BOARD.md` and left for the owner to fix the hours before it
is added.

## What it reuses

- `engines/nulls/inputs.py` for the same minimum-cell floor, read not copied.
- `engines/regimes/regime.py` for the volatility model: daily ATR, zero fitted parameters, the
  same one `studies/breakage/mcRetest`'s family D reads.
- `core.barstore.read` for the bars, `core.surface.dedupe.bootstrap_ci` for every interval.
- The harvest the gate already wrote (`studies/screening/gate/harvest.py`): trades keyed by
  identity, joined to a strategy name in `metrics.parquet` — no live SQX install is touched.
