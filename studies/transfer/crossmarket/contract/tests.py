"""The tabs of the tests that need no placement model: Timing Alpha and Exposure (1c)."""

import pandas as pd

from core.study import blocks, result as envelope
from core.symbols import alias
from studies.transfer.crossmarket.contract import shared, words

REFERENCE = {"block": "bloques de 6m"}


def reference_name(key: object) -> str:
    """How one of simulate/paired.py's reference windows reads; a number is a half-width."""
    return REFERENCE.get(key, f"centrada ±{key}m")


def paired_tab(record: dict) -> dict:
    """Timing Alpha: each trade against the exact mean of every same-length window around it."""
    rows, base = pd.DataFrame(record["rows"]), record["base"]
    return envelope.tab("paired", words.TEST_1B, [
        shared.bars(f"{words.TEST_1B} por operación, en puntos básicos",
                    [(r.feed, r.paired_bps) for r in rows.itertuples()], "bps", 0.0),
        {**blocks.table("El Alpha en todas sus unidades", pd.DataFrame(
            [[alias(r.feed), r.paired_bps, r.paired_pct, r.paired_r, r.paired_usd,
              r.paired_usd_total, 100 * r.paired_beat, r.paired_ci_lo * 1e4, r.paired_ci_hi * 1e4,
              r.paired_p]
             for r in rows.itertuples()],
            columns=["mercado", "Alpha (bps)", "Alpha (%)", "Alpha (R)", "USD / operación",
                     "Alpha acumulado (USD)", "Win Rate (%)", "CI 5 % (bps)",
                     "CI 95 % (bps)", "p (Wilcoxon)"]),
            f"Referencia: en el activo base {alias(base['feed'])}, donde se optimizó, p = "
            f"{base['paired_p']:.4f} con {base['paired_beat']:.1%} de operaciones ganando a su "
            f"ventana media. Eso dice que el código mide lo que dice medir, nada de la "
            f"estrategia."),
          "help": [None, None, None, None, None,
                   f"Cuánto de lo que ganó la estrategia lo puso el momento de entrar (el "
                   f"resultado de {words.TEST_1B}), y no el simple hecho de estar dentro del "
                   f"mercado. Suma el Alpha por operación en dólares sobre toda la muestra.",
                   None, None, None, None]},
        blocks.table("¿Depende de cómo se define «el mismo tramo»?", pd.DataFrame(
            [[alias(r.feed), reference_name(s["reference"])
              + (" (la de la tabla)" if s["reference"] == r.paired_reference else ""),
              s["bps"], s["usd_total"], 100 * s["beat_share"], s["p"]]
             for r in rows.itertuples() for s in r.paired_sensitivity],
            columns=["mercado", "referencia", "Alpha (bps)", "USD acumulado", "Win Rate (%)",
                     "p (Wilcoxon)"]),
            "Un p que sobrevive a las cuatro definiciones no depende de ella; uno que sólo "
            "sobrevive a una la tenía de muleta.")],
        note=f"Dado que esta estrategia iba a estar N velas dentro, ¿eligió N velas mejores que "
             f"las N velas medias de ese mismo tramo? El coste aparece en los dos lados y se "
             f"cancela: no dice si gana dinero, sólo si sus entradas eligen momento — mide "
             f"timing, no rentabilidad. Es el único test sin modelo nulo ni suposición de "
             f"coste. {words.TEST_1B} no lleva todavía ningún criterio de decisión (owner, "
             f"2026-09-30): se lee, no se juzga.")


def exposure_tab(record: dict) -> dict:
    """Test 1c: were the bars it occupied better than the market's average bar?"""
    rows = pd.DataFrame(record["rows"])
    return envelope.tab("exposure", "Exposición", [
        shared.bars("Exceso por vela sobre la vela media, por unidad de riesgo",
                    [(r.feed, r.risk_normalised) for r in rows.itertuples()], "", 0.0),
        {**blocks.table("A, E y sus intervalos", pd.DataFrame(
            [[alias(r.feed), r.risk_normalised, r.a, r.a_ci_lo, r.a_ci_hi, r.e,
              "no acotado" if not r.e_ci["bounded"] else
              f'[{r.e_ci["lo"]:+.2f}, {r.e_ci["hi"]:+.2f}]', r.mu_t, r.e_ci["sign_flip"]]
             for r in rows.itertuples()],
            columns=["mercado", "A / unidad de riesgo", "A (exceso por vela)", "A CI 5 %",
                     "A CI 95 %", "E", "CI 90 % de E (Fieller)", "deriva (t)",
                     "réplicas con deriva ≤ 0"])),
          "help": [None, "«A dividido unidad»: A expresado en unidades de la volatilidad "
                   "típica del mercado (el ATR mediano en la misma escala que A), para que "
                   "mercados de volatilidad distinta se comparen. Es el número que este panel "
                   "encabeza porque está siempre definido, a diferencia de E.",
                   None, None, None, None, None, None, None]}],
        note="Timing Alpha mide por operación contra el mismo tramo; Exposición mide por vela "
             "contra toda la muestra y no descuenta el régimen. A resta la vela media y existe "
             "siempre; E divide por ella y, donde la deriva no se distingue de cero, su "
             "intervalo sale no acotado.")
