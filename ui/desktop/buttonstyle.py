"""How a button looks: lit and clickable when it can be pressed, inert when it cannot, in both
looks of the window, and the round «?» mark `helpmark` puts beside it."""

# Owner, 2026-09-28: «en todos los botones, cuando sea posible pulsarlos, que se vea bien que
# son interactivos, ya sea con una luz o algo». Qt's stylesheets have no shadow, so the light is
# an accent border over a fill that brightens towards the top; hovering brightens both (the
# glow), pressing darkens the fill. A disabled button loses the accent and draws a dashed edge.
# Every shade here is the accent `C['accent']` (#8a7dff) mixed into the background it sits on.
LIT = {"edge": "#6c61d6", "glow": "#c3bbff", "top": "#2c2f4d", "bottom": "#1f2233",
       "hover_top": "#3b3f6b", "hover_bottom": "#2a2d48", "press": "#15172a",
       "checked": "#34306a", "primary_hover": "#a79dff", "primary_press": "#6f63e0",
       "term_top": "#1d1b2c", "term_bottom": "#121117", "term_hover": "#2a2644",
       "inert": "#465063"}


def gradient(top: str, bottom: str) -> str:
    """A vertical fill, lighter on top: the lit look."""
    return f"qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {top}, stop:1 {bottom})"


def qss(C: dict, T: dict, mono: str) -> str:
    """The button rules of both looks, appended by `theme` to its stylesheet.

    Args:
        C: The base palette.
        T: The terminal palette.
        mono: The monospace font family list.

    Returns:
        Stylesheet text. A button's own `setStyleSheet` still wins over it, property by property.
    """
    lit, hover = gradient(LIT["top"], LIT["bottom"]), gradient(LIT["hover_top"], LIT["hover_bottom"])
    term, term_hover = gradient(LIT["term_top"], LIT["term_bottom"]), LIT["term_hover"]
    return f"""
QPushButton, QToolButton {{ background: {lit}; color: {C['text']};
    border: 1px solid {LIT['edge']}; border-radius: 6px; padding: 7px 13px; }}
QPushButton:hover, QToolButton:hover {{ background: {hover}; border-color: {LIT['glow']}; }}
QPushButton:pressed, QToolButton:pressed {{ background: {LIT['press']}; border-color: {C['accent']}; }}
QPushButton:checked, QToolButton:checked {{ background: {LIT['checked']};
    border-color: {LIT['glow']}; font-weight: 700; }}
QPushButton:disabled, QToolButton:disabled {{ background: transparent; color: {C['faint']};
    border: 1px dashed {LIT['inert']}; }}
QPushButton#nav {{ background: transparent; border: none; text-align: left;
                   padding: 10px 16px; border-radius: 0; color: {C['muted']}; font-weight: 400; }}
QPushButton#nav:hover {{ background: {C['raised']}; color: {C['text']}; }}
QPushButton#nav:checked {{ background: {C['raised']}; color: {C['text']};
                           border-left: 3px solid {C['accent']}; font-weight: 600; }}
QPushButton#primary {{ background: {C['accent']}; border-color: {C['accent']};
                       color: #ffffff; font-weight: 600; }}
QPushButton#primary:hover {{ background: {LIT['primary_hover']}; border-color: {LIT['glow']}; }}
QPushButton#primary:pressed {{ background: {LIT['primary_press']}; }}
QPushButton#primary:disabled {{ background: transparent; color: {C['faint']};
                                border: 1px dashed {LIT['inert']}; }}
QTabBar QToolButton, QLineEdit QToolButton {{ background: {C['panel']}; border: none;
    padding: 0; border-radius: 0; }}
QCalendarWidget QToolButton {{ background: {C['raised']}; color: {C['text']}; border: none;
    border-radius: 4px; padding: 4px 8px; font-weight: 600; }}
QCalendarWidget QToolButton:hover {{ background: {C['line']}; }}

QFrame#term QPushButton, QFrame#term QToolButton {{ background: {term}; color: {T['text']};
    border: 1px solid {LIT['edge']}; border-radius: 3px; padding: 3px 10px;
    font-family: {mono}; font-size: 12px; font-weight: 700; }}
QFrame#term QPushButton:hover, QFrame#term QToolButton:hover {{ background: {term_hover};
    border-color: {LIT['glow']}; }}
QFrame#term QPushButton:pressed, QFrame#term QToolButton:pressed {{ background: {T['bg']};
    border-color: {C['accent']}; }}
QFrame#term QPushButton:checked, QFrame#term QToolButton:checked {{ background: {LIT['checked']};
    border-color: {LIT['glow']}; }}
QFrame#term QPushButton:disabled, QFrame#term QToolButton:disabled {{ background: transparent;
    color: {T['faint']}; border: 1px dashed {T['rule']}; }}

QLabel#helpmark, QFrame#term QLabel#helpmark {{ background: transparent; color: {C['muted']};
    border: 1px solid {C['faint']}; border-radius: 8px; font-family: {mono}; font-size: 11px;
    font-weight: 700; padding: 0; }}
QLabel#helpmark:hover, QFrame#term QLabel#helpmark:hover {{ color: {C['accent']};
    border-color: {C['accent']}; background: {C['raised']}; }}
"""
