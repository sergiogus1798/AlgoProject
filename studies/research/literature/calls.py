#!/usr/bin/env python3
"""The two headless calls of a run, as text in and text out: their prompts, and their answers applied."""

import argparse
import glob
import json
import re
import sys
from pathlib import Path

import yaml

from core.paths import ROOT
from studies.research.literature import anchors, fetch, scout, store

RULES = Path(__file__).with_name("rules.md")
CONDITIONS = Path(__file__).parent.parent / "marketProfile" / "measure" / "rules.py"
BLOCK = re.compile(r"```(yaml|json)\n(.*?)```", re.S)
TRIAGE = """
# Your task: triage on the abstract only

Below are papers, each with its key, title and abstract. For each one decide, from the abstract
alone, whether a hard filter above rejects it. When in doubt, keep it: a kept paper is read in full.
Reply with ONLY a JSON array, one object per paper, nothing before or after it:
  {"key": "<key>", "keep": true}
  {"key": "<key>", "keep": false, "filter": "<filter name>", "quote": "<one verbatim sentence of
   the abstract that shows it>", "reason": "<one line>"}
"""
EXTRACT = """
# Your task: this one paper

Below is the paper's stored text: its abstract and the pages that state the rule, the data and
the result (other pages were left out; a field that is only there is `not stated in source`).
Places are `abstract` and `p. N`. Reply with ONLY fenced blocks, nothing else:
- one ```yaml block per rule the paper tests — a draft exactly as «The draft» above, with
  `paper: {key}`; or
- when a hard filter rejects the paper, or it states no rule, one ```json block:
  {{"filter": "<name>", "quote": "<verbatim sentence>", "where": "<abstract or p. N>", "reason": "<one line>"}}
The only condition keys a `measures` entry may use: {conditions}
This paper was read as: {read}.
"""


def rules(upto: str = "") -> str:
    """The shared rules text, whole or up to (not including) one of its headings."""
    text = RULES.read_text(encoding="utf-8")
    return text[:text.index(upto)] if upto else text


def answer(path: str) -> str:
    """The text a headless call replied with (`result` of its JSON)."""
    return json.loads(Path(path).read_text(encoding="utf-8"))["result"]


def triage_prompt(a: argparse.Namespace) -> None:
    """Print the triage call's prompt: the rule, the filters, and every inbox paper's abstract."""
    waiting = [p for p in store.papers().values() if p["status"] == "inbox"]
    print(rules("## The draft") + TRIAGE)
    for p in waiting:
        print(f"\n## {p['key']}\n{p['title']}\n{p['abstract']}")


def triage_apply(a: argparse.Namespace) -> None:
    """Record the rejections a triage answer names; a quote not in the abstract keeps the paper."""
    said = answer(a.result)
    for row in json.loads(said[said.index("["):said.rindex("]") + 1]):
        if row["keep"]:
            continue
        try:
            scout.reject(argparse.Namespace(key=row["key"], filter=row["filter"],
                                            quote=row["quote"], where="abstract",
                                            reason=row["reason"]))
        except SystemExit as refused:
            print(f"kept {row['key']}: {refused}")


def extract_prompt(a: argparse.Namespace) -> None:
    """Print one paper's extraction prompt; with `--retry`, its refused answer and the refusals."""
    paper = store.papers()[a.key]
    keys = re.findall(r'^\s+"(\w+)": lambda', CONDITIONS.read_text(encoding="utf-8"), re.M)
    cfg = store.config()["excerpt"]
    text = store.text_path(a.key).read_text(encoding="utf-8")
    print(rules() + EXTRACT.format(key=a.key, conditions=", ".join(keys), read=paper["read"]))
    print(fetch.excerpt(anchors.pages(text), cfg["words"], cfg["pages"]))
    if a.retry:
        print(f"\n# Your previous answer was refused\n\n{answer(a.retry)}\n\n# The refusals — fix "
              f"each from the text above, or reject the paper\n\n"
              + Path(a.refused).read_text(encoding="utf-8"))


def extract_apply(a: argparse.Namespace) -> None:
    """Accept each draft of an extraction answer, or record its rejection; exit 2 on a refusal.

    With `--last` a paper still refused and with no entry is closed as `failed`, so it is not
    read again tomorrow.
    """
    refusals, blocks = [], BLOCK.findall(answer(a.result))
    for kind, body in blocks:
        try:
            if kind == "json":
                row = json.loads(body)
                scout.reject(argparse.Namespace(key=a.key, filter=row["filter"], quote=row["quote"],
                                                where=row["where"], reason=row["reason"]))
            else:
                draft = yaml.safe_load(body)
                path = ROOT / "scratch" / "literature-scout" / f"{a.key}-{draft.get('slug')}.yaml"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(body, encoding="utf-8")
                scout.accept(argparse.Namespace(draft=str(path)))
        except SystemExit as refused:
            refusals.append(str(refused))
        except (yaml.YAMLError, json.JSONDecodeError, KeyError) as broken:
            refusals.append(f"a block could not be read: {type(broken).__name__}: {broken}")
    if not blocks:
        refusals.append("the answer holds no ```yaml or ```json block")
    held = store.papers()
    if refusals and a.last and held[a.key]["status"] == "inbox":
        held[a.key].update(status="failed", reason="; ".join(refusals)[:400])
        store.save_papers(held)
    if refusals:
        print("\n".join(refusals))
        sys.exit(2)


def under(a: argparse.Namespace) -> None:
    """Exit 1 once the calls of a run have used the run's token budget."""
    used = sum(json.loads(Path(f).read_text(encoding="utf-8"))["usage"][k]
               for f in glob.glob(a.prefix + "*.json") for k in scout.USAGE)
    sys.exit(used >= store.config()["run"]["budget_tokens"])


def main() -> None:
    """One subcommand per side of each call."""
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="step", required=True)
    sub.add_parser("triage-prompt").set_defaults(fn=triage_prompt)
    s = sub.add_parser("triage-apply")
    s.add_argument("result")
    s.set_defaults(fn=triage_apply)
    s = sub.add_parser("extract-prompt")
    s.add_argument("key")
    s.add_argument("--retry", default="", help="the refused answer's JSON")
    s.add_argument("--refused", default="", help="the file of its refusals")
    s.set_defaults(fn=extract_prompt)
    s = sub.add_parser("extract-apply")
    s.add_argument("key")
    s.add_argument("result")
    s.add_argument("--last", action="store_true", help="no retry left: close a refused paper")
    s.set_defaults(fn=extract_apply)
    s = sub.add_parser("under", help="exit 1 once the run's token budget is used")
    s.add_argument("prefix")
    s.set_defaults(fn=under)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
