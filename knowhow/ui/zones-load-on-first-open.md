---
q: Why did the window take 8 s to open, and where does a zone's first read happen now?
kw: slow start, arranque lento, time to window, Shell.refresh, reloads, stale, Activos 5 s, lazy zones, Recargar
tag: 🔬  date: 2026-10-04  see: offscreen-walk-catches-three-ways
---
# The window reads a zone the first time it is opened, not before it shows
`Shell.__init__` used to call every zone's `reload` on the GUI thread before `show()`: 6.4 s of the
8.7 s to a window, 5.0 of them Activos alone (27 asset pages built at once, each with its own GET)
and 1.0 Paletas. Now `Shell.stale` holds the zones not yet read, `open_zone` reads one on its first
opening, and «Recargar» re-reads the open zone and marks the rest. Cold start: 8.7 s → 2.9 s.
Code that needs another zone's data must go through `open_zone` first (as `open_template` and
`open_library` do) — never assume `shell.palettes.data` or `shell.catalogue.data` is filled. The
gallery is the one eager read: Ctrl+K lists its projects, and it loads off the GUI thread.

## Evidence
Offscreen, scratch daemon started by the window, 2026-10-04 (two runs each):
before — desktop imports 0.44 s, daemon up 1.43 s, `Shell()` 6.67 s (Activos 5.04, Paletas 1.07,
Verificar 0.16, Cobertura 0.06, Plantillas 0.05), first paint 0.17 s, total 8.71 s;
after — 0.44 + 1.42 + 0.66 + 0.35 = 2.88 s. The cost of Activos did not go away: it is paid on its
first opening (`cProfile`: 27 × `assets.AssetPage.__init__`, 2.8 s in 28 GETs, 1.6 s in widgets) —
building an asset's page when it is selected would remove it. The daemon's import is 1.24 s
(`python3 -X importtime -c "import ui.daemon.app"`): fastapi 0.27, pandas 0.28, scipy.stats 0.33
through `core.significance`; nothing there buys a second, so it was left alone.
