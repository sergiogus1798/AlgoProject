---
q: numba ZeroDivisionError, njit error_model numpy, 0.0/0.0 nan inf, kernel crashes, njit decorator flags
tag: 🔬  date: 2026-09-25  see: perf/python-parallelism
---
# Every numba kernel: `@njit(cache=True, nogil=True, error_model="numpy")`
Default `@njit` uses Python's error model: `0.0 / 0.0` raises `ZeroDivisionError` where numpy returns `nan`/`inf` with a warning.
A kernel reproducing a numpy formula (Sharpe of a zero-variance run, ratio with zero denominator) would kill the whole process. New kernels must carry the flag.
