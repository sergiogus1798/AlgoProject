"""Read this study's config.yaml."""

from pathlib import Path

from core.study import config as study_config

HERE = Path(__file__).resolve().parent.parent


def load(overrides: list[str] | None = None) -> dict:
    """The study's tunables.

    Args:
        overrides: "section.key=value" strings; each keeps the type of the value it replaces
            (core.study.config).

    Returns:
        The parsed `config.yaml`.
    """
    return study_config.load(HERE / "config.yaml", overrides or [])
