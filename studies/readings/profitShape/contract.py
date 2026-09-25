"""The three readings as the contract's tabs: concentration, independence, and a break."""

import pandas as pd

from core.study import blocks, result as envelope
from studies.readings.profitShape import breaks, verdict

STATE = {"few_trades": "watch", "few_periods": "watch", "spread": "pass",
         "independent": "pass", "clustered": "watch", "stable": "pass", "broke": "watch"}


def reading(label: str) -> dict:
    """One reading's label and what it means, as a verdict block."""
    return blocks.verdict(label, STATE[label], verdict.MEANS[label])


def concentration_tab(conc: dict, cfg: dict) -> dict:
    """Does the result survive losing its best trades and its best year?"""
    best = cfg["run"]["best_months"]
    return envelope.tab("concentration", "1 · Concentración del beneficio", [
        reading(verdict.concentration(conc, cfg["verdict"])),
        blocks.table("Cuánto pesan los mejores", pd.DataFrame(
            [["mejor 1 % de las operaciones, parte del total", conc["top1"]],
             ["mejor 5 % de las operaciones, parte del total", conc["top5"]],
             ["media por operación", conc["mean"]], ["mediana por operación", conc["median"]],
             [f"mejores {best} meses, parte del total", conc["best_months"]],
             ["mejor año", str(conc["best_year"])],
             ["mejor año, parte del total", conc["best_year_share"]],
             ["esperanza sin el mejor año", conc["without_best_year"]["expectancy"]],
             ["operaciones sin el mejor año", conc["n_without"]]], columns=["", "valor"]),
            "La concentración no es un fallo por sí sola: un sistema de tendencia vive de "
            "pocas ganadoras grandes. Compárala con la de entradas al azar con las mismas "
            "salidas (studies/readings/monkey/, entryQuality)."),
        blocks.table("Quitando las mejores operaciones", conc["trimmed"].reset_index(),
                     "Sharpe por operación y sin anualizar: quitar operaciones cambia la "
                     "frecuencia.")],
        note="¿El resultado sobrevive a perder sus mejores operaciones y su mejor año?")


def dependence_tab(dep: dict, cfg: dict) -> dict:
    """May these trades be resampled as independent draws?"""
    return envelope.tab("dependence", "2 · Independencia de las operaciones", [
        reading(verdict.dependence(dep["runs"], dep["daily"], dep["streak"], cfg["verdict"])),
        blocks.table("Tres formas de mirar la secuencia", pd.DataFrame(
            [["rachas (Wald-Wolfowitz)", dep["runs"]["runs"], dep["runs"]["expected"],
              dep["runs"]["z"], dep["runs"]["p"]],
             ["Ljung-Box sobre operaciones", dep["trades"]["q"], None, None, dep["trades"]["p"]],
             ["Ljung-Box sobre P&L diario", dep["daily"]["q"], None, None, dep["daily"]["p"]],
             ["racha perdedora contra barajar", dep["streak"]["observed"],
              dep["streak"]["median"], None, dep["streak"]["p"]]],
            columns=["prueba", "observado", "esperado / mediana", "z", "p"]),
            f"Último retardo con autocorrelación en el P&L diario: "
            f"{dep['daily']['last_significant']}. Una sola de las tres basta: miran el signo, "
            f"el tamaño y la cola de las rachas.")],
        note="¿Se pueden remuestrear estas operaciones como sorteos independientes? Si no, "
             "un Monte Carlo que las baraja sueltas subestima la caída.")


def breaks_tab(brk: dict) -> dict:
    """Did the mean change inside the sample, and where?"""
    if not brk["cusum"]:
        return envelope.tab("breaks", "7 · ¿Cambió la media dentro de la muestra?", [],
                            note=f"{brk['n']} operaciones, por debajo del mínimo: un supremo "
                                 f"sobre una serie corta es su propio ruido. No se lee.")
    c, rolling = brk["cusum"], brk["rolling"].reset_index()
    keep = blocks.thin(len(c["path"]))
    path = [float(c["path"][i]) for i in keep]
    rolling = rolling.iloc[blocks.thin(len(rolling))]
    return envelope.tab("breaks", "7 · ¿Cambió la media dentro de la muestra?", [
        reading(verdict.structure(c)),
        {"kind": "lines", "title": "CUSUM de la media", "unit": "", "x": keep,
         "series": [{"label": "CUSUM", "values": path, "role": "real"},
                    {"label": "crítico +", "values": [breaks.CRITICAL] * len(path),
                     "role": "reference"},
                    {"label": "crítico −", "values": [-breaks.CRITICAL] * len(path),
                     "role": "reference"}],
         "note": f"Supremo {c['sup']:.2f} contra el crítico {breaks.CRITICAL}; candidato en la "
                 f"operación {c['at']} ({c['share']:.0%} de la muestra, {brk['date']:%Y-%m-%d})."},
        blocks.table("Los dos lados del candidato", brk["sides"].reset_index()),
        {"kind": "lines", "title": "Sharpe móvil con su banda", "unit": "",
         "x": [str(v) for v in rolling.iloc[:, 0]],
         "series": [{"label": col, "values": list(rolling[col]),
                     "role": "real" if col == "sharpe" else "reference"}
                    for col in rolling.columns[1:]],
         "note": "La banda usa la varianza con asimetría y curtosis de core.significance, la "
                 "misma del PSR."}],
        note="¿La media cambió en algún punto de la muestra? Si cambió, el tramo posterior es "
             "el que describe hoy.")
