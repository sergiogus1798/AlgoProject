"""The bar on top: Proyectos › proyecto › estrategia, bound to SELECTION; each crumb goes back."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton

from ui.desktop.loadbar import LoadBar
from ui.desktop.selection import SELECTION
from ui.desktop.theme import MONO, T

# Which zone each crumb opens (encargo 22 §2: the bar follows the three new zones). With no
# project chosen every crumb opens the gallery, where a project is chosen. The databank is not
# a crumb: it is where the strategy lives, written beside the asset.
TARGET = {"projects": "Proyectos", "project": "Proyecto", "strategy": "Estrategia"}


def crumb_text(now: dict) -> dict[str, str]:
    """What each crumb says for one selection.

    Args:
        now: SELECTION's fields.

    Returns:
        `{projects, project, strategy}` → text; a field not chosen reads «elige …». The
        identity is never printed (encargo 22 §10): it lives in the strategy crumb's tooltip.
    """
    return {"projects": "Proyectos", "project": now["project"] or "elige proyecto",
            "strategy": now["strategy"] or "elige estrategia"}


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
                TARGET[k] if SELECTION.now["project"] else "Proyectos"))
            lay.addWidget(b)
            self.crumbs[key] = b
        self.asset = QLabel("")
        self.asset.setStyleSheet(f"color:{T['faint']}; font-family:{MONO}; font-size:13px;")
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
            ink = T["text"] if key == "projects" or now[key] else T["faint"]
            weight = 700 if key == "strategy" and now[key] else 500
            b.setStyleSheet(f"font-family:{MONO}; font-size:14px; border:none; padding:3px 6px; "
                            f"color:{ink}; font-weight:{weight};")
            b.setToolTip(f"Abrir {TARGET[key]}" + (f" · identidad {now['identity']}"
                                                   if key == "strategy" and now["identity"]
                                                   else ""))
        self.asset.setText("   ".join(f"· {word} {now[key]}" for key, word in
                                      (("databank", "databank"), ("asset", "activo")) if now[key]))
