#!/usr/bin/env python3
"""Emit a strategy template: one concrete condition, its periods drawn at random, in a proven skeleton."""

import argparse
import re
import shutil
import uuid
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from core.paths import ROOT, worker_dir

SKELETONS = ROOT / "tools/sqx-lab/plugins/sqx-lab/skills/sqx-strategy-template/engine/skeletons"
INNER = "strategy_Portfolio.xml"
TEMPLATES_REL = "user/settings/StrategyTemplates"
HOLE = re.compile(r'<Item key="RandomCondition".*?</Item>', re.DOTALL)


def skeleton_xml(shape: str) -> str:
    """The inner XML of one proven skeleton.

    Args:
        shape: Skeleton name without the _skeleton.sqx suffix, e.g. "market_long".

    Returns:
        The strategy XML as text. Text and not a tree because the transplant replaces one
        element verbatim, and re-serialising the whole document would reorder attributes
        SQX wrote — a diff against a proven file is the only cheap correctness check here.
    """
    return zipfile.ZipFile(SKELETONS / f"{shape}_skeleton.sqx").read(INNER).decode("utf-8")


def optimizable(param: ElementTree.Element) -> bool:
    """Whether the builder should draw this param at random: a number the owner did not name.

    Args:
        param: One <Param> of the fixed block.

    Returns:
        True for an int or double that is neither the chart, the shift (the owner's default
        is 1, the last closed bar) nor a combo (price source, MA type: a choice, not a knob).
        🔬 2026-09-25: without `generate="random"` the builder leaves the default in every
        strategy — 100 of 100 USDJPY builds carried EMA period 20.
    """
    return (param.get("type") in ("int", "double") and param.get("paramType") != "shift"
            and param.get("controlType") != "combo" and "Shift" not in param.get("key", ""))


def group_xml(name: str, item: str) -> tuple[str, str]:
    """A one-item Condition group holding the owner's condition.

    Args:
        name: The template's name; the group is `<name>Signal`.
        item: The block as block_xml() rendered it.

    Returns:
        The group's id — derived from the name, so a rebuild keeps it — and its XML.
        🔬 2026-09-24/25: SQX refuses `generate="random"` on a FIXED block ("Identification
        not found"), and a frozen block builds every strategy on one period. A random hole
        bound to a group of one draws the params like any group item, and every strategy
        still carries this exact condition.
    """
    gid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"algoproject/template/{name}"))
    return gid, (f'<Group id="{gid}" name="{name}Signal" type="Condition" strategyType="Standard" '
                 f'category="Template" status="0" action="add">{item}</Group>')


def block_xml(blocks: Path, key: str, fixed: dict[str, str] | None = None) -> str:
    """One block, custom or native, rendered as the Item a signal can hold.

    Args:
        blocks: XML file of `<Item>` blocks — authored `CBlock_*` ones, or the install's
            AlgoWizard config.xml (`sqx.inspect.vocabulary.CONFIG_REL`) for a native block.
        key: Which block to take.
        fixed: Param key to value for what the owner named, e.g. {"#Type#": "1"} for an EMA.
            Every other numeric param is drawn at random by the builder (owner, 2026-09-25:
            "valores aleatorios en periodos, siempre, a menos que se indique un valor fijo").

    Returns:
        The Item as text: its store entry with <Contents> dropped and every Param carrying
        its default as a value. The definition stays in customBlocks.xml — a template
        references a custom block, it does not carry it.
    """
    root = ElementTree.parse(blocks).getroot()
    # config.xml also carries preset <Item>s under the same key; the definition is under <Blocks>.
    scope = root.find(".//Blocks") if root.find(".//Blocks") is not None else root
    item = next(i for i in scope.iter("Item") if i.get("key") == key)
    for contents in item.findall("Contents"):
        item.remove(contents)
    # config.xml groups a native block's params under <paramCategory>; a signal holds them flat.
    for category in item.findall("paramCategory"):
        item.remove(category)
        item.extend(category.findall("Param"))
    for param in item.findall("Param"):
        if param.get("key") in (fixed or {}):
            param.set("defaultValue", fixed[param.get("key")])
        elif optimizable(param):
            param.set("generate", "random")
            param.set("randomValue", "default")
        param.text = param.get("defaultValue", "")
    # A native block is not a custom block: its own categoryType is what SQX resolves it by,
    # and mislabelling it as "Custom blocks" sends the builder looking in customBlocks.xml.
    if key.startswith("CBlock_"):
        item.set("categoryType", "Custom blocks")
        item.set("customSnippet", "true")
    else:
        item.set("openingBrackets", "0")
        item.set("closingBrackets", "0")
    return ElementTree.tostring(item, encoding="unicode").strip()


def bind_into_signal(xml: str, gid: str, group: str) -> str:
    """Point the first random hole at the condition's group, and free the second.

    Args:
        xml: A skeleton's strategy XML.
        gid: The condition group's id.
        group: Its XML, embedded as the template's only group.

    Returns:
        The XML. The second hole's #Group# is emptied so it samples the whole Conditions
        vocabulary, which is what the owner asks for when he names no group.
    """
    first, second = HOLE.findall(xml)[:2]
    bound = re.sub(r'(randomGroupType="Conditions")>[^<]*</Param>', rf"\1>{gid}</Param>", first,
                   count=1)
    freed = re.sub(r'(randomGroupType="Conditions")>[^<]*</Param>', r"\1 />", second, count=1)
    xml = xml.replace(first, bound, 1).replace(second, freed, 1)
    return re.sub(r"<RandomGroups>.*?</RandomGroups>", lambda _: f"<RandomGroups>{group}</RandomGroups>",
                  xml, count=1, flags=re.S)


def write_template(xml: str, name: str, out: Path) -> Path:
    """Package the XML as an importable .sqx under a chosen name.

    Args:
        xml: The transplanted strategy XML.
        name: Template name, which SQX shows in the builder.
        out: Destination .sqx path.

    Returns:
        The path written. lastSettings.xml is carried over from the skeleton unchanged;
        it holds the builder's own last-used settings and is not part of the template.
    """
    xml = re.sub(r"<StrategyName>[^<]*</StrategyName>", f"<StrategyName>{name}</StrategyName>", xml)
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(INNER, xml)
        z.writestr("lastSettings.xml", "<Settings />")
    return out


def main() -> None:
    """Build one template from a skeleton plus one authored block, and optionally install it."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("name", help="template name, camelCase")
    ap.add_argument("blocks", type=Path, help="XML holding the block: the authored deps/blocks.xml, "
                                              "or the install's config.xml for a native one")
    ap.add_argument("key", help="key of the block to fix into the signal")
    ap.add_argument("out", type=Path, help="where to write the .sqx")
    ap.add_argument("--shape", default="market_long", help="skeleton to transplant into")
    ap.add_argument("--install", help="also copy it into this role's StrategyTemplates/")
    ap.add_argument("--set", default="authored", help="subfolder used when installing")
    ap.add_argument("--param", action="append", default=[], metavar="KEY=VALUE",
                    help="fix a param the owner named, e.g. '#Type#=1' (repeatable)")
    args = ap.parse_args()

    fixed = dict(p.split("=", 1) for p in args.param)
    gid, group = group_xml(args.name, block_xml(args.blocks, args.key, fixed))
    xml = bind_into_signal(skeleton_xml(args.shape), gid, group)
    ElementTree.fromstring(xml)
    if args.key not in xml or len(HOLE.findall(xml)) != 2:
        raise SystemExit(f"{args.key} did not land, or the holes are not two; the build failed")
    out = write_template(xml, args.name, args.out)
    groups = args.out.parent / "deps" / "groups.xml"
    groups.parent.mkdir(parents=True, exist_ok=True)
    groups.write_text(f"<RandomGroups>{group}</RandomGroups>\n", encoding="utf-8")
    drawn = re.findall(r'key="([^"]+)"[^>]*generate="random"', group)
    print(f"{out}  ({out.stat().st_size} bytes, shape {args.shape}, condition {args.key}, "
          f"drawn at random: {', '.join(drawn) or 'nothing'})")
    print(f"{groups}  — install it on both workers: python3 -m sqx.blocks.install {groups} --role …")

    if args.install:
        dest = worker_dir(args.install) / TEMPLATES_REL / args.set / out.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(out, dest)
        print(f"installed: {dest}")


if __name__ == "__main__":
    main()
