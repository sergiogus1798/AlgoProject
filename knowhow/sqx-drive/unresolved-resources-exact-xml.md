---
q: Project has unresolved resources, start refused, InstrumentInfo compared as string, getXML, Symbol block stale after feed change, decimals tickStep, Java double 1.0E-5, Broker timezone, resources from data.db, refresh
tag: 🔬  date: 2026-10-01  see: sqx-drive/renaming-feeds, sqx-drive/cannot-start-unresolved-past-data
---
# «Unresolved resources» = a task's resource XML no longer equals what SQX's registry writes
- SQX (ProjectResources.checkTaskResources) compares each `<Instruments>` entry **as text** with InstrumentInfo.getXML() of its registry; sessions likewise; brokers by timezone only; a `<Symbol>`'s nested instrument by dataType, pointValue, tickSize, tickStep, tickValueInMoney.
- So a project written before a feed's instrument, timezone or data broker changed refuses `action=start`, even though the build may still run.
- `sqx.projects.resources.refresh()` rewrites every `<Symbol>` of a task from `data.db` (keeping its dates), and `instrument_xml()` writes the instrument exactly as getXML(): Java number format (`1.0E-5`), `decimals` = the tick step's decimals, exchange/country/sector only when not null, `swap="null"`. The builder runs it on every task.
- Bisecting which task fails: `-project loadconfig` a one-task probe `.cfx` into a running worker, then `action=start` answers at once (`remove` deletes the folder).

## Evidence
2026-10-01, Test_XAUUSD_timeRangeBreakout2_M30 on the custodian (session algoproject-6d [900329]): accepted with `decimals="2"`, refused with `"3"`. `instrument_xml` matched SQX-written EURUSD_the5ers, USDJPY_the5ers, DJ30_Infinox and XAUUSD_Infinox character for character.
