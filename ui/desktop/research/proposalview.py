"""The proposal: three ideas side by side, a veto each, their open questions, the launch and the queue."""

from collections.abc import Callable

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (QCheckBox, QFrame, QHBoxLayout, QLabel, QLineEdit,
                               QMessageBox, QPushButton, QScrollArea, QVBoxLayout, QWidget)

from ui.desktop.blocks.card import text
from ui.desktop.research import parts
from ui.desktop.research.parts import esc as e
from ui.desktop.theme import C, T

POLL_MS = 15_000
STATE = {"en marcha": C["accent"], "hecha": C["promising"], "falló": C["dead"],
         "pregunta": C["weak"], "vetada": T["faint"], "esperando": T["muted"]}
QUEUE = [("Idea", ""), ("Estado", "esperando · en marcha · hecha · falló · pregunta · vetada"),
         ("Paso", "activos → plantilla → proyecto → paleta → autopilot"), ("Proyecto", ""),
         ("Nota", "")]


class ProposalView(QWidget):
    """Diagnosis on top, the ideas in columns, then the launch row and the queue."""

    def __init__(self, fetch: Callable[..., dict], send: Callable[[str, dict], dict],
                 sync: bool) -> None:
        """Build the frame; the columns are drawn when a proposal lands."""
        super().__init__()
        self.fetch, self.send, self.sync, self.p = fetch, send, sync, {}
        self.head = text("Todavía no hay ninguna propuesta: pulsa «Proponer investigación».",
                         T["text"], 14)
        self.columns = QHBoxLayout()
        holder = QWidget()
        holder.setLayout(self.columns)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(holder)
        self.button = QPushButton("▶ Crear plantillas y lanzar en SQX", objectName="primary")
        self.button.setProperty("help", "Encadena, idea a idea en el custodio: core.assets, "
                                        "templateArchitect, proyecto, buildingBlocksExpert y "
                                        "autopilot. Pide confirmación.")
        self.button.clicked.connect(self.launch)
        self.why = text("", C["weak"], 13)
        row = QHBoxLayout()
        row.addWidget(self.button)
        row.addWidget(self.why, 1)
        self.queue = parts.table(QUEUE)
        self.queue.setMaximumHeight(150)
        lay = QVBoxLayout(self)
        lay.addWidget(self.head)
        lay.addWidget(scroll, 1)
        lay.addLayout(row)
        lay.addWidget(QLabel("LA COLA: QUÉ IDEA ESTÁ EN EL CUSTODIO Y CUÁLES ESPERAN",
                             objectName="kicker"))
        lay.addWidget(self.queue)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.poll)

    def reload(self) -> None:
        """Read the newest proposal."""
        parts.call(self, lambda: self.fetch("research/proposal"), self.paint, "research-proposal")

    def paint(self, p: dict) -> None:
        """Draw the diagnosis and one column per idea."""
        if "error" in p or p.get("none"):
            self.head.setText(p.get("error") or self.head.text())
            self.button.setEnabled(False)
            return
        self.p = p
        c, b = p["cell"], p["board"]
        warn = ("<br><b style='color:%s'>COSTES PROVISIONALES</b>: el filtro «paga el doble del "
                "coste» se midió contra un coste que puede cambiar." % C["weak"]
                if p["provisional_costs"] else "")
        self.head.setText(
            f"<b style='font-size:17px;color:{parts.FAMILY[c['family']]}'>{c['symbol']} "
            f"{c['timeframe']} {c['direction']} · {c['family']}</b> — puesto {b['rank']} del "
            f"tablero, " + ("efecto sin medir (entra por la prior)" if b["trades_per_year"] is None
                         else f"{b['multiple']}x el coste, {b['trades_per_year']} op/año") + "<br>"
            f"{e(p['diagnosis'])}<br>" + (f"<i>Se aparta del tablero: {e(p['departs'])}</i><br>"
                                       if p.get("departs") else "")
            + f"<b>Ya van {p['ideas_spent']} idea(s)</b> en esta celda antes de estas tres. "
            + " ".join(p["standing_costs"]) + warn)
        while self.columns.count():
            self.columns.takeAt(0).widget().deleteLater()
        for idea in p["ideas"]:
            self.columns.addWidget(self.column(idea))
        self.check()
        self.poll()

    def column(self, i: dict) -> QFrame:
        """One idea: veto, rule, mechanism, palette, custom blocks, cost, failure, questions."""
        box = QFrame(objectName="panel")
        lay = QVBoxLayout(box)
        lay.addWidget(QLabel(i["name"], objectName="h2"))
        veto = QCheckBox("Vetar esta idea")
        veto.setChecked(bool(i.get("vetoed")))
        veto.toggled.connect(lambda on, name=i["name"]: self.change(
            "research/veto", {"id": self.p["id"], "idea": name, "vetoed": on}))
        lay.addWidget(veto)
        families = "<br>".join(f"&nbsp;&nbsp;peso {f['weight']} · {f['family']}: {e(f['reason'])}"
                               for f in i["palette"].get("families", []))
        custom = "<br>".join(f"&nbsp;&nbsp;{b['name']}: {e(b['what'])}"
                             for b in i["custom_blocks"]) or "&nbsp;&nbsp;ninguno"
        quarry = i["quarry"] + (f" ({e(i['source'])})" if i.get("source") else "")
        lay.addWidget(text(
            f"<b>Regla exacta</b><br>{e(i['rule'])}<br><br><b>Mecanismo</b><br>{e(i['mechanism'])}<br><br>"
            f"<b>Cantera</b>: {quarry} · <b>Dirección</b>: {i['direction']} · <b>Custodio</b>: "
            f"unas {i['custodian_hours']} h<br><br><b>El hueco libre</b>: "
            f"{e(i['palette'].get('role', ''))}<br>{families}<br><br><b>Bloques custom a crear</b><br>"
            f"{custom}<br><br><b>Cómo puede fallar</b><br>{e(i['failure'])}", T["text"], 13))
        for n, q in enumerate(i["questions"]):
            lay.addWidget(text(f"<b>PREGUNTA</b>: {e(q['question'])}<br>" + "<br>".join(
                f"&nbsp;&nbsp;{k}) {e(r)}" for k, r in enumerate(q["readings"], 1)), C["weak"], 13))
            field = QLineEdit(q.get("answer") or "", placeholderText="Tu respuesta, y Enter")
            field.editingFinished.connect(lambda f=field, name=i["name"], n=n: f.text().strip()
                                          and self.change("research/answer", {
                                              "id": self.p["id"], "idea": name, "question": n,
                                              "text": f.text()}))
            lay.addWidget(field)
        state = "SE PUEDE LANZAR" if i["launchable"] else f"NO SE LANZA: {e(i['why_not'])}"
        lay.addWidget(text(state, C["promising"] if i["launchable"] else C["weak"], 13, True))
        lay.addStretch(1)
        return box

    def change(self, path: str, body: dict) -> None:
        """Send a veto or an answer and redraw what came back."""
        got = self.send(path, body)
        self.paint({**got, "ids": self.p.get("ids", [])} if "error" not in got else got)

    def check(self) -> None:
        """Ask whether the queue may start now; the button follows the answer."""
        if self.p:
            parts.call(self, lambda: self.fetch("research/launch", id=self.p["id"]),
                       self.checked, "research-launch")

    def checked(self, got: dict) -> None:
        """Enable the button only when the preflight passes; say why otherwise."""
        self.button.setEnabled(bool(got.get("ok")))
        self.why.setText(got.get("error") or " · ".join(got.get("reasons", [])))

    def launch(self) -> None:
        """Fresh preflight, its sentence, and only on «Sí» the POST the daemon re-checks."""
        got = self.fetch("research/launch", id=self.p["id"])
        self.checked(got)
        if not got.get("ok"):
            return
        if QMessageBox.question(self, "Crear plantillas y lanzar en SQX",
                                got["text"] + "\n\n¿Confirmas?", QMessageBox.Yes | QMessageBox.No,
                                QMessageBox.No) != QMessageBox.Yes:
            return
        sent = self.send("research/launch", {"id": self.p["id"], "ideas": got["ideas"]})
        self.checked(sent if not sent.get("job") else {"ok": False, "reasons": [
            "En marcha: sigue la cola aquí abajo y el detalle en «En marcha»"]})
        self.poll()

    def poll(self) -> None:
        """Read the queue of the proposal on screen."""
        if self.p:
            parts.call(self, lambda: self.fetch("research/queue", id=self.p["id"]), self.queued,
                       "research-queue")

    def queued(self, got: dict) -> None:
        """Fill the queue table; keep polling while its job lives."""
        ideas = (got.get("queue") or {}).get("ideas", [])
        parts.fill(self.queue, [[i["name"], i["state"], i["step"] or "—", i["project"] or "—",
                                 i["error"] or i["note"] or "—"] for i in ideas],
                   [STATE.get(i["state"]) for i in ideas])
        if got.get("job") and not self.sync:
            self.timer.start(POLL_MS)
        else:
            self.timer.stop()
