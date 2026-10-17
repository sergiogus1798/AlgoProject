# pipeline — one project's workflow, unattended

> 2026-10-13: the old chain (`run.py`, `stages/`, `verify/`, `stubs/`, `recipe.yaml`) was deleted — no production caller. What runs is `autopilot/` and `campaign/`; `ledger/` and `cleanup.py` remain.

This module runs the workflow without a human between steps, and keeps a record small enough to
outlive the data it describes. With many strategies that is **days of unattended machine**, which is
why resumability and disk hygiene are the requirement here rather than a quality detail.

- **The ledger is written during a run, never at its end.** A step that runs forty minutes and says
  nothing until it finishes is indistinguishable from a hung one.
- **The ledger survives the deletion.** It weighs kilobytes; the data it describes weighs gigabytes.
  Deleting the data and keeping the record is what makes the deletion auditable instead of a loss.

| folder | the question it answers | read its README before |
|---|---|---|
| `ledger/` | what is happening right now, and what happened | changing `state.json`; other modules read it |
| `autopilot/` | one PROJECT's workflow, 7 → 16, unattended: the window's chain judging by `criteria.yaml` instead of stopping (owner, 2026-10-01) | running a workflow without stops, or writing criteria |
| `sqxrun/` | one launch of SQX tasks, start to stop: rule 5, snapshot, configure, start, wait, stop, restore, compare | launching tasks from the window or the autopilot |
| `campaign/` | the unattended loop over template × asset × timeframe: a ledger, pre-registered batches, one `workflow.sh template` per cell, each result kept with its strategies in the archive (owner, 2026-10-05) | running or planning the campaign |

| file | what it does | run it | in → out |
|---|---|---|---|
| `cleanup.py` | Delete a finished mother's variant data, but only what the ledger proves is recoverable. | `python3 -m pipeline.cleanup --project XAUUSD --strategy "Strategy 17.9.39" [--apply]` | ledger → freed bytes |

Manual page, in Spanish, for whoever runs it: `docs/manual/04-sqx-plantillas-y-proyectos.pdf` (cap. 17-pipeline).

## What this module must get right

**The mother is never deletable.** `cleanup` removes only paths the collect stage recorded as
removable, only after re-hashing every file that was exported, and only when the path lies inside
`pipeline/<project>/<strategy>/`. The mother lives in the SQX databank and in `raw/`, so confining
the sweep to that folder makes reaching it impossible rather than merely forbidden — a guarantee
that does not depend on the manifest's `origin` flag being right.

**The pipeline stores numbers, never judgements.** A changed threshold re-judges without re-running
anything that costs machine time.

## Budgets

The disk budget, not a full disk, is what has to stop a multi-day run: a full disk stops it too,
but by then the step that was writing has left half a file behind. The ceilings live in
`perf/config.yaml` and belong to `perf/disk`, which is also the only thing that judges them —
nothing is reimplemented here.
