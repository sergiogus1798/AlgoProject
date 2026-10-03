---
q: Where is a task's out-of-sample span stored: `<OutOfSample><Range/></OutOfSample>` under `<Data>`?
kw: mark OOS range in a task, OutOfSample Range xml, one retest IS and OOS single cost, Setup spread slippage, split OOS multiple ranges
tag: 🔬  date: 2026-10-02  see: sqx-format/retest-rewrites-sqstats, costs/per-task-costs
---
# A task's OOS span is `<OutOfSample><Range/></OutOfSample>` under `<Data>` — not used here
Sits beside `<Setups>`, not inside a `<Setup>`. Self-closing (`<OutOfSample showGraph="false" />`) when
unmarked; one or more `<Range dateFrom dateTo/>` when marked. ⚠️ A `<Setup>` has ONE spread and ONE
slippage, so an IS+OOS window gets a single cost. 📓 Owner's choice: separate windows (IS in the builder's
databank, OOS in the retest's), joined at export.
Trap: the frozen donor carries XAUUSD's oos1 (2018-2022) in this element. Cloned for an asset whose oos1 has other
years (indices 2020-2023) a retest splits into two sample blocks at the wrong date; the builder rewrites the Range
to the card's oos1 (`sqx/projects/setups.py`, `OOS_RANGE`, 2026-10-02, 📓 calibration of steps 6-8).

## Evidence
- Master projects `AUDJPY` and `EURUSD` use it; `Retester` carries up to **nine** Ranges (split OOS allowed).
- With one cost the OOS tier applies (the deciding span is never cheapened), IS gets dearer and no longer
  matches the builder's backtest at build spread. Implemented and reverted 2026-09-23 at the owner's request.
