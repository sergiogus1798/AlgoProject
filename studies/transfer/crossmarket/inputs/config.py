"""The single source of truth for every tunable of the study; it computes nothing."""

from pathlib import Path

from core.study import config as study_config

# parents[1]: the .yaml stays in the module root, where the manual names it.
FILE = Path(__file__).parents[1] / "config.yaml"


def load(overrides: list[str] | None = None) -> dict:
    """Read config.yaml and apply dotted-key overrides.

    Args:
        overrides: Strings like "nulls.draws=20000"; each keeps the type of the value it
            replaces (core.study.config).

    Returns:
        The whole config. Every number the study uses comes from here; a value that is not in
        this dict is a value nobody can change from the window, which is why none exist.
    """
    return study_config.load(FILE, overrides or [])
