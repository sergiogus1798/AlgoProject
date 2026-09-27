"""The fixed bar on top: Proyecto › Población › Estrategia, bound to SELECTION, each crumb a way back."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton

from ui.desktop.loadbar import LoadBar
from ui.desktop.selection import SELECTION
from ui.desktop.theme import MONO, T

# Which zone each crumb opens. With no project chosen every crumb opens «Población», the only
# zone with the project and databank pickers.
TARGET = {"project": "Workflow", "databank": "Población", "strategy": "Estrategia"}


def crumb_text(now: dict) -> dict[str, str]:
    """What each crumb says for one selection.

    Args:
        now: SELECTION's fields.

    Returns:
        `{project, databank, strategy}` → text; a field not chosen reads «elige …».
    """
    ident = f"  ({now['identity'][:8]})" if now["identity"] else ""
    return {"project": now["project"] or "elige proyecto",
            "databank": now["databank"] or "elige databank",
            "strategy": f"{now['strategy']}{ident}" if now["strategy"] else "elige estrategia"}


class ContextBar(QFrame):
    """Where the owner stands, always on screen. `zone(name)` asks the shell to open one."""

    zone = Signal(str)

    def __init__(self) -> None:
        """Build the three crumbs and follow the global selection."""
        super().__init__(objectName="term")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 6, 12, 6)
        lay.setSpacing(6)
        self.crumbs = {}
        for i, key in enumerate(TARGET):
            if i:
                sep = QLabel("›")
                sep.setStyleSheet(f"color:{T['faint']}; font-size:16px;")
                lay.addWidget(sep)
            b = QPushButton()
            b.clicked.connect(lambda _, k=key: self.zone.emit(
                TARGET[k] if SELECTION.now["project"] else "Población"))
            lay.addWidget(b)
            self.crumbs[key] = b
        self.asset = QLabel("")
        self.asset.setStyleSheet(f"color:{T['faint']}; font-family:{MONO}; font-size:12px;")
        lay.addWidget(self.asset)
        lay.addStretch()
        # The selected databank's data, loaded the moment it is chosen (owner, 2026-09-27).
        self.load = LoadBar()
        lay.addWidget(self.load)
        SELECTION.changed.connect(self.follow)
        self.follow(dict(SELECTION.now))

    def follow(self, now: dict) -> None:
        """Restate the crumbs for a new selection.

        Args:
            now: What `SELECTION.changed` carries.
        """
        for key, text in crumb_text(now).items():
            b = self.crumbs[key]
            b.setText(text)
            ink = T["text"] if now[key] else T["faint"]
            weight = 700 if key == "strategy" and now[key] else 500
            b.setStyleSheet(f"font-family:{MONO}; font-size:13px; border:none; padding:3px 6px; "
                            f"color:{ink}; font-weight:{weight};")
            b.setToolTip(f"Abrir {TARGET[key]}" + (f" · identidad {now['identity']}"
                                                   if key == "strategy" and now["identity"]
                                                   else ""))
        self.asset.setText(f"· activo {now['asset']}" if now["asset"] else "")
