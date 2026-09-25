"""The assets/ YAML files read and written without losing a comment — the only round-trip here."""

from pathlib import Path

from ruamel.yaml import YAML

_Y = YAML()
_Y.preserve_quotes = True
_Y.width = 4096                              # never re-wrap a long `why`; the files carry them
_Y.indent(mapping=2, sequence=4, offset=2)   # the indentation assets/ already uses
# ruamel writes a bare None as an empty value; these files say `null` and mean «undecided»,
# which is a decision the reader has to see. Verified 2026-09-24: with these three settings
# a load+dump of the four shared files and the nineteen symbol files is byte-identical.
_Y.representer.add_representer(
    type(None), lambda r, d: r.represent_scalar("tag:yaml.org,2002:null", "null"))


def read(path: Path) -> object:
    """One assets/ file with its comments and its order kept.

    Args:
        path: The file.

    Returns:
        A CommentedMap: a dict that also remembers every comment and every line number, so
        writing it back changes only the value that was changed.
    """
    return _Y.load(path.read_text(encoding="utf-8"))


def write(path: Path, data: object) -> None:
    """Write a document read by `read` back over its own file.

    Args:
        path: The file.
        data: The CommentedMap, with whatever was changed in it.
    """
    with path.open("w", encoding="utf-8") as f:
        _Y.dump(data, f)


def hint(lines: list[str], line: int) -> str:
    """The comment a key carries in the file, as the sentence to show beside it.

    Args:
        lines: The file, split into lines.
        line: Zero-based line of the key.

    Returns:
        The contiguous comment block immediately above the key plus its end-of-line
        comment, joined. Empty when the key carries neither. This is where the window's
        explanations come from: the files already say what every field means and in which
        unit, and a second copy of that in the code would drift from them.
    """
    above, i = [], line - 1
    while i >= 0 and lines[i].strip().startswith("#"):
        above.insert(0, lines[i].strip().lstrip("#").strip())
        i -= 1
    _, _, eol = lines[line].partition(" #")
    return " ".join([*above, eol.strip()]).strip()


def leaves(path: Path, data: object = None) -> list[dict]:
    """Every editable value of one file, with where it lives and what the file says it is.

    Args:
        path: The file.
        data: Its parsed content, re-read when not given.

    Returns:
        One entry per editable value, in file order: `path` (the keys and list indices
        leading to it), `label` (the last of them), `value`, `hint` and `kind` — "scalar",
        or "list" for a list of scalars, which is edited whole because its items have no
        keys to address them by.
    """
    doc = data if data is not None else read(path)
    lines = path.read_text(encoding="utf-8").splitlines()
    out: list[dict] = []
    _walk(doc, [], lines, out)
    return out


def _walk(node: object, here: list, lines: list[str], out: list[dict]) -> None:
    """Collect one node's leaves into `out`, depth first and in file order.

    Args:
        node: A mapping, a list or a scalar.
        here: The path taken to reach it.
        lines: The file, for the hints.
        out: The list being filled, in place.
    """
    if isinstance(node, dict):
        for key in node:
            line, before = node.lc.key(key)[0], len(out)
            _walk(node[key], [*here, key], lines, out)
            # One new leaf means the key IS that leaf — a scalar, or a list of scalars,
            # which is one editable value. Several means it was a branch, and a branch's
            # comment introduces its children rather than describing a value.
            if len(out) == before + 1:
                out[-1]["hint"] = hint(lines, line)
    elif isinstance(node, list) and any(isinstance(v, (dict, list)) for v in node):
        for i, item in enumerate(node):
            _walk(item, [*here, i], lines, out)
    else:
        out.append({"path": here, "label": str(here[-1]) if here else "",
                    "value": list(node) if isinstance(node, list) else node,
                    "hint": "", "kind": "list" if isinstance(node, list) else "scalar"})
