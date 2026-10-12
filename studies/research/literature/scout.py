#!/usr/bin/env python3
"""The scout's command: search papers, fetch one, reject it with its reason, accept or amend an entry."""

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

import yaml

from studies.research.literature import (amend, anchors, dedupe, fetch, gather, schema,
                                         selection, store)

ORDER = ["id", "paper", "asset_class", "assets", "family", "direction", "horizon", "condition",
         "size", "sample", "source", "grade", "verified", "read", "needs_clock", "overlaps_is",
         "overlaps_oos1", "overlaps_oos2",
         "decay", "selection", "translation", "anchors", "question", "similar_to"]
# The four token counts of a headless run's `usage`: what was written, read and cached.
USAGE = ["input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"]


def find(a: argparse.Namespace) -> None:
    """Ask every source for every query and keep the papers never seen, up to `--papers`."""
    cfg, held, entries = store.config(), store.papers(), store.entries()
    run, new = datetime.now().strftime("%Y%m%d-%H%M%S"), []
    want, per = a.papers or cfg["run"]["papers"], cfg["run"]["per_query"]
    if cfg["sources"]["repos"]["enabled"]:
        gather.collections(cfg["sources"]["repos"], run, held, new)
    if cfg["sources"]["web"]["enabled"]:
        gather.sites(cfg["sources"]["web"], run, held, new)
    want += len(new)    # `papers` counts the papers: repository and site items come on top
    for query in cfg["queries"]:
        taken = 0
        # A query's first page is soon all known: go deeper until it gives its share.
        for page in range(cfg["run"]["pages"]):
            if taken == per or len(new) == want:
                break
            taken += gather.page(query, page, run, per - taken, want - len(new), held, entries,
                                 new)
            time.sleep(cfg["run"]["pause_s"])
    store.save_papers(held)
    print(f"RUN {run}: {len(new)} papers new to the register")
    show(new)


def show(papers: list[dict]) -> None:
    """Print each paper as the scout triages it: key, year, venue, title and abstract."""
    for p in papers:
        print(f"\n## {p['key']} · {p['year']} · {p['venue']} · pdf {'yes' if p['pdf'] else 'no'}\n"
              f"{p['title']}\n{p['abstract']}")


def inbox(a: argparse.Namespace) -> None:
    """The papers found and not yet rejected or accepted: what an interrupted run left."""
    waiting = [p for p in store.papers().values() if p["status"] == "inbox"]
    print(f"{len(waiting)} papers in the inbox, runs {sorted({p['run'] for p in waiting})}")
    show(waiting)


def text_of(paper: dict) -> dict[str, str]:
    """A paper's source by place: the stored text, or its abstract while nothing was fetched."""
    path = store.text_path(paper["key"])
    if path.exists():
        return anchors.pages(path.read_text(encoding="utf-8"))
    return {"abstract": paper["abstract"]}


def get(a: argparse.Namespace) -> None:
    """Store a paper's source and say how much of it could be read."""
    held = store.papers()
    paper = held[a.key]
    text, paper["read"], why = fetch.source(paper)
    path = store.text_path(a.key)
    path.write_text(text, encoding="utf-8")
    store.save_papers(held)
    print(f"{paper['read']}: {path} ({len(anchors.pages(text)) - 1} pages)"
          + (f" — {why}" if why else ""))


def excerpt(a: argparse.Namespace) -> None:
    """Print the pages of a stored paper that speak of its rule, its sample and its results."""
    cfg = store.config()["excerpt"]
    text = store.text_path(a.key).read_text(encoding="utf-8")
    print(fetch.excerpt(anchors.pages(text), cfg["words"], cfg["pages"]))


def reopen(a: argparse.Namespace) -> None:
    """Put a rejected or failed paper back in the inbox, so the next run reads it again."""
    held = store.papers()
    held[a.key].update(status="inbox", filter="", quote="", reason="", read="")
    store.save_papers(held)
    print(f"{a.key}: back in the inbox")


def reject(a: argparse.Namespace) -> None:
    """Record a rejection: the hard filter, the sentence of the source that shows it, the reason."""
    held = store.papers()
    paper = held[a.key]
    if a.filter not in schema.FILTERS:
        raise SystemExit(f"filter: one of {list(schema.FILTERS)}")
    if a.filter != "unreadable" and not anchors.found(a.quote, a.where, text_of(paper)):
        raise SystemExit(f"the quote is not in the source at {a.where}: nothing recorded")
    paper.update(status="rejected", filter=a.filter, quote=a.quote, where=a.where,
                 reason=a.reason)
    store.save_papers(held)
    print(f"rejected {a.key}: {a.filter}")


def stamp(draft: dict, paper: dict, cfg: dict, similar: list[str]) -> dict:
    """A validated draft as a stored entry: its id, source, how it was read, the build overlap."""
    names = ", ".join(paper["authors"][:3]) + (" et al." if len(paper["authors"]) > 3 else "")
    chosen = draft["selection"]
    entry = {**draft,
             "id": f"{cfg['prefix'][draft['family']]}-{store.next_number()}-{draft['slug']}",
             "source": f"{names} ({paper['year']}), '{paper['title']}', {paper['venue']} — "
                       f"{paper['url']} ({paper['read']} read)",
             "verified": schema.READS[paper["read"]], "read": paper["read"],
             **{f"overlaps_{k}": selection.overlap(chosen["sample_from"], chosen["sample_to"],
                                                   selection.symbols(draft, cfg["classes"]), seg)
                for k, seg in (("is", "build"), ("oos1", "oos1"), ("oos2", "oos2"))},
             "similar_to": similar}
    if paper["source"] == "github":    # never the draft's word: a repository is not a paper
        entry["grade"] = f"code repository ({paper['venue']})"
    return {k: entry[k] for k in ORDER if k in entry}


def accept(a: argparse.Namespace) -> None:
    """Validate a draft entry against its stored source and store it; print every refusal."""
    cfg, held, entries = store.config(), store.papers(), store.entries()
    draft = yaml.safe_load(Path(a.draft).read_text(encoding="utf-8"))
    paper = held[draft["paper"]]
    wrong = schema.validate(draft, text_of(paper), paper["read"], cfg["anchors"]["min_chars"])
    specs = [] if wrong else draft["translation"].get("measures", [])
    taken, twins = amend.clashes(specs, entries)
    if specs and len(twins) == len(specs):
        paper["status"] = paper["status"] if paper["entries"] else "duplicate"
        paper["reason"] = f"same rule: {'; '.join(twins)}"
        store.save_papers(held)
        return print(f"DUPLICATE: {'; '.join(twins)}; nothing stored")
    wrong += taken + [f"translation.measures: {t} — drop that measure" for t in twins]
    if wrong:
        raise SystemExit("REFUSED\n" + "\n".join(f"- {w}" for w in wrong))
    entry = stamp(draft, paper, cfg, dedupe.similar(draft, entries, cfg["dedupe"]["similar"]))
    path = store.add(entry, datetime.now().strftime("%Y-%m-%d"))
    paper["status"] = "accepted"
    paper["entries"].append(entry["id"])
    store.save_papers(held)
    print(f"ACCEPTED {entry['id']} -> {path}"
          + (f"\nsimilar to {entry['similar_to']}" if entry["similar_to"] else ""))


def measure(a: argparse.Namespace) -> None:
    """Add measures to a stored entry from a YAML list of `{name, args}`."""
    wrong = amend.measures(a.id, yaml.safe_load(Path(a.specs).read_text(encoding="utf-8")))
    if wrong:
        raise SystemExit("REFUSED\n" + "\n".join(f"- {w}" for w in wrong))
    print(f"{a.id}: measures written; run the profile's --top-up")


def cost(a: argparse.Namespace) -> None:
    """Close a run: what it read and stored, and what it cost in tokens (owner: never dollars).

    `tokens` is every token of every call — written, read and re-read from the cache —;
    `tokens_reread` is the part that was the same context read again, known for headless calls.
    """
    reread = None
    if a.result:
        said = [json.loads(Path(f).read_text(encoding="utf-8")) for f in a.result]
        a.tokens = sum(s["usage"][k] for s in said for k in USAGE)
        reread = sum(s["usage"]["cache_read_input_tokens"] for s in said)
    mine = [p for p in store.papers().values() if p["run"] == a.run]
    count = {s: sum(p["status"] == s for p in mine) for s in
             ("inbox", "rejected", "accepted", "duplicate", "failed")}
    made = sum(len(p["entries"]) for p in mine)
    read = len(mine) - count["duplicate"]
    row = {"run": a.run, "papers": read, **count, "entries": made, "model": a.model,
           "calls": len(a.result) or None, "tokens": a.tokens, "tokens_reread": reread,
           "tokens_per_paper": round(a.tokens / read) if read else None,
           "tokens_per_entry": round(a.tokens / made) if made else None}
    store.add_run(row)
    print(json.dumps(row, indent=1))


def main() -> None:
    """One subcommand per step of a scout run."""
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="step", required=True)
    s = sub.add_parser("search", help="find papers never seen and print their abstracts")
    s.add_argument("--papers", type=int, default=0, help="how many (default: the config's)")
    s.set_defaults(fn=find)
    sub.add_parser("inbox", help="the papers found and not yet decided").set_defaults(fn=inbox)
    s = sub.add_parser("fetch", help="store one paper's full text, or its abstract")
    s.add_argument("key")
    s.set_defaults(fn=get)
    s = sub.add_parser("excerpt", help="the pages that state the rule, instead of the whole paper")
    s.add_argument("key")
    s.set_defaults(fn=excerpt)
    s = sub.add_parser("reopen", help="put a rejected paper back in the inbox")
    s.add_argument("key")
    s.set_defaults(fn=reopen)
    s = sub.add_parser("reject", help="record a rejection by a hard filter")
    s.add_argument("key")
    s.add_argument("--filter", required=True)
    s.add_argument("--quote", default="", help="the verbatim sentence that shows it")
    s.add_argument("--where", default="abstract", help="abstract, or `p. N`")
    s.add_argument("--reason", required=True)
    s.set_defaults(fn=reject)
    s = sub.add_parser("accept", help="validate a draft entry and store it")
    s.add_argument("draft")
    s.set_defaults(fn=accept)
    s = sub.add_parser("measure", help="add measures to a stored entry (a session, not the agent)")
    s.add_argument("id")
    s.add_argument("specs", help="a YAML file: a list of {name, args}")
    s.set_defaults(fn=measure)
    s = sub.add_parser("cost", help="close a run with its tokens")
    s.add_argument("run")
    s.add_argument("--tokens", type=int, default=0)
    s.add_argument("--result", nargs="+", default=[],
                   help="the JSON files `claude -p --output-format json` wrote, one per call")
    s.add_argument("--model", default="")
    s.set_defaults(fn=cost)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
