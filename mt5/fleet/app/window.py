"""MetaTracker's window: the five tabs over the fleet, the refresh timer and the desktop notifications."""

import time
from datetime import datetime

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QLabel, QScrollArea, QTabWidget, QVBoxLayout, QWidget

from core import proc
from mt5.fleet.app import fmt, read, state, theme
from mt5.fleet.app.tab_deploy import DeployTab
from mt5.fleet.app.tab_fleet import FleetTab
from mt5.fleet.app.tab_health import HealthTab
from mt5.fleet.app.tab_reconcile import ReconcileTab
from mt5.fleet.app.tab_strategies import StrategiesTab

TABS = ["Flota", "Estrategias", "Despliegue", "Salud", "Conciliación"]


def tab_index(name: str) -> int:
    """The position of a tab by its name, ignoring case and accents: «conciliacion» is the fifth."""
    plain = {"ó": "o", "á": "a"}
    key = "".join(plain.get(c, c) for c in name.lower())
    return next(
        i
        for i, t in enumerate(TABS)
        if "".join(plain.get(c, c) for c in t.lower()) == key
    )


class Tracker(QWidget):
    """The window. It holds the tabs and the timer; every figure comes from `state.rows`."""

    def __init__(
        self,
        at: int | None = None,
        notify: bool = True,
        tab: str = "Flota",
        account: int | None = None,
    ) -> None:
        """Build the window and paint it once.

        Args:
            at: UTC epoch to read the fleet as of, instead of the clock — for a capture.
            notify: Whether a light turning red or silent raises a desktop notification.
            tab: The tab to open on.
            account: The login to choose in the Flota tab, for a capture; the first by default.
        """
        super().__init__()
        self.at, self.notify, self.seen, self.rows = at, notify, {}, []
        self.setWindowTitle("MetaTracker")
        self.setStyleSheet(theme.SHEET)
        self.resize(1700, 950)
        box = QVBoxLayout(self)
        box.setContentsMargins(22, 18, 22, 18)
        title = QLabel("MetaTracker — la flota de MT5 en la VPS")
        title.setObjectName("title")
        self.clock = QLabel()
        self.clock.setObjectName("clock")
        self.fleet, self.strategies, self.deploy = (
            FleetTab(),
            StrategiesTab(),
            DeployTab(),
        )
        self.health, self.reconcile = HealthTab(), ReconcileTab()
        self.tabs = QTabWidget()
        for page, name in zip(
            (self.fleet, self.strategies, self.deploy, self.health, self.reconcile),
            TABS,
        ):
            self.tabs.addTab(page, name)
        self.tabs.setCurrentIndex(tab_index(tab))
        for w in (title, self.clock, self.tabs):
            box.addWidget(w)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(read.CFG["refresh_s"] * 1000)
        self.refresh()
        if account:
            self.fleet.choose([r["beat"]["login"] for r in self.rows].index(account))

    def refresh(self) -> None:
        """Re-read the files and repaint every tab, keeping the chosen account."""
        now = self.at or int(time.time())
        self.rows = state.rows(now)
        self.clock.setText(
            f"Leído a las {datetime.fromtimestamp(now).strftime('%H:%M:%S')} · "
            f"{len(self.rows)} cuentas · se refresca cada {read.CFG['refresh_s']} s · "
            "las horas de las tablas son del reloj del servidor"
        )
        self.fleet.paint(self.rows)
        self.strategies.paint(self.rows, now)
        self.deploy.paint(self.rows, now)
        self.health.paint(self.rows)
        self.reconcile.paint()
        self.alert()

    def alert(self) -> None:
        """A desktop notification for each account whose light just turned red or silent."""
        for r in self.rows:
            login = r["beat"]["login"]
            if (
                self.notify
                and r["light"] in (state.RED, state.SILENT)
                and self.seen.get(login) != r["light"]
            ):
                proc.run(
                    [
                        "notify-send",
                        "-u",
                        "critical",
                        "MetaTracker",
                        f"{fmt.who(r['beat'], r['stage'])}: {r['text']}",
                    ],
                    check=False,
                    timeout=120,
                )
            self.seen[login] = r["light"]

    def fit(self) -> None:
        """Make the window tall enough to show the open tab whole, for a capture."""
        extra = self.height() - self.tabs.currentWidget().height()
        inner = self.tabs.currentWidget().findChild(QScrollArea).widget()  # pyright: ignore[reportAttributeAccessIssue]  # Qt: the open tab always holds a scroll page
        self.resize(
            self.width(), max(self.height(), inner.sizeHint().height() + extra + 20)
        )
