---
q: Why can a schema-1 FleetBeacon beat not give a live account's daily floor exactly?
kw: MetaTracker daily floor approximate ≈; FleetBeacon deals_today server midnight vs FTMO Prague day; live daily loss floor max(balance, equity) at midnight; equity at day start from one beat; fleet history
tag: 📓  date: 2026-10-02  see: locations/vps-fleet-access, mt5/mt5-verify-clock-zones
---
# A schema-1 beacon beat cannot always give a live account's daily floor: two gaps, both marked «≈»; schema 2's `hours[]` closes both
1. `deals_today` is cut at the **server's** midnight; FTMO's day is Prague's, 01:00 server time:
   between 00:00 and 01:00 yesterday's deals are missing (after 01:00, filter them by time).
2. A `max_be` floor (Hantec; FundingPips by `catalog.plan`'s default) starts from max(balance,
   equity) at midnight, which a beat lacks: exact only with no position carried over midnight.
Schema 2's `hours[]` (balance and equity at each server hour's first sample) is exact once the
service has run through the firm's day start. Times are server epochs; offset = `server_time − written_gmt`.

## Evidence
- 📓 2026-10-02, the three live beats in `AlgoData/fleet/live/`: `server_time − written_gmt` = 10800,
  `day_start` = the server's 00:00; FTMO's rule `daily_loss_basis` reads «balance at midnight CE(S)T».
- `mt5/fleet/app/floors.py` (`reading`, its `approx` list), `tests/test_fleet_floors.py`.
