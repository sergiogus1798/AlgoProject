#!/usr/bin/env python3
"""The portfolio test root: under ALGO_DATA_ROOT the real ledger, archive and pool writers land in it, never in the real root."""

import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
TMP = Path(tempfile.mkdtemp(prefix="algo-testroot-"))
os.environ["ALGO_DATA_ROOT"] = str(TMP)  # before anything imports core.paths

from live_only import only_here  # noqa: E402

from core import paths  # noqa: E402
from ledger import record, study  # noqa: E402
from portfolio.common.construct import funded, real  # noqa: E402
from portfolio.common.construct.equity import store  # noqa: E402
from portfolio.common.construct.inputs import pool  # noqa: E402
from portfolio.testroot import build, guard, harvest  # noqa: E402
from ui.daemon.strategy import archive_write  # noqa: E402

PROJECT, DATABANK = "Test_NIKKEI225_M30_simpleL_ref", "Stop_p90"
MEMBER_STUDY = study.study_id(
    "NIKKEI225", "M30", "simple:long"
)  # a file the running autopilot also appends to
FAILURES = []


def check(name: str, ok: bool) -> None:
    """Print one line per case; remember the failures."""
    print(f"{'OK   ' if ok else 'FALLO'}  {name}")
    if not ok:
        FAILURES.append(name)


def redirected() -> None:
    """Every path a portfolio run writes to is under the test root, cached-at-import ones included."""
    check("core.paths.DATA is the test root", paths.DATA == TMP)
    for name, where in (
        ("pool.ROOT", pool.ROOT),
        ("store.ROOT", store.ROOT),
        ("funded.RUNS", funded.RUNS),
        ("real.RUNS", real.RUNS),
        ("ledger file", study.path("X")),
        ("archive", paths.archive_dir()),
    ):
        check(f"{name} is under the test root", TMP in where.parents)
    said = subprocess.run(
        [sys.executable, "-c", "import core.paths"],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    check(
        "a process under the test root says RAÍZ DE PRUEBA",
        "RAÍZ DE PRUEBA" in said.stderr,
    )
    quiet = subprocess.run(
        [sys.executable, "-c", "import core.paths"],
        cwd=REPO,
        capture_output=True,
        text=True,
        env={k: v for k, v in os.environ.items() if k != build.ENV},
    )
    check("a process on the real root says nothing", quiet.stderr == "")


def _names(folder: Path) -> set[str]:
    """What a real folder holds; none when the machine never made it (a clean clone)."""
    return set(os.listdir(folder)) if folder.is_dir() else set()


@only_here(
    build.REAL / "harvest" / PROJECT / DATABANK,
    "re-escribe la cosecha real del proyecto de referencia Test_NIKKEI225 (sus .sqx de las versiones con stop) "
    "bajo la raíz de prueba, y sólo esta máquina la tiene",
)
def writers() -> None:
    """The real ledger, harvest, archive and pool writers, run once each, leave the real root alone."""
    token = uuid.uuid4().hex
    row = {
        "step": 27,
        "launched_by": "test",
        "symbol": "NIKKEI225",
        "timeframe": "M30",
        "segment": "build",
        "n_in": 1,
        "n_out": 1,
        "criterion": "testroot",
        "note": token,
    }
    real_archive = _names(build.REAL / "archive")
    real_pools = _names(build.REAL / "portfolio" / "pools")
    with guard.untouched(build.REAL / "ledger", "PORTFOLIO_*"):
        record.log("PORTFOLIO_testroot_construct", row)
        record.log(MEMBER_STUDY, row)
        member = harvest.harvest(PROJECT, DATABANK)[0]
        frozen = archive_write.archive(
            PROJECT,
            DATABANK,
            member["identity"],
            "24",
            family="simple:long",
            sqx=Path(member["sqx"]),
        )
        declared = pool.declare(
            "t", [{"identity": member["identity"], "version": frozen.name}], "test"
        )
    check(
        "the ledger rows are in the test root",
        all(
            token in (TMP / "ledger" / f"{s}.jsonl").read_text()
            for s in ("PORTFOLIO_testroot_construct", MEMBER_STUDY)
        ),
    )
    real_member = build.REAL / "ledger" / f"{MEMBER_STUDY}.jsonl"
    check(
        "the member's REAL ledger study did not get the row",
        not real_member.exists() or token not in real_member.read_text(),
    )
    check(
        "the archive version is in the test root",
        TMP in frozen.parents and (frozen / "harvest" / "equity.parquet").is_file(),
    )
    check(
        "the real archive holds the same identities as before",
        _names(build.REAL / "archive") == real_archive,
    )
    check("the pool is in the test root", TMP in declared.parents)
    check(
        "the real pools are the same as before",
        _names(build.REAL / "portfolio" / "pools") == real_pools,
    )
    try:
        pool.declare("t", [], "test")
        check("a second declaration is refused", False)
    except FileExistsError:
        check("a second declaration is refused", True)


def guards() -> None:
    """`untouched` sees a write; `readonly` stops one and puts the modes back. On a temp folder only."""
    folder = TMP / "guarded"
    (folder / "sub").mkdir(parents=True)
    (folder / "sub" / "PORTFOLIO_a.jsonl").write_text("x")
    try:
        with guard.untouched(folder, "PORTFOLIO_*"):
            (folder / "PORTFOLIO_b.jsonl").write_text("y")
        check("untouched raises on a new matching file", False)
    except RuntimeError:
        check("untouched raises on a new matching file", True)
    with guard.untouched(folder, "PORTFOLIO_*"):
        (folder / "other.jsonl").write_text("z")
    check("untouched ignores a file outside the pattern", True)
    before = (folder / "sub").stat().st_mode
    with guard.readonly(folder):
        try:
            (folder / "sub" / "new").write_text("no")
            check("readonly refuses a write", False)
        except PermissionError:
            check("readonly refuses a write", True)
    (folder / "sub" / "new").write_text("yes")
    check("readonly restores the modes", (folder / "sub").stat().st_mode == before)


def disposable() -> None:
    """`build --root`: a second root with its own empty ledger; the real root is refused."""
    other = TMP / "desechable"
    build.main(["--root", str(other)])
    check(
        "--root builds the writable folders, the ledger empty",
        all((other / name).is_dir() for name in build.WRITABLE)
        and not os.listdir(other / "ledger"),
    )
    check(
        "--root links what a run only reads",
        all((other / name).is_symlink() for name in build.LINKS),
    )
    try:
        build.main(["--root", str(build.REAL)])
        check("--root refuses the real root", False)
    except SystemExit:
        check("--root refuses the real root", True)


def main() -> None:
    """Run every case in a throwaway test root, print a line each, exit non-zero on any failure."""
    build.build(TMP)
    try:
        redirected()
        writers()
        guards()
        disposable()
    finally:
        subprocess.run(
            ["chmod", "-R", "u+w", str(TMP)], check=True
        )  # an archived version is sealed
        shutil.rmtree(TMP)
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()
