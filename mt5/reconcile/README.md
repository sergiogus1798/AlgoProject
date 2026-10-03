# mt5/reconcile — the weeklyReconciler: the live accounts against the SQX backtest of the same week

OPEN.md #78 (owner, 2026-09-29): each weekend, the SQX backtest of the strategies that are
live, over the week that just ended, on the development data, against what the account really
did. Live EAs run on another server; this machine only **reads** the account. It **describes
and does not judge**: every gap is a number, there is no pass bar (owner pending).

```
register.csv (magic → strategy, firm)                         ── the owner's file
live:   terminal `history` verb ─▶ deals ─▶ trades per position ─▶ split by magic   (live.py)
sqx:    Test_Reconcile_<asset>_<tf>_<week> on the conductor ─▶ orderstocsv          (sqxside.py)
judge:  zones → residual whole-hour clock → cut to the ISO week → pair → gaps       (judge.py)
        MAE/MFE of BOTH sides rebuilt on the feed's M1 (PLAN §14.2)                 (floating.py)
report: result.json (study contract, no verdict) + Spanish lines on stdout          (report.py)
```

| file | what it does | run it | in → out |
|---|---|---|---|
| `run.py` | The command: owner's keys checked, the register read, each side read from the terminal / the conductor or from a parquet, one reconciliation per live EA, the week's folder written | `python3 -m mt5.reconcile.run --week YYYY-Www [--live-trades P] [--sqx-trades P] [--register CSV] [--out DIR] [--set k=v]` | a week → `AlgoData/mt5/reconcile/<week>/` |
| `week.py` | An ISO week's Monday 00:00 → next Monday 00:00 on the server's clock, and the trades OPENED inside it | imported | "2026-W38" → bounds, cut frame |
| `register.py` | The register of live EAs (`magic,strategy,identity,sqx,firm,since`), refused when absent or when a magic repeats on a firm; a strategy's asset and timeframe from its `.sqx` | imported | CSV → rows |
| `live.py` | `history_deals_get` rows (the `history` verb of `mt5/winside/query.py`, through `mt5.live.ask`) grouped by `position_id` into schema-T trades — net P&L, entry deal's magic, server clock, open positions kept with `Close time` NaT — and split by magic into the register's strategies; unregistered magics returned apart | imported | deals → {strategy: trades}, strays |
| `sqxside.py` | The SQX job, **unrun**: rule 5, a `Test_Reconcile_…` project per asset × timeframe cloned by the builder, the donor's retest rewritten by `sqx.projects.mt5verify.write_task` (asset's own costs, warm-up + week, fixed lot), run/stop/retire through `mt5.verify.sqxside` | imported | register rows + week → trades per strategy |
| `floating.py` | `portfolio…equity.excursions.rebuild` applied only to trades the M1 bars cover; NaN otherwise | imported | trades + M1 → `mae`, `mfe` |
| `judge.py` | One EA's week: `mt5.compare.to_zone`, `mt5.verify.judge.clock`/`shifted`, `mt5.compare.pair`, `in_points`; the pairs table, the trades with no twin on each side, the summary; `totals` over EAs | imported | two trade frames → pairs, lonely, summary |
| `report.py` | `result.json` in the study contract (verdict None; tabs «Resumen» and «Operaciones»), `pairs.parquet`, and the Spanish summary; step 26's ledger bars quoted as reference, never applied | imported | pieces → files, text |
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
| magic → strategy | `AlgoData/mt5/reconcile/register.csv` (`register:`) | refused |
| entry tolerance, in bars | `pairing.entry_tolerance_bars` | refused |
| what «matches» means | — | no bar: numbers only |

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
