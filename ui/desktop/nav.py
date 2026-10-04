"""The sidebar: every zone in its group, one checkable button each."""

from collections.abc import Callable

from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout

from ui.desktop.theme import C

# The groups of the window (encargo 22 §2), in the order the owner walks them: the library
# he builds from, the project he is judging (Proyectos → Proyecto → Databanks → Estrategia),
# what is running,
# and the portfolios after step 20. «Trabajos» is not a zone: it is the strip in the status bar.
# The five older PROYECTO zones were retired by F13 of plan 24 (2026-09-28): their content lives
# in Proyecto and Estrategia (ui/desktop/README.md). Databanks was split out of Proyecto the
# same day: the two did not fit one screen (owner, 2026-09-28).
#
# Owner, 2026-10-03: the five template views are ONE place. The sidebar holds its front page,
# Cobertura; the other four are pages of the strip the shell shows above it (`LIBRARY`, in the
# workflow's order: where to look, what exists, a new one, its blocks). They stay zones — a
# name `open_zone`, Ctrl+K and `--zone` open — but have no sidebar button.
# To go back to five sidebar entries: put the four names back in «Biblioteca» below and set
# `LIBRARY = []`. Nothing else reads either.
LIBRARY = ["Cobertura", "Investigar", "Plantillas", "Nueva plantilla", "Paletas"]
GROUPS = [
    ("Biblioteca", ["Cobertura", "Activos", "Configuración SQX", "Datos"]),
    ("Proyecto", ["Proyectos", "Proyecto", "Databanks", "Estrategia", "Criterios"]),
    ("Operación", ["En marcha", "Registro de búsquedas"]),
    # Owner, 2026-09-29: the bridge with MetaTrader 5 is a section of this same window; before
    # the portfolios, which go last (owner, 2026-10-03).
    ("MT5 Bridge", ["Verificar"]),
    ("Portfolios", ["Portfolios"]),
]
SIDEBAR = [name for _, names in GROUPS for name in names]
ZONES = SIDEBAR + [name for name in LIBRARY if name not in SIDEBAR]
# The sidebar's own words for a button whose zone is more than its name says.
LABEL = {"Cobertura": "Cobertura y plantillas"} if LIBRARY else {}
# What each zone is, on hover.
TIPS = {
    "Cobertura": "La portada de la biblioteca: lo probado por familia, activo y timeframe, la "
                 "propuesta del director, y desde cada celda sus plantillas, su paleta, una "
                 "plantilla nueva o lo que se mide ahí.",
    "Plantillas": "La librería de plantillas y borradores, con la ficha de cada una.",
    "Investigar": "Dónde investigar: el mapa de los mercados, la memoria de lo probado, el "
                  "director de investigación y su propuesta de tres ideas.",
    "Nueva plantilla": "La entrevista que redacta el borrador de una plantilla nueva.",
    "Paletas": "Las paletas de bloques que alimentan los huecos libres de las plantillas.",
    "Activos": "Costes, tramos, rangos del MC Retest y mercados cruzados de cada activo.",
    "Proyectos": "Una tarjeta por proyecto de cualquier install: símbolo, timeframe, "
                 "estrategias, plantilla y estado.",
    "Proyecto": "El proyecto elegido: el workflow — lanzar en SQX, continuar workflow, el "
                "raíl de pasos — y el embudo de la población.",
    "Databanks": "Los databanks del proyecto elegido: filtros, pestañas por paso, la tabla de "
                 "estrategias y su equity agregada.",
    "Criterios": "Lo que tiene que cumplir una estrategia en cada paso del workflow para "
                 "pasar sola al siguiente: se ven, se editan y se congelan.",
    "Estrategia": "La ficha de la estrategia elegida: curvas, estadísticas IS/OOS1/OOS2, "
                  "sus estudios y metadatos.",
    "Configuración SQX": "Los parámetros de entrada de SQX por test, para los proyectos que "
                         "se creen a partir de ahora.",
    "Datos": "El catálogo de AlgoData, las velas por activo y los estudios del paso 4.",
    "En marcha": "Lo que corre en SQX, en una pantalla: el pulso del custodio (backtests, JVM "
                 "contra -Xmx, CPU, RAM libre) y las tareas del mismo proyecto una a una.",
    "Registro de búsquedas": "Una línea por búsqueda que miró datos y redujo una población, "
                             "los filtros de la ventana incluidos: cuánto se ha buscado en "
                             "cada estudio y qué tramos se han gastado.",
    "Portfolios": "Las estrategias archivadas: se importan a la ficha de Estrategia tal como "
                  "se guardaron, sin recalcular nada.",
    "Verificar": "El paso 26: la estrategia en SQX con las condiciones de cada empresa contra "
                 "su backtest en MT5 en la cuenta de esa empresa.",
}


def reload_tip(zones: list[str]) -> str:
    """What the «Recargar» button says on hover.

    Args:
        zones: The zones the shell's `refresh` reloads, in its order.

    Returns:
        The sentence: which zones it reloads, and that the others read on their own.
    """
    return ("Vuelve a leer del demonio la zona abierta ahora mismo, y deja pendientes de releer "
            "al abrirlas las demás que leen una sola vez: " + ", ".join(zones) + ". El resto lee "
            "solo al abrirse o al cambiar la selección, y no necesita este botón.")


def sidebar(go: Callable[[str], None], reload: Callable[[], None],
            reloads: list[str]) -> tuple[QFrame, dict]:
    """The navigation column down the left.

    Args:
        go: Called with a zone's name when its button is pressed.
        reload: Called by the «Recargar» button at the foot.
        reloads: The zones `reload` reloads, named in its tooltip.

    Returns:
        The framed column, and `{zone name: its button}` so the shell can mark the open one.
    """
    f = QFrame(objectName="sidebar")
    f.setFixedWidth(224)             # «Registro de búsquedas» in bold fits
    lay = QVBoxLayout(f)
    lay.setContentsMargins(0, 18, 0, 14)
    lay.setSpacing(1)
    brand = QLabel("  AlgoProject")
    brand.setStyleSheet("font-size:16px; font-weight:700; padding:0 16px 8px 16px;")
    lay.addWidget(brand)
    buttons = {}
    for group, names in GROUPS:
        head = QLabel(group)
        # Owner, 2026-10-03: the titles were 11 px and faint, «pequeñísimos» beside the zones.
        head.setStyleSheet(f"color:{C['accent']}; font-size:16px; font-weight:700; "
                           "padding:16px 16px 5px 16px;")
        lay.addWidget(head)
        for name in names:
            b = QPushButton(LABEL.get(name, name), objectName="nav")
            b.setCheckable(True)
            b.setToolTip(TIPS[name])
            b.clicked.connect(lambda _, n=name: go(n))
            lay.addWidget(b)
            buttons[name] = b
    lay.addStretch()
    reload_btn = QPushButton("Recargar", toolTip=reload_tip(reloads))
    reload_btn.clicked.connect(reload)
    holder = QVBoxLayout()
    holder.setContentsMargins(12, 0, 12, 0)
    holder.addWidget(reload_btn)
    lay.addLayout(holder)
    return f, buttons
