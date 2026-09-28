---
q: template family for the ledger, --family, template stem, registry.csv template column, template.sqx stem is "template", which study id does a project sign, family of a project with no template
tag: 🔬  date: 2026-09-27  see: eng/blind-steps-write-no-ledger-rows
---
# A project's template family is its library folder's name, not the `.sqx` file's stem
Every library template is `AlgoData/templates/library/<name>/template.sqx`, so `Path(row["template"]).stem`
is `template` for all of them. The family (the third part of a ledger study id, owner Q9 of plan 24)
is `<name>`: `ui/daemon/runner/where.family(project)` reads the newest `projects/registry.csv` row
that names a template and returns its folder; no template → None, and the window refuses to run a
study that signs the ledger. Step 20's door — the rail's and blindJoint's — reads only that study;
looks signed with the project as family (E1's tests) live in another study and never open it.

## Evidence
- `registry.csv`, 2026-09-27: all 4 rows with a template point at `…/library/donchianUpperCrossUp/template.sqx`;
  `ls library/*/` → 5 folders, 5 `template.sqx`, no other `.sqx`.
- The rail printed «Plantilla template» for `Test_USDJPY_donchianUpperCrossUp_M30` until
  `ui/daemon/workflow/sources.template` took the folder (2026-09-27).
- The same project's steps 17-18 rows sit in `USDJPY_M30_Test_USDJPY_donchianUpperCrossUp_M30`
  (family = project, E1's run), the template's in `USDJPY_M30_donchianUpperCrossUp`; since
  2026-09-27 `ledgerview.door` asks the gate over the latter only → «faltan [17, 18, 19] (en el estudio …)».
