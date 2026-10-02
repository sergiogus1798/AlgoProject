"""Where the research director's pieces live under the data root."""

from pathlib import Path

from core.paths import DATA


def research_profiles_dir() -> Path:
    """The market profile's map: `cells/` per asset and the judged tables. Fed by `build` only."""
    return DATA / "research" / "profiles"


def research_memory_dir() -> Path:
    """The research director's results memory: the attempts table and the ideas index."""
    return DATA / "research" / "memory"


def autopilot_runs() -> Path:
    """The autopilot's runs: `<project>/<stamp>/{plan.json, estado.txt, resumen.md, fallo.md}`."""
    return DATA / "autopilot"


def ideas_dir() -> Path:
    """The `ideaExpert`'s files: `<SYMBOL>/<date>-<slug>.md`, one per session."""
    return DATA / "ideas"
