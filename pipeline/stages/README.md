# pipeline/stages — what a stage is, how one is run, and when it refuses

A stage is a **row of `recipe.yaml`**, not a function: a name, a `python3 -m` command line, the
paths that must exist before it, the paths that must exist after it. There is exactly one executor
for all of them, so adding the eighth stage is adding a row and nothing else. The daemon that
replaces `run.py` imports this same registry.

| file | what it does | run it | in → out |
|---|---|---|---|
| `recipe.py` | the registry: `recipe.yaml` filled in for one strategy | imported | row + strategy → command, gates, outputs |
| `execute.py` | runs one stage as its own process and turns what it prints into progress | imported | resolved row → ledger entries |
| `gates.py` | the hard refusals: inputs, outputs, disk budget, already-done | imported | resolved row → pass or `SystemExit` |
| `verdict.py` | the seventh stage: judges one mother against the thresholds | `python3 -m pipeline.stages.verdict --work DIR --brief FILE` | numbers on disk → `verdict.json` |

## Why each stage is its own process

Explicit requirement: **if `run.py` disappeared, everything would still work by hand.** Every row
is a command someone can paste into a terminal, with its input and its output on disk. `run.py`
holds no logic of its own; it chains, it does not compute.

The price is that progress has to cross a process boundary, and the protocol is deliberately the
smallest thing that can: a stage prints `PROGRESS <0..100> <status>` on stdout. Any other line
becomes the status without moving the bar, so a module that never adopts the protocol still proves
it is alive. **A stage joins the pipeline by adding one print, not an import.**

## The gates

| gate | refuses when | why it is hard |
|---|---|---|
| `entering` | an input is missing | a stage without its input either crashes deep inside someone else's module or writes a plausible empty answer, and a hundred unattended mothers is where that goes unnoticed |
| `leaving` | a promised output was not written | an exit code of zero is not evidence |
| `room` | the data root is over budget | the budget has to stop the run, not the disk filling |
| `costs` | a required cost override has no agreed value | the same condition `python3 -m core.assets <SYMBOL>` exits non-zero on. Days of machine spent on backtests priced with nothing is worth one file read. A *provisional* value is a decision, not a blocker, and the ledger stamps it |
| `unchanged` | a fingerprinted file is no longer that file | `brief_hash` says which design the later stages were built from. A brief edited afterwards makes every stage after it measure one design against another's numbers — a failure that produces plausible results rather than an error |
| `must` | the stage's own output says the experiment is invalid | a failed canary is not a strategy being bad, it is the variants SQX ran not being the ones that were written. That is a gate, not a threshold: it stops the run instead of producing a verdict nobody should read |
| `done` | — | it is the resume rule: the ledger says done **and** the outputs are still there |

**Where the line between a gate and a threshold falls.** A threshold lives in `config.yaml`, is the
user's, is changeable, and produces a verdict. A gate lives on a recipe row under `must`, and stops
the run. The test is whether the number says *this strategy is not good enough* or *this
measurement does not mean anything*. Canaries are the second kind, which is why they are a `must`
on the `ran` row and deliberately **not** a verdict rule.

`done` is false for a row marked `recompute`. Only the verdict carries it: thresholds are the
user's and are changeable, and changing one must re-judge without re-running anything that costs
machine time.

## The verdict

`verdict.py` reads `brief.*` from the design brief and `<stem>.*` from every JSON the stages left
in the work directory, flattens them into one namespace, and compares them against the rules in
`config.yaml`. A rule naming a number nothing produced raises instead of passing: **a threshold
silently skipped is a strategy silently approved.**
