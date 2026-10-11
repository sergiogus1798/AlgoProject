"""The store's command: save a project's survivors, verify what is stored, list it, open one."""

import argparse
import shutil
import sys
import zipfile
from pathlib import Path

from core.paths import WORKERS
from core.store import audit, save, verify, write


def resolve(token: str) -> list[str]:
    """The stored identities a word names: the start of an identity, or a strategy's exact name."""
    return [i for i in verify.stored()
            if i.startswith(token) or write.manifest(i).get("origin", {}).get("strategy") == token]


def opened(identity: str, out: Path) -> Path:
    """Lay one stored strategy out as plain folders, for reading or for handing its .sqx on.

    Args:
        identity: A stored strategy; refused when `verify.check` finds anything wrong with it.
        out: Where to write `<strategy name> <identity[:12]>/`.

    Returns:
        That folder: `<strategy name>.sqx`, `manifest.json` and one folder per zip, unpacked.
        The store itself is not touched; the copy is writable and can be thrown away.
    """
    bad = verify.check(identity)
    if bad:
        raise SystemExit(f"{identity[:12]} no está entera: " + "; ".join(bad))
    here, name = write.folder(identity), write.manifest(identity)["origin"]["strategy"]
    there = out / f"{name} {identity[:12]}"
    there.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(here / write.SQX, there / f"{name}.sqx")
    shutil.copyfile(here / write.MANIFEST, there / write.MANIFEST)
    for path in sorted(here.glob("*.zip")):
        with zipfile.ZipFile(path) as z:
            z.extractall(there / path.stem)
    return there


def main() -> None:
    """`save <project>`, `verify [identity...]`, `audit <project>`, `list`, `open <identity or name> --out DIR`."""
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="verb", required=True)
    s = sub.add_parser("save", help="guarda las supervivientes del paso 8 de un proyecto")
    s.add_argument("project")
    s.add_argument("--sqx-dir", action="append", type=Path, default=[],
                   help="carpeta donde buscar los .sqx; sin ella, los databanks del proyecto en los workers")
    v = sub.add_parser("verify", help="comprueba que lo guardado está entero")
    v.add_argument("identity", nargs="*", help="sin ninguna, todas")
    sub.add_parser("list", help="lo guardado, una línea por estrategia")
    o = sub.add_parser("open", help="desempaqueta una estrategia guardada en carpetas normales")
    o.add_argument("which", help="principio de la huella, o el nombre exacto de la estrategia")
    o.add_argument("--out", type=Path, required=True, help="carpeta de destino (fuera del repo)")
    au = sub.add_parser("audit", help="lo que un proyecto dejó en disco y no está en ningún zip")
    au.add_argument("project")
    a = ap.parse_args()

    if a.verb == "audit":
        falta, ajeno = audit.missing(a.project)
        for line in ajeno:
            print(f"ajeno  {line}")
        for line in falta:
            print(f"FALTA  {line}")
        print(f"{a.project}: {len(falta)} sin guardar, {len(ajeno)} que no son de ninguna guardada")
        sys.exit(1 if falta else 0)
    if a.verb == "open":
        hits = resolve(a.which)
        if len(hits) != 1:
            print(f"{a.which}: {len(hits)} estrategias guardadas con ese nombre o esa huella"
                  + "".join(f"\n  {i[:12]}  {write.manifest(i).get('cell')}  "
                            f"{write.manifest(i)['origin'].get('project')}" for i in hits))
            sys.exit(1)
        print(opened(hits[0], a.out))
        return

    if a.verb == "save":
        dirs = a.sqx_dir or sorted(d for w in WORKERS.values()
                                   for d in (w["path"] / "user/projects" / a.project / "databanks").glob("*"))
        got = save.project(a.project, dirs)
        print(f"{a.project}: {len(got['saved'])} guardadas, {len(got['no_sqx'])} sin .sqx en "
              f"ningún sitio, {len(got['problems'])} con problemas")
        for name in got["no_sqx"]:
            print(f"  SIN .sqx  {name}")
        for identity, bad in got["problems"].items():
            print(f"  MAL  {identity[:12]}  " + "; ".join(bad))
        sys.exit(1 if got["problems"] or got["no_sqx"] else 0)
    wrong = 0
    # Through `resolve`, like `open`: what `list` prints is `identity[:12]`, and verifying that
    # prefix used to report the strategy as broken — «el manifiesto nombra otra identidad;
    # strategy.sqx no tiene la identidad de su carpeta» — instead of saying it is a prefix
    # (📓 2026-10-11). A word that names nothing stops the command rather than verifying all.
    chosen = []
    for token in getattr(a, "identity", None) or []:
        hit = resolve(token)
        if not hit:
            sys.exit(f"{token}: nada guardado empieza así ni se llama así")
        chosen += hit
    for identity in (chosen or verify.stored()):
        doc, bad = write.manifest(identity), verify.check(identity) if a.verb == "verify" else []
        o, steps = doc.get("origin", {}), doc.get("steps", {})
        last = max(steps, key=float) if steps else "?"
        said = (f"paso {last}: {steps[last]['verdict']} ({steps[last]['outcome']})"
                + (" [smoke]" if steps[last].get("smoke") else "")) if steps else ""
        print(f"{'MAL ' if bad else 'ok  ' if a.verb == 'verify' else ''}{identity[:12]}  "
              f"{doc.get('cell', '?')}  {o.get('project', '?')}  {o.get('strategy', '?')}  "
              f"{len(doc.get('files', {}))} archivos  {said}" + ("  — " + "; ".join(bad) if bad else ""))
        wrong += bool(bad)
    sys.exit(1 if wrong else 0)
