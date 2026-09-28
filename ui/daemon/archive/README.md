# ui/daemon/archive — what PORTFOLIOS asks

The two routes of the PORTFOLIOS zone (encargo 23 §4, plan 24 front F12). Read-only over
`AlgoData/archive/` through `core.archive.read`: nothing here writes, runs a study, queues a job or
reaches SQX. Showing an archived strategy's panels is the job of the routes that already take
`source=archive` (`results/`, `tearsheet/`, `strategy/`); these two only say what the archive holds.

```
api ─▶ shelf ─▶ core.archive.read (listing, load) + each version's manifest.json
             └▶ results.catalogue (a study's title, family and step)
```

**Imports from:** `core/archive`, `core/paths`, `ui/daemon/results` · **Consumed by:** `ui/desktop/portfolios` over HTTP

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Package marker, one docstring | imported | — |
| `api.py` | `GET /api/archive/list` and `GET /api/archive/show?identity&version`; a failure is a Spanish sentence, never a 500 | imported | request → JSON |
| `shelf.py` | `strategies()`: one row per identity (name, project, symbol, timeframe, newest step, `archived_at`, the ledger count, versions oldest first); `show(identity, version)`: one version with the studies it froze per databank, what it skipped and why, and its provenance | imported | archive → dicts |

## Contracts and traps

- **The ledger count is per version, as that day's.** The list shows the newest version's; the
  versions' own counts are in each version row. `n` is `trials.accumulated`'s N (strategies tried),
  `searches` the ledger rows of the study; a NaN σ is sent as null.
- **`held` lists the per-strategy results the archive froze.** A study that writes only a
  population result (`spread`, `crossTF`) is held with `result: null` for the strategy; the
  window then shows the population result archived beside it.
- **Symbol and timeframe come from the project's registry row frozen in the manifest**, the
  symbol falling back to the asset card's.
