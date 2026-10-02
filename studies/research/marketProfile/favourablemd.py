"""The favourable-families tables as Markdown: what `report --favourable` prints for `assets/FAMILIAS.md`."""

import json

import pandas as pd

from studies.research.marketProfile.favourable import (AVOID, avoided, by_timeframe, clocked,
                                                       ranked, regraded, reverse, summary)

TIMEFRAMES = ["M15", "M30", "H1", "H4"]


def _cell(r: pd.Series) -> str:
    """One timeframe of the per-timeframe view: the grade in bold, or the nearest miss."""
    text = f"{r['direction']} · `{r['lead']}` · {r['multiple']:.1f}× · p {r['p']:.2f} · {r['trades_per_year']:.0f}/año"
    return f"**{r['grade']}** {text}" if r["grade"] else f"— {text}"


def timeframes(scores: pd.DataFrame) -> list[str]:
    """The per-timeframe view: one line per asset and family, one column per timeframe."""
    view = by_timeframe(scores).set_index(["symbol", "family", "timeframe"])
    parts = ["| activo | familia | " + " | ".join(TIMEFRAMES) + " |", "|---|---|" + "---|" * 4]
    for symbol, family in dict.fromkeys(i[:2] for i in view.index):
        cells = [_cell(view.loc[(symbol, family, t)]) if (symbol, family, t) in view.index
                 else "" for t in TIMEFRAMES]
        parts.append(f"| `{symbol}` | `{family}` | " + " | ".join(cells) + " |")
    return parts


def clock(measures: pd.DataFrame) -> list[str]:
    """The note «medido pero descartado por usar reloj» as a table."""
    parts = ["| activo | celda | medida | elegido | nota que tendría | efecto | p corr. | op/año |",
             "|---|---|---|---|---|---|---|---|"]
    for r in clocked(measures).itertuples():
        chosen = ", ".join(f"{k} {v}" for k, v in json.loads(r.detail).items())
        parts.append(f"| `{r.symbol}` | {r.timeframe} {r.direction} | `{r.measure}` | {chosen} | "
                     f"{r.grade} | {r.multiple:.2f}× | {r.p:.3f} | {r.trades_per_year:.0f} |")
    return parts


def alternative(scores: pd.DataFrame) -> list[str]:
    """What changes if the correction is made inside each family instead of over every test."""
    moved = regraded(scores)
    parts = [f"Con la corrección alternativa (Benjamini-Hochberg dentro de cada familia): "
             f"{int(scores['passes_family'].sum())} celdas-familia pasan los cuatro filtros, "
             f"frente a {int(scores['passes'].sum())} con la corrección de cabecera; "
             f"{len(moved)} cambian de nota.", "",
             "| activo | celda | familia | medida | efecto | p cruda | p corr. (todas) | "
             "p corr. (familia) | nota | nota alternativa |", "|---|---|---|---|---|---|---|---|---|---|"]
    parts += [f"| `{r.symbol}` | {r.timeframe} {r.direction} | `{r.family}` | `{r.lead}` | "
              f"{r.multiple:.2f}× | {r.p_raw:.3f} | {r.p:.3f} | {r.p_family:.3f} | "
              f"{r.grade or '—'} | {r.grade_family or '—'} |" for r in moved.itertuples()]
    return parts


def markdown(scores: pd.DataFrame, measures: pd.DataFrame) -> str:
    """The tables of `assets/FAMILIAS.md` as Markdown: summary, reverse, detail, avoid, then the
    per-timeframe view, the alternative correction and what the clock rule leaves out."""
    table, bad = ranked(scores), avoided(scores)
    symbols = sorted(scores["symbol"].unique())
    parts = ["| activo | familias, de más a menos favorable |", "|---|---|"]
    parts += [f"| `{r.symbol}` | {r.families} |" for r in summary(table, symbols).itertuples()]
    parts += ["", "| familia | activos donde aparece, el mejor primero |", "|---|---|"]
    parts += [f"| `{r.family}` | {r.assets} |" for r in reverse(table).itertuples()]
    parts += ["", "| activo | nº | familia | nota | celda | medida | efecto | p corr. | p cruda "
              "| estab. | op/año | flaqueza | también en | paleta | hueco libre (peso) |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    parts += [f"| `{r.symbol}` | {r.rank} | `{r.family}` | **{r.grade}** | {r.timeframe} "
              f"{r.direction} | `{r.lead}` | {r.multiple:.2f}× | {r.p:.3f} | {r.p_raw:.3f} | "
              f"{r.stability:.2f} | {r.trades_per_year:.0f} | {r.weak or '—'} | {r.also or '—'} "
              f"| `{r.palette}` | {r.hole} |" for r in table.itertuples()]
    parts += ["", "| activo | familia | alcance | por qué | celdas | lo máximo que paga |",
              "|---|---|---|---|---|---|"]
    parts += [f"| `{r.symbol}` | `{r.family}` | {r.scope} | {AVOID[r.reason]} | {r.cells} de "
              f"{r.of}{' (' + r.where + ')' if r.where else ''} | {r.best_multiple:.2f}× |"
              for r in bad.itertuples()]
    parts += ["", *timeframes(scores), "", *alternative(scores), "", *clock(measures)]
    return "\n".join(parts) + "\n"
