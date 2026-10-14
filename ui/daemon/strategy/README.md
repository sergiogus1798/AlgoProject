# ui/daemon/strategy — the Estrategia page of one strategy (encargo 22 §5, plan 24 front F4)

What the ficha's fixed panel and its metadata column read, and «Archivar». Files only: no route
here reaches SQX. Every route takes `source=live|archive` (and `version`, "" for the newest):
`archive` answers from `core.archive.read` and computes no study — the arithmetic of the basic
panel (cumulative sums, percentiles) is redone on the frozen rows, so it equals the live answer
on the day of archiving (measured 2026-09-28, JSON diff empty).

```
api ─▶ meta.live ─▶ locate.sqx (install → raw/ export → archive) · locate.cfx ─▶ strategymeta.read
    ├▶ costcurve.curve ◀─ tearsheet.harvest.read
    ├▶ stats.build ─▶ tearsheet.tradestats (shape, returns) · tearsheet.oos2 (door, oos2 cosecha)
    ├▶ archived.* ─▶ core.archive.read (also used by results/, tearsheet/, tearmarket/)
    └▶ POST archive ─▶ archive_write ─▶ archive_view ─▶ results/, tearsheet/, gateview (family = the template folder of registry.csv)
```

**Imports from:** `core.archive` (`collect`, `manifest`, `read`), `core.sqxfile`, `core.paths`, `core.study.blocks`,
`sqx.inspect.strategymeta`, `ui.daemon.{loader,results,runner,tearsheet,progress,runs}` ·
**Consumed by:** `ui/daemon/routers.py`, `ui/desktop/workspace/ficha.py`; `archived` by
`results/api.py`, `tearsheet/api.py`, `tearmarket/api.py`

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | One strategy as the Estrategia page reads it: metadata, stats, cost curve, archive. | — | — |
| `api.py` | The Estrategia page's routes: metadata, basic stats, the curve, and «Archivar». | imported | request → JSON |
| `archive_view.py` | What the window is served today for one live strategy, captured so the archive can serve it again. | imported | live daemon reads → `view.json` + parquet |
| `archive_write.py` | Freeze one strategy into the archive: its .sqx, its cosecha rows, every study result, its provenance. | imported | a live strategy → `archive/<identity>/<stamp>/` |
| `archived.py` | The `source=archive` side of every Ficha route: an archived version read back, nothing computed. | imported | archive → the live shapes |
| `costcurve.py` | One strategy's equity curve: SQX's daily one, IS then OOS1 on one axis. | imported | cosecha rows + trades → curves |
| `locate.py` | Where one strategy's .sqx and its project.cfx are, by reading files only — never asking SQX. | imported | identity → path, sentence |
| `meta.py` | The metadata panel's data: `sqx.inspect.strategymeta.read` on the located .sqx, or the archived one. | imported | path → dict |
| `stats.py` | The basic statistics of one strategy per sample — IS, OOS1, both joined, and OOS2 behind its door. | imported | cosecha rows → dict |

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
- **«Archivar» needs the template family** (`runner.where.family`): without it the ledger count
  cannot be signed, and the route refuses with `where.no_family`'s sentence.
- **Per lot needs `Size`.** `tearsheet.harvest.TRADES` carries it since 2026-09-28; versions
  archived before froze their tearsheet without it, so `archived.tearsheet` takes the trades
  from the version's `harvest/trades.parquet`, which keeps every column.
