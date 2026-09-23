## 24. Costes por activo — qué le cobras a cada mercado, y en qué unidad

### Qué pregunta responde

Antes de construir o retestear nada hay que saber qué paga esa estrategia por operar: el spread, la
comisión y el swap. SQX trae sus propios números y **casi nunca son los que te cobra tu bróker**, así
que esa diferencia se escribe una vez en `assets/` y se consulta siempre. Esta página dice cómo está
organizado eso, qué unidad lleva cada campo, y por qué un activo de forex se rellena distinto que el
oro.

También contesta la otra mitad: en qué otros mercados hay que comprobar que la estrategia sigue
funcionando, que es `assets/_markets.yaml`.

### Cuándo lo usas, y cuándo no

**Lo usas** antes de tocar cualquier proyecto, tarea o plantilla de un símbolo. Es la regla dura 5
del `CLAUDE.md` y no es opcional: si el activo tiene un coste sin decidir, el comando falla y el
trabajo se para hasta que tú des la cifra.

**No lo usas** para saber qué pagó de verdad un backtest que ya corrió. Eso no se supone, se
recupera de las propias operaciones (`gross − P/L`), y lo hace `strategies/monteCarlo/inputs/costs.py`.
`assets/` dice lo que hay que aplicar de aquí en adelante, no lo que se aplicó.

### Antes de empezar

Nada. No hace falta SQX abierto ni datos exportados: son ficheros de texto y un comando que los lee.

### Cómo se ejecuta

```bash
python3 -m core.assets XAUUSD          # el preflight de un activo
python3 -m core.assets --index         # regenera assets/INDEX.md
python3 -m core.assets --dataranges    # relee de SQX hasta dónde llega cada feed
```

El tercero es el que usas **después de darle a "Update all" en el maestro**: pregunta a SQX qué
histórico tiene ahora de cada feed y reescribe el `data:` de los 17 en `_policy.yaml`. Sólo imprime
lo que se movió:

```
XAUUSD: data: {from: 2003-05-05, to: 2026-01-16}   # …, 7.708.823 barras M1
     →  data: {from: 2003-05-05, to: 2026-09-22}   # …, 7.949.285 barras M1
```

Pregunta al **conductor**, no al maestro, así que puedes lanzarlo con tu GUI abierta sin ningún
riesgo. Ve los datos del maestro igualmente porque `bin/sqx-worker.sh` copia su `user/data` al
worker en cada arranque, y el `History` es un enlace al del maestro.

Salida real del primero:

```
# XAUUSD — clase `no_forex`, overrides a aplicar

SQX symbol: XAUUSD_DukasM1_Infinox   verificado: 2026-09-03

- **spread_is**: usar `10.0` points (SQX lleva hoy `10`) — PROVISIONAL 2026-09-21 — default de SQX…
- **spread_oos**: usar `10.0` points (SQX lleva hoy `10`) — PROVISIONAL 2026-09-21 — default de SQX…
- **commission**: usar `0.00229` pct_of_notional (SQX lleva hoy `{'method': 'SizeBased', 'value': 8}`)…
- **swap_long**: usar `SIN DECIDIR` pct_annual (SQX lleva hoy `{'type': 'points', 'value': -73.42}`)
- **swap_short**: usar `SIN DECIDIR` pct_annual (SQX lleva hoy `{'type': 'points', 'value': 38.76}`)
- **segmento build**: 2008-01-01 a 2017-12-31 inclusive (dateFrom 1199145600000, dateTo 1514764800000)
- **segmento oos1**: 2018-01-01 a 2022-12-31 inclusive (dateFrom 1514764800000, dateTo 1672531200000)
- **segmento oos2**: 2023-01-01 a 2026-12-31 inclusive (…)  ⚠️ RESERVADO para WFC, WFM
- **retest family**: XAGUSD_DukasM1_Infinox, BRENTCMDUSD_ftmo
- **retest structural**: (vacío)
```

Los tres códigos de salida, que son el mecanismo entero:

| sale con | qué significa | qué haces |
|---|---|---|
| `0` | todo decidido | sigues, diciendo en voz alta qué valores aplicas |
| `2` | algún coste obligatorio sigue en `use: null` | **paras y preguntas.** No eliges tú un número |
| `3` | el fichero no cuadra con su clase | lo arreglas: te dice exactamente qué campo falta o sobra |

### Cómo está organizado

Tres ficheros compartidos arriba y los diecisiete de instrumento en `symbols/`, para que la carpeta
se vea de un vistazo:

| fichero | qué guarda | cuántos hay |
|---|---|---|
| `_policy.yaml` | qué es cada tramo IS/OOS (una vez) **y dónde empieza y acaba en cada activo**, con la fecha de datos de SQX al lado | uno, para todos |
| `_classes.yaml` | los dos esquemas de coste: qué campos, en qué unidad, en qué ajuste de SQX | uno, para todos |
| `_markets.yaml` | el universo de retest: por activo main, mercados `family` y `structural` | uno, para todos |
| `symbols/<SÍMBOLO>.yaml` | lo propio del instrumento: sus costes y sus rangos de MC Retest | uno por activo, **en su subcarpeta** |

La idea es que abras un fichero de activo y **no veas nada repetido**. Los segmentos no están
diecisiete veces, están una. Lo que quedó dentro es lo que de verdad cambia de un mercado a otro.

### Los tramos IS/OOS: la plantilla se comparte, las fechas son de cada activo

Los históricos no empiezan a la vez. El oro tiene M1 desde el 2003-05-05 y tú construyes desde
2008; el DAX40 no tiene nada antes del 2013-09-30, así que una ventana que empiece en 2008 se
quedaría corta **sin avisar**. Por eso `_policy.yaml` parte el asunto en dos:

- `segments_default` — **qué es** cada tramo: su papel y qué spread usa. Una sola copia.
- `segments` — **dónde empieza y acaba en cada activo**, con `data` al lado. Los 17 juntos, para
  poder compararlos y ajustarlos de una vez en lugar de abrir diecisiete ficheros.

```yaml
segments:
  XAUUSD:
    data: {from: 2003-05-05, to: 2026-01-16}   # leído de SQX, no se edita a mano
    build: {from: 2008, to: 2017}
    oos1:  {from: 2018, to: 2022}
    oos2:  {from: 2023, to: 2026}
  DAX40:
    data: {from: 2013-09-30, to: 2026-01-16}
    build: {from: null, to: null}              # sin decidir
```

Un extremo puede ser **un año o una fecha**. El año significa el año entero, ambos extremos
incluidos: `from: 2008, to: 2017` es del 1 de enero de 2008 al 31 de diciembre de 2017 completo. La
fecha significa ese día, también incluido, y es como se corta un tramo a mitad de año:
`to: 2026-08-30` llega hasta el último instante del 30 de agosto.

Las ventanas de forex y metales, decididas el 2026-09-22:

| tramo | desde | hasta |
|---|---|---|
| `build` | 2008-01-01 | 2017-12-31 |
| `oos1` | 2018-01-01 | 2022-12-31 |
| `oos2` | 2023-01-01 | 2026-08-30 |

Los seis índices siguen sin ventana a propósito: sus históricos empiezan en 2011-2013 y una
ventana de 2008 no cabría — el comando la rechazaría.

`data` lo lee el proyecto de SQX con `bin/sqx-worker.sh run -symbol action=list` y está ahí
justo para que veas si la ventana que pones cabe. **Si no cabe, el comando falla:**

```
ESQUEMA ROTO en assets/DAX40.yaml: el tramo `build` empieza en 2008 y los datos de
`DAX40_DukasM1_Infinox` empiezan en 2013-09-30
```
→ exit 3. Eso es fatal: esa ventana no se puede llenar nunca. En cambio, que un tramo **acabe
después** del último dato es sólo un aviso, porque es el estado normal del tramo más reciente
mientras no sincronizas:

```
AVISO: el tramo `oos2` llega a 2026-08-30 y los datos de `XAUUSD_DukasM1_Infinox`
acaban en 2026-01-16
```

Y si las dejas en `null`, nadie se inventa una ventana: `window()` se niega y el comando avisa.

Lo que tiene SQX hoy, leído el 2026-09-22:

| activo | datos desde | | activo | datos desde |
|---|---|---|---|---|
| EURUSD, GBPUSD, USDCHF, USDJPY, XAUUSD | 2003-05-05 | | NIKKEI225 | 2011-09-19 |
| AUDUSD, EURJPY, GBPJPY, USDCAD | 2003-08-04 | | USA500, USATEC | 2012-01-19 |
| AUDJPY | 2003-12-01 | | DAX40, DJ30 | 2013-09-30 |
| CADJPY | 2004-10-25 | | **SP500ft** | **no existe en SQX** |

### Las dos clases, que es lo que decide cómo se rellena

| | `forex` | `no_forex` (índices y metales) |
|---|---|---|
| spread | `spread`, **un** valor en puntos | `spread_is` **y** `spread_oos`, en puntos |
| comisión | `commission`, **$ por lote** (`SizeBased`) | `commission`, **% del nocional** (`PercentageBased`) |
| slippage | `slippage`, en puntos | igual |
| swap | `swap_long`/`swap_short`, **puntos por noche** | `swap_long`/`swap_short`, **% ANUAL** |

**Por qué dos spreads fuera de forex.** El precio de estos activos se multiplica a lo largo del
histórico: el oro va de 800 a 3500. Un spread fijo en puntos cuesta siempre lo mismo en dólares, así
que en porcentaje cuesta **el triple en 2010 que hoy** — y eso mete una pendiente dentro de la misma
muestra que ve el generador. Declarando uno para el tramo de construcción y otro para los dos fuera
de muestra, esa pendiente desaparece. Se puede hacer porque **SQX guarda los costes dentro de cada
tarea**, no una vez por proyecto: la tarea de build lleva un `defaultSpread` y las de retest otro.

**Por qué el % fuera de forex.** Un porcentaje escala con el precio él solo, que es justo lo que le
falta a un número fijo en puntos.

### Los rangos del MC Retest

La tarea **MC Retest** vuelve a correr el backtest entero contra una entrada perturbada, y dos de
sus métodos sortean un valor dentro de un rango: el spread y el slippage. Ese rango lo pones tú,
por activo, al final de su fichero:

```yaml
mc_retest:
  spread:
    min: 5                    # puntos
    max: 12
    sqx_now: [{min: 1, max: 5}, {min: 5, max: 12}]   # varias tareas, rangos distintos
  slippage:
    min: 0
    max: 10
    sqx_now: [{min: 0, max: 5}, {min: 0, max: 10}]
```

**Los dos van en puntos absolutos**, no en múltiplos del spread real. Eso es lo que obliga a que
sean por activo: un rango de 1 a 5 puntos es razonable en EURUSD y no significa nada en el
NIKKEI225.

Si los dejas sin decidir **no se bloquea nada**: el comando avisa y sale con 0, porque un rango sin
fijar sólo deja sin interpretar esa tarea concreta del MC Retest, no el resto del trabajo.

```
AVISO: los rangos MC Retest spread, slippage no están decididos. No bloquea,
pero esa tarea del MC Retest no es interpretable hasta que el dueño los fije.
```

⚠️ Mirando el maestro el 2026-09-22, **casi todos los instrumentos llevan el rango de fábrica de
SQX** —spread 1,0–5,0 y slippage 0,0–5,0— que es idéntico en todos los mercados. En el NIKKEI225,
cuyo spread real son 1100 puntos, eso perturba entre 1 y 5: unas 200 veces más barato que el propio
backtest. Donde sí los has puesto a mano están a la escala del activo: el oro lleva spread 5–12
contra un spread real de 10, y el NIKKEI225 lleva 80–200 y 120–400 en sus otras tareas.

(`RandomizeMinDistance` tiene la misma forma y rango de fábrica 0,0–10,0. No está en `assets/`
porque pediste estos dos.)

### Las dos trampas, que cuestan dinero de verdad

⚠️ **El swap en % es ANUAL, no por noche.** SQX divide entre 100 y entre 360 antes de aplicarlo. Si
escribes ahí el porcentaje de una noche, te equivocas por 360 veces. Para pasar un swap que hoy está
en puntos:

```
pct_anual = puntos × tick_size × 36000 / precio_de_referencia
```

Los `-73.42` puntos del oro, con tick 0.01 y precio 3500, son **7,55 % anual**; los `+38.76` del
corto son **3,99 %**. Comprobado: por las dos vías, una noche de un lote cuesta 73,42 $ y 38,76 $.

⚠️ **La comisión en % puede estar cobrándose por pata o por operación, y no está verificado.** El
código de SQX sólo cobra al abrir, pero lo medido en los exports con `SizeBased 8` son 16 $ ida y
vuelta. Es un factor de 2 sobre toda la comisión de los activos no-forex. Antes de dar por buena una
cifra, hay que comprobarlo con un backtest y el residual `gross − P/L`.

### Los dos tipos de mercado adicional

`_markets.yaml` separa en dos, y la diferencia importa porque responden a preguntas distintas:

- **`family`** — mismo motor económico que el activo principal. Oro y plata, por ejemplo. Es la
  prueba fácil: **pasarla no demuestra gran cosa**, porque puede que los dos mercados sean la misma
  operación con otro nombre. Fallarla sí dice algo.
- **`structural`** — parecidos en estructura (volatilidad, horario, ruido) pero **sin ningún motor
  compartido**. Es la prueba dura: si el edge transfiere aquí, es que la lógica capta algo del
  movimiento del precio y no una exposición a un factor macro.

**La lista se cierra antes de mirar ningún resultado.** Elegir los mercados después de ver dónde
funciona convierte la prueba en una selección, y sus p-valores en decoración.

### Cómo se rellena un valor

Abres `assets/<SÍMBOLO>.yaml` y en el bloque del campo pones el número en `use:` y el motivo en
`why:`. `sqx_now` no se toca: es lo que SQX lleva hoy, y está ahí para que veas de qué partes —
ojo, **muchas veces en otra unidad** que la que va en `use`.

```yaml
costs:
  spread_is:
    use: 14                   # points — tramo `build`
    sqx_now: 10               # points, el unico que hay hoy
    why: "Infinox, media de la sesión de Londres 2008-2017, confirmado 2026-XX-XX"
```

Sólo **el spread y la comisión bloquean**. El slippage y los swaps no, y los dos llevan ya una
cifra PROVISIONAL: el slippage es **la mitad del spread** de cada instrumento.

No es una medición y no puede serlo — un backtest aplica el slippage que le das, así que de un
export no se recupera nunca el real. Es una convención, y se eligió ésa porque es la única que
aguanta entre clases: un punto vale `tick_size × point_value`, que va de 0,0065 $ en el Nikkei a
11,53 $ en USDCHF, así que 2,5 puntos planos serían 0,02 $ en uno y 28,82 $ en el otro. La mitad
del spread deja el coste entre 0,33 $ y 5,00 $ por lote y pata, y en el oro cae en 5 puntos: el
punto medio del rango 0-10 que tu propio MC Retest ya sortea.

Si escribes `PROVISIONAL` en el `why`, el valor **decide pero no bloquea**: el comando sale con 0 y
todo informe construido encima queda marcado, para que dentro de seis meses nadie confunda un número
de relleno con una cifra pactada con el bróker.

### Cómo se sabe que está bien

`python3 -m core.assets <SÍMBOLO>` sale con 0 y el índice lo marca:

```bash
python3 -m core.assets --index && head -8 assets/INDEX.md
```

`✅` decidido, `⚠️ provisional` decidido con un número de relleno, `—` bloqueado.

### Qué NO hace

- **No escribe en SQX.** `core.assets.sqx_settings()` devuelve lo que una tarea tendría que llevar,
  pero meterlo en el proyecto es otro trabajo. Hoy hay que hacerlo a mano en la GUI.
- **No adivina.** Si no hay cifra pactada, hay `null` y el trabajo se para. Un fichero con valores
  inventados es peor que no tener fichero: parece decidido.
- **No sabe qué te cobró un backtest ya corrido.** Eso se recupera de las operaciones.

### Dónde está el detalle

- `assets/RULES.md` — la regla y el esquema, para una sesión de Claude.
- `knowhow/09-costs.md` — qué puede cobrar SQX y en qué unidad, con las fórmulas decompiladas.
- `assets/_classes.yaml` — los dos esquemas, uno al lado del otro.
