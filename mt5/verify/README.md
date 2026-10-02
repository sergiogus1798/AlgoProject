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
| `run.py` | The job: rule 5, each firm priced, the SQX project built/run/retired, the EA compiled and backtested per account, the comparison, one ledger row per firm (step 26), `result.json` + `run.json` in `AlgoData/mt5/verify/<run>/` | `python3 -m mt5.verify.run --strategy <sqx> --from YYYY-MM-DD --to YYYY-MM-DD --model ohlc_m1 [--firms ftmo,hantec] [--set k=v]` | a `.sqx` → a verdict per firm |
| `firms.py` | The firms with a saved account (`core.paths.MT5_ACCOUNTS`, from `config/machine.yaml`), their symbol names (`mt5:` of `assets/symbols/<S>.yaml`, versioned with the asset since 2026-09-30), and `config()` with the ledger's thresholds filled | imported | asset → firms usable, or why not |
| `conditions.py` | One symbol's specification read off the firm's server, and its costs in SQX's units: spread now (points × point ÷ SQX tick), swap by MT5's mode, triple-swap day; commission from `assets/symbols/<S>.yaml` `costs.commission.brokers.<firm>` — refused when unconfirmed | imported | account + symbol → `sqx_settings`-shaped costs |
| `sqxside.py` | The builder's command for the `Test_MT5Verify_…` project, the run on the conductor (only `action=status` between start and «Project finished», stop in a `finally`), the trades by `orderstocsv` with the worker down, and `sqx.projects.retire` | imported | project → trades per firm |
| `mt5side.py` | Compile the exported EA under a space-free name, and one tester pass per account, waited for | imported | `.mq5` → trades per firm |
| `judge.py` | Every row on price moves at the asset's one point value, SQX and MT5 alike (`mt5.compare.in_points`; owner 2026-09-30: SQX prices a JPY pair at a fixed rate, MT5 at the day's — USD only shown). SQX's times converted from the feed's zone to the server's (`mt5.compare.to_zone`, `clock.server_zone`: the firms change hour on US dates, the5ers' feed on Israel's), then any whole-hour offset left read off the trades — close pairs first (`knowhow/eng/mt5-verify-clock-zones.md`) —, the pairing (`mt5.compare.pair`) and the five rows against `ledger/thresholds.yaml` (`mt5verify.*`); one firm's verdict, unpaired-trades table and daily curves (`firm_result`), the shared parameter table (`params_table`) and the merged chart of every firm's pair of curves (`combined_chart`) — one tab, not one per firm (owner, 2026-09-29 §3.7) | imported | trade lists + costs → verdict, tables, chart |
| `sidebyside.py` | The side-by-side trades table (owner, 2026-09-30: paired by entry time): one row per SQX entry in the feed's clock, then per firm the P&L of its own SQX retest, the MT5 entry in its server's clock and the MT5 P&L, empty when the EA opened nothing there; the last 500 entries; `firm_columns` lists each firm's three columns so its light hides them | imported | `firm_result`'s pairs → one table block |
| `report.py` | Writes `result.json` in the study contract and `run.json` beside it — the headline is `pass` when every firm validates, `watch` («Validada en FTMO») when some do, `fail` when none; marks a crashed run `failed` so the window never shows it running forever | imported | summaries + tabs → the two files |
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
  (`knowhow/eng/mt5-history-depth-first-bar.md`), `HISTORY_FALLBACK_YEARS` (4) only when no
  server answers.
- **Every asset names its symbol at each firm** in `mt5:` of its file —
  `knowhow/eng/mt5-symbols-csv-only-had-one-row.md`.

## Traps

- **`mt5.initialize(path=…)` must not start the terminal**: its child holds the Windows Python's
  stdout and `wine.run` waits forever. `wine.open_terminal()` starts it detached first
  (`knowhow/eng/mt5-account-switch-unattended.md`).
- **MetaEditor and the tester need the terminal closed**: `wine.close_terminal()` posts
  WM_CLOSE (`taskkill` without /F) before each.
- **A file name with a space never reaches MetaEditor whole** (`wine.run`): the EA is copied
  to `V<hhmmss>_<name>` before compiling.
- **The terminal stays on the last account used.** It only backtests; the live EAs run on
  another server.
- **An asset whose `mt5:` does not name a firm stops that firm** — never guessed
  (encargo 35 §1 #3).
