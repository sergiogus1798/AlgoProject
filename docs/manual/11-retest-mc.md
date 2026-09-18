# 11. Retest de Monte Carlo — ¿habrían ocurrido siquiera estas operaciones?

> **Ojo con el nombre.** Aquí «retest» significa **Monte Carlo Retest**: SQX vuelve a ejecutar el
> backtest entero mil veces contra una entrada perturbada. No es el *retest multi-mercado*, que es
> la página `05-retest-mercados.md`. Son dos cosas distintas con el mismo nombre.

### Qué pregunta responde

Todas las pruebas de robustez que ya usas remezclan una lista de operaciones que **ya existe**: el
Monte Carlo de operaciones las reordena, el retest multi-mercado las coloca en otro mercado. La
estrategia nunca se vuelve a ejecutar.

Esta es al revés. Cada simulación cambia una entrada del backtest —el spread, un parámetro, la vela
histórica— y **vuelve a correr la estrategia entera** contra esa entrada. Por eso tarda, y por eso
responde algo más profundo: no «¿fue suerte la forma de esta curva?», sino «¿habría existido esta
curva?». Y como cada tarea cambia **una sola cosa**, te dice **cuál** de ellas la rompe.

### Cuándo lo usas, y cuándo no

**Úsalo** cuando una estrategia ya ha pasado los filtros de población, el decaimiento IS/OOS y el
retest multi-mercado, y lo que quieres saber es de qué depende: del coste de entrar, del relleno
que te dan, de sus propios parámetros, o del histórico exacto que le tocó ver.

**No lo uses** para decidir si la ventaja existe — eso lo dan otros estudios y aquí se da por
supuesto. Y no lo uses para medir sobreajuste de generación: para eso hace falta saber cuántas
estrategias se probaron, un número que en esta fase no existe.

### Antes de empezar  

Este comando **solo lee ficheros de disco**. No toca SQX, ni el worker, ni ningún proyecto, así que
puedes lanzarlo con la GUI abierta sin ningún riesgo.

Lo que sí tiene que existir antes son **las ocho tareas ya corridas en SQX**, cada una en su propio
databank del proyecto, con un único método de perturbación activo:

| databank | qué aleatoriza | papel |
|---|---|---|
| `MCR 1 Bar` | la barra en la que empieza el backtest | **control** |
| `MCR 2 Spread` | el spread cobrado | ejecución |
| `MCR 3 Slippage` | el slippage del relleno | ejecución |
| `MCR 4 MinDist` | la distancia mínima de una orden pendiente al precio | ejecución |
| `MCR 5 Params` | todos los parámetros de la estrategia | especificación |
| `MCR 6 Exits` | solo los parámetros de salida | especificación |
| `MCR 7 OHLC` | el propio histórico de precios | datos |
| `MCR 8 Stress` | las seis cosas a la vez, sobre muestra completa | producción |

Si un databank lleva dos métodos activos, el comando **se niega a escribir**. Es a propósito: una
tarea que perturba dos cosas no sirve para atribuir el daño a ninguna.

### Cómo se ejecuta

```bash
python3 -m strategies.retest.ingest --project XAUUSD --databank MCR_All --day 2026-09-18
```

| flag | obligatorio | qué hace |
|---|---|---|
| `--project` | sí | nombre del proyecto tal y como aparece en SQX |
| `--databank` | no | nombre de **esta corrida de ingesta**, no de un databank de SQX. Por defecto `MCR_All`. Los ocho databanks de SQX van dentro como particiones |
| `--day` | no | fecha del export, `YYYY-MM-DD`. Por defecto hoy |
| `--limit` | no | solo las primeras N estrategias de cada tarea, para una prueba rápida |
| `--set` | no | cambia cualquier ajuste del `config.yaml`, p. ej. `--set ingest.capital=50000` |

**Tarda 8 segundos** con 5 estrategias × 8 tareas × 1.000 simulaciones en esta máquina (96 núcleos).
Escala a cientos de estrategias sin cargar nada entero en memoria: el pico es una estrategia por
proceso.

### Qué produce

Todo bajo `~/Desktop/AlgoData/raw/<proyecto>/<databank>/<fecha>/`:

| carpeta | qué es |
|---|---|
| `sims/` | **la tabla principal**: una fila por simulación con las 30 métricas reconstruidas |
| `levels/` | la tabla de confianza que guardó SQX, en formato largo |
| `original/` | el backtest sin perturbar del que salió cada tarea |
| `pnl/` | el P/L crudo de cada operación de cada simulación |
| `manifest.json` | qué métodos corrió cada tarea, con qué números, y el resultado de la reconciliación |

**Un export es inmutable.** Si vuelves a lanzarlo sobre la misma fecha, el comando se niega en vez
de escribir encima. Para rehacerlo, otra `--day` o borra la carpeta a mano.

### Cómo se lee el resultado

La salida real de la corrida del 18 de septiembre de 2026:

```
ingest: 40 runs, 39996 simulations -> /home/sergioguslw/Desktop/AlgoData/raw/XAUUSD/MCR_All/2026-09-18
  reconciled 30 metrics against SQX, 0 disagreements
  level tables unusable (run cut short): 3 — bar/1.19.29, exits/1.19.29, ohlc/41.5.25
```

Tres líneas, y las tres importan:

**`40 runs, 39996 simulations`** — 8 tareas × 5 estrategias. Si el número de simulaciones no es
múltiplo redondo de 1.000, alguna corrida se cortó (ver la tercera línea).

**`reconciled 30 metrics against SQX, 0 disagreements`** — la línea que hace fiable todo lo demás.
El estudio entero es una reconstrucción: SQX guardó once percentiles por métrica y tiró las
simulaciones individuales, así que cada número de aquí está recalculado desde el P/L crudo. Esa
reconstrucción solo vale si reproduce lo que SQX calculó. Son **12.210 comprobaciones** —30 métricas
× 11 niveles × 5 estrategias × 8 tareas— y **si una sola falla, el comando no escribe nada.**

**`level tables unusable`** — estas tres corridas se cortaron antes de las 1.000 simulaciones. Las
simulaciones que guardaron están bien (los índices se truncan por la cola, nunca dejan huecos), pero
SQX escribió su tabla de confianza sobre las 1.000 que le pediste, así que **en esas tres la tabla
guardada tiene todos los rangos desplazados** y no se lee. La reconstruida sí vale.

### Un ejemplo completo

```bash
$ python3 -m core.assets XAUUSD          # preflight obligatorio antes de nada
$ python3 -m strategies.retest.ingest --project XAUUSD --databank MCR_All --day 2026-09-18
ingest: 40 runs, 39996 simulations -> /home/sergioguslw/Desktop/AlgoData/raw/XAUUSD/MCR_All/2026-09-18
  reconciled 30 metrics against SQX, 0 disagreements
  level tables unusable (run cut short): 3 — bar/1.19.29, exits/1.19.29, ohlc/41.5.25
```

Y así se mira lo que ha escrito:

```python
from strategies.retest.measure import store
s = store.load_sims(project="XAUUSD", databank="MCR_All", day="2026-09-18")
print(s.groupby("task").NetProfit.median().round(0))
```

```
task
bar         23229.     <- el control: casi no se mueve, que es lo que debe pasar
exits       23766.
mindist     23064.     <- no perturbó nada: los stops están lejos del precio
ohlc        23302.
params      18887.
spread      20969.
slippage    16262.     <- el slippage duele el triple que el spread
stress      11837.     <- las seis cosas a la vez
```

### Qué NO te dice

- **No te dice si la ventaja es real.** Eso se da por supuesto; aquí solo se mide de qué depende.
- **Un nivel de confianza no es un escenario.** El nivel 95 de `NetProfit` y el nivel 95 de
  `Drawdown` salen de **simulaciones distintas**: cada métrica se ordena por su cuenta. Leídos como
  pareja describen una corrida que no existió nunca.
- **`MaxLoss` está ordenado al revés.** Su nivel 100 es la peor operación **más suave** de la
  corrida, no la más dura. Leerlo como cifra de estrés es exactamente al contrario.
- **Solo 30 de las 148 métricas se reconstruyen por simulación.** `SharpeRatio`, `SortinoRatio`,
  `UlcerIndex`, `RSquared` y `Stability` las calcula SQX sobre la **equity diaria**, que ninguna
  simulación lleva. Otras 60 —MAE, MFE, exposición, duración— solo existen como los once percentiles.
- **Las tareas 1 a 7 y la 8 no se comparan de tú a tú.** Las siete primeras corrieron solo en
  muestra; la 8 corrió sobre la muestra completa y su backtest de referencia tiene un 50% más de
  operaciones. Son backtests distintos.

### Si algo falla

**`0 retest results, expected one`** — ese `.sqx` no lleva un Monte Carlo Retest. Suele ser un
databank de Monte Carlo de *operaciones*, que guarda un fichero de órdenes parecido pero no es lo
mismo. Comprueba que estás apuntando al databank correcto.

**`ran ['RandomizeSpread', 'RandomizeSlippage'], expected ['RandomizeSpread']`** — esa tarea corrió
con dos métodos activos. Vuelve a correrla en SQX con uno solo, o el estudio no podrá atribuir nada.

**`already holds an ingest`** — ya existe un export de esa fecha. Usa otra `--day` o borra la
carpeta. No sobrescribe a propósito: parquet **añade** en vez de reemplazar, y una ingesta repetida
duplicaría todas las filas en silencio.

**`REFUSING to write — N reconstructions disagree with SQX`** — alguna fórmula reconstruida ya no
reproduce lo que SQX calculó. No es un aviso: no escribe nada. Suele significar que alguien tocó
`strategies/retest/model/` sin volver a calibrar.
