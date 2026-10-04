"""The Estrategias tab: every live magic over all accounts, and the same magic's entries paired across accounts."""
from PySide6.QtWidgets import QCheckBox, QComboBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from mt5.fleet.app import chart, equity, fmt, history, read, strategies, theme, widgets
from mt5.fleet.app.widgets import cell, signed

RECORD = ["Estrategia", "Magic", "Cuentas", "Operaciones", "Net Profit", "Win Rate", "Peor flotante (MAE)",
          "Primera operación"]
PAIRS = ["Estrategia", "Magic", "Cuentas", "Entradas gemelas", "Sin gemela"]
OPEN = ["Estrategia", "Magic", "Cuenta", "Símbolo", "Lado", "Volumen", "Abierta (servidor)", "Flotante",
        "Peor flotante (MAE)", "Mejor flotante (MFE)"]
LONELY = ["Estrategia", "Hora (servidor)", "Lado", "Entró en", "Le falta a"]
CURVES = ["Cuenta", "Trades", "Net Profit", "Win Rate", "Max drawdown"]
UNITS = ["% del tamaño de la cuenta", "Divisa de la cuenta"]
LEGEND = (
    "<b>Curva por estrategia</b>: resultado neto acumulado (beneficio, swap y comisiones) de las operaciones "
    "cerradas con ese magic, una línea por cuenta que la lleva, con la hora del servidor en el eje X. En % del tamaño "
    "de la cuenta una de 10.000 y una de 100.000 son comparables. <b>Combinada</b>: la suma de las cuentas marcadas "
    "(en %, sobre la suma de sus tamaños). <b>Max drawdown</b>: la mayor caída desde un máximo de esa curva, en % del "
    "tamaño de la cuenta; cuenta sólo lo cerrado, no el flotante. Hace falta el historial de la cuenta (FleetBeacon v2).<br>"
    "<b>Abiertas ahora</b>: las posiciones abiertas de todas las cuentas, por estrategia. <b>Flotante</b>: su "
    "resultado ahora. <b>Peor y mejor flotante</b>: lo más bajo y lo más alto que ha estado desde que el colector "
    "la ve, una lectura por minuto: no cuenta lo anterior al colector ni una punta de segundos.<br>"
    "<b>Operaciones</b>: operaciones cerradas con ese magic, sumadas en todas las cuentas. <b>Net Profit</b>: "
    "suma de beneficio, swap y comisiones de esas operaciones, en la divisa de cada cuenta. <b>Win Rate</b>: "
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
        self.accounts, self.checked, self.listed, self.missing = [], {}, (), []
        self.strategy, self.unit, self.combined = QComboBox(), QComboBox(), QCheckBox("Combinada")
        self.unit.addItems(UNITS)
        self.picks = QHBoxLayout()
        controls = QWidget()
        bar = QHBoxLayout(controls)
        bar.setContentsMargins(0, 0, 0, 0)
        for w in (QLabel("Estrategia"), self.strategy, QLabel("Cuentas")):
            bar.addWidget(w)
        bar.addLayout(self.picks)
        bar.addWidget(self.combined)
        bar.addWidget(self.unit)
        bar.addStretch(1)
        self.strategy.currentIndexChanged.connect(self.draw)
        self.unit.currentIndexChanged.connect(self.draw)
        self.combined.toggled.connect(self.draw)
        self.canvas, self.curves = chart.LinesCanvas(), widgets.table(CURVES, "Cuenta")
        self.canvas.setMinimumHeight(380)
        self.eq_head, self.eq_notes = widgets.label("Curva de equity por estrategia", "section"), widgets.label(
            "", "notes", True)
        self.heads = [widgets.label(t, "section") for t in
                      ("Cada estrategia en vivo", "Misma estrategia en varias cuentas", "Entradas sin gemela")]
        scroll, _ = widgets.page([self.open_head, self.open, self.empty, self.eq_head, controls, self.canvas,
                                  self.curves, self.eq_notes, self.heads[0], self.record, self.heads[1],
                                  self.pairs, self.heads[2], self.lonely], LEGEND)
        QVBoxLayout(self).addWidget(scroll)
        self.layout().setContentsMargins(0, 0, 0, 0)

    def paint(self, rows: list[dict], now: int) -> None:
        """Show the strategies of these rows as of `now` (UTC epoch)."""
        accounts = strategies.accounts(rows)
        register = {m: s for (_, m), s in read.names().items()}
        self.paint_open(rows, register)
        self.paint_equity(rows, accounts, register)
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
            name = fmt.who(beat, r["stage"])
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

    def paint_equity(self, rows: list[dict], accounts: list[dict], register: dict[int, str]) -> None:
        """Refill the strategy and account pickers when they changed, then draw."""
        self.accounts = accounts
        magics = [(r["magic"], f"{r['strategy']} · magic {r['magic']}") for r in
                  sorted(strategies.record(accounts, register), key=lambda r: r["magic"])]
        self.missing = [fmt.who(r["beat"], r["stage"]) for r in rows if r["deals"] is None]
        logins = tuple(a["login"] for a in accounts)
        for w, items in ((self.strategy, magics),):
            if [w.itemData(i) for i in range(w.count())] != [m for m, _ in items]:
                w.blockSignals(True)
                keep = w.currentData()
                w.clear()
                for m, text in items:
                    w.addItem(text, m)
                w.setCurrentIndex(max(0, w.findData(keep)))
                w.blockSignals(False)
        if logins != self.listed:   # a fresh checkbox per account, all ticked the first time
            while self.picks.count():
                self.picks.takeAt(0).widget().deleteLater()
            for a in accounts:
                box = QCheckBox(a["name"])
                box.setChecked(self.checked.get(a["login"], True))
                box.toggled.connect(self.draw)
                self.picks.addWidget(box)
            self.listed = logins
        self.draw()

    def draw(self, *_: object) -> None:
        """The chosen strategy's curves for the ticked accounts, their table and the accounts with no history."""
        boxes = [self.picks.itemAt(i).widget() for i in range(self.picks.count())]
        for a, b in zip(self.accounts, boxes):
            self.checked[a["login"]] = b.isChecked()
        pct = self.unit.currentIndex() == 0
        shown = [c for c in equity.curves(self.accounts, self.strategy.currentData())
                 if self.checked.get(c["login"], True)] if self.strategy.count() else []
        if pct:
            shown = [c for c in shown if c["pct"] is not None]
        key = "pct" if pct else "cum"
        lines = [{"name": c["name"], "times": c["times"], "values": c[key], "colour": chart.LINES[i % len(chart.LINES)],
                  "width": 2.4} for i, c in enumerate(shown)]
        both = equity.combined(shown) if self.combined.isChecked() else None
        if both and both[key]:
            lines.append({"name": "Combinada", "times": both["times"], "values": both[key],
                          "colour": chart.COMBINED, "width": 3.2})
        why = ("Sin historial de ninguna cuenta: recarga FleetBeacon v2 en cada terminal de la VPS"
               if not self.accounts else "Esta estrategia no tiene operaciones cerradas en las cuentas marcadas")
        self.canvas.paint_lines(lines, "% del tamaño de la cuenta" if pct else "Net Profit acumulado", why)
        widgets.fill(self.curves, [[
            cell(c["name"], right=False), cell(str(c["trades"])), signed(c["net"]), cell(fmt.pct(c["win_rate"])),
            cell(fmt.pct(c["max_dd"] / 100 if c["max_dd"] is not None else None))] for c in shown])
        self.curves.setVisible(bool(shown))
        self.eq_notes.setText("<br>".join(f"{who}: sin historial — recarga FleetBeacon v2 en ese terminal de la VPS"
                                          for who in self.missing))
        self.eq_notes.setVisible(bool(self.missing))
