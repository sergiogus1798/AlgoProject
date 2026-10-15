"""`assetdata.load` refuses an unquoted `rollout_hour`: YAML reads 23:00 as the integer 1380."""

import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import assetdata


def test_an_unquoted_hour_is_refused_and_every_card_is_quoted() -> None:
    """A copy of a card with `rollout_hour: 23:00` fails to load; the real cards all load."""
    with tempfile.TemporaryDirectory() as tmp:
        card = Path(tmp) / "ZZTEST.yaml"
        shutil.copy(assetdata.SYMBOLS / "AUS200.yaml", card)
        card.write_text(
            card.read_text(encoding="utf-8").replace('"23:00"', "23:00"),
            encoding="utf-8",
        )
        real = assetdata.SYMBOLS
        assetdata.SYMBOLS = Path(tmp)
        try:
            assetdata.load("ZZTEST")
            raise AssertionError("an unquoted rollout_hour loaded")
        except ValueError as e:
            assert "1380" in str(e)
        finally:
            assetdata.SYMBOLS = real
    for f in sorted(assetdata.SYMBOLS.glob("*.yaml")):
        assetdata.load(f.stem)


if __name__ == "__main__":
    test_an_unquoted_hour_is_refused_and_every_card_is_quoted()
    print("test_assetdata_rollout_hour: ok")
