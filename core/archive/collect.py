"""Find every report file of one identity across a project's databanks and freeze a copy of it."""

import csv
import json
import shutil
from pathlib import Path

import pandas as pd

from core.paths import DATA


def _rows(path: Path) -> list[dict]:
    """A CSV as a list of row dicts, every value a string."""
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _names(folder: Path, identity: str) -> tuple[list[str], list[str], str | None]:
    """The names this identity goes by in one study folder, or why the folder cannot say.

    Args:
        folder: reports/<P>/<D>/<day>/<study>/.
        identity: SHA-256 of the normalised XML.

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
        got = json.loads(path.read_text(encoding="utf-8"))
        name, rows = got.get("strategy") or path.stem, True
        signed = signed or bool(got.get("identity"))
        if (got.get("identity") or table.get(name)) == identity:
            own.append(name)
    names = sorted(set(own) | {n for n, i in table.items() if i == identity})
    reason = None
    if not names and not rows:
        reason = "sin filas por estrategia: solo resultado de población o tablas sin columna strategy"
    elif not names and not (table or signed):
        reason = "sus filas no llevan identidad: emparejar por nombre sería adivinar"
    return own, names, reason


def _table(path: Path, identity: str, names: list[str], out: Path) -> None:
    """Freeze one table: only this strategy's rows when it names strategies, whole otherwise.

    Args:
        path: A .csv or .parquet of the study folder.
        identity: The strategy's identity.
        names: Its names in this folder.
        out: The folder to write the copy into.

    Returns:
        Nothing. A parquet that names no strategy is a population aggregate that can weigh
        megabytes and is left out; a CSV that names none (a funnel) is copied whole.
    """
    frame = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path, dtype=str)
    if frame.index.name == "identity":
        frame = frame[frame.index == identity]
    elif "identity" in frame.columns and frame["identity"].eq(identity).any():
        frame = frame[frame["identity"] == identity]
    elif "strategy" in frame.columns:
        frame = frame[frame["strategy"].isin(names)]
    elif path.suffix == ".parquet":
        return
    if path.suffix == ".parquet":
        frame.to_parquet(out / path.name)
    else:
        frame.to_csv(out / path.name, index=False)


def _freeze(folder: Path, identity: str, own: list[str], names: list[str], out: Path) -> list[str]:
    """Copy what one study folder holds about this strategy.

    Args:
        folder: The study folder.
        identity: The strategy's identity.
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
            _table(path, identity, names, out)
        elif path.suffix == ".json" and (path.stem in (folder.name, "manifest") or
                                         json.loads(path.read_text(encoding="utf-8"))
                                         .get("strategy") in names):
            shutil.copy2(path, out / path.name)
    return sorted(p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file())


def _hash(folder: Path, own: list[str]) -> str | None:
    """The config_hash of the result this folder holds for the strategy, else its population's."""
    for path in [folder / "estrategias" / f"{n}.json" for n in own] + [folder / f"{folder.name}.json"]:
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8")).get("config_hash")
    return None


def _loose(root: Path, identity: str, out: Path) -> tuple[list[str], list[dict]]:
    """The CSVs outside any study folder — at the project's or a day's level — cut to this identity.

    Args:
        root: reports/<P>/.
        identity: The strategy's identity.
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
        frame = pd.read_csv(path, dtype=str)
        rows = frame[frame.eq(identity).any(axis=1)]
        if len(rows):
            (out / rel).parent.mkdir(parents=True, exist_ok=True)
            rows.to_csv(out / rel, index=False)
            frozen.append(rel.as_posix())
        elif not any("identity" in c for c in frame.columns):
            skipped.append({"path": rel.as_posix(), "reason": "no nombra estrategias por identidad"})
    return frozen, skipped


def freeze(project: str, identity: str, out: Path) -> tuple[list[dict], list[str], list[dict]]:
    """Every study, every databank and every day that judged this identity, frozen.

    Args:
        project: SQX project name.
        identity: SHA-256 of the strategy's normalised XML.
        out: `<version>/reports/`, mirrored as `<databank>/<day>/<study>/`.

    Returns:
        (entries, loose, skipped). One entry per study folder that names the identity:
        databank, day, study, `named` (the name with a per-strategy JSON, or None), `names`,
        `config_hash` and `files`. `loose`: the CSVs outside a study folder whose rows were
        kept. `skipped`: `{path, reason}` for everything that could not be paired — nothing
        is left out silently.
    """
    root = DATA / "reports" / project
    entries, skipped = [], []
    for folder in sorted(root.glob("*/*/*")):
        databank, day = folder.parts[-3:-1]
        if not folder.is_dir() or databank.startswith("_"):
            continue
        own, names, reason = _names(folder, identity)
        if reason:
            skipped.append({"path": folder.relative_to(root).as_posix(), "reason": reason})
        if not names:
            continue
        files = _freeze(folder, identity, own, names, out / databank / day / folder.name)
        entries.append({"databank": databank, "day": day, "study": folder.name,
                        "named": own[0] if own else None, "names": names,
                        "config_hash": _hash(folder, own), "files": files})
    loose, lost = _loose(root, identity, out)
    return entries, loose, skipped + lost


def harvest_rows(folder: Path, identity: str, out: Path) -> dict:
    """The cosecha's three tables cut to this identity, every column kept.

    Args:
        folder: harvest/<P>/<D>/<day>/.
        identity: The strategy's identity.
        out: `<version>/harvest/`.

    Returns:
        Rows kept per table.
    """
    out.mkdir()
    counts = {}
    for name in ("metrics", "equity", "trades"):
        rows = pd.read_parquet(folder / f"{name}.parquet", filters=[("identity", "==", identity)])
        rows.to_parquet(out / f"{name}.parquet")
        counts[name] = len(rows)
    return counts
