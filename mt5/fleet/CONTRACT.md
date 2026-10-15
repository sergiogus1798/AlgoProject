# Fleet v2 — the contract between FleetBeacon, the collector and MetaTracker

Owner decisions, 2026-10-03 (do not reopen): MetaTracker gets ideas 1-10 and 12; idea 11 (acting on
accounts: pause, close) is REFUSED — nothing here ever sends, modifies or closes an order. Phone
alerts (idea 3) are deferred to a «Por ahora» list; the closed-window desktop alert on a floor or on
silence is `guard.py` (owner, 2026-10-15; not news, not Friday close). The session that owns this work now
also owns `mt5/fleet/vps/FleetBeacon.mq5` and the collector. The service stays READ-ONLY.

Thresholds (owner): weekend — yellow 3 h before the symbol's Friday close, red 1 h before; news —
yellow 30 min before a release that moves an open position's symbol, red inside the firm's window
(FTMO 2 min, Hantec 3 min, from `mt5/newsfilter/firms.py`); red also when the open stops would break a
floor, or a position has no SL. Existing: silent > 300 s, red under 25 % of a floor's allowance.

## 1. FleetBeacon schema 2 (`Common\Files\fleet\`)

`<login>.json`, every 30 s, atomic (tmp + FileMove) as today. All schema-1 fields stay, `schema` = 2, plus:

| field | what |
|---|---|
| `service_started` | server epoch the service started |
| `positions[].tick_size` | `SYMBOL_TRADE_TICK_SIZE` |
| `positions[].tick_value_loss` | `SYMBOL_TRADE_TICK_VALUE_LOSS`, account currency per tick per lot |
| `positions[].friday_close` | server epoch of the end of the symbol's last trade session on the current or coming Friday (`SymbolInfoSessionTrade`, day FRIDAY, the last index); 0 if none |
| `hours[]` | the last 48 server hours the service saw: `{start, balance0, equity0, low, high}` — `start` the server epoch of the hour, `balance0`/`equity0` at the first sample in it, `low`/`high` the min/max equity sampled every loop pass (500 ms) in it. In memory only; restarts empty |
| `charts[]` | every chart with an EA: `{symbol, period, expert}` (`ChartFirst/ChartNext`, `CHART_EXPERT_NAME`; `period` as "M1".."MN1") |
| `news[]` | calendar values from 1 h ago to 24 h ahead, importance MODERATE or HIGH: `{time, event_id, code, currency, country, importance, name}` — `time` server epoch, `code` `MqlCalendarEvent.event_code`, `country` the ISO code of `MqlCalendarCountry.code`, `importance` 2 or 3. Refreshed every 5 min, not every beat |

`<login>.history.json`, rewritten only when `HistoryDealsTotal()` over the whole history changes (and at
start): `{schema: 2, login, written_gmt, server_time, deals: [...]}` — every deal since the account
opened, same fields as `deals_today`.

## 2. The collector — `mt5/fleet/collect.py` + `bin/fleet-collect.sh`, cron every minute

1. `scp` the VPS's `…\Terminal\Common\Files\fleet\*.json` into a temp folder, then move each into
   `AlgoData/fleet/live/` (atomic rename). `ssh vps` facts: `knowhow/locations/vps-fleet-access.md`.
2. Per `<login>.json`: append one row to `AlgoData/fleet/history/<login>/<server YYYY-MM-DD>.parquet`
   (rewrite the day's file; skip when `written_gmt` equals the last row's): `written_gmt, server_time,
   balance, equity, floating, margin, connected, autotrading, ping_us, n_positions`.
3. `AlgoData/fleet/history/<login>/excursions.json`: per position ticket ever seen `{magic, symbol,
   side, volume, time, min_profit, max_profit, last_seen}` — the floating MAE/MFE at the collector's
   1-minute resolution; a closed ticket is kept.
4. Every 5 minutes: `AlgoData/fleet/live/vps.json` — `{written_gmt, ram_total_mb, ram_free_mb,
   cpu_pct, disk_free_gb, uptime_h, terminals: [{install (origin.txt), pid, ram_mb, login (from the
   day's log, last "authorized" line, or null), errors: [last 10 log lines that carry an error]}]}`
   via one piped PowerShell script. Terminal logs are UTF-16LE.
5. Lock with `flock -n` (a slow run is skipped, never stacked). A VPS that does not answer is NOT an
   error: the files simply stop changing and MetaTracker reads the silence. Log one line per run to
   `AlgoData/logs/fleet-collect.log`, one line per failure.

## 3. MetaTracker (`mt5/fleet/app/`) — what each idea is

Every new figure reads schema 2 and shows «—» on a schema-1 beat. Times on screen are server clock.

1. **Si saltan los stops** — per position `loss_to_sl = (sl − price_current) · dir / tick_size ·
   tick_value_loss · volume` (dir +1 buy, −1 sell; may be positive when the SL is in profit). Account:
   `equity_at_stops = equity + Σ`. Red «Los stops romperían el suelo diario/total» when it is under a
   floor; red «Posición sin SL» when one has `sl == 0`. Column in the fleet table and per position.
2. **Reglas que prohíben** — only for a stage with `weekend_ok` / `news_ok` False (catalogue): weekend
   per position by `friday_close`; news by `news[]`, the firm's profile and symbol→currency match in
   `mt5/newsfilter/firms.py` / `windows.py` (reuse, do not restate; live there is no Forex Factory: say
   «sólo calendario MT5» for Hantec). Reasons listed under the account; worst one sets the light.
   FundingPips' prohibitions come from its manual catalogue: label «según catálogo».
4. **Progreso de fase** — from `<login>.history.json`, the stage starting at `deposit_time`: profit vs
   the stage target, trading days and profitable days (catalogue's `min_days`, `min_days_kind`,
   `profitable_pct`) counted on the firm's day (the clocks of `read.clocks()`), consistency if set; on
   a funded stage: last payout (a negative balance deal), next payout date (`payout_days`), payable
   now ≈ (balance − size) × reward share.
5. **EAs** — expected = the account's sheet of `AlgoData/fleet/Flota_de_cuentas.xlsx` (sheet name in
   `fleet.vps.accounts.<login>.excel`; absent → «sin hoja en el Excel»); mounted = `charts[]`; magics
   from positions and history; names from the reconciler's register. Flags: expected and not mounted,
   mounted and not expected, magic not in the register, a magic with no trade for more than
   `silent_strategy_days` (config, 30).
6. **Curva del día** — the chosen account's equity today from the history parquet (minute) with the
   `hours[]` low/high, the daily floor and the total floor as lines; matplotlib (`FigureCanvasQTAgg`).
   Also fixes the «≈» of a `max_be` floor: `hours[]` entry whose `start` is the firm's day start gives
   `equity0` (and `balance0`); the day's worst equity is the min of `low` since then.
7. **Estrategias en vivo** — per magic over all accounts: trades, net, win rate, worst MAE
   (excursions), first trade.
8. **Misma estrategia, varias cuentas** — a magic on ≥ 2 accounts: its entries of the last 7 days
   paired across accounts by side and open time ± 5 min; the unpaired listed.
9. **Salud** — per terminal: connected, ping, build, disconnections today (history rows with
   `connected` 0), service uptime, last errors; the VPS's RAM, CPU, disk, uptime (`vps.json`).
10. **Totales** — strip above the fleet table: accounts, capital (Σ size), equity, floating, payable.
12. **Pestañas** — Flota (table + totals + chosen account's detail: curve, reasons, positions with
    their stop risk, today's deals, progress) · Estrategias (7, 8) · Despliegue (5) · Salud (9) ·
    Conciliación (the newest `AlgoData/mt5/reconcile/<week>/result.json`: summary per strategy and
    pairs; none yet → say so).

House rules: `CODESTYLE.md` (500 lines per file, README table, docstrings and type hints, no defensive
code except at the window's boundary), Spanish on screen, English in code. Own theme (`theme.py`),
never `ui/`'s.
