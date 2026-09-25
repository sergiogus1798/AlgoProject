---
q: mark OOS range in a task, OutOfSample Range xml, one retest IS and OOS single cost, Setup spread slippage, split OOS multiple ranges
tag: 🔬  date: 2026-09-23  see: sqx-format/retest-rewrites-sqstats, costs/per-task-costs
---
# A task's OOS span is `<OutOfSample><Range/></OutOfSample>` under `<Data>` — not used here
Sits beside `<Setups>`, not inside a `<Setup>`. Self-closing (`<OutOfSample showGraph="false" />`) when
unmarked; one or more `<Range dateFrom dateTo/>` when marked. ⚠️ A `<Setup>` has ONE spread and ONE
slippage, so an IS+OOS window gets a single cost. 📓 Owner's choice: separate windows (IS in the builder's
databank, OOS in the retest's), joined at export.

## Evidence
- Master projects `AUDJPY` and `EURUSD` use it; `Retester` carries up to **nine** Ranges (split OOS allowed).
- With one cost the OOS tier applies (the deciding span is never cheapened), IS gets dearer and no longer
  matches the builder's backtest at build spread. Implemented and reverted 2026-09-23 at the owner's request.
