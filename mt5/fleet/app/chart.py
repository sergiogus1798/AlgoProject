"""The matplotlib canvas that draws the day's equity curve in MetaTracker's colours."""

from datetime import datetime, timezone

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.dates import DateFormatter
from matplotlib.figure import Figure

from mt5.fleet.app import fmt, theme

# Discrete colours, one per element, readable on the dark panel.
EQUITY, BAND, DAILY, TOTAL = (
    theme.ACCENT,
    "#7f8ea3",
    theme.LIGHTS["yellow"],
    theme.LIGHTS["red"],
)


def at(epoch: float) -> datetime:
    """A server-clock epoch as a naive datetime, so the axis reads the server's hours."""
    return datetime.fromtimestamp(epoch, timezone.utc).replace(tzinfo=None)


class CurveCanvas(FigureCanvasQTAgg):
    """A canvas that paints one account's curve of the day, or says why it cannot."""

    def __init__(self) -> None:
        """An empty figure on the panel's colour."""
        super().__init__(
            Figure(figsize=(9, 4.4), facecolor=theme.PANEL, layout="constrained")
        )
        self.axes = self.figure.add_subplot()

    def paint(self, curve: dict | None, why: str) -> None:
        """Draw the curve; with None, write `why` in the middle.

        Args:
            curve: `curve.data()`.
            why: The Spanish reason there is nothing to draw.
        """
        ax = self.axes
        ax.clear()
        ax.set_facecolor(theme.PANEL)
        for side in ax.spines.values():
            side.set_color(theme.LINE)
        ax.tick_params(colors=theme.TEXT, labelsize=12)
        if curve is None:
            ax.set_axis_off()
            ax.text(
                0.5,
                0.5,
                why,
                ha="center",
                va="center",
                color=theme.DIM,
                fontsize=15,
                wrap=True,
                transform=ax.transAxes,
            )
            self.draw()
            return
        for h in curve["hours"]:
            ax.fill_between(
                [at(h["start"]), at(h["start"] + 3600)],  # pyright: ignore[reportArgumentType]  # matplotlib stubs reject datetime axes
                h["low"],
                h["high"],
                color=BAND,
                alpha=0.45,
                linewidth=0,
                label="Mínimo y máximo de cada hora",
            )
        ax.plot(
            [at(t) for t in curve["times"]],  # pyright: ignore[reportArgumentType]  # matplotlib stubs reject datetime axes
            curve["equity"],
            color=EQUITY,
            linewidth=2.4,
            marker="o" if len(curve["times"]) < 3 else None,
            label="Equity (minuto)",
        )
        ax.axhline(
            curve["daily_floor"],
            color=DAILY,
            linestyle="--",
            linewidth=2,
            label=f"Suelo diario {fmt.money(curve['daily_floor'])}",
        )
        ax.axhline(
            curve["max_floor"],
            color=TOTAL,
            linestyle="--",
            linewidth=2,
            label=f"Suelo total {fmt.money(curve['max_floor'])}",
        )
        ax.set_xlim(at(curve["start"]), at(max(curve["now"], curve["start"] + 3600)))  # pyright: ignore[reportArgumentType]  # matplotlib stubs reject datetime axes
        ax.xaxis.set_major_formatter(DateFormatter("%H:%M"))
        ax.grid(color=theme.LINE, linewidth=0.8)
        handles, labels = ax.get_legend_handles_labels()
        unique = dict(zip(labels, handles))
        ax.legend(
            unique.values(),
            unique.keys(),
            loc="best",
            fontsize=12,
            facecolor=theme.BG,
            edgecolor=theme.LINE,
            labelcolor=theme.TEXT,
        )
        self.draw()


LINES = [
    theme.ACCENT,
    "#ffc832",
    "#3ddc84",
    "#ff8fd0",
    "#b48cff",
    "#ff9d4d",
]  # one per account, distinct
COMBINED = "#ffffff"


class LinesCanvas(CurveCanvas):
    """A canvas of cumulative-result step lines, one per account, plus an optional combined one."""

    def paint_lines(self, lines: list[dict], ylabel: str, why: str) -> None:
        """Draw the lines; with none, write `why` in the middle.

        Args:
            lines: Dicts of `name`, `times` (server epochs), `values`, `colour` and `width`.
            ylabel: The Y axis' unit.
            why: The Spanish reason there is nothing to draw.
        """
        ax = self.axes
        ax.clear()
        ax.set_facecolor(theme.PANEL)
        for side in ax.spines.values():
            side.set_color(theme.LINE)
        ax.tick_params(colors=theme.TEXT, labelsize=12)
        if not lines:
            ax.set_axis_off()
            ax.text(
                0.5,
                0.5,
                why,
                ha="center",
                va="center",
                color=theme.DIM,
                fontsize=15,
                wrap=True,
                transform=ax.transAxes,
            )
            self.draw()
            return
        for ln in lines:
            ax.step(
                [at(t) for t in ln["times"]],  # pyright: ignore[reportArgumentType]  # matplotlib stubs reject datetime axes
                ln["values"],
                where="post",
                color=ln["colour"],
                linewidth=ln["width"],
                label=ln["name"],
            )
        ax.axhline(0, color=theme.LINE, linewidth=1.2)
        ax.set_ylabel(ylabel, color=theme.TEXT, fontsize=12)
        ax.xaxis.set_major_formatter(DateFormatter("%d-%m"))
        ax.grid(color=theme.LINE, linewidth=0.8)
        ax.legend(
            loc="best",
            fontsize=12,
            facecolor=theme.BG,
            edgecolor=theme.LINE,
            labelcolor=theme.TEXT,
        )
        self.draw()
