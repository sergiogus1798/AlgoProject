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

⚠️ **Known exception, fix it while you are here:** `bin/clone-sqx-worker.sh` and
`bin/sqx-worker.sh` carry the original machine's paths hard-coded at the top
(`/home/sergioguslw/Desktop/SQX`). `checks.py` only scans `.py` files, so it does not catch them.
**Edit `MASTER` and `WORKER` in both scripts before running either**, or they will operate on paths
that do not exist — or worse, on the wrong install.

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

**Two is the working minimum, and it is what the code assumes today.**

| install | role | GUI | command API | who may touch it |
|---|---|---|---|---|
| **master** | the owner's. Holds his projects and his data feeds | yes, he opens it | port 5050 — **dead while the GUI is up** | read-only for agents |
| **worker** | headless clone. Every export, authoring and retest job | never | **port 5060 — always answers** | agents, one job at a time |

The reason is not preference, it is measured: with the master's GUI running, its CLI replies
`Error: CLI not ready.` A headless second install has no GUI to compete with and answers always.

**A third install** is worth it only when two jobs must run at once — typically a long retest holding
a large databank while something else exports. The reason it helps is not throughput, it is
**safety**: every SQX sync deletes on-disk `.sqx` files it does not hold in memory, so touching the
install that holds a 5,000-variant databank is how work gets destroyed. A second worker lets that
databank sit undisturbed.

If you add one, give it its **own** port triple (e.g. 5070 / 5071 / 8082), its **own** copy of the H2
bar files, and add it to `machine.yaml`. Note that `core/paths.py` exposes a single `WORKER` and
`WORKER_PORT` today: supporting a pool is a code change, not configuration.

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

```bash
# 1. Point the script at THIS machine first.
sed -i 's|^MASTER=.*|MASTER="'"$HOME"'/Desktop/SQX"|;s|^WORKER=.*|WORKER="'"$HOME"'/Desktop/SQX_w1"|' \
  bin/clone-sqx-worker.sh
bin/clone-sqx-worker.sh
```

What it does, and why each step exists:

| step | what | why it matters |
|---|---|---|
| 1 | `rsync` master → worker, excluding `user/data/`, `user/log/`, `user/projects/` | the worker starts with no projects of its own |
| 2 | copy the H2 bar files; **symlink** `user/data/History` | H2 files cannot be shared (exclusive lock) so each install needs its own; `History` is a raw archive and is shared |
| 3 | patch `internal/AppSettings.txt` → sqcli 5060, editor 5061 | two installs on the same ports collide |
| 4 | **rewrite every absolute path in `settings.xml`** | ⚠️ **the dangerous one.** Without it the worker is a silent *alias* of the master and writes into it |
| 5 | patch `WebServerPortUsed` → 8081 | the third port, easy to miss |
| 6 | heap: sqcli 32 GB, GUI 8 GB | tune to the machine's RAM |

The script verifies 4 and refuses to finish if any path still points at the master. **Do not skip or
override that check.**

Then confirm the worker answers on its own port:

```bash
sed -i 's|^MASTER=.*|MASTER="'"$HOME"'/Desktop/SQX"|;s|^WORKER=.*|WORKER="'"$HOME"'/Desktop/SQX_w1"|' \
  bin/sqx-worker.sh
bin/sqx-worker.sh start
curl -sg "http://localhost:5060/call?cmd=-project%20action=list"
bin/sqx-worker.sh stop
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
| `sqx_master`, `sqx_worker` | the two folders from §3 and §4 |
| `worker_port` | 5060 unless you changed it |
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
python3 -c "from core.paths import MASTER, WORKER, DATA; print(MASTER, WORKER, DATA)"
ls "$(python3 -c 'from core.paths import DATA; print(DATA)')"   # data root exists
bin/sqx-worker.sh check                                   # bar versions agree
bin/sqx-worker.sh start && curl -sg "http://localhost:5060/call?cmd=-project%20action=list"
bin/sqx-worker.sh stop
grep -c "Desktop/SQX" bin/*.sh                            # paths are THIS machine's
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
2. The two (or three) install paths and their port triples.
3. The output of §8, verbatim.
4. Any symbol whose `core.assets` preflight exits non-zero — these block all authoring.
5. Whether `bin/*.sh` still contain any path from another machine.
