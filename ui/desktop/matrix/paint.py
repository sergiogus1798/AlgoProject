"""How the matrix is painted: a cell in its state's colour, and a header with its title and its counts."""

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QHeaderView, QStyledItemDelegate, QStyleOptionViewItem, QStyle

from ui.desktop.blocks.states import colour
from ui.desktop.matrix.model import CELL, FIXED
from ui.desktop.theme import C, T

# Order of the counts under a header and of the bar: the verdicts first, the holes last.
ORDER = ("pass", "watch", "fail", "info", "none", "missing")
INK = QColor("#0b0b0c")
HEAD_HEIGHT = 118


def mono(size: int, bold: bool = True) -> QFont:
    """The terminal face at one pixel size."""
    f = QFont("JetBrains Mono")
    f.setStyleHint(QFont.Monospace)
    f.setPixelSize(size)
    f.setBold(bold)
    return f


def mark(p: QPainter, x: int, y: int, role: str) -> None:
    """Paint the role mark in a 15 px square: ⛔ (red disc, white bar) for gate, 👁 for describe.

    Args:
        p: Painter.
        x, y: Top-left corner.
        role: "gate" or "describe".
    """
    p.save()
    p.setRenderHint(QPainter.Antialiasing)
    if role == "gate":
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(C["dead"]))
        p.drawEllipse(x, y, 15, 15)
        p.fillRect(x + 3, y + 6, 9, 3, QColor("#ffffff"))
    else:
        p.setPen(QPen(QColor(C["accent"]), 1.6))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(x, y + 3, 15, 9)
        p.setBrush(QColor(C["accent"]))
        p.drawEllipse(x + 5, y + 5, 5, 5)
    p.restore()


class CellDelegate(QStyledItemDelegate):
    """A study cell: filled with its state's colour, its label in ink, hatched with ◷ when stale."""

    def paint(self, p: QPainter, option: QStyleOptionViewItem, index: object) -> None:
        """Paint one cell; the two fixed columns go to Qt's own painter."""
        if index.column() < len(FIXED):
            super().paint(p, option, index)
            return
        cell = index.data(CELL)
        r = option.rect.adjusted(1, 1, -1, -1)
        chosen = bool(option.state & QStyle.State_Selected)
        p.save()
        if cell is None:
            p.fillRect(option.rect, QColor(T["select"] if chosen else T["bg"]))
            p.setPen(QColor(T["faint"]))
            p.setFont(mono(12, False))
            p.drawText(r, Qt.AlignCenter, "·")
            p.restore()
            return
        p.fillRect(r, QColor(colour(cell["state"])))
        if cell["stale"]:
            p.fillRect(r, QBrush(QColor(0, 0, 0, 150), Qt.BDiagPattern))
        p.setPen(INK)
        p.setFont(mono(11))
        text = ("◷ " if cell["stale"] else "") + cell["label"]
        p.drawText(r.adjusted(5, 0, -3, 0), Qt.AlignVCenter | Qt.AlignLeft,
                   p.fontMetrics().elidedText(text, Qt.ElideRight, r.width() - 8))
        if chosen:
            p.setPen(QPen(QColor(T["text"]), 2))
            p.drawLine(r.topLeft(), r.topRight())
            p.drawLine(r.bottomLeft(), r.bottomRight())
        p.restore()


class StudyHeader(QHeaderView):
    """The column headers: role mark and title on two lines, then a bar and the counts of the visible rows."""

    def __init__(self) -> None:
        """A horizontal header, clickable, as tall as two title lines, a bar and a count line."""
        super().__init__(Qt.Horizontal)
        self.setSectionsClickable(True)
        self.setMinimumHeight(HEAD_HEIGHT)
        self.filtered: set[str] = set()

    def sizeHint(self) -> object:
        """Fixed height, whatever the style says."""
        s = super().sizeHint()
        s.setHeight(HEAD_HEIGHT)
        return s

    def paintSection(self, p: QPainter, rect: QRect, section: int) -> None:
        """Paint one header section.

        Args:
            p: The painter Qt hands over.
            rect: The section's rectangle.
            section: Logical column.
        """
        model = self.model()
        p.save()
        p.fillRect(rect, QColor(T["bg"]))
        p.setPen(QColor(T["rule"]))
        p.drawLine(rect.bottomLeft(), rect.bottomRight())
        p.drawLine(rect.topRight(), rect.bottomRight())
        box = rect.adjusted(6, 5, -6, -5)
        field = model.field(section)
        order = model.order
        arrow = ("▲" if order[1] == Qt.AscendingOrder else "▼") if order and order[0] == field else ""
        funnel = " ≡" if field in self.filtered else ""
        p.setPen(QColor(T["text"]))
        p.setFont(mono(12))
        title = model.headerData(section, Qt.Horizontal, Qt.DisplayRole)
        indent = 0 if section < len(FIXED) else 20
        if indent:
            mark(p, box.left(), box.top() + 1, model.columns[section - len(FIXED)]["role"])
        head = QRect(box.left() + indent, box.top(), box.width() - 22 - indent, 46)
        p.drawText(head, Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, title)
        p.setPen(QColor(T["muted"]))
        p.drawText(box, Qt.AlignRight | Qt.AlignTop, arrow + funnel)
        if section < len(FIXED):
            p.setFont(mono(12, False))
            p.drawText(box, Qt.AlignLeft | Qt.AlignBottom, f"{len(model.rows):,} filas")
            p.restore()
            return
        counts = model.counts[section - len(FIXED)]
        total = sum(counts.values()) or 1
        bar = QRect(box.left(), box.top() + 52, box.width(), 10)
        x = bar.left()
        for state in ORDER:
            w = round(bar.width() * counts[state] / total)
            p.fillRect(QRect(x, bar.top(), w, bar.height()),
                       QColor(T["line"] if state == "missing" else colour(state)))
            x += w
        p.setFont(mono(12))
        x, y = box.left(), bar.bottom() + 6
        for state in ORDER:
            if counts[state]:
                p.setPen(QColor(T["faint"] if state == "missing" else colour(state)))
                text = f"{counts[state]:,}"
                width = p.fontMetrics().horizontalAdvance(text + " ")
                if x + width > box.right() + 8:
                    x, y = box.left(), y + 18
                p.drawText(QRect(x, y, width, 18), Qt.AlignLeft | Qt.AlignVCenter, text)
                x += width
        p.restore()
