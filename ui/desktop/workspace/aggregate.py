"""The databank's aggregate equity beside the table: SQX's and the real-cost curve, with stats."""

import httpx
from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from ui.desktop import client
from ui.text.numbers import num
from ui.desktop.workspace.curves import INK, NAME, Curves

MIN_HEIGHT = 230            # px


def ask(path: str, **params: str) -> dict:
    """One GET to the daemon; a daemon that does not answer is an `error` to show."""
    try:
        return client.get(path, **params)
    except httpx.HTTPError as failed:
        return {"error": f"El demonio no respondió: {failed}"}


class Aggregate(QWidget):
    """The two curves, each with its switch, the IS/OOS boundary, the stats and the source."""

    def __init__(self) -> None:
        """Build it empty, at the width the panel gives it."""
        super().__init__()
        self.setFixedWidth(340)
        # Kicker, switches, curve, three lines of stats and the source: below this the splitter
        # squeezed the stats over the curve (seen 2026-09-28), so the panel stops shrinking here.
        self.setMinimumHeight(MIN_HEIGHT)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 0, 0, 0)
        self.cache: dict[tuple, dict] = {}
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
        for key in ("sqx", "real"):
            box = QCheckBox(NAME[key])
            box.setChecked(True)
            box.setStyleSheet(f"color: {INK[key]};")
            box.toggled.connect(lambda on, k=key: self.curves.toggle(k, on))
            switches.addWidget(box)
        switches.addStretch(1)
        lay.addLayout(switches)
        lay.addWidget(self.curves, 1)
        self.stats = QLabel("")
        self.stats.setObjectName("mono")
        self.stats.setWordWrap(True)
        lay.addWidget(self.stats)
        self.source = QLabel("")
        self.source.setObjectName("dim")
        self.source.setWordWrap(True)
        lay.addWidget(self.source)

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
        if key not in self.cache:
            try:
                self.cache[key] = client.post("databank/equity", {
                    "project": project, "databank": databank, "ids": ids if hidden else None})
            except httpx.HTTPError as failed:
                self.cache[key] = {"error": f"El demonio no respondió: {failed}"}
        self.fill(self.cache[key])

    def forget(self) -> None:
        """Drop every curve read, so the next `load` asks again (a rerun, a reload)."""
        self.cache = {}

    def fill(self, curve: dict) -> None:
        """Paint GET /api/databank/equity's answer, or its error in place of the stats.

        Args:
            curve: `sqx`, `real` (None without a spread report), `split`, `stats`, `source`
                and `real_why` — or `error`.
        """
        of = curve.get("of")
        self.of.setText("" if of is None else "· de todas las filas" if of == "todas"
                        else f"· {num(of)} visibles")
        if "error" in curve:
            self.curves.fill([0.0, 0.0], [])
            self.stats.setText(curve["error"])
            self.source.setText("")
            return
        self.curves.fill(curve["sqx"], curve["real"] or [], curve.get("split"))
        pairs = [f"{k}: {num(v)}" for k, v in curve["stats"].items()]
        self.stats.setText("\n".join("   ".join(pairs[i:i + 2]) for i in range(0, len(pairs), 2)))
        self.source.setText(" ".join(t for t in (curve.get("source", ""),
                                                 curve.get("real_why") or "") if t))
