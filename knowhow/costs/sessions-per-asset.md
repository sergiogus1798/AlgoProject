---
q: session missing for asset builder refuses; unify_sessions; borrow session from another asset; clone donor for non-gold asset; --symbol does not switch market; GBPUSD AUDUSD USDCAD no session; what does the session field actually resolve to; Asia London New York overlap hours
tag: 🔬  date: 2026-09-23  see: authoring/donor-clone-market, costs/per-task-costs
---
# A session cannot be borrowed — and it is not a session-of-day partition either
- `sqx.projects.doctrine.unify_sessions` copies a session only between tasks of one project; `None` if none defines it → builder refuses.
- The XAUUSD donor has only `XAUUSD_ftmo`, `XAUUSD_the5ers` → no clone of it can build a non-gold asset.
- ⚠️ Trap: borrowing `USDJPY_ftmo` into the gold donor made `builder` succeed yet it still built `XAUUSD_DukasM1_Infinox` at gold's spread with USDJPY hours — `--symbol` never switches the market (`OPEN.md` issue 35).
- GBPUSD, AUDUSD, USDCAD have no session anywhere on this machine: register one in SQX first. The code never invents hours (deliberate).
- 🔬 A session resolves to the broker's trading **week** (Mon–Fri, near round-the-clock), never a
  partition of the **day** into Asia/London/New York/overlap — that split needs UTC hours this
  repo does not have anywhere and must not invent (CLAUDE.md rule 11, encargo 14).

## Evidence
Donor `projectsBackup/XAUUSD_base_2026-09-21`. 📓 Sessions per master project (`.cfx`):

| session | defined in |
|---|---|
| `USDJPY_ftmo`, `USDJPY_the5ers` | `USDJPY` |
| `EURUSD_the5ers` | `EURUSD` |
| `AUDJPY_the5ers` | `AUDJPY` |
| `CADJPY_the5ers`, `EURJPY_the5ers`, `GBPJPY_the5ers`, `USDCHF_the5ers` | `CADJPY_H1`, `EURJPY_H1`, `GBPJPY_H1`, `USDCHF` |
| `XAUUSD_ftmo` | `XAUUSD`, `Retester`, frozen donor |

🔬 2026-09-26: `XAUUSD_ftmo`'s block is `<Element dayFrom="Mon" dayTo="Mon" timeFrom="01:05"
timeTo="23:50" eod="true" />` repeated for each of Mon–Fri — the week, not the day.
