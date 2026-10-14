"""The Despliegue tab: per account, the EAs the workbook expects against the charts that carry one, and the magics that trade."""

from PySide6.QtWidgets import QVBoxLayout, QWidget

from mt5.fleet.app import eas, fmt, theme, widgets
from mt5.fleet.app.widgets import cell

COLUMNS = [
    "Cuenta",
    "Estrategia",
    "Activo",
    "TF",
    "En el Excel",
    "Montada",
    "Magic",
    "Última operación",
    "Avisos",
]
LEGEND = (
    "<b>En el Excel</b>: la estrategia está en la hoja de esa cuenta de <code>Flota_de_cuentas.xlsx</code> (lo que el "
    "dueño quiere desplegar). <b>Montada</b>: hay un gráfico con ese EA en el terminal, según el servicio de la VPS "
    "(versión 2). Estrategia y temporalidad se comparan por el nombre del EA (3.23.151); el activo no, porque cada "
    "firma lo llama de una forma. <b>Magic</b>: el que usan sus operaciones, leído de los comentarios del histórico; "
    "sale «—» si aún no ha operado o no hay histórico. <b>Última operación</b>: hora del servidor de la última "
    "apertura o cierre con ese magic. <b>Avisos</b>: esperada y no montada · montada y no esperada · magic que el "
    "registro del reconciliador no nombra · sin operar desde hace más de <code>silent_strategy_days</code> días "
    "(una estrategia de pocas operaciones puede estar sana y callada). Cuando falta un dato la cuenta lo dice "
    "encima de la tabla, en amarillo."
)


def tick(value: bool | None) -> tuple[str, str | None]:
    """Sí / No / — for a flag that may be unknown, and its colour."""
    return (
        ("—", None)
        if value is None
        else ("sí", theme.GAIN)
        if value
        else ("no", theme.LIGHTS["yellow"])
    )


class DeployTab(QWidget):
    """The tab's table and the notes about what could not be read."""

    def __init__(self) -> None:
        """Build the empty tab."""
        super().__init__()
        self.notes, self.table = (
            widgets.label("", "notes", True),
            widgets.table(COLUMNS, "Avisos"),
        )
        scroll, _ = widgets.page([self.notes, self.table], LEGEND)
        box = QVBoxLayout(self)
        box.addWidget(scroll)
        box.setContentsMargins(0, 0, 0, 0)

    def paint(self, rows: list[dict], now: int) -> None:
        """Show every account's deployment as of `now` (UTC epoch)."""
        notes, lines = {}, []
        for r in rows:
            view = eas.account_view(r, now)
            who = fmt.who(r["beat"], r["stage"])
            for n in view["notes"]:
                notes.setdefault(n, []).append(who)
            for e in view["rows"]:
                (ex, exc), (mo, moc) = tick(e["expected"]), tick(e["mounted"])
                lines.append(
                    [
                        cell(who, right=False),
                        cell(e["strategy"], right=False),
                        cell(e["symbol"], right=False),
                        cell(e["tf"], right=False),
                        cell(ex, exc),
                        cell(mo, moc),
                        cell(str(e["magic"]) if e["magic"] is not None else fmt.DASH),
                        cell(fmt.clock(e["last"])),
                        cell(
                            " · ".join(e["flags"]), theme.LIGHTS["yellow"], right=False
                        ),
                    ]
                )
        self.notes.setText(
            "<br>".join(
                f"{n[0].upper()}{n[1:]} — "
                + ("todas las cuentas" if len(accts) == len(rows) else ", ".join(accts))
                + "."
                for n, accts in notes.items()
            )
        )
        self.notes.setVisible(bool(notes))
        widgets.fill(self.table, lines)
