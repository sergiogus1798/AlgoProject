#!/usr/bin/env python3
"""Literature scout: the anchors, the validator's refusals, the two dedupes, the build overlap, the
queue's states and the measures the profile takes from the entries — on a synthetic paper and
synthetic entries (nothing of AlgoData is read or written)."""

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import re

from studies.research.literature import (
    anchors,
    dedupe,
    fetch,
    schema,
    scout,
    search,
    selection,
    waiting,
)
from studies.research.marketProfile import literature

TEXT = """[abstract]
We test a channel rule on gold futures and find that it earns 4.1% a year before costs.
[page 1]
The rule buys when the close exceeds the highest close of the pre-
ceding 55 days, and sells when it falls below the lowest close of the preceding 20 days.
[page 2]
Our sample runs from January 1990 to December 2015. Proﬁts vanish after 2005.
We examined 12 parameter pairs and report the best one.
"""
SOURCE = anchors.pages(TEXT)
ABSENT = anchors.ABSENT
DRAFT = {
    "paper": "arxiv-0000.00000",
    "slug": "gold-channel-55-20",
    "asset_class": "metals",
    "assets": "gold futures",
    "family": "ruptura",
    "direction": "long on the breakout",
    "horizon": {
        "lookback": "55 days",
        "holding": "until the 20-day low",
        "source_bar": "daily",
    },
    "condition": ABSENT,
    "size": "4.1% a year before costs",
    "sample": "1990-2015",
    "grade": "working paper (arXiv)",
    "needs_clock": "no",
    "decay": "profits vanish after 2005",
    "selection": {
        "variants_tried": "12 parameter pairs, the best reported",
        "sample_from": 1990,
        "sample_to": 2015,
    },
    "translation": {
        "entry": "long when the close is above the highest close of 55 D1 bars",
        "hold": "until the close is below the lowest close of 20 D1 bars",
        "context": "D1",
        "params": "55 / 20",
        "note": "futures, not the CFD",
        "conditions": 1,
        "measures": [
            {
                "name": "gold_channel_55_20",
                "args": {"enter": "break_d55", "leave": "below_d20"},
            }
        ],
    },
    "anchors": {
        "rule": {
            "quote": "The rule buys when the close exceeds the highest close of the "
            "preceding 55 days",
            "where": "p. 1",
        },
        "assets": {
            "quote": "We test a channel rule on gold futures",
            "where": "abstract",
        },
        "direction": {"quote": "The rule buys when the close exceeds", "where": "p. 1"},
        "lookback": {
            "quote": "highest close of the preceding 55 days",
            "where": "p. 1",
        },
        "holding": {
            "quote": "sells when it falls below the lowest close of the preceding 20 days",
            "where": "p. 1",
        },
        "condition": ABSENT,
        "size": {"quote": "it earns 4.1% a year before costs", "where": "abstract"},
        "sample": {
            "quote": "Our sample runs from January 1990 to December 2015",
            "where": "p. 2",
        },
        "variants_tried": {"quote": "We examined 12 parameter pairs", "where": "p. 2"},
        "out_of_sample": {"quote": "Profits vanish after 2005.", "where": "p. 2"},
    },
}


def changed(**edits: object) -> dict:
    """The good draft with some keys replaced; a dotted key reaches one level down."""
    draft = copy.deepcopy(DRAFT)
    for key, new in edits.items():
        node, *rest = key.split("__")
        if rest:
            draft[node][rest[0]] = new
        else:
            draft[node] = new
    return draft


def refused(draft: dict, word: str, read: str = "full text") -> None:
    """The draft is refused, and one of the reasons names `word`."""
    wrong = schema.validate(draft, SOURCE, read, 20)
    assert any(word in w for w in wrong), (word, wrong)


def test_anchors() -> None:
    """A quote is the source's words at that place, and every anchor fault is named."""
    assert schema.validate(DRAFT, SOURCE, "full text", 20) == []
    # A word broken at the line end and a ligature (Proﬁts) are still the source's words.
    assert anchors.found("highest close of the preceding 55 days", "p. 1", SOURCE)
    assert anchors.found("Profits vanish after 2005", "p. 2", SOURCE)
    assert not anchors.found("Profits vanish after 2005", "p. 1", SOURCE)
    assert not anchors.found("highest close of the preceding 50 days", "p. 1", SOURCE)
    # A minus sign and a significance star are the result of a table row: they must match.
    row = {"p. 1": "SPX 0.10% \u22120.09% 0.20% \u2217\u2217 0.15%"}
    assert anchors.found("SPX 0.10% -0.09% 0.20% ** 0.15%", "p. 1", row)
    assert not anchors.found("SPX 0.10% 0.09% 0.20% ** 0.15%", "p. 1", row)
    assert not anchors.found("SPX 0.10% -0.09% 0.20% 0.15%", "p. 1", row)
    refused(
        changed(
            anchors__size={
                "quote": "it earns 5.1% a year before costs",
                "where": "abstract",
            }
        ),
        "size: the quote is not in the source",
    )
    refused(
        changed(anchors__size={"quote": "4.1% a year", "where": "abstract"}),
        "not a sentence",
    )
    refused(changed(anchors__size=ABSENT), "must be both the value and the anchor")
    refused(changed(size=ABSENT), "must be both the value and the anchor")
    refused(changed(anchors__rule=ABSENT, translation__entry=ABSENT), "no_rule")
    refused(DRAFT, "read as abstract only", read="abstract only")
    marks = {k: v for k, v in DRAFT["anchors"].items() if k != "sample"}
    refused(changed(anchors=marks), "anchors: missing sample")


def test_excerpt() -> None:
    """The excerpt keeps the abstract and the pages densest in rule words, and names the rest."""
    pages = {
        "abstract": "A.",
        "p. 1": "history of markets",
        "p. 2": "the rule buys; the rule sells",
        "p. 3": "acknowledgements",
        "p. 4": "our sample and the buy signal",
    }
    got = fetch.excerpt(pages, ["rule", "buy", "sell", "sample", "signal"], 2)
    assert got.index("[abstract]") < got.index("[p. 2]") < got.index("[p. 4]")
    assert "history" not in got and got.endswith("[left out: p. 1, p. 3]")


def test_repository() -> None:
    """A collection's layout is recognised, a notebook becomes text, and the grade is stamped."""
    pattern, _ = search.KINDS["stocksharp"]
    assert (
        re.match(pattern, "API/0001-0100/0002_NDay_Breakout/README.md")[1]
        == "0002_NDay_Breakout"
    )
    assert not re.match(pattern, "API/0001-0100/0002_NDay_Breakout/README_es.md")
    notebook = json.dumps(
        {
            "cells": [
                {
                    "cell_type": "markdown",
                    "source": ["# Momentum\n", "Long the winners."],
                },
                {
                    "cell_type": "code",
                    "source": ["run()"],
                    "outputs": [
                        {"text": ["Sharpe 0.8\n"]},
                        {"data": {"image/png": "…"}},
                    ],
                },
            ]
        }
    )
    first, body = search._notebook(notebook)
    assert first.startswith("# Momentum") and "run()" in body and "Sharpe 0.8" in body
    code = {
        "abstract": "Buys the break.",
        "pages": ["if close > high: buy()"],
        "pdf": "",
    }
    text, read, why = fetch.source(code)
    assert read == "full text" and "[page 1]\nif close > high" in text and why == ""
    paper = {
        "source": "github",
        "authors": ["StockSharp"],
        "year": 2026,
        "title": "0002_X",
        "venue": "GitHub StockSharp/AlgoTrading",
        "url": "u",
        "read": "full text",
    }
    cfg = {"prefix": {"ruptura": "BRK"}, "classes": {"metals": ["XAUUSD"]}}
    scout.store.next_number = lambda: 99
    assert (
        scout.stamp(DRAFT, paper, cfg, [])["grade"]
        == "code repository (GitHub StockSharp/AlgoTrading)"
    )
    assert "no_backtest" in schema.FILTERS


def test_rules() -> None:
    """The owner's hard rules: stamped keys, the clock, two conditions, the open question."""
    refused(changed(id="BRK-99-x"), "id is stamped")
    refused(changed(family="sesion"), "family")
    refused(changed(needs_clock="yes (session open)"), "needs_clock")
    refused(changed(translation__hold="exit at 16:00"), "reads the clock")
    refused(changed(translation__hold="held overnight"), "reads the clock")
    refused(changed(translation__conditions=3), "hard rule 14")
    refused(
        changed(
            translation__measures=[
                {
                    "name": "x",
                    "args": {"enter": "break_d55", "when": ["vol_up", "up_d200"]},
                }
            ]
        ),
        "more than one `when`",
    )
    question = {
        "text": "«the channel»: of closes or of highs?",
        "readings": ["highest close", "highest high"],
        "answer": "",
    }
    refused(changed(question=question), "not measured before the owner answers")
    asked = changed(question=question)
    del asked["translation"]["measures"]
    assert schema.validate(asked, SOURCE, "full text", 20) == []
    refused(
        changed(question={**question, "readings": ["one"]}), "at least two readings"
    )


def test_same_paper() -> None:
    """The same paper by arXiv id, by DOI and by title; a short title only with its author."""
    held = [
        {
            "key": "arxiv-2607.01550",
            "arxiv": "2607.01550",
            "doi": "",
            "title": "Is Trend Still Your Friend?",
        }
    ]
    entries = [
        {
            "id": "TR-01-tsmom-12m",
            "source": "Moskowitz, Ooi, Pedersen (2012), 'Time series "
            "momentum', J. Financial Economics 104:228-250 — https://x/TimeSeriesMomentum.pdf",
        },
        {
            "id": "TR-04-slow",
            "source": "Kurth et al. (2026), 'Is Trend Still Your Friend?', "
            "arXiv:2607.01550 — https://arxiv.org/abs/2607.01550",
        },
        {
            "id": "REV-36",
            "source": "Someone (2020), J. Banking, doi 10.1016/j.jbf.2020.01.5.",
        },
    ]

    def paper(**fields: object) -> dict:
        """A paper new to everything, but for the fields given."""
        return {
            "key": "new",
            "arxiv": "",
            "doi": "",
            "title": "Something else entirely here",
            "authors": ["A. Smith"],
            **fields,
        }

    assert dedupe.same_paper(paper(arxiv="2607.01550"), held, []) == "arxiv-2607.01550"
    assert dedupe.same_paper(paper(arxiv="2607.01550"), [], entries) == "TR-04-slow"
    assert (
        dedupe.same_paper(paper(doi="10.1016/j.jbf.2020.01.5"), [], entries) == "REV-36"
    )
    assert dedupe.same_paper(paper(title="Is trend still our friend"), held, []) == ""
    assert (
        dedupe.same_paper(paper(title="Is Trend still  your Friend?"), held, [])
        == "arxiv-2607.01550"
    )
    # A short title is inside many sources: it is the same paper only with its first author.
    short = paper(
        title="Time series momentum", authors=["Tobias J. Moskowitz", "Y. Ooi"]
    )
    assert dedupe.same_paper(short, [], entries) == "TR-01-tsmom-12m"
    assert dedupe.same_paper({**short, "authors": ["A. Smith"]}, [], entries) == ""
    assert dedupe.same_paper(paper(), held, entries) == ""


def test_same_rule() -> None:
    """The same rule under another name or family, in the profile or in an entry; rules alike."""
    measures = [
        {
            "name": "donchian_d55_opp",
            "family": "ruptura",
            "fn": "rule",
            "lit": "BRK-14",
            "args": {"enter": "break_d55", "leave": "below_d20"},
        },
        {"name": "channel55", "family": "ruptura", "fn": "breakout", "args": {"N": 55}},
    ]
    mine = DRAFT["translation"]["measures"][0]["args"]
    assert dedupe.same_rule(mine, [], measures) == "measure donchian_d55_opp (BRK-14)"
    longer = {**mine, "days": 20}
    assert dedupe.same_rule(longer, [], measures) == ""
    stored = {
        **changed(translation__measures=[{"name": "y", "args": longer}]),
        "id": "BRK-70-x",
    }
    assert dedupe.same_rule(longer, [stored], []) == "BRK-70-x"
    # An empty filter list, a cap of 0 spelled out, another family: still the same rule.
    a = {"enter": "rsi_low", "when": ["up_d200"]}
    b = {
        **changed(
            family="reversion",
            translation__measures=[
                {
                    "name": "b",
                    "args": {
                        "enter": "rsi_low",
                        "when": ["up_d200"],
                        "cap": 0,
                        "days": 0,
                    },
                }
            ],
        ),
        "id": "REV-71-x",
    }
    assert dedupe.same_rule(a, [b], []) == "REV-71-x"
    assert dedupe.same_rule({**mine, "when": []}, [], measures).startswith(
        "measure donchian"
    )
    near = {
        **changed(
            translation__entry="long when the close is above the highest close of "
            "50 D1 bars"
        ),
        "id": "BRK-72-x",
    }
    far = {
        **changed(translation__entry="long when RSI(2) is under 10"),
        "id": "BRK-73-x",
    }
    assert dedupe.similar(DRAFT, [near, far], 0.6) == ["BRK-72-x"]


def test_overlap() -> None:
    """The authors' sample against the build window, and the assets an entry speaks of."""
    # XAUUSD's build is 2008-2017 (assets/symbols/XAUUSD.yaml).
    assert selection.overlap(None, 2015, ["XAUUSD"]) == ABSENT
    assert selection.overlap(1985, 2005, ["XAUUSD"]).startswith("no:")
    assert selection.overlap(1985, 2009, ["XAUUSD"]).startswith("partly:")
    assert selection.overlap(1990, 2025, ["XAUUSD"]).startswith("yes, fully:")
    classes = {"metals": ["XAUUSD", "XAGUSD"], "oils": ["USOIL"]}
    assert selection.symbols(DRAFT, classes) == ["XAUUSD", "XAGUSD"]
    assert selection.symbols({**DRAFT, "assets": "XAGUSD only"}, classes) == ["XAGUSD"]


def test_queue_and_profile() -> None:
    """The queue's four states, and which measures the profile takes from the entries."""
    good = {**DRAFT, "id": "BRK-63-gold-channel"}
    question = {"text": "?", "readings": ["a", "b"], "answer": ""}
    asked = {**changed(question=question), "id": "BRK-64-asked"}
    bad = {
        **changed(
            translation__measures=[
                {"name": "z", "args": {"enter": "no_such_condition"}}
            ]
        ),
        "id": "BRK-65-bad",
    }
    bare = {**changed(), "id": "BRK-66-bare"}
    del bare["translation"]["measures"]
    assert waiting.state(good, set()) == waiting.WAITING
    assert waiting.state(good, {"gold_channel_55_20"}) == waiting.MEASURED
    assert waiting.state(asked, {"gold_channel_55_20"}) == waiting.QUESTION
    assert waiting.state(bare, set()) == waiting.NO_MEASURE
    known = {
        **bare,
        "translation": {**bare["translation"], "tested_by": ["tsmom_d252_run"]},
    }
    assert waiting.state(known, {"tsmom_d252_run"}) == waiting.MEASURED
    specs, skipped = literature.specs([good, asked, bad, bare], {"taken"})
    assert [(s["name"], s["lit"], s["tag"], s["fn"]) for s in specs] == [
        ("gold_channel_55_20", "BRK-63", "literature", "rule")
    ]
    assert (
        len(skipped) == 2
        and "pregunta" in skipped[0]
        and "no_such_condition" in skipped[1]
    )
    assert literature.specs([good], {"gold_channel_55_20"})[0] == []


if __name__ == "__main__":
    for test in (
        test_anchors,
        test_excerpt,
        test_repository,
        test_rules,
        test_same_paper,
        test_same_rule,
        test_overlap,
        test_queue_and_profile,
    ):
        test()
    print("test_literature: ok")
