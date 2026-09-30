"""«+ Nuevo proyecto»: the form under Proyectos' header that creates a workflow project."""

from PySide6.QtWidgets import (QComboBox, QFormLayout, QFrame, QLineEdit, QPushButton, QSpinBox,
                               QVBoxLayout)

from ui.desktop import background
from ui.desktop.jobbutton import JobButton
from ui.desktop.theme import C

CONFIRM = ("Crear «{name}» en el custodio: {template} sobre {symbol} {tf}, todas las tareas del "
           "workflow (builder --workflow), build de hasta {n} estrategias o {m} min. Antes corre "
           "core.assets {symbol} (regla 5) y se para si no pasa. No arranca SQX. ¿Crear?")


class NewProject(QFrame):
    """A toggle and the form it opens: template, asset, timeframe, name (suggested
    `Test_<SYMBOL>_<template>_<TF>`), strategies, minutes, purpose; its JobButton queues
    `POST /api/create/project`. `created(name)` when the job ended well."""

    def __init__(self, created: object) -> None:
        """Build the toggle; the choices come from `/api/create/options` the first time."""
        super().__init__()
        self.setObjectName("term")
        self.created = created
        self.toggle = QPushButton("+ Nuevo proyecto")
        self.toggle.clicked.connect(self.open)
        self.form = QFrame()
        self.form.setVisible(False)
        rows = QFormLayout(self.form)
        self.template, self.symbol, self.tf = QComboBox(), QComboBox(), QComboBox()
        self.name, self.purpose = QLineEdit(), QLineEdit()
        self.n, self.m = QSpinBox(), QSpinBox()
        self.n.setRange(10, 100000)
        self.m.setRange(5, 2880)
        for box in (self.template, self.symbol, self.tf):
            box.currentTextChanged.connect(self.suggest)
        for label, w in (("Plantilla", self.template), ("Activo", self.symbol),
                         ("Timeframe", self.tf), ("Nombre", self.name),
                         ("Estrategias máx. del build", self.n), ("Minutos máx. del build", self.m),
                         ("Para qué (una frase)", self.purpose)):
            rows.addRow(label, w)
        self.go = JobButton("Crear proyecto", "create/project", self.body, self.confirm,
                            lambda job: job["rc"] == 0 and self.created(self.name.text()))
        rows.addRow(self.go)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.toggle)
        lay.addWidget(self.form)

    def open(self) -> None:
        """Show or hide the form; the first time, ask the daemon for its choices."""
        self.form.setVisible(not self.form.isVisible())
        if self.form.isVisible() and not self.template.count():
            background.get("create/options", self.fill, owner=self)

    def fill(self, got: dict) -> None:
        """The choices arrived: fill the combos and the defaults."""
        if "error" in got:
            self.go.say(got["error"], C["dead"])
            return
        self.template.addItems(got["templates"])
        self.symbol.addItems(got["symbols"])
        self.tf.addItems(got["timeframes"])
        self.n.setValue(got["max_strategies"])
        self.m.setValue(got["minutes"])

    def suggest(self) -> None:
        """The name rule 6 accepts, from the three choices; the owner may edit it."""
        self.name.setText(f"Test_{self.symbol.currentText()}_{self.template.currentText()}_"
                          f"{self.tf.currentText()}")

    def body(self) -> dict:
        """The form as `POST /api/create/project` reads it."""
        return {"name": self.name.text().strip(), "template": self.template.currentText(),
                "symbol": self.symbol.currentText(), "timeframe": self.tf.currentText(),
                "max_strategies": self.n.value(), "minutes": self.m.value(),
                "purpose": self.purpose.text().strip()}

    def confirm(self) -> str | None:
        """The confirmation sentence, or None (said under the button) when the form is short."""
        b = self.body()
        if not b["name"] or not b["purpose"]:
            self.go.say("falta el nombre o el «para qué»", C["dead"])
            return None
        return CONFIRM.format(name=b["name"], template=b["template"], symbol=b["symbol"],
                              tf=b["timeframe"], n=b["max_strategies"], m=b["minutes"])
