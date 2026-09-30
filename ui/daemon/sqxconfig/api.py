"""The routes of the Configuración SQX zone: every setting a new project is built with, and its one write."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ui.daemon.sqxconfig import sections, studies, studywrite, write

ROUTER = APIRouter()


class FieldChange(BaseModel):
    """One value of one shared file, as the window chose or typed it."""

    file: str
    path: list[str | int]
    value: object


@ROUTER.get("/api/sqxconfig")
def sqxconfig() -> dict[str, object]:
    """Every SQX setting, one section per test or topic, each value typed.

    Returns:
        What `sections.state` builds, in one round trip.
    """
    return sections.state()


@ROUTER.post("/api/sqxconfig/value")
def set_value(change: FieldChange) -> dict[str, object]:
    """Write one value, comments and every other line left alone.

    Args:
        change: Which file — a shared one of assets/, or a study file behind the WFC and the
            CSCV (`studies.FILES`) — which path, and the new value.

    Returns:
        What was written. A value outside its options, a locked one or a number that is not
        a number comes back as a 422 carrying the sentence to show: it is the owner's input,
        the one boundary where a bad value is shown instead of crashing.
    """
    try:
        if change.file in studies.FILES:
            return studywrite.set_field(change.file, change.path, change.value)
        return write.set_field(change.file, change.path, change.value)
    except ValueError as err:
        raise HTTPException(422, str(err)) from err
