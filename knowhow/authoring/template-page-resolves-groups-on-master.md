---
q: template page says "atado a un grupo que esta instalación no tiene", unknown_group true, red hole in Plantillas, group installed only on the workers, holes.shape reads the master's blockGroups.xml, which install resolves a template's groups
tag: 🔬  date: 2026-09-28  see: authoring/holes-groups-randomcondition
---
# The template page resolves a hole's group against the MASTER's `blockGroups.xml`, not the workers'
`sqx/templates/holes.py:shape(path, install=MASTER)` reads the master's block groups by default, and
`ui/daemon` calls it with that default. A group installed only on the workers (where every build
runs) shows in Plantillas as «atado a un grupo que esta instalación no tiene» with `unknown_group:
True`, although the build works. Read the red as «the master lacks it», not «no install has it».
Verified 2026-09-28 on `keltnerUpperCrossUpSignal`: unknown on the master, resolved on SQX_w1 and SQX_w2.

## Evidence
- `sqx/templates/holes.py:38` signature default `install: Path = MASTER`.
- F14 of plan 24 (2026-09-28): same hole read against the conductor and the custodian gives «atado a
  keltnerUpperCrossUpSignal»; against the master, `unknown_group: True`. Chapter 35 explains it next
  to the screenshot `ui-plantilla.png`.
- Open decision (OPEN.md §81): resolve against the install that builds, or against all three.
