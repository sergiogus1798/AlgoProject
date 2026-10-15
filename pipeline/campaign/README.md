# pipeline/campaign — the unattended loop over template × asset × timeframe, one workflow per cell

The campaign walks cells (template × asset × timeframe, long only, M30/H1/H4) and runs the whole workflow
of each with `bin/workflow.sh template …` (hard rule 19), one at a time on the custodian, then keeps the
result for good. It is plain Python with **no LLM inside**: Council verdict 2026-10-05 — scheduling is
mechanical, the batch is pre-registered (frozen before its results exist, so results only inform the
*next* batch), and the `STOP` file is the owner's veto. Every cell ever queued is a line of the ledger,
and that line count is the trial count N the results are judged against, failures included.

**Imports from:** `core.paths`, `core.datapaths`, `core.researchpaths`, `core.sqxfile`, `core.assets` (as a
subprocess), the research board (`AlgoData/research/board/board.json`), `core.archive` (as a subprocess)
· **Consumed by:** the owner (terminal), the window's «Campaña» view (lists the saved workflows and opens
their strategies from the archive), `tests/test_campaign.py`.

| file | what it does | run it | in → out |
|---|---|---|---|
| `freeze.py` | Freeze a finished workflow's strategies in the archive — finalists AND their mothers — and copy the run-stamped outputs. | imported | finalists → `AlgoData/archive/` versions + links |
| `keep.py` | One finished workflow kept for good: its run folder, its timings and counts, and every finalist frozen in the archive. | imported | cell + run folder + state → `runs/<workflow>/` and the facts the ledger records |
| `ledger.py` | The campaign's ledger: every cell ever queued, one JSON line per change of state, never rewritten. | imported | cell + state → `ledger.jsonl` line |
| `palette.py` | The cell's palette, chosen by the buildingBlocksExpert in one headless session before its project exists. | imported | cell → (palette name, why not) |
| `plan.py` | The campaign's next batch: the board's admitted cells x the clean long templates of that family, never one already queued. | `python3 -m pipeline.campaign.plan [--queue N] [--show N]` (bare = read-only) | board + library + ledger → printout; `--queue` writes `batches/<id>.json` and `pending` ledger lines |
| `run.py` | The campaign's loop: take the next cell of the ledger, run its whole workflow, keep it, go on — until STOP. | `setsid nohup python3 -m pipeline.campaign.run >> ~/Desktop/AlgoData/campaign/loop.log 2>&1 &` · `--stop` · `--go` | next ledger cell → autopilot run → `keep` → ledger line |
| `shelf.py` | The survivors' shelf: every finalist of a finished workflow filed by asset, timeframe, direction, family and template. | imported (by `keep`) | cell + finalists → folders + index |
| `config.yaml` | Direction, timeframes, the Build caps (`strategies`, `minutes`), `min_free_gb`, `failures_in_a_row`, and `asset_class`: templates offered only in one asset class (`indicesIBS` → index; owner, 2026-10-05) | edit | read by `plan.py`, `run.py` |

## On disk — `AlgoData/campaign/` (`core.datapaths.campaign_dir`)

- `ledger.jsonl` — append-only; the last line of a key is its state (`pending`, `running`, `interrupted`, `done`, `failed`, `question`, `dropped` — a template the owner took out, `config.yaml` `dropped_templates`).
- `batches/<id>.json` — a batch as it was frozen, whole.
- `runs/<template>_<symbol>_<tf>_<direction>_<stamp>/` — `workflow.json` (time per step, survivor counts, `criteria.yaml` hash, finalists, `not_kept`), `run/` (the autopilot's run folder), `estrategias/` (links to each finalist frozen in `AlgoData/archive/`).
- `STOP` (the owner's veto), `loop.lock`, `loop.log`.

## Traps

- **A `done` cell's `Trade_` project is retired at once** (owner, 2026-10-15): its finalists are in the store and its databanks only slow SQX's start (1.1 GB for one NIKKEI run). `sqx.projects.retire` archives its `project.cfx`; it refuses while step-8 survivors are unsaved or the custodian is up, and then the project stays and the loop goes on. A `failed` or `interrupted` cell keeps its project: the next try resumes it.

- **The Build cap is 180 minutes always.** SQX's live session honours only `time-limit`; `strategies: 10000` is the databank's size (it keeps the best 10,000), not a stop. A running build cannot be stopped early from outside (`/project/stop` does nothing), and an exit request makes SQX save every project while the build runs on. So a STOP mid-build ends the session the hard way (owner, 2026-10-06): once the other projects' databanks are saved again, the JVM is killed by PID, the build's memory is lost, its outputs on disk and that start's project log are set aside, and the cell resumes by building again (`ui/daemon/launch/liverun.close`, `sqx/projects/exiting.py`). → `knowhow/sqx-drive/live-chain-without-restart.md`
- **A task that does not advance is a step failure**, not a wait: past 3× the longest its title ever took (`AlgoData/autopilot/task-durations.json`, floor 20 min, 60 for a title never seen) `sqx.projects.taskcap` aborts it, the session is killed and the loop's three tries follow (🔬 2026-10-06: «MCR 6 Exits» sat 1 h 40 on 2 cores — `RandomizeExitParameters` over strategies that exit by condition only never returns; the configurator now drops that method where no exit method is set). → `knowhow/sqx-drive/retest-task-hangs-silently-deadline.md`
- **Every try says `--own-log`**: the custodian's recent log is always the loop's own (the try before, or the cell before). Without it the worker counted as busy for 15 min and the try was refused — a retry on 2026-10-06, then a resumed cell's first try the same day; the refusal's words are kept in the run folder's `salida.txt`.
- **Filters are `pipeline/autopilot/criteria.yaml` as it stands**; each run records its hash. Thresholds can later be tightened on kept results, never loosened: every step deletes its rejects.
- **`dev.on: true` makes step 8 keep 10 at random** — the owner's switch, not a bug.
- **`cells()` merges every line of a key**, so a fact a later line records must not share a name with a config field: keep's step time is `steps_minutes`, because `minutes` is the Build cap and a re-queued cell built with the kept run's time (🔬 2026-10-06).
- **N = every line of the ledger, failures included.** Judging a result against fewer trials overstates it.
- **A batch is frozen before its results exist.** Never re-queue or reorder a batch after seeing outcomes; results only inform the next one.
