---
q: where are SQX trading sessions stored; session EURUSD_ftmo not defined in any project; ninguna tarea define la sesión; Data Manager sessions database; data.db SESSIONS ELEMENTS; FTMO sessions of every asset; builder refuses session; borrow session from master
tag: 🔬  date: 2026-10-02  see: costs/swap-types, sqx-drive/three-install-topology
---
# Every broker session SQX knows is in the install's `user/data/data.db`, not in the projects
A project carries only the sessions its tasks use; the full catalogue is the Data Manager's SQLite file.
The master's `user/data/data.db` holds 1,083 sessions, **102 of FTMO** — every `session:` an asset card names.
Tables: `SESSIONS(SESSION, BROKER_ID)`, `ELEMENTS(SESSION, DAYFROM, TIMEFROM, DAYTO, TIMETO, EOD)`, `BROKER`.
Mapping to the task XML: day 1..5 = Mon..Fri, time is an integer HHMM (105 = 01:05), EOD 1 = `true`.
Read a COPY of the file (the master's GUI holds it); sessions are among the three things taken from the master.
So a session missing from every `project.cfx` is not missing from SQX: build its `<Session>` block from the DB.

## Evidence
- 🔬 `XAUUSD_ftmo` in the DB — five rows `(day, 105, day, 2350, 1)` — equals the block in the master's
  `XAUUSD/project.cfx`: `<Element dayFrom="Mon" dayTo="Mon" timeFrom="01:05" timeTo="23:50" eod="true" />` ×5.
- 🔬 All 19 sessions the cards name exist (FX pairs and XAGUSD `01:05`/`00:05`-`23:50/55`, the five
  `*.cash` indices and `USOIL.cash` 01:05-23:50, `UKOIL.cash` from 03:05; `GER40.cash` closes 22:50 on Friday).
  Generated blocks: `AlgoData/scratch/sessions/ftmo_sessions.xml`.
- 📓 2026-10-01: 122 of 160 calibration builds failed with «ninguna tarea de este proyecto define la
  sesión `<SYM>_ftmo`» because `doctrine.borrow_session` only looks inside project files. Open: give it
  the DB as its fallback source (OPEN.md #93).
