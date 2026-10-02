"""The ficha's equity: SQX's curve and the one at the real spread and slippage, each switchable, IS and OOS1 in two tones."""

from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from ui.desktop.blocks import chart
from ui.text.glossary import label
from ui.desktop.theme import C
from ui.desktop.workspace.curves import INK, SampleCurves
from ui.desktop.workspace.fichajobs import Compute, uncomputed

HEIGHT = 300            # px of the drawing; the owner reads it from across the desk
# Why the real curve can beat SQX's: the owner declares SQX's spread with a safety margin
# (× 1.25 sobre el spread medido, «mejor pasarse que quedarse corto»), así que el coste real
# medido en Darwinex suele ser menor que el que SQX cobró — no es un fallo del repricing.
REAL_HELP = ("El spread y la comisión que SQX cobró llevan un margen de seguridad a propósito "
             "(× 1,25 sobre el spread medido de Darwinex): por eso esta curva sale mejor que la "
             "de SQX en casi toda estrategia, no por un error de repricing.")


def clear(lay: QHBoxLayout) -> None:
    """Empty a row of widgets and nested rows."""
    while lay.count():
        item = lay.takeAt(0)
        if item.widget():
            item.widget().deleteLater()
        elif item.layout():
            clear(item.layout())


class CostCurves(QWidget):
    """Kicker, the two switches, a «?» on why the real curve can beat SQX's, the chart, the
    missing real curve's buttons."""

    def __init__(self, compute: Compute) -> None:
        """Build it empty.

        Args:
            compute: The ficha's queue, for «calcular» when the real curve is missing.
        """
        super().__init__()
        self.compute = compute
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(QLabel("CURVA DE EQUITY", objectName="kicker"))
        switches = QHBoxLayout()
        self.boxes = {}
        for key in ("sqx", "real"):
            box = self.boxes[key] = QCheckBox(label(f"curve.{key}"))
            box.setChecked(True)
            box.setStyleSheet(f"color: {INK[f'{key}.IS']};")
            box.toggled.connect(lambda on, k=key: self.curves.toggle(k, on))
            switches.addWidget(box)
        self.boxes["real"].setToolTip(REAL_HELP)
        help_mark = QLabel("?", objectName="helpmark")
        help_mark.setFixedSize(17, 17)
        help_mark.setToolTip(REAL_HELP)
        switches.addWidget(help_mark)
        switches.addStretch(1)
        lay.addLayout(switches)
        lay.addWidget(chart.key([("line", INK[f"{k}.{part}"], f"{name} · {seg}")
                           for k, name in (("sqx", "SQX"), ("real", "SPREAD Y SLIPPAGE REALES"))
                           for part, seg in (("IS", "IS"), ("OOS", "OOS1"))]))
        self.curves = SampleCurves(HEIGHT)
        lay.addWidget(self.curves, 1)
        self.missing = QHBoxLayout()
        lay.addLayout(self.missing)
        self.figures = QLabel("", objectName="mono")
        self.figures.setWordWrap(True)
        lay.addWidget(self.figures)

    def fill(self, curve: dict) -> None:
        """Paint `/api/strategy/costcurve`'s answer, or its error.

        Args:
            curve: `sqx`, `real` (None without a spread report, with `real_why`), `split`,
                `sqx_net`, `real_net`, `sqx_dd`, `real_dd`, `source` — or `error`.
        """
        clear(self.missing)
        if "error" in curve:
            self.curves.fill([0.0, 0.0], [])
            self.figures.setText(curve["error"])
            self.figures.setStyleSheet(f"color: {C['muted' if curve.get('absent') else 'dead']};")
            return
        self.figures.setStyleSheet("")
        real = curve.get("real")
        self.curves.fill(curve["sqx"], real or [], curve.get("split"), curve.get("days", []))
        self.boxes["real"].setEnabled(bool(real))
        self.figures.setText("")
        if not real:
            self.missing.addWidget(QLabel(f"{label('curve.real')}: ", objectName="dim"))
            self.missing.addLayout(uncomputed("spread", self.compute))
