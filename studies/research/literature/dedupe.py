"""Whether a paper, or a rule under another name, is already in the literature."""

import re

from studies.research.literature.anchors import squeeze

ARXIV = re.compile(r"(?:arxiv[:./ ]|abs/)(\d{4}\.\d{4,5})", re.I)
DOI = re.compile(r"\b(10\.\d{4,9}/[^\s,;)]+)", re.I)
WORD = re.compile(r"[a-z]+|\d+(?:\.\d+)?")
# Words every rule shares: they say nothing about which rule it is.
COMMON = {
    "the",
    "a",
    "an",
    "of",
    "when",
    "and",
    "or",
    "is",
    "its",
    "on",
    "in",
    "to",
    "bar",
    "bars",
    "close",
    "long",
    "short",
    "mirror",
    "at",
    "by",
    "for",
    "with",
    "than",
    "that",
    "it",
}


def same_paper(paper: dict, known: list[dict], entries: list[dict]) -> str:
    """What a paper duplicates: a paper already seen, or an entry's source; '' when it is new.

    Args:
        paper: `key`, `title`, `authors`, and `arxiv` and `doi` when it has them.
        known: The papers register's rows.
        entries: Every literature entry (its `source` is free text).

    Returns:
        The key or the entry id it matches — by arXiv id, by DOI, or by title.
    """
    title = squeeze(paper["title"])
    # A short title («Time series momentum») is inside many sources: it needs its first author too.
    surname = squeeze(paper["authors"][0].split()[-1]) if paper.get("authors") else ""
    for other in known:
        if other["key"] != paper["key"] and (
            (paper.get("arxiv") and paper["arxiv"] == other.get("arxiv"))
            or (paper.get("doi") and paper["doi"] == other.get("doi"))
            or title == squeeze(other["title"])
        ):
            return other["key"]
    for e in entries:
        source = str(e["source"])
        if (
            (paper.get("arxiv") and paper["arxiv"] in ARXIV.findall(source))
            or (
                paper.get("doi")
                and paper["doi"].lower()
                in [d.lower().rstrip(".") for d in DOI.findall(source)]
            )
            or (
                title in squeeze(source)
                and (len(title) >= 25 or (surname and surname in squeeze(source)))
            )
        ):
            return e["id"]
    return ""


def spec_key(args: dict) -> tuple:
    """A `rule` measure as it compares: its arguments, whatever it is called or filed under.

    The family is not part of it: the paper that calls a rule «momentum» and the one that calls
    it «trend» state the same rule (MOM-75 entered beside `tsmom_d252_run` until this was fixed).
    """
    return (
        args["enter"],
        tuple(sorted(args.get("when") or [])),
        args.get("leave"),
        args.get("cap", 0),
        args.get("days", 0),
        args.get("trail", 0.0),
        args.get("ruler", "bar"),
    )


def same_rule(args: dict, entries: list[dict], measures: list[dict]) -> str:
    """The entry or profile measure that already tests one `rule` measure; '' when none does.

    Args:
        args: The measure's arguments.
        entries: Every stored entry.
        measures: The `measures` rows of the market profile's config.
    """
    mine = spec_key(args)
    for m in measures:
        if m["fn"] == "rule" and spec_key(m["args"]) == mine:
            return f"measure {m['name']}" + (f" ({m['lit']})" if m.get("lit") else "")
    for e in entries:
        for other in e["translation"].get("measures", []):
            if spec_key(other["args"]) == mine:
                return e["id"]
    return ""


def words(text: str) -> set[str]:
    """The words and numbers that tell one rule from another."""
    return set(WORD.findall(str(text).lower())) - COMMON


def similar(entry: dict, entries: list[dict], threshold: float) -> list[str]:
    """Stored entries of the same family whose rule reads alike: Jaccard of their words."""
    mine = words(entry["translation"]["entry"])
    out = []
    for e in entries:
        theirs = words(e["translation"]["entry"])
        if e["family"] == entry["family"] and mine and theirs:
            if len(mine & theirs) / len(mine | theirs) >= threshold:
                out.append(e["id"])
    return out
