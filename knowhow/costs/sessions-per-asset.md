---
q: session missing for asset builder refuses; unify_sessions; borrow session from another asset; --session-from; builder finds session automatically; --symbol does not switch market; GBPUSD AUDUSD USDCAD no session; Asia London New York overlap hours
tag: 🔬  date: 2026-09-27  see: authoring/donor-clone-market, costs/per-task-costs, export/feed-clock-timezones
---
# A session and its feed are borrowed whole from a project SQX wrote — never invented
The XAUUSD donor has only gold's sessions and feed. For another asset the builder copies the session
AND the feed's `<Symbol>` from a project holding both: `--session-from`, or by default (2026-09-27,
`sqx/projects/source.py`) the newest such `project.cfx` on any install. Session alone was the trap:
gold built at gold's spread on USDJPY hours (`OPEN.md` §35). No project for GBPUSD, AUDUSD, USDCAD,
EURUSD → the builder refuses; register the session in SQX first. A session is the broker's trading
**week**; the Asia/London/NY day split is the owner's, in `conditionalMap/config.yaml`.

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
