# ui/daemon/tearsheet — the Ficha of one strategy, from the newest cosecha

Order items 1 and 2 of `scratch/ui-order-2026-09-27.md`, trimmed by the owner on 2026-09-28: what
the harvest holds about the strategy SELECTION names, as two contract results the window draws
with `blocks.ResultView`. Per sample, three blocks: «P&L acumulado» (SQX's daily curve and the one
at the real spread and slippage, each dashed again without its best X % of trades when `top` is
set), «Drawdown» (SQX's curve below its peak, in % or in $) and «P&L por año» (columns). The
monthly grids, the facts table, the rolling windows, the 5 % concentration bar and the episodes
table were removed with it. Arithmetic only (cumulative sums, drawdowns, yearly sums); no study.

```
api ─▶ harvest.read (newest harvest/<P>/<D>/<day>/, pyarrow filter on identity, IS/OOS asserted)
     ├ sheet.build ─▶ pnl.curves ◀─ strategy.costcurve.repriced (the spread report's trades)
     │              · drawdowns.underwater · months.monthly/yearly     (tabs «IS», «OOS»)
     └ exits.build ─▶ tradestats.by_exit · exit_paths                  (tabs «IS», «OOS»)
```

**Imports from:** `core.paths`, `core.study` (`result.tab`, `blocks.validate`), `ui.daemon.strategy`
(`archived`, `costcurve`) · **Consumed by:** `ui/desktop/studypage/ficha.py` (`/api/tearsheet`),
`ui/desktop/portfolios/studies.py` (both routes, `source=archive`), `ui/daemon/strategy/stats.py`
(`oos2`, `tradestats`)

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Names the package; holds no code | — | — |
| `api.py` | `ROUTER`: `GET /api/tearsheet` (`&top=0-50&dd=%\|$`) and `GET /api/tearsheet/exits`, `?project&databank&identity&sample=&source=live\|archive&version=`; `sample` IS, OOS1 (or OOS) keeps one tab, OOS2 goes through `oos2`; the `spread` report folders live or frozen in the version; a refusal is `{"error"}`, never a 500 | imported | request → contract dict |
| `harvest.py` | The newest cosecha of (P, D), one identity's equity, trades and metrics row; refuses a sample outside IS/OOS; the sentence naming the harvest command when there is none | imported | disk → dict · sentence |
| `pnl.py` | One sample's curves on one daily index: SQX's, the real one (SQX's corrected on each closing day by the repriced trades), and each without its own best `top` % of trades | imported | curve, trades, repriced → series |
| `drawdowns.py` | Underwater in money and in % of the account's peak | imported | daily curve → series |
| `months.py` | Monthly P&L exact to the cent, and the years they add up to | imported | daily curve → months, years |
| `tradestats.py` | Starting capital, the per-exit table and one cumulative path per exit type; per-trade returns in USD per lot or per trade (`SHORT`: «$/lote», «$/trade») and their shape (mean, std, skew, excess kurtosis) | imported | trades → numbers |
| `sheet.py` | The Ficha: one tab per sample — «P&L acumulado», «Drawdown», «P&L por año», each series and column carrying its sample's `ink` (`blocks.states.CURVE`) | imported | harvest rows → result |
| `oos2.py` | The step-20 door (`ledgerview.door`) and, once open, one strategy's OOS2 rows from the newest cosecha of the project that carries them — or the sentence «OOS2 abierto, sin export» | imported | project, identity → dict · sentence |
| `exits.py` | «Salidas» (read by PORTFOLIOS only since 2026-09-28): one tab per sample — the per-exit table and the cumulative line per exit type | imported | harvest rows → result |

Test: `python3 tests/test_ui_tearsheet.py` — both routes on
`harvest/Test_USDJPY_donchianUpperCrossUp_M30/Results/2026-09-28/` (≈0.3 s warm): the three
blocks per sample, years summing to the curve, the real curve present, four series with `top`,
the drawdown's unit, exits summing to the trades, the refusals on synthetic cosechas, and the
Ficha drawn offscreen with its switches (grabs `scratch/ui-plan/shots/H1-*.png`).

## Contracts and traps

- **IS and OOS never meet.** Each sample is filtered first and computed alone; each starts at 0.
  A sample value other than `IS`/`OOS` in the identity's rows refuses the whole answer (the
  one-way door: `harvest.read` never reads oos2). OOS2 has its own reader, `oos2.read`, called
  once `oos2.blocked` says open — only under `ALGO_AUTONOMOUS=1` (`core.assetdata.enforced`); for a human it is always open (owner, 2026-09-28); sealed, the route answers
  `{"blocked": "reservado: se abre tras los pasos 17, 18 y 19"}`.
- **`source=archive` recomputes arithmetic, never a study**: the frozen `harvest.read` dict of
  `core.archive.read` goes through the same `sheet.build`/`exits.build`.
- **An identity pairs only inside its databank** (`knowhow/sqx-format/identity-differs-across-databanks.md`).
  The harvest is keyed by the build databank's identity; asked with another databank's, the
  route says the strategy is not in the cosecha, it never looks elsewhere.
- **Two P&L totals, two sources.** The P&L, the drawdown and the years read `equity.parquet`
  (SQX's daily curve from the .sqx); the exits sum `trades.parquet`. They differ by tens of dollars
  on real strategies, and each note names its source.
- **The real curve needs the `spread` report**, as the basic panel's (`strategy/costcurve`):
  without one the P&L draws SQX's curve alone and its note says so. OOS2 never has one.
- **«Sin el top X %» ranks each curve in its own column**: SQX's best trades by `Profit/Loss`,
  the real curve's by the repriced column — at least one trade, taken off on its close day.
- **% drawdown needs the account.** The P&L curve peaks at 0 on day one, so the percentage is
  of the balance at the peak: capital (first `Balance` − its `Profit/Loss`) plus the peak P&L;
  a sample without trades falls back to $.
- **Exit types are the export's words.** Grouped on `Close type` as written, with no renaming
  table that would drop a new type; the category dtype is cast to text so absent categories
  do not appear as empty rows.
- **Titles never judge.** Columns and lines carry the sample's colour, never a verdict's.
