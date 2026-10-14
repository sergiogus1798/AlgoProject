"""The ficha's equity: SQX's curve, IS and OOS1 in two tones."""

from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from ui.desktop.blocks import chart
from ui.text.glossary import label
from ui.desktop.theme import C
from ui.desktop.workspace.curves import INK, SampleCurves

HEIGHT = 300            # px of the drawing; the owner reads it from across the desk


class CostCurves(QWidget):
    """Kicker, the switch, the chart and the line a failed read speaks on."""

    def __init__(self) -> None:
        """Build it empty."""
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(QLabel("Curva de equity", objectName="kicker"))  # pyright: ignore[reportCallIssue]  # PySide6 stub lacks property kwargs
        switches = QHBoxLayout()
        box = QCheckBox(label("curve.sqx"))
        box.setChecked(True)
        box.setStyleSheet(f"color: {INK['sqx.IS']};")
        box.toggled.connect(lambda on: self.curves.toggle("sqx", on))
        switches.addWidget(box)
        switches.addStretch(1)
        lay.addLayout(switches)
        lay.addWidget(chart.key([("line", INK[f"sqx.{part}"], f"SQX · {seg}")
                                 for part, seg in (("IS", "IS"), ("OOS", "OOS1"))]))
        self.curves = SampleCurves(HEIGHT)
        lay.addWidget(self.curves, 1)
        self.figures = QLabel("", objectName="mono")  # pyright: ignore[reportCallIssue]  # PySide6 stub lacks property kwargs
        self.figures.setWordWrap(True)
        lay.addWidget(self.figures)

    def fill(self, curve: dict) -> None:
        """Paint `/api/strategy/costcurve`'s answer, or its error.

        Args:
            curve: `sqx`, `split`, `sqx_net`, `sqx_dd`, `source` — or `error`.
        """
        if "error" in curve:
            self.curves.fill([0.0, 0.0])
            self.figures.setText(curve["error"])
            self.figures.setStyleSheet(f"color: {C['muted' if curve.get('absent') else 'dead']};")
            return
        self.figures.setStyleSheet("")
        self.curves.fill(curve["sqx"], curve.get("split"), curve.get("days", []))
        self.figures.setText("")
