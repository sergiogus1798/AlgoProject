"""The joint null across a strategy's out-of-sample markets: one statistic, one p.

The per-market tests answer "did the timing carry information *here*". The question the
retest exists for is whether it carries across markets, and counting how many markets came in
under alpha does not answer it: the per-market p-values are **dependent** — they are computed
on the same draws, on markets that move together — so combining them as if they were
independent (Fisher, Stouffer, or a vote) is anti-conservative exactly when it matters.

One a-priori statistic, one p. `trade_models.block_shift` draws one displacement per calendar
semester and applies it in every market, so draw d is one coupled counterfactual of the whole
set; pooling it needs no correlation matrix, because the resampling already carries whatever
correlation there is."""

import numpy as np

REASONS = {"one_market": "hace falta más de un mercado fuera de muestra",
           "uneven_draws": "los mercados se corrieron con distinto número de tiradas",
           "no_draws": "esta sesión no guardó los sorteos por mercado"}


def pooled(values: dict[str, np.ndarray], real: dict[str, float], pool: str) -> tuple:
    """The equal-weight statistic, over raw values or over each market's own z.

    Args:
        values: {feed: mean_r of every draw on that market}, all the same length.
        real: {feed: the real backtest's mean_r there}.
        pool: "mean_r" to average the raw statistic, "z" to average each market's own
            standardised one.

    Returns:
        (T_real, T_null): the pooled real statistic and one pooled value per draw. Equal
        weight per market, because each out-of-market is one vote that the edge generalises;
        weighting by trade count would let the busiest market decide alone. Raw `mean_r` is
        the default and is right while the markets' null spreads sit within a small factor of
        each other — measured 0.1236 against 0.1026, a factor of 1.20. Pool over z when one
        market's spread is several times another's, or it silently decides the verdict.
    """
    feeds = sorted(values)
    if pool == "z":
        sd = {f: values[f].std(ddof=1) or 1.0 for f in feeds}
        mu = {f: float(values[f].mean()) for f in feeds}
        real_t = float(np.mean([(real[f] - mu[f]) / sd[f] for f in feeds]))
        null_t = np.mean([(values[f] - mu[f]) / sd[f] for f in feeds], axis=0)
        return real_t, null_t
    return (float(np.mean([real[f] for f in feeds])),
            np.mean([values[f] for f in feeds], axis=0))


def run(runs: dict, cfg: dict) -> dict:
    """One p for the whole out-of-sample set, under the coupled null.

    Args:
        runs: {feed: what analysis produced for that market} — the base asset is not in here,
            and must not be: on the market it was optimised on a strategy beats its null by
            construction, so including it would import a guaranteed pass into the pool.
        cfg: What config.load() returned.

    Returns:
        The pooled real statistic, the null's median and spread, p, the markets pooled and
        how many draws each contributed — or `reason` saying why it was withheld, and never a
        number in its place. p adds one to numerator and denominator, like every other p in
        this study, so a set that beats every draw reports the resolution of the test.
    """
    model, pool = cfg["nulls"]["headline"], cfg["joint"]["pool"]
    have = {f: r[model] for f, r in runs.items() if model in r and "mean_r_draws" in r[model]}
    sizes = {len(v["mean_r_draws"]) for v in have.values()}
    reason = ("no_draws" if not have else "one_market" if len(have) < 2
              else "uneven_draws" if len(sizes) > 1 else None)
    if reason:
        return {"reason": reason, "markets": sorted(have), "pool": pool, "model": model}
    values = {f: np.asarray(v["mean_r_draws"]) for f, v in have.items()}
    real = {f: v["table"]["mean_r"]["observed"] for f, v in have.items()}
    real_t, null_t = pooled(values, real, pool)
    return {"reason": None, "markets": sorted(have), "pool": pool, "model": model,
            "draws": int(next(iter(sizes))), "observed": real_t,
            "median": float(np.median(null_t)), "std": float(null_t.std(ddof=1)),
            "z": float((real_t - null_t.mean()) / (null_t.std(ddof=1) or np.nan)),
            "beats": float(np.mean(null_t < real_t)),
            "p": float((1 + np.sum(null_t >= real_t)) / (1 + null_t.size))}


def block(view: dict, alpha: float) -> str:
    """The joint null as the panel shows it: one headline, or the reason there is none.

    Args:
        view: What run() returned.
        alpha: diagnostics.alpha, for colouring p. It decides nothing here either.

    Returns:
        A stat block plus the sentence that says what it is a test of. Deliberately one
        number and not a per-market grid: the point of pooling is that there is a single
        a-priori statistic to read, and a reader offered several will pick the best one.
    """
    names = ", ".join(f"<code>{m}</code>" for m in view["markets"]) or "ninguno"
    if view["reason"]:
        return (f'<div class="note"><b>Sin p conjunto.</b> {REASONS[view["reason"]]}. '
                f'Mercados disponibles: {names}.</div>')
    colour = "ok" if view["p"] <= alpha else "no"
    return (f'<div class="headline">'
            f'<div class="stat"><b class="{colour}">{view["p"]:.4f}</b>'
            f'<span>p conjunto, {len(view["markets"])} mercados fuera de muestra</span></div>'
            f'<div class="stat"><b>{view["z"]:+.2f}</b><span>z del conjunto</span></div>'
            f'<div class="stat"><b>{view["observed"]:+.4f}</b>'
            f'<span>estadístico real agrupado</span></div>'
            f'<div class="stat"><b>{view["median"]:+.4f}</b>'
            f'<span>mediana del nulo conjunto</span></div>'
            f'<div class="stat"><b>{view["beats"]:.1%}</b>'
            f'<span>sorteos conjuntos batidos</span></div></div>'
            f'<div class="note"><b>Qué es este número.</b> Un solo estadístico decidido de '
            f'antemano — la media de <code>mean_r</code> sobre {names}, un voto por mercado — '
            f'medido contra {view["draws"]:,} sorteos en los que <b>el mismo desplazamiento '
            f'de calendario se aplica a todos los mercados a la vez</b>. Por eso está bien '
            f'dimensionado sin modelar ninguna matriz de correlación: el remuestreo ya lleva '
            f'dentro la dependencia que haya entre los mercados. <b>No</b> es la combinación '
            f'de los p por mercado: combinarlos con Fisher o por votación supondría que son '
            f'independientes, que es justo lo que este test no supone. El activo base no '
            f'entra — ahí la estrategia bate a su nulo por construcción. Modelo: '
            f'<code>{view["model"]}</code>; agregación: <code>{view["pool"]}</code>.</div>')
