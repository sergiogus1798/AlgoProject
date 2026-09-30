"""The ficha's equity: SQX's curve and the one at the real spread and slippage, each switchable, IS and OOS1 in two tones."""

from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from ui.desktop.blocks import chart
from ui.text.glossary import label
from ui.text.numbers import num
from ui.desktop.theme import C
from ui.desktop.workspace.curves import INK, SampleCurves
from ui.desktop.workspace.fichajobs import Compute, uncomputed

HEIGHT = 300            # px of the drawing; the owner reads it from across the desk
SOURCE = ("Las cifras de aquí salen de la curva diaria de SQX (equity.parquet); las de las "
          "estadísticas suman las operaciones (trades.parquet) y difieren en decenas de dólares. "
          "El real es la curva diaria de SQX corregida, el día que cierra cada operación, por "
          "lo que cambian el spread y el slippage de Darwinex (estudio spread, paso 8).")


def clear(lay: QHBoxLayout) -> None:
    """Empty a row of widgets and nested rows."""
    while lay.count():
        item = lay.takeAt(0)
        if item.widget():
            item.widget().deleteLater()
        elif item.layout():
            clear(item.layout())


class CostCurves(QWidget):
    """Kicker, the two switches, the chart, the missing real curve's buttons, the source."""

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
        switches.addStretch(1)
        lay.addLayout(switches)
        lay.addWidget(chart.key([("line", INK[f"{k}.{part}"], f"{name} · {seg}")
                           for k, name in (("sqx", "SQX"), ("real", "spread y slippage"))
                           for part, seg in (("IS", "IS"), ("OOS", "OOS1"))]))
        self.curves = SampleCurves(HEIGHT)
        lay.addWidget(self.curves, 1)
        self.missing = QHBoxLayout()
        lay.addLayout(self.missing)
        self.figures = QLabel("", objectName="mono")
        self.figures.setWordWrap(True)
        lay.addWidget(self.figures)
        self.source = QLabel("", objectName="dim")
        self.source.setWordWrap(True)
        lay.addWidget(self.source)

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
            self.source.setText("")
            return
        self.figures.setStyleSheet("")
        real = curve.get("real")
        self.curves.fill(curve["sqx"], real or [], curve.get("split"), curve.get("days", []))
        self.boxes["real"].setEnabled(bool(real))
        if not real:
            self.missing.addWidget(QLabel(f"{label('curve.real')}: ", objectName="dim"))
            self.missing.addLayout(uncomputed("spread", self.compute))
        figures = [f"{label('curve.sqx')} {num(curve['sqx'][-1])} (DD {num(curve.get('sqx_dd'))})"]
        if real:
            figures.append(f"{label('curve.real')} {num(real[-1])} (DD {num(curve.get('real_dd'))})")
        self.figures.setText("   ·   ".join(figures))
        self.source.setText(f"{curve.get('source', '')}. {SOURCE}" if real
                            else curve.get("source", ""))
