"""The records the rail passes between its modules: the step row, the install view, the context."""

from pathlib import Path
from typing import Any, TypedDict

_StepKeys = TypedDict(
    "_StepKeys",
    {"state": str, "why": str, "in": int | None, "out": int | None, "day": str | None},
)


class StepRow(_StepKeys, total=False):
    """What `derive` says of one step; `titles` only for 11.7, whose tasks are the project's."""

    titles: list[str]


class Result(TypedDict):
    """One contract result of one study: where it is, its day, its databank (None for a batch)."""

    path: Path
    day: str
    databank: str | None
    manifest: dict[str, Any]


class SqxView(TypedDict):
    """A project's files in an install: tasks, databank counts, today's runs, the log's last run."""

    role: str
    folder: Path
    tasks: list[dict[str, Any]]
    banks: dict[str, int]
    runs: list[dict[str, Any]]
    run: dict[str, Any]
    alive: bool


class Oos2Gauge(TypedDict):
    """How often this project's studies looked at oos2, and who may."""

    looks: int
    allowed: None
    virgin: bool
    text: str
    reserved_for: list[str]
    by_step: dict[str, int]


class _DoorKeys(TypedDict):
    """The three fields every door has."""

    sealed: bool
    done: list[str]
    text: str


class Door(_DoorKeys, total=False):
    """The blind door over some rows (`sealed`, `done`, `text`) and, from `door`, its `study`."""

    study: str | None


class Context(TypedDict):
    """Everything the steps read about one project, gathered once per request."""

    project: str
    asset: str | None
    template: tuple[str | None, str]
    family: str | None
    sqx: SqxView | None
    blind: Door
    oos2: Oos2Gauge


class StudyTest(TypedDict):
    """One test of one step as the rail paints it."""

    key: str
    title: str
    config: str
    runnable: bool
    databank: str | None
    spends: str
    auto: bool
    state: str
    why: str


class BackfillOffer(TypedDict):
    """Whether to offer «rehacer las filas de 17-19», why, and the command it runs."""

    offer: bool
    why: str
    argv: list[str]


class Started(TypedDict):
    """The jobs a press of the run button queued, and the ticked tests refused with why."""

    jobs: list[dict[str, Any]]
    refused: list[dict[str, str]]


class Stop(TypedDict):
    """Where the chain stops: the step (None when it runs out), its title and why."""

    n: str | None
    title: str
    why: str


class Plan(TypedDict):
    """What one press of «Correr workflow» runs, in order, and where it stops."""

    do: list[dict[str, Any]]
    stop: Stop


class Rail(TypedDict):
    """The whole rail of one project: its steps with their tests, the tabs, the gauges, the chain."""

    project: str
    asset: str | None
    family: str | None
    steps: list[dict[str, Any]]
    tabs: list[str]
    oos2: Oos2Gauge
    blind: Door
    backfill: BackfillOffer
    chain: Plan
