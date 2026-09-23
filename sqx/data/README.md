# sqx/data — keep SQX's own data store current

One job: run the data update the GUI's "Update all" button runs, and then make
`assets/_policy.yaml` agree with what SQX now holds.

| file | what it does | run it | in → out |
|---|---|---|---|
| `update.py` | Download fresh bars on the master, guarded, and refresh every asset's data range | `python3 -m sqx.data.update [--apply] [--symbol SYM]` | — → bars, `_policy.yaml` |

**It must run on the master, and only with its GUI closed.** Both halves of that matter:

- *On the master*, because `bin/sqx-worker.sh` runs
  `rsync -a --exclude='History/' "$MASTER/user/data/" "$WORKER/user/data/"` on every start. The flow
  is master → worker. `History` is a shared symlink so new bar files would land correctly, but the
  three H2 databases a backtest actually reads are per-install copies, and a worker's fresh copy is
  overwritten by the master's stale one at the next start. A download run on a worker disappears
  while the master keeps building on old bars.
- *With the GUI closed*, because hard rule 2 forbids `sqcli` on the master while it is up. The
  module reads `/proc` and refuses; it never kills anything. The owner closes it himself.

**Why the snapshot is not a formality.** Every `sqcli` run ends with `Synchronizing databanks to
files`, and hard rule 1 says that sync deletes on-disk `.sqx` the databank does not hold in memory.
So `update.py` inventories every `.sqx` under `user/projects` before and after, saves both to
`AlgoData/backups/data-update/`, and reports any that vanished. An empty report is the only
acceptable result.

Dry run by default: it prints the exact command line and the file count, and changes nothing.
`--apply` is the only thing that downloads.

The read-only half of this — refreshing the data ranges without touching the master — is
`python3 -m core.assets --dataranges`, which asks the conductor and is safe at any time.
