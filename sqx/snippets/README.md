# sqx/snippets — the project's own Java snippets for SQX

Java that SQX compiles and runs inside itself, mirrored as `user/extend/` wants it:
`Snippets/SQ/…` the `.java`, `Code/<language>/blocks/` a block's code templates. Writing snippets is
the extension the vendor offers; nothing here reads or decompiles SQX's own classes
(`SQ_License_and_Service_Terms.pdf` §4.9).

| file | what it does | run it | in → out |
|---|---|---|---|
| `install.py` | Copy the snippets into a stopped worker, start it once so SQX compiles them, stop it, and verify — `pending()` names what an install does not run yet; also creates the tool project | `python3 -m sqx.snippets.install --role conductor\|custodian [--check]` | this folder → the install's `user/extend/` and `Snippets.jar` |
| `toolproject.py` | `Trade_AlgoTools`, the one-task project a CustomAnalysis snippet is run from: it reads any other project's databank, so no workflow project carries a task that is not a backtest | imported | a role → its `project.cfx` |
| `Snippets/SQ/CustomAnalysis/AlgoBank.java` | Whole databanks from memory: every strategy's orders, statistics, equity and XML in one `.abk` per databank (format: `core/bankfile.py`) | `sqx.export.membank` in a live session | `project\|databank` → `.abk` under `core.paths.bank_dir` |
| `Snippets/SQ/Blocks/RandomEntry/SeededRandomEntry.java` | A random entry that reproduces: true on a bar when a hash of (bar time, `Seed`) falls under `Probability` | a template or a strategy that names the block | — |

Three traps, all 🔬 2026-10-12 (`knowhow/sqx-drive/snippets-compile-on-start.md`):

- **SQX compiles on start and loads what the previous start compiled.** A new snippet needs two
  starts; `install.py` spends the first.
- **One compile error and NO snippet is updated** — SQX keeps every old class and says so only in
  its log (`Compilation FAILED`). The old class then runs under the new name. `install.py` reads
  that log and `pending()` compares the jar's time with the source's.
- **A workflow project cannot carry a CustomAnalysis task**: 17 places in `sqx/projects/` treat
  every task XML as a backtest. Hence the tool project.
