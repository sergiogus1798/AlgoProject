"""«Constructor»: one real-path run — the portfolio chosen in build, every combination scored, its verdict."""

from collections.abc import Mapping
from typing import Any, cast

import pandas as pd

from portfolio.common.construct import oos2 as oos2_mod
from portfolio.common.construct.inputs import pool as pool_mod
from ui.daemon.portfolios import parts, shelf
from ui.text import numbers

METRICS = ("score", "rar", "r_cubed", "gain_to_pain", "p_losing_year", "sharpe")
HEAD = {"score": "puntuación", "rar": "RAR", "r_cubed": "R³", "gain_to_pain": "gain-to-pain",
        "p_losing_year": "P(año perdedor)", "sharpe": "Sharpe diario", "floor_risk": "riesgo mín. %",
        "k": "K"}
STATE = {True: "pass", False: "fail", None: "watch"}
OOS2 = {"not_opened": "No se ha leído", "refused": "Rechazada la lectura", "no_sigma": "No se puede leer",
        "pass": "PASA", "fail": "NO PASA"}
UNJUDGED = ("Esta cartera no está juzgada. «Juzgar: veredicto» la mide en oos1 contra carteras "
            "admisibles al azar del mismo tamaño y, SOLO si lo pasa, lee oos2: una única lectura "
            "por pool, que no se repite.")
MAX_ROWS = 300


def pick(pool: str, run: str, kind: str) -> shelf.RunRow | None:
    """The run asked for when it is of this pool and kind, else the pool's newest of the kind."""
    found = [r for r in shelf.runs() if r["pool"] == pool and r["kind"] == kind]
    return next((r for r in found if r["id"] == run), found[0] if found else None)


def spent(pool: str, members: list[str] | None = None) -> str:
    """One sentence when the pool's oos2 has been read already, "" while it has not.

    With `members` (a launcher's portfolio) it says what THAT press can do: nothing new either
    way, but the portfolio that read it gets its stored reading back, any other is refused.
    """
    row = oos2_mod.spent(pool_mod.read(pool, None))
    if row is None:
        return ""
    said = f"El oos2 del pool «{pool}» YA se leyó el {str(row.get('ts', ''))[:10]}"
    if members is None:
        return f"{said}: otra cartera de este pool ya no puede leerlo."
    if (row.get("thresholds") or {}).get("members") == "+".join(sorted(members)):
        return f"{said}, y lo leyó esta misma cartera: el veredicto repetirá esa lectura guardada, sin abrir nada."
    return (f"{said}: otra cartera de este pool ya no puede leerlo. Este veredicto ya no puede abrirlo: "
            "solo medirá oos1.")


def read(pool: str = "", run: str = "", **_: str) -> dict[str, Any]:
    """The tabs of one real run: Resultado, Combinaciones, Nulo y veredicto."""
    if not pool:
        return parts.empty("No hay ningún pool declarado.", "marca estrategias abajo, en "
                           "«Estrategias», y pulsa «Declarar pool con las marcadas».")
    row = pick(pool, run, "real")
    if row is None:
        return parts.empty(f"El pool «{pool}» no tiene ninguna búsqueda.", "pulsa «Buscar cartera»: "
                           "puntúa en build todas las combinaciones admisibles y elige la mejor.")
    folder, known = shelf.folder("runs", row["id"]), shelf.names()
    m = shelf.load(folder / "manifest.json")
    best, n_pool = m["best"], len(m["identities"])
    chosen = ", ".join(shelf.label(i, known) for i in m["best_members"])
    head = (f"CARTERA ELEGIDA: K = {best['k']} [{chosen}] · puntuación {best['score']:.3f} · deja fuera "
            f"{n_pool - best['k']} de {n_pool} estrategias utilizables.")
    facts = parts.table("Cómo se buscó", ["qué", "valor"], [
        ["combinaciones admisibles puntuadas en build", m["n_scored"]],
        ["rangos tomados entre", m["n_reference"]], ["modo de búsqueda", m["mode"]],
        ["inicio de la ventana desplazado", m["shift"]]],
        "Se elige mirando solo build: ni oos1 ni oos2 se tocan aquí.")
    figures = parts.table("La cartera elegida en build", ["métrica", "valor", "qué es"],
                          [[HEAD[k], best[k], parts.WORDS[k]] for k in METRICS]
                          + [[HEAD["floor_risk"], round(100 * best["floor_risk"], 4), parts.WORDS["floor_risk"]]])
    forced = parts.callout(f"FORZADA A MANO: {m['forced']}", "watch") if m.get("forced") else None
    return {"run": row["id"], "relaxed": parts.relaxed(m.get("relaxed")), "empty": None,
            "judged": (folder / "verdict.json").exists(), "spent": spent(pool),
            "tabs": [parts.tab("Resultado", forced, parts.callout(head), figures, facts),
                     combos(folder, m, known), verdict(folder)]}


def combos(folder: shelf.Path, m: dict[str, Any], known: dict[str, dict]) -> parts.TabBlock:
    """«Combinaciones»: the ranked table of every combination scored."""
    frame = pd.read_parquet(folder / "search.parquet").sort_values("score", ascending=False)
    best = "+".join(sorted(m["best_members"]))
    rows, states = [], []
    for n, r in enumerate(frame.head(MAX_ROWS).itertuples(), 1):
        r = cast(Any, r)   # itertuples rows are namedtuples; the stubs only know a tuple
        ids = r.members.split("+")
        rows.append([n, " + ".join(shelf.short(i) for i in ids), r.k, r.score, r.rar, r.r_cubed,
                     r.gain_to_pain, r.p_losing_year, r.sharpe, round(100 * r.floor_risk, 4)])
        states.append(["pass" if "+".join(sorted(ids)) == best else None] + [None] * 9)
    cols = ["#", "miembros", *(HEAD[k] for k in ("k", *METRICS, "floor_risk"))]
    helps = [None, "Las estrategias de la combinación, por el inicio de su identidad.",
             *(parts.WORDS[k] for k in ("k", *METRICS, "floor_risk"))]
    note = (f"{len(frame)} combinaciones, de mejor a peor puntuación en build"
            + (f"; se listan las {MAX_ROWS} primeras" if len(frame) > MAX_ROWS else "")
            + ". En verde, la elegida. Pasa el ratón por una cabecera para saber qué mide.")
    return parts.tab("Combinaciones", parts.table("Todas las combinaciones puntuadas", cols, rows, note,
                                                  helps, states))


def verdict(folder: shelf.Path) -> parts.TabBlock:
    """«Nulo y veredicto»: the oos1 bar against chance, the oos2 line, the sentence."""
    if not (folder / "verdict.json").exists():
        return parts.tab("Nulo y veredicto", parts.callout(UNJUDGED, "watch"))
    v = shelf.load(folder / "verdict.json")
    one, two = v["oos1"], v["oos2"]
    blocks: list[Mapping[str, Any]] = [parts.callout(parts.headline(v["label"]), STATE[v["pass"]])]
    if one["state"] == "no_discrimina":
        blocks.append(parts.callout(
            f"NO SE PUEDE JUZGAR: solo hay {one['n_space']} combinaciones admisibles de K = {one['k']} "
            f"y el azar saca la elegida en el {one['share_chosen']:.0%} de los sorteos. Un percentil "
            "contra sí misma no dice nada.", "watch"))
    blocks.append(parts.table(f"oos1 ({one['span'][0]} … {one['span'][1]}): la elegida contra el azar",
                              ["qué", "valor", "qué es"], [
        ["puntuación de la elegida", one["value"], parts.WORDS["score"]],
        [f"percentil {one['quantile']:.0f} del azar", one["bar"],
         parts.WORDS["p95"].format(q=one["quantile"], rest=100 - one["quantile"])],
        ["mediana del azar", one["null_median"], "La puntuación de una cartera al azar cualquiera."],
        ["percentil de la elegida (%)", parts.pct(one["percentile"]),
         "Qué parte de las carteras al azar queda por debajo de la elegida."],
        ["carteras al azar medidas", one["n"], "Sorteos de combinaciones admisibles del mismo K."],
        ["combinaciones distintas de ese K", one["n_space"],
         "Cuántas hay en total: con pocas, el azar repite la elegida."]]))
    if "sharpe" in two:
        blocks.append(parts.table("oos2: la única lectura", ["qué", "valor", "qué es"], [
            ["Sharpe diario en oos2", two["sharpe"], parts.WORDS["sharpe"]],
            ["máximo esperable del azar", two["benchmark"],
             f"El mejor Sharpe que saldría por suerte entre {numbers.num(two['n'])} pruebas (todas las del proyecto)."],
            ["exceso", two["excess"], "Sharpe menos ese máximo: pasa si es mayor que 0."]]))
    blocks.append(parts.callout(f"oos2 — {OOS2.get(two['state'], two['state'])}"
                                + (f": {two['reason']}" if two.get("reason") else "."),
                                {"pass": "pass", "fail": "fail"}.get(two["state"], "info")))
    doc = shelf.load(folder / "cartera.json") if (folder / "cartera.json").exists() else {"tabs": []}
    drawn = next((t["blocks"] for t in doc["tabs"] if t["title"] == "Veredicto"), [])
    blocks += [b for b in drawn if b["kind"] == "distribution"]
    blocks.append(parts.callout(v["sentence"].replace("\n", "<br>")))
    return parts.tab("Nulo y veredicto", *blocks)
