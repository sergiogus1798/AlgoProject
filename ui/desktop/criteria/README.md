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
| `__init__.py` | The package's one-line purpose | imported | — |
| `zone.py` | Under a step's rules, «Disponibles, sin umbral todavía»: the step's `offered` facts as rows with «—» for a threshold — shown, judging nothing. `CriteriaZone`: reads `/api/criteria` on first show; the banners (frozen since when, and whether the file changed by hand after; `dev.on` — a random sample of survivors is being kept); a section per step; opens the dialog and posts what it built; «Congelar» after a confirmation. Frozen, or a step without `cut`: «Añadir criterio» is off with the reason in its «?» | imported | daemon → zone |
| `parts.py` | The zone's sentences (what pass, limbo and fail are, what `cut` is, the column tooltips), `mark` (a «?» beside something that is not a button), `table` (read only, as tall as its rows, a long cell cut with «…» and whole in its tooltip) and `cells` (one rule as its five cells) | imported | rows → widgets |
| `overrides.py` | `by` ⇄ rows (pure, `by_rows`/`by_built`) and the row's widgets | imported | `by` → rows → `by` |
| `dialog.py` | `RuleDialog`: type (Métrica SQX, Test de la app, Veredicto, Compuesto), the fact picker (the step's menu, a key may be typed), threshold (comparator + number, optional limbo band) or «cerca de la mediana» (±%), «Si no cumple» (Fallo, or Limbo = never eliminates), a verdict (Aprobado/Suspenso), a compound built one level deep (each condition through the same dialog, `nested`); a simple rule's `by` (per-timeframe/asset overrides) is edited as rows, a compound's is carried through untouched; «Borrar» | imported | a rule → a rule |
