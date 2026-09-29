# 34 · Validación en MT5 con la feed de cada empresa, y el pool de estrategias validadas — encargo autocontenido

**Tu oficio:** Python sobre `mt5/` y `portfolio/`, con MT5 bajo Wine.
**Tu encargo es el paso 26 del WORKFLOW: la puerta entre la estrategia individual y la cartera.**
Una estrategia que ha superado los pasos 1-25 se backtestea en MT5 con la feed de cada empresa de
fondeo; si ese backtest coincide con el de SQX según un criterio fijado de antemano, entra en el
**pool de estrategias validadas** para esa empresa, y sólo de ese pool lee el módulo de cartera.

Lee `CLAUDE.md` · `CODESTYLE.md` · `mt5/README.md` (y `mt5/compare.py`) · `OPEN.md` #78 ·
`docs/AgentPDFs/WORKFLOW.md` · `knowhow/export/feed-clock-timezones.md` · `portfolio/CLAUDE.md` ·
`portfolio/funded/catalog/README.md` · `core/archive/` · `docs/encargos/33-economia-del-fondeo.md`.

---

## 0 · De dónde sale

El dueño, 2026-09-29. Las empresas de fondeo tienen en MT5 mucho menos histórico que SQX. La idea:
backtestear con la feed de cada empresa, ver cuánto se parece a SQX en el tramo común y, si se
parece, dar por bueno el histórico largo de SQX para esa empresa. Sobre el orden: **todo lo que usa
`oos2` para desarrollar la estrategia se hace antes, en los pasos 1-25.** Sólo después, con la
estrategia dada por buena, llega esta validación. Como el tramo de la feed de fondeo cae casi
entero en `oos2`, y `oos2` ya se ha gastado en el desarrollo cuando se llega aquí, esta puerta no
elige estrategias por su rendimiento: sólo comprueba que SQX reproduce la cuenta de la empresa.

## 1 · Qué se compara, y por qué no basta el beneficio total

Dos backtests pueden sumar lo mismo en dos años y tener días muy distintos. Las reglas de una
fondeada leen **días** (pérdida diaria sobre el día del servidor) y **caminos** (pérdida máxima,
intradía, sobre flotante). Así que se compara lo que las reglas leen, por estrategia × empresa,
sobre el tramo en que las dos fuentes tienen datos:

| # | qué | cómo |
|---|---|---|
| 1 | coincidencia de operaciones | % de operaciones de SQX emparejadas en MT5 (mismo lado, entrada dentro de una tolerancia en minutos) — `mt5.compare.pair` |
| 2 | P&L por operación | diferencia media y su dispersión sobre las emparejadas, en R o en % de la cuenta |
| 3 | P&L diario en el día del servidor de la empresa | correlación entre las dos series diarias y diferencia media absoluta, en % de la cuenta |
| 4 | peor día | peor día de cada lado, en % de la cuenta |
| 5 | drawdown intradía máximo sobre flotante | el de cada lado, con la equity reconstruida con M1 |

Antes de comparar, **SQX se traduce a la cuenta de la empresa** (§2): comparar sin traducir mide
la diferencia de reloj y de costes, no la fidelidad.

## 2 · La traducción del histórico de SQX a cada empresa

Es la pieza que después usa el encargo 33 sobre el histórico entero:

1. **Reloj**: las horas de SQX están en la zona de su feed (`sqx.inspect.feeds.timezone`); se pasan
   a la del servidor de la empresa (Hantec: medianoche de su servidor; FTMO: CE(S)T). El día de la
   regla de pérdida diaria es el del servidor, no el de SQX.
2. **Costes**: spread, comisión y swap de la cuenta de esa empresa, medidos en su feed MT5 (el
   símbolo, su sufijo, su especificación), en vez de los de `assets/`.
3. **Flotante intradía**: la equity minuto a minuto con las barras M1, para el drawdown intradía y
   la pérdida diaria sobre equity.

## 3 · El veredicto

Por estrategia × empresa: **validada** o **no validada, con la causa** (qué fila de §1 falla). Si
falla, se diagnostica (casi siempre el reloj o un coste), se corrige la traducción y se vuelve a
comparar **una vez**; si sigue fallando, esa estrategia no entra en el pool de esa empresa. Cada
comparación deja su fila en el ledger.

**Los umbrales son parámetros de entrada, no constantes** (dueño, 2026-09-29): cada uno es una
fila de `ledger/thresholds.yaml` y el `config.yaml` del módulo lleva `ledger:<clave>` en su sitio
(`knowhow/eng/thresholds-live-in-the-ledger.md`); una corrida puede cambiarlos con `--set`. El dueño
aceptó estos valores de partida:

| # | umbral | valor de partida |
|---|---|---|
| 1 | operaciones emparejadas · tolerancia de entrada | ≥ 95 % · 1 barra del timeframe |
| 2 | diferencia media por operación | ≤ 0,05 R |
| 3 | P&L diario: correlación · diferencia media absoluta | ≥ 0,95 · ≤ 0,1 % de la cuenta |
| 4 | peor día | diferencia ≤ 0,5 puntos de % |
| 5 | drawdown intradía máximo | diferencia relativa ≤ 10 % |

Cambiarlos después de ver un resultado está permitido — el dueño lo sabe y lo quiere así — pero no
es gratis: cada corrida guarda los umbrales con los que se juzgó, y el ledger cuenta las repeticiones
de la misma estrategia con otros umbrales como ensayos (encargo 32). El pool guarda el veredicto con
los umbrales vigentes al darlo.

## 4 · El pool

Un registro en `AlgoData/pool/` (formato a decidir con el dueño; que el catálogo de fondeo use
SQLite es un precedente, no una obligación), una fila por estrategia × empresa: la identidad y
versión del archivo (`AlgoData/archive/<identity>/<version>/`), la empresa y su símbolo, el tramo
comparado, las cinco cifras, los umbrales vigentes, el veredicto y la fecha. Una estrategia puede
estar validada para Hantec y no para FTMO: el pool es **por empresa**. El módulo de cartera y el
encargo 33 **sólo** leen estrategias validadas, y del pool sacan también la traducción de §2.

Una versión nueva de la estrategia en el archivo (otro stop, otros parámetros) no hereda la
validación: se valida otra vez.

## 5 · Entregables

1. La traducción de §2 (reloj, costes de la empresa, flotante M1) como función reutilizable.
2. La comparación de §1 sobre `mt5.compare` (que ya empareja operaciones), más el P&L diario en el
   día del servidor, el peor día y el drawdown intradía.
3. El veredicto con los umbrales del dueño, escrito en el ledger y en el pool.
4. El pool y su lectura para `portfolio/`; la zona PORTFOLIOS de la ventana lista sólo lo validado.
5. El capítulo del manual (regla 8) y las cards de `knowhow/` que salgan.

**Depende de** OPEN.md #78: el primer backtest de MT5 bajo Wine y que su informe traiga todas las
operaciones. **Hecho es:** una superviviente real de los 25 pasos, backtesteada con la feed de
Hantec, con su veredicto y su fila en el pool.
