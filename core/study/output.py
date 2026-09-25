"""Where a study's results land: one JSON and one page per strategy, and the population's three."""

import json
from pathlib import Path

from core import manifest
from core.paths import report_dir
from core.study import identity
from core.study.render import markdown, page


def folder(export: Path, module: str) -> Path:
    """Where a module that read one export writes: beside that export's own day.

    Args:
        export: A trades.parquet (or any file) inside raw/<project>/<databank>/<day>/.
        module: The module's report folder name, e.g. "profitShape".

    Returns:
        reports/<project>/<databank>/<day>/<module>/, project and databank read from the
        export's manifest — the path spells the databank with underscores, SQX with spaces.
    """
    source = manifest.read(export.parent)["source"]
    return report_dir(source["project"], source["databank"], export.parent.name) / module


def identify(folder: Path, names: list[str]) -> dict[str, str | None]:
    """The identity of each strategy an export names, read from its databank's .sqx files.

    Args:
        folder: The export folder that holds its manifest.json.
        names: Strategy names as the export spells them.

    Returns:
        name -> identity, None where no install still holds the .sqx.
    """
    source = manifest.read(folder)["source"]
    return identity.lookup(source["project"], source["databank"], names)


def member(out: Path, result: dict, title: str, lede: str = "") -> Path:
    """One strategy's result as <out>/estrategias/<strategy>.json and .html.

    Args:
        out: The module's report folder.
        result: A validated result with its strategy named.
        title: The page's heading.
        lede: One paragraph under it.

    Returns:
        The JSON's path — what the window loads.
    """
    folder = out / "estrategias"
    folder.mkdir(parents=True, exist_ok=True)
    # Names carry dots ("Strategy 10.15.25"), so the suffix is appended, never swapped.
    stem = folder / result["strategy"]
    Path(f"{stem}.json").write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    Path(f"{stem}.html").write_text(page.page(result, title, lede), encoding="utf-8")
    return Path(f"{stem}.json")


def population(out: Path, name: str, result: dict, title: str, lede: str = "") -> None:
    """The population's result as <name>.json, <name>.html and <name>.md.

    Args:
        out: The module's report folder.
        name: File stem, the module's short name.
        result: A validated population result.
        title: The page's heading.
        lede: One paragraph under it.
    """
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{name}.json").write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    (out / f"{name}.html").write_text(page.page(result, title, lede), encoding="utf-8")
    (out / f"{name}.md").write_text(markdown.render(result, title), encoding="utf-8")
