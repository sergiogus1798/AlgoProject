"""«Archivar»: the dialog that asks the step and the note before the ficha freezes the strategy."""

from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit,
                               QPlainTextEdit, QVBoxLayout, QWidget)

WHAT = ("Congela la estrategia en AlgoData/archive/: su .sqx, sus filas de la cosecha, cada "
        "resultado de estudio que la nombra, la ficha de costes del activo y la cuenta del "
        "ledger de hoy. Una versión nueva cada vez; nunca se sobrescribe.")


def ask(parent: QWidget, name: str) -> dict | None:
    """Ask the owner for the note and the step before archiving.

    Args:
        parent: The ficha, for the dialog's placement.
        name: The strategy's name, in the title.

    Returns:
        `{note, step}`; None when cancelled; `{error}` when the step was left empty.
    """
    dialog = QDialog(parent)
    dialog.setWindowTitle(f"Archivar {name}")
    lay = QVBoxLayout(dialog)
    what = QLabel(WHAT, objectName="dim")
    what.setWordWrap(True)
    lay.addWidget(what)
    form = QFormLayout()
    # No default: the rail's last «hecho» step can be a reading run past a sealed 17-19, so
    # guessing where the strategy stands would write a wrong step into the manifest.
    step_box = QLineEdit()
    step_box.setPlaceholderText("p. ej. 16.5 — el paso del WORKFLOW en que está")
    note_box = QPlainTextEdit()
    note_box.setPlaceholderText("Por qué se archiva: se guarda tal cual.")
    form.addRow("Paso", step_box)
    form.addRow("Nota", note_box)
    lay.addLayout(form)
    buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    buttons.button(QDialogButtonBox.Ok).setText("Archivar")
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    lay.addWidget(buttons)
    if dialog.exec() != QDialog.Accepted:
        return None
    if not step_box.text().strip():
        return {"error": "No se archivó: falta el paso del WORKFLOW en que está la estrategia."}
    return {"note": note_box.toPlainText().strip(), "step": step_box.text().strip()}
