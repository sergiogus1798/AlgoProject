# mt5/fleet — the live MT5 fleet on the VPS: the beacon, the collector, MetaTracker

Field list of everything below: `CONTRACT.md` (FleetBeacon schema 2, the collector, what MetaTracker shows).
The beacon is read-only: it sends, modifies and closes nothing. The VPS is reached with `ssh vps`
(`knowhow/locations/vps-fleet-access.md`).

| file | what it does | run it | in → out |
|---|---|---|---|
| `collect.py` | Pull the VPS's FleetBeacon files and keep the fleet's live copy, minute history, excursions and health. | `python3 -m mt5.fleet.collect` (cron: `bin/fleet-collect.sh`, every minute) | VPS → `AlgoData/fleet/` |
| `remote.py` | The two calls to the VPS over `ssh vps`: pull the beacon's files, run the health probe. | imported | VPS → files, dict |
| `rows.py` | The collector's pure parts: a beat's history row, the skip test, and the floating MAE/MFE ledger. | imported | beat → row |
| `vps/FleetBeacon.mq5` | MQL5 service in each VPS terminal: every 30 s `<login>.json` (schema 2: positions with tick size and value and Friday close, 48 server hours of equity low/high, charts with an EA, MODERATE/HIGH calendar news), and `<login>.history.json` when the deal count changes | compile with `mt5/metaeditor.py`; the owner starts it in each terminal | terminal → `Common\Files\fleet\` |
| `vps/probe.ps1` | The VPS's RAM, CPU, disk, uptime and, per running terminal, its process and last log lines, as one JSON | piped by `remote.py` | VPS → JSON |
| `app/` | MetaTracker, the window over all of this | `bin/metatracker` | `AlgoData/fleet/` → window |

The collector writes, under `AlgoData/fleet/` (`core/fleetpaths.py`): `live/<login>.json` and
`live/<login>.history.json` (literal copies), `live/vps.json`, `history/<login>/<server day>.parquet`
(`written_gmt, server_time, balance, equity, floating, margin, connected, autotrading, ping_us,
n_positions`) and `history/<login>/excursions.json` (per ticket, floating min and max profit at one-minute
resolution). Log: `AlgoData/logs/fleet-collect.log`. It works on schema-1 beats too; a VPS that does not
answer leaves the files unchanged. Manual: chapter `94-flota-colector`.
