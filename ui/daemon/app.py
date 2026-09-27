"""The daemon's HTTP surface: everything the window knows, it asks for here."""

import os

from fastapi import FastAPI
from pydantic import BaseModel

from ui.daemon import brief, coverage, interview, jobs, library, palettes, version, writes
from ui.daemon.assetapi import ROUTER
from ui.daemon.batch.api import ROUTER as BATCH
from ui.daemon.loader.api import ROUTER as LOADER
from ui.daemon.ops.api import ROUTER as OPS
from ui.daemon.results.api import ROUTER as RESULTS
from ui.daemon.runner.api import ROUTER as RUNNER
from ui.daemon.studyapi import ROUTER as STUDIES
from ui.daemon.tearmarket.api import ROUTER as TEARMARKET
from ui.daemon.tearsheet.api import ROUTER as TEARSHEET
from ui.daemon.workflow.api import ROUTER as WORKFLOW

APP = FastAPI(title="AlgoDaemon", docs_url=None, redoc_url=None)
# Taken once at import: the code this process is actually running, not what is on disk now.
CODE = version.fingerprint()
# Each surface that would double this file arrives as a router rather than as a second
# daemon: the asset library, the older strategies/gate zones, and the study viewer's four
# (results, runner, workflow, operation), and the Ficha's market and the variant batch.
for router in (ROUTER, STUDIES, RESULTS, RUNNER, WORKFLOW, OPS, TEARSHEET, TEARMARKET, BATCH, LOADER):
    APP.include_router(router)


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


@APP.get("/api/health")
def health() -> dict[str, object]:
    """Whether the daemon is up and what it is serving.

    Returns:
        A fixed marker the window polls on startup to know the daemon has bound its port,
        plus the code it serves, its pid and how many jobs it runs — what the launcher
        needs to replace a daemon left over from older code without killing a job.
    """
    busy = sum(j["rc"] is None for j in jobs.listing())
    return {"ok": True, "module": "templates", "code": CODE, "pid": os.getpid(), "busy": busy}


@APP.get("/api/templates")
def templates() -> dict[str, object]:
    """The whole catalogue, plus the drafts shelf and the headline counts.

    Returns:
        Everything the two left-hand views need, in one round trip. The catalogue is small
        — tens of rows — so paging it would add a mode for nothing.
    """
    return {"templates": library.catalogue(), "drafts": library.drafts(),
            "totals": coverage.totals(), "statuses": list(library.STATUSES),
            "verdicts": list(library.VERDICTS)}


@APP.get("/api/template/{name}")
def template(name: str) -> dict[str, object]:
    """One template's record, its runs and its brief.

    Args:
        name: Template name as it appears in the registry.

    Returns:
        The catalogue entry plus the brief read verbatim.
    """
    return library.one(name)


@APP.get("/api/coverage")
def coverage_matrix(row_axis: str = "archetype") -> dict[str, object]:
    """The grid of what has been tried.

    Args:
        row_axis: `archetype`, `symbol` or `template`.

    Returns:
        Rows, columns and cells as `coverage.matrix` builds them.
    """
    return coverage.matrix(row_axis)


@APP.post("/api/template/{name}/status")
def set_status(name: str, change: StatusChange) -> dict[str, str]:
    """Move a template's status, or archive it.

    Args:
        name: Template name.
        change: The new status and, when given, the note replacing the stored one.

    Returns:
        The registry row as written.
    """
    return writes.set_status(name, change.status, change.notes)


@APP.post("/api/verdict")
def set_verdict(change: VerdictChange) -> dict[str, str]:
    """Record a run's verdict.

    Args:
        change: Which run, and what it came to.

    Returns:
        The run row as written.
    """
    return writes.set_verdict(change.template, change.symbol, change.timeframe, change.verdict)


@APP.get("/api/palettes")
def palette_state() -> dict[str, object]:
    """The taxonomy, the three palettes and what each one resolves to.

    Returns:
        Everything the palette view needs in one round trip — 767 blocks is a single parse
        and paging it would add a mode for nothing on loopback.
    """
    return palettes.state()


@APP.post("/api/palette/{name}")
def set_palette(name: str, change: PaletteChange) -> dict[str, object]:
    """Write one palette of the library.

    Args:
        name: Its slug.
        change: Its label, its note, its unlabelled policy and the complete override map.

    Returns:
        The palette as written plus its new summary.
    """
    return palettes.save(name, change.unlabelled, change.overrides, change.label, change.note)


@APP.post("/api/palettes/new")
def new_palette(new: NewPalette) -> dict[str, object]:
    """Add a palette to the library, empty or cloned from another.

    Args:
        new: The slug, the label, the family and what to clone.

    Returns:
        The palette as written plus its summary.
    """
    return palettes.create(new.name, new.label, new.family, new.source)


@APP.post("/api/palette/{name}/delete")
def delete_palette(name: str) -> dict[str, object]:
    """Remove one palette from the library.

    Args:
        name: Its slug.

    Returns:
        What was removed.
    """
    return palettes.remove(name)


@APP.post("/api/interview/step")
def interview_step(payload: Answers) -> dict[str, object]:
    """What to ask next, given what has been answered.

    Args:
        payload: The answers so far.

    Returns:
        The next question, or `done`.
    """
    return interview.step(payload.answers)


@APP.post("/api/interview/finish")
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
