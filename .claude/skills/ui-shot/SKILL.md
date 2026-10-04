---
name: ui-shot
description: See a change to the desktop window (ui/) before saying it is done — shoot the zone offscreen on a scratch daemon, look at the PNG, have the uiCritic agent critique it, walk every zone for exceptions — and the checklist for a new zone or view. Use after editing anything under ui/, when the owner gives feedback on how the window looks, asks for a critique of a zone, or asks for a new view, zone or panel.
---

# /ui-shot

Never report a window change from the code alone, and never write a `shot.py`: the launcher shoots.

## Shoot and look

```bash
S=<session scratchpad>/shots
QT_QPA_PLATFORM=offscreen bin/algoui --port 8757 --shot $S --zone <Zona>
```

`--port 8757` is a scratch daemon, so the owner's open window (8765, `ui_port`) is untouched and
runs the new code. `Read` the PNG and check what the owner asked for, against his standing
preferences: big readable text, high contrast, tables as small as their content, terminal style.
The window opens at 1440×900; the owner's screen is 2560×1440, so a layout question (what sits
beside what, empty width) is shot with `--size 2560x1400` too.
What cannot be seen in the shot (a click, a drawer) is said as not verified, not assumed.

## Critique it — an eye that did not write it

After a change the owner asked for by looking at the window, a new zone or view, or when he asks
for a critique of a zone («critica Activos»): shoot at `--size 2560x1400` and hand the PNG to the
`uiCritic` agent (`.claude/agents/uiCritic.md`, Sonnet, read-only) — one agent per zone, with the
PNG path, what the zone is for, what the owner asked, and the zone's source files. It returns at
most five issues, P0-P3, each with a concrete fix. Fix every P0 and P1 and shoot again; list the
P2 and P3 to the owner instead of fixing them unasked. Skip it for a change with nothing to look
at (a daemon fix, a tooltip's text). A session started before the agent file existed runs it as a
`general-purpose` subagent, `model: "sonnet"`, told to read that file and follow it.

## Walk every zone

```bash
python3 -m ui.daemon.serve --port 8757 &          # only if no scratch daemon is up
QT_QPA_PLATFORM=offscreen python3 tools/uiwalk.py --port 8757   # 0 exceptions expected
```

Kill the scratch daemon by PID when done. Then `python3 tools/depmap.py && python3 tools/checks.py`.

## A new zone or view

Stop first if the request admits two readings — where it goes in the sidebar, what it shows when
empty, which button launches SQX (rule 11; an SQX-launching button needs the owner's word, rule 3).

1. Read `ui/README.md` (the zones and the owner's six decisions) and the folder's own `README.md`.
2. Daemon: a package under `ui/daemon/<zone>/` with a router; **one line appended at the end** of
   `ROUTERS` in `ui/daemon/routers.py`. A study returns data, the window paints it — no HTML.
3. Desktop: a package under `ui/desktop/` — a `QFrame` named `term`, colours from `theme.T`, no
   second theme; its entry in `ui/desktop/nav.py`, the command palette and `shell.py`.
4. Shoot and walk as above; the shot becomes the chapter's screenshot (`/manual-chapter`, family
   `02-la-ventana`), and each new file gets its row in its folder's `README.md`.
