"""The three boxes the asset zone opens to change something: a text, a cost, a new asset."""

from PySide6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QFormLayout, QLabel,
                               QLineEdit, QPlainTextEdit, QVBoxLayout)

from ui.desktop import client
from ui.desktop.theme import C

WIDE = 560   # the width every paragraph in this zone wraps against

BLOCKING = ("Un coste sin decidir (`null`) BLOQUEA la autoría: la preflight sale con 2 y "
            "ninguna plantilla ni proyecto se escribe para este activo. Es a propósito — "
            "un número inventado parece decidido.")


def explain(text: str) -> QLabel:
    """One paragraph of small print that really wraps.

    Args:
        text: The paragraph.

    Returns:
        A muted label with word wrap on and a width it can wrap against.
    """
    label = QLabel(text)
    label.setWordWrap(True)
    label.setFixedWidth(WIDE)
    label.setStyleSheet(f"color:{C['muted']};")
    # A wrapped QLabel reports a one-line sizeHint and the layout believes it, so the
    # paragraph lands on top of whatever sits above it. The height is asked for, not guessed.
    label.setMinimumHeight(max(label.heightForWidth(WIDE), 0))   # -1 on an empty paragraph
    return label


def buttons(dialog: QDialog) -> QDialogButtonBox:
    """The accept/cancel pair, wired to the dialog.

    Args:
        dialog: The dialog they belong to.

    Returns:
        A button box already connected.
    """
    box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
    box.accepted.connect(dialog.accept)
    box.rejected.connect(dialog.reject)
    return box


class TextBox(QDialog):
    """A value too long or too listy for a table cell: a `why`, a note, a list of feeds."""

    def __init__(self, title: str, hint: str, value: str, lines: bool) -> None:
        """Open the box on one value.

        Args:
            title: What is being edited, as the file names it.
            hint: What the file says about it, shown above the box.
            value: The current text.
            lines: True for a list, which is edited one item per line.
        """
        super().__init__()
        self.setWindowTitle(title)
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel(title, objectName="h2"))
        if hint:
            lay.addWidget(explain(hint))
        if lines:
            lay.addWidget(explain("Un elemento por línea. Una línea vacía se descarta."))
        self.box = QPlainTextEdit(value)
        self.box.setMinimumSize(WIDE, 170)
        lay.addWidget(self.box)
        lay.addWidget(buttons(self))

    def text(self) -> str:
        """What was typed, verbatim."""
        return self.box.toPlainText()


class CostBox(QDialog):
    """One cost and the line that justifies it, which are written together or not at all."""

    def __init__(self, symbol: str, cost: dict) -> None:
        """Open the box on one cost field.

        Args:
            symbol: Asset name.
            cost: The field as the daemon reports it: use, unit, sqx_now, why, required.
        """
        super().__init__()
        self.symbol, self.field = symbol, cost["field"]
        self.setWindowTitle(f"{symbol} · {cost['field']}")
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel(f"{symbol} · {cost['field']}", objectName="h2"))
        lay.addWidget(explain(
            f"Se aplica en {cost['unit']}. SQX lleva hoy `{cost['sqx_now']}`, que no siempre "
            f"está en la misma unidad. {BLOCKING if cost['required'] else ''}"))

        form = QFormLayout()
        self.value = QLineEdit("" if cost["use"] is None else str(cost["use"]))
        self.value.setPlaceholderText("vacío = null, sin decidir")
        self.value.editingFinished.connect(self.propose)
        form.addRow(f"Usar ({cost['unit']})", self.value)
        lay.addLayout(form)

        lay.addWidget(QLabel("Por qué", objectName="h2"))
        lay.addWidget(explain(
            "La app propone una línea con la fecha y el valor que sustituye; acábala. No "
            "escribe PROVISIONAL por ti: esa palabra es la que lee `assetcheck.provisional` "
            "para marcar el activo, y ponerla sería decidir por ti cuán provisional es."))
        self.why = QPlainTextEdit(cost["why"])
        self.why.setMinimumSize(WIDE, 120)
        lay.addWidget(self.why)
        lay.addWidget(buttons(self))

    def propose(self) -> None:
        """Offer the justification for the figure just typed, if the box is untouched."""
        if self.why.document().isModified():
            return
        proposed = client.get(f"asset/{self.symbol}/why", field=self.field,
                              text=self.value.text())["why"]
        self.why.setPlainText(proposed)

    def payload(self) -> dict:
        """The write, as the daemon takes it."""
        return {"field": self.field, "text": self.value.text(),
                "why": self.why.toPlainText().strip()}


class NewAssetBox(QDialog):
    """An instrument entering the library, with every cost deliberately left undecided."""

    FACTS = (("tick_size", "Tamaño de tick"), ("point_value", "Valor del punto"),
             ("min_distance", "Distancia mínima"))

    def __init__(self, classes: dict) -> None:
        """Ask for what only SQX and the broker can say.

        Args:
            classes: The two cost schemas, to say what each class implies.
        """
        super().__init__()
        self.setWindowTitle("Nuevo activo")
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("Nuevo activo", objectName="h2"))
        lay.addWidget(explain(
            "La clase decide QUÉ CAMPOS de coste tendrá el fichero: " +
            " · ".join(f"`{k}` {v['what']}" for k, v in classes.items())))

        form = QFormLayout()
        self.fields = {}
        for key, label in (("symbol", "Nombre"), ("broker", "Bróker"),
                           ("sqx_symbol", "Símbolo SQX"), ("session", "Sesión")):
            self.fields[key] = QLineEdit()
            form.addRow(label, self.fields[key])
        self.fields["symbol"].setPlaceholderText("XAUUSD — es también el nombre del fichero")
        self.fields["sqx_symbol"].setPlaceholderText("tal y como lo imprime -symbol action=list")
        self.fields["session"].setPlaceholderText("vacío = sin decidir, y eso bloquea la autoría")
        self.cls = QComboBox()
        self.cls.addItems(list(classes))
        form.addRow("Clase", self.cls)
        for key, label in self.FACTS:
            self.fields[key] = QLineEdit()
            form.addRow(label, self.fields[key])
        lay.addLayout(form)
        lay.addWidget(explain(
            "Los tres últimos son hechos del feed, no decisiones: sácalos con "
            "`python3 -m sqx.inspect.instruments`. Todos los costes nacen `null` y el activo "
            "queda bloqueado hasta que los pactes."))
        lay.addWidget(buttons(self))

    def payload(self) -> dict:
        """The new asset, as the daemon takes it."""
        return {**{k: f.text().strip() for k, f in self.fields.items()},
                "cls": self.cls.currentText()}
