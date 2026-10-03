"""Knowhow check: a card's header must not cite a repo path that no longer exists."""

import re
from functools import lru_cache
from pathlib import Path

import knowhowmap

ROOT = knowhowmap.ROOT
TOP = ("ui", "core", "sqx", "studies", "engines", "portfolio", "pipeline", "ledger", "perf", "mt5",
       "tools", "bin", "tests", "assets", "config", "docs", "knowhow")
EXT = (".py", ".sh", ".md", ".yaml", ".yml", ".json", ".toml")
BACKTICKED = re.compile(r"`([^`\n]+)`")
NOT_REPO = {"AlgoData", "scratch", "user", "raw", "harvest", "memory", "manual"}
SKIPPED = {".git", "scratch", "graphify-out", "node_modules", "__pycache__", "audit"}


def tokens(text: str) -> list[str]:
    """Backticked tokens of a text that look like repo paths, cleaned of ``::symbol`` and ``:line``.

    Args:
        text: Markdown.

    Returns:
        Path-like tokens. Placeholders (``<P>``, ``*``, ``{}``, ``$``), absolute and ``~`` paths,
        and tokens with spaces are dropped: they name a kind of path, not a file.
    """
    out = []
    for raw in BACKTICKED.findall(text):
        tok = re.sub(r"(::\S*|:\d[\d,-]*|\(.*)$", "", raw.strip()).rstrip(".,;)")
        if (" " in tok or "/" not in tok or re.search(r"[<>*{}$\[\]|=]", tok) or tok[0] in "/~."
                or "://" in tok):
            continue
        first = tok.split("/")[0]
        if first in TOP and (tok.endswith(EXT + ("/",)) or re.search(r"\.[A-Za-z_]\w*$", tok)):
            out.append(tok)
        elif first not in TOP + tuple(NOT_REPO) and tok.endswith(".py"):
            out.append(tok)
    return out


@lru_cache(maxsize=1)
def _tails() -> frozenset[str]:
    """Every proper path suffix of every repo file, so a path written relative to a folder resolves."""
    out: set[str] = set()
    for f in ROOT.rglob("*"):
        parts = f.relative_to(ROOT).parts
        if SKIPPED & set(parts) or not f.is_file():
            continue
        out.update("/".join(parts[i:]) for i in range(len(parts)))
    return frozenset(out)


def dead(tok: str) -> bool:
    """Whether a path-like token resolves to nothing: from the root if it starts at one, else by suffix."""
    tok = tok.rstrip("/")
    if (ROOT / "knowhow" / f"{tok}.md").exists():  # a card written as domain/slug, e.g. mt5/mt5-under-wine
        return False
    if tok.split("/")[0] in TOP:
        base = re.sub(r"\.[A-Za-z_]\w*$", "", tok)  # path.symbol names a module member, not a file
        return not any((ROOT / t).exists() for t in (tok, base, base + ".py"))
    return tok not in _tails() and not any(t.startswith(tok + "/") for t in _tails())


def header(card: Path) -> str:
    """A card's text above ``## Evidence``, frontmatter included."""
    return card.read_text(encoding="utf-8").split("## Evidence")[0]


def dead_header_paths(files: list[Path]) -> list[str]:
    """Cards whose header (above ## Evidence) cites a repo path that does not exist.

    Args:
        files: Unused; the signature every check in checks.py shares.

    Returns:
        One message per card and dead path. Evidence is exempt: it narrates what a path was.
    """
    return [f"{c.relative_to(ROOT)}: header cites {t}, which does not exist"
            for c in knowhowmap.cards() for t in sorted(set(tokens(header(c)))) if dead(t)]
