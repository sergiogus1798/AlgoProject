"""The real path's decision sentence (PLAN §5.5): the cost next to the gain."""

from . import decide

STATE = {"pass": "PASA", "fail": "NO PASA"}


def oos1_lines(first: dict) -> list[str]:
    """The oos1 reading in Spanish: the bar, or why the null cannot say anything."""
    space = ("un espacio demasiado grande para contarlo" if first["n_space"] is None
             else f"{decide.grouped(first['n_space'])} combinaciones admisibles distintas de ese tamaño")
    head = (f"  oos1 ({first['span'][0]}…{first['span'][1]}) contra {decide.grouped(first['n'])} carteras "
            f"admisibles al azar de K={first['k']} ({space}; {decide.grouped(first['n_distinct'])} salieron):")
    m = first["metrics"]
    figures = (f"    en oos1: RAR {m['rar']:.4f} por unidad de riesgo y año · R³ {m['r_cubed']:.2f} · "
               f"gain-to-pain {m['gain_to_pain']:.2f} · P(año perdedor) {m['p_losing_year']:.0%} · "
               f"Sharpe diario {first['sharpe']:.4f}")
    if first["state"] == "no_discrimina":
        return [head, f"    NO DISCRIMINA: la cartera elegida es ella sola el {first['share_chosen']:.1%} "
                      f"de las extracciones, más que el {1 - first['quantile'] / 100:.0%} que deja "
                      f"libre el percentil {first['quantile']:.0f}; el listón sería su propia cifra y el "
                      "percentil no se lee. Hace falta un pool con más combinaciones admisibles.",
                figures]
    return [head, f"    puntuación por rangos {first['value']:.3f} frente al percentil "
                  f"{first['quantile']:.0f} del azar {first['bar']:.3f} (mediana {first['null_median']:.3f}); "
                  f"la elegida queda en el percentil {first['percentile']:.1%} → {STATE[first['state']]}",
            figures]


def sentence(v: dict) -> str:
    """The real-path decision in Spanish."""
    c, cost = v["chosen"], v["cost"]
    lines = [f"La cartera de K={len(c['members'])} [{', '.join(m[:8] for m in c['members'])}] "
             f"(de {cost['n_pool']} utilizables; {decide.grouped(cost['n_scored'])} combinaciones probadas en "
             f"build; deja fuera {cost['n_pool'] - len(c['members'])}):"]
    lines += oos1_lines(v["oos1"])
    lines += [decide.oos2_line(v["oos2"]), decide.hold_line(v["hold"], cost["segments"])]
    tail = {True: "la combinación queda validada en backtest; lo siguiente es la incubación en vivo",
            False: "esta combinación no se opera",
            None: "no se aprueba ni se descarta nada"}[v["pass"]]
    lines.append(f"Veredicto: {v['label']} — {tail}.")
    return "\n".join(lines)
