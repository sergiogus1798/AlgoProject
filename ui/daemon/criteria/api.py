"""The routes of the Criterios zone: the state, one rule written, and the freeze."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ui.daemon.criteria import read, write

ROUTER = APIRouter()


class RuleChange(BaseModel):
    """One rule of one step as the dialog built it; `rule` None deletes, `at` None appends."""

    n: str
    at: int | None = None
    rule: dict | None = None
    was: dict | None = None


@ROUTER.get("/api/criteria")
def criteria() -> dict[str, object]:
    """Every step's rules, the Build filters, the dev draw, the freeze and the history.

    Returns:
        What `read.state` builds.
    """
    return read.state()


@ROUTER.post("/api/criteria/rule")
def set_rule(change: RuleChange) -> dict[str, object]:
    """Add, change or delete one rule, comments kept, stamped in the history.

    Args:
        change: The step, the position and the rule.

    Returns:
        What was done. A rule the judge could not read, a step without `cut`, a file that
        changed underneath or frozen criteria come back as a 422 with the sentence to show.
    """
    try:
        return write.set_rule(change.n, change.at, change.rule, change.was)
    except ValueError as err:
        raise HTTPException(422, str(err)) from err


@ROUTER.post("/api/criteria/freeze")
def freeze() -> dict[str, object]:
    """Lock the criteria from now on; refused (422) when they already are."""
    try:
        return write.freeze()
    except ValueError as err:
        raise HTTPException(422, str(err)) from err
