"""The one design system: the palette every view reads, the stylesheet it becomes, and the two
smallest pieces every zone draws with (a rule, a kicker)."""

from PySide6.QtWidgets import QFrame, QLabel

from ui.desktop import buttonstyle

# One colour, one meaning, everywhere. The verdict scale is discrete and only ever has
# these five steps: a verdict is a decision the owner took, not a number to interpolate.
C = {"bg": "#0f1219", "panel": "#171c26", "raised": "#1e2431", "line": "#2a3140",
     "text": "#e7eaf0", "muted": "#8d96aa", "faint": "#5c6678", "accent": "#8a7dff",
     "promising": "#2fb98a", "weak": "#d9a441", "dead": "#c2515e",
     "pending": "#8390a8", "untried": "#141922"}

# Scroll bars and splitter handles: a track that shows where the bar is, a handle that stands out.
BAR = {"track": "#262c38", "handle": "#7d879b"}

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
    "archived": "Fuera del trabajo diario. Su fila y sus runs se conservan.",
}

# Owner, 2026-09-27 (encargo 22 §10): one step larger everywhere, a livelier accent (violet: it
# collides with none of the verdict colours), a little more separation between sections, and
# the active tab drawn as a rounded box instead of Qt's underline.
QSS = f"""
QWidget {{ background: {C['bg']}; color: {C['text']};
           font-family: "Inter", "DejaVu Sans", sans-serif; font-size: 14px; }}
QLabel#h1 {{ font-size: 22px; font-weight: 600; }}
QLabel#h2 {{ font-size: 16px; font-weight: 600; }}
QLabel#muted {{ color: {C['muted']}; }}
QLabel#faint {{ color: {C['faint']}; font-size: 13px; }}
QLabel#readonly {{ background: {C['raised']}; color: {C['weak']}; border: 1px solid {C['weak']};
                   border-radius: 6px; padding: 6px 12px; font-weight: 700; }}
QFrame QLabel {{ background: transparent; }}

QFrame#sidebar {{ background: {C['panel']}; border-right: 1px solid {C['line']}; }}
QFrame#panel {{ background: {C['panel']}; border: 1px solid {C['line']}; border-radius: 8px; }}
QFrame#tile {{ background: {C['raised']}; border: 1px solid {C['line']}; border-radius: 8px; }}

QLineEdit, QTextEdit, QPlainTextEdit, QComboBox {{
    background: {C['raised']}; border: 1px solid {C['line']}; border-radius: 6px;
    padding: 7px 9px; selection-background-color: {C['accent']}; }}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus {{ border-color: {C['accent']}; }}
QComboBox QAbstractItemView {{ background: {C['raised']}; border: 1px solid {C['line']};
                               selection-background-color: {C['accent']}; }}
/* A plain list popup, not the menu style: that one reserved two scroller arrows inside the
   rows' height and showed 2 of 4 options (2026-10-01). `combofix` sizes it to the screen. */
QComboBox {{ combobox-popup: 0; }}
QComboBox QAbstractItemView::item {{ padding: 4px 8px; }}

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

/* Scroll bars and splitter handles meant to be SEEN (owner, 2026-09-28: «mucho más claras, en
   todos los lugares»): a visible track, a light handle, the accent under the mouse. */
QScrollBar:vertical {{ background: {BAR['track']}; width: 14px; margin: 0; border-radius: 7px; }}
QScrollBar:horizontal {{ background: {BAR['track']}; height: 14px; margin: 0; border-radius: 7px; }}
QScrollBar::handle:vertical {{ background: {BAR['handle']}; border-radius: 6px; min-height: 40px;
    margin: 2px; }}
QScrollBar::handle:horizontal {{ background: {BAR['handle']}; border-radius: 6px; min-width: 40px;
    margin: 2px; }}
QScrollBar::handle:hover, QScrollBar::handle:pressed {{ background: {C['accent']}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: none; }}
QSplitter::handle {{ background: {BAR['track']}; }}
QSplitter::handle:vertical {{ height: 9px; }}
QSplitter::handle:horizontal {{ width: 9px; }}
QSplitter::handle:hover, QSplitter::handle:pressed {{ background: {C['accent']}; }}
QToolTip {{ background: {C['raised']}; color: {C['text']}; border: 1px solid {C['accent']};
            padding: 6px; }}

QTabWidget::pane {{ border: none; border-top: 1px solid {C['line']}; }}
QTabBar {{ qproperty-drawBase: 0; }}
QTabBar::tab {{ background: transparent; color: {C['muted']}; border: 1px solid transparent;
                border-radius: 7px; padding: 5px 14px; margin: 3px 3px 5px 0; }}
QTabBar::tab:hover {{ color: {C['text']}; border-color: {C['line']}; }}
QTabBar::tab:selected {{ background: {C['raised']}; color: {C['text']};
                         border: 1px solid {C['accent']}; font-weight: 700; }}
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


# The second look, for every zone built since 2026-09-25: a terminal of analysis rather than a
# dashboard. Neutral near-black with no blue cast, one monospace face for every figure and
# identifier, tabular digits so columns read without being looked at, rows of 24 px and thin
# rules instead of cards. Colour keeps the same five meanings as `C`; nothing here is decorative.
# Owner, 2026-09-25: the greys were unreadable. `muted` and `faint` are now light enough to
# read as text, not as decoration; hierarchy comes from weight, not from fading.
# 2026-09-27: `rule` one step lighter, so sections part visibly, and `accent` — the touch of
# colour inside the terminal look: kickers and the active tab, never a meaning.
T = {"bg": "#0b0b0c", "panel": "#111113", "line": "#232326", "rule": "#3e3e46",
     "text": "#f0f0ec", "muted": "#c2c2c8", "faint": "#9a9aa2",
     # 2026-09-29 (feedback §1.6): the selected row of a term list/table/tab was almost the
     # same shade as the background — a card someone picked in Configuración SQX did not read
     # as picked. Lighter and tinted with the accent so a selection is unmistakable.
     "select": "#332c52", "accent": C["accent"]}
MONO = '"JetBrains Mono", "DejaVu Sans Mono", monospace'

QSS += f"""
QFrame#term {{ background: {T['bg']}; border: none; }}
QFrame#term QWidget {{ background: {T['bg']}; color: {T['text']}; }}
QFrame#term QLabel#kicker {{ color: {T['accent']}; font-size: 12px; font-weight: 700;
                             letter-spacing: 1.5px; }}
QFrame#term QLabel#mono {{ font-family: {MONO}; font-size: 13px; font-weight: 600; }}
QFrame#term QLabel#figure {{ font-family: {MONO}; font-size: 26px; font-weight: 700; }}
QFrame#term QLabel#dim {{ color: {T['faint']}; font-family: {MONO}; font-size: 13px; }}
QFrame#term QLabel#h1 {{ font-weight: 700; }}
QFrame#term QFrame#rule {{ background: {T['rule']}; max-height: 1px; min-height: 1px; }}
QFrame#term QTableWidget, QFrame#term QListWidget {{
    background: {T['bg']}; border: none; border-top: 1px solid {T['rule']};
    border-radius: 0; gridline-color: {T['line']}; font-family: {MONO}; font-size: 13px;
    padding: 0; }}
QFrame#term QHeaderView::section {{ background: {T['bg']}; color: {T['text']};
    border: none; border-bottom: 1px solid {T['rule']}; padding: 4px 6px;
    font-family: {MONO}; font-size: 12px; font-weight: 700; }}
QFrame#term QTableWidget::item {{ padding: 0 6px; }}
QFrame#term QTableWidget::item:selected, QFrame#term QListWidget::item:selected {{
    background: {T['select']}; color: {T['text']}; }}
QFrame#term QListWidget::item {{ padding: 3px 8px; border-radius: 0; }}
QFrame#term QComboBox {{ background: {T['panel']}; border: 1px solid {T['rule']};
    border-radius: 2px; padding: 3px 8px; font-family: {MONO}; font-weight: 700; }}
QFrame#term QCheckBox {{ font-weight: 600; }}
QFrame#term QLineEdit {{ background: {T['panel']}; border: 1px solid {T['rule']};
    border-radius: 2px; padding: 4px 8px; font-family: {MONO}; font-size: 13px; }}
QFrame#term QScrollBar:vertical, QFrame#term QScrollBar:horizontal {{
    background: {BAR['track']}; }}
QFrame#term QScrollBar::handle:vertical, QFrame#term QScrollBar::handle:horizontal {{
    background: {BAR['handle']}; }}
QFrame#term QScrollBar::handle:hover, QFrame#term QScrollBar::handle:pressed {{
    background: {C['accent']}; }}
QFrame#term QSplitter::handle {{ background: {BAR['track']}; }}
QFrame#term QSplitter::handle:hover, QFrame#term QSplitter::handle:pressed {{
    background: {C['accent']}; }}
QFrame#term QTabWidget::pane {{ border: none; border-top: 1px solid {T['rule']}; }}
QFrame#term QTabBar::tab {{ background: transparent; color: {T['muted']};
    border: 1px solid transparent; border-radius: 7px; padding: 4px 12px;
    margin: 3px 3px 5px 0; font-family: {MONO}; font-size: 13px; font-weight: 600; }}
QFrame#term QTabBar::tab:hover {{ color: {T['text']}; border-color: {T['rule']}; }}
QFrame#term QTabBar::tab:selected {{ background: {T['select']}; color: {T['text']};
    border: 1px solid {T['accent']}; font-weight: 700; }}
QFrame#term QTabBar::tab:disabled {{ color: {T['faint']}; }}
"""
QSS += buttonstyle.qss(C, T, MONO)    # after both looks: buttons lit, the «?» mark


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


def rule() -> QFrame:
    """A one-pixel horizontal line, which the stylesheet paints as a rule."""
    return QFrame(objectName="rule")


def kicker(text: str) -> QLabel:
    """A small spaced-out heading, upper-cased on screen.

    Args:
        text: The heading.
    """
    return QLabel(text.upper(), objectName="kicker")
