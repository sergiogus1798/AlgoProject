"""The whole of one study result, or two side by side: verdict, staleness, tabs, warnings, glossary."""

from PySide6.QtWidgets import (QFrame, QHBoxLayout, QPushButton, QScrollArea, QSizePolicy,
                               QTabWidget, QVBoxLayout, QWidget)

from ui.desktop.blocks import fuse, tools
from ui.desktop.blocks.card import initial, text
from ui.desktop.blocks.head import head as _head
from ui.desktop.blocks.head import stale as _stale
from ui.desktop.blocks.pick import selectors
from ui.desktop.blocks.states import colour, label
from ui.desktop.blocks.tabpage import Slot, TabPage
from ui.text.glossary import label as words
from ui.desktop.theme import T

FOLD = 8        # warnings shown before the rest fold behind a button


def _warnings(results: list[dict], titles: list[str]) -> tuple[list[QWidget], list[QWidget]]:
    """Each distinct warning once, coloured, counted, split into a study's `highlight`ed ones
    (KS, say) and the rest — a population raises the same sentence once per strategy, so
    identical ones are counted, never dropped."""
    seen: dict[tuple, list] = {}
    high: dict[tuple, bool] = {}
    helps: dict[tuple, str] = {}
    for r, t in zip(results, titles):
        for w in r.get("warnings") or []:
            key = (t, w["state"], w["text"])
            seen.setdefault(key, []).append(w["code"])
            high[key] = high.get(key, False) or bool(w.get("highlight"))
            helps[key] = helps.get(key) or w.get("help") or ""
    top, rest = [], []
    for (t, state, body), codes in seen.items():
        h, c = high[(t, state, body)], colour(state)
        times = f"×{len(codes)} · " if len(codes) > 1 else ""
        said = helps[(t, state, body)]     # a warning that explains itself shows a «?» (KS)
        mark = f" <span style='color:{T['faint']}'>(?)</span>" if said else ""
        line = text(f"{times}{t + ' · ' if t else ''}{body}{mark}", T["text"], 15 if h else 13, h)
        line.setStyleSheet(line.styleSheet() + f" border-left: {6 if h else 4}px solid {c}; "
                           f"padding: {8 if h else 4}px 10px;")
        line.setToolTip(said or f"Aviso «{codes[0]}» · {label(state)}: colorea, nunca elimina")
        (top if h else rest).append(line)
    return top, rest


def _glossary(results: list[dict]) -> list[QWidget]:
    """Every term once, with its sentence."""
    terms = {g["term"]: g["text"] for r in results for g in r.get("glossary") or []}
    return [text(f"<b>{initial(k)}</b> — {v}", T["text"], 13) for k, v in terms.items()]


def _section(title: str) -> QWidget:
    """A small upper-case heading between the parts of the page."""
    return text(title.upper(), T["text"], 11, True)


class ResultView(QWidget):
    """One study result as a page, or two compared. Remembers the open tab and the selectors
    across calls, so moving from one strategy to the next keeps the reader where he was."""

    def __init__(self) -> None:
        """Start empty, inside its own scroll area."""
        super().__init__()
        self.memory: dict[str, dict] = {}
        self.tab = ""
        self.results: list[dict] = []
        self.titles: list[str] = []
        self.stored: dict | None = None     # the result as read, whatever is drawn from it
        self.meta: dict | None = None
        self.showing = "stored"
        self.pages: dict[int, TabPage] = {}
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        self.content = QWidget()
        scroll.setWidget(self.content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        self.scroll = scroll
        self.show_result(None, None)

    def show(self, *args: object) -> None:
        """Draw one result: `show(result, meta)`. Called bare it is Qt's own `show()`, which
        this name would otherwise hide from every caller that means the widget's visibility.

        Args:
            args: (result, meta) as in `show_result`, or nothing.
        """
        if args:
            self.show_result(*args)
        else:
            super().show()

    def show_result(self, result: dict | None, meta: dict | None = None) -> None:
        """Draw one result.

        Args:
            result: A contract result, None when the study has not run on this strategy.
            meta: The daemon's `meta` (config_hash, current_hash, stale, day…), may be None.
        """
        self.stored, self.meta, self.showing = result, meta, "stored"
        if result is None:
            return self.empty("Sin resultado todavía: este estudio no ha corrido aquí.")
        top = [_head(result, None)] + ([_stale(meta)] if meta and meta.get("stale") else [])
        self._build([result], [""], top + [self._tools()])

    def empty(self, sentence: str) -> None:
        """No result: one muted sentence in its place."""
        self._build([], [], [text(sentence, T["muted"], 15)])

    def compare(self, left: dict, right: dict, titles: tuple[str, str]) -> None:
        """Draw two results in two columns, the same tab open in both, block beside block.

        Args:
            left, right: Two contract results of the same study (two runs, or two strategies).
            titles: What each column is, e.g. the day of each run or each strategy's name.
        """
        row = QWidget()
        lay = QHBoxLayout(row)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(24)
        for r, t in zip((left, right), titles):
            lay.addWidget(_head(r, t), 1)
        self._build([left, right], list(titles), [row, self._tools()])

    def beside(self, index: int) -> None:
        """A partial re-run beside the stored result, on the sub-test it re-ran.

        Args:
            index: Its position in the stored result's `partials`.
        """
        part = self.stored["partials"][index]["result"]
        for tab in part["tabs"]:            # open the stored side on the same market or test
            for s in selectors(tab):
                if len(s["options"]) == 1:
                    self.memory.setdefault(tab["name"], {})[s["key"]] = s["options"][0]
        self.showing = f"beside:{index}"
        self.compare(self.stored, part, (f"Guardado · {self.stored.get('computed_at')}",
                                         f"Solo {part.get('only')} · {part.get('computed_at')}"))

    def merged(self, index: int) -> None:
        """The stored result with one sub-test taken from a partial re-run (`fuse.merge`).

        Args:
            index: Its position in the stored result's `partials`.
        """
        part = self.stored["partials"][index]["result"]
        got = fuse.merge(self.stored, part)
        self.showing = f"merged:{index}"
        said = text(fuse.notice(self.stored, part), T["text"], 14, True)
        said.setStyleSheet(said.styleSheet() + f" border-left: 4px solid {colour('info')}; "
                           "padding: 4px 10px;")
        self._build([got], [""], [_head(got, None), said, self._tools()])

    def _tools(self) -> QWidget:
        """The report button with its line, and the strip of partial re-runs when there are any."""
        box = QWidget()
        lay = QVBoxLayout(box)
        lay.setContentsMargins(0, 0, 0, 0)
        said = text("", T["muted"], 12)
        button = QPushButton(words("screen.report"))
        button.setToolTip("Escribe una página HTML con exactamente lo que ves: las pestañas, la "
                          "combinación de cada selector, los mercados elegidos, los avisos y el "
                          "glosario, dibujados por core.study.render desde el mismo resultado.")
        button.clicked.connect(lambda: said.setText(tools.report(
            self.results, self.titles, self.memory, (self.meta or {}).get("path"))))
        if not (self.meta or {}).get("path"):
            # A result read straight from AlgoData (Datos' step-4 studies) has no report
            # folder: the click could only ever say so (📓 2026-09-29), so it is off instead.
            button.setEnabled(False)
            button.setToolTip("Este resultado no viene de un informe guardado: no hay dónde "
                              "escribir la página.")
        lay.addWidget(button)
        lay.addWidget(said)
        if self.stored and self.stored.get("partials"):
            lay.addWidget(tools.strip(self.stored["partials"], self.beside, self.merged,
                                      lambda: self.show_result(self.stored, self.meta),
                                      self.showing))
        return box

    def _build(self, results: list[dict], titles: list[str], top: list[QWidget]) -> None:
        """Lay the page out again: header widgets, the warnings (highlighted first, top of the
        page — §1: «Avisos: moverlos arriba, visibles»), the tabs, the glossary."""
        self.results, self.titles, self.pages = results, titles, {}
        self.content = QFrame()
        self.content.setObjectName("term")
        lay = QVBoxLayout(self.content)
        lay.setContentsMargins(16, 12, 16, 16)
        lay.setSpacing(10)
        for w in top:
            lay.addWidget(w)
        high, rest = _warnings(results, titles)
        for w in high:
            lay.addWidget(w)
        if rest:
            lay.addWidget(_section(f"avisos ({len(rest)} más)"))
            for k, w in enumerate(rest):
                lay.addWidget(w)
                w.setVisible(k < FOLD)
            if len(rest) > FOLD:
                more = QPushButton(f"Ver los {len(rest) - FOLD} avisos restantes")
                more.clicked.connect(lambda: [w.setVisible(True) for w in rest] + [more.hide()])
                lay.addWidget(more)
        names = list(dict.fromkeys(t["name"] for r in results for t in r["tabs"]))
        self.names = names
        if names:
            self.tabs = QTabWidget()
            self.tabs.setDocumentMode(True)
            # Expanding (Qt's default) grabs the leftover space the outer stretch was meant
            # to hold, leaving a blank gap inside the tab instead of above the glossary
            # (§1 «hueco vacío enorme»); Minimum keeps it at its content's own height.
            self.tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
            for n in names:
                tab = next(t for r in results for t in r["tabs"] if t["name"] == n)
                holder = Slot()            # the page goes in on first opening: a population
                QVBoxLayout(holder).setContentsMargins(0, 0, 0, 0)   # has hundreds of tables
                i = self.tabs.addTab(holder, initial(tab.get("title") or n).replace("&", "&&"))
                self.tabs.setTabToolTip(i, tab.get("note") or tab.get("title") or n)
            self.tabs.currentChanged.connect(self._open)
            lay.addWidget(self.tabs)
            self.tabs.setCurrentIndex(names.index(self.tab) if self.tab in names else 0)
            self._open(self.tabs.currentIndex())
        glossary = _glossary(results)
        if glossary:
            lay.addWidget(_section("glosario"))
            for g in glossary:
                lay.addWidget(g)
        lay.addStretch(1)
        self.scroll.setWidget(self.content)   # deletes the previous page itself

    def _open(self, index: int) -> None:
        """Build a tab's page the first time it is opened, and size the tabs to it alone.

        Args:
            index: The tab opened.
        """
        name = self.names[index]
        if index not in self.pages:
            sides = [next((t for t in r["tabs"] if t["name"] == name), None) for r in self.results]
            pool = ([b for t in self.results[0]["tabs"] for b in t["blocks"]]
                    if len(self.results) == 1 else None)
            page = TabPage(sides, self.memory.setdefault(name, {}), pool)
            self.memory[name] = page.chosen
            self.pages[index] = page
            self.tabs.widget(index).layout().addWidget(page)
        self.tab = name
        self.tabs.widget(index).updateGeometry()   # the slots' hints changed with the tab shown
        self.tabs.updateGeometry()
