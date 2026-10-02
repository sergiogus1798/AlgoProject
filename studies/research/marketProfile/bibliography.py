"""What the literature says beside what the profile measured: the bibliography view of `assets/FAMILIAS.md`."""

import pandas as pd
import yaml

from core.researchpaths import research_profiles_dir

FILE = "edges-2026-10-02.yaml"
CLASSES = {"indices": ["DAX40", "DJ30", "NIKKEI225", "USA500", "USATEC"],
           "forex": ["AUDJPY", "AUDUSD", "CADJPY", "EURJPY", "EURUSD", "GBPJPY", "GBPUSD", "USDCAD",
                     "USDCHF", "USDJPY"],
           "metals": ["XAGUSD", "XAUUSD"], "oils": ["UKOIL", "USOIL"]}
MEASURED, ONLY, ABSENT, CLOCK = ("medido", "sólo bibliografía",
                                 "la bibliografía lo afirma y aquí no se mide",
                                 "descartado por usar reloj")
# Why an entry that needs no clock and has a testable translation is still not measured.
WHY = {
    "TR-13": "es una rejilla de correlaciones lookback × hold en D1, no una regla; los `tsmom_d*` "
             "miden sus diagonales",
    "REV-44": "es una vida media por par en D1; el perfil sólo la mide en el marco de la celda "
              "(`pullback_speed`)",
    "GOLD-51": "necesita otro activo (EURUSD como proxy del dólar): el perfil mide cada activo solo",
    "VOL-52": "es una correlación de rangos diarios, no una regla con operaciones",
    "VOL-53": "es un filtro de volatilidad sobre cualquier entrada larga de índice; medido sólo "
              "en `fast_d5_20_quiet_run`",
    "VOL-54": "necesita terciles móviles de la anchura de Bollinger; no implementado"}


def entries() -> list[dict]:
    """The literature file's entries, as written by the literature agent."""
    path = research_profiles_dir().parent / "literature" / FILE
    return yaml.safe_load(path.read_text(encoding="utf-8"))["entries"]


def tested(cfg: dict) -> dict[str, list[str]]:
    """Literature id → the measures of the config that test it (their `lit` field)."""
    out = {}
    for spec in cfg["measures"]:
        for key in str(spec.get("lit", "")).split():
            out.setdefault(key, []).append(spec["name"])
    return out


def flag(entry: dict, names: list[str]) -> str:
    """One of MEASURED, CLOCK, ONLY, ABSENT for an entry, given the measures that test it."""
    if names:
        return MEASURED
    if str(entry["needs_clock"]).startswith(("yes", "mixed")):
        return CLOCK
    return ONLY if str(entry["translation"]["entry"]).startswith("n/a") else ABSENT


def symbols(entry: dict) -> tuple[list[str], bool]:
    """The assets an entry speaks of, and whether it names them (else it is class-level)."""
    every = [s for group in CLASSES.values() for s in group]
    named = [s for s in every if s in str(entry["assets"])]
    if named:
        return named, True
    group = [s for k, v in CLASSES.items() if k in str(entry["asset_class"]) for s in v]
    return group or every, False


def directions(entry: dict) -> list[str]:
    """The sides an entry claims: one when its `direction` opens with it, else both."""
    said = str(entry["direction"]).lower()
    return [d for d in ("long", "short") if said.startswith(d)] or ["long", "short"]


def _flat(text: object) -> str:
    """A field of the file as one table cell: no line break, no column bar."""
    return " ".join(str(text).split()).replace("|", "/")


def _best(rows: pd.DataFrame) -> str:
    """The best row of a set in one phrase: what passes first, then the smallest corrected p."""
    r = rows.sort_values(["passes", "q", "multiple"], ascending=[False, True, False]).iloc[0]
    fails = [w for w, ok in (("no significativa", r["significant"]), ("no paga 2×", r["pays"]),
                             ("inestable", r["stable"]), ("pocas operaciones", r["frequent"]))
             if not ok]
    verdict = "pasa los cuatro filtros" if r["passes"] else "falla: " + ", ".join(fails)
    return (f"{r['symbol']} {r['timeframe']} {r['direction']} `{r['measure']}` {r['multiple']:.1f}× "
            f"· p corr. {r['q']:.2f} (cruda {r['p']:.3f}) · {r['trades_per_year']:.0f}/año — "
            f"{verdict}")


def reading(rows: pd.DataFrame) -> str:
    """What the profile measured for one entry: the counts over its cells and the best one."""
    if rows.empty:
        return "—"
    ran = rows[rows["n_trades"] >= 30]
    if ran.empty:
        return f"{len(rows)} celdas, ninguna llega a 30 operaciones en build: sin contraste"
    return (f"{len(ran)} celdas con contraste: {int((ran['p'] <= 0.05).sum())} con p cruda ≤ 0,05, "
            f"{int(ran['significant'].sum())} significativas tras corregir, "
            f"{int(ran['passes'].sum())} pasan los cuatro. Mejor: {_best(ran)}")


def table(measures: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """One row per literature entry: what it says, its source and caveat, the flag, the reading.

    Args:
        measures: The profile's `measures.csv`.
        cfg: The parsed config (its measures' `lit` links them to the entries).

    Returns:
        `id`, `family`, `assets`, `named` (the entry names assets, else class-level),
        `symbols`, `directions`, `claim`, `source`, `verified`, `grade`, `flag`, `measures`, `reading`.
    """
    links, rows = tested(cfg), []
    for e in entries():
        names = links.get(e["id"].split("-")[0] + "-" + e["id"].split("-")[1], [])
        where, named = symbols(e)
        own = measures[measures["measure"].isin(names) & measures["symbol"].isin(where)
                       & measures["direction"].isin(directions(e))]
        state = flag(e, names)
        rows.append({"id": e["id"], "family": e["family"], "assets": str(e["assets"]),
                     "named": named, "symbols": where, "directions": directions(e),
                     "claim": _flat(f"{e['direction']} — {e['size']}"),
                     "source": _flat(e["source"]),
                     "verified": _flat(e["verified"]), "grade": _flat(e["grade"]), "flag": state,
                     "measures": names,
                     "reading": reading(own) if state == MEASURED else WHY.get(
                         e["id"].split("-")[0] + "-" + e["id"].split("-")[1], "—")})
    return pd.DataFrame(rows)


def _line(r: pd.Series, reading_: str) -> str:
    """One Markdown row; a source the file does not mark verified carries its caveat in bold."""
    sure = r["verified"] if r["verified"].startswith("yes") else f"**⚠️ {r['verified']}**"
    return (f"| `{r['id']}` | `{r['family']}` | {r['claim']} | {r['source']} | {sure} · "
            f"{r['grade']} | «{r['flag']}» | {reading_} |")


def markdown(measures: pd.DataFrame, cfg: dict) -> str:
    """The bibliography view: every entry once, then per asset the entries that name it."""
    got = table(measures, cfg)
    head = ["| id | familia | qué afirma (dirección — tamaño) | fuente | verificado · grado | "
            "estado | lo medido aquí |", "|---|---|---|---|---|---|---|"]
    counts = got["flag"].value_counts()
    parts = [", ".join(f"{n} «{k}»" for k, n in counts.items()) + f" — {len(got)} entradas.", ""]
    parts += head + [_line(r, r["reading"]) for _, r in got.iterrows()]
    for symbol in sorted(s for group in CLASSES.values() for s in group):
        mine = got[got["named"] & got["symbols"].map(lambda v: symbol in v)]
        parts += ["", f"#### `{symbol}` — lo que la bibliografía dice nombrándolo", ""]
        if mine.empty:
            parts.append("Ninguna entrada lo nombra; le aplican las de su clase (tabla de arriba).")
            continue
        parts += head
        for _, r in mine.iterrows():
            own = measures[measures["measure"].isin(r["measures"]) & (measures["symbol"] == symbol)
                           & measures["direction"].isin(r["directions"])]
            parts.append(_line(r, reading(own) if r["flag"] == MEASURED else r["reading"]))
    return "\n".join(parts) + "\n"
