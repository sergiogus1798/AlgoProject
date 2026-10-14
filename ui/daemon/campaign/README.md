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
| `__init__.py` | The campaign's saved workflows: listed, described, and one strategy opened with all its results. | imported | — |
| `api.py` | The campaign's four routes: `/api/campaign/list`, `show`, `open` and `extra` — files read, nothing run. | imported | request → JSON |
| `shelf.py` | The campaign's folders as the window reads them: workflows, their strategies and the results the archive cannot pair. | imported | folders → dicts |

## Contracts and traps

- **The finalist has no results of its own.** Every study of steps 8-22 is signed with the MOTHER's identity and the
  stop variant has no cosecha, so `open` serves the mother's version, labelled «de la madre» in `banner`.
- **`extras`** are results the archive cannot pair (steps 17-20 sign another identity per databank; 23-24 are
  per run stamp), kept in the workflow's folder; `extra` refuses a key outside the folder.
- `marketSurfaces.json` (100 MB per mother) is not kept: only its `.md`/`.html`; `not_kept` says so.
