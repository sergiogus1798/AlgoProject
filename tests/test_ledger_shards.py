#!/usr/bin/env python3
"""D27 phase 1: the union of shards counts a common row once, legacy rows dedup against the same
row with `id`/`host`, and the rows of every shard add up. Data root is a temp folder."""

import json
import os
import sys
import tempfile
from pathlib import Path

TMP = Path(tempfile.mkdtemp())
os.environ["ALGO_DATA_ROOT"] = str(TMP)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ledger import shards  # noqa: E402
from core.paths import DATA  # noqa: E402

assert DATA == TMP


def put(file: Path, rows: list[dict]) -> None:
    """Write rows as a jsonl file."""
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def test_union() -> None:
    """Common row once, legacy against id, N summed, pulling twice idempotent."""
    f = DATA / "ledger" / "X_H1_s.jsonl"
    a = {"ts": "2026-10-01", "n": 1}
    b = {"ts": "2026-10-02", "n": 2}
    c = {"ts": "2026-10-03", "n": 3}
    put(f, [a])  # legacy
    put(shards.shard_path(f), [{**b, "id": "zz", "host": shards.server()}])
    # gorilla's pulled shard: the common row b, plus its own c
    remote = shards.REMOTE / "gorilla" / "ledger"
    put(
        remote / "X_H1_s.gorilla.jsonl",
        [{**b, "host": "gorilla"}, {**c, "host": "gorilla"}],
    )
    got = shards.read_all(f)
    assert [r["n"] for r in got] == [1, 2, 3], got  # b once; order by ts
    assert len(got) == 3  # N summed across shards
    # legacy line without id == the same row with id/host
    assert shards.row_id(json.dumps(b)) == shards.row_id(
        json.dumps({**b, "id": "q", "host": "h"})
    )
    # idempotent: a second pull of the same file adds nothing
    put(
        remote / "X_H1_s.gorilla.jsonl",
        [{**b, "host": "gorilla"}, {**c, "host": "gorilla"}],
    )
    assert len(shards.read_all(f)) == 3


def test_csv() -> None:
    """judgements.csv unions across servers."""
    f = DATA / "ledger" / "cells" / "judgements.csv"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("project,date,sha256\nP,2026-10-01,aa\n", encoding="utf-8")
    r = shards.REMOTE / "gorilla" / "ledger" / "cells"
    r.mkdir(parents=True)
    (r / "judgements.csv").write_text(
        "project,date,sha256\nP,2026-10-01,aa\nQ,2026-10-02,bb\n"
    )
    got = shards.read_all(f)
    assert [x["project"] for x in got] == ["P", "Q"], got


if __name__ == "__main__":
    test_union()
    test_csv()
    print("ok")
