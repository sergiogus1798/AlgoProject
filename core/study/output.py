"""Where a study's results land: one JSON per strategy, and the population's JSON, page and markdown."""

import json
import os
from pathlib import Path

from core import manifest
from core.paths import report_dir
from core.study import identity
from core.study.render import markdown, page


def _write(path: Path, text: str) -> None:
    """Whole file or nothing: a temporary beside it, renamed over it, so the window never reads half.

    No fsync, unlike `core.store.write.atomic`: a population writes one pair of files per strategy.
    """
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def folder(export: Path, module: str) -> Path:
    """Where a module that read one export writes: beside that export's own day.

    Args:
        export: A trades.parquet (or any file) inside raw/<project>/<databank>/<day>/.
        module: The module's report folder name, e.g. "entryQuality".

    Returns:
        reports/<project>/<databank>/<day>/<module>/, project and databank read from the
        export's manifest — the path spells the databank with underscores, SQX with spaces.
    """
    source = manifest.read(export.parent)["source"]
    return report_dir(source["project"], source["databank"], export.parent.name) / module


def identify(folder: Path, names: list[str]) -> dict[str, str | None]:
    """The identity of each strategy an export names: installs, then cosecha, then kept .sqx.

    Args:
        folder: The export folder that holds its manifest.json.
        names: Strategy names as the export spells them.

    Returns:
        name -> identity, None where no source names it (`identity.resolve`).
    """
    doc = manifest.read(folder)
    source = doc["source"]
    return identity.resolve(source["project"], source["databank"], names, folder, doc["date"])


def member(out: Path, result: dict, title: str, lede: str = "") -> Path:
    """One strategy's result as <out>/estrategias/<strategy>.json (no page: the window draws it on demand).

    Args:
        out: The module's report folder.
        result: A validated result with its strategy named.
        title, lede: Unused since the per-strategy page stopped being written; kept so no caller changes.

    Returns:
        The JSON's path — what the window loads.
    """
    folder = out / "estrategias"
    folder.mkdir(parents=True, exist_ok=True)
    # Names carry dots ("Strategy 10.15.25"), so the suffix is appended, never swapped.
    stem = folder / result["strategy"]
    _write(Path(f"{stem}.json"), json.dumps(result, ensure_ascii=False))
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
    _write(out / f"{name}.json", json.dumps(result, ensure_ascii=False))
    _write(out / f"{name}.html", page.page(result, title, lede))
    _write(out / f"{name}.md", markdown.render(result, title))
