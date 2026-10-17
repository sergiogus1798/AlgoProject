# ui/daemon/mt5bridge — MT5 BRIDGE › Verificar

Owner, 2026-09-29: the bridge with MetaTrader 5 is a section of this same window, and it starts
with one thing — verifying a strategy's performance in SQX and in MT5 (encargo 34 §0.5). The job
itself is `mt5.verify.run` (`mt5/verify/README.md`); this package lists, checks and queues.

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | MT5 Bridge › Verificar: one strategy in SQX at each prop firm's conditions against its MT5 backtest. | imported | — |
| `api.py` | MT5 Bridge's routes: the form's options, past checks, one result, the preflight and the job. | imported | request → JSON |
| `display.py` | How a stored Verificar result reads in the window: capitals, percentages and one line per firm. | imported by `runs.result` | dict → dict |
| `runs.py` | What MT5 Bridge › Verificar reads and checks: past checks, the strategy's file, and whether one may start now. | imported | disk → JSON |

## Contracts and traps

- **It reaches SQX and MT5, so it is a launcher** (hard rule 3): `mt5verify` is in
  `sqx.worker.winddown.LAUNCHERS` (a cancel lets the job's `finally` stop the conductor) and in
  `launch.api.LAUNCHERS` (it and «Lanzar en SQX»/«Continuar workflow» refuse each other).
- **Nothing is defaulted**: the window's dates, the tester's model and the firms come from the
  owner each time (some firms' data is poor), and a missing one is a refusal, not a guess.
- **An open MT5 terminal is a refusal**: the job opens and closes it itself, and the owner may
  be looking at it.
- **`/close-terminal` is the exception**: it always acts, even with `mt5verify` running — a
  terminal that needs forcing is not legitimately serving a job — and only warns in its reply.
