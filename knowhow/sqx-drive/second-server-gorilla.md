---
q: How is the second server (gorilla) set up, how do I run something there, and what traps does a fresh clone hit?
kw: gorilla leaseWeb second server ssh sqx2; bin/remote.sh git pull; bin/mirror-data.sh; Xvfb not found worker failed to start --gui; el preflight del activo no pasa project name without asset; build time-limit not honoured never ends 3000% CPU; Runtime args -Xmx8g JVM max heap size 7.0GB; java.lang.OutOfMemoryError Java heap space WFC 2 OOS1; clone-sqx-worker.sh; sync_bars --check 27 feeds; feedQuality scan calendar.parquet write_index INDEX.md; plan.scanned AttributeError; CLI not ready right after start
tag: 🔬  date: 2026-10-11  see: eng/clean-clone-differs-from-the-working-tree, sqx-drive/three-install-topology, sqx-drive/live-chain-without-restart, pipeline/bar-library-behind-sqx-kills-the-oos2-reading
---
# gorilla is a custodian + Python box driven from leaseWeb over SSH; a fresh clone needs its heap, bars and scans checked
Run everything with `bin/remote.sh [--detach] gorilla <cmd>` (pulls first; no pull under a running SQX); data only by `bin/mirror-data.sh`.
- `sqx-worker.sh --gui` needs `$HOME/.local/bin/Xvfb` (symlink `/usr/bin/Xvfb`) or «failed to start»; the asset is read from the project NAME (`Test_Smoke_gorilla` died at step 4).
- RESOLVED, «build never ends, 3000 % CPU»: `bin/clone-sqx-worker.sh` pinned the GUI heap at `-Xmx8g` and the autopilot runs that binary headless; 7 GB on a 121.5 GiB box, custodian died of `OutOfMemoryError` in 16.5. Fixed in the script and by hand: `SQX_w2` 80g, `SQX_w1` 16g. Check `grep Xmx <install>/StrategyQuantX.config` = `sqcli.config`. Then steps 6-16 ran clean in ~1 h 40 (32 cores vs 96).
- `bin/remote.sh` pulls under `flock -w 120 .git/remote-pull.lock`: two calls at once died «Cannot fast-forward to multiple branches», exit 97, nothing run 🔬 (4 concurrent calls). Clone-vs-tree failures: `eng/clean-clone-differs-from-the-working-tree`.
- `mirror-data.sh` now also rsyncs `AlgoData/manual-fuentes` and runs `sqx.export.sync_bars` there via remote.sh (the M1 library, not SQX's `user/data`, is what Python reads). The feedQuality scan stays by hand per server.
- Fresh data root: empty `AlgoData` broke `feedQuality.scan` twice (`calendar.parquet` before `feedQuality/` exists; `write_index` read a missing `INDEX.md`), fixed in code. Bars were 27 feeds behind (`sqx.export.sync_bars --check`), which kills 18.5 and step 4 (fixed in `mirror-data.sh`, next bullet). Unscanned asset feed: `plan.scanned` refuses the plan.
- Gorilla eats only GitHub code: `8b84b8b` pushed `run.py` calling a `plan.scanned` left uncommitted on leaseWeb (`AttributeError`).
- 🔬 2026-10-15: the «workflow running» guard of `bin/remote.sh` (`pgrep -f bin/workflow.sh`) matched the remote shell itself, whose command line carries the text, so `bin/remote.sh --detach gorilla bin/workflow.sh …` was always refused with exit 96; fixed by dropping the shell's own PID (`grep -qvx $$`). Wait for a detached run with a read-only `ssh sqx2 tail --pid=<PID> -f /dev/null`: remote.sh refuses everything while a workflow runs.

## Evidence
- OPEN (owner's decision): ledgers `AlgoData/ledger/*.jsonl` (asset×TF), store and reports are per server, nothing brings gorilla's back; trial counts for multiple testing are split (gorilla: UK100_H1 only; leaseWeb: USATEC_H1, USA500_H1, DAX40_H1, XAUUSD_H1).
📓 gorilla SQX log: `Runtime args: -Xmx8g`, `JVM max heap size: 7.0GB`. Old run
`AlgoData/autopilot/Test_XAUUSD_H1_smoke_gorilla/20261010-134935/` (rc=1 after manual stop). Both servers
run SQX build 144.2953; gorilla workers: conductor 5060, custodian 5070, 32 threads.
