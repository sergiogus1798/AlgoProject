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

**No lo uses** para decidir un filtro sin pasar por el ledger. Y **no** enseña la sesión del día
(Asia/Londres/Nueva York/solape) todavía: ver «Qué no te dice».

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
volatilidad realizada (ATR diario) en el día de la entrada, columnas el tercil de tendencia (ratio
de eficiencia de Kaufman) del mismo día — los dos cortados **una sola vez**, sobre el tramo
`build` del activo, y aplicados sin cambios a la muestra que se lee. Una celda vacía (`—`) no es
cero: es que tiene menos operaciones que el suelo de la puerta OOS
(`engines/nulls/config.yaml#verdict.min_trades`, hoy 30) y no se enseña ni se juzga. La tabla de
abajo trae, celda a celda, operaciones, P&L medio, su intervalo por bootstrap y el acierto.

**Pestaña «Día de la semana».** Lo mismo por día, lunes a viernes, con el mismo suelo.

Ejemplo real, `XAU_ISOOS_ejemplo / Strategy 5.16.81` (361 operaciones OOS1, tramo build
2008–2017; las 333 de la tabla son las que caen en las seis celdas con población — el resto se
reparte en las tres celdas de volatilidad media, ninguna de las cuales llega a 30):

```
Terciles congelados sobre el tramo de construcción de XAUUSD. ATR(20) para la volatilidad —
cortes [16.6062, 20.7802]. Ratio de eficiencia a 20 días para la tendencia — cortes
[0.1411, 0.3049].

| volatilidad | tendencia | operaciones | pnl_medio | ci_baja | ci_alta | acierto |
|---|---|---|---|---|---|---|
| baja  | baja  | 45 | -445.35 | -785.65 | -126.30 | 0.378 |
| baja  | media | 42 |   36.01 | -317.19 |  395.48 | 0.524 |
| baja  | alta  | 54 |  168.82 | -120.17 |  466.24 | 0.556 |
| alta  | baja  | 59 |  -84.28 | -341.55 |  158.42 | 0.542 |
| alta  | media | 62 |   87.02 | -266.50 |  430.45 | 0.500 |
| alta  | alta  | 71 |  -24.99 | -254.17 |  210.73 | 0.451 |
```

(La celda «media» de volatilidad no aparece: ninguna de sus tres combinaciones llegó a 30
operaciones en esta muestra — 322 operaciones repartidas en 9 celdas se quedan cortas casi
siempre, y es la razón de que el mapa esté pensado para leerse, no para recortar.)

Léelo así: seis de las nueve celdas posibles tienen población, y **ninguna** de ellas tiene el
intervalo del P&L medio enteramente por encima o por debajo de cero salvo `baja x baja`
(-785.65 a -126.30, la única que no cruza cero). Eso es exactamente lo que el aviso de arriba
predice — con seis celdas mirando, una sale «significativa» sin que signifique nada — y es una
candidata a **anotar y revalidar**, nunca a aplicar tal cual.

### Un ejemplo completo

Con `USDJPY_emaCross_H1 / Strategy 14.19.58` (256 operaciones OOS1, todas con día y tercil
válidos), sólo la fila `baja` de volatilidad tiene población — las otras dos terciles no llegan a
30 operaciones en ninguna de sus tres combinaciones de tendencia; las 205 de la tabla son las de
esa fila:

```
| volatilidad | tendencia | operaciones | pnl_medio | ci_baja | ci_alta | acierto |
|---|---|---|---|---|---|---|
| baja | baja  | 78 | -56.31 | -156.67 |  42.40 | 0.487 |
| baja | media | 71 | -33.51 | -146.08 |  79.22 | 0.493 |
| baja | alta  | 56 | -41.35 | -168.36 |  92.17 | 0.464 |
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
- **La sesión (Asia / Londres / Nueva York / solape) no está construida.** El campo `session` de
  `assets/symbols/<SÍMBOLO>.yaml` nombra una sesión de SQX (`USDJPY_ftmo`, `XAUUSD_ftmo`); lo que
  esa sesión define dentro del proyecto (`<Resources><Sessions>`, comprobado 2026-09-26 sobre el
  donante congelado de XAUUSD) es la semana de mercado abierto — lunes a viernes, 01:05 a 23:50 —,
  no una partición del día en zonas horarias. Inventar esos cortes está prohibido (CLAUDE.md regla
  11): se necesitan las horas UTC de cada sesión, que hoy no están decididas en ningún sitio de
  este repositorio. Día de la semana se construye en su lugar; la sesión queda pendiente en
  `_coord/BOARD.md` hasta que el dueño las fije.
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
