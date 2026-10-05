"""«Correlación»: a pool's pair measures as a matrix judged against the threshold, and its admissible graph."""

import pandas as pd

from portfolio.common.construct.inputs import pool as pool_mod
from ui.daemon.portfolios import parts, shelf

# (key in pairs.parquet — {f} is the frequency —, the threshold it answers to, label, meaning).
MEASURES = (
    ("pearson_{f}", "pearson", "Pearson", "Correlación lineal del P&L por periodo de las dos."),
    ("spearman_{f}", "spearman", "Spearman", "Correlación de los rangos del P&L por periodo: no "
     "la mueve un mes extremo."),
    ("co_loss", "co_loss", "Pérdidas a la vez", "Cuánto más coinciden sus meses perdedores de "
     "lo que coincidirían por azar."),
    ("tail", "tail", "Colas", "Correlación en los meses en que alguna de las dos está en su "
     "peor 30 %."),
    ("rolling_pearson_whole", "rolling_whole", "Móvil 60 m · Pearson · todo build",
     "La peor correlación de Pearson en cualquier ventana de 60 meses de build."),
    ("rolling_spearman_whole", "rolling_whole", "Móvil 60 m · Spearman · todo build",
     "La peor correlación de Spearman en cualquier ventana de 60 meses de build."),
    ("rolling_pearson_recent", "rolling_recent", "Móvil 60 m · Pearson · reciente",
     "La peor de Pearson en las ventanas que acaban en los últimos 36 meses de build."),
    ("rolling_spearman_recent", "rolling_recent", "Móvil 60 m · Spearman · reciente",
     "La peor de Spearman en las ventanas que acaban en los últimos 36 meses de build."),
)
FILTERS = {"overlap": "solape < 24 meses", "undefined": "coeficiente indefinido"}
STEPS = (("pass", "baja: hasta la mitad del umbral"), ("watch", "admisible, cerca del umbral"),
         ("fail", "pasa del umbral: la pareja se rechaza"))
NO_SCREEN = ("Este universo se construyó antes de que el comando guardase su criba: no sé con qué "
             "umbrales se juzgó ni qué parejas pasan. Pulsa «Calcular parejas» y aparece.")


def universe(pool: str, firm: str) -> tuple[shelf.Path | None, dict | None]:
    """The pool's newest universe folder and its `screen.json` (None when it has none)."""
    found = shelf.universes(pool_mod.read(pool, firm or None)["hash"])
    if not found:
        return None, None
    screen = found[0] / "screen.json"
    return found[0], shelf.load(screen) if screen.exists() else None


def state(value: float | None, threshold: float | None, two_sided: bool) -> str | None:
    """The discrete step a cell is painted in, relative to the threshold in force."""
    if value is None or pd.isna(value) or threshold is None:
        return None
    size = abs(value) if two_sided else value
    return "fail" if size > threshold else "watch" if size > threshold / 2 else "pass"


def read(pool: str = "", firm: str = "", freq: str = "monthly", measure: str = "pearson", **_: str) -> dict:
    """The matrix of one measure and the admissible graph of the pool's newest universe."""
    if not pool:
        return parts.empty("No hay ningún pool declarado.", "marca estrategias abajo, en "
                           "«Estrategias», y pulsa «Declarar pool con las marcadas».")
    folder, screen = universe(pool, firm)
    if folder is None:
        return parts.empty(f"Las parejas del pool «{pool}» no están medidas.", "pulsa «Calcular parejas»: "
                           "reconstruye la curva diaria de cada miembro y mide todas las parejas "
                           "en build (unos segundos por estrategia).")
    known = shelf.names()
    pairs = pd.read_parquet(folder / "pairs.parquet")
    key, limit, label, meaning = next((m for m in MEASURES if measure in (m[1], m[0])), MEASURES[0])
    key = key.format(f=freq)
    ids = (screen or {}).get("identities") or sorted(set(pairs["i"]) | set(pairs["j"]))
    threshold = screen["thresholds"][limit] if screen else None
    two_sided = bool(screen) and screen["sign"] == "abs" and key not in screen["one_sided"]
    cell = {(r.i, r.j): r.value for r in pairs[pairs["measure"] == key].itertuples()}
    values = [[None if a == b else parts.clean(float(cell.get((a, b), cell.get((b, a), float("nan")))))
               for b in ids] for a in ids]
    matrix = {"ids": ids, "labels": [shelf.label(i, known) for i in ids], "values": values,
              "states": [[state(v, threshold, two_sided) for v in row] for row in values],
              "measure": label, "meaning": meaning, "threshold": threshold, "two_sided": two_sided,
              "steps": [{"state": s, "text": t} for s, t in STEPS]}
    return {"matrix": matrix, "tabs": [graph(screen, known)], "relaxed": parts.relaxed((screen or {}).get("relaxed")),
            "measures": [{"key": m[1] if "{f}" in m[0] else m[0], "label": m[2], "help": m[3],
                          "by_freq": "{f}" in m[0]} for m in MEASURES],
            "facts": [f"universo {folder.name[-16:]} · construido {shelf.load(folder / 'manifest.json')['built_at'][:16]}"],
            "empty": None if screen else NO_SCREEN}


def graph(screen: dict | None, known: dict) -> dict:
    """The «Parejas admisibles» tab: every pair, whether it clears the six filters, and why not."""
    if not screen:
        return parts.tab("Parejas admisibles", parts.callout(NO_SCREEN, "watch"))
    why: dict[tuple, list[str]] = {}
    for f in screen["failing"]:
        why.setdefault((f["i"], f["j"]), []).append(FILTERS.get(f["filter"], f["filter"]))
    ids, edges = screen["identities"], {tuple(e) for e in screen["edges"]}
    rows, states = [], []
    for a, i in enumerate(ids):
        for j in ids[a + 1:]:
            ok = (i, j) in edges
            rows.append([shelf.label(i, known), shelf.label(j, known), "sí" if ok else "no",
                         ", ".join(why.get((i, j), why.get((j, i), []))) or "—"])
            states.append([None, None, "pass" if ok else "fail", None])
    calm, stress = screen["effective_n"]["calm"], screen["effective_n"]["stress"]
    head = (f"{screen['n_admissible_pairs']} parejas admisibles de {screen['n_pairs']} · "
            f"{screen['n_out']} de {screen['n_in']} estrategias tienen al menos una pareja admisible · "
            f"N efectivo {calm['participation']:.1f} en calma y {stress['participation']:.1f} en estrés "
            "(a cuántas estrategias independientes equivale el pool).")
    limits = parts.table("Umbrales en vigor", ["filtro", "umbral"],
                         [[k, v] for k, v in screen["thresholds"].items()],
                         "Una pareja es admisible solo si no pasa de NINGUNO. «Colas» y «pérdidas a la "
                         "vez» solo rechazan por arriba; el resto, por valor absoluto.")
    return parts.tab("Parejas admisibles", parts.callout(head),
                     parts.table("Cada pareja contra los seis filtros", ["estrategia", "con", "admisible", "falla por"],
                                 rows, "Solo las combinaciones cuyas parejas son todas admisibles pueden "
                                 "ser cartera.", states=states), limits)


def pair(pool: str, i: str, j: str, firm: str = "", freq: str = "monthly") -> dict:
    """One cell opened: the two strategies' P&L per period in build, and every measure of the pair."""
    folder, screen = universe(pool, firm)
    known, manifest = shelf.names(), shelf.load(folder / "manifest.json")
    lo, hi = (pd.Timestamp(d) for d in manifest["calendar"]["build"])
    if freq == "monthly":
        frame = pd.read_parquet(folder / "monthly.parquet", columns=[i, j])
        frame = frame[(frame.index.to_timestamp() >= lo) & (frame.index.to_timestamp() <= hi)]
    else:
        frame = pd.read_parquet(folder / "daily.parquet", columns=[i, j]).loc[lo:hi]
    frame = frame.dropna(how="all")
    series = [{"label": shelf.label(k, known), "role": "sim",
               "values": [parts.clean(float(v)) for v in frame[k]]} for k in (i, j)]
    pairs = pd.read_parquet(folder / "pairs.parquet")
    mine = pairs[((pairs["i"] == i) & (pairs["j"] == j)) | ((pairs["i"] == j) & (pairs["j"] == i))]
    rows, states = [], []
    for key, limit, label, _ in MEASURES:
        for f in (("monthly", "daily") if "{f}" in key else ("",)):
            hit = mine[mine["measure"] == key.format(f=f)]
            if hit.empty:
                continue
            value = float(hit["value"].iloc[0])
            threshold = screen["thresholds"][limit] if screen else None
            two = bool(screen) and screen["sign"] == "abs" and key.format(f=f) not in screen["one_sided"]
            verdict = state(value, threshold, two)
            rows.append([label + ({"monthly": " · mensual", "daily": " · diaria"}.get(f, "")), value,
                         threshold, {"fail": "no pasa", None: "—"}.get(verdict, "pasa")])
            states.append([None, None, None, "fail" if verdict == "fail" else "pass" if verdict else None])
    word = "mes" if freq == "monthly" else "día"
    return {"title": f"{shelf.label(i, known)}  ×  {shelf.label(j, known)}",
            "relaxed": parts.relaxed((screen or {}).get("relaxed")),
            "blocks": [{"kind": "lines", "title": f"P&L por {word} de las dos, en build", "unit": "",
                        "x": [str(d)[:10] for d in frame.index], "series": series,
                        "note": "En la moneda del backtest archivado de cada una. Las parejas se "
                                "miden solo en build."},
                       parts.table("Todas las medidas de la pareja", ["medida", "valor", "umbral", "¿pasa?"],
                                   rows, f"{int(mine['n_overlap_months'].iloc[0])} meses compartidos.",
                                   states=states)]}
