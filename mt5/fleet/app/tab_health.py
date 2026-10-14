"""The Salud tab: each terminal's connection, ping, build and errors, and the VPS they share."""
from PySide6.QtWidgets import QVBoxLayout, QWidget

from mt5.fleet.app import fmt, health, history, read, theme, widgets
from mt5.fleet.app.widgets import cell

COLUMNS = ["Cuenta", "Conectado", "Ping", "Build", "Desconexiones hoy", "Servicio activo", "Último error"]
LEGEND = (
    "<b>Conectado</b>: el terminal habla con el servidor de la firma ahora. <b>Ping</b>: ida y vuelta al servidor, "
    "en milisegundos; por encima de unos 150 ms el EA entra tarde. <b>Build</b>: versión del terminal. "
    "<b>Desconexiones hoy</b>: veces que el terminal pasó a desconectado desde medianoche del servidor y, entre "
    "paréntesis, los minutos que estuvo así; sale del histórico del colector, que mira una vez por minuto, así que "
    "un corte de segundos no cuenta. <b>Servicio activo</b>: cuánto lleva el servicio FleetBeacon sin reiniciarse "
    "(si se reinicia pierde las horas y los extremos que guardaba en memoria). <b>Último error</b>: la última "
    "línea del registro del terminal que trae un error, según la lectura de la VPS; las diez últimas están debajo. "
    "<b>RAM, CPU, disco</b>: de la máquina Windows donde corren los terminales, cada cinco minutos; con la RAM "
    "o el disco casi llenos los terminales se caen. Todo esto sólo existe cuando el colector lo trae.")


class HealthTab(QWidget):
    """The tab's cards, table and error lists."""

    def __init__(self) -> None:
        """Build the empty tab."""
        super().__init__()
        self.cards = [widgets.card(n) for n in ("RAM libre", "CPU", "Disco libre", "En marcha desde hace")]
        self.strip = widgets.strip([c for c, _ in self.cards])
        self.empty, self.table = widgets.label("", "empty", True), widgets.table(COLUMNS, "Último error")
        self.errors = widgets.label("", "notes", True)
        scroll, _ = widgets.page([self.empty, self.strip, widgets.label("Terminales", "section"), self.table,
                                  self.errors], LEGEND)
        box = QVBoxLayout(self)
        box.addWidget(scroll)
        box.setContentsMargins(0, 0, 0, 0)

    def paint(self, rows: list[dict]) -> None:
        """Show the health of these rows' terminals and of the VPS."""
        vps = read.vps()
        self.empty.setVisible(vps is None)
        self.empty.setText("El colector aún no ha escrito <code>vps.json</code>: no hay lecturas de la máquina "
                           "(RAM, CPU, disco) ni de los registros de los terminales.")
        self.strip.setVisible(vps is not None)
        for (_, value), (_, text) in zip(self.cards, health.machine(vps)):
            value.setText(text)
        lines, errors = [], []
        for r in rows:
            beat = r["beat"]
            mins = history.minutes(beat["login"], [beat["day_start"]])
            t = health.terminal(beat, mins, vps)
            d = t["disconnections"]
            who = fmt.who(beat, r['stage'])
            lines.append([cell(who, right=False), cell("sí" if t["connected"] else "NO", None if t["connected"]
                                                       else theme.LIGHTS["red"]),
                          cell(f"{t['ping_ms']:.0f} ms", theme.LIGHTS["yellow"] if t["ping_ms"] > 150 else None),
                          cell(str(t["build"])), cell(fmt.DASH if d is None else f"{d[0]} ({d[1]} min)"),
                          cell(fmt.DASH if t["uptime_s"] is None else fmt.span(t["uptime_s"])),
                          cell(t["errors"][-1][:90] if t["errors"] else fmt.DASH, right=False)])
            errors += [f"<b>{who}</b>: {e}" for e in t["errors"]]
        widgets.fill(self.table, lines)
        self.errors.setText("<br>".join(errors))
        self.errors.setVisible(bool(errors))
