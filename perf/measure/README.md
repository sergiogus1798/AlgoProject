# perf/measure — how a number is taken

Execution only. What gets measured is `perf/inputs/`; what the number means is `perf/verdict.py`.

| file | what it does | run it | in → out |
|---|---|---|---|
| `harness.py` | Run a target in its own process, watch the whole tree's memory, and keep the median run. | imported | target name → one measurement |
| `hotspots.py` | Where one target's time and memory actually go: the functions and the allocation sites. | imported | target name → two rankings |
| `runner.py` | Run one target inside its own process and report what it cost. Internal to the harness. | internal to the harness | target name → JSON |
| `scaling.py` | What this machine gives when every core asks for memory at once, which is the real ceiling. | imported | config → two curves |

## Two traps this code exists to avoid

- 🔬 **`ru_maxrss` is not the answer when a target spawns workers.** For the child processes it
  reports the largest single one, not their sum. Measured 2026-09-20: `montecarlo.analyse` reads
  535 MB by `ru_maxrss` and **2,340 MB** by sampling the process tree. The harness samples the tree.
- 🔬 **A `tracemalloc` snapshot taken after the call shows what survived, which is nothing.** The
  sites that matter are alive at the peak, so `runner.py` keeps a snapshot from the moment the
  traced total was highest.

Sampling every 50 ms can miss a peak shorter than that, so the tree figure is a floor, not a
ceiling. `self_rss_mb` is stored beside it as the cross-check.
