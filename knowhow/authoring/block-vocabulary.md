---
q: where is the AlgoWizard block catalogue config.xml; how many blocks; customBlocks.xml owner's blocks; ctemplate config.xml confusion; catalog.json value atoms
tag: 🔬  date: 2026-09-22  see: authoring/builder-block-switches, authoring/holes-groups-randomcondition
---
# The native block catalogue is `internal/web/SQWIZARD/branding/global/config.xml`; own blocks in `customBlocks.xml`
Native: 849 built-ins (Comparisons 23 · Conditions 500 in 63 categories · Actions 23 · Values 303 in 8
categories, 190 indicators). Own: `user/settings/customBlocks.xml`, 171 `<Item>`. Total 1,020.
`key` is what templates/groups reference; `display` is the written form with `#Param#` holes.
Not `internal/ctemplate/config.xml` (18 KB) — the editor's `<UsedBlocks>` shortlist (~14 keys).

## Evidence
- Native file 1.19 MB; one `<Blocks>` with four sections of `<Category>` of `<Item key= name= display= returnType=>`.
- `customBlocks.xml` 1.3 MB, flat, each Item with `category`, `type`, `oppositeBlockKey`; backups in
  `customBlocks-backups/`; same pattern for `blockGroups.xml`.
- `tools/sqx-lab/.../sqx-custom-block/catalog.json`: derived index of value atoms only (235 = 178 native + 57 own); regenerate, never hand-edit.
