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

# core.paths may be loaded already by an earlier test, so point the module at the temp root
DATA = shards.DATA = TMP
shards.REMOTE = TMP / "ledger" / "_remote"


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


def test_outside_data_and_empty_csv() -> None:
    """A ledger path outside the data root works; a zero-byte pulled CSV is skipped."""
    out = TMP.parent / f"{TMP.name}_out" / "a.jsonl"
    put(out, [{"ts": "2026-10-01", "n": 1}])
    assert [r["n"] for r in shards.read_all(out)] == [1]
    f = DATA / "ledger" / "cells" / "empty.csv"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("project,date\nP,2026-10-01\n", encoding="utf-8")
    z = shards.REMOTE / "gorilla" / "ledger" / "cells" / "empty.csv"
    z.parent.mkdir(parents=True, exist_ok=True)
    z.write_bytes(b"")
    assert [r["project"] for r in shards.read_all(f)] == ["P"]


def test_phase2_write_and_count() -> None:
    """append writes this server's shard with host and id; study.read and studies() count a row that
    only lives under _remote/gorilla; the board's attempts count a Simple Strategy of the registry."""
    from ledger import record, study

    real = study.path
    study.path = lambda sid: DATA / "ledger" / f"{sid}.jsonl"
    try:
        row = {"ts": "2026-10-05T00:00:00+00:00", "step": 8, "n_in": 10, "n_out": 2}
        record.append("Z_H1_s", row)
        mine = shards.shard_path(DATA / "ledger" / "Z_H1_s.jsonl")
        written = json.loads(mine.read_text().splitlines()[0])
        assert written["host"] == shards.server() and written["id"]
        put(
            shards.REMOTE / "gorilla" / "ledger" / "Z_H1_s.jsonl",
            [{"ts": "2026-10-06T00:00:00+00:00", "step": 6, "n_in": 5, "n_out": 5}],
        )
        put(shards.REMOTE / "gorilla" / "ledger" / "G_M15_t.gorilla.jsonl", [row])
        record.append("Z_H1_s", row)  # a genuine identical search stays a second row
        assert len(study.read("Z_H1_s")) == 3  # two of this server's + gorilla's
        assert {"Z_H1_s", "G_M15_t"} <= set(study.studies())  # a study only gorilla ran
        assert not any("." in x for x in study.studies())
    finally:
        study.path = real
    from studies.research.memory import attempts

    reg = {
        "symbol": "GBPJPY",
        "timeframe": "H1",
        "template": "simple:long",
        "family": "momentum",
    }
    got = attempts.one(
        "Trade_GBPJPY_H1_momentumL_gorilla", reg, {}, {}, frozenset(), TMP
    )
    assert (got["symbol"], got["timeframe"], got["direction"], got["family"]) == (
        "GBPJPY",
        "H1",
        "long",
        "momentum",
    )


if __name__ == "__main__":
    test_union()
    test_csv()
    test_outside_data_and_empty_csv()
    test_phase2_write_and_count()
    print("ok")
