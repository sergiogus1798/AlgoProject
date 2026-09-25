"""The envelope every study result travels in, and the progress line the window reads."""

import time
from datetime import datetime

from core.study import blocks
from core.study.config import fingerprint

DIGITS = 6


def progress(percent: int, state: str) -> None:
    """Print the line the window and the pipeline move their progress bar with.

    Args:
        percent: 0..100.
        state: What is running now, in Spanish.
    """
    print(f"PROGRESS {int(percent)} {state}", flush=True)


def envelope(module: str, strategy: str | None, identity: str | None, cfg: dict,
             started: float, tabs: list[dict], verdict: dict | None = None,
             warnings: list[dict] | None = None, glossary: list[dict] | None = None,
             summary: dict | None = None) -> dict:
    """One strategy's (or one population's) whole result, checked against the contract.

    Args:
        module: The module's dotted name, e.g. "studies.readings.profitShape".
        strategy: The strategy's name, None for a population result.
        identity: SHA-256 of its normalised XML (core.sqxfile.identity), None when the input
            does not carry it; the name alone does not identify a strategy.
        cfg: The config it was computed under.
        started: time.time() when the computation began.
        tabs: [{"name", "title", "selectors", "blocks"}], in reading order.
        verdict: A "verdict" block, None when the module describes and does not judge.
        warnings: {"code", "state", "text"} per warning; they colour and never eliminate.
        glossary: {"term", "text"} per term the tabs use.
        summary: The flat numbers one row of the population table carries for this
            strategy — what verdict.csv and many.run() read, so they never re-derive them.

    Returns:
        The result dict, validated.
    """
    for t in tabs:
        t.setdefault("selectors", [])
        t.setdefault("note", "")
    # Blocks are built from numpy results; plain() is the one place their scalars and NaNs
    # become JSON, so no module has to remember to cast. What is drawn keeps six significant
    # digits; the summary, which verdict.csv carries, keeps every digit.
    return blocks.validate({
        "module": module, "strategy": strategy, "identity": identity,
        "config_hash": fingerprint(cfg), "computed_at": datetime.now().isoformat("T", "seconds"),
        "wall_s": round(time.time() - started, 2),
        "verdict": blocks.plain(verdict, DIGITS), "tabs": blocks.plain(tabs, DIGITS),
        "warnings": warnings or [], "glossary": glossary or [],
        "summary": blocks.plain(summary or {})})


def tab(name: str, title: str, blocks_: list[dict], selectors: list[dict] | None = None,
        note: str = "") -> dict:
    """One tab of a result.

    Args:
        name: Short key, e.g. "familyA".
        title: What the tab's header says, in Spanish.
        blocks_: Its blocks, in reading order.
        selectors: {"key", "label", "options", "default"} per drop-down; each block then
            carries "select": {key: option} naming the combination it belongs to. A block
            that names fewer keys than there are selectors shows for any value of the rest.
        note: The paragraph the tab opens with, in Spanish; the window prints it under the
            tab's title.

    Returns:
        A tab dict.
    """
    return {"name": name, "title": title, "note": note, "selectors": selectors or [],
            "blocks": blocks_}
