"""The one design system: the palette every view reads, and the stylesheet it becomes."""

# One colour, one meaning, everywhere. The verdict scale is discrete and only ever has
# these five steps: a verdict is a decision the owner took, not a number to interpolate.
C = {"bg": "#0f1219", "panel": "#171c26", "raised": "#1e2431", "line": "#2a3140",
     "text": "#e7eaf0", "muted": "#8d96aa", "faint": "#5c6678", "accent": "#4c8dff",
     "promising": "#2fb98a", "weak": "#d9a441", "dead": "#c2515e",
     "pending": "#8390a8", "untried": "#141922"}

VERDICT_COLOUR = {"promising": C["promising"], "weak": C["weak"], "dead": C["dead"],
                  "": C["pending"]}
VERDICT_LABEL = {"promising": "prometedora", "weak": "floja", "dead": "muerta",
                 "": "sin veredicto"}


def verdict_colour(verdict: str) -> str:
    """The colour of one verdict, whatever the CSV holds.

    Args:
        verdict: The `verdict` column of a run.

    Returns:
        Its colour, or the pending grey for anything outside the three. The column is
        written by hand and by other sessions, so an unknown value is data to show, not an
        invariant to trust: looking it up straight is what shut the window on startup.
    """
    return VERDICT_COLOUR.get(verdict, C["pending"])


def verdict_label(verdict: str) -> str:
    """What one verdict says on screen, whatever the CSV holds.

    Args:
        verdict: The `verdict` column of a run.

    Returns:
        Its label, or the value itself quoted and called unknown, so a note somebody wrote
        into the column is visible instead of silently painted as «sin veredicto».
    """
    return VERDICT_LABEL.get(verdict, f"veredicto desconocido: «{verdict}»")


STATUS_COLOUR = {"buildConfirmed": C["promising"], "validated": C["accent"],
                 "draft": C["weak"], "archived": C["faint"], "": C["faint"]}
STATUS_HELP = {
    "draft": "Escrita, sin comprobar. El XML puede no resolver.",
    "validated": "El XML resuelve y las referencias existen. Nadie la ha construido todavía.",
    "buildConfirmed": "Una construcción real sacó estrategias y llevan de verdad su bloque fijo.",
    "archived": "Fuera del trabajo diario. Su fila y sus corridas se conservan.",
}

QSS = f"""
QWidget {{ background: {C['bg']}; color: {C['text']};
           font-family: "Inter", "DejaVu Sans", sans-serif; font-size: 13px; }}
QLabel#h1 {{ font-size: 21px; font-weight: 600; }}
QLabel#h2 {{ font-size: 15px; font-weight: 600; }}
QLabel#muted {{ color: {C['muted']}; }}
QLabel#faint {{ color: {C['faint']}; font-size: 12px; }}
QFrame QLabel {{ background: transparent; }}

QFrame#sidebar {{ background: {C['panel']}; border-right: 1px solid {C['line']}; }}
QFrame#panel {{ background: {C['panel']}; border: 1px solid {C['line']}; border-radius: 8px; }}
QFrame#tile {{ background: {C['raised']}; border: 1px solid {C['line']}; border-radius: 8px; }}

QPushButton {{ background: {C['raised']}; border: 1px solid {C['line']};
               border-radius: 6px; padding: 7px 13px; }}
QPushButton:hover {{ border-color: {C['accent']}; }}
QPushButton:disabled {{ color: {C['faint']}; border-color: {C['line']}; }}
QPushButton#nav {{ background: transparent; border: none; text-align: left;
                   padding: 10px 16px; border-radius: 0; color: {C['muted']}; }}
QPushButton#nav:hover {{ background: {C['raised']}; color: {C['text']}; }}
QPushButton#nav[soon="true"] {{ color: {C['faint']}; }}
QPushButton#nav:checked {{ background: {C['raised']}; color: {C['text']};
                           border-left: 3px solid {C['accent']}; font-weight: 600; }}
QPushButton#primary {{ background: {C['accent']}; border-color: {C['accent']};
                       color: #ffffff; font-weight: 600; }}

QLineEdit, QTextEdit, QPlainTextEdit, QComboBox {{
    background: {C['raised']}; border: 1px solid {C['line']}; border-radius: 6px;
    padding: 7px 9px; selection-background-color: {C['accent']}; }}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus {{ border-color: {C['accent']}; }}
QComboBox QAbstractItemView {{ background: {C['raised']}; border: 1px solid {C['line']};
                               selection-background-color: {C['accent']}; }}

QTableWidget {{ background: {C['panel']}; gridline-color: {C['line']};
                border: 1px solid {C['line']}; border-radius: 8px; }}
QHeaderView::section {{ background: {C['panel']}; color: {C['muted']};
                        border: none; border-bottom: 1px solid {C['line']};
                        padding: 8px; font-weight: 600; }}
QTableWidget::item:selected {{ background: {C['raised']}; color: {C['text']}; }}

QListWidget {{ background: {C['panel']}; border: 1px solid {C['line']};
               border-radius: 8px; padding: 4px; }}
QListWidget::item {{ padding: 9px 10px; border-radius: 6px; }}
QListWidget::item:selected {{ background: {C['raised']}; }}

QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {C['line']}; border-radius: 5px; min-height: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
QToolTip {{ background: {C['raised']}; color: {C['text']}; border: 1px solid {C['accent']};
            padding: 6px; }}
"""


def chip(text: str, colour: str) -> str:
    """One coloured label, as the rich text a QLabel renders.

    Args:
        text: What the chip says.
        colour: Hex colour of its text and border.

    Returns:
        HTML for a QLabel. Chips are text and not painted widgets so they sit inside the
        same layouts as everything else and inherit the window's font scaling.
    """
    return (f'<span style="color:{colour}; border:1px solid {colour}; border-radius:9px; '
            f'padding:1px 8px; font-size:11px;">{text}</span>')


# The second look, for the zones from «Estrategias» on: a terminal of analysis rather than a
# dashboard. Neutral near-black with no blue cast, one monospace face for every figure and
# identifier, tabular digits so columns read without being looked at, rows of 24 px and thin
# rules instead of cards. Colour keeps the same five meanings as `C`; nothing here is decorative.
T = {"bg": "#0b0b0c", "panel": "#111113", "line": "#232326", "rule": "#2e2e33",
     "text": "#e6e6e3", "muted": "#8a8a90", "faint": "#55555c", "select": "#1c1c20"}
MONO = '"JetBrains Mono", "DejaVu Sans Mono", monospace'

QSS += f"""
QFrame#term {{ background: {T['bg']}; border: none; }}
QFrame#term QWidget {{ background: {T['bg']}; color: {T['text']}; }}
QFrame#term QLabel#kicker {{ color: {T['muted']}; font-size: 11px; font-weight: 600;
                             letter-spacing: 1.5px; }}
QFrame#term QLabel#mono {{ font-family: {MONO}; font-size: 12px; }}
QFrame#term QLabel#figure {{ font-family: {MONO}; font-size: 26px; font-weight: 600; }}
QFrame#term QLabel#dim {{ color: {T['faint']}; font-family: {MONO}; font-size: 12px; }}
QFrame#term QFrame#rule {{ background: {T['rule']}; max-height: 1px; min-height: 1px; }}
QFrame#term QTableWidget, QFrame#term QListWidget {{
    background: {T['bg']}; border: none; border-top: 1px solid {T['rule']};
    border-radius: 0; gridline-color: {T['line']}; font-family: {MONO}; font-size: 12px;
    padding: 0; }}
QFrame#term QHeaderView::section {{ background: {T['bg']}; color: {T['muted']};
    border: none; border-bottom: 1px solid {T['rule']}; padding: 4px 6px;
    font-family: {MONO}; font-size: 11px; font-weight: 600; }}
QFrame#term QTableWidget::item {{ padding: 0 6px; }}
QFrame#term QTableWidget::item:selected, QFrame#term QListWidget::item:selected {{
    background: {T['select']}; color: {T['text']}; }}
QFrame#term QListWidget::item {{ padding: 3px 8px; border-radius: 0; }}
QFrame#term QPushButton {{ background: transparent; border: 1px solid {T['rule']};
    border-radius: 2px; padding: 3px 10px; font-family: {MONO}; font-size: 11px; }}
QFrame#term QPushButton:hover {{ border-color: {T['text']}; }}
QFrame#term QLineEdit {{ background: {T['panel']}; border: 1px solid {T['rule']};
    border-radius: 2px; padding: 4px 8px; font-family: {MONO}; font-size: 12px; }}
QFrame#term QScrollBar::handle:vertical, QFrame#term QScrollBar::handle:horizontal {{
    background: {T['rule']}; }}
QFrame#term QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
QFrame#term QScrollBar::handle:horizontal {{ border-radius: 5px; min-width: 30px; }}
"""


def state_colour(value: str) -> str:
    """The colour of one verdict word, whatever module wrote it.

    Args:
        value: The `verdict`, `tier` or `stage` a report row carries.

    Returns:
        Green for what passed, red for what died, amber for a middle word, grey for a word
        no module of this project uses — shown, never hidden.
    """
    v = value.lower()
    if v in {"pass", "proceed", "keep", "mantener", "worth_it", "promising", "reliable"}:
        return C["promising"]
    if v in {"fail", "reject", "descartar", "not_worth_it", "dead"}:
        return C["dead"]
    if v in {"marginal", "dudosa", "provisional", "weak"}:
        return C["weak"]
    return C["pending"]
