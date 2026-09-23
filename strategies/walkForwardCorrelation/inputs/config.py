"""Read this study's config.yaml."""

from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent.parent


def load() -> dict:
    """The study's tunables.

    Returns:
        The parsed `config.yaml`, unmodified.
    """
    return yaml.safe_load((HERE / "config.yaml").read_text(encoding="utf-8"))
