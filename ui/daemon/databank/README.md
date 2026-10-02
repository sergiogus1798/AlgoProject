# ui/daemon/databank — the databank panel of Proyecto, SQX-style

What the bottom strip of Proyecto (encargo 22 §4.2, §4.3) reads: the two rows of tabs, one
databank as a table (a row per strategy, SQX's metrics, a column group per study), its aggregate
equity (SQX's and at Darwinex's real spread and slippage), the population's funnel, and
«Recargar databank». Read-only on disk except the owner's column choice (`columns.py`);
nothing here sends a command to SQX.

**Imports from:** `core.paths`, `core.datapaths`, `core.cfx`, `engines.variants.look`,
`sqx.projects.stage`, `pipeline.ledger.state`, `ui.daemon.{loader, results, workflow, gateview}`
· **Consumed by:** `ui/daemon/routers.py` (`ROUTER`) → `ui/desktop/workspace/`

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | The package's one-line purpose | — | — |
| `cells.py` | Every study folder of a project read into entries (verdict, state, `verdict.csv` columns, the per-task / per-market table of `mcRetest` and `crossmarket`, crossTF split by timeframe), per databank by identity and by name, and across databanks by identity; `lotes()` reads the one-off multi-mother lotes (`structure`, `atrCalculator`) `reports/` never carries, by name | imported | `reports/<P>/*/<day>/<study>/`, `structural\|atrCalculator/<P>/*/estudios/` → entries |
| `batches.py` | The studies of a mother's variant batch — `cloud`, `wfc` (each `wfc_<composition>.json` a sub-panel), `cscv`, `marketSurfaces` — keyed by her name; two batches of one mother say so instead of a figure (OPEN §51) | imported | `strategyPermutations/`, `pipeline/` → entries |
| `metrics.py` | The databank's SQX metrics: the newest cosecha (by identity, IS + OOS) or else `metrics/<P>/<D>/metrics.csv` (by name), a sample where a strategy made no trade blanked to «—» (a Cross Market/TF task files `build..oos1` under OOS; its IS was zeros painted red) | imported | parquet / csv → frame |
| `table.py` | `GET /api/databank/table`: rows = roster (or, with the files gone, the cosecha's and the reports' strategies), metric columns (a row the cosecha lacks — no OOS retest — read from the databank's metrics export by name), one column group per study; drops wfc/cscv/wfm/blindJoint while the ledger's door is shut | imported | project, databank → payload |
| `equity.py` | `GET`/`POST /api/databank/equity`: the cosecha's daily P&L summed over strategies, IS then OOS, and the same with the `spread` report's per-trade correction added by closing day; `ids` keeps only those identities (the rows a filter left visible; POST for long lists), `of` says `todas` or how many | imported | parquet → curves + stats |
| `layout.py` | `GET /api/databank/panels`: the seven tabs (WFM, WFC, CSCV and Market Surfaces merged into one window-only virtual tab since 2026-09-30 §2/§8 — no SQX project or databank changes), each sub-panel with its databank (where its study reported, else the one its stage's task writes per `project.cfx` or, with no install holding the project, the data root's folder of that name, else the build's; the batch studies on the smallest of WFM/SPP that holds every mother — the WFC tasks' databanks hold variants), one «Resumen» per tab except Cross TF's timeframes (owner, 2026-10-01: gate screens, markets, MCR tasks and WFC compositions are read in the strategy view); 17-20 locked with the ledger's sentence | imported | project → tabs |
| `funnel.py` | `GET /api/databank/funnel`: the newest gate's `funnel.csv` with each screen's why, then every later Python step `/api/workflow` counted; sealed and running steps without a count | imported | project → rows |
| `segments.py` | `GET /api/databank/segments`: the IS+OOS1 figures SQX's export does not carry — net, trades, PF, % winners, Drawdown, Ret/DD — from the newest cosecha's IS and OOS trades together, per identity; `no_oos` (IS trades, no OOS one), `oos` (the span the OOS trades' `Sample type` names, OOS1 on the USDJPY cosecha); no union unless that span is OOS1; without a cosecha, `why` and `oos` None | imported | `trades.parquet` → {union, rows, why} |
| `columns.py` | `GET`/`POST /api/databank/columns`: the columns the owner chose per table of one databank, in `AlgoData/filters/<P>/<D>/columns.json` (`discards.folder`), {«métricas» (the databank's metric choice, every tab) or «tab › sub» (that table's study columns): {hidden, added, order}} against the default; `view` None forgets one («restaurar vista por defecto»); a file that is not a JSON object reads as {} and the next save overwrites it; writes atomic (tmp + `os.replace`) under a lock | imported | choice ↔ JSON |
| `api.py` | The routes as `ROUTER` (equity also as POST, for a list of visible identities), every read failure an `error` field; `POST /api/databank/reload` = `find.forget()` + `POST /api/load` | imported | request → JSON |

## Contracts and traps

- **What the column chooser can add, per databank** (🔬 2026-09-28 on
  `Test_USDJPY_donchianUpperCrossUp_M30`). IS: the 21 numeric metrics of SQX's Export Data
  View; OOS (OOS1 here, per the trades' `Sample type`; a databank without a cosecha does not say, and the window calls it «OOS (tramo de la tarea)»): its 13 (no trades, Drawdown, Max DD %, Stability… — SQX's view has none, «–»);
  OOS2: nothing anywhere yet, «–»; IS+OOS1: the six of `segments.UNION`, computed, every other
  metric «–» (🤔 SQX's full-period block, sample 127, repeats the one filled block of a
  single-window task — `knowhow/export/databank-metrics-is-oos.md` —, so on the build
  databank it is IS, not the union). Only a databank with a cosecha (`Results`
  here) or a metrics export (`SPP_IS`) has metrics at all: the retest databanks
  (`Retest_Markets_-_Family`, `CrossTF`, `MCR_All`, `WFM`) offer the six union names with «–».
- **The union reproduces SQX's own definitions**: checked on the IS trades against `[IS]` —
  trades and Drawdown exact (the closed-trade balance's worst fall), net within 0.004, PF and
  Ret/DD within SQX's two-decimal rounding, Winning Percent only once zero-P&L trades leave
  its denominator. The six are the same trades added up, so the union is exact, not a proxy.
- **Pairing across databanks is by identity only.** A retest databank keeps the build's identity
  when the study signs the pre-retest one (mcRetest and crossTF do, 🔬 2026-09-27 on
  `Test_USDJPY_donchianUpperCrossUp_M30`: 8 of 8 each pair with `Results`). `crossmarket` and
  `spp` write no identity, so they show only in their own databank, paired there by name.
- **Batch studies pair by the mother's name** (`Strategy_9.27.83`, `Strategy_9-27-83` and
  `Strategy 9.27.83` are one name, `cells.norm`): a batch folder carries no identity. They
  appear in any databank of the project that holds a strategy of that name.
- **The door holds 17, 18, 19 and 20** — only under `ALGO_AUTONOMOUS=1` (`core.assetdata.enforced`); for a human it is always open (owner, 2026-09-28). While `ledgerview.blind` is sealed, the table leaves
  out `wfc`, `cscv`, `wfm` and `blindJoint` and says so in `sealed`; `panels` marks their
  sub-panels `blocked` with the ledger's own sentence. Nothing of them leaves the daemon.
- **A databank no install holds any more still has rows**: the cosecha's identities, then the
  strategies its reports name (`rows_from: informes`). Double-clicking one of them reaches a
  strategy F2's `/api/projects/find` cannot locate (it reads rosters): that is the truth, not a bug.
- **Reload queues what `/api/load` queues.** On a databank a worker holds, that can be an
  `orderstocsv` job on the conductor — the loader's own contract. The roster cache is keyed by
  the folder's mtime, which an in-place rewrite does not move; `find.forget` drops it.
- **The funnel's later rows are not a cascade.** Each later step read its own databank, so
  crossmarket's 208 can exceed the gate's 160; the note under the kicker says so.
- **F6 adds its rows on the desktop**: `ui/desktop/workspace/funnel.py` appends
  `GET /api/filters/state`'s `rows` (same shape: screen, entered, passed, died, why) when it
  answers, and nothing on a 404.

## Cost

Measured 2026-09-27 on `Test_USDJPY_donchianUpperCrossUp_M30` (200 strategies, 7 studies):
`table` 0.5 s (360 KB of JSON), `segments` 0.46 s the first time (348 k trades) and cached by
the cosecha's mtime after, `panels` 0.7 s, `equity` 0.5 s the first time and 0.02 s
cached (806,400 equity rows, 302,155 trades), `funnel` 0.7 s (it runs `/api/workflow`).
