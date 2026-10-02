"""Known-answer tests of the favourable-families ranking: grades, order, what is left out.

A hand-made `scores.csv` whose grade is known by construction, cell by cell; the clock rule
(no grade, own note), the per-timeframe view and the alternative correction; and the free
hole's palettes checked against the board's own reading of the two rules.

Run: python3 tests/test_marketprofile_favourable.py
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.research.board import palette  # noqa: E402
from studies.research.board.inputs import CONFIG  # noqa: E402
from studies.research.marketProfile import favourable, favourablemd  # noqa: E402


def cell(symbol: str, family: str, multiple: float, p: float, p_raw: float,
         stability: float = 0.8, trades: float = 100.0, timeframe: str = "H1",
         direction: str = "long", clock: bool = False, p_family: float | None = None) -> dict:
    """One row of scores.csv, its four filters derived as the profile derives them."""
    alone = p if p_family is None else p_family
    rest = multiple >= 2.0 and stability > 0.5 and trades >= 40
    return {"symbol": symbol, "timeframe": timeframe, "direction": direction, "family": family,
            "lead": "m", "p": p, "p_raw": p_raw, "multiple": multiple, "stability": stability,
            "trades_per_year": trades, "significant": p <= 0.05, "pays": multiple >= 2.0,
            "stable": stability > 0.5, "frequent": trades >= 40, "needs_clock": clock,
            "passes": p <= 0.05 and rest, "p_family": alone, "significant_family": alone <= 0.05,
            "passes_family": alone <= 0.05 and rest}


def measure(symbol: str, name: str, q: float, multiple: float, clock: bool) -> dict:
    """One row of measures.csv: a trade measure that is stable and frequent."""
    return {"symbol": symbol, "timeframe": "H1", "direction": "long", "family": "sesion",
            "measure": name, "detail": '{"hour": 9}', "p": q / 10, "q": q, "multiple": multiple,
            "stability": 0.8, "trades_per_year": 250.0, "significant": q <= 0.05,
            "pays": multiple >= 2.0, "stable": True, "frequent": True, "needs_clock": clock}


def scores() -> pd.DataFrame:
    """Two assets with one cell of every kind, and a third with nothing above the bar."""
    return pd.DataFrame([
        cell("AAA", "momentum", 3.0, 0.01, 0.001),                      # A: the four filters
        cell("AAA", "reversion", 9.0, 0.01, 0.001, trades=15),          # B: too few trades
        cell("AAA", "ruptura", 4.0, 0.01, 0.001, stability=0.4),        # B: fragile
        cell("AAA", "sesion", 1.5, 0.01, 0.001),                        # C: significant, 1-2x
        cell("AAA", "tendencia", 5.0, 0.30, 0.04),                      # C: pays, raw p only
        cell("AAA", "tendencia", 2.5, 0.30, 0.04, timeframe="H4"),      # its second cell
        cell("AAA", "patron", 0.2, 0.01, 0.001),                        # avoid: does not pay
        cell("AAA", "volatilidad", 6.0, 0.90, 0.40),                    # nothing: pure noise
        cell("BBB", "momentum", 5.0, 0.30, 0.04, trades=10),            # nothing: two weaknesses
        cell("BBB", "sesion", 0.9, 0.01, 0.001),                        # nothing: under one cost
        cell("BBB", "ruptura", -1.5, 1.0, 0.99),                        # avoid: reversed sign
        cell("BBB", "ruptura", 0.8, 0.90, 0.50, timeframe="H4"),
        cell("BBB", "tendencia", 0.3, 0.90, 0.50),                      # avoid: flat
        cell("CCC", "momentum", 0.7, 0.90, 0.50)])


def test_grades() -> None:
    """Every cell gets the grade it was built for, and the weakness is named."""
    got = favourable.graded(scores()).set_index(["symbol", "family", "timeframe"])
    grade = got["grade"].to_dict()
    assert grade[("AAA", "momentum", "H1")] == "A"
    assert grade[("AAA", "reversion", "H1")] == grade[("AAA", "ruptura", "H1")] == "B"
    assert grade[("AAA", "sesion", "H1")] == grade[("AAA", "tendencia", "H1")] == "C"
    assert {grade[k] for k in grade if k[0] != "AAA" or k[1] in ("patron", "volatilidad")} == {""}
    assert got.loc[("AAA", "reversion", "H1"), "weak"] == "pocas operaciones"
    assert got.loc[("AAA", "ruptura", "H1"), "weak"] == "frágil"
    assert got.loc[("AAA", "momentum", "H1"), "weak"] == ""
    print("notas: A, B por pocas operaciones, B frágil, C de las dos clases, y nada por debajo")


def test_ranked() -> None:
    """Most favourable first, one row per family, and an asset with nothing has no row."""
    table = favourable.ranked(scores())
    assert set(table["symbol"]) == {"AAA"}
    assert table["family"].tolist() == ["momentum", "reversion", "ruptura", "sesion", "tendencia"]
    assert table["rank"].tolist() == [1, 2, 3, 4, 5]
    trend = table.set_index("family").loc["tendencia"]
    assert trend["timeframe"] == "H1" and trend["also"] == "H4 long C 2.5×"
    assert trend["palette"] == "tendencia_base_v2"
    summary = favourable.summary(table, ["AAA", "BBB", "CCC"]).set_index("symbol")["families"]
    assert summary["BBB"] == summary["CCC"] == "nada favorable medido"
    assert summary["AAA"].startswith("momentum (A, H1 long), reversion (B")
    assert favourable.reverse(table)["family"].tolist()[0] == "momentum"
    measures = pd.DataFrame([measure("AAA", "best_hour", 0.01, 3.0, True)])
    assert "| `AAA` | 1 | `momentum` | **A** |" in favourablemd.markdown(scores(), measures)
    print("orden: nota, luego significativa antes que no, luego múltiplo; BBB y CCC, nada")


def test_avoided() -> None:
    """The three ways of being bad, and never a family that is listed as favourable."""
    bad = favourable.avoided(scores()).set_index(["symbol", "family"])
    assert bad["reason"].to_dict() == {("AAA", "patron"): "no_paga",
                                       ("BBB", "ruptura"): "signo_contrario",
                                       ("BBB", "tendencia"): "plana"}
    assert bad["scope"].to_dict() == {("AAA", "patron"): "familia", ("BBB", "ruptura"): "celda",
                                      ("BBB", "tendencia"): "familia"}
    assert bad.loc[("BBB", "ruptura"), "where"] == "H1 long"
    print("a evitar: estructura que no paga, signo contrario en su celda, familia plana")


def test_clock() -> None:
    """A family that needs the clock is never graded, never avoided, and is kept in its own note."""
    table = pd.concat([scores(), pd.DataFrame([
        cell("DDD", "sesion", 3.0, 0.01, 0.001, clock=True),             # would be an A
        cell("DDD", "patron", 0.2, 0.01, 0.001, clock=True)])],          # would be avoided
        ignore_index=True)
    got = favourable.graded(table)
    assert (got.loc[got["symbol"] == "DDD", ["grade", "avoid"]] == "").all().all()
    assert "DDD" not in set(favourable.ranked(table)["symbol"])
    assert "DDD" not in set(favourable.avoided(table)["symbol"])
    assert "DDD" not in set(favourable.by_timeframe(table)["symbol"])
    measures = pd.DataFrame([measure("DDD", "best_hour", 0.01, 3.0, True),
                             measure("DDD", "best_band", 0.01, 0.3, True),
                             measure("DDD", "prev_day_break", 0.01, 3.0, False)])
    note = favourable.clocked(measures)
    assert note["measure"].tolist() == ["best_hour"] and note["grade"].tolist() == ["A"]
    text = favourablemd.markdown(table, measures)
    assert "| `DDD` | H1 long | `best_hour` | hour 9 | A |" in text
    print("reloj: sin nota, sin «ni lo intentes», fuera de la vista por marco, y en su nota aparte")


def test_views() -> None:
    """Every timeframe of an asset is shown, graded or not; and the alternative correction
    lists exactly the cells whose grade it changes."""
    view = favourable.by_timeframe(scores()).set_index(["symbol", "family", "timeframe"])
    assert view.loc[("AAA", "tendencia", "H4"), "grade"] == "C"
    assert view.loc[("BBB", "ruptura", "H4"), "grade"] == ""          # shown though below the bar
    assert view.loc[("BBB", "ruptura", "H4"), "multiple"] == 0.8
    table = pd.concat([scores(), pd.DataFrame([
        cell("EEE", "tendencia", 4.0, 0.30, 0.004, p_family=0.02)])], ignore_index=True)
    moved = favourable.regraded(table)
    assert moved[["symbol", "grade", "grade_family"]].to_numpy().tolist() == [["EEE", "C", "A"]]
    assert favourable.ranked(table, by_family=True).query("symbol == 'EEE'")["grade"].item() == "A"
    print("vistas: cada marco de cada activo, con nota o sin ella; la corrección alternativa "
          "sólo mueve la celda que debe")


def test_hole() -> None:
    """The hole's palettes carry the weights the board gives each family, and never its own."""
    for family, fixed in CONFIG["taxonomy_family"].items():
        rules = CONFIG["palette"]
        want = {favourable.PALETTE[f]: rules["weights"].get(palette.relation(fixed, other, rules), 0)
                for f, other in CONFIG["taxonomy_family"].items()}
        got = dict(part.rstrip(")").split(" (") for part in favourable.hole(family).split(", "))
        assert got == {k: str(v) for k, v in want.items() if v}, family
        assert favourable.PALETTE[family] not in got
    assert favourable.hole("ruptura").startswith("sesion_base (3), volatilidad_base (3), reversion")
    assert all((Path(__file__).resolve().parent.parent / "sqx" / "blocks" / "palettes"
                / f"{name}.yaml").exists() for name in favourable.PALETTE.values())
    print("hueco libre: los pesos del tablero, sin la propia familia ni dos iguales")


def main() -> None:
    """Run every test."""
    test_grades()
    test_ranked()
    test_avoided()
    test_clock()
    test_views()
    test_hole()
    print("OK test_marketprofile_favourable")


if __name__ == "__main__":
    main()
