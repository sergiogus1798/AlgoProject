#!/usr/bin/env python3
"""The owner's view of the literature: what was searched, rejected and accepted, and the queue."""

import argparse
from collections import Counter

import pandas as pd

from core.researchpaths import research_literature_dir, research_profiles_dir
from studies.research.literature import amend, schema, selection, store, waiting


def scouted() -> list[dict]:
    """The scout's own entries: the ones that carry the paper they came from."""
    return [e for e in store.entries() if "paper" in e]


def queue() -> list[dict]:
    """The queue table against the profile's map on disk."""
    measures = pd.read_csv(research_profiles_dir() / "measures.csv", low_memory=False)
    return waiting.table(scouted(), measures, store.config()["classes"])


def print_queue() -> None:
    """Every scout entry with its state and, once measured, its reading on `build`."""
    rows = queue()
    print(f"{len(rows)} entradas del scout: "
          + ", ".join(f"{n} «{k}»" for k, n in Counter(r["state"] for r in rows).items()))
    for r in rows:
        print(f"\n{r['id']} · {r['family']} · «{r['state']}»"
              + (f" · medidas {', '.join(r['measures'])}" if r["measures"] else ""))
        if r["reading"] != "—":
            print(f"  {r['reading']}")
            print("  al tablero (pasan los cuatro filtros): "
                  + (", ".join(" ".join(c) for c in r["passing"]) or "ninguna celda"))


def print_rejections() -> None:
    """Every paper turned away, with the filter, the reason and the sentence that shows it."""
    for p in store.papers().values():
        if p["status"] in ("rejected", "duplicate"):
            print(f"\n{p['key']} · {p['year']} · {p['title']}\n  {p['status']}"
                  + (f" · filtro `{p['filter']}`" if p["filter"] else "") + f" · {p['reason']}"
                  + (f"\n  «{p['quote']}» ({p['where']})" if p["quote"] else ""))


def register() -> str:
    """Every paper ever seen, newest first, and what came of it — the owner's `REGISTRO.md`.

    The search drops any paper listed here (`dedupe.same_paper`), so none is read twice.
    """
    read = {"full text": "completo", "abstract only": "sólo resumen", "": "sólo resumen"}
    lines = ["# Registro de papers — qué se ha leído y qué salió de cada uno", "",
             "Lo escribe `python3 -m studies.research.literature.report --register`; la pasada "
             "diaria lo rehace. Un paper que está aquí no se vuelve a buscar ni a leer.", "",
             "| visto | paper | año | leído | qué salió |", "|---|---|---|---|---|"]
    for p in sorted(store.papers().values(), key=lambda p: p["run"], reverse=True):
        if p["status"] == "accepted":
            came = "**útil**: " + ", ".join(f"`{e}`" for e in p["entries"])
        elif p["status"] == "rejected":
            came = f"nada — `{p['filter']}`: {p['reason']}"
        elif p["status"] == "failed":
            came = f"nada — no se pudo extraer: {p['reason']}"
        elif p["status"] == "duplicate":
            came = f"repetido — {p['reason']}"
        else:
            came = "en la bandeja, sin decidir"
        day = f"{p['found'][:4]}-{p['found'][4:6]}-{p['found'][6:]}"
        title = p["title"].replace("|", "/")
        seen = "todavía no" if p["status"] == "inbox" else read[p["read"]]
        lines.append(f"| {day} | [{title}]({p['url']}) | {p['year']} | {seen} | "
                     f"{came.replace('|', '/')} |")
    return "\n".join(lines) + "\n"


def print_for(symbol: str, family: str) -> None:
    """The entries that speak of one asset — the ideaExpert's `libros` quarry — with their state."""
    classes = store.config()["classes"]
    state = {r["id"]: r for r in queue()}
    for e in store.entries():
        if symbol not in selection.symbols(e, classes) or family not in ("", e["family"]):
            continue
        row = state.get(e["id"])
        print(f"\n{e['id']} · {e['family']} · {e['direction']}\n  regla: {e['translation']['entry']}"
              f"\n  fuente: {e['source']}\n  verificado: {e['verified']} · muestra: {e['sample']} · "
              f"solapa build: {e['overlaps_is']}"
              f" · oos1: {e.get('overlaps_oos1', '-')}"
              f" · oos2: {e.get('overlaps_oos2', '-')}\n  fuera de muestra según la fuente: {e['decay']}"
              + (f"\n  variantes que los autores dicen haber probado: "
                 f"{e['selection']['variants_tried']}" if "selection" in e else "")
              + (f"\n  estado: «{row['state']}» {row['reading']}" if row else ""))


def print_status() -> None:
    """The register in one screen: papers by status, rejections by filter, the runs' cost."""
    held = store.papers().values()
    print(f"{len(held)} papers vistos: "
          + ", ".join(f"{n} {k}" for k, n in Counter(p["status"] for p in held).items()))
    for name, n in Counter(p["filter"] for p in held if p["status"] == "rejected").items():
        print(f"  {n:3d} rechazados por `{name}` — {schema.FILTERS[name]}")
    for r in store.runs():
        print(f"run {r['run']} ({r['model']}): {r['papers']} papers, {r['entries']} entradas, "
              f"{r['tokens']:,} tokens · por paper {r['tokens_per_paper']:,} · por entrada "
              f"{r['tokens_per_entry']}")
    open_ = [e for e in scouted() if e.get("question") and not e["question"]["answer"]]
    for e in open_:
        print(f"\nPREGUNTA {e['id']}: {e['question']['text']}")
        for n, text in enumerate(e["question"]["readings"], 1):
            print(f"  {n}. {text}")
    print()
    print_queue()


def main() -> None:
    """Print the view asked for; with no flag, the whole status."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--queue", action="store_true", help="only the entries and their state")
    ap.add_argument("--rejections", action="store_true", help="every rejection with its reason")
    ap.add_argument("--register", action="store_true",
                    help="rewrite REGISTRO.md: every paper seen and what came of it")
    ap.add_argument("--for", dest="symbol", default="", help="the entries that apply to an asset")
    ap.add_argument("--family", default="", help="with --for: only this board family")
    ap.add_argument("--answer", nargs=2, metavar=("ID", "N"),
                    help="the owner's choice among the readings of an entry's question")
    a = ap.parse_args()
    if a.answer:
        return print(f"{a.answer[0]}: «{amend.answer(a.answer[0], int(a.answer[1]))}»")
    if a.register:
        path = research_literature_dir() / "REGISTRO.md"
        path.write_text(register(), encoding="utf-8")
        return print(f"-> {path}")
    if a.symbol:
        return print_for(a.symbol, a.family)
    if a.rejections:
        return print_rejections()
    if a.queue:
        return print_queue()
    print_status()


if __name__ == "__main__":
    main()
