# mt5/reconcile — the weeklyReconciler: the live accounts against the SQX backtest of the same week

OPEN.md #78 (owner, 2026-09-29): each weekend, the SQX backtest of the strategies that are
live, over the week that just ended, on the development data, against what the account really
did. Live EAs run on another server; this machine only **reads** the account. It **describes
and does not judge**: every gap is a number, there is no pass bar for «coincide»: the report describes and the bar is set after 8 real weeks (owner, 2026-10-15).

```
magics.csv + workbook → register (magic → strategy, firm)      ── derived, register.py
live:   terminal `history` verb ─▶ deals ─▶ trades per position ─▶ split by magic   (live.py)
sqx:    Test_Reconcile_<asset>_<tf>_<week> on the conductor ─▶ orderstocsv          (sqxside.py)
judge:  zones → residual whole-hour clock → cut to the ISO week → pair → gaps       (judge.py)
        MAE/MFE of BOTH sides rebuilt on the feed's M1 (PLAN §14.2)                 (floating.py)
report: result.json (study contract, no verdict) + Spanish lines on stdout          (report.py)
```

| file | what it does | run it | in → out |
|---|---|---|---|
| `floating.py` | Live trades' MAE and MFE rebuilt from M1 wicks (PLAN §14.2), only where the bars cover the trade. | imported | trades + M1 → `mae`, `mfe` |
| `judge.py` | One strategy's week: live trades paired with the SQX backtest's, and every gap as a number — no pass bar. | imported | two trade frames → pairs, lonely, summary |
| `live.py` | The live side: an account's deals of one week as trades in the project's trade frame, per strategy. | imported | deals → {strategy: trades}, strays |
| `register.py` | The register of live EAs: which magic number on which firm's account is which strategy. | imported | magics.csv + workbook → rows |
| `report.py` | Write a week's reconciliation as result.json (the study contract) and say it in Spanish. | imported | pieces → files, text |
| `run.py` | weeklyReconciler: one ISO week of the live accounts against the SQX backtest of the same strategies. | `python3 -m mt5.reconcile.run --week YYYY-Www [--live-trades P] [--sqx-trades P] [--register CSV] [--out DIR] [--set k=v]` | a week → `AlgoData/mt5/reconcile/<week>/` |
| `sqxside.py` | The SQX side: the live strategies retested over one week in a Test_Reconcile project on the conductor. UNRUN. | imported | register rows + week → trades per strategy |
| `week.py` | One ISO week on the server's clock: its bounds, and the trades that belong to it. | imported | "2026-W38" → bounds, cut frame |
| `config.yaml` | The owner's keys (empty = refused), the register's place, the clock, the SQX job's knobs | edited | — |

## What it writes — `AlgoData/mt5/reconcile/<week>/` (`core.paths.MT5_DATA`)

- `result.json` — the study contract; `summary.strategies["<firm>/<strategy>"]` and `summary.totals`.
- `pairs.parquet` — every paired trade of the week, all gaps, with `firm` and `strategy`.
- `live/trades.parquet` — the live side as read: `live.COLUMNS` + `firm`, `strategy` (None: unregistered magic).
- `sqx/trades.parquet` — **the fresh-stretch retest, for a second reader** (PLAN §14.5 M9, the
  portfolio's paper OOS): orderstocsv's schema T + `strategy`, `identity`, feed clock, the
  warm-up trades included (cut by `Open time` yourself). Either file can be fed back with
  `--live-trades` / `--sqx-trades` to judge again without a terminal or a worker.

## The owner's, with no default (rule 11)

| what | where | until then |
|---|---|---|
| which `mt5_accounts` are live | `live.accounts` | refused when the terminal would be read |
| magic → strategy | not an owner's file: derived from the fleet's `AlgoData/fleet/magics.csv` + the workbook (`register.read()`, owner 2026-10-15) | refused in Spanish while `magics.csv` is absent |
| entry tolerance, in bars | `pairing.entry_tolerance_bars` = 1, as step 26 (owner 2026-10-15) | — |
| what «matches» means | — | no bar: numbers only, until 8 real weeks have run |

## Decisions it carries (each one a reading the owner may overturn)

- **A trade belongs to the week it OPENED in**, server clock (as `mt5.compare.window`); a live
  position still open is paired on its entry and has no P&L yet (`live_open`).
- **Points** are price moves in the asset's `tick_size`, size-free; **currency** figures put
  SQX's booked P&L at the live trade's lot (`Size_live / Size_sqx`), so the SQX lot is irrelevant.
- **MAE/MFE are rebuilt on both sides** from the same M1 bars at the asset's point value: SQX's
  exported `MAE ($)` is priced at its fixed rate (`knowhow/mt5/reconcile-mae-both-sides-rebuilt.md`).
  The bars are the development feed's (`core.barstore`), not the broker's.
- **SQX costs**: the asset's own of segment `sqx.segment` (oos2), not the firm's.

## Traps

- `mt5.live.ask(account=…)` **switches the open terminal to that account**; the command closes
  the terminal when it has read every live account.
- The retest cannot end on SQX's last data day (`sqxside.window`): the week's Friday is only
  read once the feed holds Saturday — check on the first real run.
- `sqx.warmup_days` (60) is unmeasured: too short and SQX's first trades of the week differ
  from a long backtest's.
