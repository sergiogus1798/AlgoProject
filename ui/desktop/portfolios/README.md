# ui/desktop/portfolios — «Portfolios»

The PORTFOLIOS zone (encargo 22 §2, encargo 23 §4, plan 24 front F12): the archived strategies and
«Importar», which opens one archived version as the Estrategia page shows a live strategy — every
panel read from the archive (`source=archive` + `version`), nothing computed, no job queued. Only
from the archive; importing from a live databank waits for the owner.

```
zone (PortfoliosZone) ─▶ /api/archive/list · /api/archive/show ─▶ detail (the words)
      └─ import_requested(identity, version) ─▶ [shell, F13] · preview ─▶ imported (ImportedFicha)
                                                  ├▶ workspace.ficha.Ficha: curves, stats, metadata on source=archive
                                                  └▶ studies (ArchivedStudies): the sheet and each frozen study
```

**Imports from:** `ui/desktop/workspace` (the ficha), `ui/desktop/studypage` (`net.fetch`, `ficha.sides`), `ui/desktop/blocks`, `glossary`, `numbers`, `theme` · **Consumed by:** the shell (F13 wires `PortfoliosZone` and its signal)

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Package marker, one docstring | imported | — |
| `zone.py` | `PortfoliosZone`: the table of archived strategies (identity only in the tooltip), the chosen one's versions newest first, what the chosen version holds, and «Importar esta versión» emitting `import_requested(identity, version)`; `pick(identity, version)` for a launcher, `reload()` for «Recargar» | imported | archive → table · click → signal |
| `detail.py` | One version in words: head facts, the studies held by databank, what was not archived and why, the ledger count and the provenance | imported | `/api/archive/show` → HTML |
| `imported.py` | `ImportedFicha`: F4's ficha subclassed — its three reads carry `source=archive` and the version, «Archivar» hidden, every «calcular» answers that nothing is computed, the frozen studies below | imported | a version → the page |
| `studies.py` | `ArchivedStudies`: the Ficha's IS/OOS, exits and «Contra el subyacente» sheets, «Operaciones» (the trade gallery, every call carrying `source=archive` and the version) and every frozen study, drawn with `ResultView` from the archive; a study with no per-strategy result shows the databank's, archived beside it; «Informe de lo que ves» hidden | imported | a version → drawings |
| `preview.py` | The zone alone in a window, «Importar» opening a standalone ImportedFicha; `--shot DIR` saves the list and the imported page; `--port` points it at a daemon other than `UI_PORT` | `python3 -m ui.desktop.portfolios.preview [--shot DIR] [--identity I] [--version V] [--port N]` | daemon → window / PNGs |

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
