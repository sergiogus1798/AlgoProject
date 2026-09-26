# 50. Edge por operación y coste de breakeven

## Qué pregunta responde

De cada operación que hizo una estrategia, ¿cuánto ganó **antes** de pagar el spread y la
comisión, y a qué múltiplo de ese coste llegaría a empatar? SQX nunca exporta el bruto: sólo
el neto (`Profit/Loss`). Este módulo lo reconstruye operación a operación, con el `Size` real
de cada una — nunca un tamaño constante — y lo lee en dos unidades: cuántos "spreads" de
ventaja tiene de media (y de mediana, porque unos pocos ganadores grandes inflan la media), y
a qué coste de ida y vuelta llegaría a cero.

## Cuándo lo usas, y cuándo no

**Lo usas** en dos sitios del WORKFLOW: al final del paso 8, como criba sobre la población que
acaba de salir de la puerta OOS, y en el paso 25, al final de todo, sobre la versión de cada
estrategia que se va a operar (después del stop de ATR del paso 24).

**No lo uses para comparar activos entre sí** mientras sus costes en `assets/symbols/` sigan
marcados `PROVISIONAL`: el edge en spreads de USDJPY es enorme aquí porque su spread modelado
(`0.1` puntos) es un valor de fábrica de SQX, no el coste real de the5ers. El número es
correcto dado el coste que se le ha dado; el coste no está pactado con el bróker todavía.

**No decide nada por ti.** `min_edge_spreads` y `action` son del dueño (ver más abajo); el
módulo sólo mide y, si `action: drop`, escribe el veredicto que `curate` puede aplicar.

## Antes de empezar

- Para el paso 8: una cosecha ya hecha (`studies.screening.gate.harvest`) — este módulo no
  toca SQX, sólo lee `trades.parquet` y `metrics.parquet`.
- Para el paso 25: el export de trades de la versión final (misma forma de columnas).
- El feed tiene que tener un fichero en `assets/symbols/`: sin coste declarado, el módulo se
  niega (`ningún fichero de assets/symbols/ declara el feed …`).

## Cómo se ejecuta

```bash
python3 -m studies.readings.edgeCost.report --project USDJPY_emaCross_H1 --databank Results --feed USDJPY_DukasM1_the5ers
python3 -m studies.readings.edgeCost.report --project XAU_ISOOS_ejemplo --databank Results --feed XAUUSD_DukasM1_Infinox --strategy "Strategy 14.19.58"
```

| flag | obligatorio | qué hace |
|---|---|---|
| `--project`, `--databank` | sí | de qué cosecha lee (el databank de build); coge siempre la más reciente |
| `--feed` | sí | feed de SQX con el que se precia el coste, p. ej. `XAUUSD_DukasM1_Infinox` |
| `--strategy` | no | una sola estrategia, leída en detalle; sin él, toda la población |
| `--set` | no | cambia un umbral sin editar el fichero: `--set verdict.min_edge_spreads=3` |

**No toca SQX en absoluto.** Sobre 100-115 estrategias y 90.000-120.000 trades tarda segundos:
es un `groupby` de pandas, no una simulación.

## Qué produce

`~/Desktop/AlgoData/reports/<proyecto>/<databank>/<fecha>/edgeCost/`:

| fichero | qué es |
|---|---|
| `edgeCost.json` / `.html` / `.md` | el panel de la población: edge medio por estrategia, cuántas por debajo del umbral |
| `verdict.csv` | `strategy`, `edge_mean`, `edge_median`, `n`, `verdict` (MANTENER/DESCARTAR) |
| `estrategias/<nombre>.json` / `.html` | una estrategia: sus números, su reconciliación, su desglose por hora y día |
| `manifest.json` | de qué cosecha salió |

## Cómo se lee el resultado

Primero la reconciliación, siempre, antes de mirar ningún bruto — se imprime por pantalla:

```
reconciliación sobre toda la cosecha: corr 1.000000, n=92502
{
  "open_time": "2008-01-04 11:00:00",
  "type": "Buy",
  "open_price": 109.357,
  "close_price": 108.525,
  "size": 1.32,
  "reported_pnl": -718.16,
  "price_pnl": -718.1606549145545,
  "spread_cost": 0.43158693204000004,
  "commission_cost": 0.0,
  "gross": -717.72841306796
}
```

`price_pnl` sale de `(Close price - Open price) * Size * point_value` — nada más que los
precios de relleno que SQX ya exportó, que llevan el spread metido dentro. Contra
`Profit/Loss + comisión` da 1.000000 en USDJPY (92.502 trades) y 0.999553 en XAUUSD (118.257
trades) — los dos por encima del suelo de 0.99 que fijó `studies/readings/monkey/`. Por
debajo de ese suelo el módulo avisa (`reconciliation`, estado `watch`) y el bruto no se debe
usar hasta revisarlo.

**Un trade a mano**, el mismo de arriba: SQX reportó −718.16 $ netos en una compra de 1.32
lotes que entró a 109.357 y cerró a 108.525. El movimiento de precio solo es
`(108.525 − 109.357) × 1.32 × 653.919594 = −718.16` — coincide con lo reportado porque USDJPY
lleva comisión 0 hoy. El coste de spread que se le suma para llegar al bruto es
`0.5 × 0.1 × 0.01 × 653.919594 × 1.32 = 0.43`, así que el bruto de esa operación es
`−718.16 + 0 + 0.43 = −717.73`: perdió casi lo mismo en bruto que en neto, porque el spread
modelado de USDJPY es minúsculo.

Después, el panel de la población — una estrategia real de la cosecha, umbral en 2.0:

```
0 de 100 por debajo de 2.0 spreads (sólo marcadas).

Strategy 10.9.51    50.48   pass
Strategy 14.19.58   22.02   pass
Strategy 16.3.66     5.37   pass
```

Y una estrategia en detalle:

```
por encima del umbral (22.02) — Edge medio 22.02 spreads contra un umbral de 2.0
(no elimina, sólo marca); reconciliación 1.000000 sobre 791 operaciones.

| operaciones | bruto medio | bruto mediano | coste de hoy (medio) | edge medio (spreads) | edge mediano (spreads) | c* (múltiplo de hoy) | coste / edge |
|---|---|---|---|---|---|---|---|
| 791 | 20.03 | 14.71 | 0.9099 | 22.02 | 16.16 | 22.02 | 0.04542 |
```

`c*` es literalmente el mismo número que el edge medio: el coste de ida y vuelta al que la
ventaja empataría, expresado como múltiplo del coste de hoy — si el coste de hoy se
multiplicase por 22, esta estrategia empataría en bruto.

## El aviso que no se puede saltar

Cuando el activo es `no_forex` (oro, plata, los índices CFD), el resultado lleva siempre un
aviso `issue26`: la comisión porcentual de SQX puede cobrarse una vez por operación o una vez
por pata, sin medir (`OPEN.md` #26). Este módulo no lo resuelve — necesitaría un run de SQX
que no le corresponde lanzar — así que todo bruto de XAUUSD sale `costs_provisional`.

## Qué NO te dice

- **No es una curva Sharpe-contra-multiplicador-de-coste.** El MC Retest sortea el spread
  dentro de un rango, no en los multiplicadores discretos 1x/1.5x/2x/3x que pedía el encargo,
  y `SharpeRatio` no es una de las métricas que se pueden reconstruir de una simulación de MC
  Retest — se computa sobre la curva de equity diaria, que ningún fichero de simulación lleva
  (`studies/breakage/mcRetest/model/recon.py`). Es un hueco declarado, no una curva inventada.
- **No juzga si el coste modelado es el real.** Mientras `assets/symbols/<SYMBOL>.yaml` siga
  en `PROVISIONAL`, el edge en spreads mide contra un coste que el dueño aún no ha pactado con
  el bróker.
- **No decide el umbral.** `min_edge_spreads` está en `config.yaml` y en
  `ledger/thresholds.yaml`, puesto por el dueño antes de ver estos números.

## Si algo falla

- `ningún fichero de assets/symbols/ declara el feed …` — el `--feed` no tiene fichero de
  costes; sin coste declarado no hay bruto que reconstruir.
- La reconciliación por debajo de 0.99 — revisa el feed y el `point_value`: el bruto de ese
  resultado no se debe usar hasta corregirlo.
