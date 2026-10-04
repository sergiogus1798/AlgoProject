---
q: What is `Signal '<login>': failed get list of signals` in an MT5 terminal's log, and is it a fault?
kw: failed get list of signals, Signal 541350656, QR 2 Signal fail, MetaTracker Salud último error FTMO, terminal log error every half hour, MT5 Signals copy trading service, probe.ps1 error|failed|cannot
tag: 📓  date: 2026-10-04  see: mt5/fleet-beat-daily-floor-needs-more-than-one-beat
---
# `failed get list of signals` is MT5's Signals service finding none on a prop firm's server — noise

MT5's built-in Signals (copy trading) asks the trade server for its signal list about every half hour; FTMO's server offers none, so the terminal logs the line under source `Signal`. It touches no EA, order or connection. `mt5/fleet/vps/probe.ps1` collects any log line matching `error|failed|cannot`, so it filled MetaTracker's Salud as «Último error»; `mt5.fleet.app.health.NOISE` drops it on the app side (the probe on the VPS is unchanged). To silence it at the source: terminal → Tools → Options → Community/Signals off — optional.

## Evidence
- 📓 2026-10-04, `vps.json`, FTMO terminal 541350656: four lines `QR 2 00:12:37.011 Signal '541350656': failed get list of signals` at 00:12, 00:30, 01:00, 01:07; the Hantec and Darwinex terminals on the same VPS logged none.
- 🤔 The cause (the server publishes no signals) is inferred from the source column and the firm, not confirmed with FTMO.
- `tests/test_fleet_progress.py` `check_health`: a `Signal` line is dropped, an order error is kept.
