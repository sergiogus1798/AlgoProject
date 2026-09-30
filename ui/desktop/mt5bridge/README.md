# ui/desktop/mt5bridge — the MT5 BRIDGE section of the window

The sidebar's fifth group (owner, 2026-09-29: the same window, a new section called MT5 Bridge).
Today one zone, «Verificar»: step 26 for one strategy.

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | The package's one-line purpose | imported | — |
| `zone.py` | `VerifyZone`: the form (the strategy chosen in Proyecto, an archived one, or one from the BanquilloEstrategias pool; Desde/Hasta pre-filled from `/api/mt5bridge/dates` and editable; the tester's model; the firms' lights), «▶ Verificar en SQX y en MT5» as a `JobButton` confirmed by `/api/mt5bridge/preflight`, the list of past checks and the chosen one's result in `blocks.result.ResultView`, filtered by the active firms | imported by `shell.py` | daemon → form, list, result |
| `render.py` | `FirmLight` (the square-with-a-light firm toggle, spelled `FTMO`/`Hantec`), the past-runs table's header and rows, and `filtered()` — the pure function that drops an inactive firm's chart series, verdict, unpaired-trades table and parameter column from a loaded result before it is drawn | imported | result + active firms → the result to draw |
