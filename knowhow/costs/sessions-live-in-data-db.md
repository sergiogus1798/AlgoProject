---
q: Where do SQX's broker session definitions live?
kw: where are SQX trading sessions stored; session EURUSD_ftmo not defined in any project; ninguna tarea define la sesión; Data Manager sessions database; data.db SESSIONS ELEMENTS; FTMO sessions of every asset; builder refuses session; borrow session from master
tag: 🔬  date: 2026-10-02  see: costs/swap-types, sqx-drive/three-install-topology
---
# Every broker session SQX knows is in the install's `user/data/data.db`, not in the projects
A project carries only the sessions its tasks use; the catalogue is the Data Manager's SQLite file: the
master's `user/data/data.db` holds 1,083 sessions, **102 of FTMO** — every `session:` an asset card names.
Tables: `SESSIONS(SESSION, BROKER_ID)`, `ELEMENTS(SESSION, DAYFROM, TIMEFROM, DAYTO, TIMETO, EOD)`, `BROKER`.
Mapping to the task XML: day 1..5 = Mon..Fri, time is an integer HHMM (105 = 01:05), EOD 1 = `true`.
Read a COPY of the file (the master's GUI holds it); sessions are among the three things taken from the master.
`sqx.projects.sessiondb` builds the `<Session>` block from `AlgoData/cache/sessions/data.db`, re-copied when stale.
Session (`doctrine.borrow_session`) and feed (`resources.definitions`) alike: a project that has it, then the DB, then refuse.

## Evidence
- 🔬 `XAUUSD_ftmo` in the DB — five rows `(day, 105, day, 2350, 1)` — equals the block in the master's
  `XAUUSD/project.cfx`: `<Element dayFrom="Mon" dayTo="Mon" timeFrom="01:05" timeTo="23:50" eod="true" />` ×5.
- 🔬 All 19 sessions the cards name exist (FX pairs and XAGUSD `01:05`/`00:05`-`23:50/55`, the five
  `*.cash` indices and `USOIL.cash` 01:05-23:50, `UKOIL.cash` from 03:05; `GER40.cash` closes 22:50 on Friday).
  Generated blocks: `AlgoData/scratch/sessions/ftmo_sessions.xml`.
- 📓 2026-10-01: 122 of 160 calibration builds failed with «ninguna tarea de este proyecto define la
  sesión `<SYM>_ftmo`» because `doctrine.borrow_session` only looked inside project files.
- 🔬 2026-10-02, after the fallback: the 16 sessions the cards then named all resolve from the DB; a real
  `Test_Calib_sesscheck` (EURUSD H1, custodian, then retired) carried `EURUSD_ftmo` 00:05-23:55 identical
  to the DB block, feed borrowed from the master's `USDJPY` project. `tests/test_session_from_db.py`.
- 🔬 2026-10-02: `DAX40_M1` and `USOIL.cash_M1` are the feeds no project on any install defines; the DB's
  `DATA` table has both, so `registryxml.definitions` writes their `<Symbol>`/`<InstrumentInfo>`/`<Broker>`.
  Built H1 into a temp install: DAX40 → chart `DAX40_M1`, instrument `DAX40_ftmo`, session `GER40.cash_ftmo`.
  USA500 built both ways (from the master's `SP500_H1` project, and from the DB alone): the Build task is
  byte-identical but for the temp path — `refresh` rewrites a borrowed block from the DB anyway.
- 🤔 `<Symbol barType>` is written from `DATA.DATATYPE` (1 in every row and every project seen). No project
  built by the DB route has been started in SQX yet.
- 🔬 2026-10-02: XAGUSD, UKOIL and USOIL took their FTMO session (owner); an XAGUSD H1 build into a temp
  install carried `XAGUSD_ftmo` from the DB and the feed from a project. Cross-market `<Setup>`s are
  unaffected: `crossmarket` writes `session="No Session"` whatever the card says.
