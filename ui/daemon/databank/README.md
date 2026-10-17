# ui/daemon/databank — the databank panel of Proyecto, SQX-style

What the bottom strip of Proyecto (encargo 22 §4.2, §4.3) reads: the two rows of tabs, one
databank as a table (a row per strategy, SQX's metrics, a column group per study), its aggregate
equity (SQX's), the population's funnel, and
«Recargar databank». Read-only on disk except the owner's column choice (`columns.py`);
nothing here sends a command to SQX.

**Imports from:** `core.paths`, `core.datapaths`, `core.cfx`, `engines.variants.look`,
`sqx.projects.stage`, `ui.daemon.{loader, results, workflow, gateview}`
· **Consumed by:** `ui/daemon/routers.py` (`ROUTER`) → `ui/desktop/workspace/`

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | A databank as the Proyecto panel shows it: table, aggregate equity, tabs, funnel, reload. | — | — |
| `api.py` | The databank panel's routes: tabs, table, columns, aggregate equity, funnel and reload. | imported | request → JSON |
| `batches.py` | The studies that write into a mother's variant batch: cloud, wfc (its three compositions in one file), cscv, marketSurfaces. | imported | `strategyPermutations/`, `pipeline/` → entries |
| `cells.py` | What every study said of each strategy of a project, per databank: verdict, state and fields. | imported | `reports/<P>/*/<day>/<study>/`, `structural\|atrCalculator/<P>/*/estudios/` → entries |
| `columns.py` | The owner's column choice per databank table: `AlgoData/filters/<P>/<D>/columns.json`. | imported | choice ↔ JSON |
| `equity.py` | A databank's aggregate daily P&L: SQX's. | imported | parquet → curves + stats |
| `funnel.py` | The population's funnel of one project: the gate's rules by level, then each later step's in and out. | imported | project → rows |
| `layout.py` | The databank panel's two rows of tabs for one project: each sub-panel and its databank. | imported | project → tabs |
| `metrics.py` | A databank's SQX metrics: its newest cosecha (IS + OOS paired) or its current metrics export. | imported | parquet / csv → frame |
| `segments.py` | A databank's IS+OOS1 figures, from its cosecha's trades: the union SQX's export does not carry. | imported | `trades.parquet` → {union, rows, why} |
| `table.py` | One databank as SQX shows it: a row per strategy, its metrics, and a column group per study. | imported | project, databank → payload |

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
