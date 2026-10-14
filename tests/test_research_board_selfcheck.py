#!/usr/bin/env python3
"""Research board: the profile's self-examination on synthetic tables (split from test_research_board)."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from test_research_board import CFG, attempt, score  # noqa: E402

from studies.research.board import selfcheck  # noqa: E402


def test_selfcheck_known_answers() -> None:
    """Too few runs: says so. A profile that orients: keep. One that does not: reduce, with cost."""
    cfg = CFG["selfcheck"]
    few = pd.DataFrame({"score": [10.0, 60.0], "survived": [False, True]})
    got = selfcheck.judge(few, cfg)
    assert not got["enough"] and "hacen falta 20" in selfcheck.text(got, 0.5)
    good = pd.DataFrame(
        {
            "score": [20.0] * 15 + [70.0] * 15,
            "survived": [False] * 14 + [True] + [True] * 12 + [False] * 3,
        }
    )
    got = selfcheck.judge(good, cfg)
    assert got["decision"] == "mantener" and got["proven"] and got["p"] < 0.001
    assert got["runs_saved"] == 15 and got["survivor_runs_lost"] == 1
    flat = pd.DataFrame(
        {
            "score": [20.0] * 15 + [70.0] * 15,
            "survived": ([True] * 5 + [False] * 10) * 2,
        }
    )
    got = selfcheck.judge(flat, cfg)
    assert (
        got["decision"] == "reducir"
        and not got["proven"]
        and got["survivor_runs_lost"] == 5
    )
    assert "de 0.50 a 0.25" in selfcheck.text(got, 0.5)


def test_selfcheck_joins_only_closed_runs() -> None:
    """Dev draws, failed and unknown runs are not evidence."""
    scores = pd.DataFrame(
        [
            score("XAUUSD", "momentum", 3.0, True),
            score("EURUSD", "momentum", 3.0, False),
        ]
    )
    rows = [
        attempt("XAUUSD", "momentum", "survivors"),
        attempt("EURUSD", "momentum", "died@gate"),
        attempt("EURUSD", "momentum", "failed@9"),
        attempt("XAUUSD", "momentum", "unknown"),
        {**attempt("XAUUSD", "momentum", "survivors"), "dev_cut": "yes"},
    ]
    runs = selfcheck.closed_runs(rows, scores)
    assert sorted(runs["survived"]) == [False, True]


def main() -> None:
    """Run every test in file order."""
    for name, test in [(n, t) for n, t in globals().items() if n.startswith("test_")]:
        test()
        print("ok", name)


if __name__ == "__main__":
    main()
