# ui/daemon/criteria — the pass criteria of every workflow step, read and written

The daemon side of the «Criterios» zone (owner, 2026-10-03, feedback §13). It is a **view over what
already judges**, not a second system: the rules are `pipeline/autopilot/criteria.yaml`, the judge
is the autopilot (`pipeline.autopilot.judge` → `criteria.outcomes`), and step 6 is
`assets/_study.yaml`, the Build's acceptance filters — the only criteria SQX itself applies, shown
here read only (the window has no writer for that file: `sqxconfig/write.py` covers `_build`,
`_classes` and `_policy`).

**Every write is stamped, and the freeze is in the file the judge reads.** A rule added, changed or
deleted appends one line to `ledger/criteria-history.jsonl` (`at`, `by`, `step`, `what`, `before`,
`after`). «Congelar» writes `frozen: {on, by, sha}` first in `criteria.yaml` — where an agent
editing the file by hand sees it — and from then on every write here is refused; `sha` is the
hash of `steps`, so the zone says when the file was edited by hand afterwards. There is no unfreeze
route: lifting it is deleting that line, which git shows.

Reaches no install and launches nothing.

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | The Criterios zone: the pass criteria of every workflow step, read and written. | imported | — |
| `api.py` | The routes of the Criterios zone: the state, one rule written, and the freeze. | imported by `routers.py` | HTTP → the two above |
| `read.py` | What the Criterios zone shows: criteria.yaml step by step, the Build filters, the freeze. | imported | `criteria.yaml`, `_study.yaml`, `hechos.parquet`, the history → dict |
| `write.py` | One rule of criteria.yaml added, changed or deleted from the window, stamped; and the freeze. | imported | a rule → `criteria.yaml`, one history line |

Tests: `tests/test_ui_criteria.py` (on a copy of `criteria.yaml`), `tests/test_autopilot_criteria.py` (the rule shapes).
