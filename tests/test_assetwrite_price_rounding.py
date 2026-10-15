"""`assetwrite.set_price_rounding` writes the card's block after `instrument`, keeps the comments, and refuses a bad value."""

import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import assetwrite
from core.assetdata import SYMBOLS


def test_the_block_lands_after_instrument_and_the_file_still_loads() -> None:
    """Written into a copy of a card: the new block, the old comments, the rest untouched."""
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "XAUUSD.yaml"
        shutil.copy(SYMBOLS / "XAUUSD.yaml", copy)
        real = (assetwrite.path_of, assetwrite.reindex)
        assetwrite.path_of, assetwrite.reindex = lambda name: copy, lambda: 0
        try:
            assetwrite.set_price_rounding("XAUUSD", "tick", "prueba")
            text = copy.read_text(encoding="utf-8")
            try:
                assetwrite.set_price_rounding("XAUUSD", "round", "x")
            except ValueError:
                pass
            else:
                raise AssertionError("a value outside tick | none was written")
        finally:
            assetwrite.path_of, assetwrite.reindex = real
    assert (
        text.index("instrument:")
        < text.index("price_rounding:\n  use: tick")
        < text.index("costs:")
    )
    assert "# Lo que se aplica." in text


if __name__ == "__main__":
    test_the_block_lands_after_instrument_and_the_file_still_loads()
    print("test_assetwrite_price_rounding: ok")
