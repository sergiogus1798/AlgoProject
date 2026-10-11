---
q: Why does `action=start` reply "Cannot start project" over unresolved resources, without saying "Error"?
kw: Cannot start project Project has unresolved resources; action=start reply not an error; launcher waits forever esperando 0 probadas; data range dateTo past last bar; verify window Hasta last day of data; which task is unresolved; InstrumentInfo decimals; feed converted EETUS generic instrument; probe a task, InstrumentInfo compared as string, getXML, Symbol block stale after feed change, Java double 1.0E-5, resources from data.db, refresh
tag: 🔬  date: 2026-10-11  see: authoring/donor-clone-market, costs/per-task-costs, sqx-drive/renaming-feeds
---
# «Unresolved resources» = a task's <Resources> disagree with the registry; `action=start` does not say «Error»
Reply «Cannot start project…» (test «Cannot start», not «rror»). SQX (`ProjectResources.
checkTaskResources`) checks each task's `<Symbol>` against `data.db` (timezone, dates, instrument
numbers), each `<Instruments>`/`<Session>` as an EXACT STRING vs its `getXML()`, each `<Broker>` by
timezone. A feed converted after cloning breaks every task naming it; `decimals` = tick step's.
Static check: `registryxml.unresolved(cfx)` lists what a start would refuse — in EVERY task, inactive ones too (📓 2026-10-06). `registryxml.clip` (from `refresh` and `set_data_range`)
cuts EVERY <Symbol> of a task to its feed's bars — main and cross-check markets (XAUUSD, UKOIL.cash in the WFM task, 2026-10-06).
A project written before a feed's instrument, timezone or data broker changed refuses `action=start` though the build might run. `sqx.projects.resources.refresh()` rewrites every `<Symbol>` of a task from `data.db` (keeping its dates); `instrument_xml()` writes the instrument exactly as `getXML()`: Java number format (`1.0E-5`), `decimals` = the tick step's, exchange/country/sector only when not null, `swap="null"`; the builder runs it on every task. Bisect: one-task probe `.cfx` → `loadconfig` into a live worker → `start` (instant) → `remove`.

## Evidence
- 🔬 2026-09-30, USDJPY (`data.to` 2026-09-25): «Verificar» to 2026-09-25 → «Cannot start project»
  on the conductor; the same strategy to 2026-09-01 ran. A `<Symbol>` `dateTo` at the midnight after
  the last day of data; `mt5.verify.run.latest` now ends the window the day before.
- 🔬 2026-10-01, Test_XAUUSD_timeRangeBreakout2_M30: all 18 one-task probes refused with the donor's
  `XAUUSD_Infinox`/EET block; with the registry's (instrument XAUUSD, broker -1, swap="null")
  `decimals="3"` refused, `"2"` accepted. XAGUSD (tick 0.001): `"3"` accepted, `"2"` refused.
  Build task with the5ers `AUDJPY_TICK` cross-check (not yet converted) accepted as it was.
- 🔬 2026-10-03, four `Test_Calib_XAUUSD_*` refused on the custodian: `_policy.yaml` had moved oos2 to
  2026-09-30, XAUUSD_M1's last bar is 2026-09-30 02:58, so the «OOS2» task's `<Symbol dateTo>` (midnight
  2026-10-01) was past it. Feeds ending 2026-10-01 02:58 started. A window may end at most the day BEFORE
  the feed's last bar. `unresolved()` flags exactly those 4 of the 19 `Test_Calib*` projects there.
- `sqx.projects.resources.refresh` (algoproject-6d, 2026-10-01) now rebuilds these from `data.db`
  at build time; a project built before a feed's conversion still goes stale.
