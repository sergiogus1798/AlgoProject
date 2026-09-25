#!/usr/bin/env python3
"""The block taxonomy: every block the builder can sample, grouped and ready to be labelled."""

import argparse
from collections import Counter
from pathlib import Path

import yaml

from core.cfx import task_xml, tasks
from core.datapaths import projects_backup
from core.paths import TAXONOMY
from sqx.inspect.vocabulary import installs, pooled_by, vocabulary

DONOR = projects_backup("XAUUSD_base_2026-09-21") / "project.cfx"

# The three switches a Build task carries over the same vocabulary, one per role the block
# can play. The catalogue says what the install knows; this says what the builder may draw.
ROLES = {"signals": "signal", "indicators": "indicator", "stopLimitBlocks": "level"}

# The owner's three families, 2026-09-24. A block carries one weight per family:
# 0 excludes it, 1 is neutral, 2 and 3 prefer it. An empty map means nobody has labelled it.
ARCHETYPES = ("breakout", "mean_reversion", "trend")

HEADER = f"""\
# Taxonomía de bloques — qué bloque pega con qué tipo de estrategia.
#
# Generado por `python3 -m sqx.blocks.taxonomy`, que RESPETA lo ya etiquetado: vuelve a
# leer la instalación, añade los bloques nuevos, y deja intactos los `archetypes` que ya
# tengan valor. Las etiquetas se ponen a mano (o las pone un agente); el resto es derivado
# y se pisa en cada refresco.
#
# Solo están los bloques que el builder puede sortear de verdad. Los que no aparecen aquí
# —las acciones, las funciones matemáticas, los 158 `talib_*`— existen en el vocabulario y
# son inalcanzables desde la generación: `knowhow/06-locations.md`.
#
# archetypes: un peso por familia. 0 lo excluye, 1 es neutro, 2 y 3 lo prefieren.
#   {", ".join(ARCHETYPES)}
# Vacío = sin etiquetar. Un bloque sin etiquetar no entra en ninguna paleta.
#
# roles   señal (condición de entrada/salida) · indicador (valor a comparar) ·
#         nivel (precio de una orden stop/limit). Un bloque puede jugar dos.
# groups  los grupos aleatorios que lo agrupan. OJO: un hueco atado a un grupo IGNORA la
#         paleta — para esos la palanca es el grupo, no el peso. Medido 2026-09-24.
"""


def builder_roles(cfx: Path) -> dict[str, list[str]]:
    """Which roles each block may play, read off a project's Build task.

    Args:
        cfx: A project.cfx holding a Build task.

    Returns:
        Block key to its roles. The task namespaces the value blocks — `Indicators.ATR`
        and `Stop/Limit Price Ranges.ATR` are the single `ATR` of the catalogue seen in
        two roles — so the prefix is stripped and the roles collected under one key.
    """
    member = next(t["file"] for t in tasks(str(cfx)) if t["type"] == "Build")
    found: dict[str, list[str]] = {}
    for block in task_xml(str(cfx), member).find(".//Blocks/BuildingBlocks"):
        found.setdefault(block.get("key").rsplit(".", 1)[-1], []).append(
            ROLES[block.get("category")])
    return found


def with_newer_own(roles: dict[str, list[str]], vocab: dict) -> list[str]:
    """Add the owner's blocks the donor's list predates, in place.

    Args:
        roles: builder_roles() of the donor, modified.
        vocab: A vocabulary() of the install.

    Returns:
        The keys added. A donor is frozen, so a block authored after it was taken is not
        in its `<BuildingBlocks>` — and SQX builds with it anyway, measured on the Keltner
        blocks of 2026-09-22. Without this the taxonomy silently loses every block
        authored since, which is exactly the set being worked on.
    """
    added = []
    for key, block in vocab["custom"].items():
        if key not in roles:
            roles[key] = ["level" if block["section"] == "Price level" else "signal"]
            added.append(key)
    return sorted(added)


def entry(key: str, vocab: dict, roles: list[str]) -> tuple[str, dict]:
    """One block's row: what it is, where it sits, and an empty label to fill.

    Args:
        key: Block key, native or CBlock_ prefixed.
        vocab: A vocabulary() of the install.
        roles: The roles the builder lets it play.

    Returns:
        Its category, then the derived half of the row plus an empty `archetypes`. `form`
        is the block's written display and `help` is SQX's own sentence about it — together
        they are what settles whether a block tests a transition or a state, which is the
        distinction the whole labelling turns on. `help` is omitted when SQX ships none,
        which is the case for 317 of the 767.
    """
    known = vocab["native"].get(key) or vocab["custom"][key]
    row = {"roles": roles,
           "origin": "native" if key in vocab["native"] else "own",
           "form": " ".join((known["display"] or key).split()),
           "groups": pooled_by(vocab, key),
           "archetypes": {}}
    if known.get("help"):
        row["help"] = " ".join(known["help"].split())
    return known["category"], row


def grouped(vocab: dict, roles: dict[str, list[str]]) -> dict[str, dict]:
    """Every reachable block, nested under its SQX category.

    Args:
        vocab: A vocabulary() of the install.
        roles: builder_roles() of the donor.

    Returns:
        Category name to its blocks, both sorted. A flat map of 767 keys is unreadable and
        a category is the unit somebody labelling actually works in — the sixteen Keltner
        conditions are one decision, not sixteen.
    """
    out: dict[str, dict] = {}
    for key, played in roles.items():
        category, row = entry(key, vocab, played)
        out.setdefault(category, {})[key] = row
    return {cat: dict(sorted(blocks.items())) for cat, blocks in sorted(out.items())}


def merge(fresh: dict[str, dict], old: dict[str, dict]) -> tuple[dict, list[str], list[str]]:
    """Carry the labels already written into a freshly read taxonomy.

    Args:
        fresh: grouped(), every `archetypes` empty.
        old: The file as it stands, or an empty dict the first time.

    Returns:
        The merged taxonomy, the keys that are new, and the labelled keys the install no
        longer holds. The dropped ones are returned rather than kept: an unreachable block
        cannot be in a palette, and git holds the labels if one comes back.
    """
    labelled = {key: block["archetypes"]
                for blocks in old.values() for key, block in blocks.items()
                if block.get("archetypes")}
    here = {key for blocks in fresh.values() for key in blocks}
    for blocks in fresh.values():
        for key, block in blocks.items():
            if key in labelled:
                block["archetypes"] = labelled[key]
    was = {key for blocks in old.values() for key in blocks}
    return fresh, sorted(here - was), sorted(set(labelled) - here)


def read(path: Path) -> dict[str, dict]:
    """The taxonomy as it stands on disk.

    Args:
        path: Where the file lives.

    Returns:
        Its parsed content, or an empty dict the first time it is generated.
    """
    return yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else {}


def flat(taxonomy: dict[str, dict]) -> dict[str, dict]:
    """The taxonomy by block key instead of by category.

    Args:
        taxonomy: As read() returns it, nested under the SQX category.

    Returns:
        Block key to its row, the category folded in. The file is nested because that is
        how it is read by a person; everything that computes with it wants it flat.
    """
    return {key: {**row, "category": category}
            for category, blocks in taxonomy.items() for key, row in blocks.items()}


def write(path: Path, taxonomy: dict[str, dict]) -> int:
    """Put the taxonomy on disk under its header.

    Args:
        path: Where to write.
        taxonomy: The merged taxonomy.

    Returns:
        How many blocks were written.
    """
    body = yaml.safe_dump(taxonomy, sort_keys=False, allow_unicode=True,
                          width=1000, default_flow_style=None)
    path.write_text(HEADER + "\n" + body, encoding="utf-8")
    return sum(len(blocks) for blocks in taxonomy.values())


def counts(taxonomy: dict[str, dict]) -> Counter:
    """How much of the taxonomy is labelled, by role.

    Args:
        taxonomy: The merged taxonomy.

    Returns:
        A count per role plus "labelled" and "total". What is left to label is the number
        that says whether a palette can be built yet.
    """
    c = Counter()
    for blocks in taxonomy.values():
        for block in blocks.values():
            c["total"] += 1
            c.update(block["roles"])
            if block["archetypes"]:
                c["labelled"] += 1
    return c


def main() -> None:
    """Refresh the block taxonomy from an install, keeping every label already written."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--role", default="master", choices=sorted(installs()),
                    help="which install's vocabulary to read; default the master")
    ap.add_argument("--donor", type=Path, default=DONOR,
                    help="the project.cfx whose Build task lists the roles")
    ap.add_argument("--out", type=Path, default=TAXONOMY)
    args = ap.parse_args()

    vocab = vocabulary(installs()[args.role])
    roles = builder_roles(args.donor)
    newer = with_newer_own(roles, vocab)
    taxonomy, added, dropped = merge(grouped(vocab, roles), read(args.out))
    total = write(args.out, taxonomy)
    c = counts(taxonomy)

    print(f"{args.out}: {total} bloques en {len(taxonomy)} categorías, leídos de "
          f"{vocab['install']}")
    print(f"  papeles   señal {c['signal']} · indicador {c['indicator']} · nivel {c['level']}")
    print(f"  etiquetas {c['labelled']} puestas, {total - c['labelled']} por poner")
    if newer:
        print(f"  posteriores al donante ({len(newer)}), añadidos por su tipo: "
              f"{', '.join(newer)}")
    if added:
        print(f"  nuevos ({len(added)}): {', '.join(added[:8])}"
              + (" …" if len(added) > 8 else ""))
    if dropped:
        print(f"  ⚠️ ETIQUETADOS QUE YA NO ESTÁN EN LA INSTALACIÓN ({len(dropped)}), "
              f"sus etiquetas se pierden: {', '.join(dropped)}")


if __name__ == "__main__":
    main()
