"""THE COMMAND: bring gorilla's survivors here and archive them, in one go (owner, 2026-10-16).

`bin/remote.sh gorilla collect [<PROJECT>] [--dry-run]`. Per project: the store folders, ledger rows,
registry row and reports (`core.store.collect`), then `core.archive archive` for each survivor, its
databank and step read from the reports (`candidates.judged`) and its family from the store cell.
Idempotent: what is already here or archived is said and left alone. Gorilla is only read.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from core.archive.read import versions
from core.paths import DATA, MIRRORS, archive_dir
from core.store import collect
from portfolio.common.construct import candidates


def _archive(project: str, folder: Path, judged: dict[str, dict]) -> str:
    """Archive one landed survivor; returns «archivada» or «ya archivada», raises with the reason otherwise."""
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    ident, origin = manifest["identity"], manifest["origin"]
    have = versions(ident)
    if (
        have
        and (archive_dir() / ident / have[-1] / "harvest" / "trades.parquet").is_file()
    ):
        return "ya archivada"  # a version without its harvest is incomplete: archived again, newest wins
    prefix = f"{origin['symbol']}_{origin['timeframe']}_"
    if not manifest["cell"].startswith(prefix):
        raise RuntimeError(
            f"{folder.name}: la celda «{manifest['cell']}» no empieza por {prefix}; no se sabe la familia"
        )
    best = judged.get(ident)
    if best is None:
        raise RuntimeError(
            f"{folder.name}: ningún informe de {project} juzga la identidad {ident[:12]}; faltan sus reports"
        )
    cmd = [
        sys.executable, "-m", "core.archive", "archive", "--project", project,
        "--databank", best["databank"], "--identity", ident, "--step", best["step"],
        "--family", manifest["cell"][len(prefix):], "--sqx", str(folder / "strategy.sqx"),
    ]  # fmt: skip
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(
            f"{folder.name}: core.archive falló: {r.stderr.strip()[-400:]}"
        )
    return "archivada"


def main(argv: list[str]) -> int:
    """`<server> [<project>] [--dry-run]`; exit 0 when every project is whole, 1 on any failure."""
    args = [a for a in argv if a != "--dry-run"]
    dry = len(args) != len(argv)
    if not args or args[0] not in MIRRORS or len(args) > 2:
        print(
            "uso: bin/remote.sh gorilla collect [<PROYECTO>] [--dry-run]",
            file=sys.stderr,
        )
        return 2
    server, project = args[0], (args[1] if len(args) > 1 else None)
    try:
        with tempfile.TemporaryDirectory(dir=DATA) as scratch:
            plans = collect.fetch_plans(server, project, Path(scratch))
    except (RuntimeError, OSError) as e:
        print(f"{server}: {e}", file=sys.stderr)
        return 1
    if not plans:
        print(
            f"{server}: nada pendiente"
            if project is None
            else f"{server}: ningún superviviente guardado de {project}",
            file=sys.stderr if project else sys.stdout,
        )
        return 1 if project else 0
    failed = done = 0
    for plan, source in plans:
        name = plan["project"]
        try:
            lines = collect.collect(plan, source, dry=dry)
            if dry:
                print(
                    f"{name}:\n  "
                    + "\n  ".join(lines)
                    + "\n  (simulacro: tampoco se archiva)"
                )
                continue
            judged = candidates.judged(name)
            states = [
                _archive(name, collect.landing(f), judged) for f in plan["folders"]
            ]
            new = states.count("archivada")
            print(
                f"{name}: {len(states)} supervivientes, {new} archivadas ahora"
                + ("" if new else " — nada que hacer, ya estaba al día")
            )
            done += new
        except (
            RuntimeError,
            OSError,
            KeyError,
            subprocess.CalledProcessError,
        ) as e:  # report every project, then fail
            failed += 1
            print(f"{name}: FALLÓ — {e}", file=sys.stderr)
    print(f"{len(plans)} proyectos, {done} estrategias archivadas, {failed} fallos")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
