"""Copy the project's Java snippets into a worker and make SQX compile them."""

import argparse
import shutil
import time
import zipfile
from pathlib import Path

from core import worker
from core.paths import worker_dir
from sqx.snippets import toolproject

SOURCES = Path(__file__).parent
READY = "SQX CLI is now ready"
FAILED = "Compilation FAILED"


def pending(role: str) -> list[str]:
    """The snippets this install does not run yet: not copied, changed since, or not compiled.

    Returns:
        Paths relative to `user/extend/`. SQX compiles on start and loads what the PREVIOUS
        start compiled, and a compile error keeps every old class without a word outside its
        log (🔬 2026-10-12) — so a class in the jar older than its source is not this source.
    """
    top = worker_dir(role)
    jar = top / "internal/libs/Snippets.jar"
    classes = set(zipfile.ZipFile(jar).namelist())
    out = []
    for src in sorted(SOURCES.rglob("*.*")):
        rel = src.relative_to(SOURCES)
        if rel.parts[0] not in ("Snippets", "Code"):
            continue
        there = top / "user/extend" / rel
        same = there.exists() and there.read_bytes() == src.read_bytes()
        built = src.suffix != ".java" or (
            rel.relative_to("Snippets").with_suffix(".class").as_posix() in classes
            and same and jar.stat().st_mtime >= there.stat().st_mtime)
        if not (same and built):
            out.append(rel.as_posix())
    return out


def _started(log: Path, since: int) -> str:
    """What SQX logged since `since`, once its CLI is ready; three minutes at most."""
    for _ in range(90):
        text = log.read_text(encoding="utf-8", errors="replace")[since:]
        if READY in text:
            return text
        time.sleep(2)
    raise SystemExit(f"{log}: SQX no llegó a «{READY}» en 3 min")


def main() -> None:
    """Install the snippets on one stopped worker: copy, one start to compile, stop, verify."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--role", required=True, choices=["conductor", "custodian"])
    ap.add_argument("--check", action="store_true", help="solo decir qué falta; no toca nada")
    a = ap.parse_args()
    todo = pending(a.role)
    if not a.check and not worker.holding(worker_dir(a.role)) and toolproject.ensure(a.role):
        print(f"{a.role}: creado el proyecto {toolproject.NAME}")
    if a.check or not todo:
        print(f"{a.role}: " + (f"faltan {todo}" if todo else "todos los snippets compilados"))
        raise SystemExit(1 if todo else 0)
    top = worker_dir(a.role)
    if worker.holding(top):
        raise SystemExit(f"{a.role} está arrancado: los snippets se instalan con el worker parado")
    for old in (top / "user/extend").rglob("*.*"):          # a snippet the repo dropped stays compiled otherwise
        rel = old.relative_to(top / "user/extend")
        if rel.parts[0] in ("Snippets", "Code") and not (SOURCES / rel).exists():
            old.unlink()
    for rel in todo:
        (top / "user/extend" / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(SOURCES / rel, top / "user/extend" / rel)
    worker.start(a.role)
    try:
        log = max((top / "user/log/StrategyQuant").glob("log_*.log"), key=lambda p: p.stat().st_mtime)
        # the start's own lines: SQX compiles in its first seconds, before the port answers
        text = _started(log, max(0, log.stat().st_size - 200_000))
    finally:
        worker.stop(a.role, export=False)
    last = text[text.rindex("Server started on port"):]
    if FAILED in last:
        raise SystemExit(f"{a.role}: SQX no compiló — ningún snippet se actualizó:\n"
                         + last[last.index(FAILED):][:1500])
    left = pending(a.role)
    if left:
        raise SystemExit(f"{a.role}: siguen sin compilar {left}")
    print(f"{a.role}: {len(todo)} snippet(s) compilados; el siguiente arranque ya los carga")


if __name__ == "__main__":
    main()
