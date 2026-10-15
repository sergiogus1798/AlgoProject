# config — machine-specific settings

| file | in git | what |
|---|---|---|
| `machine.example.yaml` | yes | the template, with every key commented |
| `machine.yaml` | **no** (gitignored) | this computer's copy; the only file that may differ between machines |
| `owner.yaml` | **no** (gitignored) | the owner's local layer, written by the window's «Entradas del dueño»: `sim:` and `construct:` sections laid over `portfolio/funded/sim/config.yaml` and `portfolio/common/construct/config.yaml` before any `--set`; absent until he types something |

Copy the example to `machine.yaml` and edit it. `core/paths.py` is the only module that reads it (`owner.yaml` is read by `core/study/config.py`);
everything else asks `core.paths`.

| key | meaning |
|---|---|
| `data_root` | where exported data lives (never inside the repo); the one that matters on Windows |
| `sqx_master`, `sqx_worker`, `worker_port` | the StrategyQuant X installs (master GUI, headless conductor) and the conductor's API port |
| `sqx_workers.custodian` | optional third install (`path`, `port`) for one long job at a time |
| `ui_port` | the desktop app's local daemon, loopback only (optional, 8765) |
| `mt5_prefix`, `mt5_accounts`, `fleet` | MetaTrader 5 under Wine, its saved funded accounts, the live fleet (optional) |
| `claude_bin`, `browser` | Claude Code CLI for the window's template chat; browser that renders the manual to PDF |
| `strategy_pools` | folders of `.sqx` files worth indexing, by short name (optional) |

No `.py` file sits in this folder.
