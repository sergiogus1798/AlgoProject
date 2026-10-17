"""Bring a retired project back from the strategy store, ready for `bin/workflow.sh run` at step 13."""

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import cast
from xml.etree import ElementTree

from core import proc
from core.paths import ROOT, project_dir, worker_dir
from core.store import cli as store
from core.store import verify, write
from sqx.projects import cfxio, crosstfload, registry, stage
from sqx.projects.databanks import databanks

LATER = ("mcretest", "spp", "wfm")  # the stages a resumed run still has to do
FIRST = 13  # where the rail must say the project is afterwards


def chosen(tokens: list[str], project: str) -> dict[str, str]:
    """The stored strategies the words name, as identity -> name; each word exactly one.

    Raises:
        SystemExit: A word names none or several, a strategy is not whole in the store, it
            came from another project, or two of them share a name (one databank, one name).
    """
    out = {}
    for token in tokens:
        hits = store.resolve(token)
        if len(hits) != 1:
            raise SystemExit(
                f"«{token}» nombra {len(hits)} estrategias del almacén: hace falta una"
            )
        bad, origin = verify.check(hits[0]), write.manifest(hits[0])["origin"]
        if bad:
            raise SystemExit(
                f"{hits[0][:12]} no está entera en el almacén: " + "; ".join(bad)
            )
        if origin["project"] != project:
            raise SystemExit(
                f"{hits[0][:12]} salió de {origin['project']}, no de {project}"
            )
        out[hits[0]] = origin["strategy"]
    if len(set(out.values())) < len(out):
        raise SystemExit(
            "dos de las elegidas llevan el mismo nombre: no caben en un databank"
        )
    return out


def fill(project: str, role: str, files: list[Path]) -> list[str]:
    """Copy the strategies into the output databank of every task the cut run had finished.

    Returns:
        The databanks filled: every task's output but those of LATER and of the WFC, which is
        what the rail reads to call steps 6 to 12 done (`ui.daemon.workflow.derive.sqx`).
    """
    later = {t for s in LATER for t in stage.titles(s)}
    folder = project_dir(project, worker_dir(role))
    parts = cfxio.members(folder / "project.cfx")
    wrote = {
        cast(str, t.get("title")): databanks(
            parts[cast(str, t.get("taskXMLFile"))].decode("utf-8")
        ).get("Output")
        for t in ElementTree.fromstring(parts["config.xml"]).iter("Task")
    }
    banks = sorted(
        {
            bank
            for title, bank in wrote.items()
            if bank and title not in later and not title.startswith("WFC")
        }
    )
    for bank in banks:
        crosstfload.refill(folder / "databanks" / bank, files)
    return banks


def builder_argv(project: str, row: dict, n: int, role: str) -> list[str]:
    """The builder's command for a registry row; `simple:<side>` is a Simple Strategy, not a file."""
    kind = row["template"]
    shape = (
        ["--simple", kind.split(":", 1)[1]]
        if kind.startswith("simple:")
        else ["--template", kind]
    )
    return [
        "sqx.projects.builder",
        project,
        "--purpose",
        f"Reanudado del almacén con {n} estrategias: {row['purpose']}"[:300],
        *shape,
        "--symbol",
        row["symbol"],
        "--role",
        role,
        "--timeframe",
        row["timeframe"],
        "--workflow",
        "--max-strategies",
        "1",
        "--minutes",
        "1",
        *(["--family", row["family"]] if row.get("family") else []),
    ]


def main() -> None:
    """Recreate the project under its own name and load the chosen stored strategies into it."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("project", help="the retired project the strategies came from")
    ap.add_argument(
        "strategies", nargs="+", help="start of an identity, or the exact name"
    )
    ap.add_argument("--role", default="custodian")
    a = ap.parse_args()

    rows = [r for r in registry.rows() if r["name"] == a.project]
    if not rows:
        raise SystemExit(
            f"{a.project} no está en registry.csv: no se sabe de qué plantilla salió"
        )
    if not rows[-1]["retired"]:
        raise SystemExit(
            f"{a.project} figura vivo en {rows[-1]['install']}: usa bin/workflow.sh run"
        )
    row, picked = rows[-1], chosen(a.strategies, a.project)

    def run(*argv: str) -> None:
        """Run one module of this project; stop the resume when it fails."""
        if proc.run(
            [sys.executable, "-m", *argv], cwd=ROOT, check=False, timeout=3600
        ).returncode:
            raise SystemExit(f"{argv[0]} salió con error: no se reanuda nada")

    run("core.assets", row["symbol"])  # hard rule 5
    run(*builder_argv(a.project, row, len(picked), a.role))
    with tempfile.TemporaryDirectory() as tmp:
        files = []
        for identity, name in picked.items():
            files.append(Path(tmp) / f"{name}.sqx")
            files[-1].write_bytes(
                (write.folder(identity) / "strategy.sqx").read_bytes()
            )
        banks = fill(a.project, a.role, files)
    print(f"{a.project}: {len(files)} estrategias en {', '.join(banks)}")
    # Step 12's judge comes first (it cuts the databank step 13 reads): the first thing RUN counts
    said = proc.run(
        [
            sys.executable,
            "-m",
            "pipeline.autopilot.run",
            "--project",
            a.project,
            "--plan",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
        timeout=600,
    ).stdout
    do = [d for d in json.loads(said)["do"] if d["kind"] != "judge"]
    first = do[0]["n"] if do else None
    if str(first) != str(FIRST):
        raise SystemExit(
            f"el raíl dice que {a.project} está en el paso {first}, no en el {FIRST}: "
            "no lo lances; mira bin/workflow.sh plan"
        )
    print(f"listo: bin/workflow.sh run {a.project}")


if __name__ == "__main__":
    main()
