"""The owner's words the workspace shows: each family's line, the preflight, step notes, where each ⚙ goes."""

# Family name as the study page's tab shows it → its one line (encargo 22 §5).
FAMILIES = {
    "Ficha": "IS y OOS lado a lado: P&L acumulado, drawdown y P&L por año; y el lote.",
    "Cribado": "Las cribas IS/OOS que pasó o la tiraron: degradación, coste, muestreo.",
    "Transferencia": "Si el edge viaja: otros mercados y otros timeframes, contra su nulo.",
    "Rotura": "MC Retest: qué perturbación la rompe y cuánto, una tarea por causa.",
    "Optimización": "SPP, variantes, WFC y CSCV: si el óptimo es meseta o pico.",
    "Cierre": "WFM y el análisis conjunto de 17, 18, 18.5 y 19.",
    "Lecturas": "Monkey, exposición, mapa condicional y estructura.",
}

# What the rail's step 4 and every launcher's preflight check, for the drawer under the rail
# (owner, 2026-09-28: «no entiendo "Preflight USDJPY pasa hoy"»). Read from core.assetcheck,
# ui/daemon/launch/preflight.py and ui/daemon/advance/preflight.py: keep in step with them.
PREFLIGHT = (
    "QUÉ ES EL PREFLIGHT. Una comprobación que se hace antes de gastar CPU, para no construir "
    "ni retestear sobre algo mal puesto. Hay dos, y ninguna toca SQX: sólo leen ficheros.\n"
    "1 · El del activo (este paso 4, core.assetcheck). Mira la ficha del activo en Activos: "
    "que tenga decididos los costes que exige su clase (spread y comisión; en un no-forex, el "
    "spread del IS y el del OOS), que no le falte ni le sobre ningún campo, que el MC Retest "
    "tenga su rango de spread y de slippage, que los números del instrumento sean números, y "
    "que ningún tramo (build, oos1, oos2) empiece antes del primer dato que SQX tiene. Si algo "
    "falta, el paso se queda «bloqueado» y no se construye nada. Un coste marcado "
    "PROVISIONAL no bloquea, pero se dice: todo lo que se construya encima lo arrastra.\n"
    "2 · El de lanzar (el ▶ SQX de cada paso, «Lanzar en SQX», «Continuar workflow» y «Correr "
    "workflow»). Se repite en el momento de pulsar: que el proyecto no viva en el maestro, "
    "que esté en registry.csv y en un solo worker; que ese worker esté libre (su puerto no "
    "responde, ningún proceso de SQX corre desde él, ningún otro proyecto suyo se tocó en las "
    "últimas 24 h, su log no se escribió en los últimos 15 min ni dice que una corrida empezó "
    "y no acabó); que el proyecto lleve las tareas del paso; que un build vaya sólo al "
    "custodio; que la tarea tenga estrategias en su databank de entrada; y que no haya otro "
    "lanzamiento en cola. Si algo falla, el botón se apaga y dice por qué.")

# The steps whose short line the drawer shows under the step's own why.
STEP_NOTES = {
    "4": PREFLIGHT,
    "17": "QUÉ MIRA. Para cada madre, sus variantes (la misma lógica con otros parámetros): "
          "¿las que mejor van dentro de muestra son también las que mejor van fuera? Un punto "
          "por variante, beneficio IS contra beneficio OOS, y su correlación de rangos (rho). "
          "Una nube en diagonal ascendente dice que optimizar sirve; una nube sin forma, que el "
          "óptimo del IS es suerte. Describe, no descarta. Lee el oos2 y apunta su fila en el "
          "ledger.",
}

# Where the ⚙ of each step takes the owner to edit that step's configuration: a section of
# «Configuración SQX» (its key in /api/sqxconfig), or «Activos» on the project's asset.
SETTINGS = {"4": ("Activos", ""), "6": ("Configuración SQX", "complexity"),
            "7": ("Activos", ""), "9": ("Configuración SQX", "crossmarket"),
            "10.5": ("Configuración SQX", "crosstf"), "11": ("Configuración SQX", "crosstf"),
            "13": ("Configuración SQX", "mc_retest"), "15": ("Configuración SQX", "spp"),
            "16.5": ("Configuración SQX", "wfc"), "17": ("Configuración SQX", "wfc"),
            "18": ("Configuración SQX", "cscv"), "19": ("Configuración SQX", "wfm")}
# What the ⚙ says when the step's settings have no editing screen in the window.
NO_SCREEN = ("la ventana no tiene pantalla para editar su configuración: está en el "
             "config.yaml de cada estudio. Abajo, «configuración» la enseña (sólo lectura) con "
             "los valores que correrán para este proyecto.")
# Said on the SQX settings a step's ⚙ opens: they reach new projects, not this one's tasks.
NOT_YET = ("Lo que cambies aquí vale para los proyectos que se creen desde ahora: las tareas "
           "de {project} ya están escritas y «▶ SQX» no las reescribe. Para que el cambio llegue "
           "a este proyecto hay que volver a configurar el paso {n} (su skill en el chat). "
           "Vuelve con «Proyecto» en la barra de la izquierda.")
# Said instead for a Python step (17, 18): its study values are read again on the next run.
STUDY_NOW = ("Viene del paso {n} de {project}: los valores del estudio (su config.yaml) valen "
             "desde la próxima corrida. Vuelve con «Proyecto» en la barra de la izquierda.")


def informes(table: dict) -> str:
    """Why a databank's rows come from its reports and not its files, in one phrase.

    📓 2026-09-29: it said «vacío en el custodian» for WFM, SPP and Retest Markets while SQX
    wrote the project (the loader reads no file then) and «ya no está en ningún install» for
    MCR_All, which never was an SQX databank.
    """
    if table.get("writing"):
        return ("SQX está escribiendo este proyecto: filas de la cosecha y los informes hasta "
                "que acabe")
    if table.get("held_by"):
        return f"vacío en el {table['held_by']}: filas de la cosecha y los informes"
    if table.get("databank") == "MCR_All":
        return "la ingesta Python de las ocho MCR, no un databank de SQX: filas de sus informes"
    return "en ningún install: filas de la cosecha y los informes"


# The Databanks panel's tabs with no aggregate equity beside the table (owner, 2026-09-29):
# every test's databank, as the IS/OOS gate already was.
TABLE_ONLY = {"Puerta IS/OOS", "Cross Market", "Cross Timeframe", "MC Retest", "SPP", "WFM",
              "WFC", "CSCV", "Market Surfaces", "Cierre"}
# The ⚙ Métricas button's tooltip, which the «?» reads too.
CHOOSER = ("Elige qué métricas enseña la tabla: quita las de siempre (hasta dejar, por ejemplo, "
           "solo Beneficio neto y DD máximo) o añade cualquiera de IS, OOS1, OOS2 o IS+OOS1. "
           "Se guarda para este databank: vale en todas sus pestañas y al volver a abrir la "
           "ventana; otro databank (Cross Market, SPP…) guarda la suya.")
