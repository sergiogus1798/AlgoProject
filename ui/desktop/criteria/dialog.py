"""The dialog that adds or changes one criterion: a number, a verdict or a compound of them."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QComboBox, QDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
                               QListWidget, QPushButton, QVBoxLayout)

from ui.desktop.criteria.overrides import HELP, KNOWN, by_built, by_line, by_rows, told
from ui.desktop.theme import C

KINDS = ("Métrica SQX", "Test de la app", "Veredicto", "Compuesto")
SQX, APP, VERDICT, COMPOUND = range(4)
OPS = (">=", ">", "<=", "<", "==")
class RuleDialog(QDialog):
    """One rule edited. `rule` holds what «Guardar» built; `deleted` says «Borrar» was pressed."""

    def __init__(self, parent: object, title: str, facts: list[dict], rule: dict | None = None,
                 nested: bool = False, why: str = "") -> None:
        """Build the form and fill it.

        Args:
            parent: The widget the dialog opens over.
            title: The window title, naming the step.
            facts: `{fact, label, sqx}`, the step's menu.
            rule: The rule being changed; None for a new one.
            nested: A compound's part: no compound inside, no name, no delete.
            why: The comment criteria.yaml carries above the rule: the rule's own sentence.
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(760)
        self.facts, self.rule, self.deleted = facts, None, False
        self.by = (rule or {}).get("by")
        self.rest = {k: v for k, v in (rule or {}).items() if k not in KNOWN}   # kept as found
        self.had_missing = "missing" in (rule or {})
        self.cell = dict(rule) if rule and "alpha" in rule else None     # per-cell: returned as found
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
        self.absent = QComboBox()
        self.absent.addItems(["Limbo", "Fallo", "Pasa"])
        self.list = QListWidget()
        self.list.setFixedHeight(110)
        add, drop = QPushButton("Añadir condición"), QPushButton("Quitar condición")
        add.setToolTip("Añade una condición a la regla compuesta: un número o un veredicto.")
        drop.setToolTip("Quita de la regla compuesta la condición seleccionada.")
        add.clicked.connect(self.add_part)
        drop.clicked.connect(self.drop_part)
        self.by_box, self.by_lines = QVBoxLayout(), []
        grow = QPushButton("+", clicked=lambda: self.add_by("", "", ""), maximumWidth=40)
        self.by_box.addWidget(grow, alignment=Qt.AlignLeft)
        self.buttons = QHBoxLayout()
        for w in (add, drop):
            self.buttons.addWidget(w)
        self.buttons.addStretch(1)
        self.form = QFormLayout()
        self.rows = {"kind": self.kind, "name": self.name, "fact": self.fact, "shape": self.shape,
                     "pass": self.pair(self.op, self.value), "want": self.want,
                     "limbo": self.pair(self.lop, self.lvalue), "miss": self.miss,
                     "absent": self.absent, "by": self.by_box, "join": self.join, "parts": self.list, "edit": self.buttons}
        labels = {"kind": "Tipo", "name": "Nombre", "fact": "Dato", "shape": "Forma",
                  "pass": "Pasa si", "want": "Tiene que decir", "limbo": "Limbo si",
                  "miss": "Si no cumple", "absent": "Si falta el dato", "by": "Ajustes por activo o temporalidad", "join": "Unir con", "parts": "Condiciones", "edit": ""}
        for key, field in self.rows.items():
            label = QLabel(labels[key], toolTip=HELP.get(key, ""))
            if hasattr(field, "setToolTip"):
                field.setToolTip(HELP.get(key, ""))
            self.form.addRow(label, field)
        self.note = QLabel("")
        self.note.setWordWrap(True)
        self.note.setStyleSheet(f"color: {C['weak']};")
        save, cancel, delete = QPushButton("Guardar"), QPushButton("Cancelar"), QPushButton("Borrar")
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
        if why:
            sentence = QLabel(why)
            sentence.setWordWrap(True)
            sentence.setStyleSheet(f"color: {C['weak']};")
            lay.addWidget(sentence)
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
        self.absent.setCurrentText({"limbo": "Limbo", "fail": "Fallo", "pass": "Pasa"}[
            rule.get("missing", "limbo")])
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
        if "alpha" in rule:      # the judge computes the line from B: nothing to type here
            self.value.setText("por celda: Φ⁻¹(1 − α/B)")
            self.value.setEnabled(False)
            self.lvalue.setEnabled(False)
        self.list.addItems([told(p) for p in self.parts])
        for row in by_rows(rule.get("by")):
            self.add_by(*row)
        self.wanted = fact

    def arrange(self) -> None:
        """Show the rows the chosen type uses, and list the facts that type offers."""
        kind, median = self.kind.currentIndex(), self.shape.currentIndex() == 1
        number = kind in (SQX, APP)
        shown = {"kind": True, "name": not self.nested, "fact": kind != COMPOUND, "shape": number,
                 "pass": number, "limbo": number, "want": kind == VERDICT,
                 "miss": kind != COMPOUND, "absent": kind != COMPOUND, "join": kind == COMPOUND, "parts": kind == COMPOUND,
                 "edit": kind == COMPOUND, "by": kind != COMPOUND}
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
        by = f" Sus excepciones ({', '.join(self.by)}) se conservan: se editan en criteria.yaml." \
            if self.by and kind == COMPOUND else ""
        none = "Este paso no tiene métricas de SQX entre sus datos: escribe la clave a mano, " \
               "o usa un test de la app." if kind == SQX and not offered else ""
        self.note.setText(none + by)

    def add_by(self, key: str, passes: str, limbo: str) -> None:
        """One override row: key, pass text, limbo text and the «−» that deletes it."""
        boxes, line, drop = by_line(key, passes, limbo)
        drop.clicked.connect(lambda: (self.by_lines.remove(boxes), line.deleteLater()))
        self.by_lines.append(boxes)
        self.by_box.insertWidget(self.by_box.count() - 1, line)

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
        if self.cell is not None:
            return self.cell
        kind = self.kind.currentIndex()
        name = {"name": self.name.text().strip()} if self.name.text().strip() else {}
        if kind == COMPOUND:
            return name | {("all", "any")[self.join.currentIndex()]: self.parts} | self.rest
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
        gone = {"Limbo": "limbo", "Fallo": "fail", "Pasa": "pass"}[self.absent.currentText()]
        if gone != "limbo" or self.had_missing:
            rule["missing"] = gone
        by = self.by if kind == COMPOUND else by_built(
            [tuple(b.text() for b in line) for line in self.by_lines], self.by)
        return rule | ({"by": by} if by else {}) | self.rest

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
