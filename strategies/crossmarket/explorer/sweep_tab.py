"""The window-sweep tab: p against block size for the free-placement models, Calendar Shift flat."""

import numpy as np

from strategies.crossmarket import figures, metrics, panel, sweep, tables

TRENDS_ES = {"timing": "plano/decreciente → timing", "regime": "creciente → régimen",
             "no_pass": "sin pass a ningún tamaño: no hay aprobado que descomponer",
             "unassessable": "no evaluable: menos de dos tamaños calculados"}
REASONS_ES = {"short_window": "ventana por debajo de sweep.min_months",
              "weak_blocks": "demasiadas operaciones en bloques débiles"}
INTRO = (
    '<div class="note">Los tres modelos de colocación libre recolocan el ritmo de operar sobre '
    'toda la ventana del backtest, y con eso destruyen a la vez tres cosas: el <b>régimen</b> '
    'en que cae cada operación, su <b>calendario</b> y sus <b>rachas</b>. Aquí se vuelven a '
    'sortear dentro de bloques de calendario cada vez más cortos: cada operación sólo puede '
    'caer dentro de su propio bloque. Encoger el bloque devuelve el régimen y nada más, así '
    'que la curva separa qué parte del p es acierto y qué parte es herencia de régimen.</div>'
    '<div class="scroll"><table><tr><th>nulo</th><th>régimen</th><th>calendario</th>'
    '<th>rachas</th></tr>'
    '<tr><td>libre, ventana completa</td><td>destruido</td><td>destruido</td>'
    '<td>destruido</td></tr>'
    '<tr><td>libre, ventana encogiendo</td><td>← se restaura</td><td>destruido</td>'
    '<td>destruido</td></tr>'
    '<tr><td>Calendar Shift (referencia)</td><td>conservado</td><td>conservado</td>'
    '<td>conservado</td></tr></table></div>'
    '<div class="note"><b>Cómo se lee.</b> Si p se mantiene bajo al encoger, el acierto '
    'sobrevive aunque se le quite la suerte de régimen: es timing. Si p sube, el aprobado a '
    'ventana completa era herencia de régimen. <b>La curva nunca converge a Calendar '
    'Shift</b>: incluso con bloques cortos estos modelos siguen destruyendo calendario y '
    'rachas, que Calendar Shift conserva. Es otro eje; la línea naranja es una referencia, no '
    'un destino.<br><b>Léela siempre con las operaciones al lado.</b> Con bloques cortos hay '
    'menos sitio donde recolocar, el nulo se ensancha y p pierde resolución. Un tamaño en el '
    'que demasiadas operaciones caen en bloques con pocas operaciones o casi sin hueco libre '
    'no se calcula: sale como ✕, nunca como un número.</div>')


def _name(window: str) -> str:
    """A sweep window as the owner reads it.

    Args:
        window: A sweep.windows entry.

    Returns:
        "completa" for the whole window, "3 años" for 3y, "6 meses" for 6m.
    """
    if window == sweep.FULL:
        return "completa"
    count = int(window[:-1])
    words = {"y": ("año", "años"), "m": ("mes", "meses")}[window[-1]]
    return f"{count} {words[count != 1]}"


def power_table(sw: dict, model: str, alpha: float) -> str:
    """One model's sweep point by point, beside the counts that say how far to trust each p.

    Args:
        sw: What analysis.window_sweep() returned for one market.
        model: Which free-placement model.
        alpha: diagnostics.alpha, for colouring p.

    Returns:
        A scrollable table: blocks, real trades per block, the free room, the share of trades
        in weak blocks, the live trades per random run, the null's σ, and p — or why it was
        withheld.
    """
    head = tables._row(["ventana", "bloques (vacíos)", "ops/bloque mín · mediana",
                        "hueco libre, velas H1", "libre mín", "ops en bloques débiles",
                        "ops vivas por tirada", "σ del nulo", "p"], "th")
    body = []
    for window, point in zip(sw["windows"], sw["points"][model]):
        used = [b for b in window["blocks"] if b["trades"]]
        counts = [b["trades"] for b in used]
        p = (f'<span class="no">✕ {REASONS_ES[window["reason"]]}</span>' if point["p"] is None
             else f'<span class="chip-{"pass" if point["p"] <= alpha else "fail"}">'
                  f'{point["p"]:.4f}</span>')
        body.append(tables._row([
            _name(window["window"]),
            f'{len(window["blocks"])} ({len(window["blocks"]) - len(used)})',
            f"{min(counts)} · {np.median(counts):.0f}",
            f'{sum(b["free"] for b in window["blocks"]):,.0f}',
            f'{min(b["free_share"] for b in used):.0%}', f'{window["weak_share"]:.1%}',
            "—" if point["trades"] is None else f'{point["trades"]:,.0f} de {sum(counts):,}',
            "—" if point["sigma"] is None else f'{point["sigma"]:.4f}', p]))
    return f'<div class="scroll"><table>{head}{"".join(body)}</table></div>'


def blocks_detail(sw: dict) -> str:
    """Every block of every window size on one market: the counts behind the power table.

    Args:
        sw: What analysis.window_sweep() returned for one market.

    Returns:
        One collapsed section per size. Blocks depend on the real trades and the calendar,
        not on the model, so they are listed once per market rather than once per model.
    """
    head = tables._row(["bloque", "velas H1", "operaciones", "ocupadas H1", "libres H1",
                        "libre", ""], "th")
    out = []
    for window in sw["windows"]:
        rows = "".join(tables._row(
            [f'{b["start"]} → {b["end"]}', f'{b["bars"]:,.0f}', str(b["trades"]),
             f'{b["occupied"]:,.0f}', f'{b["free"]:,.0f}', f'{b["free_share"]:.0%}',
             "" if not weak else "vacío" if not b["trades"] else '<span class="no">débil</span>'])
            for b, weak in zip(window["blocks"], window["weak"]))
        out.append(f'<details><summary>Bloques de la ventana {_name(window["window"])} · '
                   f'{len(window["blocks"])}</summary><div class="scroll"><table>{head}{rows}'
                   f'</table></div></details>')
    return "".join(out)


def sweep_tab(record: dict, cfg: dict) -> str:
    """The window sweep on every market this strategy was analysed on.

    Args:
        record: What work.RESULTS holds.
        cfg: The configuration that run was made with.

    Returns:
        The tab's HTML: the decomposition it rests on, then per market one curve and one power
        table per swept model, each with its trend caption, and the blocks underneath.
    """
    s, alpha = cfg["sweep"], cfg["diagnostics"]["alpha"]
    floor = 1.0 / (1 + cfg["nulls"]["draws"])
    out = [INTRO]
    for feed, runs in record["runs"].items():
        sw = runs["sweep"]
        reference = (None if sw["reference"] is None
                     else {"name": panel.NAMES[s["reference"]], "p": sw["reference"]})
        out.append(f"<h2><code>{feed}</code></h2>")
        for model in s["models"]:
            points = [{"name": _name(w["window"]), "p": pt["p"],
                       "detail": f'≈{np.median([b["bars"] for b in w["blocks"]]):,.0f} velas H1'}
                      for w, pt in zip(sw["windows"], sw["points"][model])]
            out.append(f'<h3>{panel.NAMES[model]} <span class="tagline">'
                       f'{TRENDS_ES[sw["trend"][model]]}</span></h3>'
                       + figures.p_curve(points, reference, alpha, floor,
                                         f"p de «{metrics.LABELS['mean_r']}» según el tamaño "
                                         f"de bloque — {feed}")
                       + power_table(sw, model, alpha))
        out.append(blocks_detail(sw))
    return "".join(out)
