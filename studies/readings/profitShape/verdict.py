"""What each measurement means, against thresholds fixed before the trades are read."""

MEANS = {
    "few_trades": "el resultado lo sostienen unas pocas operaciones",
    "few_periods": "el resultado lo sostiene un tramo corto del calendario",
    "spread": "el beneficio está repartido entre operaciones y periodos",
    "independent": "nada contradice que las operaciones sean independientes",
    "clustered": "las operaciones se agrupan: remuestrearlas sueltas subestima la caída",
    "stable": "nada indica que la media haya cambiado dentro de la muestra",
    "broke": "la media cambia dentro de la muestra, y el tramo posterior es el que describe hoy",
}


def concentration(found: dict, cfg: dict) -> str:
    """Whether the result survives losing its best trades and its best year.

    Args:
        found: What `concentration.time_concentration` returned, plus `top5` and `median`.
        cfg: The `verdict` block of config.yaml.

    Returns:
        One key of MEANS. Two independent ways to be concentrated -- a few trades and a
        few months -- and either one earns the label, because they fail for different
        reasons and a strategy only needs one of them to be fragile.
    """
    if found["top5"] >= cfg["max_top5"] or found["median"] <= 0 < found["mean"]:
        return "few_trades"
    if (found["best_months"] >= cfg["max_best_months"]
            or found["without_best_year"]["expectancy"] <= 0):
        return "few_periods"
    return "spread"


def dependence(runs: dict, box: dict, streak: dict, cfg: dict) -> str:
    """Whether the trade sequence may be resampled as independent draws.

    Args:
        runs: What `dependence.runs` returned.
        box: What `dependence.ljung_box` returned.
        streak: What `dependence.streak` returned.
        cfg: The `verdict` block of config.yaml.

    Returns:
        One key of MEANS. Any of the three is enough: they look at clustering of signs, at
        autocorrelation of sizes, and at the tail of the run-length distribution, and a
        series can fail one while passing the others.
    """
    hit = (runs["z"] <= -cfg["min_runs_z"] or box["p"] <= cfg["alpha"]
           or streak["p"] <= cfg["alpha"])
    return "clustered" if hit else "independent"


def structure(found: dict) -> str:
    """Whether a break in the mean is rejected.

    Args:
        found: What `breaks.cusum` returned.

    Returns:
        One key of MEANS.
    """
    return "broke" if found["rejects"] else "stable"
