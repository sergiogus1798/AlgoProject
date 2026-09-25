---
q: install custom block group template without GUI; customBlocks.xml blockGroups.xml edit safely; sqcli rewrites customBlocks; headless authoring chain; custom block in signal XML; build output databank empty Auto-sync never
tag: 🔬  date: 2026-09-23  see: authoring/project-skill, authoring/block-vocabulary, databanks/autosync-nothing-on-disk
---
# Blocks, groups and templates install by writing a file into a stopped install — no GUI import
`user/settings/customBlocks.xml`, `user/settings/blockGroups.xml`, `user/settings/StrategyTemplates/<set>/<name>.sqx`.
`sqcli` never rewrites the first two (unlike `project.cfx`); the GUI does. Protocol: stop, edit, start, verify.
Install on EVERY install that builds (`vocabulary --diff` first). Build with `type="template"`, `action=start`, `stop` before each re-start.
Build output databank may be `Auto-sync never` → force a write with `-databank action=synctofiles project=… name=…`.

## Evidence
Chain on custodian, pilot template `keltnerUpperCrossUp`:
| step | how | result |
|---|---|---|
| author block | `<Item key="CBlock_…">` XML | — |
| install | `python3 -m sqx.blocks.install <xml> --role conductor` | 171 → 173 blocks |
| install on build install | same, `--role custodian` | `vocabulary --diff` caught W2 lacked it |
| emit template | `python3 -m sqx.templates.build …` | transplant into `market_long_skeleton` |
| install template | copy into `StrategyTemplates/<set>/` | — |
| build | `-project action=start`, single-task project | 30 strategies in 29 s |
- 🔬 On `SQX_w1` both XMLs stamped 2026-07-04 across months of headless starts, while `settings.xml`,
  `wizard.txt`, `snippets.txt` carry today's date. GUI saves leave dated copies in `customBlocks-backups/`.
  Concurrent write with an instance up: not measured.
- 🔬 SQX reads an externally written `customBlocks.xml`: builder generated 13,639 strategies from a
  template referencing a Python-written block.
- 🔬 In a signal, a custom block = its store entry minus `<Contents>`, every `<Param>` valued, plus
  `categoryType="Custom blocks"`; definition stays in `customBlocks.xml`.
- 🔬 30/30 built strategies carry the fixed block, random partners vary (`CSSAMarketRegimeAboveLevel` ×15,
  `VWAP` ×5, `BollingerBands` ×5, `HighD`, `UlcerIndex`…). Only difference from issue 9: `StrategyType type=`.
- XAUUSD donor build databank is `Auto-sync never` → directory empty after a build. Alternative:
  set `Auto-sync every 1 hour` in `project.cfx` with the install stopped, rebuild, stop (shutdown sync writes).
  Full `-databank` verb list: `internal/web/SQUANT/help.txt`.
