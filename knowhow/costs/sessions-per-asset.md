---
q: session missing for asset builder refuses; unify_sessions; borrow session from another asset; clone donor for non-gold asset; --symbol does not switch market; GBPUSD AUDUSD USDCAD no session
tag: 🔬  date: 2026-09-23  see: authoring/donor-clone-market, costs/per-task-costs
---
# A session cannot be borrowed — and fixing the session does not switch the market
- `sqx.projects.doctrine.unify_sessions` copies a session only between tasks of one project; `None` if none defines it → builder refuses.
- The XAUUSD donor has only `XAUUSD_ftmo`, `XAUUSD_the5ers` → no clone of it can build a non-gold asset.
- ⚠️ Trap: borrowing `USDJPY_ftmo` into the gold donor made `builder` succeed yet it still built `XAUUSD_DukasM1_Infinox` at gold's spread with USDJPY hours — `--symbol` never switches the market (`OPEN.md` issue 35).
- GBPUSD, AUDUSD, USDCAD have no session anywhere on this machine: register one in SQX first. The code never invents hours (deliberate).

## Evidence
Donor `projectsBackup/XAUUSD_base_2026-09-21`. 📓 Sessions per master project (`.cfx`):

| session | defined in |
|---|---|
| `USDJPY_ftmo`, `USDJPY_the5ers` | `USDJPY` |
| `EURUSD_the5ers` | `EURUSD` |
| `AUDJPY_the5ers` | `AUDJPY` |
| `CADJPY_the5ers`, `EURJPY_the5ers`, `GBPJPY_the5ers`, `USDCHF_the5ers` | `CADJPY_H1`, `EURJPY_H1`, `GBPJPY_H1`, `USDCHF` |
| `XAUUSD_ftmo` | `XAUUSD`, `Retester`, frozen donor |
