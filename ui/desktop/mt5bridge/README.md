# ui/desktop/mt5bridge — the MT5 BRIDGE section of the window

The sidebar's fifth group (owner, 2026-09-29: the same window, a new section called MT5 Bridge).
Today one zone, «Verificar»: step 26 for one strategy.

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | MT5 BRIDGE: the window's zones over MetaTrader 5 — today «Verificar», step 26. | imported | — |
| `forceclose.py` | The button for a wedged-open MT5 terminal: close it well if possible, kill it if not. | imported | click → daemon call, status text |
| `render.py` | Drawing helpers for Verificar: the firm's light widget, the past-runs table, result filtering. | imported | result + active firms → the result to draw |
| `zone.py` | MT5 BRIDGE › Verificar: one strategy in SQX at each prop firm's conditions against its MT5 backtest. | imported by `shell.py` | daemon → form, list, result |
