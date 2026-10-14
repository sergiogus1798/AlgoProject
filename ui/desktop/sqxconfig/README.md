# ui/desktop/sqxconfig — Configuración SQX

The zone of encargo 22 §8.2 (plan 24 F9), in BIBLIOTECA: every SQX setting a new project is built
and tested with, one foldable section per test, a dropdown wherever the values are fixed. `SqxConfigZone` is wired into the sidebar in `shell.py`; `python3 -m ui.desktop.sqxconfig.preview` is a
standalone viewer that opens it alone over the running daemon.

```
SqxConfigZone (zone) ── index of sections │ scroll of Section (section) ── one Field (field) per value
      └ status line: what the last write did, or why the daemon refused it
```

**Imports from:** `ui.desktop.client`, `glossary`, `numbers`, `theme` · **Consumed by:** `shell.py` (F2)

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Configuración SQX: the zone that shows and edits the settings new SQX projects are built with. | imported | — |
| `field.py` | One value of the SQX settings as an editor: a dropdown where the values are fixed, a box otherwise. | imported | value → write |
| `preview.py` | The Configuración SQX zone alone in a window, over the running daemon — until the sidebar carries it. | `python3 -m ui.desktop.sqxconfig.preview [--shot DIR]` | daemon → window · PNGs |
| `section.py` | One test or topic of the SQX settings: a header that folds, the file's own words, one row per value. | imported | section → rows |
| `zone.py` | Configuración SQX: every setting a new project is built and tested with, one section per test. | imported | daemon → zone |
