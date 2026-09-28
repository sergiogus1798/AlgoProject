"""The library's routes: the template catalogue, its coverage and writes, the palettes, the chat."""

from fastapi import APIRouter
from pydantic import BaseModel

from ui.daemon import brief, coverage, interview, library, palettes, writes

ROUTER = APIRouter()


class StatusChange(BaseModel):
    """A move along the template lifecycle, optionally carrying a new note."""

    status: str
    notes: str | None = None


class VerdictChange(BaseModel):
    """What one run of one template on one market came to."""

    template: str
    symbol: str
    timeframe: str
    verdict: str


class PaletteChange(BaseModel):
    """A palette as the window holds it: its name on screen, its policy and every override."""

    label: str
    note: str = ""
    unlabelled: str
    overrides: dict[str, int]


class NewPalette(BaseModel):
    """A palette about to be added to the library, empty or cloned from `source`."""

    name: str
    label: str
    family: str
    source: str | None = None


class Answers(BaseModel):
    """The whole interview so far, by question id. Blank means «apply the default»."""

    answers: dict[str, str]


@ROUTER.get("/api/templates")
def templates() -> dict[str, object]:
    """The whole catalogue, plus the drafts shelf and the headline counts.

    Returns:
        Everything the two left-hand views need, in one round trip. The catalogue is small
        — tens of rows — so paging it would add a mode for nothing.
    """
    return {"templates": library.catalogue(), "drafts": library.drafts(),
            "totals": coverage.totals(), "statuses": list(library.STATUSES),
            "verdicts": list(library.VERDICTS)}


@ROUTER.get("/api/template/{name}")
def template(name: str) -> dict[str, object]:
    """One template's record, its runs and its brief.

    Args:
        name: Template name as it appears in the registry.

    Returns:
        The catalogue entry plus the brief read verbatim.
    """
    return library.one(name)


@ROUTER.get("/api/coverage")
def coverage_matrix(row_axis: str = "archetype") -> dict[str, object]:
    """The grid of what has been tried.

    Args:
        row_axis: `archetype`, `symbol` or `template`.

    Returns:
        Rows, columns and cells as `coverage.matrix` builds them.
    """
    return coverage.matrix(row_axis)


@ROUTER.post("/api/template/{name}/status")
def set_status(name: str, change: StatusChange) -> dict[str, str]:
    """Move a template's status, or archive it.

    Args:
        name: Template name.
        change: The new status and, when given, the note replacing the stored one.

    Returns:
        The registry row as written.
    """
    return writes.set_status(name, change.status, change.notes)


@ROUTER.post("/api/verdict")
def set_verdict(change: VerdictChange) -> dict[str, str]:
    """Record a run's verdict.

    Args:
        change: Which run, and what it came to.

    Returns:
        The run row as written.
    """
    return writes.set_verdict(change.template, change.symbol, change.timeframe, change.verdict)


@ROUTER.get("/api/palettes")
def palette_state() -> dict[str, object]:
    """The taxonomy, the three palettes and what each one resolves to.

    Returns:
        Everything the palette view needs in one round trip — 767 blocks is a single parse
        and paging it would add a mode for nothing on loopback.
    """
    return palettes.state()


@ROUTER.post("/api/palette/{name}")
def set_palette(name: str, change: PaletteChange) -> dict[str, object]:
    """Write one palette of the library.

    Args:
        name: Its slug.
        change: Its label, its note, its unlabelled policy and the complete override map.

    Returns:
        The palette as written plus its new summary.
    """
    return palettes.save(name, change.unlabelled, change.overrides, change.label, change.note)


@ROUTER.post("/api/palettes/new")
def new_palette(new: NewPalette) -> dict[str, object]:
    """Add a palette to the library, empty or cloned from another.

    Args:
        new: The slug, the label, the family and what to clone.

    Returns:
        The palette as written plus its summary.
    """
    return palettes.create(new.name, new.label, new.family, new.source)


@ROUTER.post("/api/palette/{name}/delete")
def delete_palette(name: str) -> dict[str, object]:
    """Remove one palette from the library.

    Args:
        name: Its slug.

    Returns:
        What was removed.
    """
    return palettes.remove(name)


@ROUTER.post("/api/interview/step")
def interview_step(payload: Answers) -> dict[str, object]:
    """What to ask next, given what has been answered.

    Args:
        payload: The answers so far.

    Returns:
        The next question, or `done`.
    """
    return interview.step(payload.answers)


@ROUTER.post("/api/interview/finish")
def interview_finish(payload: Answers) -> dict[str, object]:
    """Close the interview: write the draft brief and hand back the command.

    Args:
        payload: The complete answers.

    Returns:
        The brief, where it was written, the prompt to paste into Claude Code, and the
        commands the skill will run.
    """
    composed = brief.compose(payload.answers)
    return {"brief": composed, "path": brief.save(composed),
            "prompt": brief.prompt(composed), "commands": brief.commands(composed)}
