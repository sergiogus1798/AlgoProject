# perf/measure — how a number is taken

Execution only. What gets measured is `perf/inputs/`; what the number means is `perf/verdict.py`.

| file | what it does | run it | in → out |
|---|---|---|---|
| `harness.py` | spawns the target, samples the whole tree's RSS, keeps the median of N runs | imported | target name → one measurement |
| `runner.py` | the subprocess that actually calls the target, with tracemalloc watching | internal to the harness | target name → JSON |
| `hotspots.py` | `cProfile` and the allocation sites alive at the peak, for one target | imported | target name → two rankings |
| `scaling.py` | a STREAM triad at 1…96 processes, cache-resident and DRAM-resident | imported | config → two curves |

## Two traps this code exists to avoid

- 🔬 **`ru_maxrss` is not the answer when a target spawns workers.** For the child processes it
  reports the largest single one, not their sum. Measured 2026-09-20: `montecarlo.analyse` reads
  535 MB by `ru_maxrss` and **2,340 MB** by sampling the process tree. The harness samples the tree.
- 🔬 **A `tracemalloc` snapshot taken after the call shows what survived, which is nothing.** The
  sites that matter are alive at the peak, so `runner.py` keeps a snapshot from the moment the
  traced total was highest.

Sampling every 50 ms can miss a peak shorter than that, so the tree figure is a floor, not a
ceiling. `self_rss_mb` is stored beside it as the cross-check.
