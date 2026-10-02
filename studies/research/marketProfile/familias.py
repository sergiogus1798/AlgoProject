"""`assets/FAMILIAS.md` assembled: the owner's prior leads, what was measured annotates it."""

from pathlib import Path

import pandas as pd
import yaml

from studies.research.marketProfile import bibliography, favourable, favourablemd, priorview
from studies.research.marketProfile.priorview import AGAINST, FOR, NONE, TIMEFRAMES

TEXTS = yaml.safe_load(Path(__file__).with_name("familias_texto.yaml").read_text(encoding="utf-8"))
TARGET = Path(__file__).parents[3] / "assets" / "FAMILIAS.md"
MARK = {FOR: "✔", NONE: "○", AGAINST: "✖"}
PULLBACK = ("Paleta para `pullback`: tendencia_base_v2 (contexto) + reversion_base_v2 (disparo) — "
            "el contexto de tendencia como condición fija y el disparo de reversión en el hueco, "
            "por las dos reglas.")
HEAD = ["| marco | nº | familia | prior | estado | veredicto desnudo (mejor medida) | con salida "
        "razonable (barrido aparte) | cociente de varianzas frente a la familia principal |",
        "|---|---|---|---|---|---|---|---|"]


def describe(name: str, cfg: dict) -> str:
    """A measure of the config in one Spanish phrase: its entry, its filters and its exit."""
    spec = next(s for s in cfg["measures"] if s["name"] == name)
    a, said = spec["args"], TEXTS["conditions"]
    if spec["fn"] == "lookback":
        return f"largo si las últimas {a['L']} velas subieron; se mantiene {a['H']}"
    if spec["fn"] == "breakout":
        return f"ruptura del canal de {a['N']} velas, mantenida {a['H']}"
    if spec["fn"] != "rule":
        return TEXTS["measures"].get(name, name)
    text = "entra: " + " y ".join(said[k] for k in [a["enter"], *a.get("when", [])])
    out = []
    if a.get("leave"):
        out.append("deja de cumplirse: " + said[a["leave"][4:]] if a["leave"].startswith("not:")
                   else said[a["leave"]])
    out += [f"{a['cap']} velas"] if a.get("cap") else []
    out += [f"{a['days']} día(s) de velas"] if a.get("days") else []
    if a.get("trail"):
        out.append(f"trailing de {a['trail']:g} ATR "
                   + ("de D1" if a.get("ruler") == "day" else "de la vela"))
    return text + "; sale: " + " o ".join(out) + " (escrita para largos; en corto, su espejo)"


def summary(data: dict) -> list[str]:
    """Section 1: per asset, the prior's two families of each timeframe with their state."""
    naked = favourable.summary(data["ranked"], data["symbols"]).set_index("symbol")["families"]
    best = data["best"]
    lines = ["| activo | M15 | M30 | H1 | H4 | veredicto desnudo (nota) | barrido: variantes en "
             "meseta |", "|---|---|---|---|---|---|---|"]
    for symbol in data["symbols"]:
        cells = []
        for timeframe in TIMEFRAMES:
            if symbol not in priorview.PRIOR["matrix"]:
                cells.append("sin prior")
                continue
            got = {r["family"]: r for r in priorview.ranking(data["graded"], data["variants"],
                                                             symbol, timeframe)}
            cells.append(" / ".join(f"{f} {MARK[got[f]['flag']]}" for f in
                                    priorview.PRIOR["by_timeframe"][symbol][timeframe]))
        flat = best[(best["symbol"] == symbol) & best["on_plateau"]]
        plateau = "; ".join(f"{r.family} {r.timeframe} {r.direction} ({r.multiple:.1f}×)"
                            for r in flat.itertuples()) or "ninguna"
        lines.append(f"| `{symbol}` | " + " | ".join(cells) + f" | {naked[symbol]} | {plateau} |")
    return lines


def prior_table(data: dict, symbol: str) -> list[str]:
    """One asset's ranking by the prior, timeframe by timeframe, with what was measured beside."""
    lines = list(HEAD)
    for timeframe in TIMEFRAMES:
        main = priorview.PRIOR["by_timeframe"][symbol][timeframe][0]
        for k, r in enumerate(priorview.ranking(data["graded"], data["variants"], symbol,
                                                timeframe), 1):
            flag = r["flag"] + (f" ({', '.join(r['how'])})" if r["how"] else "")
            flag = "⚠️ **medido en contra**" if r["flag"] == AGAINST else flag
            flag = ("**la medida contradice la prior** — " if r["contradicts"] else "") + flag
            ratio = priorview.variance_cell(data["ratios"], symbol, timeframe, main) if k == 1 else ""
            lines.append(f"| {timeframe} | {k} | `{r['family']}`{' (largo)' if r['long_only'] else ''}"
                         f" | {r['role']}; matriz: {r['level']} | «{flag}» | {r['naked']} | "
                         f"{r['swept']} | {ratio} |")
    return lines


def naked_tables(data: dict, symbol: str) -> list[str]:
    """For an asset the prior does not cover: the naked verdict and the sweep on each timeframe."""
    view = data["view"][data["view"]["symbol"] == symbol].set_index(["family", "timeframe"])
    head = ["| familia | " + " | ".join(TIMEFRAMES) + " |", "|---|" + "---|" * 4]
    lines = ["", "**Por marco** (veredicto desnudo, la mejor dirección):", "", *head]
    for family in dict.fromkeys(i[0] for i in view.index):
        lines.append(f"| `{family}` | " + " | ".join(
            favourablemd._cell(view.loc[(family, t)]) if (family, t) in view.index else ""
            for t in TIMEFRAMES) + " |")
    best = data["best"][data["best"]["symbol"] == symbol].sort_values(
        ["plateau_any", "pass_any", "multiple"], ascending=False).drop_duplicates(
        ["family", "timeframe"]).set_index(["family", "timeframe"])
    lines += ["", "**Con salida razonable** (barrido aparte):", "", *head]
    for family in dict.fromkeys(i[0] for i in sorted(best.index)):
        cells = []
        for t in TIMEFRAMES:
            r = best.loc[(family, t)]
            kind = "**meseta**" if r["on_plateau"] else ("pico" if r["passes"] else "—")
            cells.append(f"{kind} {r['direction']} · `{r['entry']}` {r['param']:g} · {r['exit']} · "
                         f"{r['multiple']:.1f}× · {int(r['plateau'])}/{int(r['neighbours'])} · "
                         f"p {r['q']:.2f}")
        lines.append(f"| `{family}` | " + " | ".join(cells) + " |")
    return lines


def asset(data: dict, symbol: str, cfg: dict) -> list[str]:
    """One asset's section: the prior-led ranking, the naked verdict, what to avoid, its context."""
    lines = [f"### `{symbol}`", ""]
    covered = symbol in priorview.PRIOR["matrix"]
    if covered:
        lines += [f"*Prior: {TEXTS['prior_notes'][symbol]}.*", ""] if symbol in TEXTS[
            "prior_notes"] else []
        lines += ["**Ranking según la prior, marco por marco, con lo medido al lado** (Alta antes "
                  "que Media; a igual nivel, lo medido a favor antes; lo medido en contra se "
                  "queda, marcado):", "", *prior_table(data, symbol), "", PULLBACK]
    else:
        lines.append("**La prior no cubre este activo.** Se ordena sólo con lo medido y con la "
                     "bibliografía.")
    mine = data["ranked"][data["ranked"]["symbol"] == symbol]
    lines += ["", "**Veredicto desnudo** (los cuatro filtros sobre la medida líder de cada una de "
              "las siete familias):" + (" nada con nota." if mine.empty else "")]
    for r in mine.itertuples():
        lines.append(
            f"{r.rank}. **`{r.family}` — nota {r.grade}** · {r.timeframe} {r.direction} · "
            f"`{r.lead}` ({describe(r.lead, cfg)}) · {r.multiple:.2f}× el coste · p corr. "
            f"{r.p:.3f} (cruda {r.p_raw:.3f}) · estabilidad {r.stability:.2f} · "
            f"{r.trades_per_year:.0f} op/año" + (f" · flaqueza: {r.weak}" if r.weak else "")
            + (f" · también: {r.also}" if r.also else "")
            + f"  \n   Paleta: `{r.palette}`. Hueco libre: {r.hole}.")
    lines += [] if covered else naked_tables(data, symbol)
    bad = data["avoid"][data["avoid"]["symbol"] == symbol]
    if not bad.empty:
        lines += ["", "**Ni lo intentes (medido):** " + "; ".join(
            f"`{r.family}`" + (f" sólo en {r.where} ({favourable.AVOID[r.reason]})" if r.where else
                               f" ({favourable.AVOID[r.reason]}: {r.cells} de {r.of} celdas, "
                               f"máximo {r.best_multiple:.2f}×)") for r in bad.itertuples()) + "."]
    ctx = data["context"][data["context"]["symbol"] == symbol].set_index("timeframe")
    lines += ["", "Coste/ATR: " + ", ".join(f"{t} {ctx.loc[t, 'cost_over_atr']:.2f}"
                                            for t in TIMEFRAMES)
              + f" · deriva en build {100 * ctx.loc['H4', 'drift_per_year']:+.1f} %/año."]
    lit = data["literature"]
    named = lit[lit["named"] & lit["symbols"].map(lambda v: symbol in v)]
    if not named.empty:
        lines += ["", "**Bibliografía que lo nombra:** " + "; ".join(
            f"`{r.id}` «{r.flag}»" for r in named.itertuples()) + " — detalle en el apartado 8."]
    return [*lines, ""]


def load(folder: Path, cfg: dict) -> dict:
    """Everything the document reads: the judged map, the sweep, the variance ratios, the file."""
    scores, measures = pd.read_csv(folder / "scores.csv"), pd.read_csv(folder / "measures.csv")
    return {"scores": scores, "measures": measures, "symbols": sorted(scores["symbol"].unique()),
            "graded": priorview.graded(measures), "ranked": favourable.ranked(scores),
            "avoid": favourable.avoided(scores), "view": favourable.by_timeframe(scores),
            "variants": pd.read_parquet(folder / "sweep" / "variants.parquet"),
            "best": pd.read_csv(folder / "sweep" / "best.csv"),
            "ratios": pd.read_csv(folder / "variance_ratio.csv"),
            "context": pd.read_csv(folder / "context.csv"),
            "literature": bibliography.table(measures, cfg)}


def document(folder: Path, cfg: dict) -> str:
    """The whole of `assets/FAMILIAS.md` from the files of one judged profile.

    Args:
        folder: `AlgoData/research/profiles/` — scores, measures, context, the sweep and
            `variance_ratio.csv`.
        cfg: The parsed config.
    """
    data, said = load(folder, cfg), TEXTS["fragments"]
    parts = favourablemd.markdown(data["scores"], data["measures"]).split("\n\n")
    lit = data["literature"]
    clock = lit[lit["flag"] == bibliography.CLOCK]
    out = [said["head"], "## 1. Resumen: activo → qué generar, según la prior y lo medido", "",
           "Cada celda: familia principal / secundaria de la prior en ese marco, con su estado "
           "medido: ✔ a favor · ○ sin evidencia · ✖ en contra.", "", *summary(data), "",
           said["notes"], "## 2. Al revés: familia → activos donde el veredicto desnudo le pone "
           "nota", "", parts[1], "", "## 3. Activo por activo", ""]
    for symbol in data["symbols"]:
        out += asset(data, symbol, cfg)
    out += ["## 4. Tabla completa del veredicto desnudo (la que imprime `--favourable`)", "",
            parts[2], "", "## 5. Lo medido como malo", "", "`familia` = la familia entera en ese "
            "activo; `celda` = sólo las celdas que se nombran.", "", parts[3], "",
            "## 6. Todos los marcos, la corrección alternativa y lo descartado por usar reloj", "",
            "### 6.1 Cada activo × familia en M15, M30, H1 y H4 (veredicto desnudo)", "", parts[4],
            "", "### 6.2 La corrección alternativa — tú eliges", "", said["alt"], parts[5], "",
            parts[6], "", "### 6.3 Medido pero descartado por usar reloj", "", said["clock"],
            parts[7], "", "De la bibliografía, descartado por la misma razón (no se mide):", "",
            "| id | qué afirma | fuente | verificado |", "|---|---|---|---|"]
    out += [f"| `{r.id}` | {r.claim[:260]} | {r.source} | "
            + (r.verified if r.verified.startswith("yes") else f"**⚠️ {r.verified}**") + " |"
            for r in clock.itertuples()]
    out += ["", "## 7. El barrido de salidas y parámetros — «con salida razonable»", "",
            said["sweep"], "", "## 8. Bibliografía: lo que dicen los libros y los artículos, junto "
            "a lo medido", "", said["bib"], bibliography.markdown(data["measures"], cfg), "",
            said["tail"]]
    return "\n".join(out)
