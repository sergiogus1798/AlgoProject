---
q: oos2 reserved_for refused, PermissionError el paso no puede mirar oos2, step 20 blind sealed, sellado, puerta ciega, no quemar el oos2, ALGO_AUTONOMOUS, enforced, human may read oos2, window hides wfc cscv wfm, OOS2 reservado ficha, configure --segment oos2 refused, cloud cuts oos2
tag: 🔬  date: 2026-09-28  see: eng/blind-steps-write-no-ledger-rows, research/cscv-always-reads-oos2
---
# The oos2 reservation and the step-20 blind door bind only an autonomous agent
Owner, 2026-09-28: a human (window, terminal, or a session he steers) may read any segment and
any of 17/18/19 at any time. `core.assetdata.enforced()` is True only with `ALGO_AUTONOMOUS=1`,
set by nothing today; whether an autonomous agent should stay held is open. Every oos2 check asks
that one function — `ledger.gate`, the window's seals, `sqx.projects` segment refusals, the
cloud's cut. The ledger still records every look: the deflated Sharpe needs the count.

## Evidence
- 🔬 `tests/test_ledger.py`, `test_wfc.py`, `test_blindjoint.py`, `test_ui_batch.py`,
  `test_ui_workflow.py`: without the variable step 8 reads oos2 and the rail shows 17-19 unsealed;
  with `ALGO_AUTONOMOUS=1` every old refusal still fires.
- 🔬 `/api/tearsheet … sample=OOS2` on `Test_USDJPY_donchianUpperCrossUp_M30` answers «OOS2
  abierto, sin export» instead of «reservado: se abre tras los pasos 17, 18 y 19».
- ⚠️ A new check on oos2 must call `core.assetdata.enforced()`, not read `reserved_for` bare.
