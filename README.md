# AlgoProject

Strategy development for MetaTrader 5. StrategyQuant X generates and robustness-tests candidates;
Python does the mathematics that decides which of them are real.

## The phases

| folder | what happens there |
|---|---|
| `1_sqx/` | Everything touching StrategyQuant X: reading projects, authoring blocks, groups, templates and build projects, and getting data out |
| `2_tasks/` | Whole databanks at once — the maths on a population of thousands of generated strategies |
| `3_strategies/` | One promising strategy in depth, including translating it into Python and reconciling that against SQX |
| `4_portfolio/` | Combining strategies, separately for funded accounts and for real capital |
| `5_mt5/` | Deployment and live-versus-backtest. Reserved, not built |

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

## Working here

Read `CLAUDE.md` — it holds the rules that prevent irreversible damage, and a router that says which
file to open for which task. Read `CODESTYLE.md` before writing Python. Data never goes in this
repository; it lives in the data root, indexed by `~/Desktop/AlgoData/INDEX.md`.

Two specialists run over the project: `/audit` checks it daily for drift, breakage and weak
statistics, and `/doc` records what a session discovered so the next one does not rediscover it.
