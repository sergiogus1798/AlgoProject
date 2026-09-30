# AlgoProject

Strategy development for MetaTrader 5. StrategyQuant X generates and robustness-tests candidates;
Python does the mathematics that decides which of them are real.

## The phases

| folder | what happens there |
|---|---|
| `sqx/` | Everything touching StrategyQuant X: reading projects, authoring blocks, groups, templates and build projects, and getting data out |
| `tasks/` | Whole databanks at once — the maths on a population of thousands of generated strategies |
| `strategies/` | One promising strategy in depth, including translating it into Python and reconciling that against SQX |
| `portfolio/` | Combining strategies, separately for funded accounts and for real capital |
| `mt5/` | Deployment and live-versus-backtest. Reserved, not built |

Supporting them: `core/` shared library · `assets/` per-asset cost overrides that must be read before
authoring anything · `knowhow/` the facts that cost time to discover · `docs/` generated reference. The daily
reports of the unattended agents live in the data root, `AlgoData/audit/`.

## Setting up on a new machine

```bash
cp config/machine.example.yaml config/machine.yaml   # edit the paths for that machine
python3 -m pip install -r requirements.txt
python3 tools/checks.py                              # should be green
```

Nothing else is machine-specific: `core/paths.py` is the only module that knows where anything lives.
Python 3.10 to 3.13; numpy, scipy and arch have no wheels for 3.14 yet.

That covers a machine that only analyses already-exported data. Setting up **StrategyQuant X itself**
— how many installs, cloning the headless worker, the port triples, and the check that stops the
worker being a silent alias of the master — is `docs/SETUP-NEW-MACHINE.md`. Follow it in full on any
machine that has to drive SQX.

## Windows

The project splits in two, and only one half is tied to Linux.

| half | what it does | Windows |
|---|---|---|
| export and curation | `core/worker.py`, `core/exportdrv.py`, `sqx/export/`, `sqx/curate/` | **no** — they all shell out to `bin/sqx-worker.sh`, which needs `rsync`, `ss`, `curl` and `setsid`. They raise a clear `RuntimeError` instead of failing obscurely |
| analysis | `studies/`, `engines/`, `portfolio/`, over CSVs already in the data root | **yes** |
| the desktop app | `ui/` | **yes**, with no SQX install — `bin\algoui.cmd` |

Set up exactly as above, with forward slashes in `machine.yaml`, and drop the `sqx_workers` and
`strategy_pools` blocks:

```yaml
data_root: C:/Users/<you>/Desktop/AlgoData
sqx_master: C:/none      # required to be present, never opened on Windows
sqx_worker: C:/none
```

`bin\algoui.cmd` sets `PYTHONUTF8=1` before starting the window, and the daemon's jobs get it too:
without it Python on Windows reads and prints in cp1252. With no install, a template's page shows
its bound holes as bound to a group this install lacks — the group names live in the install's
`blockGroups.xml`. Verified on 2026-09-26 by a clean copy of the tree with no SQX path, every zone
walked offscreen; not yet on a real Windows box.

Porting `sqx-worker.sh` to cross-platform Python would remove the split; it is not done.

## Working here

Read `CLAUDE.md` — it holds the rules that prevent irreversible damage, and a router that says which
file to open for which task. Read `CODESTYLE.md` before writing Python. Data never goes in this
repository; it lives in the data root, indexed by `~/Desktop/AlgoData/INDEX.md`.

Three specialists run over the project: `/audit` checks it daily for drift, breakage and weak
statistics, `/doc` records what a session discovered so the next one does not rediscover it, and
`/sync` keeps the GitHub copy equal to this machine so a clone elsewhere works — see
`docs/manual/01-empezar.pdf` (cap. 10-github).
