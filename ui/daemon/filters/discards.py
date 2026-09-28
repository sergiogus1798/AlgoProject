"""The discard log of one databank: what a filter or a manual deletion set aside, replayed from disk."""

import json
from datetime import datetime, timezone
from pathlib import Path

from core.paths import DATA


def root() -> Path:
    """`AlgoData/filters/`, the one root of every filter file. Derived here and not in
    `core/paths.py`, which cannot take another function under the 250-line limit."""
    return DATA / "filters"


def folder(project: str, databank: str) -> Path:
    """Where one databank's filters live: `<root>/<P>/<D>/`, the databank as its report
    folder spells it (underscores)."""
    return root() / project / databank.replace(" ", "_")


def log_file(project: str, databank: str) -> Path:
    """The databank's `discards.jsonl`, whether or not it exists yet."""
    return folder(project, databank) / "discards.jsonl"


def events(project: str, databank: str) -> list[dict]:
    """Every line of the log, oldest first; none when nothing was ever filtered."""
    path = log_file(project, databank)
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def live(project: str, databank: str) -> list[dict]:
    """The discard lines since the last «quitar filtros»: what the view hides now.

    Returns:
        One dict per identity set aside: `identity`, `name`, `origin` (filter | manual),
        `expression`, `ts`, `n_in` (how many were visible when it was applied).
    """
    return [e for e in since_clear(project, databank) if "identity" in e]


def since_clear(project: str, databank: str) -> list[dict]:
    """Every line after the last «quitar filtros»: applied headers and discards."""
    lines = events(project, databank)
    cut = max((i for i, e in enumerate(lines) if e.get("clear")), default=-1)
    return lines[cut + 1:]


def hidden(project: str, databank: str) -> set[str]:
    """The identities set aside now."""
    return {e["identity"] for e in live(project, databank)}


def stamp() -> str:
    """Now, in UTC, to the second."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def append(project: str, databank: str, lines: list[dict]) -> None:
    """Add lines to the log, in append mode: nothing here rewrites a line.

    Args:
        project: Project name.
        databank: Either spelling.
        lines: One dict per line.
    """
    path = log_file(project, databank)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for line in lines:
            handle.write(json.dumps(line, ensure_ascii=False) + "\n")


def record(project: str, databank: str, dropped: dict[str, str], origin: str,
           expression: str, n_in: int, blank: int = 0, anonymous: int = 0) -> None:
    """Write one filter's or one manual deletion's discards, after one `applied` line that
    keeps its counts (a filter that set nobody aside is still a step of the funnel).

    Args:
        project: Project name.
        databank: Either spelling.
        dropped: identity → strategy name.
        origin: `filter` or `manual`.
        expression: What was applied, as the ledger's `criterion` says it.
        n_in: How many were visible before.
        blank: How many stayed for lacking a value (a filter's «sin valor»).
        anonymous: Rows of the table without identity, which no filter can hide.
    """
    ts = stamp()
    head = {"applied": True, "origin": origin, "expression": expression, "ts": ts,
            "n_in": n_in, "n_out": n_in - len(dropped), "blank": blank,
            "anonymous": anonymous}
    append(project, databank, [head] + [{"identity": i, "name": n, "origin": origin,
                                "expression": expression, "ts": ts, "n_in": n_in}
                               for i, n in sorted(dropped.items(), key=lambda kv: kv[1])])


def clear(project: str, databank: str) -> int:
    """«Quitar filtros»: a `clear` line; the lines before it stay as history.

    Returns:
        How many identities it brought back.
    """
    back = len(hidden(project, databank))
    append(project, databank, [{"clear": True, "ts": stamp()}])
    return back


def steps(project: str, databank: str) -> list[dict]:
    """The live log as the funnel counts it: one row per filter or deletion, in order.

    Returns:
        `expression`, `origin`, `ts`, `entered`, `died`, `passed`, `blank`, `anonymous`.
    """
    return [{"expression": e["expression"], "origin": e["origin"], "ts": e["ts"],
             "entered": e["n_in"], "passed": e["n_out"], "died": e["n_in"] - e["n_out"],
             "blank": e.get("blank", 0), "anonymous": e.get("anonymous", 0)}
            for e in since_clear(project, databank) if e.get("applied")]


def databanks(project: str) -> list[str]:
    """The databank folders of a project that have a discard log."""
    top = root() / project
    return sorted(p.parent.name for p in top.glob("*/discards.jsonl")) if top.is_dir() else []
