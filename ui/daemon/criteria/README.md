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
| `__init__.py` | The package's one-line purpose | imported | — |
| `read.py` | `offered(n, used)`: the facts `pipeline/autopilot/offered.yaml` lists for a step that no rule names yet, as rows with no threshold (each step of `state()` carries them as `offered`, and `menu` adds them to the picker); `said` words any side of a history line — a rule, a step's whole list, a plain value. `state()`: the freeze, the `dev` draw, step 6's filters, then every step that has tests or an entry in `criteria.yaml`, in WORKFLOW's order (`ui.daemon.workflow.steps`) — each rule worded (`row`: label from the study's title and the fact's last part, «Tipo», what passes, the limbo band, the `by` exceptions, and `why`, the comment the file carries above the rule) — the facts a rule of that step may name (`menu`: the keys of the newest `hechos.parquet` of that step under `AlgoData/autopilot/`, plus those its rules already name; `sqx` when the key's last part says so) and the newest 30 lines of the history. `FILES` holds the two paths, so a test points them at copies | imported | `criteria.yaml`, `_study.yaml`, `hechos.parquet`, the history → dict |
| `write.py` | `set_rule(n, at, rule, was)`: add (`at` None), change or delete (`rule` None) one rule through `core.assetyaml` (comments kept; the rule written on one line, as the file writes its own), after `check` — a threshold `criteria.holds` can read, a verdict `pass`/`fail`, a non-empty compound, each `by` entry folded — refusing frozen criteria, a step without `cut` and a file whose rule at `at` is no longer `was`; `stamp` appends the history line; `freeze()`. ⚠️ ruamel joins a rule written over two lines into one: the first write from the window changes those lines too (two today), nothing else | imported | a rule → `criteria.yaml`, one history line |
| `api.py` | `GET /api/criteria`, `POST /api/criteria/rule`, `POST /api/criteria/freeze`; a refusal is a 422 with the sentence to show | imported by `routers.py` | HTTP → the two above |

Tests: `tests/test_ui_criteria.py` (on a copy of `criteria.yaml`), `tests/test_autopilot_criteria.py` (the rule shapes).
