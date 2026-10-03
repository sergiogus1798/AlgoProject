"""The Estrategias tab: every live magic over all accounts, and the same magic's entries paired across accounts."""
from PySide6.QtWidgets import QVBoxLayout, QWidget

from mt5.fleet.app import fmt, history, read, strategies, theme, widgets
from mt5.fleet.app.widgets import cell, signed

RECORD = ["Estrategia", "Magic", "Cuentas", "Operaciones", "Resultado neto", "% acierto", "Peor flotante (MAE)",
          "Primera operación"]
PAIRS = ["Estrategia", "Magic", "Cuentas", "Entradas gemelas", "Sin gemela"]
OPEN = ["Estrategia", "Magic", "Cuenta", "Símbolo", "Lado", "Volumen", "Abierta (servidor)", "Flotante",
        "Peor flotante (MAE)", "Mejor flotante (MFE)"]
LONELY = ["Estrategia", "Hora (servidor)", "Lado", "Entró en", "Le falta a"]
LEGEND = (
    "<b>Abiertas ahora</b>: las posiciones abiertas de todas las cuentas, por estrategia. <b>Flotante</b>: su "
    "resultado ahora. <b>Peor y mejor flotante</b>: lo más bajo y lo más alto que ha estado desde que el colector "
    "la ve, una lectura por minuto: no cuenta lo anterior al colector ni una punta de segundos.<br>"
    "<b>Operaciones</b>: operaciones cerradas con ese magic, sumadas en todas las cuentas. <b>Resultado neto</b>: "
    "suma de beneficio, swap y comisiones de esas operaciones, en la divisa de cada cuenta. <b>% acierto</b>: "
    "operaciones cerradas con resultado neto positivo; con menos de 30 operaciones no significa nada. <b>Peor "
    "flotante (MAE)</b>: lo más bajo que llegó a estar el resultado flotante de una posición suya, medido por el "
    "colector una vez por minuto, así que una caída de segundos puede no verse; sale «—» hasta que el colector "
    "escriba las excursiones. <b>Primera operación</b>: cuándo entró por primera vez en cualquier cuenta.<br>"
    "<b>Entradas gemelas</b>: la misma estrategia (mismo magic) en dos o más cuentas debería entrar a la vez. Dos "
    "entradas se emparejan si son del mismo lado y se abren con menos de los minutos de tolerancia entre sí "
    "(<code>pair_tolerance_min</code>), mirando los últimos <code>pair_days</code> días. <b>Sin gemela</b>: "
    "entradas que alguna cuenta no hizo. Desconfía de las cuentas que empezaron a operar después, y de las "
    "firmas con tamaños distintos, que pueden tardar más en ejecutar: una entrada sin gemela es una pregunta, "
    "no un error.")


class StrategiesTab(QWidget):
    """The tab's tables and the message that stands in for them while the collector has written nothing."""

    def __init__(self) -> None:
        """Build the empty tab."""
        super().__init__()
        self.empty = widgets.label("", "empty", True)
        self.record, self.pairs = widgets.table(RECORD, "Estrategia"), widgets.table(PAIRS, "Estrategia")
        self.lonely, self.open = widgets.table(LONELY, "Estrategia"), widgets.table(OPEN, "Estrategia")
        self.open_head = widgets.label("Abiertas ahora", "section")
        self.heads = [widgets.label(t, "section") for t in
                      ("Cada estrategia en vivo", "Misma estrategia en varias cuentas", "Entradas sin gemela")]
        scroll, _ = widgets.page([self.open_head, self.open, self.empty, self.heads[0], self.record, self.heads[1],
                                  self.pairs, self.heads[2], self.lonely], LEGEND)
        QVBoxLayout(self).addWidget(scroll)
        self.layout().setContentsMargins(0, 0, 0, 0)

    def paint(self, rows: list[dict], now: int) -> None:
        """Show the strategies of these rows as of `now` (UTC epoch)."""
        accounts = strategies.accounts(rows)
        register = {m: s for (_, m), s in read.names().items()}
        self.paint_open(rows, register)
        self.empty.setVisible(not accounts)
        self.empty.setText("Las operaciones cerradas y la comparación entre cuentas necesitan el historial completo "
                           "de cada cuenta, que sólo envía el servicio de la versión 2: en cada terminal de la VPS, "
                           "Navegador → Servicios → FleetBeacon → Detener y después Iniciar.")
        for w in (*self.heads, self.record, self.pairs, self.lonely):
            w.setVisible(bool(accounts))
        if not accounts:
            return
        widgets.fill(self.record, [[
            cell(r["strategy"], right=False), cell(str(r["magic"])), cell(str(r["accounts"])), cell(str(r["trades"])),
            signed(r["net"]), cell(fmt.pct(r["win_rate"], 0)), signed(r["worst_mae"]),
            cell(fmt.clock(r["first"]))] for r in strategies.record(accounts, register)])
        paired = strategies.pairing(accounts, register, now)
        widgets.fill(self.pairs, [[
            cell(p["strategy"], right=False), cell(str(p["magic"])), cell(", ".join(p["accounts"]), right=False),
            cell(str(p["complete"])), cell(str(len(p["lonely"])), theme.LIGHTS["yellow"] if p["lonely"] else None)]
            for p in paired])
        widgets.fill(self.lonely, [[
            cell(p["strategy"], right=False), cell(fmt.clock(g["time"])), cell("Compra" if g["side"] == "buy" else "Venta",
                                                                                right=False),
            cell(", ".join(g["present"]), right=False), cell(", ".join(g["missing"]), theme.LIGHTS["yellow"],
                                                             right=False)] for p in paired for g in p["lonely"]])
        self.heads[1].setText("Misma estrategia en varias cuentas" + ("" if paired else
                              " — ninguna estrategia está en dos cuentas todavía"))
        self.pairs.setVisible(bool(paired))
        self.lonely.setVisible(any(p["lonely"] for p in paired))
        self.heads[2].setVisible(any(p["lonely"] for p in paired))

    def paint_open(self, rows: list[dict], register: dict[int, str]) -> None:
        """The open positions of every account, by strategy, with the collector's floating extremes."""
        lines = []
        for r in rows:
            beat, seen = r["beat"], history.excursions(r["beat"]["login"]) or {}
            name = (r["stage"]["firm"] if r["stage"] else beat["company"]) + f" {beat['login']}"
            for p in beat["positions"]:
                ex = seen.get(str(p["ticket"]))
                lines.append((register.get(p["magic"], p["comment"]), [
                    cell(register.get(p["magic"], p["comment"]), right=False), cell(str(p["magic"])),
                    cell(name, right=False), cell(p["symbol"], right=False),
                    cell("Compra" if p["side"] == "buy" else "Venta", right=False), cell(f"{p['volume']:g}"),
                    cell(fmt.clock(p["time"])), signed(p["profit"]),
                    signed(ex["min_profit"]) if ex else cell("—"), signed(ex["max_profit"]) if ex else cell("—")]))
        widgets.fill(self.open, [line for _, line in sorted(lines, key=lambda x: x[0])])
        self.open.setVisible(bool(lines))
        self.open_head.setText("Abiertas ahora" + ("" if lines else " — ninguna cuenta tiene posiciones abiertas"))
