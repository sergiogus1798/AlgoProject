"""`registry.check_name` and `registry.kind`: the three allowed prefixes and what is refused."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqx.projects import registry                          # noqa: E402


def test_check_name() -> None:
    """Three prefixes pass; a bare prefix, lowercase, spaces and other prefixes are refused."""
    for ok in ("Test_a", "Trade_XAUUSD_x_H1", "Research_XAUUSD_ideaA_H4"):
        assert registry.check_name(ok) is None, ok
    for bad in ("Research", "Research_", "research_x", "Builder", "Test x", "Research_a b", "Foo_x"):
        assert registry.check_name(bad), bad


def test_kind() -> None:
    """Each prefix maps to its kind, anything else is legacy."""
    assert registry.kind("Test_a") == "test"
    assert registry.kind("Trade_a") == "trade"
    assert registry.kind("Research_a") == "research"
    assert registry.kind("XAU_old") == "legacy"


if __name__ == "__main__":
    test_check_name()
    test_kind()
    print("ok")
