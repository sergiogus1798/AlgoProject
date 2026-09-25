#!/usr/bin/env python3
"""What one SQX install can express: its blocks, its random groups, and what each pools."""

import argparse
import json
from datetime import date
from pathlib import Path
from xml.etree import ElementTree

from core.datapaths import vocabulary_snapshot
from core.paths import MASTER, WORKERS

CONFIG_REL = "internal/web/SQWIZARD/branding/global/config.xml"
CUSTOM_REL = "user/settings/customBlocks.xml"
GROUPS_REL = "user/settings/blockGroups.xml"


def installs() -> dict[str, Path]:
    """Every install on this machine, by the name it is addressed with.

    Returns:
        "master" plus one entry per headless role in machine.yaml.
    """
    return {"master": MASTER, **{role: w["path"] for role, w in WORKERS.items()}}


def native_blocks(install: Path) -> dict[str, dict]:
    """AlgoWizard's built-in vocabulary, from the install's own config.xml.

    Args:
        install: Top-level install folder.

    Returns:
        Block key to its section, category, return type, display form and SQX's own help
        text. The display form carries the block's typed holes (#Period#, #Line#), which is
        what a design has to fill and the reason it is kept verbatim; the help is what
        settles whether a block tests a transition or a state, which its name rarely does.
    """
    root = ElementTree.parse(install / CONFIG_REL).getroot()
    found = {}
    for section in root.find(".//Blocks"):
        for category in section:
            for item in category:
                found[item.get("key")] = {"section": section.tag,
                                          "category": category.get("name"),
                                          "returns": item.get("returnType"),
                                          "display": item.get("display") or item.get("name"),
                                          "help": item.get("help") or ""}
    return found


def custom_blocks(install: Path) -> dict[str, dict]:
    """The owner's own blocks, from customBlocks.xml.

    Args:
        install: Top-level install folder.

    Returns:
        Block key to its category, type and display form. Keys are prefixed CBlock_,
        which is how a group item tells a custom block from a native one.
    """
    root = ElementTree.parse(install / CUSTOM_REL).getroot()
    return {item.get("key"): {"section": item.get("type"),
                              "category": item.get("category"),
                              "returns": item.get("returnType"),
                              "display": item.get("display") or item.get("name"),
                              "help": item.get("help") or ""}
            for item in root}


def groups(install: Path) -> dict[str, dict]:
    """The random groups a template can point a hole at.

    Args:
        install: Top-level install folder.

    Returns:
        Group name to its type (Condition or Value) and the block keys it pools. Value
        groups pool native keys; Condition groups embed whole copies of custom blocks,
        so both kinds are read the same way and told apart by the key prefix.
    """
    root = ElementTree.parse(install / GROUPS_REL).getroot()
    return {g.get("name"): {"type": g.get("type"),
                            "items": [i.get("key") for i in g]}
            for g in root}


def vocabulary(install: Path) -> dict:
    """Everything one install can express, in one structure.

    Args:
        install: Top-level install folder.

    Returns:
        The install name, its native and custom blocks, and its groups. Nothing here
        starts SQX or writes to the install; it is three XML files and nothing else.
    """
    return {"install": install.name,
            "native": native_blocks(install),
            "custom": custom_blocks(install),
            "groups": groups(install)}


def pooled_by(vocab: dict, key: str) -> list[str]:
    """Which groups pool one block.

    Args:
        vocab: A vocabulary().
        key: Block key, native or CBlock_ prefixed.

    Returns:
        Group names. Empty means the block exists but no template can reach it: a
        template references groups, never blocks, so an unpooled block is unusable
        until sqx-random-group puts it in one.
    """
    return sorted(name for name, g in vocab["groups"].items() if key in g["items"])


def find(vocab: dict, term: str) -> list[dict]:
    """Every block whose key or display form mentions a term.

    Args:
        vocab: A vocabulary().
        term: Case-insensitive substring, e.g. "keltner".

    Returns:
        One row per block with its origin, type, display form and the groups pooling it.
    """
    needle = term.lower()
    rows = []
    for origin in ("native", "custom"):
        for key, b in vocab[origin].items():
            if needle in key.lower() or needle in (b["display"] or "").lower():
                rows.append({"key": key, "origin": origin, **b, "pooled_by": pooled_by(vocab, key)})
    return sorted(rows, key=lambda r: r["key"])


def usable_groups(vocab: dict) -> dict[str, list[str]]:
    """Groups split by whether a template can actually sample from them.

    Args:
        vocab: A vocabulary().

    Returns:
        "condition" and "value" hold the groups with at least one item; "empty" holds
        the ones with none. An empty group is the silent failure this tool exists for:
        it is structurally valid, a template pointing a hole at it builds without error,
        and nothing is ever sampled.
    """
    out = {"condition": [], "value": [], "empty": []}
    for name, g in sorted(vocab["groups"].items()):
        if not g["items"]:
            out["empty"].append(name)
        else:
            out[g["type"].lower()].append(name)
    return out


def missing(reference: dict, target: dict) -> dict[str, list[str]]:
    """What the target install lacks against the reference.

    Args:
        reference: Vocabulary of the install a template was authored on.
        target: Vocabulary of the install it would be built on.

    Returns:
        Missing custom block keys and missing group names. A template authored on one
        install and built on another needs both to exist there; when they do not, the
        group goes broken and the template disappears from the builder in silence.
    """
    return {"custom_blocks": sorted(set(reference["custom"]) - set(target["custom"])),
            "groups": sorted(set(reference["groups"]) - set(target["groups"]))}


def report(vocab: dict) -> str:
    """One install's inventory as readable lines.

    Args:
        vocab: A vocabulary().

    Returns:
        The counts, the usable groups by type, and the empty ones called out.
    """
    u = usable_groups(vocab)
    lines = [f"{vocab['install']}: {len(vocab['native'])} native + {len(vocab['custom'])} own "
             f"blocks, {len(vocab['groups'])} groups",
             f"  Condition pools ({len(u['condition'])}): " + ", ".join(u["condition"]),
             f"  Value pools     ({len(u['value'])}): " + ", ".join(u["value"])]
    if u["empty"]:
        lines.append(f"  EMPTY, unusable ({len(u['empty'])}): " + ", ".join(u["empty"]))
    if not u["value"]:
        lines.append("  no Value pool: every stop-entry shape is ungenerable here")
    return "\n".join(lines)


def main() -> None:
    """Search the vocabulary, report it, snapshot it, or diff two installs."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("term", nargs="?", help="substring to look for, e.g. keltner")
    ap.add_argument("--role", default="conductor", choices=sorted(installs()),
                    help="which install to read; default the conductor")
    ap.add_argument("--diff", choices=sorted(installs()),
                    help="report what that install lacks against --role")
    ap.add_argument("--snapshot", action="store_true",
                    help="also write the inventory under the data root")
    args = ap.parse_args()

    vocab = vocabulary(installs()[args.role])

    if args.term:
        rows = find(vocab, args.term)
        if not rows:
            print(f"{args.term}: nothing in {vocab['install']}")
        for r in rows:
            pools = ", ".join(r["pooled_by"]) or "NO GROUP POOLS IT — unusable in a template"
            print(f"{r['key']}  [{r['origin']}/{r['section']}/{r['category']}] -> {r['returns']}\n"
                  f"    {r['display']}\n    pooled by: {pools}")
    elif args.diff:
        other = vocabulary(installs()[args.diff])
        gap = missing(vocab, other)
        print(f"{other['install']} lacks, against {vocab['install']}:")
        print(f"  custom blocks ({len(gap['custom_blocks'])}): "
              + (", ".join(gap["custom_blocks"]) or "none"))
        print(f"  groups ({len(gap['groups'])}): " + (", ".join(gap["groups"]) or "none"))
    else:
        print(report(vocab))

    if args.snapshot:
        out = vocabulary_snapshot(vocab["install"], date.today().isoformat())
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(vocab, indent=1, sort_keys=True), encoding="utf-8")
        print(f"\nsnapshot: {out}")


if __name__ == "__main__":
    main()
