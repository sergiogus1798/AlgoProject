"""A paper's source as stored text: its abstract, and its full text page by page when reachable."""

import io

import httpx
from pypdf import PdfReader

AGENT = {"User-Agent": "AlgoProject-literatureScout/1.0"}


def pdf_pages(url: str) -> tuple[list[str], str]:
    """The text of each page of the PDF at a URL, or no pages and why.

    A publisher that answers a script with a login page or a 403 (SSRN does) is the expected
    case, not an error: the paper is then read from its abstract only.
    """
    try:
        reply = httpx.get(url, headers=AGENT, timeout=120, follow_redirects=True)
    except httpx.HTTPError as error:
        return [], f"{url}: {type(error).__name__}"
    if reply.status_code != 200 or not reply.content.startswith(b"%PDF"):
        kind = reply.headers.get("content-type", "?")
        return [], f"{url}: HTTP {reply.status_code}, {kind}, not a PDF"
    return [
        page.extract_text() or "" for page in PdfReader(io.BytesIO(reply.content)).pages
    ], ""


def source(paper: dict) -> tuple[str, str, str]:
    """The text to store for a paper, and how much of it was read.

    Args:
        paper: A row of the papers register (`abstract`, `pdf`).

    Returns:
        (the text — `[abstract]` and one `[page N]` mark per page —, "full text" or
        "abstract only", why the full text could not be read or '').
    """
    if paper.get("pages"):  # a code repository's item: its code arrived with the search
        pages, why = paper["pages"], ""
    else:
        pages, why = [], "no open-access PDF known"
        # Every copy OpenAlex knows of, the best first: one host refusing is not the paper's end.
        for url in dict.fromkeys([paper["pdf"], *paper.get("pdfs", [])]):
            if url and not pages:
                pages, why = pdf_pages(url)
    text = f"[abstract]\n{paper['abstract']}\n"
    text += "".join(f"[page {n}]\n{page}\n" for n, page in enumerate(pages, 1))
    full = bool(paper.get("pages")) or sum(len(p) for p in pages) > 2 * len(
        paper["abstract"]
    )
    return (
        text,
        "full text" if full else "abstract only",
        "" if full else why or "a PDF with no text",
    )


def excerpt(pages: dict[str, str], words: list[str], most: int) -> str:
    """The abstract and the pages that speak most of the rule, in reading order.

    Reading a whole paper costs its length in tokens; the rule, the sample and the result sit
    on a few pages. A quote from any page still validates: the stored text is whole.

    Args:
        pages: The stored source by place (anchors.pages).
        words: Words that mark a page as stating the rule, the data or the result.
        most: Pages to keep beside the abstract.

    Returns:
        The kept pages under their `[p. N]` marks, and a last line naming the pages left out.
    """
    body = [k for k in pages if k != "abstract"]
    hits = {k: sum(pages[k].lower().count(w) for w in words) for k in body}
    kept = set(sorted(body, key=lambda k: -hits[k])[:most])
    out = [f"[abstract]\n{pages['abstract']}"] + [
        f"[{k}]\n{pages[k]}" for k in body if k in kept
    ]
    left = [k for k in body if k not in kept]
    return "\n".join(out) + f"\n[left out: {', '.join(left) or 'nothing'}]"
