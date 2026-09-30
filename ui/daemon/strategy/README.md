# ui/daemon/strategy — the Estrategia page of one strategy (encargo 22 §5, plan 24 front F4)

What the ficha's fixed panel and its metadata column read, and «Archivar». Files only: no route
here reaches SQX. Every route takes `source=live|archive` (and `version`, "" for the newest):
`archive` answers from `core.archive.read` and computes no study — the arithmetic of the basic
panel (cumulative sums, percentiles) is redone on the frozen rows, so it equals the live answer
on the day of archiving (measured 2026-09-28, JSON diff empty).

```
api ─▶ meta.live ─▶ locate.sqx (install → raw/ export → archive) · locate.cfx ─▶ strategymeta.read
    ├▶ costcurve.curve ◀─ tearsheet.harvest.read · costcurve.repriced (member file, then population; also read by tearsheet.pnl)
    ├▶ stats.build ─▶ tearsheet.tradestats (shape, returns) · tearsheet.oos2 (door, oos2 cosecha)
    ├▶ archived.* ─▶ core.archive.read (also used by results/, tearsheet/, tearmarket/)
    └▶ POST archive ─▶ core.archive.write (family = the template folder of registry.csv)
```

**Imports from:** `core.archive`, `core.sqxfile`, `core.paths`, `core.study.blocks`,
`sqx.inspect.strategymeta`, `ui.daemon.{loader,results,runner,tearsheet,progress,runs}` ·
**Consumed by:** `ui/daemon/routers.py`, `ui/desktop/workspace/ficha.py`; `archived` by
`results/api.py`, `tearsheet/api.py`, `tearmarket/api.py`

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Names the package; holds no code | — | — |
| `api.py` | `ROUTER`: `GET /api/strategy/meta`, `/costcurve`, `/stats`, `/archived`, `POST /api/strategy/archive`; a refusal is `{"error"}`, never a 500 | imported | request → JSON |
| `locate.py` | The strategy's `.sqx` — the install holding the databank, else an export's copy under `raw/<P>/*/*/strategies/`, else the newest archived version — by identity; the project's `project.cfx` | imported | identity → path, sentence |
| `meta.py` | E2's fields of the located file (a copy outside the databank folder is read from a temporary folder named as the databank) or of the archived version | imported | path → dict |
| `costcurve.py` | SQX's daily curve and the same corrected by the `spread` study's repriced trades, IS then OOS1 on one axis, with `days` for the year ticks; nets and DDs. `repriced` (the report's rows of one strategy) is also what `tearsheet.pnl` corrects each sample with | imported | cosecha rows + trades → curves |
| `stats.py` | Per sample (IS, OOS1, IS+OOS1 — OOS's curve continued from IS's end, no SQX Sharpe —, OOS2): trades, nets (SQX and real), Profit Factor, win rate, DD, Sharpe; the return's mean, std, skew and excess kurtosis in «$/lote» or «$/trade»; and its distribution per unit (USD por lote by default) as a `distribution` block whose percentile row reads «1%»… in $ (`row_unit`) | imported | cosecha rows → dict |
| `archived.py` | The `source=archive` answers: `load`, `tearsheet`, `harvest_folder`, and `/api/result`, `/api/history`, `/api/matrix` from the frozen view | imported | archive → the live shapes |

## Contracts and traps

- **OOS2 is behind the ledger's door** only under `ALGO_AUTONOMOUS=1` (`core.assetdata.enforced`) (`ui.daemon.workflow.ledgerview.door`, the study
  blindJoint reads): sealed, it answers `{"blocked": "reservado: se abre tras los pasos 17, 18 y
  19", "why": …}`; open, it reads the newest cosecha of the project that carries a sample
  `OOS2`/`oos2` for the identity, else `{"blocked": "OOS2 abierto, sin export: exporta el retest
  oos2"}` (owner's reading of Q10). No other source is guessed.
- **The .sqx of a workflow project is usually not on the install.** `Test_USDJPY_donchianUpperCrossUp_M30`
  keeps an empty `databanks/` on the custodian; its `Results` strategy is found as the export
  copy in `raw/…/SPP_IS/…/strategies/` — same identity, but its `last_test` is the SPP IS task,
  which the panel says. Without any file the panel says «sin .sqx en ningún install».
- **E2's reader matches the project's tasks by the .sqx's folder name**, so a copy found in
  `raw/…/strategies/` is copied to a temporary folder named as the databank before reading;
  read in place, `backtest` would list no task.
- **The real curve needs the `spread` report.** A run on the strategy alone writes
  `estrategias/<name>.trades.parquet`, a population run `trades.parquet`; both are read, newest
  day first. Missing → `real: None`, and the window offers «calcular» (`spread`, scope one/many).
- **«Archivar» needs the template family** (`runner.where.family`): without it the ledger count
  cannot be signed, and the route refuses with `where.no_family`'s sentence.
- **Per lot needs `Size`.** `tearsheet.harvest.TRADES` carries it since 2026-09-28; versions
  archived before froze their tearsheet without it, so `archived.tearsheet` takes the trades
  from the version's `harvest/trades.parquet`, which keeps every column.
