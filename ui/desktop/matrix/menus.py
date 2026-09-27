"""The matrix's menus and filters: sort and filter one column, clear them, and pick a gate study to curate."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QMenu

from ui.desktop.blocks.states import label
from ui.desktop.matrix.model import FIXED

EVERY = ("pass", "watch", "fail", "info", "none", "missing")


def column_menu(view: QFrame, section: int) -> QMenu:
    """The menu of one column: two sorts, a check per state, and /curate for a gate study.

    Args:
        view: The `Matrix`.
        section: Model column.

    Returns:
        The menu, built but not shown.
    """
    model = view.model
    menu = QMenu(view)
    menu.addAction("ordenar ▲", lambda: model.sort(section, Qt.AscendingOrder))
    menu.addAction("ordenar ▼", lambda: model.sort(section, Qt.DescendingOrder))
    if section < len(FIXED):
        return menu
    key = model.field(section)
    menu.addSeparator()
    wanted = model.wanted.get(key)
    for state in EVERY:
        act = menu.addAction(f"mostrar «{label(state)}»")
        act.setCheckable(True)
        act.setChecked(wanted is None or state in wanted)
        act.toggled.connect(lambda on, s=state: want(view, key, s, on))
    if view.entry(key)["role"] == "gate":
        menu.addSeparator()
        menu.addAction("⊘ aplicar su veredicto con /curate…", lambda: show_curate(view, key))
    return menu


def want(view: QFrame, key: str, state: str, on: bool) -> None:
    """Show or hide the rows in one state of one column.

    Args:
        view: The `Matrix`.
        key: Study key.
        state: Contract state, or `missing`.
        on: Show (True) or hide.
    """
    model = view.model
    wanted = set(model.wanted.get(key, EVERY))
    wanted = wanted | {state} if on else wanted - {state}
    if wanted == set(EVERY):
        model.wanted.pop(key, None)
    else:
        model.wanted[key] = wanted
    view.header.filtered = set(model.wanted)
    model.refilter()


def clear_filters(view: QFrame) -> None:
    """Drop every state filter and the name filter."""
    view.model.wanted.clear()
    view.header.filtered = set()
    view.text.clear()
    view.model.refilter("")


def curate_menu(view: QFrame) -> None:
    """Pick which shown gate study's command to show."""
    menu = QMenu(view)
    for e in view.model.columns:
        if e["role"] == "gate":
            menu.addAction(e["title"], lambda k=e["key"]: show_curate(view, k))
    menu.exec(view.curate.mapToGlobal(view.curate.rect().bottomLeft()))


def show_curate(view: QFrame, key: str) -> None:
    """Show the /curate command for one gate study's newest verdict in this databank.

    Args:
        view: The `Matrix`.
        key: A gate study with at least one cell here.
    """
    cells = [row[key] for row in view.data["cells"].values() if key in row]
    day = max(c["day"] for c in cells)
    drops = sum(c["state"] == "fail" for c in cells if c["day"] == day)
    view.strip.show_for(*view.where, view.entry(key), day, drops)
