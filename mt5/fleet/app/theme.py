"""MetaTracker's own look: the palette, the lights' colours and the stylesheet."""

BG, PANEL, LINE = "#0f1319", "#18202b", "#4a5d73"
TEXT, DIM, ACCENT = "#eef2f6", "#b3c0cf", "#5cc8ff"
LIGHTS = {"green": "#3ddc84", "yellow": "#ffc832", "red": "#ff4d4d", "silent": "#a3adb8",
          "unknown": "#b48cff"}
GAIN, LOSS = "#3ddc84", "#ff6b6b"

SHEET = f"""
QWidget {{ background: {BG}; color: {TEXT}; font-family: "DejaVu Sans"; font-size: 15px; }}
QLabel {{ background: transparent; }}
QLabel#title {{ font-size: 26px; font-weight: bold; color: {ACCENT}; }}
QLabel#clock {{ color: {DIM}; }}
QLabel#section {{ font-size: 17px; font-weight: bold; color: {ACCENT}; padding-top: 10px; }}
QLabel#reasons {{ font-size: 16px; padding: 6px 4px; }}
QLabel#notes {{ color: {LIGHTS['yellow']}; }}
QLabel#empty {{ color: {DIM}; font-size: 16px; background: {PANEL}; border: 1px solid {LINE};
                border-radius: 6px; padding: 16px; }}
QLabel#legend {{ color: {DIM}; font-size: 14px; background: {PANEL}; border: 1px solid {LINE};
                 border-radius: 6px; padding: 12px; }}
QFrame#card {{ background: {PANEL}; border: 1px solid {LINE}; border-radius: 8px; }}
QLabel#cardname {{ color: {DIM}; font-size: 14px; }}
QLabel#cardvalue {{ font-size: 24px; font-weight: bold; font-family: "DejaVu Sans Mono"; }}
QScrollArea {{ border: 0; }}
QTabWidget::pane {{ border: 1px solid {LINE}; border-radius: 6px; top: -1px; }}
QTabBar::tab {{ background: {PANEL}; color: {DIM}; border: 1px solid {LINE}; border-bottom: 0;
                padding: 10px 26px; font-size: 16px; font-weight: bold; margin-right: 4px;
                border-top-left-radius: 6px; border-top-right-radius: 6px; }}
QTabBar::tab:selected {{ background: #25405c; color: {TEXT}; border-color: {ACCENT}; }}
QTableWidget {{ background: {PANEL}; border: 1px solid {LINE}; border-radius: 6px;
                gridline-color: {LINE}; font-family: "DejaVu Sans Mono"; font-size: 15px; }}
QTableWidget::item {{ padding: 6px 8px; }}
QHeaderView::section {{ background: #212c3a; color: {DIM}; border: 0; border-bottom: 1px solid {LINE};
                        padding: 8px 8px; font-weight: bold; font-size: 14px; }}
"""
