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


def batch(cfg: dict) -> dict:
    """`cfg` with `nulls.draws` replaced by `nulls.batch_draws`.

    Args:
        cfg: A loaded config.

    Returns:
        cfg, `nulls.draws` overwritten. `studies.transfer.crossmarket.many.run` never draws
        `nulls.draws` — the population's null is always `batch_draws` draws (its own
        docstring) — but signs the cfg it actually used, so a stored population result's
        `config_hash` carries this substitution. `population()` below reproduces it for the
        window's staleness check (OPEN #52: before this, the window always signed the raw
        `nulls.draws` and a population result read stale even freshly written).
    """
    return {**cfg, "nulls": {**cfg["nulls"], "draws": cfg["nulls"]["batch_draws"]}}


def population(overrides: list[str] | None = None) -> dict:
    """The config a population run signs: `load(overrides)` through `batch`.

    Args:
        overrides: As `load`.

    Returns:
        As `load`, with the same substitution `many.run` applies before it fingerprints.
    """
    return batch(load(overrides))
