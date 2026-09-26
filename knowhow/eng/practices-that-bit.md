---
q: python heredoc bash -c SyntaxError, verify SQX write, session names unstable, forkserver ProcessPoolExecutor fork deadlock threads, set_forkserver_preload, ELECTRON_RUN_AS_NODE bad option --no-sandbox
tag: 🔬  date: 2026-09-18  see: eng/moving-module-into-layer, perf/process-pool-shutdown
---
# Practices that already bit
- Complex Python: write it to a file and run it; never `bash -c` heredocs (quoting → `SyntaxError: '(' was never closed`).
- Verify an SQX write by reading back what SQX stored; the `loadconfig` auto-rename (`knowhow/sqx-drive/`) lands "successful" writes elsewhere.
- Identity goes in files, not session names (auto-named, change on reopen; `ListAgents` shows only live ones). One owner per lane (`sqx/CLAUDE.md`).
- `ProcessPoolExecutor` in a process that has threads: use `forkserver`, never `fork`; reuse one pool.
- Launch SQX with `ELECTRON_RUN_AS_NODE` unset.

## Evidence
- 🔬 2026-09-10: `portfolio/common/monteCarlo/`'s own Flask explorer (retired 2026-09-25, encargo 19)
  ran analysis on its request thread; `fork` pool deadlocked mid 7th sub-test, no error, no CPU (child
  inherits a mutex held by another thread). Fix: `multiprocessing.get_context("forkserver")` +
  `set_forkserver_preload([...])` (workers start with numpy imported). Was 19 pools × 96 workers per
  strategy → one reused pool. The trap is moot now that `ui/daemon/runs.py` runs
  `portfolio.common.monteCarlo.report` as its own subprocess rather than importing it into a shared
  server thread — but the `forkserver`-over-`fork` rule inside the pool itself still holds.
- 🤔 `set_forkserver_preload()` takes the module path as a string: no import checker follows it; a wrong
  one only gets slower (workers reimport numpy). After moving a module, grep its dotted path in strings and
  time one strategy (2m07s → 2m01s, 36-strategy XAUUSD databank, 3,000 sims = unchanged).
- 🔬 VS Code exports `ELECTRON_RUN_AS_NODE`; inherited, SQX's Electron shell runs as Node and the GUI dies with `bad option: --no-sandbox`.
