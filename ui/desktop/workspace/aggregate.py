"""The databank's aggregate equity beside the table: SQX's and the real-cost curve, with stats."""

import httpx
from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from ui.desktop import background, client
from ui.text.numbers import num
from ui.desktop.workspace.curves import INK, NAME, Curves

MIN_HEIGHT = 230            # px
MIN_WIDTH = 300             # px: the two switches and the stats' two columns still read


def ask(path: str, **params: str) -> dict:
    """One GET to the daemon; a daemon that does not answer is an `error` to show."""
    try:
        return client.get(path, **params)
    except httpx.HTTPError as failed:
        return {"error": f"El demonio no respondió: {failed}"}


class Aggregate(QWidget):
    """The two curves, each with its switch, the IS/OOS boundary and the stats. No line under
    them names the cosecha or the spread report (owner, 2026-09-28): why the real curve is
    missing is the tooltip of its switch."""

    def __init__(self) -> None:
        """Build it empty, at the width the panel's splitter gives it: the curve takes every
        pixel of width and height the owner drags it to."""
        super().__init__()
        self.setMinimumWidth(MIN_WIDTH)
        # Kicker, switches, curve and three lines of stats: below this the splitter
        # squeezed the stats over the curve (seen 2026-09-28), so the panel stops shrinking here.
        self.setMinimumHeight(MIN_HEIGHT)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 0, 0, 0)
        self.cache: dict[tuple, dict] = {}
        self.shown: tuple = ()
        top = QHBoxLayout()
        kicker = QLabel("EQUITY AGREGADA")
        kicker.setObjectName("kicker")
        self.of = QLabel("")
        self.of.setObjectName("dim")
        top.addWidget(kicker)
        top.addWidget(self.of, 1)
        lay.addLayout(top)
        self.curves = Curves(80)
        switches = QHBoxLayout()
        self.boxes = {}
        for key in ("sqx", "real"):
            box = QCheckBox(NAME[key])
            box.setChecked(True)
            box.setStyleSheet(f"color: {INK[key]};")
            box.toggled.connect(lambda on, k=key: self.curves.toggle(k, on))
            switches.addWidget(box)
            self.boxes[key] = box
        switches.addStretch(1)
        lay.addLayout(switches)
        lay.addWidget(self.curves, 1)
        self.stats = QLabel("")
        self.stats.setObjectName("mono")
        self.stats.setWordWrap(True)
        lay.addWidget(self.stats)

    def load(self, project: str, databank: str, rows: list[dict], hidden: set[str]) -> None:
        """Read and paint the databank's aggregate: of every row, or — when a filter hid some
        (F6) — only of the visible ones, sent by identity. Each answer is kept until `forget`.

        Args:
            project: Project name.
            databank: The databank on screen.
            rows: GET /api/databank/table's rows.
            hidden: The identities the table hides.
        """
        ids = sorted(r["identity"] for r in rows if r["identity"] and r["identity"] not in hidden)
        key = (project, databank, tuple(ids) if hidden else None)
        self.shown = key
        if key in self.cache:
            self.fill(self.cache[key])
            return
        self.stats.setText("leyendo la curva…")
        background.post("databank/equity", {"project": project, "databank": databank,
                                            "ids": ids if hidden else None},
                        lambda got: self.landed(key, got), key=f"equity:{id(self)}", owner=self)

    def landed(self, key: tuple, curve: dict) -> None:
        """The daemon's curve: kept unless it failed, painted if it is still the one shown."""
        if "error" not in curve:
            self.cache[key] = curve
        if key == self.shown:
            self.fill(curve)

    def forget(self) -> None:
        """Drop every curve read, so the next `load` asks again (a rerun, a reload)."""
        self.cache = {}

    def fill(self, curve: dict) -> None:
        """Paint GET /api/databank/equity's answer, or its error in place of the stats.

        Args:
            curve: `sqx`, `real` (None without a spread report), `split`, `stats` and
                `real_why` — or `error`.
        """
        of = curve.get("of")
        self.of.setText("" if of is None else "· de todas las filas" if of == "todas"
                        else f"· {num(of)} visibles")
        if "error" in curve:
            self.curves.fill([0.0, 0.0], [])
            self.stats.setText(curve["error"])
            return
        self.curves.fill(curve["sqx"], curve["real"] or [], curve.get("split"))
        pairs = [f"{k}: {num(v)}" for k, v in curve["stats"].items()]
        self.stats.setText("\n".join("   ".join(pairs[i:i + 2]) for i in range(0, len(pairs), 2)))
        self.boxes["real"].setToolTip(curve.get("real_why") or "")
