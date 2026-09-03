# core — shared library

Everything that more than one phase needs. Import it as a package from the project root; scripts that
live deeper add the root to `sys.path` in their first lines.

| file | what it does | in → out |
|---|---|---|
| `paths.py` | The only module that knows where anything lives. Reads `config/machine.yaml` | names → `Path` |
| `sqxfile.py` | Read a `.sqx` without SQX: identity hash, symbol, inner XML, parameters | `.sqx` → values |
| `cfx.py` | Read a `project.cfx`: task chain, output databanks, acceptance conditions | project → dicts |
| `worker.py` | Start, stop and command the headless worker over its HTTP API | command → reply |
| `exportdrv.py` | The three exports SQX offers: trades, databank metrics, bars | request → files |
| `manifest.py` | Write and read the `manifest.json` every export must carry | facts → JSON |
| `assets.py` | Load per-asset overrides; `python3 -m core.assets <SYMBOL>` is the preflight | symbol → report |

Two rules specific to this folder:

- **No absolute path may appear anywhere but `paths.py`.** `tools/checks.py` enforces it.
- These modules read and drive SQX, they do not analyse. Maths belongs in a phase folder.
