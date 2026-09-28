"""The boxes the asset zone opens to change something: a text, a cost, a market, a new asset."""

from PySide6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QFormLayout, QLabel,
                               QLineEdit, QPlainTextEdit, QVBoxLayout)

from ui.desktop import client
from ui.text.glossary import LABELS, label
from ui.text.numbers import num
from ui.desktop.theme import C

WIDE = 560   # the width every paragraph in this zone wraps against

FIXED_FIRST = ("LA LISTA SE FIJA ANTES DE MIRAR NINGÚN RESULTADO: elegir los mercados después "
               "de ver dónde funcionan las estrategias convierte la prueba en una selección y "
               "sus p-valores en decoración.")

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


def now(value: object) -> str:
    """What the master carries today, in whichever shape `sqx_now` was recorded.

    Args:
        value: A figure, a {min, max} range, a {method|type, value} commission or swap, or
            a list of ranges when several tasks carry different ones.

    Returns:
        «1 – 5 · 5 – 12» for ranges, «8 USD por lote» for a commission, the figure otherwise.
    """
    if isinstance(value, list):
        return " · ".join(now(v) for v in value)
    if isinstance(value, dict) and "min" in value:
        return f"{num(value['min'])} – {num(value['max'])}"
    if isinstance(value, dict):
        return f"{num(value.get('value'))} {word(value.get('method') or value.get('type'))}"
    return num(value)


def word(key: object) -> str:
    """A key of assets/ as the zone shows it: its `assets.` glossary entry, else `label()`."""
    return LABELS.get(f"assets.{key}") or label(key)


def buttons(dialog: QDialog) -> QDialogButtonBox:
    """The accept/cancel pair, wired to the dialog.

    Args:
        dialog: The dialog they belong to.

    Returns:
        A button box already connected.
    """
    box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
    box.button(QDialogButtonBox.Save).setText("Guardar")
    box.button(QDialogButtonBox.Cancel).setText("Cancelar")
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


class MarketBox(QDialog):
    """A market joining one category of an asset's Cross Market check."""

    def __init__(self, symbol: str, categories: list[str], candidates: list[dict]) -> None:
        """Offer the category first, then every asset not yet in the check.

        Args:
            symbol: The main asset.
            categories: family and structural, as `_markets.yaml` names them.
            candidates: {asset, feed, data_from} for every asset that can still be added.
        """
        super().__init__()
        self.candidates = candidates
        self.setWindowTitle(f"{symbol} · Check de Cross Market")
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel(f"{symbol} · Añadir un mercado", objectName="h2"))
        lay.addWidget(explain(
            "Family: mismo motor económico que el activo, la prueba fácil. Structural: misma "
            f"estructura y ningún motor compartido, la prueba dura. {FIXED_FIRST}"))
        form = QFormLayout()
        self.category = QComboBox()
        for c in categories:
            self.category.addItem(word(c), c)
        form.addRow("Categoría", self.category)
        self.market = QComboBox()
        self.market.addItems([f"{c['asset']} — datos desde {c['data_from'] or 'sin fecha'}"
                              for c in candidates])
        form.addRow("Activo", self.market)
        lay.addLayout(form)
        lay.addWidget(buttons(self))

    def payload(self) -> tuple[str, dict]:
        """The category chosen and the market going into it, as {feed, data_from}."""
        pick = self.candidates[self.market.currentIndex()]
        return self.category.currentData(), {"feed": pick["feed"],
                                             "data_from": pick["data_from"] or None}


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
        self.setWindowTitle(f"{symbol} · {word(cost['field'])}")
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel(f"{symbol} · {word(cost['field'])}", objectName="h2"))
        lay.addWidget(explain(
            f"Unidad: {word(cost['unit'])}. SQX lleva hoy {now(cost['sqx_now'])}, que no "
            f"siempre está en la misma unidad. {BLOCKING if cost['required'] else ''}"))

        form = QFormLayout()
        self.value = QLineEdit("" if cost["use"] is None else str(cost["use"]))
        self.value.setPlaceholderText("vacío = null, sin decidir")
        self.value.editingFinished.connect(self.propose)
        form.addRow(f"Usar ({word(cost['unit'])})", self.value)
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
