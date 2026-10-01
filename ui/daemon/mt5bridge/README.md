# ui/daemon/mt5bridge — MT5 BRIDGE › Verificar

Owner, 2026-09-29: the bridge with MetaTrader 5 is a section of this same window, and it starts
with one thing — verifying a strategy's performance in SQX and in MT5 (encargo 34 §0.5). The job
itself is `mt5.verify.run` (`mt5/verify/README.md`); this package lists, checks and queues.

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | The package's one-line purpose | imported | — |
| `runs.py` | `listing()` every `AlgoData/mt5/verify/<run>/run.json`, newest first; `result(run)` its `result.json`; `options()` the saved accounts, the tester's models and the archive; `strategy_file()` the `.sqx` from the archive or `strategy.locate`; `check()` the preflight and the confirmation text | imported | disk → JSON |
| `api.py` | `GET /api/mt5bridge/options`, `/runs`, `/result?run=`; `POST /preflight` and `POST /verify` (the same preflight re-run, plus `launch.queued`, then one job on the conductor lane labelled `mt5verify`); `POST /close-terminal` — `mt5.wine.close_terminal()`, then `kill_terminal()` if that fails, for a terminal wedged open past the window's own controls | imported | request → JSON |

## Contracts and traps

- **It reaches SQX and MT5, so it is a launcher** (hard rule 3): `mt5verify` is in
  `winddown.LAUNCHERS` (a cancel lets the job's `finally` stop the conductor) and in
  `launch.api.LAUNCHERS` (it and «Lanzar en SQX»/«Continuar workflow» refuse each other).
- **Nothing is defaulted**: the window's dates, the tester's model and the firms come from the
  owner each time (some firms' data is poor), and a missing one is a refusal, not a guess.
- **An open MT5 terminal is a refusal**: the job opens and closes it itself, and the owner may
  be looking at it.
- **`/close-terminal` is the exception**: it always acts, even with `mt5verify` running — a
  terminal that needs forcing is not legitimately serving a job — and only warns in its reply.
