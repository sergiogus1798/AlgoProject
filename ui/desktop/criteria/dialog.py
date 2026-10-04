"""The dialog that adds or changes one criterion: a number, a verdict or a compound of them."""

from PySide6.QtWidgets import (QComboBox, QDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
                               QListWidget, QPushButton, QVBoxLayout)

from ui.desktop.theme import C

KINDS = ("Métrica SQX", "Test de la app", "Veredicto", "Compuesto")
SQX, APP, VERDICT, COMPOUND = range(4)
OPS = (">=", ">", "<=", "<", "==")
HELP = {
    "kind": "Métrica SQX: un número que SQX calculó y el estudio copió del databank. Test de "
            "la app: un número de un estudio propio. Veredicto: un test que responde Aprobado "
            "o Suspenso. Compuesto: varias condiciones unidas por «todas» o «alguna».",
    "fact": "El dato que se mira, de los que el paso reunió en su último run del autopilot. "
            "Se puede escribir a mano la clave de uno que aún no esté en la lista.",
    "shape": "Umbral: el dato comparado con un número. Cerca de la mediana: el dato a menos "
             "de ±X % de la mediana de la población que se juzga (el databank que se corta).",
    "pass": "Lo que tiene que cumplir para pasar.",
    "limbo": "Opcional. Si no pasa pero cumple esto, queda en Limbo: sigue adelante, marcada. "
             "Vacío: no hay banda de limbo.",
    "miss": "Qué es no cumplir ni la condición ni el limbo. Fallo: la estrategia se elimina. "
            "Limbo: este criterio nunca elimina a nadie, solo marca.",
    "join": "Todas: el resultado es el de su peor condición. Alguna: el de la mejor — basta "
            "con que una pase.",
    "name": "Opcional: las palabras con que la tabla nombra este criterio.",
}


def told(rule: dict) -> str:
    """A compound's part in one line, for the list."""
    test = {"pass": "Aprobado", "fail": "Suspenso"}[rule["is"]] if "is" in rule else \
        f"±{100 * rule['near_median']:g} % de la mediana" if "near_median" in rule else rule["pass"]
    return f"{rule['fact']}   {test}" + (f"   · limbo {rule['limbo']}" if "limbo" in rule else "")


class RuleDialog(QDialog):
    """One rule edited. `rule` holds what «Guardar» built; `deleted` says «Borrar» was pressed."""

    def __init__(self, parent: object, title: str, facts: list[dict], rule: dict | None = None,
                 nested: bool = False) -> None:
        """Build the form and fill it.

        Args:
            parent: The widget the dialog opens over.
            title: The window title, naming the step.
            facts: `{fact, label, sqx}`, the step's menu.
            rule: The rule being changed; None for a new one.
            nested: A compound's part: no compound inside, no name, no delete.
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(760)
        self.facts, self.rule, self.deleted = facts, None, False
        self.by = (rule or {}).get("by")
        self.parts: list[dict] = list((rule or {}).get("all") or (rule or {}).get("any") or [])
        self.kind = QComboBox()
        self.kind.addItems(KINDS[:COMPOUND] if nested else KINDS)
        self.fact = QComboBox(editable=True)
        self.shape, self.op, self.lop = QComboBox(), QComboBox(), QComboBox()
        self.shape.addItems(["Umbral", "Cerca de la mediana"])
        self.op.addItems(OPS)
        self.lop.addItems(OPS)
        self.value, self.lvalue, self.name = QLineEdit(), QLineEdit(), QLineEdit()
        self.want, self.miss, self.join = QComboBox(), QComboBox(), QComboBox()
        self.want.addItems(["Aprobado", "Suspenso"])
        self.miss.addItems(["Fallo", "Limbo (nunca elimina)"])
        self.join.addItems(["Todas las condiciones", "Alguna de las condiciones"])
        self.list = QListWidget()
        self.list.setFixedHeight(110)
        add, drop = QPushButton("Añadir condición"), QPushButton("Quitar condición")
        add.setToolTip("Añade una condición a la regla compuesta: un número o un veredicto.")
        drop.setToolTip("Quita de la regla compuesta la condición seleccionada.")
        add.clicked.connect(self.add_part)
        drop.clicked.connect(self.drop_part)
        self.buttons = QHBoxLayout()
        self.buttons.addWidget(add)
        self.buttons.addWidget(drop)
        self.buttons.addStretch(1)
        self.form = QFormLayout()
        self.rows = {"kind": self.kind, "name": self.name, "fact": self.fact, "shape": self.shape,
                     "pass": self.pair(self.op, self.value), "want": self.want,
                     "limbo": self.pair(self.lop, self.lvalue), "miss": self.miss,
                     "join": self.join, "parts": self.list, "edit": self.buttons}
        labels = {"kind": "Tipo", "name": "Nombre", "fact": "Dato", "shape": "Forma",
                  "pass": "Pasa si", "want": "Tiene que decir", "limbo": "Limbo si",
                  "miss": "Si no cumple", "join": "Unir con", "parts": "Condiciones", "edit": ""}
        for key, field in self.rows.items():
            label = QLabel(labels[key])
            label.setToolTip(HELP.get(key, ""))
            if hasattr(field, "setToolTip"):
                field.setToolTip(HELP.get(key, ""))
            self.form.addRow(label, field)
        self.note = QLabel("")
        self.note.setWordWrap(True)
        self.note.setStyleSheet(f"color: {C['weak']};")
        save, cancel = QPushButton("Guardar"), QPushButton("Cancelar")
        delete = QPushButton("Borrar")
        save.setDefault(True)
        save.clicked.connect(self.save)
        cancel.clicked.connect(self.reject)
        delete.clicked.connect(self.delete)
        delete.setToolTip("Borra este criterio del paso. Queda anotado en el historial.")
        delete.setVisible(rule is not None and not nested)
        foot = QHBoxLayout()
        foot.addWidget(delete)
        foot.addStretch(1)
        foot.addWidget(cancel)
        foot.addWidget(save)
        lay = QVBoxLayout(self)
        lay.addLayout(self.form)
        lay.addWidget(self.note)
        lay.addLayout(foot)
        self.nested = nested
        self.fill(rule or {})
        self.kind.currentIndexChanged.connect(self.arrange)
        self.shape.currentIndexChanged.connect(self.arrange)
        self.arrange()

    def pair(self, op: QComboBox, value: QLineEdit) -> QHBoxLayout:
        """A comparator and its number on one row."""
        op.setFixedWidth(80)
        row = QHBoxLayout()
        row.addWidget(op)
        row.addWidget(value, 1)
        return row

    def fill(self, rule: dict) -> None:
        """Put a rule into the form; an empty one leaves the defaults."""
        fact = rule.get("fact", "")
        sqx = next((f["sqx"] for f in self.facts if f["fact"] == fact), False)
        kind = COMPOUND if self.parts else VERDICT if "is" in rule else SQX if sqx else APP
        self.kind.setCurrentIndex(kind if rule else APP)
        self.name.setText(rule.get("name", ""))
        self.join.setCurrentIndex(1 if "any" in rule else 0)
        self.want.setCurrentIndex(1 if rule.get("is") == "fail" else 0)
        self.miss.setCurrentIndex(1 if rule.get("else") == "limbo" else 0)
        self.shape.setCurrentIndex(1 if "near_median" in rule else 0)
        if "near_median" in rule:
            self.value.setText(f"{100 * rule['near_median']:g}")
            if "limbo_near_median" in rule:
                self.lvalue.setText(f"{100 * rule['limbo_near_median']:g}")
        for key, op, value in (("pass", self.op, self.value), ("limbo", self.lop, self.lvalue)):
            if key in rule:
                sign, _, number = str(rule[key]).partition(" ")
                op.setCurrentText(sign)
                value.setText(number)
        self.list.addItems([told(p) for p in self.parts])
        self.wanted = fact

    def arrange(self) -> None:
        """Show the rows the chosen type uses, and list the facts that type offers."""
        kind, median = self.kind.currentIndex(), self.shape.currentIndex() == 1
        number = kind in (SQX, APP)
        shown = {"kind": True, "name": not self.nested, "fact": kind != COMPOUND, "shape": number,
                 "pass": number, "limbo": number, "want": kind == VERDICT,
                 "miss": kind != COMPOUND, "join": kind == COMPOUND, "parts": kind == COMPOUND,
                 "edit": kind == COMPOUND}
        for key, on in shown.items():
            self.form.setRowVisible(self.rows[key], on)
        self.op.setVisible(number and not median)
        self.lop.setVisible(number and not median)
        self.value.setPlaceholderText("% de la mediana, p. ej. 20" if median else "número")
        self.lvalue.setPlaceholderText("% de la mediana (opcional)" if median
                                       else "número (opcional)")
        offered = [f for f in self.facts if kind == VERDICT or f["sqx"] == (kind == SQX)]
        typed = self.fact.currentText() or self.wanted
        self.fact.clear()
        for f in offered:
            self.fact.addItem(f"{f['label']}   ·   {f['fact']}", f["fact"])
        at = self.fact.findData(typed)
        self.fact.setCurrentIndex(at)
        if at < 0:
            self.fact.setEditText(typed)
        by = f" Sus excepciones ({', '.join(self.by)}) se conservan: se editan en " \
             "criteria.yaml." if self.by else ""
        none = "Este paso no tiene métricas de SQX entre sus datos: escribe la clave a mano, " \
               "o usa un test de la app." if kind == SQX and not offered else ""
        self.note.setText(none + by)

    def add_part(self) -> None:
        """Open the same dialog for one condition of the compound and append what it built."""
        part = RuleDialog(self, "Condición de la regla compuesta", self.facts, nested=True)
        if part.exec() and part.rule:
            self.parts.append(part.rule)
            self.list.addItem(told(part.rule))

    def drop_part(self) -> None:
        """Remove the selected condition of the compound."""
        at = self.list.currentRow()
        if at >= 0:
            self.list.takeItem(at)
            del self.parts[at]

    def built(self) -> dict:
        """The rule the form says, in criteria.yaml's shape. A box that is not a number raises
        ValueError; everything else is the daemon's to refuse."""
        kind = self.kind.currentIndex()
        name = {"name": self.name.text().strip()} if self.name.text().strip() else {}
        if kind == COMPOUND:
            return name | {("all", "any")[self.join.currentIndex()]: self.parts}
        at = self.fact.findText(self.fact.currentText())
        rule = name | {"fact": self.fact.itemData(at) if at >= 0
                       else self.fact.currentText().strip()}
        value, limbo = (w.text().strip().replace(",", ".") for w in (self.value, self.lvalue))
        if kind == VERDICT:
            rule["is"] = ("pass", "fail")[self.want.currentIndex()]
        elif self.shape.currentIndex() == 1:
            rule["near_median"] = float(value) / 100
            if limbo:
                rule["limbo_near_median"] = float(limbo) / 100
        else:
            float(value), float(limbo or 0)
            rule["pass"] = f"{self.op.currentText()} {value}"
            if limbo:
                rule["limbo"] = f"{self.lop.currentText()} {limbo}"
        if self.miss.currentIndex() == 1:
            rule["else"] = "limbo"
        return rule | ({"by": self.by} if self.by else {})

    def save(self) -> None:
        """Close with the rule built, or say which box is not a number."""
        try:
            self.rule = self.built()
        except ValueError:
            self.note.setText("El valor tiene que ser un número (y el de limbo, un número o "
                              "nada).")
            return
        self.accept()

    def delete(self) -> None:
        """Close saying the rule goes."""
        self.deleted = True
        self.accept()
