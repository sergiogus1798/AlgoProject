"""Whether a stored strategy is whole: its file carries its identity and every file its recorded hash."""

import hashlib
import json
import zipfile
from pathlib import Path

from core import sqxfile
from core.paths import store_dir
from core.store.write import MANIFEST, SQX, folder, manifest


def _damaged(path: Path) -> str | None:
    """The first bad member of a zip, None when whole; the file is closed either way."""
    with zipfile.ZipFile(path) as archive:
        return archive.testzip()


def check(identity: str) -> list[str]:
    """Everything wrong with one stored strategy.

    Args:
        identity: The folder's name.

    Returns:
        One Spanish line per problem, [] when it is whole: the manifest names this identity,
        `strategy.sqx` carries it, every file the manifest names is there with its sha256 and
        opens, and no file is there unnamed. A temporary left by a cut write is not a problem:
        it never had the final name.
    """
    here = folder(identity)
    if not (here / MANIFEST).exists():
        return ["sin manifiesto: no está guardada"]
    try:
        doc, bad = manifest(identity), []
    except ValueError as e:
        return [f"el manifiesto no se puede leer: {e}"]
    if doc.get("identity") != identity:
        bad.append("el manifiesto nombra otra identidad")
    if not (here / SQX).exists():
        bad.append("falta strategy.sqx")
    else:
        try:
            if sqxfile.identity(here / SQX) != identity:
                bad.append("strategy.sqx no tiene la identidad de su carpeta")
        except (zipfile.BadZipFile, KeyError, OSError) as e:
            bad.append(f"strategy.sqx no se puede leer: {e}")
    for name, about in doc.get("files", {}).items():
        path = here / name
        if not path.exists():
            bad.append(f"falta {name}")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != about["sha256"]:
            bad.append(f"{name} no tiene la huella del manifiesto")
        elif _damaged(path):
            bad.append(f"{name} está dañado por dentro")
    named = set(doc.get("files", {})) | {SQX, MANIFEST}
    bad += [f"{p.name} no está en el manifiesto" for p in sorted(here.iterdir())
            if p.name not in named and not p.name.endswith(".tmp")]
    return bad


def stored() -> list[str]:
    """Every identity with a folder in the store, whatever its cell."""
    return sorted(json.loads(p.read_text(encoding="utf-8"))["identity"]
                  for p in store_dir().glob("*/*/manifest.json"))
