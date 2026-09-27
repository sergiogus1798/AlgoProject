"""The sidebar: every zone in its group, one checkable button each, the unbuilt ones included."""

from collections.abc import Callable

from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout

from ui.desktop.soon import ZONES as SOON
from ui.desktop.theme import C

# The four groups of the unified viewer (scratch/ui-plan/SPEC.md §0), in the order the owner
# walks them: the library he builds from, the project he is judging, what is running, and the
# portfolios after step 20. «Trabajos» is not a zone: it is the strip in the status bar.
GROUPS = [
    ("BIBLIOTECA", ["Cobertura", "Plantillas", "Nueva plantilla", "Paletas", "Activos", "Datos"]),
    ("PROYECTO", ["Workflow", "Población", "Estudio de población", "Estrategia", "Estrategias",
                  "Puerta IS/OOS"]),
    ("OPERACIÓN", ["Custodio", "Ledger", "Generación"]),
    ("CARTERAS", ["Carteras"]),
]
ZONES = [name for _, names in GROUPS for name in names]

# What each zone of the study viewer is, on hover. The older zones keep no tooltip; the
# unbuilt ones get theirs from `soon`.
TIPS = {
    "Workflow": "Los pasos de WORKFLOW.md para el proyecto elegido: estado, embudo, oos2.",
    "Población": "Las estrategias del databank contra los estudios: una celda por veredicto.",
    "Estudio de población": "Un estudio sobre todo el databank: su resultado, su configuración "
                            "y sus corridas.",
    "Estrategia": "Todos los estudios de la estrategia elegida, familia por familia.",
    "Estrategias": "La zona anterior: databanks, tabla de métricas y lo que dijo cada módulo.",
    "Puerta IS/OOS": "La zona anterior del paso 8: cosechas, embudo y scorecard.",
    "Custodio": "El pulso del custodio: backtests hechos, JVM contra -Xmx, CPU y RAM libre.",
    "Ledger": "El ledger de búsquedas: cuántas miradas se han gastado y en qué segmento.",
    "Generación": "Por dónde va el proyecto SQX que corre, tarea a tarea.",
}


def sidebar(go: Callable[[str], None], reload: Callable[[], None]) -> tuple[QFrame, dict]:
    """The navigation column down the left.

    Args:
        go: Called with a zone's name when its button is pressed.
        reload: Called by the «Recargar» button at the foot.

    Returns:
        The framed column, and `{zone name: its button}` so the shell can mark the open one.
    """
    f = QFrame(objectName="sidebar")
    f.setFixedWidth(208)
    lay = QVBoxLayout(f)
    lay.setContentsMargins(0, 18, 0, 14)
    lay.setSpacing(1)
    brand = QLabel("  AlgoProject")
    brand.setStyleSheet("font-size:16px; font-weight:700; padding:0 16px 8px 16px;")
    lay.addWidget(brand)
    buttons = {}
    for group, names in GROUPS:
        head = QLabel(group)
        head.setStyleSheet(f"color:{C['faint']}; font-size:11px; font-weight:700; "
                           "letter-spacing:1px; padding:12px 16px 4px 16px;")
        lay.addWidget(head)
        for name in names:
            b = QPushButton(name, objectName="nav")
            b.setCheckable(True)
            if name in SOON:
                b.setProperty("soon", True)
                b.setToolTip(f"{name}: todavía no. Ábrela para ver qué irá ahí y cómo se hace "
                             "hoy mientras tanto.")
            else:
                b.setToolTip(TIPS.get(name, ""))
            b.clicked.connect(lambda _, n=name: go(n))
            lay.addWidget(b)
            buttons[name] = b
    lay.addStretch()
    reload_btn = QPushButton("Recargar")
    reload_btn.clicked.connect(reload)
    holder = QVBoxLayout()
    holder.setContentsMargins(12, 0, 12, 0)
    holder.addWidget(reload_btn)
    lay.addLayout(holder)
    return f, buttons
