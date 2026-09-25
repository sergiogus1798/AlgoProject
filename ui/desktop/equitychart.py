"""One strategy's daily P&L, the build backtest and the retest side by side."""

from PySide6.QtCharts import QChart, QChartView, QDateTimeAxis, QLineSeries, QValueAxis
from PySide6.QtCore import QDateTime, QMargins, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen

from ui.desktop.theme import C, T

COLOUR = {"IS": C["accent"], "OOS": C["promising"]}


class EquityChart(QChartView):
    """Two lines. Each side was its own backtest and starts from zero on disk; here the
    retest is lifted to the build's last level so both read as one history, which is how
    the gate glues them too — on daily returns, never on balances."""

    def __init__(self) -> None:
        """Build an empty dark chart."""
        super().__init__()
        self.setRenderHint(QPainter.Antialiasing)
        self.setMinimumHeight(220)
        self.chart().setBackgroundBrush(QColor(T["bg"]))
        self.chart().setBackgroundRoundness(0)
        self.chart().legend().setLabelColor(QColor(T["muted"]))
        self.chart().setMargins(QMargins(0, 0, 0, 0))

    def show_curve(self, curve: dict) -> None:
        """Draw both samples.

        Args:
            curve: `{sample: {days: [...], equity: [...]}}`, as `/api/gate/strategy` returns.
        """
        chart = QChart()
        chart.setBackgroundBrush(QColor(T["bg"]))
        chart.setBackgroundRoundness(0)
        chart.setMargins(QMargins(0, 0, 0, 0))
        chart.legend().setLabelColor(QColor(T["muted"]))
        chart.legend().setAlignment(Qt.AlignTop)
        x = QDateTimeAxis()
        x.setFormat("yyyy")
        y = QValueAxis()
        y.setLabelFormat("%.0f")
        for axis in (x, y):
            axis.setLabelsColor(QColor(T["muted"]))
            axis.setLabelsFont(QFont("DejaVu Sans Mono", 8))
            axis.setGridLineColor(QColor(T["line"]))
            axis.setLinePenColor(QColor(T["rule"]))
        chart.addAxis(x, Qt.AlignBottom)
        chart.addAxis(y, Qt.AlignLeft)
        lift = 0.0
        xs: list[int] = []
        ys: list[float] = []
        for sample in ("IS", "OOS"):
            block = curve.get(sample)
            if not block:
                continue
            s = QLineSeries()
            s.setName("build (IS)" if sample == "IS" else "retest (OOS), empalmado")
            s.setPen(QPen(QColor(COLOUR[sample]), 1.5))
            for day, e in zip(block["days"], block["equity"]):
                t = QDateTime.fromString(day, "yyyy-MM-dd").toMSecsSinceEpoch()
                s.append(t, e + lift)
                xs.append(t)
                ys.append(e + lift)
            lift += block["equity"][-1]
            chart.addSeries(s)
            s.attachAxis(x)
            s.attachAxis(y)
        # An axis takes its range from the first series attached and ignores the next, so
        # the retest fell outside the plot: both are ranged here over the two series.
        x.setRange(QDateTime.fromMSecsSinceEpoch(min(xs)), QDateTime.fromMSecsSinceEpoch(max(xs)))
        y.setRange(min(ys), max(ys))
        self.setChart(chart)
