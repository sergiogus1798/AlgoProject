# perf — el catálogo de rendimiento

Qué cuesta cada parte cara del proyecto, en tiempo y en memoria, medido de la misma forma cada vez
para que dos fechas se puedan comparar.

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | makes `perf` a regular package, so it beats the system `perf` module Ubuntu's linux-tools puts on the path (gorilla) | — | — |
| `catalogue.py` | measures every target, appends it, judges it against last time | `python3 -m perf.catalogue` | registry → rows in `history.csv` |
| `store.py` | the catalogue files, the commit and the machine's load at the time | imported | rows → CSV under the data root |
| `verdict.py` | what counts as a regression, and what is only noise | imported | history → one verdict per target |
| `config.yaml` | every tunable: repeats, thresholds, worker counts, sample data | read | — |

Subfolders: `inputs/` what is measured · `measure/` how it is measured · `disk/` what the data root
holds.

## The three commands

```bash
python3 -m perf.catalogue                      # measure everything, store it, judge it
python3 -m perf.catalogue --only strategies    # one area, or one target name
python3 -m perf.catalogue --hotspots montecarlo.analyse   # where that target's time and memory go
python3 -m perf.catalogue --scaling            # also re-measure the machine's memory ceiling
python3 -m perf.disk.report                    # inventory AlgoData: size, duplicates, formats; also /tmp's use %
```

`catalogue` **exits non-zero when anything regressed**, so it can sit in cron unattended.

## Rules this module keeps

- **It never touches StrategyQuant X.** Every target reads files already exported. The catalogue
  has to be runnable while a build is running, which is exactly when the owner wants it.
- **History is append-only.** `history.csv` under the data root only grows. A row is never edited:
  the comparison between dates is the whole product.
- **Times are compared per unit of work.** An export that grew from 500 to 3,000 trades is not a
  regression, and the panel would say it was if it compared wall clock.
- **A change smaller than the measurement's own spread is called `noisy`, not `steady`.** Saying
  steady would claim the instrument can see something it cannot.
- **`cpu_s` is the whole process tree too** (owner, 2026-10-07): the runner adds its reaped and
  its living children to its own CPU time. Rows measured before that date count the parent only.
- **The memory number is the whole process tree, as PSS** (`/proc/<pid>/smaps_rollup`). `ru_maxrss`
  of a parent that spawns 96 workers reports the largest single child; summed RSS counts a page
  shared by forked workers once per worker (a 200 MB array under 4 children reads ~1 GB, PSS reads 200 MB).
- **Timings are clean.** `tracemalloc` runs only when memory is asked for (`--memtop`, i.e.
  `--hotspots`): it inflated object-heavy code x1,83 and numpy code x0,98. `alloc_peak_mb` is blank
  in a timing run. The scaling probe builds and touches its vectors before the clock starts.
- **The figures restart on 2026-10-13** (owner, D8, encargo 66 §10): the three measurement fixes
  above make every earlier row incomparable, so the old `history.csv` was moved to
  `AlgoData/profiling/_antes-2026-10-13/` and the catalogue starts empty; the first full run
  after that date is the new baseline.
