"""Find every report file of one identity across a project's databanks and freeze a copy of it."""

import csv
import json
import shutil
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd

from core.paths import DATA
from core.study import draws


_READ: dict = {}        # (path, kind) -> (mtime, size, value): a save freezes many survivors from the same files
_LOCK = threading.Lock()    # the daemon's threads archive side by side
_ROOM = 1 << 31         # bytes of files held; past it the cache starts again


def _cached(path: Path, kind: str, load: Callable[[Path], Any]) -> Any:
    """`load(path)`, parsed once per file version; callers never change what they get back."""
    st = path.stat()
    key, stamp = (path, kind), (st.st_mtime_ns, st.st_size)
    with _LOCK:
        hit = _READ.get(key)
    if hit is not None and hit[0] == stamp:
        return hit[1]
    value = load(path)
    with _LOCK:
        if sum(v[0][1] for v in _READ.values()) > _ROOM:
            _READ.clear()
        _READ[key] = (stamp, value)
    return value


def release() -> None:
    """Drop what the cache holds: a save or an archive is over, the daemon lives on."""
    with _LOCK:
        _READ.clear()


def _csv_rows(path: Path) -> list[dict]:
    """Every row of a CSV as a dict of strings."""
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _rows(path: Path) -> list[dict]:
    """A CSV as a list of row dicts, every value a string."""
    return _cached(path, "rows", _csv_rows)


def _json(path: Path) -> dict:
    """A JSON file parsed once per file version."""
    return _cached(path, "json", lambda p: json.loads(p.read_text(encoding="utf-8")))


def _names(folder: Path, ids: frozenset[str]) -> tuple[list[str], list[str], str | None]:
    """The names this identity goes by in one study folder, or why the folder cannot say.

    Args:
        folder: reports/<P>/<D>/<day>/<study>/.
        ids: The strategy's identity and any alias SQX gave it (`late.aliases`).

    Returns:
        (names with a per-strategy JSON, every name, reason). Names pair through any CSV
        with `strategy` and `identity` — verdict.csv first, then the rest (curate's
        `before-*.csv`) — and a JSON signed without identity takes the one those rows give
        its name, as the daemon pairs them; a name alone never pairs
        (knowhow/sqx-format/identity-differs-across-databanks.md). `reason` is None unless
        no name matched AND the folder could not have named it: no row per strategy at all,
        or rows that carry no identity.
    """
    table, rows = {}, False
    for path in sorted(folder.glob("*.csv"), key=lambda p: p.name != "verdict.csv"):
        got = _rows(path)
        rows = rows or bool(got and "strategy" in got[0])
        for r in got:
            if "strategy" in r and r.get("identity"):
                table.setdefault(r["strategy"], r["identity"])
    own, signed = [], False
    for path in sorted(folder.glob("estrategias/*.json")):
        got = _json(path)
        name, rows = got.get("strategy") or path.stem, True
        signed = signed or bool(got.get("identity"))
        if (got.get("identity") or table.get(name)) in ids:
            own.append(name)
    names = sorted(set(own) | {n for n, i in table.items() if i in ids})
    reason = None
    if not names and not rows:
        reason = "sin filas por estrategia: solo resultado de población o tablas sin columna strategy"
    elif not names and not (table or signed):
        reason = "sus filas no llevan identidad: emparejar por nombre sería adivinar"
    return own, names, reason


def _table(path: Path, ids: frozenset[str], names: list[str], out: Path) -> None:
    """Freeze one table: only this strategy's rows when it names strategies, whole otherwise.

    Args:
        path: A .csv or .parquet of the study folder.
        ids: The strategy's identities.
        names: Its names in this folder.
        out: The folder to write the copy into.

    Returns:
        Nothing. A parquet that names no strategy is a population aggregate that can weigh
        megabytes and is left out; a CSV that names none (a funnel) is copied whole.
    """
    frame = _cached(path, "table", lambda p: pd.read_parquet(p) if p.suffix == ".parquet" else pd.read_csv(p, dtype=str))
    if frame.index.name == "identity":
        frame = frame[frame.index.isin(ids)]
    elif "identity" in frame.columns and frame["identity"].isin(ids).any():
        frame = frame[frame["identity"].isin(ids)]
    elif "strategy" in frame.columns:
        frame = frame[frame["strategy"].isin(names)]
    elif path.suffix == ".parquet":
        return
    if path.suffix == ".parquet":
        frame.to_parquet(out / path.name)
    else:
        frame.to_csv(out / path.name, index=False)


def _freeze(folder: Path, ids: frozenset[str], own: list[str], names: list[str], out: Path) -> list[str]:
    """Copy what one study folder holds about this strategy.

    Args:
        folder: The study folder.
        ids: The strategy's identities.
        own: Its names with a per-strategy JSON.
        names: Every name it goes by here.
        out: The mirror folder inside the archive.

    Returns:
        The files frozen, relative to `out`. Figures (.html, .md) are left out: the window
        redraws from the numbers.
    """
    out.mkdir(parents=True)
    if own:
        (out / "estrategias").mkdir()
    for name in own:
        shutil.copy2(folder / "estrategias" / f"{name}.json", out / "estrategias" / f"{name}.json")
    for path in sorted(folder.iterdir()):
        if path.suffix in (".csv", ".parquet"):
            _table(path, ids, names, out)
        elif path.suffix == ".json" and (path.stem in (folder.name, "manifest") or
                                         _json(path).get("strategy") in names):
            shutil.copy2(path, out / path.name)
    return sorted(p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file())


def _hash(folder: Path, own: list[str]) -> str | None:
    """The config_hash of the result this folder holds for the strategy, else its population's."""
    for path in [folder / "estrategias" / f"{n}.json" for n in own] + [folder / f"{folder.name}.json"]:
        if path.is_file():
            return _json(path).get("config_hash")
    return None


def _loose(root: Path, ids: frozenset[str], out: Path) -> tuple[list[str], list[dict]]:
    """The CSVs outside any study folder — at the project's or a day's level — cut to this identity.

    Args:
        root: reports/<P>/.
        ids: The strategy's identities.
        out: `<version>/reports/`.

    Returns:
        (files frozen, relative to `out`; skipped entries). A row is kept when any cell is
        the identity, whatever the column is called (`identity_pre_mcr`...). A file with no
        identity column at all is listed as skipped; one that names others but not this
        identity is simply not about it.
    """
    frozen, skipped = [], []
    for path in sorted(root.glob("*.csv")) + sorted(root.glob("*/*/*.csv")):
        rel = path.relative_to(root)
        frame = _cached(path, "table", lambda p: pd.read_csv(p, dtype=str))
        rows = frame[frame.isin(ids).any(axis=1)]
        if len(rows):
            (out / rel).parent.mkdir(parents=True, exist_ok=True)
            rows.to_csv(out / rel, index=False)
            frozen.append(rel.as_posix())
        elif not any("identity" in c for c in frame.columns):
            skipped.append({"path": rel.as_posix(), "reason": "no nombra estrategias por identidad"})
    return frozen, skipped


def freeze(project: str, identity: str, out: Path, also: frozenset[str] = frozenset()) -> tuple[list[dict], list[str], list[dict]]:
    """Every study, every databank and every day that judged this identity, frozen.

    Args:
        project: SQX project name.
        identity: SHA-256 of the strategy's normalised XML.
        out: `<version>/reports/`, mirrored as `<databank>/<day>/<study>/`.
        also: Identities SQX gave the same strategy later; their rows are its rows.

    Returns:
        (entries, loose, skipped). One entry per study folder that names the identity:
        databank, day, study, `named` (the name with a per-strategy JSON, or None), `names`,
        `config_hash` and `files`. `loose`: the CSVs outside a study folder whose rows were
        kept. `skipped`: `{path, reason}` for everything that could not be paired — nothing
        is left out silently.
    """
    root, ids = DATA / "reports" / project, frozenset({identity, *also})
    entries, skipped = [], []
    for folder in sorted(root.glob("*/*/*")):
        databank, day = folder.parts[-3:-1]
        if not folder.is_dir() or databank.startswith("_"):
            continue
        draws.consolidate(folder)       # a `--strategy` run leaves its rows apart; a copy by file name would miss them
        own, names, reason = _names(folder, ids)
        if reason:
            skipped.append({"path": folder.relative_to(root).as_posix(), "reason": reason})
        if not names:
            continue
        files = _freeze(folder, ids, own, names, out / databank / day / folder.name)
        entries.append({"databank": databank, "day": day, "study": folder.name,
                        "named": own[0] if own else None, "names": names,
                        "config_hash": _hash(folder, own), "files": files})
    loose, lost = _loose(root, ids, out)
    return entries, loose, skipped + lost
