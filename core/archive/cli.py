"""The archive's command: list what is archived, archive one strategy, show one."""

import argparse
import json
from pathlib import Path

from core.archive import read


def _show(identity: str, version: str | None) -> None:
    """Print one version's provenance and what it holds, in Spanish."""
    got = read.load(identity, version)
    doc = got["manifest"]
    tear = got["tearsheet"]
    print(f"versión {got['version']} · {doc['project']}/{doc['databank']} · paso {doc['step']}"
          f" · archivada {doc['archived_at']} · código {doc['code_version']}")
    print(f"  estrategia: {tear['strategy'] if isinstance(tear, dict) else tear}")
    print(f"  .sqx: {doc['sqx']['from']}{' (a mano)' if doc['sqx']['by_hand'] else ''}")
    print(f"  activo: {doc['asset']['symbol']} sha256 {doc['asset']['sha256'][:12]}")
    led = doc["ledger"]
    print(f"  ledger {led['study']}: {led['searches']} búsquedas, "
          f"N={led['trials']['n']} candidatos puntuados")
    for e in doc["studies"]:
        print(f"  {e['databank']:<26} {e['day']} {e['study']:<12} hash {str(e['config_hash'])[:8]}"
              f"  {len(e['files'])} ficheros")
    for rel in doc.get("loose", []):          # versions archived before 2026-09-27T21 lack both lists
        print(f"  suelto: {rel}")
    for skip in doc.get("skipped", []):
        print(f"  no archivado: {skip['path']} — {skip['reason']}")
    if doc["harvest"]:
        print(f"  cosecha: {doc['harvest']['rows']}")
    print(f"  gate: {'sí' if got['gate'] else 'no'} · metadatos: {'sí' if got['meta'] else 'no'}")


def main() -> None:
    """`list`, `archive` or `show`, as argparse reads them."""
    p = argparse.ArgumentParser(prog="python3 -m core.archive")
    sub = p.add_subparsers(dest="verb", required=True)
    sub.add_parser("list")
    a = sub.add_parser("archive")
    for flag in ("--project", "--databank", "--identity", "--step", "--family"):
        a.add_argument(flag, required=True)
    a.add_argument("--note", default="")
    a.add_argument("--sqx", type=Path)
    s = sub.add_parser("show")
    s.add_argument("identity")
    s.add_argument("--version")
    args = p.parse_args()
    if args.verb == "list":
        for row in read.listing():
            print(json.dumps(row, ensure_ascii=False))
    elif args.verb == "archive":
        from core.archive import write
        print(write.archive(args.project, args.databank, args.identity, args.step, args.note,
                            family=args.family, sqx=args.sqx))
    else:
        _show(args.identity, args.version)
