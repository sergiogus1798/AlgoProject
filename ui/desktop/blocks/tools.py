"""Above a result: the report of what is on screen, and the partial re-runs kept beside the stored result."""

from collections.abc import Callable

import httpx
from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from ui.desktop import client
from ui.desktop.blocks.card import text
from ui.desktop.blocks.screen import screen
from ui.text.glossary import label
from ui.desktop.theme import T


def report(results: list[dict], titles: list[str], memory: dict[str, dict],
           path: str | None) -> str:
    """Have the daemon write what is on screen as a page, through `core.study.render`, and open it.

    Args:
        results: The results on screen, one or two.
        titles: What each column is ("" for a lone result).
        memory: {tab name: chosen values}, as `ResultView` keeps them.
        path: The stored result's JSON, which says where the page goes; None when the
            result was not read from a report.

    Returns:
        The sentence to show: where the page was written, or why it was not.
    """
    if not path:
        return "Este resultado no viene de un informe guardado: no hay dónde escribir la página."
    body = {"results": [screen(r, memory, len(results) == 1) for r in results],
            "titles": titles, "path": path}
    try:
        got = client.post("study/screen", body)
    except httpx.HTTPError as e:      # the boundary with a person: said, never raised
        return f"El demonio no respondió a /api/study/screen: {e}"
    if "error" in got:
        return got["error"]
    QDesktopServices.openUrl(QUrl.fromLocalFile(got["html"]))
    return f"Informe de lo que ves escrito en {got['html']}"


def strip(partials: list[dict], beside: Callable[[int], None], merged: Callable[[int], None],
          stored: Callable[[], None], showing: str) -> QWidget:
    """The partial re-runs of this strategy, each with «al lado» and «fusionado», and the way back.

    Args:
        partials: `result["partials"]` as the daemon attached them, newest first.
        beside, merged: Called with a partial's index.
        stored: Called to draw the stored result alone again.
        showing: What is on screen now: "stored", "beside:<i>" or "merged:<i>".

    Returns:
        The strip; the pressed view's button is disabled so the reader sees where he is.
    """
    box = QWidget()
    lay = QVBoxLayout(box)
    lay.setContentsMargins(0, 4, 0, 4)
    lay.addWidget(text(f"{label('partial.head').upper()} ({len(partials)})", T["text"], 11, True))
    back = QPushButton(label("partial.stored"))
    back.setEnabled(showing != "stored")
    back.clicked.connect(stored)
    lay.addWidget(back)
    for i, p in enumerate(partials):
        row = QHBoxLayout()
        row.addWidget(text(f"solo <b>{p['only']}</b> · {p['computed_at']}", T["text"], 13), 1)
        for name, act, tag in (("partial.beside", beside, f"beside:{i}"),
                               ("partial.merged", merged, f"merged:{i}")):
            b = QPushButton(label(name))
            b.setEnabled(showing != tag)
            b.setToolTip("Al lado: el guardado a la izquierda y la re-ejecución a la derecha, "
                         "bloque con bloque. Fusionado: el guardado con esta subprueba tomada "
                         "de la re-ejecución. Ninguno de los dos toca el fichero guardado ni su "
                         "veredicto.")
            b.clicked.connect(lambda _=False, act=act, i=i: act(i))
            row.addWidget(b)
        lay.addLayout(row)
    return box
