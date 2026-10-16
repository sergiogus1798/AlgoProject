#!/usr/bin/env python3
"""Ratchet: debt counts that may fall but never rise (CODESTYLE.md §12), baseline in ratchet.json."""

import ast
import json
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

import depmap
import layering

BASELINE = Path(__file__).with_name("ratchet.json")
RUFF_CODES = ("B905", "C901", "PLR0913")
MODERN_RNG = {
    "default_rng",
    "Generator",
    "SeedSequence",
    "PCG64",
    "PCG64DXSM",
    "Philox",
    "SFC64",
    "MT19937",
    "BitGenerator",
}


def _package(path: Path) -> str:
    """Top-level package of a file ('root' for a file at the repo root)."""
    parts = path.relative_to(depmap.ROOT).parts
    return parts[0] if len(parts) > 1 else "root"


def _is_np_random(func: ast.expr) -> bool:
    """Whether a call target is `np.random.<x>` or `numpy.random.<x>`."""
    return (
        isinstance(func, ast.Attribute)
        and isinstance(func.value, ast.Attribute)
        and func.value.attr == "random"
        and isinstance(func.value.value, ast.Name)
        and func.value.value.id in ("np", "numpy")
    )


def _file_counts(path: Path) -> Counter[str]:
    """The four ast counters of one file."""
    pkg, out = _package(path), Counter()
    for node in ast.walk(depmap.tree(path)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if (
                not node.name.startswith("_")
                and isinstance(node.returns, ast.Name)
                and node.returns.id == "dict"
            ):
                out[f"untyped_dict.{pkg}"] += 1
        elif isinstance(node, ast.ExceptHandler):
            t = node.type
            caught = (
                t.elts if isinstance(t, ast.Tuple) else [t]
            )  # (Exception, X) is broad too
            if t is None or any(
                isinstance(e, ast.Name) and e.id in ("Exception", "BaseException")
                for e in caught
            ):
                out["broad_except"] += 1
        elif (
            isinstance(node, ast.Attribute)
            and node.attr == "replace"
            and isinstance(node.value, ast.Name)
            and node.value.id == "os"
            and path.name != "fsio.py"
        ):  # a hand-rolled atomic write: core.fsio.atomic_write is the one writer
            out["os_replace"] += 1
        elif isinstance(node, ast.Call):
            f = node.func
            name = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")
            if name == "default_rng" and not node.args and not node.keywords:
                out["unseeded_rng"] += 1
            if (
                isinstance(f, ast.Attribute)
                and _is_np_random(f)
                and f.attr not in MODERN_RNG
            ):
                out["legacy_np_random"] += 1
    return out


def ruff_counts() -> Counter[str]:
    """Findings per code of RUFF_CODES over the whole project (ruff must be installed)."""
    res = subprocess.run(
        [
            "ruff",
            "check",
            "--select",
            ",".join(RUFF_CODES),
            "--no-cache",
            "--output-format",
            "json",
            str(depmap.ROOT),
        ],
        capture_output=True,
        text=True,
    )
    if (
        res.returncode > 1 or not res.stdout
    ):  # 0 clean, 1 findings; else ruff itself failed
        raise RuntimeError(f"ruff failed, ratchet not checked: {res.stderr[-500:]}")
    return Counter(d["code"] for d in json.loads(res.stdout))


def pyright_counts() -> Counter[str]:
    """Pyright errors per package of pyproject's [tool.pyright] include, from one run (zeros kept)."""
    toml = (depmap.ROOT / "pyproject.toml").read_text(
        encoding="utf-8"
    )  # no tomllib on 3.10
    m = re.search(r"^include = \[(.*?)\]", toml, re.M)
    assert m, "pyproject.toml has no [tool.pyright] include"
    pkgs = re.findall(r'"([^"]+)"', m[1])
    res = subprocess.run(
        ["pyright", "--outputjson"], capture_output=True, text=True, cwd=depmap.ROOT
    )
    if (
        res.returncode > 1 or not res.stdout
    ):  # an empty run would read as 0 and save as a fall
        raise RuntimeError(f"pyright failed, ratchet not checked: {res.stderr[-500:]}")
    out = Counter({f"pyright.{p}": 0 for p in pkgs})
    for d in json.loads(res.stdout).get("generalDiagnostics", []):
        if d["severity"] == "error":
            out[f"pyright.{Path(d['file']).relative_to(depmap.ROOT).parts[0]}"] += 1
    return out


def counts(files: list[Path]) -> dict[str, int]:
    """Every ratcheted count, flat keys, zeros for the ruff codes and layering included."""
    # Every key exists at 0, or a count that first appears would be saved instead of flagged.
    total = Counter(
        {
            c: 0
            for c in (
                *RUFF_CODES,
                "broad_except",
                "unseeded_rng",
                "legacy_np_random",
                "os_replace",
            )
        }
    )
    for (
        f
    ) in files:  # every package keeps its key at 0, or a rise from 0 would go unseen
        total[f"untyped_dict.{_package(f)}"] += 0
        total.update(_file_counts(f))
    total.update(ruff_counts())
    total.update(pyright_counts())
    total["layering_allow"] = len(layering.ALLOW)
    return dict(sorted(total.items()))


def check(files: list[Path]) -> list[str]:
    """Problems for each count above the baseline; a fall (and no rise) rewrites the baseline."""
    for tool in (
        "ruff",
        "pyright",
    ):  # a missing tool would read 0 and be saved as a fall
        if not shutil.which(tool):
            return [
                f"{tool} not found: ratchet not checked (pip install --user -r requirements.txt)"
            ]
    now = counts(files)
    old = json.loads(BASELINE.read_text(encoding="utf-8")) if BASELINE.exists() else {}
    rose = [
        f"{k}: {old.get(k, 0)} -> {v} (ratchet: may not rise; see CODESTYLE.md §12)"
        for k, v in now.items()
        if v > old.get(k, 0)
    ]
    if not rose and (set(now) != set(old) or any(now[k] < old.get(k, 0) for k in now)):
        BASELINE.write_text(
            json.dumps(now, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    return rose


def main() -> None:
    """Print current counts against the baseline."""
    now = counts(depmap.py_files())
    old = json.loads(BASELINE.read_text(encoding="utf-8")) if BASELINE.exists() else {}
    for k, v in now.items():
        print(f"{k:28} {v:6}  (baseline {old.get(k, '-')})")
    print(
        f"{'total untyped_dict':28} {sum(v for k, v in now.items() if k.startswith('untyped_dict.')):6}"
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
