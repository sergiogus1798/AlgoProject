# core/store — the strategy store (owner, 2026-10-08)

A strategy that passed the gate (step 8, limbo included) is irreproducible — the build is genetic —
so its `.sqx` is saved the moment it passes, and every later set of tests adds one file beside it.
Nothing is deleted when a later step fails: the step is marked in the manifest and the owner purges.
`sqx.projects.retire` refuses a project whose gate survivors are not whole here.

**Imports from:** `core.paths`, `core.sqxfile`, `core.manifest`, `core.archive` (its collector and
provenance) · **Consumed by:** `sqx.projects.retire`, `sqx.variants.rebuild`, `pipeline.autopilot.resume`. The older `core/archive` (encargo 23, sealed
snapshots written by hand) stays as the reader of what was archived before.

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Names the package; holds no code | — | — |
| `__main__.py` | Makes `python3 -m core.store` run `cli.main` | `python3 -m core.store …` | — |
| `cli.py` | The command: `save <project> [--sqx-dir DIR]`, `verify [identity…]`, `audit <project>`, `list`, `open <identity start or strategy name> --out DIR` (the folder unpacked as plain folders, its `.sqx` under the strategy's name; refused when damaged; several hits are listed, never guessed); exit 1 on a survivor without file or a damaged folder | `python3 -m core.store save Test_X` | args → printed |
| `write.py` | The only writer: `atomic` (temporary, fsync, sealed, rename), `locked` (one writer per cell: every manifest change is read-change-rewrite), `put_sqx`, `add` (one zip per set of tests, never overwritten), `pooled` (equal bytes once per cell, hard-linked into each folder), `step`, `run` | imported | files → `store/<cell>/<name> <identity8>/` |
| `verify.py` | `check(identity)`: the `.sqx` carries the folder's identity, every file its recorded sha256, nothing unnamed; `stored()` | imported | folder → problems |
| `extra.py` | What the report folders do not hand over: `population` (the files that are the same for every strategy, split into a zip of their own), `trades` (the strategy's and its sisters' trades in every exported databank — other markets, other timeframes — a databank repeating another's trades named in `also`), `sisters` (step 12's `scaling.parquet` rows with each file's identity, and the sisters' rows of every report table), `neighbours` (step 13's T1 table cut to the strategy) | imported | raw, crosstf, reports → folders to zip |
| `late.py` | What steps 13-20 leave outside the report folders: `mothers` (identity a task gave a strategy -> the one it is stored under, from every export's `lineage.csv`), `names`, `cut`, `exports` (an export's sub-folders: MC simulations, SPP runs, WFM cells), `variants` (step 16.5's batch and the studies read on it), `leftovers`, `unpaired` | imported | raw, reports, variants → folders to zip |
| `audit.py` | `held` / `missing(project)`: what a project left on disk that no stored strategy's zip holds (`FALTA`, exit 1) and what vouches for no stored strategy (`ajeno`) | `python3 -m core.store audit Test_X` | project folders → printed |
| `save.py` | `project(name, sqx_dirs)`: every gate survivor of a project with its studies, trades everywhere, sisters, cosecha rows, cost card and each step's verdict; `unsaved(name)` for the retire guard | imported | reports, harvest, autopilot → store |

## On disk

```
AlgoData/store/<SYMBOL>_<TF>_<template>/      a cell: every run of it saves here
  runs.json                                   project -> generated, survivors, saved, no_sqx, run
  .pool/<sha256>.zip                          every zip's bytes, once; the folders hard-link them
  <strategy name> <first 8 of its identity>/
    strategy.sqx                              once, read-only
    manifest.json                             cell, origin, files {name: sha256…}, steps {n: verdict…}
    gate.Results.<day>.zip                    one zip per study × databank × day: this strategy's rows,
                                              its per-strategy JSON and `distribuciones.parquet`
    gate.Results.<day>.poblacion.zip          what is the same for every strategy of the run (the
                                              population JSON, the funnel, the rejected): one inode
    crossmarket.<databank>.<day>.zip          a repeat with other content is `….2.zip`
    operaciones.<databank>.<day>.zip          its trades and its sisters' in that databank: build,
                                              OOS, other markets (step 10), other timeframes (step 12)
    hermanas.<day>.zip                        step 12's sisters: parameters to rebuild them
                                              (`python3 -m sqx.variants.rebuild`) and their results
    exportacion.<databank>.<day>.zip          an export's sub-folders: MC simulations, SPP runs, WFM cells
    variantes.<day>.zip                       step 16.5's variants batch (almost all of the disk a
                                              strategy costs past step 12)
    optimizacion.<day>.zip                    the studies read on that batch (cloud, WFC, CSCV, 18.5)
    metricas.zip                              the strategy's metrics
    vecinas.zip                               its rows of step 13's T1 neighbours table
    cosecha.<databank>.<day>.zip              the strategy's metrics, equity and trades rows
    costes.<SYMBOL>.zip                       the cost card on the day of saving
```

**Distributions.** A study that draws a z or a p from simulations writes `distribuciones.parquet`
beside its report through `core.study.draws` — per distribution the observed value, the 200-bin
histogram over the whole range, the 100 extremes of each side and, unless they come thousands at a
time, the draws themselves. Its rows carry the identity or the strategy's name, so they enter the
study's zip with the rest: no test is rerun to look at one.

**The pool.** A folder still holds every file — copying it elsewhere carries everything — and the
disk pays once for what 41 strategies share. After a purge, a pool file with `st_nlink == 1` is
garbage.

A strategy SQX gave a second identity (each the other's mother in `lineage.csv`, `late.aliases`) is saved whole
under the gate's identity: its crossmarket and sisters ride in the same folder.

The state «where it got to» is nothing but the steps in the manifest and the files present. A cut
write leaves a hidden `.tmp`; a file written but not yet named in the manifest is an orphan `verify`
reports and the next `save` adopts.

WFM and blindJoint reports are filed under the mother through `lineage.csv` (the WFM gives a
strategy another identity). `audit` is the check that nothing was left out. A smoke run (an empty
file `smoke` in its autopilot folder) marks its steps `smoke: true`. Resuming a retired project
from the store is `pipeline.autopilot.resume`.

## Not built yet

Saving from inside the workflow at step 8 and after each step; re-running a stored strategy in SQX
and comparing with the stored numbers; steps 21 on (atrCalculator, structural); the window's zone.
Skills: `/store-save`, `/store-open`, `/store-resume`, `/rebuild-sister`.
