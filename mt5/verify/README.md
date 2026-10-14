# mt5/verify — step 26: SQX at each prop firm's conditions against MT5 on that firm's account

The owner's design (2026-09-29, replacing encargo 34 §2's "translate SQX's history"): **one SQX
backtest per firm, priced with that firm's conditions, compared with the MT5 backtest of the EA
SQX exported, on that firm's own account.** No clicks: the terminal logs into each saved account
by itself. The window's **MT5 BRIDGE › Verificar** zone launches it (`ui/daemon/mt5bridge/`).

```
strategy.sqx ─▶ conditions (MT5, each account: spread now, swap, leverage) + assets (commission)
            ─▶ sqx.projects.mt5verify: Test_ project on the conductor — «MT5 FTMO», «MT5 HANTEC», «MQL5»
            ─▶ sqxside: start, load, run, sync, stop · orderstocsv · retire the project
            ─▶ mt5side: compile the exported .mq5 · tester on each account ([Common] Login/Server)
            ─▶ judge: clock offset · pair · the five rows of encargo 34 ─▶ result.json (study contract)
```

| file | what it does | run it | in → out |
|---|---|---|---|
| `autopilot.py` | Step 26 as an autopilot action: the window's preflight over a list of finalists, one check each, the pool filled. | imported by `pipeline.autopilot` | finalists + the owner's dates, model, firms → pool rows, `out/verificados.csv`, `out/mt5verify.log`, one summary line |
| `conditions.py` | A prop firm's conditions for one symbol, read off its own MT5 account and put in SQX's units. | imported | account + symbol → `sqx_settings`-shaped costs |
| `firms.py` | Which prop firms the bridge can verify on: their saved MT5 account and their symbol names. | imported | asset → firms usable, or why not |
| `judge.py` | Compare each firm's SQX retest with its MT5 backtest on the rows of encargo 34, and judge. | imported | trade lists + costs → verdict, tables, chart |
| `mt5side.py` | The MT5 half of a check: compile the EA SQX exported, and backtest it on each firm's account. | imported | `.mq5` → trades per firm |
| `pool.py` | The validated pool of step 26: an append-only register per prop firm, the first verdict per check counts. | `python3 -m mt5.verify.pool [--rebuild]` | `AlgoData/mt5/verify/<run>/` → `AlgoData/pool/<firm>.csv` |
| `report.py` | Write mt5.verify.run's result.json (the study contract) and its run.json, and mark a crash. | imported | summaries + tabs → the two files |
| `run.py` | Step 26: one strategy in SQX at each prop firm's conditions against its MT5 backtest on that firm's account. | `python3 -m mt5.verify.run --strategy <sqx> --from YYYY-MM-DD --to YYYY-MM-DD --model ohlc_m1 [--firms ftmo,hantec] [--set k=v]` | a `.sqx` → a verdict per firm |
| `sidebyside.py` | Every SQX entry beside the MT5 trade each firm's EA opened for it: one row per entry, one set of columns per firm. | imported | `firm_result`'s pairs → one table block |
| `sqxside.py` | The SQX half of a check: a Test_ project on the conductor, one retest per firm, the EA exported. | imported | project → trades per firm |
| `ticks.py` | The optional second MT5 pass on real ticks: its backtest, its verdict beside the chosen model's, and the merged tab with three curves per firm. | imported by `run.py` | pieces → the Verificación tab |
| `config.yaml` | Role, the donor's retests reused, the databank names, SaveToFiles' generator and first magic, slippage 0, tester polling, clock search span; thresholds as `ledger:<key>` | edited | — |

## Decisions it carries

- **Which data SQX runs on:** its own (Dukascopy/Darwinex feed), with the firm's costs — so the
  comparison answers "is SQX's long history valid for this firm" (owner, 2026-09-29).
- **Spread:** the one the firm quotes at the moment of reading (owner: «spread actual del
  símbolo»). It moves with the hour: 41 points on FTMO's gold at 19:31 Madrid on 2026-09-29.
- **Sizing: the strategy's own, on both sides** (owner, 2026-09-29, after the first real run).
  `sqx.projects.mt5verify.own_sizing` reads `strategy_Portfolio.xml`'s `<MoneyManagement>`
  (only FixedSize today; anything else is refused); the retest tasks get it through
  `tasksettings.set_money_management`, and the exported EA is compiled with
  `UseMoneyManagement = false` and `mmLotsIfNoMM` = that lot (`mt5side.fixed_lots`). Neither side
  does it on its own: the task applies the donor's ATR sizing whatever `customSettings` says,
  and SaveToFiles writes the EA with a «Fixed Amount» of its own.
- **Slippage 0 in SQX:** the MT5 tester does not slip a market order.
- **The window and the tester's model have no default** — some firms' data is poor.
- **R in row 2** is the SQX side's average losing trade, because the doctrine's strategies
  carry no stop (an older one may: `Strategy 3.48.75` stops at 4×ATR, and its initial risk would
  be the other reading). Unconfirmed reading of encargo 34's "≤ 0.05 R" — the owner's to confirm.
- **Row 5** is the drawdown of the balance at each trade's close; the intraday floating one
  with M1 bars is still pending.
- **Desde/Hasta in the window** (owner, 2026-09-29 §3.2): Hasta defaults to the last day
  `assets/symbols/<S>.yaml`'s `data.to` says SQX holds (`ui.daemon.mt5bridge.runs.hasta_default`),
  editable, the day before that (a range closing on SQX's last day never starts). Desde defaults
  to `MT5`: the job reads each firm's first month of whole H1 weeks once the terminal is open
  (`knowhow/mt5/mt5-history-depth-first-bar.md`), `HISTORY_FALLBACK_YEARS` (4) only when no
  server answers.
- **Every asset names its symbol at each firm** in `mt5:` of its file —
  `knowhow/mt5/mt5-symbols-csv-only-had-one-row.md`.

## Traps

- **`mt5.initialize(path=…)` must not start the terminal**: its child holds the Windows Python's
  stdout and `wine.run` waits forever. `wine.open_terminal()` starts it detached first
  (`knowhow/mt5/mt5-account-switch-unattended.md`).
- **MetaEditor and the tester need the terminal closed**: `wine.close_terminal()` posts
  WM_CLOSE (`taskkill` without /F) before each.
- **A file name with a space never reaches MetaEditor whole** (`wine.run`): the EA is copied
  to `V<hhmmss>_<name>` before compiling.
- **The terminal stays on the last account used.** It only backtests; the live EAs run on
  another server.
- **An asset whose `mt5:` does not name a firm stops that firm** — never guessed
  (encargo 35 §1 #3).
