# sqx/curate — act on a verdict inside SQX

The only folder here that **changes what a databank contains**. Everything it does is reversible from
the snapshot it takes first, and nothing runs without `--apply`.

| file | what it does | run it | in → out |
|---|---|---|---|
| `apply_verdict.py` | Moves the strategies a verdict rejected into another databank of the same project, after backing the source up | `python3 -m sqx.curate.apply_verdict --project XAUUSD --databank RetestMarkets --verdict <path>/verdict.csv --into Rejected --apply` | `verdict.csv` → strategies moved, snapshot in `AlgoData/snapshots/` |

## The three guards, and why each exists

1. **The master's GUI must be closed.** This is the one place in the project that drives the master
   install rather than the worker, because a project's databanks only exist inside their own install.
   Its databases take an exclusive lock while the GUI holds them, and a file changed underneath a
   running instance is silently undone by the next sync. The command checks and refuses.
2. **A snapshot is taken before anything moves**, into `AlgoData/snapshots/<date>/<project>/<databank>/`,
   outside the install. It has to be outside: every sync deletes on-disk strategies that are not in
   memory, so a backup inside `user/projects` is not a backup.
3. **The result is verified by counting the files back**, not by trusting the reply. If the number
   that left the source does not match the number the verdict named, the command stops and prints
   where the snapshot is.

## Before the first run

Create the destination databank **in the GUI**. One created over the API is not picked up by the
startup sync, so the move would report success into a databank that is not really there.

Move, never delete. A strategy that fails one test on eight markets is evidence about that test, and
the population it came from is the input to every later study.
