"""Where the strategy-template library lives under the data root. Split out of core/paths.py."""

from pathlib import Path

from core.paths import DATA


def template_dir(name: str) -> Path:
    """Folder of one strategy template in the library.

    Args:
        name: Template name in camelCase, underscores separating roles only, e.g.
            "keltnerCrossClose_atrTrail".

    Returns:
        Path under the data root. Self-contained — the .sqx, its brief and the blocks and
        groups it references — so it installs on any SQX unchanged. A template carries no
        symbol and no timeframe: those belong to a run.
    """
    return DATA / "templates" / "library" / name


def template_registry() -> Path:
    """The CSV of every template in the library, one row each.

    Returns:
        Path under the data root. CSV and not parquet because a human reads it; written by
        code, never hand-edited.
    """
    return DATA / "templates" / "registry.csv"


def template_runs() -> Path:
    """The CSV of every (template, symbol, timeframe) that has been tried.

    Returns:
        Path under the data root. Separate from the registry because one template is tried
        on many markets: "have I run this on NASDAQ H1" is a row here, not a second copy.
    """
    return DATA / "templates" / "runs.csv"


def vocabulary_snapshot(install: str, day: str) -> Path:
    """Where one install's block-and-group inventory is kept.

    Args:
        install: Folder name of the install, e.g. "SQX_w1".
        day: Snapshot date as YYYY-MM-DD.

    Returns:
        Path under the data root. Dated and kept, not replaced: the point is comparing
        installs and dates, which a single current file cannot answer.
    """
    return DATA / "templates" / "vocabulary" / f"{install}-{day}.json"

