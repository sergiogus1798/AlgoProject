"""Where the research director's pieces live under the data root."""

from pathlib import Path

from core.paths import DATA


def research_profiles_dir() -> Path:
    """The market profile's map: `cells/` per asset and the judged tables. Fed by `build` only."""
    return DATA / "research" / "profiles"


def research_memory_dir() -> Path:
    """The research director's results memory: the attempts table and the ideas index."""
    return DATA / "research" / "memory"


def research_literature_dir() -> Path:
    """The literature file and the scout's store: entries, the papers seen, their texts, the runs."""
    return DATA / "research" / "literature"


def autopilot_runs() -> Path:
    """The autopilot's runs: `<project>/<stamp>/{plan.json, estado.txt, resumen.md, fallo.md}`."""
    return DATA / "autopilot"


def ideas_dir() -> Path:
    """The `ideaExpert`'s files: `<SYMBOL>/<date>-<slug>.md`, one per session."""
    return DATA / "ideas"
