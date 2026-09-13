"""What a button actually runs: analyse a strategy, analyse the database, write the report."""

from datetime import date
from types import SimpleNamespace

import pandas as pd

from core import manifest, trades as tradeio
from core.paths import report_dir
from strategies.crossmarket import (backtest, exposure, inference, panel, stress, tables,
                                    text, trade_models)
from strategies.crossmarket.explorer import analysis, cache, jobs

DRAWS = 5000
VERDICT_MODEL = "block_shift"   # the only model that randomises exactly one thing
SHOWN = 12          # strategies whose own tables are drawn in the static report
ADHOC: dict = {}    # a market/model re-run, kept aside from the stored analysis
DATABASE: dict = {} # the whole-database summary, filled by "Analizar toda la base de datos"


def default_cfg() -> dict:
    """The factory defaults for the config drawer, read from where each already lives.

    Returns:
        A flat, JSON-safe dict. Nothing here is written back to a file: the drawer only
        changes what one run holds in memory, same as monteCarlo's.
    """
    models = [VERDICT_MODEL, *[m for m in trade_models.MODELS if m != VERDICT_MODEL]]
    return {"draws": DRAWS, "models": models, "alpha": inference.ALPHA,
            "min_trades": inference.MIN_TRADES, "min_on_open": inference.MIN_ON_OPEN,
            "min_markets": inference.MIN_MARKETS, "correlated": inference.CORRELATED,
            "bootstrap_block": exposure.BLOCK, "bootstrap_draws": 2000,
            "cost_multiples": list(stress.DEFAULT_MULTIPLES), "bar_shift": 1,
            "slippage_fractions": [0.1, 0.25, 0.5]}


def analyse(setup: dict, cfg: dict, name: str) -> dict:
    """Analyse one strategy on every additional market. "Analizar esta estrategia".

    Args:
        setup: What serve.main() assembled.
        cfg: The run configuration.
        name: Strategy name.

    Returns:
        A short summary for the log line; the full record goes to the cache.
    """
    with analysis.overridden(cfg):
        record = analysis.analyse_strategy(setup, cfg, name, on_market=jobs.advance)
    cache.save(setup["project"], setup["databank"], name, record, cfg)
    return {"strategy": name, **record["verdict"]}


def analyse_all(setup: dict, cfg: dict) -> dict:
    """Analyse every strategy in the export. "Analizar toda la base de datos".

    Args:
        setup: What serve.main() assembled.
        cfg: The run configuration.

    Returns:
        A short summary; the per-strategy table lands in DATABASE for the headline strip.
    """
    with analysis.overridden(cfg):
        for name in setup["strategies"]:
            record = analysis.analyse_strategy(setup, cfg, name)
            cache.save(setup["project"], setup["databank"], name, record, cfg)
            jobs.advance(f"estrategia {name}")
        table = pd.DataFrame([{"strategy": n, **cache.load(setup["project"], setup["databank"],
                                                           n, cfg)["body"]["verdict"]}
                             for n in setup["strategies"]])
        luck = inference.false_passes(int(table["markets"].median()), len(table))
    DATABASE.clear()
    DATABASE.update({"table": table.to_dict("records"), "luck": luck,
                     "kept": int((table["verdict"] == inference.VERDICTS[0]).sum())})
    return {"strategies": len(setup["strategies"]), "kept": DATABASE["kept"]}


def rerun(setup: dict, name: str, market: str, model: str, draws: int) -> dict:
    """Re-run one (market, model) pair with its own draw count, on its own.

    Args:
        setup: What serve.main() assembled.
        name: Strategy name.
        market: Market feed.
        model: A key of trade_models.MODELS.
        draws: Draws for this run only.

    Returns:
        The shape and p-value. Kept in ADHOC, never in the cache: a single re-run must not
        overwrite or be mistaken for the stored analysis.
    """
    price = setup["bars"][market]
    real = tradeio.read(setup["trades"] / market / f"{name}.csv")
    out = backtest.run(real, price, draws, model)
    located = inference.locate(out["real"], out["null"])
    result = {"shape": inference.shape(out["real"], out["null"]), "p": located["p"]}
    ADHOC.setdefault(name, {})[f"{market}|{model}"] = result
    return result


def page(meta: SimpleNamespace, per_market: pd.DataFrame, calls: pd.DataFrame, luck: dict,
        shapes: dict, records: dict) -> str:
    """The illustrated static report, in reading order — byte-for-byte what the panel shows.

    Args:
        meta: project, databank, asset, export, models — the run's identity and the models
            "Analizar toda la base de datos" was run with.
        per_market: Every (strategy, market) row across the whole database.
        calls: One row per strategy.
        luck: What inference.false_passes() returned.
        shapes: {"strategy|market": the verdict model's shape}.
        records: {strategy: what cache.load()'s "body" holds}, for the correlation/PCA figures.

    Returns:
        A self-contained HTML page.
    """
    title = f"Retest en mercados adicionales — {meta.project} / {meta.databank}"
    top = calls.sort_values(["beaten", "edge_r"], ascending=False)["strategy"].head(SHOWN)
    shown = per_market[per_market["strategy"].isin(top)]
    corr_figs = "".join(tables.correlation_section(records[s]["correlation"], records[s]["pca"])
                        for s in top)
    return panel.render(title, [
        f"<h1>{title}</h1>",
        f'<p class="lede">Activo base <code>{meta.asset}</code> · export {meta.export}. '
        f'Generado por el panel, no por línea de comandos: '
        f'<code>strategies.crossmarket.explorer.serve</code>.</p>',
        panel.headline(per_market, calls, luck), panel.luck_note(calls, luck),
        "<h2>Por mercado</h2>", panel.market_table(per_market),
        "<h2>Estrategia a estrategia — Test 1a</h2>",
        panel.per_strategy(per_market, shapes, meta.models),
        "<h2>Test 1c — retorno ajustado por exposición</h2>", tables.exposure_table(shown),
        "<h2>Significancia y amplitud</h2>", tables.significance_table(shown),
        "<h2>Huella conductual</h2>", tables.fingerprint_table(shown),
        "<h2>Robustez de coste y ejecución</h2>", tables.cost_table(shown),
        "<h2>Correlación y PCA</h2>", corr_figs,
        "<h2>Comprobaciones</h2>", panel.diagnostics(per_market), panel.glossary(meta.models),
        f"<footer>{meta.project} / {meta.databank} · semilla {backtest.SEED} · "
        f"generado por <code>strategies.crossmarket.explorer.serve</code></footer>"])


def report(setup: dict, cfg: dict) -> dict:
    """Write by_market.csv, verdict.csv, crossmarket.md and crossmarket.html for the whole
    database, from what "Analizar toda la base de datos" already cached.

    Args:
        setup: What serve.main() assembled.
        cfg: The run configuration.

    Returns:
        Where the files landed.

    Raises:
        RuntimeError: A strategy has no cached result under this configuration — the button
        asks for "Analizar toda la base de datos" first rather than computing anything itself.
    """
    records = {}
    for name in setup["strategies"]:
        record = cache.load(setup["project"], setup["databank"], name, cfg)
        if record is None or record["stale"]:
            raise RuntimeError(f"{name}: falta «Analizar toda la base de datos» con esta "
                              "configuración antes de generar el informe")
        records[name] = record["body"]

    per_market = pd.concat([pd.DataFrame(b["rows"]).assign(strategy=n)
                            for n, b in records.items()], ignore_index=True)
    calls = pd.DataFrame([{"strategy": n, **b["verdict"]} for n, b in records.items()])
    with analysis.overridden(cfg):
        luck = inference.false_passes(int(calls["markets"].median()), len(calls))

    out = report_dir(setup["project"], setup["databank"], date.today().isoformat()) / "crossmarket"
    out.mkdir(parents=True, exist_ok=True)
    per_market.to_csv(out / "by_market.csv", index=False)
    calls.to_csv(out / "verdict.csv", index=False)
    meta = SimpleNamespace(project=setup["project"], databank=setup["databank"],
                           asset=setup["args"].asset, export=setup["args"].export,
                           draws=cfg["draws"], models=cfg["models"])
    (out / "crossmarket.md").write_text(
        text.render(meta, setup["spec"], per_market, calls, luck), encoding="utf-8")
    shapes = {f"{n}|{market}": model_shapes[meta.models[0]]
             for n, b in records.items() for market, model_shapes in b["shapes"].items()}
    (out / "crossmarket.html").write_text(page(meta, per_market, calls, luck, shapes, records),
                                          encoding="utf-8")
    manifest.write(out, {"project": setup["project"], "databank": setup["databank"],
                         "asset": meta.asset, "export": meta.export, "draws": cfg["draws"],
                         "seed": backtest.SEED, "models": cfg["models"]},
                   f"strategies.crossmarket.explorer.serve --project {setup['project']} "
                   f"--databank {setup['databank']} --asset {meta.asset} --export {meta.export}",
                   {"strategies": len(calls), "markets": len(setup["spec"]["additional"]),
                    **calls.verdict.value_counts().to_dict()})
    return {"path": str(out)}
