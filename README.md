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
authoring anything · `knowhow/` the facts that cost time to discover · `docs/` generated reference ·
`audit/` daily reports · `archive/` finished work, no longer maintained.

## Setting up on a new machine

```bash
cp config/machine.example.yaml config/machine.yaml   # edit the paths for that machine
python3 -m pip install -r requirements.txt
python3 tools/checks.py                              # should be green
```

Nothing else is machine-specific: `core/paths.py` is the only module that knows where anything lives.
Python 3.10 to 3.13; numpy, scipy and arch have no wheels for 3.14 yet.

## Windows

The project splits in two, and only one half is tied to Linux.

| half | what it does | Windows |
|---|---|---|
| export and curation | `core/worker.py`, `core/exportdrv.py`, `sqx/export/`, `sqx/curate/` | **no** — they all shell out to `bin/sqx-worker.sh`, which needs `rsync`, `ss`, `curl` and `setsid`. They raise a clear `RuntimeError` instead of failing obscurely |
| analysis | `tasks/`, `strategies/`, `portfolio/`, the panels and reports | **yes** — pure Python over CSVs that are already exported |

So the working split is: export on the Linux machine, then analyse the CSVs on either. Set up on
Windows exactly as above, with forward slashes in `machine.yaml`:

```yaml
data_root: C:/Users/<you>/Desktop/AlgoData
sqx_master: C:/none      # required to be present, never opened on Windows
sqx_worker: C:/none
```

Porting `sqx-worker.sh` to cross-platform Python would remove the split; it is not done.

## Working here

Read `CLAUDE.md` — it holds the rules that prevent irreversible damage, and a router that says which
file to open for which task. Read `CODESTYLE.md` before writing Python. Data never goes in this
repository; it lives in the data root, indexed by `~/Desktop/AlgoData/INDEX.md`.

Three specialists run over the project: `/audit` checks it daily for drift, breakage and weak
statistics, `/doc` records what a session discovered so the next one does not rediscover it, and
`/sync` keeps the GitHub copy equal to this machine so a clone elsewhere works — see
`docs/manual/10-github.md`.
