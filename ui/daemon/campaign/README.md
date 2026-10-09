# ui/daemon/campaign — what PORTFOLIOS › Campaña asks

Read-only over `AlgoData/campaign/runs/<workflow>/` (written by `pipeline/campaign/keep.py`): nothing here
writes, runs a study or reaches SQX. A finalist opens through the archive routes that already take
`source=archive`; these four only say what the campaign saved and serve what the archive cannot pair.

```
api ─▶ shelf ─▶ workflow.json, madres/, WFM/, structural/, atrCalculator/ of the workflow folder
            └▶ archive.shelf.show (the mother's frozen version) · results.catalogue (titles, steps)
```

**Imports from:** `core/datapaths`, `ui/daemon/archive`, `ui/daemon/results` · **Consumed by:** `ui/desktop/portfolios/campaign.py`, `imported.py`

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Package marker, one docstring | imported | — |
| `api.py` | `GET /api/campaign/list`, `show?workflow`, `open?workflow&strategy`, `extra?workflow&key`; a failure is a Spanish sentence, never a 500 | imported | request → JSON |
| `shelf.py` | `workflows()` (newest first), `show(name)` (funnel, steps with seconds, strategies, `not_kept`), `opened(name, strategy)` (the MOTHER's archived version plus `label`, `banner`, `extras`), `extra(name, key)` (a kept contract JSON as `/api/result` serves it) | imported | folders → dicts |

## Contracts and traps

- **The finalist has no results of its own.** Every study of steps 8-22 is signed with the MOTHER's identity and the
  stop variant has no cosecha, so `open` serves the mother's version, labelled «de la madre» in `banner`.
- **`extras`** are results the archive cannot pair (steps 17-20 sign another identity per databank; 23-24 are
  per run stamp), kept in the workflow's folder; `extra` refuses a key outside the folder.
- `marketSurfaces.json` (100 MB per mother) is not kept: only its `.md`/`.html`; `not_kept` says so.
