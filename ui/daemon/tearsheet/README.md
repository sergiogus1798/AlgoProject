# ui/daemon/tearsheet — the Ficha of one strategy, from the newest cosecha

Order items 1 and 2 of `scratch/ui-order-2026-09-27.md`: what the harvest already holds about the
strategy SELECTION names, as two contract results the window draws with `blocks.ResultView`.
Arithmetic only (cumulative sums, drawdowns, monthly sums, counts, a Wilson interval); no study.

```
api ─▶ harvest.read (newest harvest/<P>/<D>/<day>/, pyarrow filter on identity, IS/OOS asserted)
     ├ sheet.build ─▶ drawdowns · months · facts · tradestats   (tabs «IS», «OOS»)
     └ exits.build ─▶ tradestats.by_exit · exit_paths            (tabs «IS», «OOS»)
```

**Imports from:** `core.paths`, `core.study` (`result.tab`, `blocks.table`, `blocks.validate`) · **Consumed by:** `ui/desktop/studypage/ficha.py`

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Names the package; holds no code | — | — |
| `api.py` | `ROUTER`: `GET /api/tearsheet` and `GET /api/tearsheet/exits`, `?project&databank&identity`; a refusal is `{"error"}`, never a 500 | imported | request → contract dict |
| `harvest.py` | The newest cosecha of (P, D), one identity's equity, trades and metrics row; refuses a sample outside IS/OOS; the sentence naming the harvest command when there is none | imported | disk → dict · sentence |
| `drawdowns.py` | Underwater in money and in % of the account's peak, the deepest episodes, the longest flat spell, each year's max DD, days to the first close above 0 | imported | daily curve → numbers |
| `months.py` | Monthly P&L exact to the cent, years, rolling 3/6/12/24-month windows, the year × month layout | imported | daily curve → months |
| `tradestats.py` | Starting capital, win rate with its 95 % Wilson interval, the best 5 %'s share of the net, the per-exit table and one cumulative path per exit type | imported | trades → numbers |
| `facts.py` | The facts table (months, years, SQX Sharpe, flat spell, annual DD, first high, win rate, both P&L totals), the rolling table, the concentration bar with Dennis' 95 % | imported | numbers → blocks |
| `sheet.py` | The Ficha: one tab per sample — curve, underwater ×2, episodes, monthly grid, yearly bars, facts, windows, concentration | imported | harvest rows → result |
| `exits.py` | «Salidas»: one tab per sample — the per-exit table and the cumulative line per exit type | imported | harvest rows → result |

Test: `python3 tests/test_ui_tearsheet.py` — both routes on
`harvest/USDJPY_workflow_profiling_v1/Results/2026-09-26/` (≈0.3 s warm), a hand-checked
episode, months summing to the curve to the cent, exits summing to the trades, the refusals on
synthetic cosechas, and the Ficha drawn offscreen (grabs `scratch/ui-plan/shots/H1-*.png`).

## Contracts and traps

- **IS and OOS never meet.** Each sample is filtered first and computed alone; each starts at 0.
  A sample value other than `IS`/`OOS` in the identity's rows refuses the whole answer (the
  one-way door: oos2 is never read).
- **An identity pairs only inside its databank** (`knowhow/sqx-format/identity-differs-across-databanks.md`).
  The harvest is keyed by the build databank's identity; asked with another databank's, the
  route says the strategy is not in the cosecha, it never looks elsewhere.
- **Two P&L totals, two sources.** The months sum `equity.parquet` (SQX's daily curve from the .sqx)
  to the cent; the exits sum `trades.parquet`. They differ by tens of dollars on real strategies
  (Strategy 22.18.65 IS: 59 291.63 vs 59 690.75), so the facts table shows both and each note
  names its source.
- **% underwater needs the account.** The P&L curve peaks at 0 on day one, so the percentage is
  of the balance at the peak: capital (first `Balance` − its `Profit/Loss`, 100 000 on
  `USDJPY_workflow_profiling_v1`, both samples) plus the peak P&L.
- **Exit types are the export's words.** Grouped on `Close type` as written, with no renaming
  table that would drop a new type; the category dtype is cast to text so absent categories
  do not appear as empty rows.
- **Titles never judge.** Bars are all `info`; the Dennis line and Chan's remark are named as
  book references in the notes, not thresholds.
