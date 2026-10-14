# ui/desktop/criteria — the «Criterios» zone

PROYECTO › Criterios (owner, 2026-10-03, feedback §13): what a strategy has to meet at each
workflow step to go on by itself, seen and edited. It paints what `ui/daemon/criteria/` reads from
`pipeline/autopilot/criteria.yaml` and `assets/_study.yaml`; it launches nothing.

```
CriteriaZone (zone) ── «Congelar» · frozen and dev banners · status line
   └ scroll: Paso 6 (read only) · one section per step: «Corta: <databank>», its table of rules
     or «Sin criterios: pasan todas», «Añadir criterio» · Historial de cambios
        └ double click on a rule / «Añadir criterio» ─▶ RuleDialog (dialog) ─▶ POST /api/criteria/rule
```

**Imports from:** `ui.desktop.client`, `theme` · **Consumed by:** `shell.py`, `nav.py`

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | The Criterios zone: every step's pass criteria seen and edited. | imported | — |
| `dialog.py` | The dialog that adds or changes one criterion: a number, a verdict or a compound of them. | imported | a rule → a rule |
| `overrides.py` | A rule's per-timeframe / per-asset overrides (`by`) as editable rows and back, and the dialog's help texts and one-line wording. | imported | `by` → rows → `by` |
| `parts.py` | What the Criterios zone is made of: its sentences, the «?» mark and the table of rules. | imported | rows → widgets |
| `zone.py` | Criterios: what a strategy has to meet at each workflow step to go on, seen and edited. | imported | daemon → zone |
