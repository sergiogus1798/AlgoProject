#!/usr/bin/env python3
"""Inventory every actionable widget of one zone of the window, drive each one, and say what happened.

Dev-only, the count behind «I touched everything». `uiwalk` moves combos, tabs and tables of every
zone; this takes ONE zone and, by introspection, lists every button (checkboxes and «?» marks
included), every item of every combo, every tab, every text or spin input and every item view
(rows, header clicks, cell clicks, checkbox cells) — per module of the zone's rail when it has one
(`zone.rail`, `zone.stack`) — then drives each and records `ok`, `excepción` (a Python exception,
a Qt warning, an HTTP 4xx/5xx, a traceback in the daemon's log, or an error painted on screen),
`negativa esperada` (the refusal's text) or `no ejercido` (why). The inventory is taken again after
every action, so what a tab, a selection or a job adds is driven too; a window an action opens is
swept and closed, a navigation undone. Modal dialogs answer `ANSWER`: «No» unless a caller says so.

Read-only by default (every POST refused, as in `uiwalk`); `--write` runs each «Calcular» for real, test root only.

    QT_QPA_PLATFORM=offscreen ALGO_DATA_ROOT=<test root> python3 tools/uiinventory.py --port 8771 \
        --zone Portfolios [--write] [--shots DIR] [--out FILE.md] [--daemon-log FILE]
"""

import argparse
import json
import re
import sys
import time
import traceback
from collections import Counter
from pathlib import Path

import uiwalk
from uiwalk import ERRORS, HERE, settle

import httpx  # noqa: E402 — uiwalk sets the Qt platform and the path first
from PySide6.QtCore import QtMsgType, qInstallMessageHandler  # noqa: E402
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QInputDialog, QLabel,  # noqa: E402
                               QMessageBox, QWidget)
from shiboken6 import isValid  # noqa: E402

from ui.desktop import background, client  # noqa: E402
from uiparts import Item, inventory, plain  # noqa: E402

JOB_S = 1800      # seconds a job a button queued may take
OK, BAD, REFUSED, SKIPPED = "ok", "excepción", "negativa esperada", "no ejercido"
REFUSAL = re.compile(r"No se (lanza|ha lanzado|declara)|no se envía|Marca al menos|solo se admiten")
PAINTED = re.compile(r"Traceback|\b[A-Za-z]+(Error|Exception)\b|No se pudo|El demonio no respondió|Falló \(código")
NOISE = ("propagateSizeHints", "QFontDatabase", "does not support", "Populating font")
ANSWER = {"yes": False, "text": ""}      # what a modal gets: QMessageBox Yes/No, QInputDialog's text
RESULTS: list[dict] = []                 # one row per item: ctx, what, result, detail
FOUND: dict[tuple, str] = {}
DONE: set[tuple] = set()
STATE = {"app": None, "shots": None, "log": None, "at": 0, "n": 0, "dialogs": [], "shot": set()}


def idle(limit: float = uiwalk.WAIT_S) -> None:
    """Pump events until no daemon call is out and its answer has painted."""
    settle(STATE["app"], 0.06)
    end = time.monotonic() + limit
    while background.POOL.activeThreadCount() and time.monotonic() < end:
        settle(STATE["app"], 0.06)
    settle(STATE["app"], 0.12)


def texts(root: QWidget) -> set[str]:
    """What the visible labels under a widget say."""
    return {plain(x.text()) for x in root.findChildren(QLabel) if isValid(x) and x.isVisible() and x.text()}


def shoot(root: QWidget, name: str) -> None:
    """Save what is on screen, numbered in the order it was seen."""
    if STATE["shots"]:
        STATE["n"] += 1
        root.grab().save(str(STATE["shots"] / f"{STATE['n']:03d}_{re.sub(r'[^A-Za-z0-9áéíóúñÁÉÍÓÚ]+', '_', name)[:90]}.png"))


def daemon_log() -> None:
    """Record a traceback the daemon wrote since the last look."""
    if STATE["log"] and STATE["log"].exists():
        new = STATE["log"].read_text(encoding="utf-8", errors="replace")[STATE["at"]:]
        STATE["at"] += len(new)
        if "Traceback" in new or " 500 " in new:
            ERRORS.append((HERE["zone"], "registro del demonio:\n" + new[-1500:]))


def drive(zone: QWidget, ctx: str, it: Item) -> dict:
    """Do one action and classify what followed."""
    errors, before, dialogs = len(ERRORS), texts(zone), len(STATE["dialogs"])
    tops = {t for t in QApplication.topLevelWidgets() if t.isVisible()}
    if it.skip:
        return {"ctx": ctx, "what": it.what, "result": SKIPPED, "detail": it.skip}
    try:
        it.act()
    except Exception as e:  # noqa: BLE001 — every exception is the report's content
        ERRORS.append((ctx, "".join(traceback.format_exception(e))))
    idle()
    if it.undo:
        it.undo()
    end = time.monotonic() + JOB_S
    while isValid(it.widget) and isinstance(it.widget, QAbstractButton) and not it.widget.isEnabled() \
            and time.monotonic() < end:
        settle(STATE["app"], 1)         # a job the button queued: it is enabled again when the job ends
    idle()
    said = texts(zone) - before if isValid(zone) else set()
    for top in [t for t in QApplication.topLevelWidgets() if t.isVisible() and t not in tops]:
        idle()
        said |= texts(top) | {f"abre «{top.windowTitle()}»"}
        if (ctx, type(top)) not in STATE["shot"]:        # one picture per kind of window and module
            STATE["shot"].add((ctx, type(top)))
            shoot(top, f"{ctx}_{it.what}")
        sweep(top, f"{ctx} › ventana {type(top).__name__}")      # by class: one pair dialog is every pair dialog
        top.close()
    daemon_log()
    if it.nav:
        shoot(zone.window(), f"{ctx}_{it.what}")
    said |= set(STATE["dialogs"][dialogs:])
    painted = sorted(s for s in said if PAINTED.search(s))
    refused = sorted(s for s in said if REFUSAL.search(s) or s.startswith("diálogo"))
    if len(ERRORS) > errors or painted:
        return {"ctx": ctx, "what": it.what, "result": BAD,
                "detail": " ¦ ".join([e[1].strip()[-700:] for e in ERRORS[errors:]] + painted)}
    return {"ctx": ctx, "what": it.what, "result": REFUSED if refused else OK, "detail": " ¦ ".join(refused)[:400]}


def sweep(root: QWidget, ctx: str, zone: QWidget | None = None, skip: tuple = ()) -> None:
    """Drive every action under `root` not yet driven in this context, looking again after each."""
    while isValid(root) and root.isVisible():
        items = inventory(root, skip)
        for it in items:
            FOUND.setdefault((ctx, it.key), it.what)
        todo = [it for it in items if (ctx, it.key) not in DONE]
        if not todo:
            return
        it = min(todo, key=lambda i: i.nav)
        DONE.add((ctx, it.key))
        RESULTS.append(drive(zone or root, ctx, it))
        if zone is not None and not zone.isVisible():     # the action navigated away (an import): come back
            zone.window().open_zone(next(k for k, v in zone.window().zones.items() if v is zone))
            idle()


def walk(shell: QWidget, name: str) -> None:
    """One zone: each module of its rail (when it has one), the module first and then the rest."""
    zone = shell.zones[name]
    shell.open_zone(name)
    idle()
    rail = getattr(zone, "rail", None)
    for row in range(rail.count() if rail is not None else 1):
        ctx = name
        if rail is not None:
            rail.setCurrentRow(row)
            idle()
            ctx = rail.item(row).text()
            RESULTS.append({"ctx": ctx, "what": f"módulo «{ctx}» del carril", "result": OK, "detail": ""})
            shoot(shell, ctx)
            sweep(zone.stack.currentWidget(), ctx, zone)
        sweep(zone, ctx, zone, (rail,) if rail is not None else ())
    RESULTS.extend({"ctx": c, "what": what, "result": SKIPPED, "detail": "desapareció antes de su turno"}
                   for (c, key), what in FOUND.items() if (c, key) not in DONE)


def report() -> str:
    """The inventory as Markdown: touched / total per context, then every row that is not ok."""
    lines = ["| módulo | tocados | total | ok | negativa esperada | excepción | no ejercido |", "|---|---|---|---|---|---|---|"]
    for ctx in dict.fromkeys(r["ctx"] for r in RESULTS):
        n = Counter(r["result"] for r in RESULTS if r["ctx"] == ctx)
        lines.append(f"| {ctx} | {n.total() - n[SKIPPED]} | {n.total()} | {n[OK]} | {n[REFUSED]} | {n[BAD]} | {n[SKIPPED]} |")
    n = Counter(r["result"] for r in RESULTS)
    lines += [f"| **todo** | {len(RESULTS) - n[SKIPPED]} | {len(RESULTS)} | {n[OK]} | {n[REFUSED]} | {n[BAD]} | {n[SKIPPED]} |",
              "", "| módulo | control | resultado | detalle |", "|---|---|---|---|"]
    lines += [f"| {r['ctx']} | {r['what']} | {r['result']} | {r['detail'].replace('|', '¦').replace(chr(10), ' ⏎ ')} |"
              for r in RESULTS if r["result"] != OK]
    return "\n".join(lines) + "\n"


def boot(port: int, write: bool = False, log: Path | None = None, shots: Path | None = None) -> QWidget:
    """The real window against the daemon on `port`, with every trap set; returns the shell."""
    if not client.health(port):
        sys.exit(f"No hay demonio en el puerto {port}: python3 -m ui.daemon.serve --port {port}")
    uiwalk.aim(port, write)
    if write and not client.get("portfolios/state").get("test_root"):
        sys.exit("--write solo contra un demonio en una raíz de prueba (ALGO_DATA_ROOT)")
    uiwalk.trap()
    real = client.send

    def send(method: str, path: str, **how: object) -> dict:
        """The window's request, with a non-2xx answer kept for the report."""
        try:
            return real(method, path, **how)
        except httpx.HTTPStatusError as e:
            ERRORS.append((HERE["zone"], f"HTTP {e.response.status_code} {method} /api/{path}: {e.response.text[:300]}"))
            raise

    def modal(box: QDialog) -> int:
        """A modal that would block: say it was shown, answer as `ANSWER` says."""
        said = plain(box.text())[:300] if isinstance(box, QMessageBox) else ""
        STATE["dialogs"].append(f"diálogo «{box.windowTitle()}» {said} → {'Sí' if ANSWER['yes'] else 'No'}")
        return QMessageBox.Yes if ANSWER["yes"] else QMessageBox.No

    def ask(_parent: QWidget, title: str, text: str = "", *a: object, **k: object) -> int:
        """`QMessageBox.question` and its siblings."""
        STATE["dialogs"].append(f"diálogo «{title}» {plain(text)[:300]} → {'Sí' if ANSWER['yes'] else 'No'}")
        return QMessageBox.Yes if ANSWER["yes"] else QMessageBox.No

    def get_text(_parent: QWidget, title: str, *a: object, **k: object) -> tuple[str, bool]:
        """`QInputDialog.getText`: the text in `ANSWER`, cancelled when it is empty."""
        STATE["dialogs"].append(f"diálogo «{title}» → {ANSWER['text'] or 'cancelado'}")
        return ANSWER["text"], bool(ANSWER["text"])

    client.send = send
    QMessageBox.exec = QDialog.exec = modal
    for name in ("question", "warning", "information", "critical"):
        setattr(QMessageBox, name, staticmethod(ask))
    QInputDialog.getText = staticmethod(get_text)
    qInstallMessageHandler(lambda mode, _ctx, msg: ERRORS.append((HERE["zone"], f"Qt: {msg}")) if mode in (
        QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg) and not any(x in msg for x in NOISE) else None)
    from ui.desktop import helpmark
    from ui.desktop.shell import Shell
    from ui.desktop.theme import QSS
    STATE.update(app=QApplication(sys.argv), shots=shots, log=log, at=log.stat().st_size if log and log.exists() else 0)
    if shots:
        shots.mkdir(parents=True, exist_ok=True)
    STATE["app"].setStyleSheet(QSS)
    helpmark.install(STATE["app"])
    shell = Shell()
    shell.resize(1600, 1000)
    shell.show()
    idle()
    return shell


def main() -> None:
    """Walk one zone and print (or write) its inventory; exit 1 when anything raised."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--port", type=int, required=True, help="el puerto del demonio a usar")
    ap.add_argument("--zone", required=True, help="la zona, como la nombra la barra lateral")
    ap.add_argument("--write", action="store_true", help="deja pasar los POST: cada «Calcular» corre de verdad (raíz de prueba)")
    ap.add_argument("--shots", type=Path, help="carpeta donde guardar un PNG por módulo, pestaña y ventana")
    ap.add_argument("--out", type=Path, help="el inventario en Markdown (y sus filas en .jsonl al lado)")
    ap.add_argument("--daemon-log", type=Path, help="el registro del demonio, para ver sus tracebacks")
    args = ap.parse_args()
    HERE["zone"] = args.zone
    walk(boot(args.port, args.write, args.daemon_log, args.shots), args.zone)
    text = report()
    if args.out:
        args.out.write_text(text, encoding="utf-8")
        args.out.with_suffix(".jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in RESULTS), encoding="utf-8")
    print(text, flush=True)
    uiwalk.os._exit(1 if any(r["result"] == BAD for r in RESULTS) else 0)


if __name__ == "__main__":
    main()
