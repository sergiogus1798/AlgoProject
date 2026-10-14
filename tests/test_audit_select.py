"""Known-answer test for tools/audit_tests.py `select`: which tests a change reaches."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import audit_tests  # noqa: E402

GRAPH = {
    "core/a.py": set(),
    "core/b.py": {"core/a.py"},
    "studies/s.py": {"core/b.py"},
    "tests/test_a.py": {"core/a.py"},
    "tests/test_s.py": {"studies/s.py"},
    "tests/test_other.py": {"core/c.py"},
    "tests/helper.py": {"core/a.py"},
}

if __name__ == "__main__":
    # a leaf change reaches direct and transitive importers
    assert list(audit_tests.select({"core/a.py"}, GRAPH)) == [
        "tests/test_a.py",
        "tests/test_s.py",
    ]
    # a change in the middle reaches only what sits above it
    assert list(audit_tests.select({"core/b.py"}, GRAPH)) == ["tests/test_s.py"]
    # a changed test selects itself; a non-test file under tests/ does not
    assert list(
        audit_tests.select({"tests/test_other.py", "tests/helper.py"}, GRAPH)
    ) == ["tests/test_other.py"]
    # nothing imports it: nothing selected
    assert audit_tests.select({"studies/s2.py"}, GRAPH) == {}
    print("ok")
