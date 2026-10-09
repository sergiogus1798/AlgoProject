"""The Flota tab: totals, one row per account, and the chosen account's curve, reasons, progress, positions and deals."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QWidget

from mt5.fleet.app import chart, curve, fmt, progress, read, theme, widgets
from mt5.fleet.app.widgets import cell, signed

ACCOUNTS = ["Estado", "Cuenta", "Balance", "Equity", "Flotante", "Hoy", "Peor equity\nhoy", "Suelo\ndiario",
            "Al suelo\ndiario", "Suelo\ntotal", "Al suelo\ntotal", "Equity si\nsaltan stops", "Latido"]
POSITIONS = ["Símbolo", "Lado", "Volumen", "Abierta (servidor)", "Entrada", "Ahora", "SL", "TP",
             "Si salta el SL", "Beneficio", "Swap", "Magic", "Estrategia"]
DEALS = ["Hora (servidor)", "Símbolo", "Volumen", "Precio", "Neto", "Magic", "Estrategia"]
CHOSEN = "#25405c"
SHORT = 26   # characters of the worst reason the table shows; the detail has them whole
LEGEND = (
    "<b>Estado</b> — verde: operando · amarillo: algo que vigilar (AutoTrading apagado, terminal desconectado, "
    "fin de semana o noticia cerca) · rojo: queda menos del 25 % del margen hasta un suelo, los stops abiertos "
    "romperían un suelo, una posición no tiene SL, o una regla prohibida está encima · gris: el terminal calla "
    "más de cinco minutos (las cifras son las del último latido). Al elegir una cuenta salen todos sus motivos.<br>"
    "<b>Flotante</b>: resultado de las posiciones abiertas. <b>Hoy</b>: equity menos el balance con que empezó "
    "el día de la firma. <b>Peor equity hoy</b>: el equity más bajo desde que empezó ese día, medido cada "
    "medio segundo por el servicio de la VPS; sólo existe con el servicio de la versión 2 y se pone en rojo si "
    "cruzó el suelo diario (desconfía: parte de cuando arrancó el servicio, no de antes). <b>Suelo diario</b>: el "
    "equity por debajo del cual se pierde la cuenta hoy; <b>suelo total</b>: el de toda su vida. <b>Al suelo</b>: lo "
    "que falta para tocarlo, en USD y en % del tamaño de la cuenta. <b>Equity si saltan los stops</b>: el equity "
    "si todos los SL abiertos se ejecutaran ahora a su precio; no cuenta deslizamiento, ni gaps de fin de semana, ni "
    "las posiciones sin SL (si las hay lleva «≈» y es optimista). Un «≈» delante dice que la cifra no es exacta; "
    "el motivo sale al elegir la cuenta. <b>Latido</b>: hace cuánto escribió el terminal.<br>"
    "<b>Capital</b>: suma del tamaño de las cuentas con plan. <b>A cobrar</b>: suma de lo cobrable de las cuentas "
    "fondeadas, aproximado: (balance − tamaño) × el reparto del catálogo, sin comprobar los requisitos de la firma.<br>"
    "<b>Progreso</b>: beneficio cerrado contra el objetivo de la fase; los días se cuentan en el día de la firma "
    "(un día de trading es uno con alguna operación; uno rentable llega al % del catálogo o, sin %, gana algo). "
    "Consistencia: el mejor día sobre el total (o sobre la suma de los días positivos, según la firma); con pocos "
    "días no significa nada. El próximo pago es aproximado: el último pago (o la primera operación) más el ciclo "
    "del catálogo. <b>Si salta el SL</b>: lo que esa posición perdería (o ya tendría asegurado, en verde) en su stop. "
    "Todo lo que necesita el servicio de la versión 2 sale como «—» con el de la versión 1.")


def totals(rows: list[dict]) -> dict:
    """The strip above the table: accounts, capital, equity, floating and what is payable.

    Returns:
        `accounts`, `capital` (size of the accounts with a plan), `equity`, `floating` and `payable`
        (sum over funded accounts that have it; None when none does).
    """
    pay = [r["progress"]["payout"]["payable"] for r in rows if r["progress"] and r["progress"]["payout"]
           and r["progress"]["payout"]["payable"] is not None]
    return {"accounts": len(rows), "capital": sum(r["stage"]["size"] for r in rows if r["stage"]),
            "equity": sum(r["beat"]["equity"] for r in rows), "floating": sum(r["beat"]["floating"] for r in rows),
            "payable": sum(pay) if pay else None}


def account_line(row: dict) -> list:
    """One account's cells in the fleet table."""
    beat, stage, floor, risk = row["beat"], row["stage"], row["floor"], row["risk"]
    name = fmt.firm_phase(stage) if stage else beat["company"]
    text = row["text"] if len(row["text"]) <= SHORT else row["text"][:SHORT - 1] + "…"
    line = [cell("●  " + text, theme.LIGHTS[row["light"]], right=False), cell(name, right=False),
            cell(fmt.money(beat["balance"])), cell(fmt.money(beat["equity"])), signed(beat["floating"])]
    at_stops = risk["equity_at_stops"]
    stops = cell("— (beacon v1)" if at_stops is None else
                 ("≈ " if risk["no_sl"] else "") + fmt.money(at_stops), theme.LIGHTS["red"] if risk["breaks"] else None)
    if at_stops is None:
        stops.setToolTip("El beacon de esta cuenta es de la versión 1: no trae el tamaño de tick ni el valor del tick, "
                         "y sin ellos no se puede calcular lo que pierde cada stop. Recarga FleetBeacon v2 en ese "
                         "terminal de la VPS (Navegador → Servicios → FleetBeacon → Detener e Iniciar).")
    elif risk["no_sl"]:
        stops.setToolTip(f"≈ {risk['no_sl']} posición(es) sin SL (p. ej. un trailing que aún no se ha armado): "
                         "no cuentan, así que la cifra es optimista.")
    if floor is None:
        return line + [cell(fmt.DASH) for _ in range(7)] + [stops, cell(row["age"])]
    limit, mark = read.CFG["red_margin_left"], "≈ " if floor["approx"] else ""

    def room(usd: float, left: float, pre: str) -> object:
        """What is left to a floor, in currency and in % of the size, red under the limit."""
        return cell(f"{pre}{fmt.money(usd)} · {fmt.money(100 * usd / stage['size'])[:-1]} %",
                    theme.LIGHTS["red"] if left < limit else None)

    worst = floor["worst_today"]
    return line + [signed(floor["today"]),
                   cell(fmt.money(worst), theme.LIGHTS["red"] if worst is not None and worst < floor["daily_floor"]
                        else None),
                   cell(mark + fmt.money(floor["daily_floor"])),
                   room(floor["daily_room"], floor["daily_left"], mark), cell(fmt.money(floor["max_floor"])),
                   room(floor["max_room"], floor["max_left"], ""), stops, cell(row["age"])]


def position_line(p: dict, loss: float | None, name: str) -> list:
    """One open position's cells."""
    return [cell(p["symbol"], right=False), cell("Compra" if p["side"] == "buy" else "Venta", right=False),
            cell(f"{p['volume']:g}"), cell(fmt.clock(p["time"])), cell(f"{p['price_open']:g}"),
            cell(f"{p['price_current']:g}"), cell(f"{p['sl']:g}" if p["sl"] else "sin SL",
                                                   theme.LIGHTS["red"] if not p["sl"] else None),
            cell(f"{p['tp']:g}"), signed(loss), signed(p["profit"]), signed(p["swap"]), cell(str(p["magic"])),
            cell(name, right=False)]


class FleetTab(QWidget):
    """The tab's widgets; every figure comes from `state.rows`."""

    def __init__(self) -> None:
        """Build the empty tab."""
        super().__init__()
        self.rows, self.chosen = [], 0
        names = ["Cuentas", "Capital", "Equity", "Flotante", "A cobrar"]
        cards = [widgets.card(n) for n in names]
        self.values = [v for _, v in cards]
        self.accounts, self.positions = widgets.table(ACCOUNTS, "Cuenta"), widgets.table(POSITIONS, "Estrategia")
        self.accounts.setStyleSheet("QTableWidget { font-size: 14px; } QTableWidget::item { padding: 6px 4px; }")
        self.deals = widgets.table(DEALS, "Estrategia")
        self.accounts.cellClicked.connect(self.choose)
        self.detail, self.closed = widgets.label("", "section"), widgets.label("", "section")
        self.reasons, self.notes = widgets.label("", "reasons", True), widgets.label("", "notes", True)
        self.canvas, self.progress = chart.CurveCanvas(), widgets.label("", "reasons", True)
        self.canvas.setMinimumHeight(330)
        side = QFrame()
        side.setObjectName("card")
        QVBoxLayout(side).addWidget(self.progress, alignment=Qt.AlignTop)
        middle = QWidget()
        row = QHBoxLayout(middle)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(self.canvas, 3)
        row.addWidget(side, 2)
        parts = [widgets.strip([c for c, _ in cards]), self.accounts, self.detail, self.reasons, self.notes,
                 middle, widgets.label("Posiciones abiertas", "section"), self.positions, self.closed, self.deals]
        scroll, _ = widgets.page(parts, LEGEND)
        box = QVBoxLayout(self)
        box.setContentsMargins(0, 0, 0, 0)
        box.addWidget(scroll)
        self.scroll = scroll

    def paint(self, rows: list[dict]) -> None:
        """Show these rows, keeping the chosen account."""
        self.rows = rows
        t = totals(rows)
        for value, text in zip(self.values, [str(t["accounts"]), fmt.money(t["capital"]), fmt.money(t["equity"]),
                                             fmt.money(t["floating"]), "≈ " + fmt.money(t["payable"])
                                             if t["payable"] is not None else fmt.DASH]):
            value.setText(text)
        widgets.fill(self.accounts, [account_line(r) for r in rows])
        self.choose(min(self.chosen, len(rows) - 1))

    def choose(self, row: int, _column: int = 0) -> None:
        """Mark an account's row as the chosen one and show its detail."""
        self.chosen = row
        for i in range(self.accounts.rowCount()):
            for j in range(self.accounts.columnCount()):
                self.accounts.item(i, j).setBackground(QColor(CHOSEN if i == row else theme.PANEL))
        self.paint_detail()

    def paint_detail(self) -> None:
        """The chosen account's reasons, curve, progress, open positions and today's deals."""
        r = self.rows[self.chosen]
        beat, names = r["beat"], read.names()
        firm = r["stage"]["firm"] if r["stage"] else ""
        named = lambda magic, comment: names.get((firm, magic), comment)  # noqa: E731
        self.detail.setText(f"{fmt.who(beat, r['stage'])} — {len(beat['positions'])} posiciones abiertas")
        shown = "<br>".join(f"<span style='color:{theme.LIGHTS[level]}'>●</span> {text}" for level, text in r["reasons"])
        self.reasons.setText(shown or "<span style='color:%s'>●</span> Sin motivos de aviso" % theme.LIGHTS["green"])
        approx = r["floor"]["approx"] if r["floor"] else []
        self.notes.setText("<br>".join([f"≈ {a[0].upper()}{a[1:]}." for a in approx] + r["doubts"]))
        self.notes.setVisible(bool(approx or r["doubts"]))
        data = curve.data(beat, r["floor"]) if r["floor"] else None
        self.canvas.paint(data, "Sin curva: el colector aún no ha escrito el histórico y el servicio de la VPS "
                                "es de la versión 1 (recárgalo)" if "hours" not in beat else "Sin curva todavía")
        prog = r["progress"]
        self.progress.setText("<b>Progreso de fase</b><br>" + ("<br>".join(progress.lines(prog)) if prog else
                              "—<br>falta el historial de la cuenta: lo envía el servicio de la versión 2 (recárgalo en la VPS)" if r["deals"] is None else "—"))
        widgets.fill(self.positions, [position_line(p, loss, named(p["magic"], p["comment"]))
                                      for p, loss in zip(beat["positions"], r["risk"]["losses"])])
        widgets.fill(self.deals, [[
            cell(fmt.clock(d["time"])), cell(d["symbol"] or "balance", right=False), cell(f"{d['volume']:g}"),
            cell(f"{d['price']:g}"), signed(d["profit"] + d["swap"] + d["commission"] + d["fee"]),
            cell(str(d["magic"])), cell(named(d["magic"], d["comment"]), right=False)]
            for d in beat["deals_today"]])
        self.closed.setText("Cerrado hoy y movimientos de balance"
                            + ("" if beat["deals_today"] else " — nada desde la medianoche del servidor"))
        self.positions.setVisible(bool(beat["positions"]))
        self.deals.setVisible(bool(beat["deals_today"]))
