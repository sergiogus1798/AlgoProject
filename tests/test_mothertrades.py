#!/usr/bin/env python3
"""sqx.variants.mothertrades: each batch gets its own mother's trades, tagged with her id and leg."""

import sys
import tempfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqx.variants import mothertrades


def batch(top: Path, name: str, origin: str) -> tuple[Path, list[dict]]:
    """A batch folder whose manifest flags `origin`, and two leg databanks holding its file."""
    work = top / name
    work.mkdir()
    pd.DataFrame(
        {
            "variant_id": ["P00000", "P00001"],
            "origin": [origin == "P00000", origin == "P00001"],
        }
    ).to_parquet(work / "manifest.parquet")
    legs = []
    for segment in ("oos1", "oos2"):
        bank = top / f"{name}_{segment}"
        bank.mkdir()
        for variant in ("P00000", "P00001"):
            (bank / f"{variant}.sqx").write_text(f"{name} {variant} {segment}")
        legs.append({"segment": segment, "databank_dir": str(bank)})
    return work, legs


def test_each_batch_gets_its_mother() -> None:
    """The export is one folder for every batch: what comes back is split by where it came from."""

    def trades(staged: Path, csvs: Path) -> None:
        """Stand in for orderstocsv: one CSV per staged file, its text as the only trade."""
        csvs.mkdir()
        for f in staged.glob("*.sqx"):
            (csvs / f"{f.stem}.csv").write_text(f.read_text())

    def pack(files: list[Path], out: Path, per_market: bool) -> dict:
        """Stand in for tradepack: `strategy` is the CSV's stem, as the real one writes it."""
        pd.DataFrame(
            {
                "strategy": pd.Categorical([f.stem for f in files]),
                "what": [f.read_text() for f in files],
            }
        ).to_parquet(out)
        return {}

    real = mothertrades.exportdrv.trades, mothertrades.tradepack.pack
    mothertrades.exportdrv.trades, mothertrades.tradepack.pack = trades, pack
    try:
        with tempfile.TemporaryDirectory() as tmp:
            made = [batch(Path(tmp), "A", "P00000"), batch(Path(tmp), "B", "P00001")]
            for work, legs in made:
                mothertrades.keep(work, legs)
            written = mothertrades.harvest([work for work, _ in made])
            assert list(written.values()) == [2, 2], written
            for (work, _), origin in zip(made, ("P00000", "P00001")):
                got = pd.read_parquet(work / mothertrades.OUT)
                assert sorted(got["what"]) == [
                    f"{work.name} {origin} oos1",
                    f"{work.name} {origin} oos2",
                ], got
                assert set(got["variant_id"]) == {origin} and "strategy" not in got
                assert all(row.what.endswith(row.segment) for row in got.itertuples())
    finally:
        mothertrades.exportdrv.trades, mothertrades.tradepack.pack = real


if __name__ == "__main__":
    test_each_batch_gets_its_mother()
    print("test_mothertrades: ok")
