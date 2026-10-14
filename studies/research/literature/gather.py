"""What a run registers: a page of a query's papers, a code collection's and a site's next items."""

import sys
from collections.abc import Callable, Mapping
from itertools import zip_longest
from typing import Any

import httpx

from studies.research.literature import dedupe, search, store


DOWN: set[str] = set()  # sources that refused a request in this run: not asked again


def asked(name: str, fn: Callable, *args: object) -> Any:
    """A source's answer, or nothing once it has refused in this run.

    A search service that is down or out of its free daily budget (OpenAlex answers 429 once an
    IP has spent it) must not lose the run: the other sources still fill it.
    """
    if name in DOWN:
        return []
    try:
        return fn(*args)
    except httpx.HTTPError as error:
        DOWN.add(name)
        print(f"{name} unavailable this run: {error}"[:200], file=sys.stderr)
        return []


def row(
    paper: Mapping[str, Any], query: str, family: str, run: str, twin: str
) -> dict[str, Any]:
    """A found paper as its row of the register: undecided, or the duplicate of `twin`."""
    return {
        **paper,
        "query": query,
        "family": family,
        "run": run,
        "found": run[:8],
        "read": "",
        "entries": [],
        "status": "duplicate" if twin else "inbox",
        "filter": "",
        "quote": "",
        "reason": f"same paper as {twin}" if twin else "",
    }


def page(
    query: dict,
    page: int,
    run: str,
    most: int,
    room: int,
    held: dict,
    entries: list[dict],
    new: list[dict],
) -> int:
    """Register one page of one query's results; returns how many were new and kept.

    Args:
        query: `{family, text}` of the config.
        page: Which page of results, from 0.
        run: The run's id.
        most, room: Papers this query may still take, and the run may still take.
        held: The papers register, changed in place.
        entries: Every literature entry.
        new: The run's new papers, appended to.
    """
    cfg = store.config()
    ask, src = 4 * cfg["run"]["per_query"], cfg["sources"]
    oa = src["openalex"]
    first = iter(
        asked(
            "arxiv", search.arxiv, query["text"], src["arxiv"]["categories"], ask, page
        )
        if src["arxiv"]["enabled"]
        else []
    )
    other = (
        asked(
            "openalex",
            search.openalex,
            query["text"],
            oa["from_year"],
            oa["field"],
            ask,
            oa["open_pdf"],
            page,
        )
        if oa["enabled"]
        else []
    )
    # Two arXiv papers for each OpenAlex one: arXiv always serves its PDF.
    taken = 0
    for paper in (p for trio in zip_longest(first, first, other) for p in trio if p):
        if paper["key"] in held or taken == min(most, room):
            continue
        twin = dedupe.same_paper(paper, list(held.values()), entries)
        held[paper["key"]] = row(paper, query["text"], query["family"], run, twin)
        if not twin:
            new.append(paper)
            taken += 1
    return taken


def collections(cfg: dict, run: str, held: dict, new: list[Any]) -> None:
    """Register the next unseen items of each strategy collection (owner, 2026-10-02).

    Args:
        cfg: The `sources.repos` section: `per_run` and the `collections`.
        run: The run's id.
        held: The papers register, changed in place.
        new: The run's new papers, appended to.
    """
    for spec in cfg["collections"]:
        found = asked(spec["repo"], search.collection, spec["repo"], spec["kind"])
        fresh = [i for i in found if i["key"] not in held]
        for item in fresh[: cfg["per_run"]]:
            paper = search.item(item)
            held[paper["key"]] = row(paper, spec["repo"], "repository", run, "")
            new.append(paper)


def sites(cfg: dict, run: str, held: dict, new: list[Any]) -> None:
    """Register the next unseen articles of each practitioner site (owner, 2026-10-02).

    Args:
        cfg: The `sources.web` section: `per_run` and the `sites`.
        run: The run's id.
        held: The papers register, changed in place.
        new: The run's new papers, appended to.
    """
    for spec in cfg["sites"]:
        found = asked(
            spec["name"], search.site, spec["name"], spec["index"], spec["link"]
        )
        for item in [i for i in found if i["key"] not in held][: cfg["per_run"]]:
            got = asked(spec["name"], search.article, item)
            if got:
                held[got["key"]] = row(got, spec["index"], "practitioner", run, "")
                new.append(got)
