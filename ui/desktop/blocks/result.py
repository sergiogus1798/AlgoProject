"""The whole of one study result, or two side by side: verdict, staleness, tabs, warnings, glossary."""

from PySide6.QtWidgets import (QFrame, QHBoxLayout, QPushButton, QScrollArea, QSizePolicy,
                               QTabWidget, QVBoxLayout, QWidget)

from ui.desktop.blocks import chart, verdict
from ui.desktop.blocks.card import text
from ui.desktop.blocks.states import colour, label
from ui.desktop.blocks.tabpage import TabPage
from ui.desktop.theme import T

FOLD = 8        # warnings shown before the rest fold behind a button


def _stamp(result: dict) -> str:
    """The line saying what was computed, when, under which configuration and how fast."""
    parts = [result.get("strategy") or "población", f"calculado {result.get('computed_at', '—')}",
             f"config {result.get('config_hash', '—')}"]
    if result.get("wall_s") is not None:
        parts.append(f"{chart.num(result['wall_s'])} s")
    return " · ".join(parts)


def _head(result: dict, title: str | None) -> QWidget:
    """One side's header: its title in a comparison, its verdict and its stamp."""
    box = QWidget()
    lay = QVBoxLayout(box)
    lay.setContentsMargins(0, 0, 0, 0)
    if title:
        lay.addWidget(text(title, T["text"], 17, True))
    if result.get("verdict"):
        lay.addWidget(verdict.widget(result["verdict"]))
    else:
        lay.addWidget(text("Este estudio describe y no juzga: no hay veredicto.", T["muted"], 14))
    lay.addWidget(text(_stamp(result), T["faint"], 12))
    return box


def _stale(meta: dict) -> QWidget:
    """The red banner of a result computed under another configuration than the drawer's."""
    banner = text(f"CADUCADO — este resultado se calculó con la configuración "
                  f"{meta.get('config_hash', '—')} y la de ahora firma "
                  f"{meta.get('current_hash', '—')}. Responde a otra pregunta: vuelve a "
                  f"correrlo antes de leerlo como respuesta.", colour("fail"), 14, True)
    banner.setStyleSheet(banner.styleSheet() + f" border: 2px solid {colour('fail')}; "
                         "padding: 8px;")
    return banner


def _warnings(results: list[dict], titles: list[str]) -> list[QWidget]:
    """Each distinct warning once, in its state's colour, with how many times it was raised.

    A population raises the same sentence once per strategy: fifty identical lines would
    bury the one that differs, so identical ones are counted, never dropped.
    """
    seen: dict[tuple, list] = {}
    for r, t in zip(results, titles):
        for w in r.get("warnings") or []:
            seen.setdefault((t, w["state"], w["text"]), []).append(w["code"])
    out = []
    for (t, state, body), codes in seen.items():
        c = colour(state)
        times = f"×{len(codes)} · " if len(codes) > 1 else ""
        line = text(f"{times}{t + ' · ' if t else ''}{body}", T["text"], 13)
        line.setStyleSheet(line.styleSheet() + f" border-left: 4px solid {c}; "
                           "padding: 4px 10px;")
        line.setToolTip(f"aviso «{codes[0]}» · {label(state)}: colorea, nunca elimina")
        out.append(line)
    return out


def _glossary(results: list[dict]) -> list[QWidget]:
    """Every term once, with its sentence."""
    terms = {g["term"]: g["text"] for r in results for g in r.get("glossary") or []}
    return [text(f"<b>{k}</b> — {v}", T["text"], 13) for k, v in terms.items()]


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
        if result is None:
            self._build([], [], [text("Sin resultado todavía: este estudio no ha corrido aquí.",
                                      T["muted"], 15)])
            return
        top = [_head(result, None)] + ([_stale(meta)] if meta and meta.get("stale") else [])
        self._build([result], [""], top)

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
        self._build([left, right], list(titles), [row])

    def _build(self, results: list[dict], titles: list[str], top: list[QWidget]) -> None:
        """Lay the page out again: header widgets, the tabs, the warnings, the glossary."""
        self.results, self.pages = results, {}
        self.content = QFrame()
        self.content.setObjectName("term")
        lay = QVBoxLayout(self.content)
        lay.setContentsMargins(16, 12, 16, 16)
        lay.setSpacing(10)
        for w in top:
            lay.addWidget(w)
        names = list(dict.fromkeys(t["name"] for r in results for t in r["tabs"]))
        self.names = names
        if names:
            self.tabs = QTabWidget()
            self.tabs.setDocumentMode(True)
            for n in names:
                tab = next(t for r in results for t in r["tabs"] if t["name"] == n)
                holder = QWidget()         # the page goes in on first opening: a population
                QVBoxLayout(holder).setContentsMargins(0, 0, 0, 0)   # has hundreds of tables
                i = self.tabs.addTab(holder, (tab.get("title") or n).replace("&", "&&"))
                self.tabs.setTabToolTip(i, tab.get("note") or tab.get("title") or n)
            self.tabs.currentChanged.connect(self._open)
            lay.addWidget(self.tabs)
            self.tabs.setCurrentIndex(names.index(self.tab) if self.tab in names else 0)
            self._open(self.tabs.currentIndex())
        warnings = _warnings(results, titles)
        if warnings:
            lay.addWidget(_section(f"avisos ({len(warnings)} distintos)"))
            for k, w in enumerate(warnings):
                lay.addWidget(w)
                w.setVisible(k < FOLD)
            if len(warnings) > FOLD:
                more = QPushButton(f"ver los {len(warnings) - FOLD} avisos restantes")
                more.clicked.connect(lambda: [w.setVisible(True) for w in warnings]
                                     + [more.hide()])
                lay.addWidget(more)
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
            page = TabPage(sides, self.memory.setdefault(name, {}))
            self.memory[name] = page.chosen
            self.pages[index] = page
            self.tabs.widget(index).layout().addWidget(page)
        self.tab = name
        # A QStackedWidget is as tall as its tallest page unless the others are Ignored:
        # without this a short tab would sit on the empty height of the longest one.
        for i in range(self.tabs.count()):
            policy = QSizePolicy.Preferred if i == index else QSizePolicy.Ignored
            self.tabs.widget(i).setSizePolicy(policy, policy)
        self.tabs.updateGeometry()
