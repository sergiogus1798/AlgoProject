# ui/desktop/sqxconfig — Configuración SQX

The zone of encargo 22 §8.2 (plan 24 F9), in BIBLIOTECA: every SQX setting a new project is built
and tested with, one foldable section per test, a dropdown wherever the values are fixed. F2 wires
`SqxConfigZone` into the sidebar; until then `python3 -m ui.desktop.sqxconfig.preview` opens it
alone over the running daemon.

```
SqxConfigZone (zone) ── index of sections │ scroll of Section (section) ── one Field (field) per value
      └ status line: what the last write did, or why the daemon refused it
```

**Imports from:** `ui.desktop.client`, `glossary`, `numbers`, `theme` · **Consumed by:** `shell.py` (F2)

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | The package's one-line purpose | imported | — |
| `zone.py` | `SqxConfigZone`: the warning «se aplica a los proyectos que se creen a partir de ahora», the index, the sections grouped by file; reads `/api/sqxconfig` on first show | imported | daemon → zone |
| `section.py` | One section: folded header, the file's comment (long ones behind «seguir leyendo»), sub-headings where the path deepens (a list item named by its `title`), one row per value | imported | section → rows |
| `field.py` | One editor: a dropdown for a fixed value, one dropdown per item plus + and − for an ordered list, a box for a number or a text, a dim line for a locked value; posts to `/api/sqxconfig/value` | imported | value → write |
| `preview.py` | The zone alone in a window; `--shot DIR` saves four PNGs (folded, CrossTF, MC Retest, WFM) | `python3 -m ui.desktop.sqxconfig.preview [--shot DIR]` | daemon → window · PNGs |
