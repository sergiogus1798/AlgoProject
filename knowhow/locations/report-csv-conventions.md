---
q: report CSV strategy column; verdict tier column values MANTENER DESCARTAR; how ui finds a module's verdict; report folder per project; gate report date vs harvest date; source.harvest manifest
tag: 🔬  date: 2026-09-25  see: locations/where-things-live
---
# Report CSVs name the strategy in `strategy` and the verdict in `verdict`; pair gate↔harvest by manifest
A new per-strategy report joins the window by writing a `strategy` column (verdict in `verdict`, or `tier` for Monte Carlo).
Report folders are per project, not per databank. A gate report is dated the day it ran:
`reports/<project>/<databank>/<today>/gate/`; its harvest is `source.harvest` in the manifest — never pair by folder date.

## Evidence
- Checked every CSV under `reports/`: `gate`, `curate`, `crossmarket`, `retest`, `montecarlo`, `nulls`,
  `exposure`, `wfc`, `wfm` write `strategy`. Exceptions: SQX exports copied by `curate` (`Strategy Name`), `decay.csv` (`name`).
- Verdict words: `MANTENER · DESCARTAR · DUDOSA · NO EVALUABLE · FAIL · MARGINAL · worth_it · not_worth_it`.
  `ui/desktop/theme.state_colour` names any word outside the list instead of hiding it. `ui/daemon/studies.py` relies on the column.
- A strategy built in `Results` is judged under `OOS`, `SPP_IS` or `MC_Trades`.
- `reports/P/D/2026-09-25/gate` can judge `harvest/P/D/2026-09-24`; a harvest judged twice has two report
  folders. `ui/daemon/gateview.judged` pairs by manifest (absolute harvest path), keeps the newest.
