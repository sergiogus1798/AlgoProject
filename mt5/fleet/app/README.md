# mt5/fleet/app — MetaTracker: the window over the live MT5 fleet on the VPS

Encargo 35, piece A. **A desktop app of its own, apart from `ui/`** (owner, 2026-10-02 — a
conscious exception to «anything with an interface is a view inside `ui/`», for the fleet and the
reconciliation only), with its own theme and no daemon: it reads the files the collector leaves
in `AlgoData/fleet/live/<login>.json` (a literal copy of what `../vps/FleetBeacon.mq5` writes
every 30 s) and repaints every `refresh_s`. It never reaches the VPS and writes nothing.

`bin/metatracker` opens it (desktop entry `metatracker.desktop`). Manual: chapter `93-metatracker`.

| file | what it does | run it | in → out |
|---|---|---|---|
| `chart.py` | The matplotlib canvas that draws the day's equity curve in MetaTracker's colours. | imported | curve → canvas |
| `curve.py` | The day's equity curve of one account: minute rows, the service's hourly extremes, the two floors. | imported | history → series |
| `eas.py` | The EAs an account should carry against the ones mounted and the magics that actually trade. | imported | sheet, charts, trades → rows |
| `equity.py` | One strategy's cumulative net result per account, from the closed trades of `history.trades()`; no Qt. | imported | trades → series |
| `floors.py` | One account's distance to its daily and total floors, from one beat and its stage's rules. | imported | beat + stage → distances |
| `fmt.py` | How a figure is written on MetaTracker's screens: the Spanish way, and «—» where there is none. | imported | — |
| `health.py` | The health of each terminal and of the VPS they run on, from the beats, the minute history and `vps.json`. | imported | minutes, vps.json → rows |
| `history.py` | What the collector keeps per account: every deal since it opened, the minute curve, the floating excursions. | imported | disk → frames |
| `launch.py` | Open MetaTracker, the window over the live MT5 fleet, or save a capture of it. | `python3 -m mt5.fleet.app.launch [--root DIR] [--tab NAME] [--account LOGIN] [--shot PNG] [--at EPOCH]` | beats → window, PNG |
| `progress.py` | How far an account is through its stage: profit against the target, the days counted on the firm's clock, the payout. | imported | deals + stage → reading |
| `read.py` | What MetaTracker reads from disk: the fleet's beats, each account's plan, the firms' clocks, the magics, the VPS, the reconciliation. | imported | disk → dicts |
| `risk.py` | What the open stops would cost: each position's loss at its SL and the equity if all of them hit. | imported | positions → loss |
| `rules.py` | The rules a funded stage forbids — holding over the weekend, trading around news — against the open positions. | imported | beat + stage → reasons |
| `state.py` | The fleet as rows: each account's beat, its floors and the light the window paints. | imported | beats → rows |
| `strategies.py` | Live strategies across the whole fleet: each magic's record, and whether the same magic entered together on every account. | imported | trades → rows |
| `tab_deploy.py` | The Despliegue tab: per account, the EAs the workbook expects against the charts that carry one, and the magics that trade. | imported | sheet, charts → table |
| `tab_fleet.py` | The Flota tab: totals, one row per account, and the chosen account's curve, reasons, progress, positions and deals. | imported | rows → widgets |
| `tab_health.py` | The Salud tab: each terminal's connection, ping, build and errors, and the VPS they share. | imported | beats, vps.json → tables |
| `tab_reconcile.py` | The Conciliación tab: the newest reconciled week — each live strategy against its SQX backtest, and the paired trades. | imported | result.json → tables |
| `tab_strategies.py` | The Estrategias tab: every live magic over all accounts, and the same magic's entries paired across accounts. | imported | histories → tables |
| `theme.py` | MetaTracker's own look: the palette, the lights' colours and the stylesheet. | imported | — |
| `widgets.py` | The Qt pieces every tab of MetaTracker is made of: cells, tables, cards, legends, scrolling pages. | imported | — |
| `window.py` | MetaTracker's window: the five tabs over the fleet, the refresh timer and the desktop notifications. | imported | rows → widgets |
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
