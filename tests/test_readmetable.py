"""tools/readmetable.render on a temp folder: a stale row, a missing row and a gone row, hand columns kept."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import readmetable  # noqa: E402

README = """intro

| file | what it does | run it | in → out |
|---|---|---|---|
| `a.py` | old words | `python3 a.py` | x → y |
| `gone.py` | no longer here | — | — |
| `sub/` | a subfolder | — | — |

outro
"""

EXPECTED = """intro

| file | what it does | run it | in → out |
|---|---|---|---|
| `a.py` | Does A, with a \\| pipe. | `python3 a.py` | x → y |
| `b.py` | Does B. | — | — |
| `sub/` | a subfolder | — | — |

outro
"""


def test_render() -> None:
    """A stale row is rewritten, a missing one added with «—», a gone one dropped, the rest untouched."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "a.py").write_text('"""Does A, with a | pipe.\n\nMore."""\n')
        (root / "b.py").write_text('"""Does B."""\n')
        (root / "README.md").write_text(README)
        assert readmetable.render(root / "README.md") == EXPECTED
        (root / "README.md").write_text(EXPECTED)
        assert readmetable.render(root / "README.md") == EXPECTED  # idempotent


if __name__ == "__main__":
    test_render()
    print("ok")
