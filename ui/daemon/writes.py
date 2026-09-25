"""The three things the window may change: a template's status, its notes, a run's verdict."""

from sqx.templates.registry import RUN_COLUMNS, TEMPLATE_COLUMNS, append

from core.datapaths import template_registry, template_runs
from ui.daemon import library


def set_status(name: str, status: str, notes: str | None = None) -> dict[str, str]:
    """Move a template along draft → validated → buildConfirmed, or archive it.

    Args:
        name: Template name as it appears in the registry.
        status: One of `library.STATUSES`. `archived` is how a template leaves the working
            set without its row and its runs being lost.
        notes: Replacement note, or None to leave the stored one alone.

    Returns:
        The row as written, so the window redraws from what the CSV now holds rather than
        from what it hoped it wrote.
    """
    assert status in library.STATUSES, f"unknown status {status}"
    row = next(r for r in library.rows(template_registry()) if r["name"] == name)
    row["status"] = status
    if notes is not None:
        row["notes"] = notes
    append(template_registry(), TEMPLATE_COLUMNS, row, ("name",))
    return row


def set_verdict(template: str, symbol: str, timeframe: str, verdict: str) -> dict[str, str]:
    """Record what a run came to, on the run itself.

    Args:
        template: Template name.
        symbol, timeframe: Which run — together with the template they identify one row.
        verdict: One of `library.VERDICTS`, or "" to take a verdict back.

    Returns:
        The run row as written.
    """
    assert verdict in library.VERDICTS or verdict == "", f"unknown verdict {verdict}"
    row = next(r for r in library.rows(template_runs())
               if (r["template"], r["symbol"], r["timeframe"]) == (template, symbol, timeframe))
    row["verdict"] = verdict
    append(template_runs(), RUN_COLUMNS, row, ("template", "symbol", "timeframe"))
    return row
