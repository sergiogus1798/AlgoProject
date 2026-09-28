"""Ctrl+K: type a few letters, Enter opens that zone, project, databank, strategy or study.

The PROYECTO zones are three — Proyectos, Proyecto, Estrategia —: a project opens Proyecto, a
databank selects it and opens Proyecto, a strategy opens its ficha and a study opens it on the
ficha of the strategy chosen.
"""

import httpx
from PySide6.QtCore import QEvent, QPoint, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QApplication, QFrame, QLabel, QLineEdit, QListWidget,
                               QListWidgetItem, QPlainTextEdit, QTextEdit, QVBoxLayout)

from ui.desktop import client
from ui.desktop.cmdrank import ALIASES, SHOWN, TAG, load_recent, rank, save_recent
from ui.desktop.nav import ZONES
from ui.desktop.selection import SELECTION
from ui.desktop.theme import MONO, T
from ui.text.numbers import num


class CmdPalette(QFrame):
    """The popup. Built once by the shell, filled from the daemon each time it opens."""

    def __init__(self, shell: object) -> None:
        """Build the box; nothing is read until `open`.

        Args:
            shell: The `Shell`; every choice goes through its `go_to`.
        """
        super().__init__(shell, Qt.Popup)
        self.setObjectName("term")
        self.shell = shell
        self.catalogue: list[dict] = []
        self.matrix: tuple = ((None, None), [])
        self.items: list[dict] = []
        self.shown: list[dict] = []
        self.trouble = ""
        self.setStyleSheet(f"QFrame#term {{ border: 1px solid {T['rule']}; }}")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 10, 10, 8)
        self.field = QLineEdit()
        self.field.setPlaceholderText("zona, proyecto, databank, estrategia o estudio…")
        self.field.setStyleSheet(f"font-family:{MONO}; font-size:15px; padding:6px;")
        self.field.textChanged.connect(self.fill)
        self.field.installEventFilter(self)
        self.list = QListWidget()
        self.list.setStyleSheet(f"font-family:{MONO}; font-size:13px;")
        self.list.itemClicked.connect(lambda it: self.choose(self.list.row(it)))
        self.hint = QLabel("")
        self.hint.setStyleSheet(f"color:{T['faint']}; font-family:{MONO}; font-size:12px;")
        self.hint.setWordWrap(True)
        for w in (self.field, self.list, self.hint):
            lay.addWidget(w)
        self.resize(680, 440)

    def open(self) -> None:
        """Read what can be chosen now, centre the box over the window and focus the field.

        A text field with the focus (the chat's answer box, a filter) keeps Ctrl+K as Qt's
        «delete to end of line» on X11, or nothing: the palette never opens over typing.
        """
        if isinstance(QApplication.focusWidget(), (QLineEdit, QTextEdit, QPlainTextEdit)):
            return
        self.items, self.trouble = self.gather()
        self.move(self.shell.mapToGlobal(QPoint((self.shell.width() - self.width()) // 2, 70)))
        self.field.clear()
        self.fill("")
        self.show()
        self.field.setFocus()

    def gather(self) -> tuple[list[dict], str]:
        """Every candidate: projects and databanks from the gallery, the rest from the daemon.

        The gallery fetches its rows off the GUI thread; asking `/api/projects/all` here
        would freeze the window ~12 s on a cold daemon. Until they land, projects are missing
        and the hint says so.

        Returns:
            The items, and one sentence naming what could not be read ("" when all was).
        """
        items = [{"kind": "zone", "label": z, "hint": "zona", "also": ALIASES.get(z, ())}
                 for z in ZONES]
        now, trouble = SELECTION.now, []
        here = (now["project"], now["databank"])
        projects = list(self.shell.gallery.rows.values())
        if not projects:
            trouble.append("Los proyectos aún se están leyendo: vuelve a abrir Ctrl+K en unos "
                           "segundos.")
        try:
            if not self.catalogue:
                self.catalogue = client.get("catalogue")["studies"]
            if all(here) and self.matrix[0] != here:
                got = client.get("matrix", project=here[0], databank=here[1])
                self.matrix = (here, got.get("strategies", []))
        except (httpx.HTTPError, KeyError) as e:
            trouble.append(f"El demonio no respondió: {e}")
        for p in projects:
            items.append({"kind": "project", "label": p["name"], "project": p["name"],
                          "asset": p["symbol"],
                          "hint": f"{p['symbol'] or '—'} · {p['timeframe'] or '—'} · "
                                  f"{num(p['strategies'])} estrategias · {p['state']}"})
            items += [{"kind": "databank", "label": f"{p['name']} / {d}", "databank": d,
                       "project": p["name"], "asset": p["symbol"],
                       "hint": f"databank · {num(n)} estrategias"}
                      for d, n in p["databanks"].items() if n]
        if not all(here):
            trouble.append("Sin databank elegido: no hay estrategias que listar.")
        elif self.matrix[0] == here:
            items += [{"kind": "strategy", "label": s["strategy"], "project": now["project"],
                       "databank": now["databank"], "asset": now["asset"],
                       "identity": s["identity"], "hint": now["databank"]}
                      for s in self.matrix[1]]
        # A study opens on the ficha of the chosen strategy: only then, and only one that
        # speaks per strategy — a population-only study lives in Proyecto's databank panel.
        if now["strategy"]:
            items += [{"kind": "study", "label": f"{e['title']} ({e['key']})", "study": e["key"],
                       "hint": f"{e['family']} · en la ficha"}
                      for e in self.catalogue if e["one"]]
        return items, " ".join(trouble)

    def fill(self, query: str) -> None:
        """List what matches the field, recent choices first, at most `SHOWN` rows.

        Args:
            query: The field's text.
        """
        found = rank(query, self.items, load_recent())
        self.shown = found[:SHOWN]
        self.list.clear()
        for i in self.shown:
            row = QListWidgetItem(f"{'↺' if i.get('recent') else ' '} {TAG[i['kind']]:<10} "
                                  f"{i['label']}   · {i['hint']}")
            # The identity is never printed on a row (encargo 22 §10); only its tooltip names it.
            row.setToolTip(("Elegido hace poco" if i.get("recent") else TAG[i["kind"]])
                           + (f" · identidad {i['identity']}" if i.get("identity") else ""))
            if i.get("recent"):
                row.setForeground(QColor(T["muted"]))
            self.list.addItem(row)
        self.list.setCurrentRow(0)
        more = f" (se muestran {SHOWN})" if len(found) > SHOWN else ""
        self.hint.setText(f"{len(found)} coinciden{more} · ↑↓ elegir · Enter ir · Esc cerrar · "
                          "↺ = elegido hace poco" + (f"\n{self.trouble}" if self.trouble else ""))

    def eventFilter(self, obj: object, ev: QEvent) -> bool:
        """Arrows move the list, Enter goes, Esc closes, while the focus stays in the field."""
        if ev.type() != QEvent.KeyPress:
            return False
        key = ev.key()
        if key in (Qt.Key_Down, Qt.Key_Up) and self.shown:
            step = 1 if key == Qt.Key_Down else -1
            self.list.setCurrentRow((self.list.currentRow() + step) % len(self.shown))
        elif key in (Qt.Key_Return, Qt.Key_Enter):
            self.choose(self.list.currentRow())
        elif key == Qt.Key_Escape:
            self.close()
        else:
            return False
        return True

    def choose(self, row: int) -> None:
        """Go where one listed item points, remember it and close.

        Args:
            row: Index into the rows on screen; out of range does nothing.
        """
        if 0 <= row < len(self.shown):
            self.close()
            save_recent(self.shown[row])
            self.shell.go_to(self.shown[row])

