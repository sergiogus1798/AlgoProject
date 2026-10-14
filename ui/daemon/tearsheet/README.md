# ui/daemon/tearsheet — the Ficha of one strategy, from the newest cosecha

Order items 1 and 2 of `scratch/ui-order-2026-09-27.md`, trimmed by the owner on 2026-09-28: what
the harvest holds about the strategy SELECTION names, as two contract results the window draws
with `blocks.ResultView`. Per sample, three blocks: «P&L acumulado» (SQX's daily curve, dashed again
without its best X % of trades when `top` is set), «Drawdown» (SQX's curve below its peak, in % or in $) and «P&L por año» (columns). The
monthly grids, the facts table, the rolling windows, the 5 % concentration bar and the episodes
table were removed with it. Arithmetic only (cumulative sums, drawdowns, yearly sums); no study.

```
api ─▶ harvest.read (newest harvest/<P>/<D>/<day>/, pyarrow filter on identity, IS/OOS asserted)
     ├ sheet.build ─▶ pnl.curves
     │              · drawdowns.underwater · months.monthly/yearly     (tabs «IS», «OOS»)
     └ exits.build ─▶ tradestats.by_exit · exit_paths                  (tabs «IS», «OOS»)
```

**Imports from:** `core.paths`, `core.study` (`result.tab`, `blocks.validate`), `ui.daemon.strategy`
(`archived`, `costcurve`) · **Consumed by:** `ui/desktop/studypage/ficha.py` (`/api/tearsheet`),
`ui/desktop/portfolios/studies.py` (both routes, `source=archive`), `ui/daemon/strategy/stats.py`
(`oos2`, `tradestats`)

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | The Ficha of one strategy: its tear sheet and its exits, read from the newest cosecha. | — | — |
| `api.py` | The Ficha's routes: one strategy's tear sheet, and its P&L by exit reason, from the newest cosecha or the archive. | imported | request → contract dict |
| `borrow.py` | A test databank's strategy read from a cosecha of the project — same XML first, else by name — and said so. | imported by `harvest.read` | roster + cosecha → (databank, identity, note) |
| `drawdowns.py` | Drawdown arithmetic on one sample's daily cumulative P&L: the distance below the running peak. | imported | daily curve → series |
| `exits.py` | P&L and expectancy by exit reason as a contract result: tabs «IS» and «OOS», each on its own. | imported | harvest rows → result |
| `harvest.py` | One strategy of a databank's newest cosecha: its daily curve, its trades and its SQX metrics. | imported | disk → dict · sentence |
| `months.py` | Calendar arithmetic on one sample's daily cumulative P&L: months and years. | imported | daily curve → months, years |
| `oos2.py` | OOS2 for the Ficha, read from a cosecha that carries it — sealed until 17-19 only for an autonomous agent (`ledger.gate.enforced`). | imported | project, identity → dict · sentence |
| `pnl.py` | One sample's cumulative P&L: SQX's daily curve, with or without its best trades. | imported | curve, trades → series |
| `sheet.py` | The Ficha of one strategy as a contract result: tabs «IS» and «OOS», each computed on its own. | imported | harvest rows → result |
| `tradestats.py` | Trade arithmetic on one sample: starting capital, exits, and the per-trade return and its shape. | imported | trades → numbers |

Test: `python3 tests/test_ui_tearsheet.py` — both routes on
`harvest/Test_USDJPY_donchianUpperCrossUp_M30/Results/2026-09-28/` (≈0.3 s warm): the three
blocks per sample, years summing to the curve, two series with `top`,
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
- **A databank without a cosecha borrows one** (`borrow`), never a red «no tiene cosecha» while
  the project has the strategy harvested: same identity first, then the name (identities differ
  across databanks, `knowhow/sqx-format/identity-differs-across-databanks.md`). Both routes take
  an optional `strategy` for the name. A databank WITH its own cosecha is read by identity only.
- **Two P&L totals, two sources.** The P&L, the drawdown and the years read `equity.parquet`
  (SQX's daily curve from the .sqx); the exits sum `trades.parquet`. They differ by tens of dollars
  on real strategies, and each note names its source.
- **% drawdown needs the account.** The P&L curve peaks at 0 on day one, so the percentage is
  of the balance at the peak: capital (first `Balance` − its `Profit/Loss`) plus the peak P&L;
  a sample without trades falls back to $.
- **Exit types are the export's words.** Grouped on `Close type` as written, with no renaming
  table that would drop a new type; the category dtype is cast to text so absent categories
  do not appear as empty rows.
- **Titles never judge.** Columns and lines carry the sample's colour, never a verdict's.
