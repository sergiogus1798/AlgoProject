"""A rule's per-timeframe / per-asset overrides (`by`) as editable rows and back."""

from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QWidget


def by_line(key: str, passes: str, limbo: str) -> tuple[tuple, QWidget, QPushButton]:
    """The widgets of one override row: its three boxes, the row, and its «−» button."""
    boxes = tuple(QLineEdit(t) for t in (key, passes, limbo))
    for box, hint in zip(boxes, ("H4, XAUUSD, forex…", "pasa: >= 2.5", "limbo: >= 1.65")):
        box.setPlaceholderText(hint)
    drop = QPushButton("−")
    drop.setFixedWidth(40)
    line = QWidget()
    row = QHBoxLayout(line)
    row.setContentsMargins(0, 0, 0, 0)
    for box in boxes:
        row.addWidget(box)
    row.addWidget(drop)
    return boxes, line, drop


def by_rows(by: dict | None) -> list[tuple[str, str, str]]:
    """A rule's `by` as the section's rows: (key, pass, limbo)."""
    return [(k, str(v.get("pass", "")), str(v.get("limbo", ""))) for k, v in (by or {}).items()]


def by_built(rows: list[tuple[str, str, str]], old: dict | None) -> dict:
    """The rows back into `by`: no key, no row; no text, no field; other fields of an override
    survive while its key does."""
    out = {}
    for key, passes, limbo in rows:
        if key.strip():
            keep = {k: v for k, v in ((old or {}).get(key.strip()) or {}).items()
                    if k not in ("pass", "limbo")}
            out[key.strip()] = keep | {k: t.strip() for k, t in (("pass", passes), ("limbo", limbo))
                                       if t.strip()}
    return {k: v for k, v in out.items() if v}
