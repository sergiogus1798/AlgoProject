# Setting this project up on a new machine

**Who this is for:** the agent asked to configure AlgoProject and its StrategyQuant X installations
on a machine that has never run it. Follow it top to bottom. Every step says what to verify, because
several of the failures here are silent — the worst one produces a worker that looks fine and
quietly corrupts the master.

**What the owner has decided:** the platform must run on **several Linux machines**. Windows is
wanted for development only, and is understood to be partial today — see §7.

---

## 0 · Before anything: what is and is not machine-specific

| | where | travels in git? |
|---|---|---|
| All code | the repo | yes |
| **Every machine-specific value** | `config/machine.yaml` | **no** — this is the only file that differs |
| The template for it | `config/machine.example.yaml` | yes |
| Exported data | the data root (`~/Desktop/AlgoData` by convention) | **never** — heavy data must not enter the repo |

`core/paths.py` is the **only** module allowed to read `machine.yaml`, and the only place an
absolute path may appear. `python3 tools/checks.py` enforces that.

`bin/sqx-worker.sh` and `bin/clone-sqx-worker.sh` carry no paths of their own: they ask
`core/paths.py` for the install of the role they were given. Nothing in `bin/` has to be edited on a
new machine, and `tools/checks.py` now scans `bin/*.sh` as well as the `.py` files, so a path
creeping back in fails the check instead of hiding for months.

---

## 1 · System prerequisites

Linux, and these on `PATH`:

```bash
for c in rsync ss curl setsid md5sum stat nohup python3 git; do
  command -v "$c" >/dev/null || echo "MISSING: $c"
done
```

`ss` comes from `iproute2`, `setsid` from `util-linux`; both are usually present. Python 3.10–3.13
(3.14 has no wheels for numpy, scipy or arch yet).

⚠️ **On this owner's machines `sudo` prompts for a password and is not available to agents.** Install
Python packages with `pip install --user` into `~/.local/bin`, never with `apt`. If a system package
is genuinely missing, stop and tell the owner rather than trying to work around it.

```bash
git clone <repo> AlgoProject && cd AlgoProject
python3 -m pip install --user -r requirements.txt
```

---

## 2 · How many SQX installations, and why

**Three per machine is the shape the code now speaks**, and each has a fixed role. Two — master plus
conductor — is a valid, supported configuration; the custodian is optional and everything works
without it.

| | install | role | GUI | port triple (cli / editor / web) | `-Xmx` sqcli | `coreUsage` (96c / 16c) | who may touch it |
|---|---|---|---|---|---|---|---|
| **M** | `~/Desktop/SQX` | the owner's. His projects, his data feeds | yes, he opens it | 5050 / 5051 / 8080 — **dead while the GUI is up** | 24g | **`-1` on both — untouched** | read-only for agents |
| **W1** | `~/Desktop/SQX_w1` | **conductor**: short jobs, always awake — exports, authoring, queries | never | **5060** / 5061 / 8081 | 16g | 8 / 2 | agents, freely |
| **W2** | `~/Desktop/SQX_w2` | **custodian**: one long job at a time | never | **5070** / 5071 / 8082 | 48g | 48 / 8 | agents, one job, no command in between |

Why a headless worker at all is measured, not preference: with the master's GUI running its CLI
replies `Error: CLI not ready.` forever. A headless install has no GUI to compete with.

Why a **second** worker, in order of value:

1. **A busy worker cannot answer.** One worker means a three-hour retest queues every list, count and
   status behind it. The conductor is what keeps the system answerable.
2. **It removes a class of failure rather than mitigating it.** Every SQX sync deletes on-disk `.sqx`
   it does not hold in memory. Give a 5,000-variant databank an install nobody commands and that risk
   stops existing.
3. **It overlaps the two expensive stages** — one worker exports while the other retests.

The core split is **elastic**: leave the master at `coreUsage = -1` and cap only the workers, so an
idle machine gives the owner's generation everything. That also means **the master's own
`settings.xml` is never edited**, which keeps hard rule 3 clean. Full reasoning, with the measured
numbers, in `knowhow/03-driving-sqx.md` § *The three-install topology*.

A third install costs **~3 GB, not 98**: `user/data/History` is a symlink to the master's and only
the three H2 bar files are copied.

In `machine.yaml`, the conductor is `sqx_worker` + `worker_port`; every other role goes under
`sqx_workers` as `path` + `port`. `core/paths.py` exposes them as `WORKERS`, `worker_dir(role)` and
`worker_staging(role)`; `WORKER`, `WORKER_PORT` and `STAGING` still mean the conductor. Asking for a
role `machine.yaml` does not define raises — which is the right answer on a two-install machine.

⚠️ **Check the SQX licence before running more than one headless instance.** Nobody has read the
EULA on this point. Ask the owner; do not decide it yourself.

---

## 3 · Install the master

Done by the owner, by hand, from StrategyQuant's own installer. An agent does not automate this.
What you need afterwards:

1. The install folder — it contains `internal/` and `user/`.
2. Its data imported (symbols, feeds) through the GUI. Bars are the slow part; they cannot be
   copied from another machine's master except via `user/data/`, which §4 handles.
3. The GUI opened once and closed cleanly, so `user/settings/settings.xml` exists and is complete.

Verify:

```bash
ls ~/Desktop/SQX/internal/AppSettings.txt ~/Desktop/SQX/user/settings/settings.xml
grep -oE '<AppWebServerPort[A-Z]*>[0-9]+' ~/Desktop/SQX/internal/AppSettings.txt
```

---

## 4 · Clone the worker

**SQX and `sqcli` must both be closed.** H2 takes exclusive locks on the bar databases; cloning while
anything is running produces a torn copy that truncates backtest windows silently.

Configure `machine.yaml` first (§5) — the script reads the install paths and ports from it — then
clone one role at a time:

```bash
bin/clone-sqx-worker.sh              # conductor, the default
bin/clone-sqx-worker.sh custodian    # only if this machine is getting the third install
```

What it does, and why each step exists:

| step | what | why it matters |
|---|---|---|
| 1 | `rsync` master → worker, excluding `user/data/`, `user/log/`, `user/projects/` | the worker starts with no projects of its own |
| 2 | copy the H2 bar files; **symlink** `user/data/History` | H2 files cannot be shared (exclusive lock) so each install needs its own; `History` is a raw archive and is shared |
| 3 | patch `internal/AppSettings.txt` → the role's sqcli and editor ports | two installs on the same ports collide |
| 4 | **rewrite every absolute path in `settings.xml`** | ⚠️ **the dangerous one.** Without it the worker is a silent *alias* of the master and writes into it |
| 5 | patch `WebServerPortUsed` → the role's web port | the third port, easy to miss |
| 6 | heap: sqcli 16 GB conductor / 48 GB custodian, GUI 8 GB | the §2 table; tune to the machine's RAM |

The ports are derived from the role's cli port — editor is `cli + 1`, web is `8080 + (cli - 5050)/10`
— so the triple always matches the §2 table and a new role only ever sets one number.

The script verifies 4 and refuses to finish if any path still points at the master. **Do not skip or
override that check.**

Then confirm the worker answers on its own port:

```bash
bin/sqx-worker.sh start                       # --role conductor is the default
curl -sg "http://localhost:5060/call?cmd=-project%20action=list"
bin/sqx-worker.sh stop

bin/sqx-worker.sh --role custodian start      # the same, one port up
curl -sg "http://localhost:5070/call?cmd=-project%20action=list"
bin/sqx-worker.sh --role custodian stop
```

The port opens and answers `Error: CLI not ready.` for roughly 20 seconds before commands work, and
strategy loading finishes later still. That is normal — poll, do not conclude it is broken.

---

## 5 · Configure the project

```bash
cp config/machine.example.yaml config/machine.yaml
```

Edit it. The template documents every key; the ones that must be right:

| key | note |
|---|---|
| `sqx_master`, `sqx_worker` | the master from §3 and the **conductor** from §4 |
| `worker_port` | 5060 unless you changed it — the conductor's |
| `sqx_workers` | every other role, `path` + `port`. Omit the block on a two-install machine |
| `data_root` | **outside the repo.** Heavy data never enters git |
| `browser` | Chrome or Chromium, for rendering the manual to PDF |
| `archive`, `strategy_pools` | optional; omit the blocks entirely if absent on this machine |

Then:

```bash
python3 tools/depmap.py && python3 tools/checks.py     # must end "0 problems"
python3 tests/test_surface.py                          # property test, no data needed
python3 -m core.assets XAUUSD                          # the per-asset preflight
```

`core.assets` exiting non-zero is **not** a setup failure: it means the owner has not agreed a
spread and commission for that symbol. Report it and stop; do not fill the values in yourself.

---

## 6 · Bars, and the one rule about them

The worker's H2 bar files are a **copy**, so they go stale the moment the owner imports new data on
the master. `bin/sqx-worker.sh` handles this by syncing **on start**, when the worker is stopped by
definition and the copy is therefore always safe.

```bash
bin/sqx-worker.sh check     # compares the .version stamps; changes nothing
```

It compares `user/data/*.version`, **not** the `.db` files: H2 rewrites a database header every time
it is opened, so the bytes diverge on first run even when the bars are identical. A comparison of
`.db` files will tell you they are stale forever.

⚠️ **Two of the `.version` files are restamped by `sqcli` itself, and `check` knows it.** Every
launch writes a value of its own into `data_futures.version` and `data_stock.version` — one *newer*
than the master's — so those two differ on a worker that was synced minutes earlier. `check` prints
them as `restamp` and does **not** count them, which is what keeps its exit code meaning something.
The forex bars this project actually trades live in `data.db` and are unaffected. Measured
2026-09-21, in `knowhow/03-driving-sqx.md`.

The price of that exemption: a genuine futures or stock import on the master is not flagged by
`check`. It does not matter — `start` syncs unconditionally before every run.

---

## 7 · Windows — what works and what does not

The project splits cleanly in two, and only one half is tied to Linux.

| half | modules | Windows |
|---|---|---|
| export, authoring, curation | `core/worker.py`, `core/exportdrv.py`, `sqx/export/`, `sqx/curate/` | **no** |
| analysis | `core/surface/`, `tasks/`, `strategies/`, `portfolio/`, all reports and panels | **yes** |

The blocker is `bin/sqx-worker.sh`: bash, needing `rsync`, `ss`, `curl` and `setsid`.
`core/worker.require_posix()` raises a clear `RuntimeError` on Windows rather than failing
obscurely, and `core/exportdrv.py` and `sqx/curate/apply_verdict.py` call it at every entry point.

So **development on Windows works today for everything that reads already-exported data** — which is
the whole of the analysis work. Set `machine.yaml` with forward slashes:

```yaml
data_root: C:/Users/<you>/Desktop/AlgoData
sqx_master: C:/none      # must be present, never opened on Windows
sqx_worker: C:/none
```

⚠️ **This is a known limit, not a decision.** The owner has stated the platform must run on several
machines, and porting `sqx-worker.sh` to cross-platform Python removes the split entirely. It is
roughly a day's work and the right moment is whenever `sqx/variants/` is built, because that is when
this layer is being touched anyway. Until then, Windows is an analysis-only development box.

---

## 8 · Verification checklist

Nothing is configured until all of these pass.

```bash
python3 tools/checks.py                                   # 0 problems
python3 tests/test_surface.py                             # property test green
python3 -c "from core.paths import MASTER, WORKERS, DATA; print(MASTER, WORKERS, DATA)"
ls "$(python3 -c 'from core.paths import DATA; print(DATA)')"   # data root exists
bin/sqx-worker.sh check                                   # exit 0; restamped lines are exempt
bin/sqx-worker.sh start && curl -sg "http://localhost:5060/call?cmd=-project%20action=list"
bin/sqx-worker.sh stop
grep -c "Desktop/SQX" bin/*.sh                            # 0 — bin/ holds no paths at all
```

And one that is not a command: **read `CLAUDE.md`.** Its nine hard rules exist because each of them
has already destroyed work once. The three that bite hardest on a fresh machine:

- **Every sync deletes on-disk `.sqx` not held in memory.** Snapshot `user/projects` before anything
  that restarts SQX.
- **Never run `sqcli` against the master while its GUI is up**, and never `pkill -f StrategyQuantX`
  — that pattern matches your own shell. Kill by PID.
- **Never start a build, and never change what a project builds.** The master's configuration is the
  owner's. It is not a bug to fix and not a finding to report.

---

## 9 · What to hand back

Report to the owner:

1. Which of §1's prerequisites were missing and what you did about them.
2. The install paths and port triples of every role you created, and whether the custodian exists
   on this machine or the configuration is the two-install one.
3. The output of §8, verbatim.
4. Any symbol whose `core.assets` preflight exits non-zero — these block all authoring.
5. The output of `grep -c "Desktop/SQX" bin/*.sh` — it must be 0 on every machine, because the
   scripts resolve their install through `core/paths.py`.
