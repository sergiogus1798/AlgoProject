"""The buttons that open the study's side panel — configuración, historial, lote — folded by default."""

from PySide6.QtWidgets import QHBoxLayout, QPushButton, QSizePolicy, QTabWidget, QWidget

# The button of each side tab, by the tab's text; a tab with no row here gets no button.
BUTTONS = {
    "configuración": ("⚙ Configuración", "Abre los parámetros del estudio: lo que cambies aquí "
                      "solo vale para la próxima ejecución, como --set; el config.yaml no se toca."),
    "historial y comparar": ("Historial", "Abre los runs anteriores del estudio, para "
                             "ver una vieja o comparar dos, o esta estrategia contra otra."),
    "Lote": ("Lote", "Abre el lote de variantes de esta madre en coordenadas paralelas."),
}


class SideToggles(QWidget):
    """One checkable button per tab of `side`. The panel starts hidden, so the result takes the
    whole width (owner, 2026-09-30: always open, the knobs took the space the result needs);
    a button opens it on its tab, the same button again folds it."""

    def __init__(self, side: QTabWidget) -> None:
        """Hide `side` and build the buttons of the tabs it has now; `sync` adds later ones.

        Args:
            side: The study page's side `QTabWidget` (drawer, history, and «Lote» once built).
        """
        super().__init__()
        self.side = side
        self.buttons: dict[QWidget, QPushButton] = {}
        self.row = QHBoxLayout(self)
        self.row.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)    # never wider than its buttons
        side.hide()
        self.sync()

    def sync(self) -> None:
        """A button for each tab not yet given one, each shown only while its tab is."""
        for i in range(self.side.count()):
            page = self.side.widget(i)
            if page not in self.buttons and self.side.tabText(i) in BUTTONS:
                words, tip = BUTTONS[self.side.tabText(i)]
                b = QPushButton(words, checkable=True)
                b.setProperty("help", tip)
                b.clicked.connect(lambda _=False, p=page: self.toggle(p))
                self.row.addWidget(b)
                self.buttons[page] = b
            if page in self.buttons:
                self.buttons[page].setVisible(self.side.isTabVisible(i))
                if not self.side.isTabVisible(i) and self.side.currentWidget() is page:
                    self.fold()

    def toggle(self, page: QWidget) -> None:
        """Open the panel on `page`, or fold it when `page` is already what it shows."""
        if self.side.isVisible() and self.side.currentWidget() is page:
            return self.fold()
        self.side.setCurrentWidget(page)
        self.side.show()
        for p, b in self.buttons.items():
            b.setChecked(p is page)

    def fold(self) -> None:
        """Hide the panel and uncheck every button."""
        self.side.hide()
        for b in self.buttons.values():
            b.setChecked(False)
