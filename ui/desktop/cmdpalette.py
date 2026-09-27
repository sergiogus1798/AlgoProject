"""Ctrl+K: type a few letters, Enter opens that zone, project, databank, strategy or study."""

import json
import unicodedata

import httpx
from PySide6.QtCore import QEvent, QPoint, QSettings, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QApplication, QFrame, QLabel, QLineEdit, QListWidget,
                               QListWidgetItem, QPlainTextEdit, QTextEdit, QVBoxLayout)

from ui.desktop import client
from ui.desktop.nav import ZONES
from ui.desktop.selection import SELECTION
from ui.desktop.theme import MONO, T

# Recent choices: the per-viewer QSettings of the app (organisation, application), never AlgoData.
RECENT_KEY, RECENT_MAX, SHOWN = "cmdpalette/recent", 10, 60
STORE = ("AlgoProject", "AlgoProject")
TAG = {"zone": "zona", "project": "proyecto", "databank": "databank", "strategy": "estrategia",
       "study": "estudio"}
ORDER = list(TAG)


def fold(s: str) -> str:
    """Lower case without accents, so «poblacion» finds «Población»."""
    return "".join(c for c in unicodedata.normalize("NFD", s.lower())
                   if unicodedata.category(c) != "Mn")


def match(query: str, label: str) -> int | None:
    """Fuzzy subsequence score of a query against a label.

    Args:
        query: What the owner typed.
        label: The candidate's name.

    Returns:
        None when the query's letters do not appear in order; otherwise the letters skipped
        between the first and last hit plus where the first hit sits (lower is better).
    """
    q, s = fold(query).replace(" ", ""), fold(label)
    at, first, gaps = -1, None, 0
    for ch in q:
        nxt = s.find(ch, at + 1)
        if nxt < 0:
            return None
        if first is None:
            first = nxt
        else:
            gaps += nxt - at - 1
        at = nxt
    return gaps * 2 + (first or 0)


def ident(item: dict) -> tuple:
    """What makes two items the same choice, for the recent list."""
    return item["kind"], item["label"], item.get("project"), item.get("databank")


def rank(query: str, items: list[dict], recent: list[dict]) -> list[dict]:
    """The items to list for a query: recent matches first, newest on top, then by score and kind.

    Args:
        query: What the owner typed; "" lists everything.
        items: Every candidate.
        recent: The last choices, newest first.

    Returns:
        The matching items, a recent one carrying `recent: True`.
    """
    seen = {ident(r) for r in recent}
    pool = [{**r, "recent": True} for r in recent] + [i for i in items if ident(i) not in seen]
    kept = [(s, i) for s, i in ((match(query, i["label"]), i) for i in pool) if s is not None]
    return [i for _, i in sorted(kept, key=lambda p: (0, 0, 0) if p[1].get("recent") else
                                 (1, p[0], ORDER.index(p[1]["kind"])))]


def load_recent() -> list[dict]:
    """The last choices, newest first; a broken store reads as none."""
    try:
        got = json.loads(QSettings(*STORE).value(RECENT_KEY, "[]") or "[]")
        return [r for r in got if r.get("kind") in TAG and r.get("label")][:RECENT_MAX]
    except Exception:  # noqa: BLE001 — a per-viewer convenience must never break the window
        return []


def save_recent(item: dict) -> None:
    """Put one choice at the head of the recent list; a store that refuses is ignored."""
    clean = {k: v for k, v in item.items() if k != "recent"}
    rest = [r for r in load_recent() if ident(r) != ident(clean)]
    try:
        QSettings(*STORE).setValue(RECENT_KEY, json.dumps([clean, *rest][:RECENT_MAX]))
    except Exception:  # noqa: BLE001 — same as above
        pass


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
        """Every candidate, read from the daemon; the matrix only for the chosen databank.

        Returns:
            The items, and one sentence naming what could not be read ("" when all was).
        """
        items = [{"kind": "zone", "label": z, "hint": "zona"} for z in ZONES]
        now, trouble = SELECTION.now, []
        here = (now["project"], now["databank"])
        try:
            projects = client.get("projects")["projects"]
            if not self.catalogue:
                self.catalogue = client.get("catalogue")["studies"]
            if all(here) and self.matrix[0] != here:
                got = client.get("matrix", project=here[0], databank=here[1])
                self.matrix = (here, got.get("strategies", []))
        except (httpx.HTTPError, KeyError) as e:
            projects, trouble = [], [f"El demonio no respondió: {e}"]
        for p in projects:
            items.append({"kind": "project", "label": p["project"], "project": p["project"],
                          "asset": p["asset"], "hint": f"{len(p['databanks'])} databanks"})
            items += [{"kind": "databank", "label": f"{p['project']} / {d}", "databank": d,
                       "project": p["project"], "asset": p["asset"], "hint": "databank"}
                      for d in p["databanks"]]
        if not all(here):
            trouble.append("Sin databank elegido: no hay estrategias que listar.")
        elif self.matrix[0] == here:
            items += [{"kind": "strategy", "label": s["strategy"], "project": now["project"],
                       "databank": now["databank"], "asset": now["asset"],
                       "identity": s["identity"], "hint": f"{now['databank']} · "
                                                          f"{s['identity'][:8]}"}
                      for s in self.matrix[1]]
        items += [{"kind": "study", "label": f"{e['title']} ({e['key']})", "study": e["key"],
                   "one": e["one"], "many": e["many"], "hint": e["family"]}
                  for e in self.catalogue]
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
            row.setToolTip("Elegido hace poco" if i.get("recent") else TAG[i["kind"]])
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

