## 42. La calidad de la entrada — ¿la señal vale algo por sí sola?

### Qué pregunta responde

Una estrategia gana por tres cosas mezcladas: cuándo entra, cuándo sale, y que el mercado se moviera.
Este comando aísla **la primera**, y lo hace sin volver a correr nada en SQX: coge cada entrada,
camina las velas hacia delante y mide cuánto corrió el precio a favor y cuánto en contra, ignorando
por completo las salidas de la estrategia.

Dos preguntas:

1. **¿Predice la entrada movimiento favorable?** Se compara el recorrido a favor contra el recorrido
   en contra (el *e-ratio*), y ese número se contrasta contra **entradas al azar a las mismas horas
   y con la misma proporción de largos**. Si tu curva cae dentro de la banda del azar, la entrada no
   aporta: lo que ganas viene de las salidas o de la deriva del mercado.
2. **¿Cuánto edge se pierde llegando tarde?** Si entrar una vela después se lleva media ventaja,
   o el sistema es frágil a la latencia, o hay información del futuro metida en la señal.

### Cuándo lo usas, y cuándo no

**Lo usas** cuando quieres saber qué parte de la estrategia es la señal. Es el complemento natural
del test del mono (`26-nulos.md`): aquél pregunta si el resultado bate al azar, éste **dónde vive**
la diferencia.

**No lo uses para descartar sin más.** Una estrategia puede salir `no_signal` y ser rentable: lo que
te está diciendo es que su ventaja está en la salida o en la deriva, y eso es un objeto distinto que
hay que reconocer, no necesariamente uno malo.

**No sirve si la estrategia lleva stop o target** para la parte del retraso. Ahí las salidas se
mueven con la entrada y el tier 1 deja de valer; hace falta el simulador de replay, que todavía no
existe (`docs/encargos/16-replay-de-operaciones.md`). La población XAUUSD actual no lleva ninguno,
por eso aquí sí se puede leer.

### Antes de empezar

Dos cosas:

- un `trades.parquet` exportado (`python3 -m sqx.export.export_trades …`);
- las barras del feed en la librería (`13-barras.md`). El comando lee el M1 y el timeframe de la
  estrategia; si el timeframe no estaba cacheado, la primera corrida tarda medio segundo más.

### Cómo se ejecuta

```bash
python3 -m strategies.entryQuality.report \
    --export ~/Desktop/AlgoData/raw/XAUUSD/MC_Trades/2026-09-19/trades.parquet \
    --strategy "Strategy 35.44.31"
```

| flag | obligatorio | qué hace |
|---|---|---|
| `--export` | sí | el `trades.parquet` |
| `--strategy` | sí | el nombre exacto con el que aparece en el export |
| `--set` | no | `--set run.timeframe=H1`, `--set run.feed=USDJPY_DukasM1_the5ers`, `--set eratio.draws=500` |

⚠️ **`run.feed` y `run.timeframe` del `config.yaml` son los del último activo estudiado**, no una
propiedad del export. Si analizas otro símbolo hay que pasarlos, o las velas serán las del oro y no
lo dirá nadie.

**3,3 segundos** con 1.119 operaciones y 200 sorteos. No toca SQX.

### Qué produce

Sólo salida por pantalla, dos bloques.

### Cómo se lee el resultado

**Bloque 3 — el e-ratio.** Para cada horizonte `k` (en velas desde la entrada):

| columna | qué es |
|---|---|
| `e(k)` | recorrido a favor ÷ recorrido en contra, los dos en unidades de la volatilidad de esa entrada |
| `p5`, `mediana`, `p95` | lo mismo para entradas **al azar**, a las mismas horas y con los mismos largos/cortos |
| `sobre la banda` | si tu entrada supera el percentil 95 del azar |

`e(k) ≈ 1` o dentro de la banda = la entrada no aporta. Y el `k` donde `e(k)` hace máximo es el
**horizonte natural de la señal**: compáralo con la duración mediana real de las operaciones. Si tu
señal deja de valer a las 13 velas y tú aguantas 30, estás devolviendo lo ganado.

Debajo se imprime el e-ratio **por dirección**. Una estrategia cuyos largos lo sostienen todo es
otra cosa distinta de una cuyas dos mitades funcionan, y la curva agregada no enseña ni una ni otra.

**Bloque 4 — el retraso.** Por cada `d` (velas, y también minutos):

| columna | qué es |
|---|---|
| `entregado` | cuánto precio regalas por entrar tarde, en dólares de cuenta |
| `esperanza_neta` | lo que quedaría de tu esperanza por operación |
| `DCR` | lo entregado como fracción de la esperanza **bruta** |
| `veces_el_coste` | lo entregado como múltiplo de lo que el backtest ya te cobraba |

`DCR` por encima de 0,3 con **una sola vela** de retraso es la señal de alarma. Negativo significa
que esperar te habría salido a favor, que es lo contrario de la fragilidad.

⚠️ El PDF original pide esto en **unidades de spread**. En este install el spread va dentro de los
precios de fill y no aparece en el residual `bruto − neto` (`knowhow/costs/where-the-spread-is.md`), así que lo
recuperable por operación es el coste total, no el spread solo. La columna se llama
`veces_el_coste` por eso, y leerla como spreads exageraría la gravedad.

### Un ejemplo completo

```
Strategy 35.44.31 · muestra OOS1 · XAUUSD_DukasM1_Infinox M30 · 1119 de 1119 operaciones con camino completo

-- 3 · calidad de la entrada (MFE/MAE contra entradas al azar)
     e(k)     p5  mediana    p95  sobre la banda
k
1   0.894  0.898    1.038  1.221           False
5   1.013  0.904    1.005  1.102           False
10  1.067  0.917    1.005  1.099           False
20  1.075  0.924    1.004  1.090           False
50  1.059  0.945    1.021  1.110           False
largos (1119): k=1 0.89 · k=5 1.01 · k=10 1.07 · k=20 1.08 · k=50 1.06
máximo de e(k) en k=13 · duración mediana real 0 days 07:30:00
-> no_signal: la entrada no se distingue de entrar al azar a las mismas horas

-- 4 · lo que cuesta llegar tarde (tier 1, salidas sin mover)
en barras de M30:
   entregado  esperanza_neta    DCR  veces_el_coste
d
1     -1.582          18.227 -0.043          -0.080
2      1.433          15.212  0.039           0.073
3      1.382          15.262  0.038           0.070
4      5.694          10.950  0.157           0.289
5     17.950          -1.305  0.493           0.910
en minutos:
   entregado  esperanza_neta    DCR  veces_el_coste
d
1     -1.939          18.583 -0.053          -0.098
2     -0.994          17.639 -0.027          -0.050
3     -0.000          16.645 -0.000          -0.000
4     -1.533          18.177 -0.042          -0.078
5     -2.647          19.291 -0.073          -0.134
-> latency_robust: el edge sobrevive a entrar tarde
```

**Qué dice esto de verdad:**

- **La entrada no aporta nada.** En los cinco horizontes la curva real está dentro de la banda del
  azar, y en `k=1` incluso por debajo. Lo que gana esta estrategia no lo gana por acertar cuándo
  entra.
- **Es enteramente larga**: 1.119 operaciones, cero cortas. En un activo que subió en el periodo,
  eso es exactamente lo que la banda ya tiene en cuenta — por eso la comparación se hace con los
  lados barajados y no redibujados.
- **El horizonte de la señal son 13 velas** (6,5 horas) y la duración mediana real es 7,5 horas.
  Coinciden, así que al menos la salida no está muy desalineada con lo poco que la entrada dice.
- **La latencia no la mata**: hasta tres velas de retraso es indiferente, y al minuto es incluso
  favorable. Combinado con lo anterior tiene sentido: no se puede perder por llegar tarde a una
  señal que no marcaba nada.

### Qué NO te dice

- **Nada de las salidas**, a propósito. Un `no_signal` rentable significa que la ventaja está ahí,
  y eso se mide en otro sitio.
- **No distingue fragilidad de latencia de información del futuro.** Un DCR alto es una de las dos
  y este test no puede separarlas.
- **Con stop o target, el bloque 4 no vale.** Las salidas se moverían con la entrada.

### Si algo falla

- **Menos operaciones con «camino completo» que en total**: las que empiezan cerca del final de los
  datos se descartan a propósito, porque su camino se cortaría a un horizonte distinto del resto.
- Si `e(k)` sale absurda (cientos), casi seguro es que el `--set run.feed` no es el del export y
  estás midiendo las entradas de un activo sobre las velas de otro.
