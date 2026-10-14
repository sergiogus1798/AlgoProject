"""Papers from arXiv and OpenAlex for one query: metadata and abstract, no full text."""

import json
import re
import xml.etree.ElementTree as ET
from datetime import date
from typing import TypedDict

import httpx
from lxml import html

ARXIV_API = "https://export.arxiv.org/api/query"
OPENALEX_API = "https://api.openalex.org/works"
GITHUB, RAW = "https://api.github.com/repos", "https://raw.githubusercontent.com"
# What one strategy of a collection is: the file whose text is its description, and its code.
KINDS = {
    "stocksharp": (r"^API/[^/]+/(\d{4}_[^/]+)/README\.md$", "PY"),
    "notebooks": (r"^([^/]+)\.ipynb$", ""),
}
ATOM = {"a": "http://www.w3.org/2005/Atom"}
AGENT = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AlgoProject-literatureScout/1.0"
}


class Paper(TypedDict):
    """A found paper as the register keeps it: identifiers, citation, link, abstract and text pages."""

    key: str
    source: str
    arxiv: str
    doi: str
    title: str
    authors: list[str]
    year: int
    venue: str
    url: str
    pdf: str
    abstract: str
    pages: list[str]


CHUNK = 6000  # characters of a web page that count as one `[page N]`


def arxiv(text: str, categories: list[str], n: int, page: int) -> list[dict]:
    """One page of n arXiv papers of those categories whose text matches, most relevant first."""
    cats = " OR ".join(f"cat:{c}" for c in categories)
    reply = httpx.get(
        ARXIV_API,
        headers=AGENT,
        timeout=60,
        follow_redirects=True,
        params={
            "search_query": f'({cats}) AND all:"{text}"',
            "max_results": n,
            "start": page * n,
            "sortBy": "relevance",
        },
    )
    reply.raise_for_status()
    out = []
    for e in ET.fromstring(reply.text).findall("a:entry", ATOM):
        ident = re.sub(
            r"v\d+$", "", e.findtext("a:id", "", ATOM).rsplit("/abs/", 1)[-1]
        )
        out.append(
            {
                "key": f"arxiv-{ident}",
                "source": "arxiv",
                "arxiv": ident,
                "doi": "",
                "title": " ".join(e.findtext("a:title", "", ATOM).split()),
                "authors": [
                    a.findtext("a:name", "", ATOM) for a in e.findall("a:author", ATOM)
                ],
                "year": int(e.findtext("a:published", "", ATOM)[:4]),
                "venue": "arXiv",
                "url": f"https://arxiv.org/abs/{ident}",
                "pdf": f"https://arxiv.org/pdf/{ident}",
                "abstract": " ".join(e.findtext("a:summary", "", ATOM).split()),
            }
        )
    return out


def _abstract(inverted: dict[str, list[int]]) -> str:
    """OpenAlex's inverted index (word → positions) back into the abstract's text."""
    placed = sorted((i, word) for word, where in inverted.items() for i in where)
    return " ".join(word for _, word in placed)


def openalex(
    text: str, from_year: int, field: int, n: int, open_pdf: bool, page: int
) -> list[dict]:
    """The n most relevant OpenAlex works of one field whose title or abstract match the words.

    Args:
        text: The query.
        from_year: Earliest publication year.
        field: OpenAlex field id of the primary topic (20 is economics, econometrics and
            finance); without it a search for "futures" returns flood plains and alloys.
        n: How many to ask for.
        page: Which page of n, from 0.
        open_pdf: Keep only open-access works that name a PDF (owner, 2026-10-02): an abstract
            almost never states the rule, so a paper that cannot be read in full is not fetched.
    """
    reply = httpx.get(
        OPENALEX_API,
        headers=AGENT,
        timeout=60,
        params={
            "per-page": n,
            "page": page + 1,
            "sort": "relevance_score:desc",
            "filter": f"title_and_abstract.search:{text},has_abstract:true,"
            f"from_publication_date:{from_year}-01-01,type:article|preprint,"
            f"primary_topic.field.id:{field}"
            + (",open_access.is_oa:true" if open_pdf else ""),
        },
    )
    reply.raise_for_status()
    out = []
    for w in reply.json()["results"]:
        place = w.get("best_oa_location") or {}
        venue = ((w.get("primary_location") or {}).get("source") or {}).get(
            "display_name"
        ) or ""
        doi = (w.get("doi") or "").replace("https://doi.org/", "")
        arx = re.search(r"arxiv\.(\d{4}\.\d{4,5})", doi, re.I)
        out.append(
            {
                "key": "oa-" + w["id"].rsplit("/", 1)[-1],
                "source": "openalex",
                "arxiv": arx[1] if arx else "",
                "doi": doi,
                "title": " ".join((w["title"] or "").split()),
                "authors": [a["author"]["display_name"] for a in w["authorships"]],
                "year": w["publication_year"],
                "venue": venue,
                "url": w.get("doi") or w["id"],
                "pdf": place.get("pdf_url") or "",
                "pdfs": [
                    x["pdf_url"] for x in w.get("locations") or [] if x.get("pdf_url")
                ],
                "abstract": _abstract(w["abstract_inverted_index"]),
            }
        )
    return [p for p in out if p["pdf"] or not open_pdf]


def collection(repo: str, kind: str) -> list[dict]:
    """Every strategy of a code collection, in the repository's own order: its key and paths.

    Args:
        repo: `owner/name` on GitHub.
        kind: A key of KINDS: how one strategy is laid out there.

    Returns:
        `{key, repo, name, path, code}` — `path` the description file, `code` the Python files
        of the same strategy (none for a notebook: it is its own code).
    """
    reply = httpx.get(
        f"{GITHUB}/{repo}/git/trees/HEAD",
        headers=AGENT,
        timeout=120,
        params={"recursive": 1},
    )
    reply.raise_for_status()
    paths = [t["path"] for t in reply.json()["tree"] if t["type"] == "blob"]
    pattern, sub = KINDS[kind]
    out = []
    for path in paths:
        hit = re.match(pattern, path)
        if hit:
            folder = path.rsplit("/", 1)[0] + f"/{sub}/" if sub else None
            out.append(
                {
                    "key": f"gh-{repo.split('/')[0]}-{hit[1]}",
                    "repo": repo,
                    "name": hit[1],
                    "path": path,
                    "code": [
                        p
                        for p in paths
                        if folder and p.startswith(folder) and p.endswith(".py")
                    ],
                }
            )
    return out


def _notebook(raw: str) -> tuple[str, str]:
    """A notebook as (its first text cell, every cell's source and printed output)."""
    cells = json.loads(raw)["cells"]
    texts = ["".join(c["source"]) for c in cells if c["cell_type"] == "markdown"]
    body = []
    for c in cells:
        body.append("".join(c["source"]))
        body += [
            "".join(o.get("text", [])) for o in c.get("outputs", []) if "text" in o
        ]
    return (texts[0] if texts else ""), "\n".join(body)


def item(found: dict) -> Paper:
    """One strategy of a collection as a paper row: its description is the abstract, its code the text."""
    base = f"{RAW}/{found['repo']}/HEAD/"
    text = httpx.get(base + found["path"], headers=AGENT, timeout=60).text
    code = [httpx.get(base + p, headers=AGENT, timeout=60).text for p in found["code"]]
    if found["path"].endswith(".ipynb"):
        text, body = _notebook(text)
        code = [body]
    return {
        "key": found["key"],
        "source": "github",
        "arxiv": "",
        "doi": "",
        "title": found["name"],
        "authors": [found["repo"].split("/")[0]],
        "year": date.today().year,
        "venue": f"GitHub {found['repo']}",
        "url": f"https://github.com/{found['repo']}/blob/HEAD/{found['path']}",
        "pdf": "",
        "abstract": " ".join(text.split()),
        "pages": code,
    }


def site(name: str, index: str, link: str) -> list[dict]:
    """Every article a practitioner site lists on its index page, in the page's order.

    Args:
        name: The site's short name, for the keys.
        index: The page (or feed) that lists the articles.
        link: A regular expression over that page's raw text whose first group is an article's
            URL, absolute or from the site's root.

    Returns:
        `{key, url, venue}` per article, without repeats.
    """
    reply = httpx.get(index, headers=AGENT, timeout=60, follow_redirects=True)
    reply.raise_for_status()
    urls = dict.fromkeys(
        str(httpx.URL(index).join(u)) for u in re.findall(link, reply.text)
    )
    return [
        {
            "key": f"web-{name}-{u.rstrip('/').rsplit('/', 1)[-1]}"[:80],
            "url": u,
            "venue": name,
        }
        for u in urls
    ]


def article(found: dict) -> Paper:
    """One article of a site as a paper row: its text cut into pages, its start as the abstract."""
    reply = httpx.get(found["url"], headers=AGENT, timeout=60, follow_redirects=True)
    reply.raise_for_status()
    tree = html.fromstring(reply.text)
    # Not `header`: Oxfordstrat keeps the whole strategy inside one.
    for junk in tree.xpath("//script|//style|//nav|//footer|//form"):
        junk.drop_tree()
    text = " ".join(tree.text_content().split())
    return {
        "key": found["key"],
        "source": "web",
        "arxiv": "",
        "doi": "",
        "title": " ".join((tree.findtext(".//title") or found["key"]).split()),
        "authors": [found["venue"]],
        "year": date.today().year,
        "venue": found["venue"],
        "url": found["url"],
        "pdf": "",
        "abstract": text[:1500],
        "pages": [text[i : i + CHUNK] for i in range(0, len(text), CHUNK)],
    }
