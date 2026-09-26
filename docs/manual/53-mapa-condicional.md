## 53. El mapa condicional — ¿de qué depende que esto siga funcionando?

> ⚠️ **Este mapa fabrica hipótesis, no las comprueba.** Corta la muestra en volatilidad x tendencia
> y en día de la semana; con tres cortes y varias celdas por cada uno, alguna sale significativa
> por azar en **cualquier** estrategia, incluida una sin ninguna ventaja real. Es el único test del
> PDF del dueño (`TRADE_LEVEL_TESTS.pdf`, item 6) que funciona así, y por eso va el último de la
> tanda y con condiciones: **ninguna celda de aquí es un filtro**. Si una celda parece decir algo,
> se anota como candidata en `ledger/thresholds.yaml` (encargo 8) y se revalida sobre datos que
> todavía no se hayan mirado — nunca se aplica directamente sobre lo que este mapa ya vio.

### Qué pregunta responde

No «¿qué filtro añado?», sino **«¿de qué depende que esto siga funcionando?»**. Clasifica cada
operación por el estado del mercado **en el momento de entrar** — sólo con información disponible
entonces — y enseña, celda a celda, cuántas operaciones hay, cuánto ganan de media (con su
intervalo) y qué parte acierta. Una estrategia que sólo gana en volatilidad alta depende de que ese
régimen vuelva: es una propiedad del objeto, no un defecto a corregir.

### Cuándo lo usas, y cuándo no

**Lo usas** para escribir en la ficha de una estrategia de qué depende su edge — al lado de la
concentración temporal que ya mide `studies/readings/profitShape/` (la misma idea sobre el eje del
calendario). Es lectura, no criba.

**No lo uses** para decidir un filtro sin pasar por el ledger.

### Antes de empezar

- Una cosecha de la puerta OOS ya hecha (`studies/screening/gate/harvest.py`): el mapa lee su
  `trades.parquet` (operaciones por `identity`) y su `metrics.parquet` (el nombre de cada
  estrategia), nunca un export directo de SQX ni una instalación viva.
- Las barras del feed en la librería (`13-barras.md`): el mapa resuelve un candil diario a partir
  de la rejilla de la estrategia.
- El tramo `build` del activo decidido en `assets/_policy.yaml` — de ahí salen los cortes de
  tercil, congelados. Sin tramo `build`, el comando se detiene con el mismo error que
  `core.assets` (regla dura 5).

### Cómo se ejecuta

```bash
python3 -m studies.readings.conditionalMap.report \
    --harvest ~/Desktop/AlgoData/harvest/XAU_ISOOS_ejemplo/Results/2026-09-23 \
    --strategy "Strategy 5.16.81" \
    --set run.symbol=XAUUSD run.feed=XAUUSD_DukasM1_Infinox run.timeframe=M30
```

| flag | obligatorio | qué hace |
|---|---|---|
| `--harvest` | sí | la carpeta del día de una cosecha (`.../harvest/<proyecto>/<databank>/<día>`) |
| `--strategy` | sí | el nombre exacto con el que la cosecha lo tiene en `metrics.parquet` |
| `--set` | no | `--set run.symbol=USDJPY run.feed=USDJPY_DukasM1_the5ers run.timeframe=H1`, `--set volatility.atr_period=30`, `--set trend.window=10` |

⚠️ **`run.symbol`, `run.feed` y `run.timeframe` de `config.yaml` son los del último activo
estudiado**, no una propiedad de la cosecha: analizar otro símbolo sin pasarlos clasifica las
operaciones contra las velas y el tramo de construcción equivocados, sin que nada avise.

**Un segundo** con 361 operaciones y 9.999 remuestreos por celda poblada. No toca SQX.

### Qué produce

Sólo salida por pantalla (Markdown) y, además, el resultado de la estrategia bajo
`reports/<proyecto>/<databank>/<día>/conditionalMap/estrategias/<estrategia>.json` y `.html` —
lo que pinta la ventana.

### Cómo se lee el resultado

**Pestaña «Volatilidad x tendencia en la entrada».** Una rejilla 3x3: filas el tercil de
volatilidad realizada (ATR diario) **del día anterior a la entrada**, columnas el tercil de
tendencia (ratio de eficiencia de Kaufman) **del mismo día anterior** — nunca el día de la propia
entrada, porque ese día incluye barras que todavía no habían pasado en el momento de entrar. Los
dos tipos de corte salen **una sola vez**, sobre el tramo `build` del activo, y se aplican sin
cambios a la muestra que se lee. Una celda vacía (`—`) no es cero: es que tiene menos operaciones
que el suelo de la puerta OOS (`engines/nulls/config.yaml#verdict.min_trades`, hoy 30) y no se
enseña ni se juzga. La tabla de abajo trae, celda a celda, operaciones, P&L medio, su intervalo por
bootstrap y el acierto.

⚠️ **Corregido 2026-09-26** (revisión de esta misma tanda): la primera versión clasificaba cada
operación con el candil diario de **su propio** día de entrada, que `engines.regimes.regime.daily()`
construye con la sesión entera — en una operación real verificada, el 79 % de las barras de ese día
llegaban **después** de la entrada, incluida la que ponía el máximo del día. Los cortes de tercil
congelados sobre `build` heredaban el mismo defecto. `studies/readings/conditionalMap/regime.py`
ahora desplaza la volatilidad y la tendencia un día completo antes de clasificar nada — una entrada
del día D lee siempre lo que se sabía al cierre de D-1 —, y `tests/test_conditionalmap.py` prueba
que una barra que llega después de la entrada, en el propio día de la entrada, no puede mover su
celda. Los números de los dos ejemplos de abajo son los de la versión corregida y no coinciden con
los de una ejecución anterior a esa fecha.

**Pestaña «Sesión y día de la semana».** Lo mismo por sesión de mercado y por día, con el mismo
suelo, en tres vistas: sesión x día, sólo sesiones y sólo días (la ventana cambia entre ellas).
Las sesiones son las horas de trabajo de cada ciudad **en su propia hora local** —Tokio 9–18,
Londres 8–17, Nueva York 8–17—, así que el cambio de horario de cada una mueve sus bordes en su
fecha: Asia, solape Asia-Londres, Londres, solape Londres-NY, Nueva York y fuera de sesión.

⚠️ **Las horas de SQX no son UTC.** Cada feed viene en la hora de su broker: los de Infinox en
`EET`, los de the5ers en hora de Israel, el Brent en `EETUS` (la de Nueva York más 7 horas). El
mapa lee la zona de cada feed del registro de SQX y pasa cada entrada a UTC antes de asignarle
sesión; sin eso, todas caerían dos o tres horas desplazadas. La hora que el cambio de horario
repite o salta no se asigna a ninguna sesión, y la nota de la pestaña dice cuántas son. El día
de la semana es el del reloj del feed.

Ejemplo real, `XAU_ISOOS_ejemplo / Strategy 5.16.81` (361 operaciones OOS1, tramo build
2008–2017; las 331 de la tabla son las que caen en las seis celdas con población — el resto se
reparte en las tres celdas de volatilidad media, ninguna de las cuales llega a 30):

```
Terciles congelados sobre el tramo de construcción de XAUUSD. ATR(20) para la volatilidad —
cortes [16.6062, 20.7802]. Ratio de eficiencia a 20 días para la tendencia — cortes
[0.1411, 0.3049].

| volatilidad | tendencia | operaciones | pnl_medio | ci_baja | ci_alta | acierto |
|---|---|---|---|---|---|---|
| baja  | baja  | 46 | -244.22 | -584.40 |  104.63 | 0.391 |
| baja  | media | 47 |  -55.25 | -398.26 |  269.87 | 0.553 |
| baja  | alta  | 47 |  123.11 | -194.50 |  446.41 | 0.532 |
| alta  | baja  | 59 |  -94.38 | -457.18 |  247.35 | 0.508 |
| alta  | media | 63 |   84.21 | -174.38 |  337.98 | 0.540 |
| alta  | alta  | 69 |  -14.68 | -253.98 |  221.13 | 0.449 |
```

(La celda «media» de volatilidad no aparece: ninguna de sus tres combinaciones llegó a 30
operaciones en esta muestra — 361 operaciones repartidas en 9 celdas se quedan cortas casi
siempre, y es la razón de que el mapa esté pensado para leerse, no para recortar.)

Léelo así: seis de las nueve celdas posibles tienen población, y **ninguna** tiene el intervalo del
P&L medio enteramente por encima o por debajo de cero — ni siquiera `baja x baja` (-584.40 a
104.63), la más negativa de las seis. Eso es exactamente lo que el aviso de arriba predice: con
seis celdas mirando y ninguna cruzando el listón con margen, no hay aquí ni un candidato razonable
a anotar en el ledger, sólo una descripción sin nada que sostenga un filtro.

### Un ejemplo completo

Con `USDJPY_emaCross_H1 / Strategy 14.19.58` (256 operaciones OOS1, todas con día y tercil
válidos), sólo la fila `baja` de volatilidad tiene población — las otras dos terciles no llegan a
30 operaciones en ninguna de sus tres combinaciones de tendencia; las 207 de la tabla son las de
esa fila:

```
| volatilidad | tendencia | operaciones | pnl_medio | ci_baja | ci_alta | acierto |
|---|---|---|---|---|---|---|
| baja | baja  | 81 | -47.64 | -149.45 |  53.11 | 0.469 |
| baja | media | 67 | -61.37 | -171.36 |  48.51 | 0.507 |
| baja | alta  | 59 |   1.48 | -122.79 | 126.54 | 0.508 |
```

Por sesión, `USDJPY_emaCross_H1 / Strategy 14.19.58` (256 operaciones OOS1; ninguna casilla
sesión x día llega a 30, así que el cruce no se enseña):

```
| sesión            | operaciones | pnl_medio | acierto |
|---|---|---|---|
| Asia              | 90 |   33.33 | 0.567 |
| Londres           | 42 |  -99.72 | 0.452 |
| Solape Londres-NY | 54 |  -13.95 | 0.537 |
| Nueva York        | 42 |  -21.75 | 0.452 |
```

Y por día de la semana:

```
| día       | operaciones | pnl_medio | acierto |
|---|---|---|---|
| lunes     | 50 |   47.23 | 0.580 |
| martes    | 48 |  -19.69 | 0.521 |
| miércoles | 67 |  -73.36 | 0.478 |
| jueves    | 45 |    8.17 | 0.556 |
| viernes   | 46 | -124.40 | 0.391 |
```

Los tres intervalos de volatilidad cruzan cero: nada aquí sostiene que la estrategia dependa de un
régimen de volatilidad concreto. El viernes es la celda más llamativa (-124.40, acierto 0.391 en
46 operaciones) — con cinco días mirando, es exactamente el tipo de celda que el aviso de arriba
avisa que va a aparecer por azar, no una que se pueda usar para excluir el viernes sin más.

### Qué NO te dice

- **No es un filtro, y ninguna celda lo es** por sí sola: es una descripción con comparaciones
  múltiples sin corregir. Aplicar una sin pasar por el ledger y sin revalidar sobre datos nuevos
  es la forma más barata de sobreajustar la cadena entera.
- **Las sesiones son una convención, no un dato del mercado.** Las horas de cada ciudad las fijó el
  dueño el 2026-09-26; con otras horas, otras celdas. Se cambian en `config.yaml`, bloque
  `sessions`.
- **Nada sobre las salidas.** Sólo mira el estado del mercado al entrar; el resto de la estrategia
  (salida, tamaño, gestión) no está aquí.
- **No corrige por comparaciones múltiples entre celdas.** El aviso lo dice, no lo esconde: leer
  seis o nueve celdas y coger la más extrema es exactamente el error que el aviso señala.

### Si algo falla

- **`el tramo build de <SÍMBOLO> no tiene fechas decididas`** — `assets/_policy.yaml` no trae ese
  tramo para el activo; hay que decidirlo ahí antes de correr el mapa (regla dura 5).
- **`N operaciones abren en días que el fichero de barras no tiene`** (desde
  `engines/regimes/regime.tag`, si se usara directamente) — símbolo o feed equivocado en
  `--set run.feed=…`; el mapa usa su propia clasificación y no llama a esa función, pero el mismo
  síntoma (una malla de barras que no cubre las fechas de la cosecha) aparece como celdas vacías
  en vez de un error: revisa `run.feed`.
- **Todas las celdas salen vacías (`—`)** — o la muestra es pequeña, o `run.feed`/`run.timeframe`
  no son los del activo que se está leyendo (ver el aviso de `--set` más arriba).
