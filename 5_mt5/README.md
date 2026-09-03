# 5_mt5 — reserved

Deployment to MetaTrader 5 is a phase of this project, deliberately not built yet. The folder exists
so adding it later does not force a reorganisation.

When it starts, it covers: exporting a strategy as an EA, tracking live results, and comparing live
against backtest for the same strategy and period. The comparison is the point — everything upstream
is an estimate until a live curve disagrees with it.

No MetaTrader install was found on this machine, so the live side will need its own configuration in
`config/machine.yaml` when the time comes.
