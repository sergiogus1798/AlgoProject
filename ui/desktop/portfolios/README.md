# ui/desktop/portfolios — «Portfolios»

The PORTFOLIOS zone (encargo 22 §2, encargo 23 §4, plan 24 front F12): the archived strategies and
«Importar», which opens one archived version as the Estrategia page shows a live strategy — every
panel read from the archive (`source=archive` + `version`), nothing computed, no job queued. Only
from the archive; importing from a live databank waits for the owner.

Since 2026-10-05 (PLAN M7, encargo 33 §7.5) the zone is a board in Quant Analyzer's structure
with the window's own theme: module rail on the left, the module (settings strip with «Calcular»,
result tabs) on the right, the databank below. The archive viewer is the rail's last entry.

```
board (PortfoliosBoard) ─ rail ─▶ modulepage (ModulePage) ─▶ /api/portfolios/module ─▶ blocks · matrix
      │                              └─ calc (CalcButton) ─▶ /preflight ─▶ [question] ─▶ /run ─▶ job ─▶ refresh
      └─ databank (Databank) ─ chosen(run or pool) ─▶ every module        «Archivo» ─▶ zone (below)
zone (PortfoliosZone) ─▶ /api/archive/list · /api/archive/show ─▶ detail (the words)
      └─ import_requested(identity, version) ─▶ [shell, F13] · preview ─▶ imported (ImportedFicha)
                                                  ├▶ workspace.ficha.Ficha: curves, stats, metadata on source=archive
                                                  └▶ studies (ArchivedStudies): the sheet and each frozen study
```

**Imports from:** `ui/desktop/workspace` (the ficha), `ui/desktop/studypage` (`net.fetch`, `ficha.sides`), `ui/desktop/blocks`, `glossary`, `numbers`, `theme` · **Consumed by:** the shell, which mounts `board.PortfoliosBoard`; `PortfoliosZone` is its «Archivo» module, unchanged, and the board re-emits its `import_requested`

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | PORTFOLIOS: the archived strategies, and «Importar» opening one as the Estrategia page shows it. | imported | — |
| `board.py` | PORTFOLIOS: a rail of modules, each with its strip and result tabs, over one databank that feeds them all. | imported | `/api/portfolios/state` → the zone |
| `calc.py` | «Calcular»: ask the daemon whether the command may start, confirm when it must, queue it, follow it. | imported | `/api/portfolios/preflight`, `/run` → a job |
| `campaign.py` | PORTFOLIOS › Campaña: the workflows the campaign saved, each one's funnel, time per phase and strategies. | imported | `/api/campaign/list`, `show` → tables |
| `databank.py` | The databank at the bottom of PORTFOLIOS: «Estrategias» to tick and «Carteras» to choose — one selection for every module. | imported | `/api/archive/list`, `/state` → `chosen`, `declared` |
| `detail.py` | What one archived version holds, in words: its studies by databank, what it left out, its provenance. | imported | `/api/archive/show` → HTML |
| `imported.py` | The Estrategia page of an archived version: F4's ficha, every read on `source=archive`, nothing run. | imported | a version → the page |
| `matrix.py` | The correlation matrix: one cell per pair, coloured in discrete steps against the threshold in force. | imported | a matrix dict → widget |
| `modulepage.py` | One rail module of PORTFOLIOS: its settings strip with «Calcular», and below it the result's tabs. | imported | `/api/portfolios/module` → widgets |
| `preview.py` | PORTFOLIOS alone in a window, «Importar» opening the archived ficha beside it — until the sidebar wires it. | `python3 -m ui.desktop.portfolios.preview [--shot DIR] [--identity I] [--version V] [--port N]` | daemon → window / PNGs |
| `series.py` | The bar that walks a saved workflow's strategies one by one: «anterior», where you are, «siguiente». | imported | index → `step(i)` |
| `strips.py` | What each rail module of PORTFOLIOS puts in its settings strip: one line of what it is, selectors, launchers. | imported | — |
| `studies.py` | Below the imported ficha: the backtest sheet and every study the version froze, each read from the archive. | imported | a version → drawings |
| `zone.py` | PORTFOLIOS: every archived strategy, its versions, and «Importar» — only from the archive for now. | imported | archive → table · click → signal |

## Contracts and traps

- **No button here reaches a job.** `ImportedFicha` replaces `compute.run` on its instance, so
  the «calcular» buttons the live panels draw for a missing figure only say why not. The shell
  must use `ImportedFicha` (or a ficha that takes `source`) for an import: F4's `Ficha.fill`
  reads live.
- **Not shown in archive mode:** «Lote» (the variant batch is read live by the mother's name and
  the archive does not freeze it) and the live page's family tabs with their state dots, the
  run history, «comparar» (two runs or two strategies) and the run bar — `studypage/` reads
  `SELECTION` and live routes throughout. `ArchivedStudies` is the read-only list of what the
  version froze instead.
- **«Informe de lo que ves» is hidden.** It writes its HTML beside the live report under
  `reports/<P>/…`, which would leave a trace of an archived version outside its folder.
- **N of the ledger** is the candidates scored over ALL searches of the ledger study (the
  template on that symbol and timeframe), not of the one search that found the strategy;
  `searches` is every row. N = 0 with searches > 0 prints «—»: rows exist, none scored.
- **An archived result is the rendering of that day.** Diffed against today's live route, a
  frozen result lacks keys the store added later (`partials`, 2026-09-28): that is the archive
  doing its job, not drift.
