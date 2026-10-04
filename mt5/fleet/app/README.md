# mt5/fleet/app — MetaTracker: the window over the live MT5 fleet on the VPS

Encargo 35, piece A. **A desktop app of its own, apart from `ui/`** (owner, 2026-10-02 — a
conscious exception to «anything with an interface is a view inside `ui/`», for the fleet and the
reconciliation only), with its own theme and no daemon: it reads the files the collector leaves
in `AlgoData/fleet/live/<login>.json` (a literal copy of what `../vps/FleetBeacon.mq5` writes
every 30 s) and repaints every `refresh_s`. It never reaches the VPS and writes nothing.

`bin/metatracker` opens it (desktop entry `metatracker.desktop`). Manual: chapter `93-metatracker`.

| file | what it does | run it | in → out |
|---|---|---|---|
| `launch.py` | Opens the window, or saves a capture of it | `python3 -m mt5.fleet.app.launch [--root DIR] [--tab NAME] [--account LOGIN] [--shot PNG] [--at EPOCH]` | beats → window, PNG |
| `window.py` | The tab shell (Flota · Estrategias · Despliegue · Salud · Conciliación), the refresh timer, the desktop notification when a light turns red or silent | imported | rows → widgets |
| `tab_fleet.py` | Flota: totals strip, one row per account, and the chosen account's curve, reasons, progress, positions and deals | imported | rows → widgets |
| `tab_strategies.py` | Estrategias: every live magic over all accounts, and its entries paired across accounts | imported | histories → tables |
| `tab_deploy.py` | Despliegue: EAs expected by the workbook against the charts mounted, and the magics that trade | imported | sheet, charts → table |
| `tab_health.py` | Salud: each terminal's connection, ping, build, errors; the VPS's RAM, CPU, disk | imported | beats, vps.json → tables |
| `tab_reconcile.py` | Conciliación: the newest reconciled week, summary per strategy and paired trades | imported | result.json → tables |
| `widgets.py` | The Qt pieces: cells, tables, cards, legend, scrolling pages | imported | — |
| `chart.py` | The matplotlib canvas (`FigureCanvasQTAgg`) of the day's curve | imported | curve → canvas |
| `curve.py` | The day's equity curve: minute rows, hourly extremes of `hours[]`, the two floors | imported | history → series |
| `equity.py` | One strategy's cumulative net per account (and the combined sum), win rate, max drawdown in % of size; no Qt (`tests/test_fleet_equity.py`) | imported | trades → series |
| `state.py` | One row per account (beat, stage, floors, risk, deals, progress) and its light; all reasons listed worst first: silent, red, yellow, green | imported | beats → rows |
| `floors.py` | The firm's day start, the day's starting balance, the daily and total floors through `portfolio.funded.rules.floors`, the day's worst equity, and why a figure is approximate | imported | beat + stage → distances |
| `risk.py` | Each position's loss at its SL, the equity if every stop hits, positions with no SL | imported | positions → loss |
| `rules.py` | Weekend and news prohibitions against the open positions, through `mt5.newsfilter` | imported | beat + stage → reasons |
| `progress.py` | Profit against target, trading and profitable days on the firm's clock, consistency, payout | imported | deals + stage → reading |
| `eas.py` | EAs expected against mounted and the flags on each | imported | sheet, charts, trades → rows |
| `strategies.py` | Per-magic record over all accounts and the cross-account pairing | imported | trades → rows |
| `health.py` | Disconnections today, terminal and VPS readings | imported | minutes, vps.json → rows |
| `history.py` | The collector's per-account files: deals, minute rows, excursions; deals grouped into trades | imported | disk → frames |
| `fmt.py` | How a figure is written (Spanish separators, «—» where there is none) | imported | — |
| `read.py` | Beats, each account's stage and terms from the funding catalogue, the clocks, the register, the workbook, `vps.json`, the reconciliation | imported | disk → dicts |
| `theme.py` | The palette, the lights' colours, the stylesheet | imported | — |
| `config.yaml` | The owner's thresholds (see below) | edited | — |

Schema 2 figures (stop risk, weekend, news, EAs mounted, `hours[]`) show «—» on a schema-1 beat, and
an empty section says in Spanish what is missing. Every light reason is listed in the account's
detail; the worst one is the text beside the light.

**Thresholds in `config.yaml`:** `silence_s` 300, `red_margin_left` 0.25, `refresh_s` 10,
`weekend_yellow_h` 3, `weekend_red_h` 1, `news_yellow_min` 30, `silent_strategy_days` 30,
`pair_tolerance_min` 5, `pair_days` 7.

**Fixtures:** `--root DIR` points the whole tree (`core.fleetpaths.FLEET`) at a folder. There
`accounts.yaml` replaces machine.yaml's plans and `reconcile/` replaces `AlgoData/mt5/reconcile`.
`tests/fixtures/fleet/` is the one the tests and the manual's example captures use (now =
1790953220, Fri 2026-10-02 15:00 UTC).

## How a floor is computed

- The rules are the catalogue's (`catalog.plan`) and the formulas are the funded simulator's
  (`floors.daily_floor`, `floors.max_floor`) — nothing is restated here.
- **The day's starting balance** = balance − every deal booked since the firm's day began. Deal
  and position times are on the server's clock; the server's offset is `server_time −
  written_gmt`, so no server zone is assumed.
- **The firm's day** comes from `equity.firm_clocks`: FTMO `Europe/Prague`, Hantec `EETUS`
  (unconfirmed). A firm with no clock there (FundingPips) is read on the server's own midnight
  and says so on screen.
- **«≈» marks a daily figure that is not exact**, with the reason under the account's name:
  - the beat's `deals_today` starts at the **server's** midnight, so between 00:00 and 01:00
    server time FTMO's day (Prague) began before it and yesterday's deals are missing — the cure
    is in the beacon (send 48 h);
  - a `max_be` floor (Hantec, and FundingPips by the catalogue's default) starts from max(balance,
    equity) at midnight. With a schema-2 beat the `hours[]` entry whose `start` is the firm's day
    start gives that equity and the floor is exact; without it the floor uses the balance alone,
    too low (optimistic) when the floating at midnight was positive, and says «≈»;
  - the service started after the day began: `hours[]` has no entry for it, «arrancó después».
- Red: `daily_left` or `max_left` (what is left ÷ the allowance) under `red_margin_left`.

## How the other figures are computed

- **Stop risk:** per position `(sl − price)·dir / tick_size · tick_value_loss · volume`; account
  `equity_at_stops = equity + Σ`, compared strictly with each floor. Ignores slippage and gaps; a
  position with no SL counts 0, so the figure is optimistic and carries «≈».
- **Weekend / news:** only for stages whose catalogue says `weekend_ok` / `news_ok` False. Weekend by
  `friday_close`: yellow ≤ 3 h, red ≤ 1 h or past it. News by `news[]` and `mt5.newsfilter` (FTMO
  by `country:code`, Hantec every importance-3 release by currency): yellow ≤ 30 min, red inside
  the firm's window (FTMO 2 min, Hantec 3). FundingPips has no profile and uses Hantec's, marked
  «(según catálogo)»; Hantec's is «(sólo calendario MT5)».
- **Progress:** profit = balance − size; a trading day is a firm day with a non-balance deal; a
  profitable day nets ≥ `profitable_pct`·size (> 0 when none); consistency through
  `rules.consistency_ok`. Payout: the last negative balance deal; next ≈ last payout (or first
  trade) + `payout_days`; payable ≈ max(balance − size, 0)·reward share. The last two are
  approximate.
- **EAs:** matched on `(strategy, timeframe)` where the strategy is the «3.23.151» pattern of the
  expert name, comment or workbook; the symbol is not compared (brokers name it differently).
- **Pairing:** entries of one magic and side on two or more accounts, last `pair_days` days, pair when
  within `pair_tolerance_min`; the rest are listed with who is missing.
- **Peor equity hoy** is the lowest `hours[].low` since the day began (sampled every 500 ms, from
  the service's start); MAE and disconnections are at the collector's 1-minute resolution.

Tests: `tests/test_fleet_floors.py`, `tests/test_fleet_risk_rules.py`, `tests/test_fleet_progress.py`.

## Por ahora

Deferred by the owner (2026-10-03): alerts to the phone and alerts with the window closed (today a
notification only fires while the window is open). Acting on accounts (pause, close) is refused:
the app never sends, modifies or closes an order.
