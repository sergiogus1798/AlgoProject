"""The panel's per-strategy tabs, rendered by the same functions everywhere."""

import pandas as pd

from strategies.crossmarket import figures, panel, tables
from strategies.crossmarket.explorer import simulations


def _rows(record: dict) -> pd.DataFrame:
    """The strategy's per-market rows as a frame, for every renderer here.

    Args:
        record: What work.RESULTS holds for one strategy.

    Returns:
        One row per market analysed, base asset excluded.
    """
    return pd.DataFrame(record["rows"])


def summary_tab(record: dict, cfg: dict) -> str:
    """The per-market result of every test, and the mechanical checks under it.

    Args:
        record: What work.RESULTS holds.
        cfg: The configuration that run was made with.

    Returns:
        The tab's HTML. No verdict: the table says what each market did and how many reasons
        there are to distrust it, and the reading is the owner's.
    """
    rows, s = _rows(record), record["summary"]
    head = (f'<div class="headline">'
            f'<div class="stat"><b>{s["under_alpha"]}/{s["markets"]}</b>'
            f'<span>mercados bajo alpha (1a)</span></div>'
            f'<div class="stat"><b>{s["paired_under_alpha"]}/{s["markets"]}</b>'
            f'<span>mercados bajo alpha (1b)</span></div>'
            f'<div class="stat"><b>{s["edge_r"]:+.3f}</b><span>ventaja mediana</span></div>'
            f'<div class="stat"><b>{s["family"]}</b><span>qué se está probando</span></div>'
            f'<div class="stat"><b>{s["warnings"]}</b><span>avisos en total</span></div></div>')
    absent = ('<div class="note"><b>Sin operaciones en '
              + ", ".join(f"<code>{f}</code>" for f in record["missing"])
              + ".</b> Esta estrategia no llegó a disparar ni una vez ahí, así que ese mercado "
                "no tiene fila. Es un resultado sobre la estrategia, no un dato que falte."
                "</div>" if record["missing"] else "")
    return (head + absent + "<h3>Por mercado</h3>" + panel.market_table(rows)
            + "<h3>Comprobaciones</h3>" + panel.diagnostics(rows))


def warnings_tab(record: dict, cfg: dict) -> str:
    """Every reason to distrust each market's numbers.

    Args:
        record: What work.RESULTS holds.
        cfg: The configuration that run was made with.

    Returns:
        The tab's HTML.
    """
    return ('<div class="note">Ningún mercado se excluye por esto. Un aviso es contexto para '
            'leer el número, no una razón para esconderlo.</div>'
            + tables.warnings_block(_rows(record), panel.WARNINGS_ES))


def paired_tab(record: dict, cfg: dict) -> str:
    """Test 1b across the strategy's markets.

    Args:
        record: What work.RESULTS holds.
        cfg: The configuration that run was made with.

    Returns:
        The tab's HTML, with the base asset's own paired result shown as the reference.
    """
    base = record["base"]
    note = (f'<div class="note">Referencia — en el activo base <code>{base["feed"]}</code>, '
            f'donde la estrategia fue optimizada, el test pareado da p = {base["paired_p"]:.4f} '
            f'con {base["paired_beat"]:.1%} de operaciones ganando a su ventana media. Eso dice '
            f'que el código mide lo que dice medir, y nada sobre la estrategia.</div>')
    return (figures.bars_by_market(
        [{"market": r["feed"], "paired_mean": r["paired_mean"]} for r in record["rows"]],
        "paired_mean", "Alfa medio por operación frente a su ventana ciega", rule=0.0)
        + tables.paired_table(_rows(record)) + note)


def exposure_tab(record: dict, cfg: dict) -> str:
    """Test 1c across the strategy's markets.

    Args:
        record: What work.RESULTS holds.
        cfg: The configuration that run was made with.

    Returns:
        The tab's HTML. A drops the market's own drift out, so it is charted rather than E,
        which exists only where that drift is real.
    """
    return (figures.bars_by_market(
        [{"market": r["feed"], "a": r["a"]} for r in record["rows"]],
        "a", "Exceso por vela sobre la vela media del mercado (A)", rule=0.0)
        + tables.exposure_table(_rows(record)))


def significance_tab(record: dict, cfg: dict) -> str:
    """Significance and breadth across the strategy's markets.

    Args:
        record: What work.RESULTS holds.
        cfg: The configuration that run was made with.

    Returns:
        The tab's HTML.
    """
    return tables.breadth_block(record["summary"]) + tables.significance_table(_rows(record))


def fingerprint_tab(record: dict, cfg: dict) -> str:
    """Behavioural fingerprint against the base asset.

    Args:
        record: What work.RESULTS holds.
        cfg: The configuration that run was made with.

    Returns:
        The tab's HTML.
    """
    return tables.fingerprint_table(_rows(record))


def drivers_tab(record: dict, cfg: dict) -> str:
    """What kind of market each one is — the structural properties of PDF section 5.4.

    Args:
        record: What work.RESULTS holds.
        cfg: The configuration that run was made with.

    Returns:
        The tab's HTML, with the note that says why there is no regression here yet.
    """
    return (tables.drivers_table(_rows(record), record["base"])
            + '<div class="note">Estas propiedades describen el <b>mercado</b>, no la '
              'estrategia. La regresión que convierte «funciona aquí y no allí» en «funciona '
              'en mercados con tal propiedad» necesita seis mercados o más; con dos, esto es '
              'una descripción de dónde se trasladó el acierto y dónde no.</div>')


def correlation_tab(record: dict, cfg: dict) -> str:
    """Correlation matrix and PCA across the strategy's markets plus the base asset.

    Args:
        record: What work.RESULTS holds.
        cfg: The configuration that run was made with.

    Returns:
        The tab's HTML, warned when PC1 says the markets are one bet.
    """
    warn = ('<div class="fail">PC1 explica más del '
            f'{cfg["diagnostics"]["pca_warn"]:.0%} de la varianza: estos mercados son una sola '
            'apuesta, no varias confirmaciones independientes.</div>'
            if record["pca"]["pc1"] > cfg["diagnostics"]["pca_warn"] else "")
    return warn + tables.correlation_section(record["correlation"], record["pca"])


def glossary_tab(record: dict, cfg: dict) -> str:
    """What every number on the page means.

    Args:
        record: What work.RESULTS holds.
        cfg: The configuration that run was made with.

    Returns:
        The closing section; none of these quantities explains itself.
    """
    return panel.glossary(cfg["nulls"]["models"])


TABS = [("summary", "Resumen"), ("random", "Entrada aleatoria (1a)"),
        ("models", "Modelos"), ("paired", "Pareado (1b)"), ("exposure", "Exposición (1c)"),
        ("stress", "Coste y ejecución"), ("significance", "Significancia"),
        ("fingerprint", "Huella"), ("drivers", "El mercado"),
        ("correlation", "Correlación"), ("warnings", "Avisos"), ("glossary", "Glosario")]
RENDER = {"summary": summary_tab, "random": simulations.random_tab,
          "models": simulations.models_tab, "stress": simulations.stress_tab,
          "paired": paired_tab, "exposure": exposure_tab,
          "significance": significance_tab, "fingerprint": fingerprint_tab,
          "drivers": drivers_tab, "correlation": correlation_tab, "warnings": warnings_tab,
          "glossary": glossary_tab}


def section(name: str, record: dict, cfg: dict) -> str:
    """One tab's HTML, for the strategy the panel is showing.

    Args:
        name: A key of RENDER.
        record: What work.RESULTS holds.
        cfg: The configuration that run was made with.

    Returns:
        The tab's content.
    """
    return RENDER[name](record, cfg)
