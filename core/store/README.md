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
| `__init__.py` | The strategy store: one folder per strategy that passed the gate, one file per set of tests. | — | — |
| `__main__.py` | Makes `python3 -m core.store` run `cli.main`. | `python3 -m core.store …` | — |
| `audit.py` | Whether everything a project left on disk is in the store: each folder in some zip, or ignored by name. | `python3 -m core.store audit Test_X` | project folders → printed |
| `cli.py` | The store's command: save a project's survivors, verify what is stored, list it, open one. | `python3 -m core.store save Test_X` | args → printed |
| `collect.py` | Bring a gorilla project's survivors to leaseWeb for step 26 (owner, 2026-10-15, D-1 = A). | no command of its own; `portfolio/common/construct/adopt.py` is it: `bin/remote.sh gorilla collect [P] [--dry-run]`, which also archives | gorilla store, ledger, registry, reports, harvest (not `_aparte`) -> the same here, `_gorilla` |
| `extra.py` | What the report folders do not hand a stored strategy: its trades everywhere, its scaled sisters, and which files are the population's. | imported | raw, crosstf, reports → folders to zip |
| `late.py` | What steps 13 to 20 leave outside the report folders: the rest of each export, and the variant batch. | imported | raw, reports, variants → folders to zip |
| `rekey.py` | Re-key the store after `core.sqxfile.identity` changed: each folder and manifest to the identity its own .sqx has now. | `python3 -m core.store rekey [--dry-run]` | store → renamed folders, `identity-map-<YYYY-MM>.csv`, backup of the manifests, the loose CSVs through every map |
| `save.py` | Save a project's gate survivors into the store: the .sqx once, then one file per set of tests. | imported | reports, harvest, autopilot → store |
| `verify.py` | Whether a stored strategy is whole: its file carries its identity and every file its recorded hash. | imported | folder → problems |
| `write.py` | Write into a strategy's folder so that a cut leaves it as it was or as it will be, never half. | imported | files → `store/<cell>/<name> <identity8>/` |

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

## What else holds an identity (encargo 76, review 2026-10-16)

`rekey` moves the store's folders and manifests, then carries every `identity-map-*.csv` into the
loose CSVs that are later matched against a fresh `sqxfile.identity` (dry run 2026-10-16: 19,030
old cells in 1,271 files, not yet rewritten). Two folders of one cell whose `.sqx` now give one identity are
the same strategy saved twice: `rekey` folds the older into the latest `saved_at` — every study file
the keeper lacks, with its manifest entry and step — and archives it under `backups/store-rekey-<day>/merged/`
(owner, K76b C, 2026-10-17). Twins in two cells still stop it. The rest:

| holder | where | handling |
|---|---|---|
| curate verdicts, export `identity.csv`/`lineage.csv`, `tf_mothers.csv`, autopilot verdicts | `reports/`, `raw/`, `autopilot/`, `harvest/` CSVs | **migrated** by `rekey` (`TABLES`), columns `*identity*` and `mother` |
| harvest parquets (`metrics`, `equity`, `trades`) | `harvest/<P>/`, `metrics/<P>/` | re-derived: a re-harvest keys them anew; only store rows are in the map |
| study result JSON (mcRetest provenance, decay) | `reports/<P>/…/*.json` | labels; re-derived on rerun, matched only through the verdict CSVs above |
| the archive | `archive/<identity>/<stamp>/` (sealed) | **not migrated**: 22 of 91 folders under an old key; needs rename + manifest + parquet column + re-seal (`core/archive`) |
| MT5 verify runs and `pool.sqlite` | `mt5/verify/*/run.json`, `pool/pool.sqlite` | migrated once by hand on 2026-10-16 (`backups/mt5-rekey-2026-10-16`); a next change needs it in this verb |
| sisters' `fabricated_identity` | `scaling.parquet` inside the store zips (sealed) | not in the map (sisters are not stored strategies): `sqx.variants.rebuild` warns loudly on a mismatch |
| live-fleet register | `fleet/magics.csv` | not present here; rewrite through the map where it exists |
| identity memo of the window | `ui/memo/identities-*.pkl` | re-derived: its name carries the mtime of `core/sqxfile.py` |
| ledger | `ledger/` | holds no strategy identity (`ledger/report.py` reads the harvest parquet by the hash it is given) |

## Not built yet

Saving from inside the workflow at step 8 and after each step; re-running a stored strategy in SQX
and comparing with the stored numbers; step 21 on (steps 22-24 were deleted on 2026-10-11); the window's zone.
Skills: `/store-save`, `/store-open`, `/store-resume`, `/rebuild-sister`.

A manifest may also carry `aliases` (the identity the strategy had before 2026-10-12, when the signal
variables left the hash) and `merged` (what a second folder of the same strategy said, folded in
that day) — `knowhow/sqx-format/identity-differs-across-databanks.md`.
