"""Known-answer test for tools/ratchet.py: each counter on a small source snippet."""

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "tools")]
import depmap  # noqa: E402
import ratchet  # noqa: E402

SRC = '''"""m."""
import numpy as np
def f() -> dict: ...
def _g() -> dict: ...
def h() -> dict[str, int]: ...
class C:
    def m(self) -> dict: ...
try: pass
except Exception: pass
try: pass
except: pass
try: pass
except ValueError: pass
r = np.random.default_rng()
s = np.random.default_rng(1)
t = np.random.seed(0)
u = np.random.choice([1])
'''


def test_counters() -> None:
    """Every counter finds exactly what the snippet plants."""
    with tempfile.TemporaryDirectory(dir=ROOT) as d:
        p = Path(d) / "m.py"
        p.write_text(SRC, encoding="utf-8")
        got = ratchet._file_counts(p)
    pkg = Path(d).name  # the temp dir is the fake package
    assert got[f"untyped_dict.{pkg}"] == 2, got
    assert got["broad_except"] == 2, got
    assert got["unseeded_rng"] == 1, got
    assert got["legacy_np_random"] == 2, got


def test_check_flags_a_rise_and_keeps_baseline() -> None:
    """A file adding a bare -> dict raises a problem and leaves ratchet.json untouched."""
    before = ratchet.BASELINE.read_bytes()
    with tempfile.NamedTemporaryFile(
        "w", suffix=".py", dir=ROOT / "tools"
    ) as t:  # package "tools" is in the baseline
        t.write("def f() -> dict: ...\n")
        t.flush()
        problems = ratchet.check(depmap.py_files() + [Path(t.name)])
    assert any("untyped_dict" in x for x in problems), problems
    assert ratchet.BASELINE.read_bytes() == before


def test_pyright_counts_per_included_package() -> None:
    """Errors are counted per package of the include list; warnings and other packages are not."""
    import json
    import types

    diag = lambda pkg, sev: {"file": str(ROOT / pkg / "m.py"), "severity": sev}  # noqa: E731
    out = json.dumps(
        {
            "generalDiagnostics": [
                diag("core", "error"),
                diag("core", "error"),
                diag("core", "warning"),
                diag("ui", "error"),
            ]
        }
    )
    real = ratchet.subprocess.run
    ratchet.subprocess.run = lambda *a, **k: types.SimpleNamespace(
        stdout=out, returncode=1, stderr=""
    )
    try:
        got = ratchet.pyright_counts()
    finally:
        ratchet.subprocess.run = real
    assert got["pyright.core"] == 2 and got["pyright.engines"] == 0, got


if __name__ == "__main__":
    test_pyright_counts_per_included_package()
    test_counters()
    test_check_flags_a_rise_and_keeps_baseline()
    print("ok")
