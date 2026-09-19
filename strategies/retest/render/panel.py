"""Assemble the page: the shell, the tables, and one section per strategy."""

from pathlib import Path

from strategies.retest.inputs import tasks
from strategies.retest.render import charts, text

TEMPLATE = Path(__file__).with_name("panel.html")
PASSING = ("STRONG", "ACCEPTABLE", "MARGINAL")


def render(title: str, sections: list[str]) -> str:
    """Put the assembled sections inside the page shell.

    Args:
        title: Browser title.
        sections: HTML blocks, in reading order.

    Returns:
        A self-contained page: no scripts, no fonts, no network. It has to open from a USB
        stick in five years.
    """
    return (TEMPLATE.read_text(encoding="utf-8")
            .replace("__TITLE__", title).replace("__BODY__", "\n".join(sections)))


def table(headers: list[str], rows: list[list[str]]) -> str:
    """One table, first column a label and the rest numbers.

    Args:
        headers: Column titles.
        rows: Already-formatted cells.

    Returns:
        A scrollable table.
    """
    def row(cells: list[str], tag: str) -> str:
        """One line of the table."""
        return (f"<tr><{tag}>{cells[0]}</{tag}>"
                + "".join(f'<{tag} class="n">{c}</{tag}>' for c in cells[1:]) + "</tr>")

    return ('<div class="scroll"><table>' + row(headers, "th")
            + "".join(row(r, "td") for r in rows) + "</table></div>")


def headline(result: dict) -> str:
    """The numbers that decide whether the rest is worth reading.

    Args:
        result: What run.battery() returned.

    Returns:
        A row of stat tiles.
    """
    calls = [got["verdict"]["verdict"] for got in result["strategies"].values()]
    tiles = [(f"{sum(c in PASSING for c in calls)} / {len(calls)}", "pasan la bateria"),
             (f"{sum(c == 'INCONCLUSIVE' for c in calls)}", "sin evidencia para juzgar"),
             (f"{result['effective_bets']['enb']:.2f}", "apuestas efectivas de "
              f"{result['effective_bets']['n']}"),
             (f"{result['multiplicity']['pool']}", "contrastes en el pool")]
    return ('<div class="headline">'
            + "".join(f'<div class="stat"><b>{v}</b><span>{k}</span></div>' for v, k in tiles)
            + "</div>")


def verdicts(result: dict) -> str:
    """The verdict table.

    Args:
        result: What run.battery() returned.

    Returns:
        One row per strategy, worst first, with the binding constraint named.
    """
    rows = sorted(result["strategies"].items(),
                  key=lambda item: item[1]["verdict"]["composite"])
    return table(["estrategia", "veredicto", "nota", "limita", "beneficio p5", "drawdown CVaR",
                  "vetos"],
                 [[name, got["verdict"]["verdict"], f"{got['verdict']['composite']:.1f}",
                   got["verdict"]["binding"],
                   f"{got['stress']['fragility']['net_p5']['point']:,.0f}",
                   f"{got['stress']['fragility']['drawdown']['cvar']:.1f}%",
                   ", ".join(got["verdict"]["vetoes"]) or "—"]
                  for name, got in rows])


def task_table(got: dict) -> str:
    """What each of the eight tasks did to one strategy.

    Args:
        got: One strategy's entry in a run.battery() result.

    Returns:
        A table with one row per task.
    """
    rows = []
    for task in tasks.TASKS:
        if task not in got:
            continue
        entry = got[task]
        if not entry["modes"]["perturbed"]:
            shape = "no perturbo nada"
        elif not entry["modes"]["discriminated"]:
            shape = f"{entry['modes']['outcomes']} valores: rejilla"
        else:
            shape = "bimodal" if entry["modes"]["bimodality"]["bimodal"] else "unimodal"
        rows.append([tasks.TITLES[task], text.PERTURBA[task],
                     f"{entry['fragility']['net_p5']['point']:,.0f}",
                     f"{entry['fragility']['drawdown']['cvar']:.1f}%",
                     f"{entry['modes']['trades']['median_share']:.0%}", shape])
    return table(["tarea", "que perturba", "beneficio p5", "drawdown CVaR",
                  "operaciones vs original", "forma"], rows)


def strategy(name: str, got: dict) -> str:
    """One strategy's whole section: the call, what fired, the figures and the tables.

    Args:
        name: Strategy id.
        got: That strategy's entry in a run.battery() result.

    Returns:
        HTML, in the order a reader needs it: the verdict, then why, then the evidence.
    """
    v = got["verdict"]
    flags = "".join(f"<li>{text.flag(f)}</li>" for f in got["flags"])
    stress, attrib = got["stress"], got["attribution"]
    return f'''<h2 id="{name}">{name} — {v['verdict']} ({v['composite']:.1f}/100)</h2>
<p class="lede">{text.VERDICTS[v['verdict']]} Limita: <b>{v['binding']}</b>.
Subnotas: {", ".join(f"{k} {x:.0f}" for k, x in v['subscores'].items())}.</p>
{'<div class="card"><ul>' + flags + "</ul></div>" if flags else ""}
{charts.cost(attrib["ranking"], attrib["control_sigma"],
             "Que la rompe", "Cada barra es una tarea, medida contra lo que el control mueve por "
             "si solo. Menos de una sigma es ruido, no un hallazgo.")}
{charts.distribution(stress["_net"], stress["original_net"],
                     "Estres combinado: mil re-ejecuciones",
                     "Las seis perturbaciones a la vez, sobre muestra completa. La linea es el "
                     "backtest que de verdad ocurrio.", "beneficio neto, USD")}
{charts.fan(stress["fan"], "El abanico de equity bajo estres",
            "Donde pudo haber ido la curva. El eje X es avance de 0 a 1 y no el numero de "
            "operacion: cada re-ejecucion tiene su propia cuenta de operaciones.")}
<h3>Las ocho tareas</h3>
{task_table(got)}'''


def page(result: dict, title: str, note: str) -> str:
    """The whole report as one self-contained HTML page.

    Args:
        result: What run.battery() returned.
        title: Page and browser title.
        note: The paragraph about the ingest this was built from.

    Returns:
        HTML.
    """
    body = [f"<h1>{title}</h1>", f'<p class="lede">{note}</p>', headline(result),
            "<h2>Veredictos</h2>", verdicts(result),
            '<div class="card">' + text.battery_note(result).replace("\n\n", "<br><br>")
            + "</div>",
            '<div class="card"><b>Los umbrales son valores por defecto, no una politica.</b> '
            "Los cortes de <code>gates.py</code> salen del <code>config.yaml</code> y nadie los "
            "ha calibrado contra la operativa real. Si fallan todas, mira primero el umbral: se "
            "mueve con <code>--set gates.survival_dd_pct=0.35</code>.</div>"]
    body += [strategy(name, got) for name, got in sorted(result["strategies"].items())]
    return render(title, body)
