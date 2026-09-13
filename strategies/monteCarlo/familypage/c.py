"""Family C's section: execution luck — worse fills, worse costs, missed entries."""

from strategies.monteCarlo import charts, gates, overlay, panel, stress
from strategies.monteCarlo.familypage.common import MODELS_ES, family_header


def family_c(result: dict, verdict: dict, cfg: dict) -> list[str]:
    """Execution luck: worse fills, worse costs, missed entries.

    Args:
        result: What run.analyse() returned.
        verdict: What scoring.verdict() returned.
        cfg: What config.load() returned.

    Returns:
        The section's HTML blocks.
    """
    q = cfg["global"]["report_percentile"]
    fired = {f["test"] for f in gates.check(result, cfg) if f["family"] == "C"}
    rows = [[stress.TITLES[name], f"{v['median_net']:,.0f} $", f"{v['keep']:.0%}",
             f"{v['net_5']:,.0f} $", f"{v['pf_5']:.2f}",
             '<span class="no">falla</span>' if name in fired
             else '<span class="ok">pasa</span>']
            for name, v in result["C"].items()]
    intro = "".join(f"<li><b>{stress.TITLES[k]}</b> — {v}</li>" for k, v in MODELS_ES.items())
    figs = "".join(
        charts.distribution(v["shapes"]["net"], f"Beneficio neto — {stress.TITLES[k]}", "",
                            "Beneficio neto de la simulación, en $")
        + overlay.section(result["degrade"][f"C.{k}"],
                          f"{stress.TITLES[k]} — IS vs OOS",
                          "Beneficio neto de la simulación, en $", q)
        for k, v in result["C"].items())
    return [
        "<h2>Familia C — suerte de ejecución</h2>",
        family_header("C", verdict),
        '<p class="lede">Las mismas operaciones peor ejecutadas. Las cuatro tienen que pasar: '
        'no se promedian, y las cuatro se ejecutan siempre, aunque alguna ya haya fallado — '
        'igual que todas las demás pruebas del informe.</p>',
        f"<ul>{intro}</ul>",
        panel.table(["Prueba", "Beneficio mediano", "Queda", "Beneficio p5", "PF p5", ""],
                    rows),
        figs]
