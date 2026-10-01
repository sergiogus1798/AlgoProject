# pipeline — one mother strategy in, one verdict out, a hundred times unattended

Stage 5 of the robustness protocol, and the only module that spans the others. A mother strategy
enters, its stages run in order, a verdict comes out, the bulky data is deleted, and the next one
starts. With ~100 mothers that is **days of unattended machine**, which is why resumability and
disk hygiene are the requirement here rather than a quality detail.

```
recipe.yaml ─▶ stages ─▶ ledger ─▶ cleanup
 the seven     run one   what is   delete only what
 as data       as its    happening the ledger proves
               own       right     is recoverable
               process   now
```

**This is the job queue of a future daemon.** Written as a script that chains stages, it gets
thrown away when the daemon arrives; written as a **job with a ledger**, the daemon reduces to a
server on top of it. Three consequences, and they are the design:

- **Stages are data, not code.** `recipe.yaml` is the only place that says what a pipeline is, and
  the daemon will read the same file. Adding the eighth stage is adding a row.
- **The ledger is written during a stage, never at its end.** A stage that runs forty minutes and
  says nothing until it finishes is indistinguishable from a hung one.
- **The ledger survives the deletion.** It weighs kilobytes; the data it describes weighs gigabytes.
  Deleting the data and keeping the record is what makes the deletion auditable instead of a loss.

| folder | the question it answers | read its README before |
|---|---|---|
| `ledger/` | what is happening right now, and what happened | changing `state.json`; other modules read it |
| `stages/` | what a stage is, how one is run, and when it refuses | adding a gate or wiring a real module in |
| `stubs/` | what stands in for the five modules not built yet | wiring a real module in |
| `verify/` | is this still a pipeline and not a script? | touching progress or resumption |
| `autopilot/` | one PROJECT's workflow, 7 → 16, unattended: the window's chain judging by `criteria.yaml` instead of stopping (owner, 2026-10-01) | running a workflow without stops, or writing criteria |

| file | what it does | run it | in → out |
|---|---|---|---|
| `run.py` | the whole chain over every mother of a project | `python3 -m pipeline.run --project XAUUSD --databank SPP_IS` | SPP export → one `state.json` and one `verdict.json` per strategy |
| `cleanup.py` | deletes a finished mother's variant data, only what the ledger proves is recoverable | `python3 -m pipeline.cleanup --project XAUUSD --strategy "Strategy 17.9.39"` | ledger → freed bytes |
| `recipe.yaml` | the seven stages: command, entry gate, exit gate | edited | — |
| `config.yaml` | every tunable, grouped by the layer that reads it | edited | — |

Manual page, in Spanish, for whoever runs it: `docs/manual/04-sqx-plantillas-y-proyectos.pdf` (cap. 17-pipeline).

## The three things this module exists to get right

**Resuming is not re-running.** A stage counts as done only when the ledger says so **and** its
outputs are still on disk. Both halves are needed: the ledger outlives the data, so a swept mother
would otherwise read as one that never finished. The verdict stage is the deliberate exception —
it is marked `recompute`, so a changed threshold re-judges without re-running anything that costs
machine time. **The pipeline stores numbers, never judgements.**

**The mother is never deletable.** `cleanup` removes only paths the collect stage recorded as
removable, only after re-hashing every file that was exported, and only when the path lies inside
`pipeline/<project>/<strategy>/`. The mother lives in the SQX databank and in `raw/`, so confining
the sweep to that folder makes reaching it impossible rather than merely forbidden — a guarantee
that does not depend on the manifest's `origin` flag being right.

**A stage joins by adding one print, not an import.** The whole coupling between this module and
the five that will fill it is the line `PROGRESS <0..100> <status>` on stdout. Anything else a
stage prints becomes its status line without moving the bar, so a module that never adopts the
protocol still proves it is alive.

## What is wired, and what is standing in

`sppultra`, `design` and `build` run real modules. `design` and `build` are the same entry point
twice — `sqx.variants.make` with and without `--design-only` — which is safe because the design is
seeded from `sqx/variants/config.yaml` and reproduces exactly. Both are pointed at `{work}` with
`--out`, so a mother's batch lands beside its own ledger rather than in `variants/<project>/…`,
which is where the command writes when a human runs it.

The remaining three rows (`ran`, `collected`, `wfc`) point at `stubs/placeholder.py`, and each
carries a comment with the line it becomes. **Wiring a real module in is editing `command` and
`produces` on its row** — no Python in this folder changes.

⚠️ `verify/` deliberately does **not** run the real rows: it swaps every command for the
placeholder, because what it tests is the ledger — ordering, resumption, `progress` monotonicity,
a `state.json` that survives a kill — and none of that needs a real SQX export or the 5,000 files
`build` writes. Testing the real wiring means running `pipeline.run` against a real strategy.

## Budgets

The disk budget, not a full disk, is what has to stop a multi-day run: a full disk stops it too,
but by then the stage that was writing has left half a file behind. `stages/gates.py` asks
`perf/disk` before each mother and refuses when the data root or any branch is over. The ceilings
live in `perf/config.yaml` and belong to `perf/disk`, which is also the only thing that judges
them — nothing is reimplemented here.
