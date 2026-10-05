# ui/daemon/portfolios — the portfolio modules' routes

The PORTFOLIOS zone's daemon side (encargo 33 §7.5, PLAN M7): each module of the window's board
(Analizar, Correlación, Constructor, Fondeo, Banco, Pesos, Incubación) is one reader that turns
what `portfolio/` already wrote under `AlgoData/portfolio/` into contract tabs, and each
«Calcular» is one background job of `ui/daemon/jobs.py` running the real `python3 -m` command.
Nothing here computes a portfolio figure and nothing here reaches SQX.

```
GET /state ─▶ shelf (pools, universes, runs) + commands (what is missing)
GET /module?name= ─▶ correlation | construct | analyse | funded | bank | weights ─▶ {"tabs": [...], "relaxed", "empty", "missing"}
GET /preflight ─▶ commands.plan ─▶ {ok, reasons, text, confirm}      POST /run ─▶ plan again + nonce ─▶ jobs.start
```

**Imports from:** `portfolio/common/construct`, `portfolio/funded/{sim,decide,catalog}`, `core/paths`, `core/study`,
`ui/daemon/{jobs,proof}` · **Consumed by:** `ui/desktop/portfolios` over HTTP, `tests/test_ui_portfolios.py`

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Package marker, one docstring | imported | — |
| `parts.py` | The small block builders every reader shares: Spanish state words, one-decimal percentages, a contract table, a callout, a tab, the verdict's headline, the «AJUSTADO» banner and the empty state | imported | values → contract blocks |
| `shelf.py` | What exists on disk: declared pools, universes (pool hash + config fingerprint + builder's code), runs with their kind, plan and verdict; whether the daemon runs on a test root | imported | `AlgoData/portfolio/` → dicts |
| `correlation.py` | Correlación: the pair matrix of one measure at one frequency with a discrete state per cell against the threshold in force, the pairs list with the filter that rejects each, one pair's detail | imported | `universe/<key>/pairs*.parquet`, `screen.json` → tabs |
| `construct.py` | Constructor: the chosen portfolio, every scored combination, the null and the verdict with the oos2 line; `spent(pool, members)`, the sentence of a pool whose oos2 is read — for a launcher it says whether that portfolio gets its stored reading back or is refused | imported | `runs/<run>/` → tabs |
| `analyse.py` | Analizar: the selected run's figures per segment each with its one-line explanation, its curve with the members named, the monthly table | imported | a run's `cartera.json` → tabs |
| `funded.py` | Fondeo: stage A (P(pass) per combination and risk), stage B (D, T1, T2) and the verdict; the plans of the catalogue; what blocks a launch | imported | `runs/<run>/` → tabs |
| `bank.py` | Banco: the decision sentence, the EV table per plan and rebuy policy against the filters, EV(h) with the monkey line and the Monte Carlo error; the owner inputs still unanswered | imported | `bank/` tables and decisions → tabs |
| `weights.py` | Pesos (the walk-forward table and its sentence) and Incubación (its rows, or the plain statement that it is not running) | imported | `weights_wf/`, `incubation/` → tabs |
| `commands.py` | One action → its argv, its Spanish refusals and, for the two verdicts, the confirmation sentence that names the pool and says oos2 is read once | imported | action + params → `{ok, reasons, text, confirm, argv, about}` |
| `bankjob.py` | The bank's three steps as ONE job: `frompool` (the portfolio's paths) → `sim.run` (the bank per plan) → `decide.run` (the decision); stops at the first that fails | `python3 -m ui.daemon.portfolios.bankjob --run <run> --horizon H --n-paths N --edge-from oos1[,oos2]` | a funded run → `bank/` table + decision |
| `api.py` | The router: `/api/portfolios/state`, `/module`, `/pair`, `/preflight`, `POST /run`, `POST /pool` | mounted by `ui/daemon/routers.py` | HTTP → the above |

## Contracts and traps

- **An unanswered knob is never defaulted here** (rule 11). `commands.plan` returns it as a reason
  («falta `<knob>`: decisión tuya») and the job is not queued. `--set` overrides are accepted
  only when the daemon runs on a test root (`ALGO_DATA_ROOT` under `portfolio/_test`).
- **The two verdict actions need a nonce.** `/preflight` issues it with the confirmation text;
  `/run` plans again and refuses a nonce that is missing, spent or of another action.
- **One portfolio job at a time**: the commands share the universe cache. A second stage B of a
  run no longer rewrites it: `funded_b.target` gives the rerun a run folder of its own (OPEN #104-4),
  which the databank lists as a new row.
- **A universe is keyed by the WHOLE config fingerprint**, so a chain of actions must carry the
  same overrides or the next step does not find the previous one's universe.
- **oos2 is never read by a reader**: the tabs show it only when the run's own verdict wrote it.
