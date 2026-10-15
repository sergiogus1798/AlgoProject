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
| `__init__.py` | The PORTFOLIOS zone's daemon side: what the portfolio commands wrote, as blocks, and their launchers. | imported | — |
| `analyse.py` | «Analizar»: the selected portfolio (a judged run's contract) or one strategy (its universe column). | imported | a run's `cartera.json` → tabs |
| `api.py` | The routes of the PORTFOLIOS zone: what exists, each module's tabs, and the «Calcular» launchers. | mounted by `ui/daemon/routers.py` | HTTP → the above |
| `bank.py` | «Banco» (encargo 33 §7.5): the bank's expected value per plan, re-buy policy and haircut, and the decision. | imported | `bank/` tables and decisions → tabs |
| `bankjob.py` | «Calcular la caja» as one job: the portfolio's paths, the bank table on them, then the decision. | `python3 -m ui.daemon.portfolios.bankjob --run <run> --horizon H --n-paths N --edge-from oos1[,oos2]` | a funded run → `bank/` table + decision |
| `commands.py` | What each «Calcular» of the zone launches: its command, what it still lacks, and the sentence to confirm. | imported | action + params → `{ok, reasons, text, confirm, argv, about}` |
| `construct.py` | «Constructor»: one real-path run — the portfolio chosen in build, every combination scored, its verdict. | imported | `runs/<run>/` → tabs |
| `correlation.py` | «Correlación»: a pool's pair measures as a matrix judged against the threshold, and its admissible graph. | imported | `universe/<key>/pairs*.parquet`, `screen.json` → tabs |
| `funded.py` | «Fondeo»: one funded run — stage A's P(pass) per combination and risk, stage B's three Monte Carlos, its verdict. | imported | `runs/<run>/` → tabs |
| `owner.py` | «Entradas del dueño» (encargo 54, A): the inputs the funding modules refuse without, written from the window. | imported | `{id, value}` → `config/owner.yaml` |
| `parts.py` | The pieces every portfolio reader answers with: contract blocks, tabs, the relaxed line, the words. | imported | values → contract blocks |
| `shelf.py` | What exists under the portfolio folder: pools, runs, universes, bank tables — listed, never computed. | imported | `AlgoData/portfolio/` → dicts |
| `weights.py` | «Pesos» and «Incubación»: the weight walk-forward's decision, and the incubation reading if one exists. | imported | `weights_wf/`, `incubation/` → tabs |

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
