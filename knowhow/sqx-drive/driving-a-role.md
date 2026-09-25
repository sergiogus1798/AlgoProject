---
q: worker roles conductor custodian in Python and bash; core/paths WORKERS worker_dir worker_staging; --role flag; sync_bars rsync creates destination; port triple formula
tag: 🔬  date: 2026-09-21  see: sqx-drive/three-install-topology, sqx-drive/version-stamps-stale
---
# Roles live only in `core/paths.py`; scripts take `--role ROLE` and ask Python for the install
`core/paths.py`: `WORKERS` (role → `{"path","port"}`), `worker_dir(role)`, `worker_staging(role)`.
`core/worker.call/start/stop/wait_ready(..., role="conductor")`. `bin/sqx-worker.sh --role ROLE`,
`bin/clone-sqx-worker.sh ROLE`. Unknown role → `KeyError`, never a fallback to the conductor.
Port triple from the CLI port: editor = cli+1, web = 8080 + (cli−5050)/10.

## Evidence
- Conductor is not in `machine.yaml`'s `sqx_workers` block: it is `sqx_worker` + `worker_port`, so
  `WORKER`, `WORKER_PORT`, `STAGING` keep their old meaning; older consumers work untouched.
- Bash scripts get three stdout lines from Python (`MASTER`, path, port) — no YAML parsing in bash.
- 🤔 No fallback: a silent one would send a 3-hour retest to the install that must stay answerable.
- Ports: master 5050/5051/8080, conductor 5060/5061/8081, custodian 5070/5071/8082;
  `clone-sqx-worker.sh` computes them, no three constants to disagree.
- `sync_bars` = `rsync -a "$MASTER/user/data/" "$WORKER/user/data/"`; rsync creates the destination,
  so on an uncloned role it built 42 MB of bars with no `sqcli`, then `clone-sqx-worker.sh` refused
  ("worker already exists"). `sync_bars` now stops unless `$WORKER/sqcli` is executable.
  `check` and `stop` are read-only and still report on a missing install.
