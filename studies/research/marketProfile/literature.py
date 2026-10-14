"""The literature scout's entries as measures of the profile: their `translation.measures`, checked."""

from typing import Any
import yaml

from core.researchpaths import research_literature_dir
from studies.research.marketProfile.measure.rules import CONDITIONS


def scouted() -> list[dict]:
    """The scout's entries (`scout-<day>.yaml`), oldest first; none while it has stored nothing."""
    files = sorted(research_literature_dir().glob("scout-*.yaml"))
    return [e for f in files for e in yaml.safe_load(f.read_text(encoding="utf-8"))["entries"]]


def named(args: dict) -> list[str]:
    """Every condition a `rule` measure names, without its `not:`."""
    keys = [args["enter"], *(args.get("when") or []), *([args["leave"]] if args.get("leave") else [])]
    return [k.removeprefix("not:") for k in keys]


def specs(entries: list[dict], taken: set[str]) -> tuple[list[dict], list[str]]:
    """The measures the entries ask for, and why the others are left out.

    Args:
        entries: The scout's entries.
        taken: Measure names the config already uses.

    Returns:
        (rows shaped as the config's `measures` — `tag: literature`, `lit` the entry's id up to
        its number —, one line per entry whose measure is not run: an open question, a
        condition `rules.CONDITIONS` does not have, a name already taken).
    """
    out, skipped = [], []
    for e in entries:
        for spec in e["translation"].get("measures", []):
            unknown = [k for k in named(spec["args"]) if k not in CONDITIONS]
            if e.get("question") and not e["question"]["answer"]:
                skipped.append(f"{e['id']}: pregunta abierta al dueño")
            elif unknown:
                skipped.append(f"{e['id']}: condición desconocida {unknown}")
            elif spec["name"] in taken:
                skipped.append(f"{e['id']}: el nombre {spec['name']} ya existe")
            else:
                taken = taken | {spec["name"]}
                out.append({"name": spec["name"], "family": e["family"], "tag": "literature",
                            "lit": "-".join(e["id"].split("-")[:2]), "fn": "rule",
                            "args": spec["args"]})
    return out, skipped


def extend(cfg: dict) -> dict[str, Any]:
    """The config with the scout's measures after its own; what was left out goes to `skipped`."""
    more, skipped = specs(scouted(), {m["name"] for m in cfg["measures"]})
    return {**cfg, "measures": cfg["measures"] + more, "literature_skipped": skipped}
