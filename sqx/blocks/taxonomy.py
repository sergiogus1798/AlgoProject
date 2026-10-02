#!/usr/bin/env python3
"""The block taxonomy: every block the builder can sample, grouped and ready to be labelled."""

import argparse
from collections import Counter
from pathlib import Path

import yaml

from core.datapaths import projects_backup
from core.paths import TAXONOMY
from sqx.blocks.taxonomy_discover import builder_roles, grouped, with_newer_own
from sqx.inspect.vocabulary import installs, vocabulary

DONOR = projects_backup("XAUUSD_base_2026-09-21") / "project.cfx"

# The owner's seven families (three on 2026-09-24, widened to seven on 2026-10-01: the
# coverage matrix's seven archetypes). A block carries one weight per family: 0 excludes
# it, 1 is neutral, 2 and 3 prefer it. An empty map means nobody has labelled it.
# The first three keep the keys they always had; `momentum`, `volatility`, `pattern` and
# `session` are the same words as the coverage registry's. Order is the file's order.
ARCHETYPES = ("breakout", "mean_reversion", "trend", "momentum", "volatility", "pattern", "session")
WEIGHTS = (0, 1, 2, 3)

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
# son inalcanzables desde la generación: `knowhow/authoring/holes-groups-randomcondition.md`.
#
# archetypes: siete pesos, uno por familia. 0 lo excluye, 1 es neutro, 2 y 3 lo prefieren.
#   {", ".join(ARCHETYPES)}
# Vacío = sin etiquetar. Un bloque sin etiquetar no entra en ninguna paleta.
#
# roles   señal (condición de entrada/salida) · indicador (valor a comparar) ·
#         nivel (precio de una orden stop/limit). Un bloque puede jugar dos.
# groups  los grupos aleatorios que lo agrupan. OJO: un hueco atado a un grupo IGNORA la
#         paleta — para esos la palanca es el grupo, no el peso. Medido 2026-09-24.
"""


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


def family_blocks(family: str, min_weight: int = 2, taxonomy: dict[str, dict] | None = None,
                  role: str | None = None) -> dict[str, int]:
    """The blocks that carry at least a given weight in one family.

    Args:
        family: One of ARCHETYPES.
        min_weight: The lowest weight to return, 0-3. 2 is "fits", 3 is "characteristic".
        taxonomy: As read() returns it; the file on disk when omitted.
        role: Optionally only blocks that play this role (`signal`, `indicator`, `level`).

    Returns:
        Block key to its weight, heaviest first. A block nobody has labelled is absent
        whatever min_weight is: no label is not a weight of 1.
    """
    assert family in ARCHETYPES, f"unknown family {family}"
    rows = flat(taxonomy if taxonomy is not None else read(TAXONOMY))
    hits = {k: r["archetypes"][family] for k, r in rows.items()
            if family in r["archetypes"] and r["archetypes"][family] >= min_weight
            and (role is None or role in r["roles"])}
    return dict(sorted(hits.items(), key=lambda kv: (-kv[1], kv[0])))


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
