"""The memory: today's coverage, the funnel of every attempt, and what each family has given."""

from collections.abc import Callable

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from ui.desktop.blocks.card import text
from ui.desktop.research import parts
from ui.desktop.theme import T

STAGE = {"built": "construidas", "oos": "tras OOS", "gate": "tras la criba",
         "markets": "tras otros mercados", "mcr": "tras MC Retest", "spp": "tras SPP",
         "survivors": "supervivientes"}
ATTEMPTS = [("Proyecto", ""), ("Plantilla", ""), ("Familia", ""), ("Celda", "Activo, marco y dirección."),
            ("Desenlace", "survivors: llegó al final con alguna · died@paso: la población murió "
                          "ahí · failed/incomplete: no concluyó · unknown: nunca corrió con el "
                          "autopilot."),
            ("Horas", "Horas de reloj en el custodio."),
            ("Embudo", "Estrategias que quedaban tras cada paso, en orden."),
            ("Veredicto", "El texto de runs.csv.")]
FAMILY = [("Familia", ""), ("Clase de activo", ""), ("Intentos", "Proyectos de esa familia."),
          ("Cerrados", "Intentos que acabaron con respuesta: murieron o sobrevivieron."),
          ("Con supervivientes", "Cerrados que dejaron al menos una estrategia."),
          ("Supervivientes", "Estrategias en total.")]


class MemoryView(QWidget):
    """Coverage in one sentence, then the two tables."""

    def __init__(self, fetch: Callable[..., dict], sync: bool) -> None:
        """Build the empty tables."""
        super().__init__()
        self.fetch, self.sync = fetch, sync
        self.cover = text("", T["text"], 15)
        self.attempts = parts.table(ATTEMPTS)
        self.family = parts.table(FAMILY)
        lay = QVBoxLayout(self)
        lay.addWidget(self.cover)
        lay.addWidget(QLabel("EL EMBUDO DE CADA INTENTO", objectName="kicker"))
        lay.addWidget(self.attempts, 3)
        lay.addWidget(QLabel("LO QUE HA DADO CADA FAMILIA, POR CLASE DE ACTIVO", objectName="kicker"))
        lay.addWidget(self.family, 1)

    def reload(self) -> None:
        """Read the memory again."""
        parts.call(self, lambda: self.fetch("research/memory"), self.paint, "research-memory")

    def paint(self, got: dict) -> None:
        """Fill the sentence and the tables."""
        if "error" in got:
            self.cover.setText(got["error"])
            return
        c = got["coverage"]
        self.cover.setText(
            f"<b>{c['cells'] - c['untouched']}</b> de {c['cells']} celdas (activo × marco × "
            f"dirección × familia) tienen algún intento · <b>{len(got['attempts'])}</b> intentos, "
            f"<b>{c['closed']}</b> cerrados con respuesta · <b>{got['ideas']}</b> ideas en el índice.")
        parts.fill(self.attempts, [
            [a["project"], a["template"], a["family"] or "—",
             f"{a['symbol']} {a['timeframe']} {a['direction']}",
             a["outcome"], a["custodian_hours"] or "—",
             " → ".join(f"{STAGE[f['stage']]} {int(f['n'])}" for f in a["funnel"]) or "sin embudo",
             a["verdict"] or "—"]
            for a in got["attempts"]],
            [parts.FAMILY.get(a["family"]) for a in got["attempts"]])
        parts.fill(self.family, [[r["family"], r["asset_class"], r["attempts"], r["closed"],
                                  r["with_survivors"], r["survivors"]] for r in got["by_family"]],
                   [parts.FAMILY.get(r["family"]) for r in got["by_family"]])
