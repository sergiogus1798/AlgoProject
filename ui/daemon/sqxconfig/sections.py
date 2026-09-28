"""The SQX settings as the zone draws them: one section per test or topic, every value typed."""

import re

from core.assetwrite import SHARED
from core.assetyaml import hint, leaves, read
from core.paths import ASSETS
from ui.daemon.sqxconfig.options import spec

# The order the zone shows the files in: how a strategy is built and tested first, then the
# cost schemas and the global policy that Activos used to show, then the universe, read only.
FILES = ("build", "classes", "policy", "markets")
# _policy.yaml's per-asset `segments` are Activos' business; only its globals come here.
POLICY_KEYS = ("segments_default", "swap", "mc_retest")
BANNER = re.compile(r"[─━]{2,}\s*(.+?)\s*[─━]{2,}")   # «─── Salidas ────», a section's title
RULE = re.compile(r"[─━]+")


def clean(text: str) -> str:
    """A file's comment as a sentence: the banner rules dropped, the spaces collapsed."""
    return re.sub(r"\s+", " ", RULE.sub(" ", BANNER.sub(r"\1 —", text))).strip()


def header(lines: list[str]) -> list[str]:
    """The comment block a file opens with, without its `#`."""
    out = []
    for line in lines:
        if not line.startswith("#"):
            break
        out.append(line.lstrip("#").strip())
    return out


def field(name: str, leaf: dict) -> dict:
    """One value, ready for the window.

    Args:
        name: The shared file it lives in.
        leaf: What `assetyaml.leaves` reports for it.

    Returns:
        Its path, current value, comment and spec (type, options, locked).
    """
    return {"path": leaf["path"], "key": leaf["label"], "value": leaf["value"],
            "help": clean(leaf["hint"]), **spec(name, leaf["path"], leaf["value"])}


def markets() -> dict:
    """The retest universe, one line per declared market, read only.

    Returns:
        One section. Its values are text because nothing here is written: Activos writes
        this file through `assetwrite.set_market`, which replaces a category whole.
    """
    path = ASSETS / SHARED["markets"]
    doc, lines = read(path), path.read_text(encoding="utf-8").splitlines()
    fields = []
    for symbol, block in doc.items():
        for category, feeds in block["categories"].items():
            value = [f"{f['feed']} (datos desde {f['data_from']})" for f in feeds]
            fields.append({"path": [symbol, "categories", category], "key": f"{symbol} · {category}",
                           "value": value, "help": clean(hint(lines, block["categories"].lc.key(
                               category)[0])), **spec("markets", [], value)})
    return {"file": "markets", "key": "universe", "source": f"assets/{SHARED['markets']}",
            "help": clean(" ".join(header(lines))), "groups": [], "fields": fields}


def groups(doc: object, lines: list[str], top: str, every: list[dict]) -> list[dict]:
    """The comment of every branch inside one section, which `leaves` leaves out.

    Args:
        doc: The parsed file.
        lines: The file, split into lines.
        top: The section's key.
        every: The file's leaves.

    Returns:
        One {path, help} per branch that carries a comment. «Timeframes extra» of CrossTF is
        explained only there: its comment sits above the branch, not above M30 or H1.
    """
    out, seen = [], set()
    for leaf in every:
        path = leaf["path"]
        for k in range(2, len(path)):
            if tuple(path[:k]) in seen or not isinstance(path[k - 1], str):
                continue
            seen.add(tuple(path[:k]))
            node = doc
            for key in path[:k - 1]:
                node = node[key]
            text = clean(hint(lines, node.lc.key(path[k - 1])[0]))
            if path[0] == top and text:
                out.append({"path": path[:k], "help": text})
    return out


def one_file(name: str) -> list[dict]:
    """Every section of one shared file, in file order.

    Args:
        name: "build", "classes" or "policy".

    Returns:
        One section per top-level key, each with the comment above that key and its values.
    """
    path = ASSETS / SHARED[name]
    doc, lines = read(path), path.read_text(encoding="utf-8").splitlines()
    every = leaves(path, doc)
    out = []
    for top in doc:
        if name == "policy" and top not in POLICY_KEYS:
            continue
        out.append({"file": name, "key": top, "source": f"assets/{SHARED[name]}",
                    "help": clean(hint(lines, doc.lc.key(top)[0])),
                    "groups": groups(doc, lines, top, every),
                    "fields": [field(name, leaf) for leaf in every if leaf["path"][0] == top]})
    return out


def state() -> dict:
    """The whole zone in one round trip.

    Returns:
        `sections` in the order of FILES, and the files they come from. A few hundred
        values: paging them would add a mode for nothing on loopback.
    """
    sections = [s for name in FILES[:3] for s in one_file(name)] + [markets()]
    return {"sections": sections,
            "files": {name: f"assets/{SHARED[name]}" for name in FILES}}
