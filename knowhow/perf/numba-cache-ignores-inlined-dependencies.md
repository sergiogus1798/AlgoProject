---
q: Why does a numba kernel with cache=True keep running old code after I edit a module it calls?
kw: numba cache=True stale, edited dependency not recompiled, nbi nbc not invalidated, kernel returns old results after edit, tick reader parallel compile, njit inlined function other module, fork compile once in parent
tag: 🔬  date: 2026-10-13  see: eng/moving-packages-numba-cache, perf/numba-division
---
# numba `cache=True` does not invalidate when a module whose functions the kernel inlines changes
The disk cache is keyed on the kernel's own source file. Editing a function defined in another module that the kernel calls (numba inlines it) leaves the stale `.nbi`/`.nbc` in use, with no warning.
Hit twice: the PCG kernels (`engines/nulls/lookup.py`, `studies/screening/analysis/permuted.py`) and the parallel tick reader (`core/tickparallel.py`).
Rule: no disk cache for kernels that call another module's `@njit` functions; compile once in the parent process before forking, so children inherit the compiled code. Cost: 0.55-3.76 s per parent process (2.91 s on the first tick read of a process).

## Evidence
Reproduced on a minimal pair (kernel in one file calling a function in another, edit the callee, rerun) by the fourth independent review of encargo 66 (2026-10-13): the cached kernel returned the old value.
Tick reader without cache: EURUSD (306 M ticks) 9.47 s serial -> 1.61 s parallel, XAUUSD (651 M) 20.44 s -> 3.28 s, bit-identical to the serial read.
