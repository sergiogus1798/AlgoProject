"""A test databank's Ficha reads the build's cosecha by name, and says so (ui.daemon.tearsheet.borrow)."""
import sys
import tempfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ui.daemon.tearsheet import borrow, harvest  # noqa: E402

P = "Test_X"


def cosecha(root: Path, names: list[str]) -> None:
    """A Results cosecha holding these strategies, one identity each."""
    day = root / "harvest" / P / "Results" / "2026-09-30"
    day.mkdir(parents=True)
    pd.DataFrame({"identity": [f"h{i}" for i in range(len(names))], "strategy": names}
                 ).set_index("identity").to_parquet(day / "metrics.parquet")


def main() -> None:
    """Borrowed by name when unique; a sentence when cut or doubled; nothing when no cosecha."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        borrow.DATA = harvest.DATA = root
        borrow.find.roster = lambda project, databank: {"w1": "Strategy 1", "w2": "Strategy 9",
                                                        "w3": "Strategy 2"}
        assert borrow.borrow(P, "WFM", "w1", harvest.newest) is None      # no cosecha at all
        cosecha(root, ["Strategy 1", "Strategy 2", "Strategy 2"])
        home, identity, note = borrow.borrow(P, "WFM", "w1", harvest.newest)
        assert (home, identity) == ("Results", "h0") and "emparejada por nombre" in note
        assert "se quedó fuera" in borrow.borrow(P, "WFM", "w2", harvest.newest)
        assert "tiene 2" in borrow.borrow(P, "WFM", "w3", harvest.newest)
        assert borrow.borrow(P, "WFM", "nobody", harvest.newest) is None
        assert borrow.borrow(P, "Results", "w1", harvest.newest) is None  # its own cosecha
    print("ok")


if __name__ == "__main__":
    main()
