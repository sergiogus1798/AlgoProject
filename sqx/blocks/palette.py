#!/usr/bin/env python3
"""The palette library: named block selections, each one a family plus what it changes."""

import argparse
import json
import re
from datetime import date
from pathlib import Path

import yaml

from core.paths import PALETTES, TAXONOMY
from sqx.blocks.taxonomy import ARCHETYPES, flat, read

# What a block with no label does. `neutral` lets it through at weight 1, so a palette on
# an unlabelled taxonomy is a no-op and narrows as the labels arrive; `off` admits only
# what the palette itself names, which is how a hand-curated shortlist is expressed.
UNLABELLED = ("neutral", "off")

# How many condition blocks a build must be able to draw from. The owner's figure,
# 2026-09-24: below 90 the builder has nothing to combine and the search chokes; above 170
# the overfitting this whole mechanism exists to narrow comes back.
CONDITIONS = (90, 170)

FAMILY_ES = {"breakout": "Ruptura", "mean_reversion": "Reversión a la media",
             "trend": "Tendencia"}
SLUG = re.compile(r"^[a-z0-9_]+$")
FIELDS = ("name", "label", "family", "origin", "based_on", "created", "note",
          "unlabelled", "overrides")

HEADER = """\
# Paleta «{label}» — familia {family}.
#
# Una paleta dice qué puede sortear el builder. Los pesos de partida salen de
# `../taxonomy.yaml`, columna `{family_key}`; aquí vive solo lo que esta paleta decide:
#   unlabelled  qué se hace con un bloque sin etiquetar — neutral (entra a peso 1) u off
#   overrides   un peso puesto a mano que gana sobre la taxonomía. 0 apaga el bloque
#
# Con `unlabelled: off` y una lista de `overrides`, la paleta ES esa lista: nada más entra.
# Es la forma de tener una paleta curada sin esperar a que la taxonomía esté etiquetada.
#
# ⚠️ Una paleta gobierna los huecos LIBRES de una plantilla. Un hueco atado a un grupo
# sortea ese grupo y la ignora, y un bloque fijo es parte del esqueleto: ninguno de los dos
# se puede estrechar desde aquí. Medido 2026-09-24, `knowhow/authoring/builder-block-switches.md`.
"""


def path(name: str) -> Path:
    """Where one palette lives.

    Args:
        name: Its slug.

    Returns:
        Its YAML under sqx/blocks/palettes/.
    """
    return PALETTES / f"{name}.yaml"


def load(name: str) -> dict:
    """One palette off disk.

    Args:
        name: Its slug.

    Returns:
        Its content. Raises if it is not there — a palette the caller named and that does
        not exist is a mistake worth seeing, not an empty default to build on silently.
    """
    return yaml.safe_load(path(name).read_text(encoding="utf-8"))


def catalogue() -> list[dict]:
    """Every palette in the library.

    Returns:
        One dict per file, sorted by family and then label. The files are the library:
        there is no index beside them, so a palette cannot go missing from a registry that
        claims it exists.
    """
    return sorted((load(f.stem) for f in PALETTES.glob("*.yaml")),
                  key=lambda p: (p["family"], p["label"]))


def save(palette: dict) -> Path:
    """Write one palette back.

    Args:
        palette: A loaded palette with `unlabelled` or `overrides` possibly changed.

    Returns:
        Where it was written.
    """
    assert palette["unlabelled"] in UNLABELLED, f"unknown policy {palette['unlabelled']}"
    assert palette["family"] in ARCHETYPES, f"unknown family {palette['family']}"
    body = {k: palette[k] for k in FIELDS}
    p = path(palette["name"])
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(HEADER.format(label=palette["label"], family=FAMILY_ES[palette["family"]],
                               family_key=palette["family"]) + "\n"
                 + yaml.safe_dump(body, sort_keys=False, allow_unicode=True,
                                  default_flow_style=False), encoding="utf-8")
    return p


def create(name: str, label: str, family: str, source: str | None = None) -> dict:
    """A new palette, empty or cloned from another.

    Args:
        name: Slug for the new file, lowercase letters, digits and underscores.
        label: What it is called on screen.
        family: Which taxonomy column its weights come from.
        source: Slug of the palette to clone, or None for an empty one.

    Returns:
        The palette as written. A clone copies the policy and the overrides and records
        where it came from, which is what makes a library of variations readable later.
    """
    assert SLUG.match(name), f"'{name}': slug is lowercase letters, digits and underscores"
    assert not path(name).exists(), f"'{name}' already exists"
    from_it = load(source) if source else None
    palette = {"name": name, "label": label, "family": family,
               "origin": "clon" if source else "propia", "based_on": source,
               "created": date.today().isoformat(), "note": "",
               "unlabelled": from_it["unlabelled"] if from_it else "neutral",
               "overrides": dict(from_it["overrides"]) if from_it else {}}
    save(palette)
    return palette


def delete(name: str) -> None:
    """Remove one palette from the library.

    Args:
        name: Its slug.
    """
    path(name).unlink()


def resolve(palette: dict, blocks: dict[str, dict]) -> dict[str, dict]:
    """What the builder would be allowed to draw under this palette.

    Args:
        palette: A loaded palette.
        blocks: flat() of the taxonomy.

    Returns:
        Block key to its resolved switch: `use`, `weight`, and `why` — `override`,
        `taxonomy` or `unlabelled` — so the window can say where a decision came from
        instead of showing a number nobody can trace.
    """
    out = {}
    for key, block in blocks.items():
        if key in palette["overrides"]:
            weight, why = palette["overrides"][key], "override"
        elif palette["family"] in block["archetypes"]:
            weight, why = block["archetypes"][palette["family"]], "taxonomy"
        else:
            weight = 1 if palette["unlabelled"] == "neutral" else 0
            why = "unlabelled"
        out[key] = {"use": weight > 0, "weight": max(weight, 1), "why": why,
                    "roles": block["roles"], "groups": block["groups"]}
    return out


def summary(resolved: dict[str, dict]) -> dict:
    """How wide this palette leaves the search, by role.

    Args:
        resolved: A resolve().

    Returns:
        Per role, how many blocks are on out of how many exist; `conditions_ok`, whether the
        signal count sits inside the owner's CONDITIONS band; how many decisions still come
        from the unlabelled default; and how many switched-off blocks a random group can
        reach anyway. That last number is the honest caveat: those blocks are in a pool, so
        a template binding a hole to it draws them whatever this palette says.
    """
    out = {"unlabelled": sum(1 for r in resolved.values() if r["why"] == "unlabelled"),
           "overridden": sum(1 for r in resolved.values() if r["why"] == "override"),
           "pooled_off": sum(1 for r in resolved.values() if r["groups"] and not r["use"])}
    for role in ("signal", "indicator", "level"):
        of = [r for r in resolved.values() if role in r["roles"]]
        out[role] = {"on": sum(1 for r in of if r["use"]), "of": len(of)}
    out["conditions_ok"] = CONDITIONS[0] <= out["signal"]["on"] <= CONDITIONS[1]
    return out


def everything() -> dict:
    """The whole library resolved against the taxonomy, in one read.

    Returns:
        `blocks`, the flat taxonomy; `palettes`, one entry per palette with its file, its
        resolution and its summary. One call because the window draws the library and one
        palette's blocks side by side, and the taxonomy is 767 rows it should parse once.
    """
    blocks = flat(read(TAXONOMY))
    out = {}
    for p in catalogue():
        r = resolve(p, blocks)
        out[p["name"]] = {"palette": p, "resolved": r, "summary": summary(r)}
    return {"blocks": blocks, "palettes": out}


def main() -> None:
    """List the palette library, or print one palette's switches for a build."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("name", nargs="?", help="a palette slug; omit to list the library")
    ap.add_argument("--json", action="store_true", help="emit the resolution as JSON")
    a = ap.parse_args()

    if not a.name:
        blocks = flat(read(TAXONOMY))
        for p in catalogue():
            s = summary(resolve(p, blocks))
            print(f"{p['name']:24} {FAMILY_ES[p['family']]:22} {p['origin']:8} "
                  f"condiciones {s['signal']['on']:4}  "
                  f"{'ok' if s['conditions_ok'] else '⚠️ FUERA DE ' + str(CONDITIONS[0]) + '-' + str(CONDITIONS[1])}"
                  f"  {p['label']}")
        return

    p = load(a.name)
    r = resolve(p, flat(read(TAXONOMY)))
    if a.json:
        print(json.dumps({"palette": p, "resolved": r}, indent=1))
        return
    s = summary(r)
    print(f"{p['label']}  ({p['name']}, familia {FAMILY_ES[p['family']]}, {p['origin']})")
    band = "dentro" if s["conditions_ok"] else (
        f"FUERA: el dueño pide entre {CONDITIONS[0]} y {CONDITIONS[1]}")
    print(f"  condiciones {s['signal']['on']}/{s['signal']['of']} — {band}")
    print(f"  indicador {s['indicator']['on']}/{s['indicator']['of']} · "
          f"nivel {s['level']['on']}/{s['level']['of']}")
    print(f"  {s['overridden']} forzados a mano · {s['unlabelled']} sin etiquetar · "
          f"{s['pooled_off']} apagados que un grupo alcanza igual")


if __name__ == "__main__":
    main()
