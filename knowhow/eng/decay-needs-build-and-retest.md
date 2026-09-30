---
q: Decaimiento IS OOS sharpe_is empty retention empty; decay study one databank; workflow IS and OOS in two databanks; --is-databank; built_from OOS input Results
tag: 🔬  date: 2026-09-30  see: sqx-drive/study-cli-defaults-to-master
---
# Decay needs the build and its retest: in a workflow no single databank holds IS and OOS
`studies.screening.decay.report` splits one daily curve at `--split`. A workflow project keeps the
build (`Results`, IS only) and its retest (`OOS`, OOS only) apart, so on `OOS` every `sharpe_is`
and `retention` came out empty and 207 of 296 strategies were «DESCARTAR» on a half-read. With
`--is-databank Results` it glues the build's daily P&L before the split to the retest's after,
paired by name; `ui.daemon.loader.find.built_from` (the `OOS` task's input) makes the window pass it.

## Evidence
- 🔬 2026-09-30, `Test_USDJPY_donchianUpperCrossUp_H1/OOS` (60 after the step-8 cut): before, 0 of
  296 `sharpe_is`; after, 60 of 60 — e.g. `Strategy 1.26.46` Sharpe IS 0.435, OOS 0.686, t 1.41, DUDOSA.
