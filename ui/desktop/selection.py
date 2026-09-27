"""The one global selection: project, databank and strategy, shared by every zone."""

from PySide6.QtCore import QObject, Signal

# The keys a selection holds. `identity` is the SHA-256 of the normalised XML: a name
# identifies nothing, so any view that pairs results pairs them by this.
KEYS = ("project", "databank", "strategy", "identity", "asset")


class Selection(QObject):
    """What the owner is looking at. Choosing it in one zone chooses it in all of them."""

    changed = Signal(dict)

    def __init__(self) -> None:
        """Start with nothing chosen."""
        super().__init__()
        self.now = dict.fromkeys(KEYS)

    def choose(self, **fields: str | None) -> None:
        """Change some fields and tell every listener, clearing what hangs below them.

        Args:
            fields: Any of `KEYS`. A new project clears databank and strategy; a new
                databank clears the strategy — a strategy never survives into a
                databank it is not in.
        """
        below = {"project": ("databank", "strategy", "identity"),
                 "databank": ("strategy", "identity")}
        for key, value in fields.items():
            if value != self.now[key]:
                for gone in below.get(key, ()):
                    self.now[gone] = None
            self.now[key] = value
        self.changed.emit(dict(self.now))


SELECTION = Selection()
