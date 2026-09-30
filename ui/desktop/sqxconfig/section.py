"""One test or topic of the SQX settings: a header that folds, the file's own words, one row per value."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from ui.desktop.theme import C
from ui.text.glossary import LABELS, label
from ui.desktop.sqxconfig.field import Field

HELP_WIDTH = 440   # px of the per-value comment beside its editor
SHORT = 420        # characters of a long comment shown before «seguir leyendo»


def words(key: object) -> str:
    """The label of one key of the settings files, the zone's own glossary entry first."""
    return label(f"sqx.{key}") if f"sqx.{key}" in LABELS else label(key)


def group_of(section: dict, spec: dict) -> str:
    """The sub-heading a value sits under: the path between the section and the value.

    Args:
        section: The section, to name a list item by its `title` when it has one.
        spec: The value. A study value of WFC or CSCV brings its own `group` heading and
            the `base` of its path that heading already names.

    Returns:
        The heading, e.g. «Tareas › MCR 7 OHLC › Métodos › RandomizeHistoryDataOHLC», or ""
        for a value that hangs straight off the section.
    """
    path = spec["path"]
    if spec.get("group"):
        return " › ".join([spec["group"], *(words(k) for k in path[len(spec["base"]):-1])])
    parts = []
    for depth, key in enumerate(path[1:-1], start=1):
        if isinstance(key, int):
            titled = [f["value"] for f in section["fields"]
                      if f["path"][:depth + 1] == path[:depth + 1] and f["key"] == "title"]
            parts.append(titled[0] if titled else f"n.º {key + 1}")
        else:
            parts.append(words(key))
    return " › ".join(parts)


def note(text: str, width: int = 0, short: int = 0) -> QWidget:
    """The file's own comment over a section or a group: its opening, and the rest on demand.

    Args:
        text: The comment, as one paragraph.
        width: A fixed width in px, for the comment beside a value; 0 lets it fill the row.
        short: Characters shown before the button; 0 means SHORT.

    Returns:
        A dim paragraph. Past SHORT characters it shows the opening and a «seguir leyendo»
        button: MC Retest's comment is forty lines and would push every value off screen.
    """
    short = short or SHORT
    box = QWidget()
    if width:
        box.setFixedWidth(width)
    lay = QVBoxLayout(box)
    lay.setContentsMargins(0, 0, 0, 4)
    lay.setSpacing(2)
    words_ = QLabel(text if len(text) <= short else text[:short].rsplit(" ", 1)[0] + " …")
    words_.setWordWrap(True)
    words_.setObjectName("dim")
    words_.setTextInteractionFlags(Qt.TextSelectableByMouse)
    lay.addWidget(words_)
    if len(text) > short:
        more = QPushButton("seguir leyendo")
        more.setFixedWidth(160)
        more.clicked.connect(lambda: (words_.setText(text), more.hide()))
        lay.addWidget(more)
    return box


class Section(QFrame):
    """A section of the zone. Folded it is one line; open it lists every value. `written`,
    `refused` and `stale` bubble up from its fields."""

    written = Signal(str)
    refused = Signal(str)
    stale = Signal()

    def __init__(self, section: dict) -> None:
        """Build the header now and the rows on first unfold.

        Args:
            section: One entry of `/api/sqxconfig`'s `sections`.
        """
        super().__init__()
        self.section, self.body = section, None
        locked = sum(bool(f.get("locked")) for f in section["fields"])
        self.head = QPushButton()
        self.head.setFlat(True)
        self.head.setCheckable(True)
        self.head.setStyleSheet("text-align: left; border: none; font-size: 15px;")
        count = len(section["fields"])
        self.caption = (f"{words(section['key'])}   ·   {count} valor{'es' if count != 1 else ''}"
                        + (f", {locked} bloqueados" if locked else "")
                        + f"   ·   {section['source']}")
        self.head.setToolTip("\n".join(section.get("files", [section["source"]])))
        self.head.toggled.connect(self.fold)
        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(0, 4, 0, 4)
        self.lay.setSpacing(4)
        self.lay.addWidget(self.head)
        rule = QFrame()
        rule.setObjectName("rule")
        self.lay.addWidget(rule)
        self.fold(False)

    def fold(self, open_: bool) -> None:
        """Show or hide the rows, building them the first time.

        Args:
            open_: Whether the section is now open.
        """
        self.head.setText(("▾  " if open_ else "▸  ") + self.caption)
        if open_ and self.body is None:
            self.body = self.rows()
            self.lay.insertWidget(1, self.body)
        if self.body is not None:
            self.body.setVisible(open_)

    def rows(self) -> QWidget:
        """The section's comment, then one row per value, sub-headed where the path deepens.

        Returns:
            The body widget.
        """
        body = QWidget()
        grid = QGridLayout(body)
        grid.setContentsMargins(18, 2, 0, 10)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(5)
        r = 0
        if self.section["help"]:
            grid.addWidget(note(self.section["help"]), r, 0, 1, 3)
            r += 1
        heading, told = "", {self.section["help"]}
        for spec in self.section["fields"]:
            group = group_of(self.section, spec)
            if group != heading:
                sub = QLabel(group)
                sub.setObjectName("kicker")
                grid.addWidget(sub, r, 0, 1, 3)
                heading, r = group, r + 1
                # WFC and CSCV's study values: one warning under the heading, not one per row
                if spec.get("group_help") and spec["group_help"] not in told:
                    told.add(spec["group_help"])
                    warning = QLabel(spec["group_help"])
                    warning.setWordWrap(True)
                    warning.setStyleSheet(f"color: {C['weak']}; font-weight: 700;")
                    grid.addWidget(warning, r, 0, 1, 3)
                    r += 1
            for g in self.section["groups"]:
                if spec["path"][:len(g["path"])] == g["path"] and g["help"] not in told:
                    told.add(g["help"])
                    grid.addWidget(note(g["help"]), r, 0, 1, 3)
                    r += 1
            name = QLabel(words(spec["key"]))
            name.setObjectName("mono")
            name.setToolTip(" › ".join(str(p) for p in spec["path"]))
            field = Field(spec.get("file", self.section["file"]), spec)
            field.written.connect(self.written)
            field.refused.connect(self.refused)
            field.stale.connect(self.stale)
            grid.addWidget(name, r, 0, Qt.AlignTop)
            grid.addWidget(field, r, 1, Qt.AlignTop)
            if spec["help"] and spec["help"] not in told:
                grid.addWidget(note(spec["help"], HELP_WIDTH, SHORT // 2), r, 2, Qt.AlignTop)
            r += 1
        grid.setColumnStretch(1, 1)
        return body
