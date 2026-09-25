---
q: builder clone of donor still trades XAUUSD; project for non-XAUUSD asset built on gold; set_costs only rewrites matching Chart symbol; resources.py borrow Symbol InstrumentInfo Broker; zero Setup on asset feed guard
tag: 🔬  date: 2026-09-24  see: sqx-drive/only-flag-wrong-databank, costs/per-task-costs, eng/feed-in-config-yaml
---
# A donor clone must have its feed swapped; `sqx.projects.builder` does it and refuses zero asset `<Setup>`s
Before 2026-09-24 a clone for another asset kept the donor's XAUUSD feed while taking the asset's
window/session/timeframe — built on gold with `spread="0"`, commission off, no error.
Fix: `sqx/projects/resources.py` borrows `<Symbol>`, `<InstrumentInfo>`, `<Broker>` from a project
already trading that feed and swaps the `<Chart>` of the donor feed only (cross-check markets keep theirs).
🤔 Any non-XAUUSD project built with the builder before that date ran on gold — check before trusting one.

## Evidence
Log: `CONSTRUCCION : Loading backtest data for Higher backtest precision - XAUUSD_DukasM1_Infinox / H1`.
Cause: `setups.py` `set_costs` rewrites only a `<Setup>` whose `<Chart symbol=…>` already is the asset.
Donor feed read from the first `<Chart>` of its Build task; same mechanism as `borrow_session`.
Guard: `builder` refuses when a task ends with zero `<Setup>` on the asset feed (count existed since 2026-09-23, unread).
`runs.csv` holds only XAUUSD runs, so probably nothing contaminated.
