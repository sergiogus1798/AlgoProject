"""«Recargar databank»: the daemon relists the databank's folder off the GUI thread, then a repaint."""

from PySide6.QtWidgets import QWidget

from ui.desktop import background
from ui.text.numbers import num
from ui.text.brief import full, line


def ask(panel: QWidget) -> None:
    """Send POST /api/databank/reload for the databank on screen; `answered` reads the reply.

    Args:
        panel: The Databanks `Panel` (its `project`, `sub_spec`, `said`).
    """
    bank = panel.sub_spec().get("databank", "")
    if not bank:
        panel.said.setText("Este panel no tiene databank que recargar.")
        return
    panel.said.setText(f"Releyendo {bank}…")
    project = panel.project
    background.post("databank/reload", {"project": project, "databank": bank},
                    lambda got: answered(panel, project, bank, got), owner=panel)


def answered(panel: QWidget, project: str, bank: str, got: dict) -> None:
    """Drop what was read of that databank, read it again and say what the daemon found.

    Args:
        panel: The Databanks `Panel`.
        project, bank: What was asked; another project on screen now drops the answer.
        got: The daemon's answer, or `{"error": …}`.
    """
    if project != panel.project:
        return
    if "error" in got:
        panel.said.setText(line(got["error"]))
        panel.said.setToolTip(full(got["error"]))
        return
    panel.cache.pop(bank, None)
    panel.columns.forget(bank)
    panel.side.forget()
    panel.open_sub(panel.sub.currentIndex())
    load = got.get("load") or {}
    queued = load.get("queued") or []
    held = (f"{num(got['strategies'])} estrategias en disco" if got.get("strategies") else
            f"SQX está escribiendo {project} ahora: se relee cuando termine"
            if load.get("writing") else
            f"{bank} no tiene estrategias en disco: las filas son las de la cosecha y los "
            "informes" if load.get("role") else
            f"{bank} no está en ningún install: las filas siguen siendo las de la cosecha "
            "y los informes")
    panel.said.setText(f"Releído: {held}" + (f" · cargando {', '.join(queued)}" if queued
                                             else ""))
