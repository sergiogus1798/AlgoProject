# portfolio/testroot — a second data root for test runs of the real code

A test of the portfolio module runs the **real** code — the real ledger writer, the real archive
writer, the real CLIs — and only its destination changes: `ALGO_DATA_ROOT=<root>` in the
environment makes `core/paths.py` take that folder as the data root, and every process says so on
its first line of stderr (`RAÍZ DE PRUEBA: …`). Nothing else redirects: every module reads
`core.paths.DATA`, the ones that cache a path at import (`pool.ROOT`, `store.ROOT`, `funded.RUNS`)
included, so the variable must be set **before the process starts**, never patched in afterwards.

The root is `<real data root>/portfolio/_test/root/`. The test pool `Test_nikkei_ref` lives there.

**Imports from:** `core.*`, `engines.market.calibrate`, `portfolio.common.construct.equity`, `sqx.inspect.feeds` · **Consumed by:** the tests of `portfolio/`, by hand

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Names the package; holds no code | — | — |
| `build.py` | Creates the test root: real, empty folders for what a run writes (`ledger`, `archive`, `portfolio`, `reports`, `harvest`, `barsDerived`, `projects`, `tmp`) and symlinks for what it only reads (`bars`, `atrCalculator`, `funding`, `projects/registry.csv`); `required()` refuses a command on the real root; `PSEUDO_OOS2_FROM`, the date of the test calendar's pseudo oos2. `--root PATH` builds a second, disposable root there (its own empty ledger; refused on the real root or a parent of it) — for what can be done once, like opening a pool's oos2 | `python3 -m portfolio.testroot.build [--root PATH]` | → the root, and the line that runs a command under it |
| `guard.py` | Proof a run left a folder alone: `fingerprint` (path, size, mtime of the files matching a glob), `untouched` (raises when it moved), `readonly` (chmod the tree for the block, restore after) | imported | folder → hash, or an error |
| `harvest.py` | The traded (stop) versions' cosecha rewritten under the test root, keyed by the **grafted file's own identity**, with a stand-in daily curve; prints the `core.archive archive` command of each strategy. Test roots only | `ALGO_DATA_ROOT=<root> python3 -m portfolio.testroot.harvest --project P --databank Stop_p90 --family simple:long` | real `harvest/<P>/<D>/` → the test root's |

## Traps
- **A symlink is read-only by convention only.** A write through `bars/` or `funding/` lands in
  the real root, so nothing a portfolio run writes is linked; a phase that needs another input
  adds it to `build.LINKS`, after checking that nothing it runs writes there. `reports/` is NOT
  linked for that reason (`monteCarlo.report` writes there): an archive made in the test root
  freezes no study result.
- **`guard.readonly` is not for the real ledger.** chmod takes the write from every process, and
  other sessions and a running autopilot append to `AlgoData/ledger/` at any time. On the real
  ledger use `guard.untouched(REAL / "ledger", "PORTFOLIO_*")` — the studies only a portfolio run
  writes. A search also logs one row in each member's own study (`NIKKEI225_M30_simple_long`),
  which the autopilot writes too: there the proof is a unique token in the row's `note`, absent
  from the real file (`tests/test_portfolio_testroot.py`).
- **`equity.parquet` of the test cosecha is NOT SQX's curve.** Step 24 keeps no daily curve of the
  stop version (the retested copies are cleared from `WFC_Build`/`WFC_OOS1`, and the fabricated
  `.sqx` still carries the mother's curve, without the stop), and
  `pipeline.autopilot.traded.harvest` keys its rows by the MOTHER's identity. So `harvest.py`
  writes the engine's own M1 rebuild as a stand-in: the universe's «daily-low 100 %» against it is
  circular and proves nothing. The MAE/MFE licence is measured against SQX's own columns and is real.
  **A stop version cannot be archived from real files today** — that needs step 24 to keep the curve.
- **The test root's ledger starts empty**, so every count read from it (`ledger.trials.overall`,
  a member study's N) is the test's own rows, not the project's.
- **Pseudo oos2.** The test pool has no trades after 2023 and no real oos2 look is spent:
  `--set calendar.pseudo_oos2_from=2022-01-01` cuts oos1 there and calls its tail oos2 (the run is
  marked `AJUSTADO`). It exercises the code that reads a later segment; it is never a holdout.
- **To start over:** `chmod -R u+w <root>/archive && rm -r <root>/{archive,harvest,portfolio,ledger}`
  (an archived version is sealed), then `build`, `harvest`, the archive commands, `pool declare`.
