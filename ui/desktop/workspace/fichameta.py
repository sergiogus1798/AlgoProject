"""The ficha's metadata column: what the strategy is built from and how it was backtested (E2's fields)."""

import re

from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from ui.text.glossary import label
from ui.desktop.theme import C, T

DIRECTION = {"long": "solo largos", "short": "solo cortos", "both": "largos y cortos"}
SIDE = {"long": "larga", "short": "corta"}
EXITS = (("stop_loss", "SL"), ("profit_target", "PT"), ("trailing_stop", "trailing"),
         ("break_even", "break even"))
DAYS = {"MONDAY": "lunes", "TUESDAY": "martes", "WEDNESDAY": "miércoles", "THURSDAY": "jueves",
        "FRIDAY": "viernes", "SATURDAY": "sábado", "SUNDAY": "domingo"}
COSTS = (("spread", "spread"), ("slippage", "slippage"), ("min_distance", "min distance"))


def _on(option: dict) -> bool:
    """Whether a trading option is switched on (E2 keeps SQX's boolean or its text)."""
    return option["on"] in (True, "true")


def _params(params: dict) -> str:
    """`Name = value` pairs, as a person reads them."""
    return ", ".join(f"{k} = {v}" for k, v in params.items())


def _order(o: dict) -> str:
    """One entry order in a line: type, direction, each exit it carries or «sin»."""
    parts = [f"{o['type']} ({SIDE.get(o['direction'], o['direction'])})"]
    for key, name in EXITS:
        v = o[key]
        parts.append(f"sin {name}" if v is None else
                     f"{name} {v.get('formula', '') if isinstance(v, dict) else v}")
    if o.get("exit_after_bars"):
        parts.append(f"sale tras {o['exit_after_bars']} barras")
    return " · ".join(parts)


def _costs(test: dict) -> str:
    """A task's costs in one line; None when the task carries none of its own."""
    c = test["costs"]
    if c is None:
        return "la tarea no lleva costes propios"
    fees = ", ".join(f"{m['method']} {m['value']}" for m in c["commission"]) or "ninguna"
    swap = c["swap"]
    swapped = (f"swap largo {swap['long']}, corto {swap['short']} ({swap['type']}, triple el "
               f"{DAYS.get(swap['tripleSwapOn'], swap['tripleSwapOn'])})" if swap and swap.get("use") == "true" else "sin swap")
    return " · ".join([*(f"{name} {c[key]}" for key, name in COSTS), f"comisión {fees}", swapped])


def rows(meta: dict) -> list[tuple[str, str, str]]:
    """The panel's lines: (label, text, colour) — the colour an amber warning or the text's.

    Args:
        meta: `/api/strategy/meta`'s answer: `strategymeta.read` plus `origin`.
    """
    ink, warn = T["text"], C["weak"]
    last = meta["last_test"]
    mm = meta["money_management"]
    friday = meta["friday_close"]
    opts = meta["trading_options"]
    out = [("Dirección", DIRECTION.get(meta["direction"], meta["direction"]), ink)]
    out += [(label(s), text, ink) for s, text in meta["signals"].items()]
    out += [(f"Condición {i + 1} ({label(c['signal']).lower()})", c["text"], ink)
            for i, c in enumerate(meta["entries"] + meta["exits"])]
    for side in ("entry", "exit"):
        if meta["indicators"][side]:
            out.append((f"Indicadores de {'entrada' if side == 'entry' else 'salida'}",
                        ", ".join(meta["indicators"][side]), ink))
    out += [(f"Orden {i + 1}", _order(o), ink) for i, o in enumerate(meta["orders"])]
    out.append(("Money management", f"{mm['method']} ({_params(mm['params'])}) · capital "
                f"{mm['initial_capital']} · de la {'estrategia' if mm['from'] == 'strategy' else 'tarea'}",
                ink))
    out.append(("Cierre de los viernes", f"sí, a las {friday['time']}" if _on(friday) else "no", ink))
    others = [name for key, name in (("weekend", "no opera en fin de semana"),
                                     ("end_of_day", "cierra al final del día"),
                                     ("time_range", "limita el horario")) if _on(opts[key])]
    out.append(("Otras opciones", ", ".join(others) or "ninguna", ink))
    out.append(("Activo", f"{meta['asset']} · {meta['feed']} · {meta['timeframe']} · sesión "
                f"{opts['session']}", ink))
    out.append(("Último test", f"{last['input']} → {last['output']} · {' → '.join(last['window'])}"
                f" · {last['engine']} · precisión {last['precision']}", ink))
    out.append(("Costes del último test", _costs(last), ink))
    for task in meta.get("backtest", []):
        if "error" not in task and task["costs"] != last["costs"]:
            out.append((f"⚠ Costes de «{task['task']}»", f"{_costs(task)} — no son los del último "
                        "test guardado en el .sqx", warn))
    out += [("Nota", note, T["muted"]) for note in meta["notes"]]
    out.append(("Fichero", f"{meta['file']} · {meta['origin']}", T["muted"]))
    return out


class Meta(QScrollArea):
    """The right-hand column, scrolling on its own; each field's name above its value."""

    def __init__(self) -> None:
        """Build it empty."""
        super().__init__()
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setMinimumWidth(360)
        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(14, 0, 4, 0)
        lay.addWidget(QLabel("METADATOS", objectName="kicker"))
        self.grid = QGridLayout()
        self.grid.setVerticalSpacing(1)
        lay.addLayout(self.grid)
        lay.addStretch(1)
        self.setWidget(inner)
        self.setStyleSheet(f"QScrollArea {{ border-left: 1px solid {T['rule']}; }}")

    def fill(self, meta: dict) -> None:
        """Paint `/api/strategy/meta`'s answer; an error is the one line shown.

        Args:
            meta: The fields, or `{"error"}` («sin .sqx en ningún install»).
        """
        while self.grid.count():
            self.grid.takeAt(0).widget().deleteLater()
        if "error" in meta:
            lines = [("Sin metadatos", meta["error"], C["dead"])]
        else:
            lines = rows(meta)
        for i, (name, text, ink) in enumerate(lines):
            key = QLabel(label(name), objectName="dim")
            key.setStyleSheet(f"color: {ink};" if ink != T["text"] else "")
            # A block's text has no spaces to wrap at; a zero-width space after each separator
            # lets «CBlock_…(Int2=22)» break inside a narrow column instead of being cut.
            value = QLabel(re.sub(r"([,(=→·])", "\\1\u200b", text), objectName="mono")
            value.setWordWrap(True)
            value.setStyleSheet(f"color: {ink}; margin-bottom: 4px;")
            self.grid.addWidget(key, 2 * i, 0)
            self.grid.addWidget(value, 2 * i + 1, 0)
