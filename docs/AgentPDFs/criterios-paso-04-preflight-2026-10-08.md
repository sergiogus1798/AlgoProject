# Paso 4 — Preflight: costes, ventanas y rangos. Qué comprueba, de dónde sale cada cifra y qué no cuadra

**Fecha:** 2026-10-08 · **Para:** el dueño, que va a fijar los criterios él mismo · **Alcance:** sólo el paso 4 de `docs/AgentPDFs/WORKFLOW.md`: el comando `python3 -m core.assets <SÍMBOLO>`, las fichas de `assets/`, el aviso de calidad del feed y el spread real.

Revisado por dos miembros del Council (Feynman, Taleb) el 2026-10-08; correcciones aplicadas.

**Qué es:** el documento de consulta del paso 4, con la misma forma que el del paso 16 (`criterios-paso-16-spp-2026-10-07`). Este paso no juzga estrategias: decide **con qué costes, sobre qué fechas y con qué rangos** se va a construir y a probar todo lo que viene después. Un error aquí no descarta una estrategia; cambia el resultado de todas.

**De dónde salen los números.** El paso 4 no tiene corrida propia: es una lectura de ficheros. Los ejemplos son:

- las fichas de **NIKKEI225** y **USDJPY** tal como están hoy en disco (`assets/symbols/`, confirmadas en git el 2026-10-04) y la salida real del comando, ejecutado hoy;
- los ticks de las firmas de fondeo muestreados el 2026-10-04 (`AlgoData/mt5/ticks_hist/<firma>/<ACTIVO>/`, martes a jueves de la segunda semana de cada mes), **recalculados por mí** con `scratchpad/paso04/firm_spread.py`;
- el estudio del spread de Darwinex del 2026-09-27 (`AlgoData/spread/<ACTIVO>_TICK/`), leído y vuelto a resumir por mí;
- el escaneo de calidad del feed (`AlgoData/feedQuality/`: NIKKEI225 del 2026-10-04, USDJPY del 2026-09-26).

La corrida `Trade_NIKKEI225_M30_volatilidadL` del 2026-10-04 (la de los dossiers de los pasos 10 y 16) usó exactamente los costes de la ficha de hoy: 304,11 y 474,91 puntos de spread.

**El commit que describo:** `b2b4c8c`. **Ficheros del paso con cambios sin confirmar:** `assets/_policy.yaml` (añade `BlindJoint` a la lista de reserva de `oos2`), `assets/_build.yaml`, `assets/_markets.yaml`, `assets/_study.yaml` (no son de este paso), `core/assetcheck.py` (sólo quita dos imports sin usar) y cinco ficheros de `studies/data/feedQuality/` (`calibrate.py`, `inputs.py`, `scan.py`, `tooltips.py`, `config.yaml`: la lista de feeds del calendario pasa a estar escrita, porque el filtro por nombre dejó de funcionar al renombrar los feeds el 2026-10-01). Las fichas de `assets/symbols/` no tienen cambios pendientes. Describo lo que hay en disco.

**Ninguna línea de este documento está congelada.**

---

## 0. En una página

**La pregunta del paso.** Antes de crear nada para un activo: ¿están decididos sus costes, caben sus ventanas en los datos que SQX tiene, y qué cifras exactas va a llevar cada tarea?

**Lo que hay cargado hoy.** Dos motivos de bloqueo y cuatro avisos. Bloquea (a) una ficha que no cumple el esquema de su clase o pide histórico anterior al primer dato, y (b) un spread o una comisión sin valor. Avisa de: tramo que acaba después del último dato, tramo sin fechas, rango de MC Retest sin decidir y calidad del feed. Los 27 activos pasan hoy (salida 0). XAUUSD recibe el aviso de rango `min_distance` sin decidir; otros 15 (entre ellos NIKKEI225) reciben el aviso de calidad del feed.

**Lo que sale para los dos activos del ejemplo.**

| | NIKKEI225 | USDJPY |
|---|---|---|
| spread `build` / `oos1` / `oos2` (puntos SQX) | 304,11 / 474,91 / 796,12 | 0,51 / 0,58 / 0,77 |
| deslizamiento por pata | 106,44 / 166,22 / 278,64 | 0,18 / 0,20 / 0,27 |
| comisión | 0 % | 5 USD por lote |
| swap largo / corto | −4,78 % / −1,87 % anual | +2,57 / −22,15 puntos por noche |
| coste de una ida y vuelta en `build` | 0,0295 % del nocional | 10,49 USD por lote = 1,66 pips si el `SizeBased 5` es ida y vuelta; 15,49 USD = 2,45 pips si SQX lo cobra por pata (sin verificar, 3.7) |
| aviso de calidad del feed | toda la construcción es anterior al año estable (2020) | ninguno |

**Las once cosas que conviene saber antes de leer el resto:**

1. **El spread de las fichas no lo calcula ningún comando del repositorio.** Desde el 2026-10-04 es «el % del precio de la firma más ancha (FTMO, Hantec o FundingPips), media de 12 meses, por el precio medio de cada tramo, sin factor». La «media de 12 meses» son en realidad **36 días** (martes a jueves de la segunda semana de cada mes; ningún lunes, ningún viernes, ninguna primera semana de mes). Lo he reproducido desde los ticks (NIKKEI225: 0,01735 %; USDJPY: 0,00514 %), pero el script que lo escribió no está en el repo. El comando que sí existe, `studies.data.spread.onboard` (skill `/asset-onboard`), calcula **otra cosa**: el spread de Darwinex con un modelo. Si alguien lo ejecuta con `--write` sobre un activo existente, sobreescribe los spreads con Darwinex + modelo (el código usa hoy factor 1,0 y 35 % de deslizamiento, no el ×1,25 y la mitad que dicen los textos) y, salvo con `--spread-only`, también la comisión forex (8 USD frente a los 5 de las fichas), los tramos y el swap (5.1).
2. **Hay tres cifras de spread para el mismo tramo y difieren hasta 2,5 veces en `build` (304 / 607 / 747) y 1,9 veces en `oos1` (475 / 732 / 916).** NIKKEI225, `oos1` (2020-2023): la ficha cobra 475 puntos; Darwinex midió de media 732 puntos en esos mismos días; la propuesta del estudio de septiembre era 916. En `oos1` el spread de la ficha queda **por debajo del percentil 2,5** de lo que Darwinex cotizó (500 puntos). Es consecuencia directa de tu decisión del 2026-10-04 («la historia paga la fricción de 2026 en proporción al precio»); aquí está su tamaño.
3. **La firma más ancha del NIKKEI cotiza un spread casi fijo de unos 1.000 puntos, no un porcentaje.** FundingPips: ≈10,0 unidades de precio (entre 10,000 y 10,060 en 17 de los 19 meses muestreados; exactamente 10,000 sólo en 7) (calculado por el revisor con `firm_spread.py` sobre los ticks de las firmas). Es «la más ancha» por la regla «mayor de 12 y 3 meses» en %; en puntos, FTMO está hoy algo por encima (≈10,9 desde abril, 11,8 en septiembre; calculado por el revisor, mismo método), aunque su media de 12 meses en % es menor. Convertido a % y llevado al precio de 2011-2019 da 304 puntos. Ninguna fuente de ticks llega antes de 2017; lo que una firma de fondeo habría cobrado entonces no lo ha medido nadie.
4. **El deslizamiento se aplica dos veces, así que el coste real de una operación es spread × 1,7.** La ficha dice «35 % del spread»; SQX lo cobra en la entrada y en la salida. El «sin factor» deja como único margen la diferencia entre 1,7 y el 1,33 que costaron 600 operaciones reales de 2026: un 28 % sobre la media de las tres firmas y un 4 % sobre la más cara (calculado por el revisor con las cifras de la tarjeta). Ese margen se aplica sobre el spread de la ficha, no sobre el medido (3.6).
5. **16 de los 27 activos tienen un lado del swap que hoy se abona, y ese abono se aplica a toda la historia.** USDJPY largo: +2,57 puntos por noche (+1,62 USD por lote, +0,59 % anual) desde 2008, cuando el diferencial de tipos que lo produce es de hoy. En el crudo decidiste escribir 0 en el lado abonado por este mismo motivo; en los demás no.
6. **El rango del MC Retest de deslizamiento en forex no es «0,5× a 2,7×», es 0,5× a 6×.** `core/assetranges.py:41` ensancha a 1 punto cualquier rango más estrecho. En USDJPY el deslizamiento base es 0,18 y el sorteo va de 0,09 a 1,09. El preflight imprime las cifras correctas pero las describe como «0.5x-2.7x».
7. **El aviso de calidad del feed no para nada, y para el NIKKEI225 dice que toda la ventana de construcción es de calidad inferior.** Año estable 2020; construcción 2011-2019. La mediana anual es de 291 anomalías marcadas, y la mediana de huecos de más de 5 minutos dentro de la sesión declarada es 245 (dos medianas independientes, no una parte de la otra): es más un problema de sesión mal deducida que de precios falsos.
8. **Una comisión sin decidir no da el mensaje «BLOQUEADO»: da un error de Python.** Sigue saliendo con código distinto de cero, así que bloquea, pero quien lo lea verá una traza en vez de la frase. Verificado en memoria, sin tocar ficheros. Un activo recién dado de alta (con `data:` vacío) no llega ahí: sale antes con 3 (5.7).
9. **Cinco documentos describen un método que ya no es el de las fichas:** la skill `/asset-onboard`, el capítulo 59 del manual, `assets/RULES.md`, `assets/_classes.yaml` y la fila del paso 4 de `WORKFLOW.md` hablan de Darwinex × 1,25, deslizamiento a la mitad y 8 USD por lote (entre otras cosas). Las fichas llevan firma más ancha × 1,0, 35 % y 5 USD (5.2).
10. **La media del spread no describe ninguna hora real en forex.** En USDJPY de FTMO, la hora 0 del servidor (el rollover) es el 3,3 % del tiempo cotizado y el 29 % de la media; su spread es 9 veces la media y las otras 23 horas cotizan a 0,73 veces (calculado por el revisor, 36 días de ticks de FTMO). Una estrategia que entra en la vela de las 00:00 paga en la cuenta bastante más de lo que la ficha le cobra (5.12).
11. **Los cocientes ficha / medido de Darwinex en NIKKEI225 cambian de lado por tramo:** 0,41 en `build`, 0,65 en `oos1` y 1,74 en `oos2` (calculado por el revisor: spread de la ficha entre la media de los días medidos por Darwinex en cada tramo). El coste sube en escalón en las fronteras de los tramos, así que la caída de una estrategia de `oos1` a `oos2` mezcla pérdida de filo con subida de coste (5.3).

---

## 1. Qué es el paso y cómo decide

### 1.1 Dónde está y quién lo llama

Es la regla dura 5: antes de crear o modificar un proyecto, una tarea o una plantilla, se ejecuta `python3 -m core.assets <SÍMBOLO>` y se para si sale distinto de cero. No es sólo disciplina; lo llama el código:

| quién | dónde | qué comprueba |
|---|---|---|
| el comando único del workflow | `bin/workflow.sh:58` | el comando entero; si falla, «no se crea nada» |
| el botón «Lanzar en SQX» de la ventana | `ui/daemon/launch/run.py:32-38` | el comando entero |
| la campaña desatendida | `pipeline/campaign/plan.py:48` | el comando entero (descarta el activo) |
| el constructor de proyectos | `sqx/projects/builder.py:222` | sólo `pending()`: costes sin valor |
| los configuradores de MC Retest, SPP, WFM y filtros | `sqx/projects/{mcretest,spp,wfm,rankings}.py` | sólo `pending()` |
| el pipeline de una madre | `pipeline/stages/gates.py:124` | sólo `pending()` |

El guardián de comandos (`.claude/hooks/guard.py`) no vigila esta regla.

### 1.2 Qué lee

`core.assetdata.load()` (`core/assetdata.py:85-104`) junta dos ficheros en un solo diccionario (la ficha y `_policy.yaml`; el esquema de la clase, `_classes.yaml`, lo lee aparte `schema()`/`fields()`):

- `assets/symbols/<SÍMBOLO>.yaml` — lo propio del activo: clase, feeds, instrumento, costes, rangos de MC Retest, símbolo y punto de MT5 en cada firma.
- `assets/_policy.yaml` — qué es cada tramo (igual para todos) y dónde empieza y acaba **en ese activo**, con el rango de datos que SQX tiene al lado.
- `assets/_classes.yaml` — el esquema de costes de la clase (`forex` o `no_forex`): qué campos, en qué unidad, con qué ajuste de SQX.

### 1.3 Cómo decide: los códigos de salida

`core/assets.py:140-171`, en este orden:

| salida | cuándo | texto |
|---|---|---|
| **3** | `validate()` devuelve algún problema | `ESQUEMA ROTO en assets/symbols/…` |
| **2** | `pending()` devuelve algún campo | `BLOQUEADO: … sin valor pactado. Pregúntale al dueño.` |
| **1** | activo desconocido, comando sin argumento, o un error dentro del informe | traza de Python |
| **0** | todo lo demás, con o sin avisos | el informe |

El 3 se comprueba **antes** de imprimir nada: una ficha rota no enseña sus costes. El 2 se comprueba **al final**: una ficha con un coste sin decidir enseña todo lo demás primero.

### 1.4 Qué entrega

No escribe ningún fichero. Imprime el informe que la sesión debe leer en voz alta: cada coste con su unidad, el valor que SQX lleva hoy y el porqué; los datos que SQX tiene; cada tramo con sus milisegundos; los dos rangos de MC Retest; los mercados del retest; las notas del activo; y el aviso de calidad del feed. Lo que las tareas de SQX llevarán de verdad lo produce `sqx_settings(data, tramo)` (`core/assetdata.py:191-215`), que cada configurador llama por su cuenta.

### 1.5 Los dos activos que nos acompañan

| | **NIKKEI225** | **USDJPY** |
|---|---|---|
| clase | `no_forex` | `forex` |
| feed de construcción | `NIKKEI225_M1` | `USDJPY_M1` |
| datos en SQX | 2011-09-19 a 2026-10-01 | 2003-05-05 a 2026-10-01 |
| tamaño del tick (`tick_size`) | 0,01 | 0,01 |
| valor del punto (`point_value`) | 0,063137 USD por 1,0 de precio y lote | 631,337 USD por 1,0 de precio y lote |
| en MT5 | `JP225.cash` (FTMO), `JP225.h` (Hantec) | `USDJPY`, `USDJPY.h` |
| punto MT5 → SQX (`to_sqx`) | × 1 | × 0,1 |

El valor del punto es el contrato de MT5 de las firmas pasado a dólares al cambio de un día: un lote de NIKKEI son 10 yenes por punto de índice (10 / 158,39 = 0,0631 USD), un lote de USDJPY son 100.000 yenes por 1,0 de precio (631,34 USD).

---

## 2. Fundamentos de este paso

Este paso casi no tiene estadística propia; la que hay está en cómo se resume un spread que cambia cada segundo en **un solo número** por tramo y en **un rango** para el MC Retest. Siete conceptos, con cuentas de juguete.

### 2.1 Punto, tick y precio: tres unidades que se confunden

- **Unidad de precio:** lo que ves en el gráfico. NIKKEI a 17.525,70; USDJPY a 98,909.
- **Punto de SQX:** una vez el `tick_size` del instrumento. En los dos activos del ejemplo, 0,01. Todos los costes de `assets/` van en puntos de SQX.
- **Punto de MT5:** el `point` del símbolo en el servidor de la firma (10 elevado a menos sus decimales). No tiene por qué coincidir con el de SQX.

Ejemplo: un spread de 3,04 unidades de precio en el NIKKEI son 3,04 / 0,01 = **304 puntos de SQX**. Un spread de 0,0051 en USDJPY (medio pip) son 0,0051 / 0,01 = **0,51 puntos de SQX**.

### 2.2 Spread en puntos y spread relativo

El mismo spread se puede decir de dos formas: en puntos (lo que se resta al precio) o como porcentaje del precio (lo que pesa sobre la operación).

Ejemplo de juguete: un índice cotiza con 10 unidades de spread.

| precio del índice | spread en unidades | spread relativo |
|---|---|---|
| 20.000 | 10 | 0,050 % |
| 40.000 | 10 | 0,025 % |
| 60.000 | 10 | 0,017 % |

Si la firma mantiene el spread **fijo en unidades**, el coste relativo baja a un tercio cuando el precio se triplica. Si lo mantiene **fijo en %**, el spread en unidades se triplica. Qué supuesto se use para llevar el spread de hoy a 2012 decide el coste de toda la ventana de construcción. A veces se usa el punto básico (pb): 1 pb = 0,01 %.

### 2.3 Media, mediana y por qué un coste se resume con la media

Diez días con estos spreads medios: 5, 5, 6, 6, 6, 7, 7, 8, 9, 30.

- **Media:** la suma entre diez = 89 / 10 = **8,9**.
- **Mediana:** el valor central de la lista ordenada = entre el 5º y el 6º = (6 + 7) / 2 = **6,5**.

El día de 30 (una noticia, un cierre) tira de la media y no de la mediana. Para un coste manda la **media**: si operas todos los días pagas 89 en total, no 65. El código lo dice así (`studies/data/spread/README.md`: «the mean, not the median: a cost accrues its mean»).

### 2.4 Media por tiempo frente a media por tick

Un tick es un cambio de cotización. En los momentos agitados hay muchos ticks y el spread suele ser estrecho; en los tranquilos (noche, rollover) hay pocos y es ancho.

Juguete: durante un minuto la cotización lleva spread 2 durante 50 segundos, en los que llegan 9 ticks, y spread 10 durante 10 segundos, con 1 tick.

- **Media por tick:** (9 × 2 + 1 × 10) / 10 = **2,8**.
- **Media por tiempo:** (2 × 50 + 10 × 10) / 60 = **3,33**.

Una estrategia que entra a la apertura de una vela no elige el momento con más ticks: ve el spread que haya en ese instante. Le corresponde la media **por tiempo**. Para que un fin de semana no cuente como 48 horas de spread, cada cotización pesa como máximo 60 segundos.

Dato real, recalculado por mí: USDJPY en FTMO, septiembre de 2026: por tick 0,00524; por tiempo 0,00705 (un 35 % más).

### 2.5 Percentiles y dispersión

El **percentil 97,5** es el valor que deja por debajo al 97,5 % de los casos. Con los diez días de 2.3 ordenados, el percentil 90 está entre el 9º y el 10º valor (9 y 30). Entre el percentil 2,5 y el 97,5 cae el 95 % central: eso es **la banda**.

La **desviación típica** mide cuánto se alejan los valores de su media. Para los diez días: las distancias a 8,9 al cuadrado suman 508,9; dividido entre 9 da 56,5; su raíz es **7,5**. El **coeficiente de variación** es la desviación entre la media: 7,5 / 8,9 = 0,84. Como regla práctica mía (no hay umbral de coeficiente de variación en el código), por debajo de 0,2 el spread es estable y por encima de 0,5 hay días o regímenes muy distintos mezclados.

### 2.6 La curva spread = a · precio^b y qué dice el exponente

Para saber si el spread sigue al precio, el estudio ajusta `spread = a · precio^b` sobre el spread medio de cada día (`studies/data/spread/band.py:39-52`).

- **b = 1:** el spread es proporcional al precio (fijo en %).
- **b = 0:** fijo en puntos.
- **b negativo:** el spread en puntos **baja** cuando el precio sube.

Juguete: si al duplicarse el precio el spread pasa de 10 a 14, b = log(1,4) / log(2) = 0,49.

La banda se ajusta con una curva distinta para cada percentil (regresión cuantílica): en vez de minimizar el error al cuadrado, que da la media, se minimiza un error que castiga más quedarse por un lado que por el otro, y eso da el percentil pedido.

### 2.7 El sorteo uniforme del MC Retest

El MC Retest de spread repite el backtest muchas veces. En cada repetición SQX sortea **un** spread para todo el backtest, con la misma probabilidad para cualquier valor entre un mínimo y un máximo (distribución uniforme).

Dos propiedades que se sacan a mano:

- **La media del sorteo es el punto medio:** (mín + máx) / 2.
- **La probabilidad de salir por encima de un valor x** es (máx − x) / (máx − mín).

Con un rango de 0,5 a 2 veces el spread del backtest: la media del sorteo es (0,5 + 2) / 2 = **1,25** veces el spread, y la probabilidad de que una repetición sea **más cara** que el backtest es (2 − 1) / (2 − 0,5) = **2 de cada 3**. El rango no es simétrico alrededor del coste base: la repetición típica es un 25 % más cara.

### 2.8 Intervalo de confianza, en dos líneas

Cuando la ficha dice «600 operaciones reales costaron 1,33 × el spread, IC 95 % 1,08-1,72», el 1,33 es la media de esa muestra y el intervalo es el rango donde caería la media si se repitiera la medida con otra muestra del mismo tamaño. Que el intervalo sea ancho (de 1,08 a 1,72) dice que 600 operaciones agrupadas por día no fijan la cifra con precisión: el 1,7 que hoy cobra SQX está en el borde alto del intervalo, no en su centro.

---

## 3. Lo que hace y calcula, pieza a pieza

### 3.1 Las comprobaciones que bloquean

**B1 — El esquema de la clase** (`core/assetcheck.py:37-55`, salida 3). `validate()` devuelve una línea por problema:

| qué | regla | línea |
|---|---|---|
| falta un campo de coste | la clase pide un spread y un deslizamiento por tramo (`is`, `oos`, `oos2`), la comisión y los dos swaps (`core/assetdata.py:119-132`) | 48 |
| sobra un campo | un campo que la clase no tiene | 49 |
| falta `mc_retest.spread` o `mc_retest.slippage` | tienen que existir, aunque sus bordes estén vacíos | 50-51 |
| `instrument.*` no es un número | un comentario pegado al valor lo convierte en texto | 52-53 |
| un texto que se lee como número | en cualquier parte de la ficha; `1e-05` leído como texto rompió una vez el paso 26 | 14-34, 54 |
| un tramo empieza antes del primer dato | ver B2 | 55 |

**B2 — Un tramo pide histórico que SQX no tiene** (`core/assetcheck.py:113-131`, salida 3). Compara el **año** de inicio de cada tramo con el **año** del primer dato del feed. Si SQX no tiene ningún dato del feed, también bloquea.

Ejemplo real: el DAX40 tiene datos desde 2013-09-30. Una ventana de construcción desde 2008 se quedaría corta sin avisar; con esta comprobación, no arranca. Limitación: compara años, no días (apartado 5.6).

**B3 — Un coste obligatorio sin valor** (`core/assetcheck.py:59-79`, salida 2). Los obligatorios son los mismos en las dos clases (línea 9-10): `spread_is`, `spread_oos`, `spread_oos2` y `commission`. La comisión es especial: lleva un valor por tramo, y bloquea mientras **cualquiera** de los tres esté vacío.

**No bloquean:** el deslizamiento, los dos swaps, los rangos de MC Retest, las fechas de los tramos y la sesión. De la sesión se ocupa el constructor, un paso después (`sqx/projects/doctrine.py:63-81`): se niega si `session:` está vacío.

### 3.2 Las comprobaciones que sólo avisan

| aviso | regla | dónde | adónde va |
|---|---|---|---|
| **A1** tramo que acaba después del último dato | fin del tramo > última vela de SQX | `core/assetcheck.py:135-152`; `core/assets.py:159-160` | a la salida de error (`stderr`), no al informe |
| **A2** tramo sin fechas | algún borde vacío | `core/assetcheck.py:99-109`; `core/assets.py:161-163` | informe |
| **A3** rango de MC Retest sin decidir | no resuelve ni la ficha ni los múltiplos de la política | `core/assetcheck.py:156-172`; `core/assets.py:164-167` | informe |
| **A4** calidad del feed | ver 3.11 | `core/assets.py:105-137` | informe |
| **A5** tramo reservado | sólo con `ALGO_AUTONOMOUS=1` | `core/assets.py:84-85` | informe |

A1 es el estado normal del tramo más reciente: la ventana es correcta y los datos aún no se han sincronizado. Hoy no salta en ningún activo.

A2 no bloquea porque `window()` se niega por su cuenta a inventar una ventana (`core/assetdata.py:166-169`): cualquier configurador que la pida se para ahí.

### 3.3 Costes provisionales: ni bloqueo ni aviso

`provisional()` (`core/assetcheck.py:83-95`) devuelve los campos cuyo `why` contiene la palabra `PROVISIONAL`. No lo imprime el comando del activo; sólo marca el índice (`assets/INDEX.md`) y el registro de proyectos (`sqx/projects/builder.py:166`) y el ledger del pipeline (`pipeline/ledger/state.py:93`). Hoy ningún activo lleva la palabra.

### 3.4 Los tres tramos: qué son y cómo se convierten en fechas

**Qué son** (`assets/_policy.yaml:25-48`, igual para todos los activos):

| tramo | papel | spread que usa | quién lo lee |
|---|---|---|---|
| `build` | construcción: la única muestra que ve el generador | `spread_is` | paso 6 |
| `oos1` | del retest a los SPP | `spread_oos` | pasos 7 a 16, 22 y 23 |
| `oos2` | el último fuera de muestra | `spread_oos2` | pasos 17, 18, 18.5, 19, 20 y 24 |

**Por qué tres.** La muestra de construcción se gasta al generar: cualquier cifra medida ahí está inflada por la búsqueda. `oos1` se gasta filtrando: cada paso del 7 al 16 elige con él, así que al final ya no es una muestra limpia. `oos2` queda para la última lectura, cuando ya no se va a elegir más. La reserva formal de `oos2` (`reserved_for`) sólo obliga a un agente autónomo (`core/assetdata.py:21-27`); un humano puede mirarlo cuando quiera (dueño, 2026-09-28). El ledger cuenta cada mirada igualmente.

Los costes de los tres tramos salen de ticks de 2025-2026, es decir, de dentro de `oos2`. No es una fuga (no se eligieron mirando estrategias), pero los tramos no son comparables en coste: en NIKKEI225, `build` y `oos1` corren por debajo de lo medido y `oos2` por encima (5.3).

**Dónde caen, por activo** (`assets/_policy.yaml:50-198`):

| | `build` | `oos1` | `oos2` | reparto |
|---|---|---|---|---|
| NIKKEI225 | 2011-09-19 → 2019 (8,3 años) | 2020 → 2023 (4 años) | 2024 → 2026-09-30 (2,75 años) | 55 % / 27 % / 18 % |
| USDJPY | 2008 → 2017 (10 años) | 2018 → 2022 (5 años) | 2023 → 2026-09-30 (3,75 años) | 53 % / 27 % / 20 % |

Hay dos familias: forex y metales construyen 2008-2017 (aunque haya datos desde 2003); índices, crudo y cobre construyen desde su primer dato hasta 2019. Por qué 2008 en forex y no 2003 no está escrito en ningún fichero: es la ventana del oro heredada (la skill lo dice: «the owner did not restate them»).

**El final de `oos2` se mueve solo:** el primer sábado de cada mes `bin/monthly-oos2-roll.sh` lo lleva al último día del mes anterior, sólo si los datos llegan (`assets/RULES.md:161-165`).

**Cómo se convierten en milisegundos** (`core/assetdata.py:135-170`). Un borde es un año o una fecha, y los dos extremos son **inclusivos**:

- inicio `2011-09-19` → ese día a las 00:00 UTC → `1316390400000`;
- fin `2019` → el año entero → primer instante de 2020 → `1577836800000`.

El `dateTo` de `build` y el `dateFrom` de `oos1` son el mismo número: el instante 2020-01-01 00:00 pertenece a los dos. Es un instante sin vela en casi todos los mercados.

### 3.5 El spread por tramo: de dónde sale cada cifra

**La regla en vigor** (`assets/RULES.md:93-100`, dueño 2026-10-04): el spread medio **por tiempo** de la firma **más ancha** como % del precio (la mayor de sus medias de 12 y de 3 meses), por el **precio medio de cada tramo**, sin factor de seguridad (`ledger/thresholds.yaml:1030-1037`: `spread.safety.factor = 1.0`).

**La cuenta para NIKKEI225, recalculada por mí.** Media por tiempo de cada mes (tres días por mes, tope de 60 s por cotización), últimos 12 meses muestreados (2025-10 a 2026-09):

| firma | meses con ticks | spread medio (unidades de precio) | % del precio, media 12 m | media 3 m |
|---|---|---|---|---|
| FTMO (`JP225.cash`) | 32 | 8,15 (de 4,4 a 11,8 según el mes) | 0,01364 % | 0,01641 % |
| Hantec (`JP225.h`) | 44 | 5,00 fijo | 0,00866 % | 0,00749 % |
| **FundingPips** | 19 | **≈10,0 (10,000-10,060 salvo dos meses)** | **0,01735 %** | 0,01500 % |

La más ancha es FundingPips con 0,01735 %, y su media de 12 meses es mayor que la de 3. La ficha lleva implícito 0,017352 % (304,11 × 0,01 / 17.525,7). Coincide.

| tramo | precio medio (ficha) | × 0,017352 % | ÷ tick 0,01 | ficha |
|---|---|---|---|---|
| `build` | 17.525,7 | 3,0411 | 304,11 | **304,11** |
| `oos1` | 27.368,7 | 4,7490 | 474,90 | **474,91** |
| `oos2` | 45.879,8 | 7,9611 | 796,11 | **796,12** |

Los precios medios que saco de la tabla diaria del estudio de spread son 17.572,6 / 27.359,8 / 45.730,5: difieren un 0,3 %, un 0,03 % y un 0,3 % de los de la ficha. No he podido reproducir los de la ficha al decimal porque el script que los calculó no está en el repo.

**La cuenta para USDJPY.**

| firma | % del precio, media 12 m | media 3 m |
|---|---|---|
| **FTMO** | **0,00514 %** | 0,00432 % |
| FundingPips | 0,00303 % | 0,00322 % |
| Hantec | 0,00131 % | 0,00166 % |

| tramo | precio medio | × 0,005135 % | ÷ 0,01 | ficha |
|---|---|---|---|---|
| `build` | 98,909 | 0,005079 | 0,508 | **0,51** |
| `oos1` | 113,513 | 0,005829 | 0,583 | **0,58** |
| `oos2` | 149,483 | 0,007676 | 0,768 | **0,77** |

0,51 puntos de SQX es medio pip.

**«Medido y modelado hacia atrás»: eso es el método anterior, y es el que sigue en el código.** `studies/data/spread/` mide el spread de Darwinex minuto a minuto desde octubre de 2017 y, para los años sin ticks, lo reconstruye con uno de cuatro modelos (`model.py:38-45`): `relativo` (fijo en %), `puntos` (fijo en unidades), `volatilidad` y `volatilidad_precio`. Elige el que menos se equivoca prediciendo años que no vio (`verdict.py:34-57`), salvo que tú lo fijes: para los índices fijaste `relativo` (`config.yaml:82-89`). La cifra por tramo es `media del relativo × precio medio ÷ tick × factor` (`verdict.py:73-86`).

Lo que ese estudio dejó escrito el 2026-09-27, con factor 1,25:

| | `build` | `oos1` | `oos2` | días medidos en `build` |
|---|---|---|---|---|
| NIKKEI225 | 606,7 | 915,5 | 559,1 | 29 % |
| USDJPY | 0,48 | 0,57 | 1,17 | 2,4 % |

**Las tres cifras, una al lado de otra, para NIKKEI225** (puntos de SQX; la columna Darwinex es la media de los días medidos, calculada por mí desde `band_days.parquet`):

| tramo | ficha hoy (firma × 1,0) | Darwinex medido, media | Darwinex p2,5 – p97,5 | propuesta de septiembre (× 1,25) |
|---|---|---|---|---|
| `build` | 304 | 747 (sólo 2017-10 a 2019, 577 días) | 516 – 1.015 | 607 |
| `oos1` | 475 | 732 (1.034 días) | 501 – 980 | 916 |
| `oos2` | 796 | 458 (705 días) | 292 – 906 | 559 |

Y para USDJPY:

| tramo | ficha hoy | Darwinex medido, media | p2,5 – p97,5 |
|---|---|---|---|
| `build` | 0,51 | 0,49 (sólo 65 días de 2017) | 0,41 – 0,58 |
| `oos1` | 0,58 | 0,48 | 0,29 – 0,91 |
| `oos2` | 0,77 | 0,93 | 0,61 – 1,35 |

En USDJPY las dos fuentes están cerca. En NIKKEI225 no: la ficha cobra en `build` y `oos1` menos que casi cualquier día que Darwinex cotizó, y en `oos2` bastante más.

### 3.6 El deslizamiento

**Regla** (`studies/data/spread/config.yaml:92`, dueño 2026-10-04): 35 % del spread de su tramo, por pata.

| | `build` | `oos1` | `oos2` |
|---|---|---|---|
| NIKKEI225 | 304,11 × 0,35 = **106,44** | 474,91 × 0,35 = **166,22** | 796,12 × 0,35 = **278,64** |
| USDJPY | 0,51 × 0,35 = 0,1785 → **0,18** | 0,203 → **0,20** | 0,2695 → **0,27** |

SQX lo aplica en la entrada **y** en la salida. Así una operación paga spread × (1 + 2 × 0,35) = **spread × 1,7**. De dónde sale el 35 %: 600 operaciones reales en FTMO, Hantec y FundingPips costaron de media 1,33 veces el spread medio de 12 meses de la firma más ancha, con intervalo al 95 % de 1,08 a 1,72 (`knowhow/costs/funded-tick-spread-vs-price.md`). El 1,7 queda justo por debajo del borde alto del intervalo (1,72). Por firma, FundingPips costó 1,64: el 1,7 le deja un 4 % de margen. Las salidas por stop costaron 1,23-1,24 spreads por pata en FTMO y FundingPips, y las salidas por señal 0,44-0,60: una operación que entra por señal y sale por stop cuesta 0,44 + 1,24 = 1,68 en FTMO y 0,60 + 1,23 = 1,83 en FundingPips (calculado por el revisor sumando las cifras por pata de la tarjeta), es decir, más de lo que SQX cobra justo en las operaciones perdedoras.

Con el deslizamiento dentro, la fricción total de la ficha en NIKKEI225 es 304 × 1,7 = 517 puntos en `build` y 475 × 1,7 = 807 en `oos1`. A igualdad de trato (el mismo factor sobre las dos cifras) la fricción de la ficha es el 65 % de la medida en `oos1` y el 41 % en `build` (calculado por el revisor: ficha entre media de Darwinex en cada tramo; con el 1,7 aplicado también al spread medido de `oos1` serían 1.245, y con el 1,33 medido, 974).

### 3.7 La comisión

Un valor por tramo, en el método de la clase (`core/assetdata.py:210-213`).

- **NIKKEI225:** `PercentageBased 0,0` en los tres tramos. Decisión tuya del 2026-09-29: los índices no pagan comisión en ninguna firma. Confirmado en las operaciones reales de FTMO y Hantec (`knowhow/costs/funded-accounts-real-costs.md`).
- **USDJPY:** `SizeBased 5,0` en los tres tramos: 5 USD por lote ida y vuelta. Las operaciones reales dan 2,50 USD por lote y lado en las dos firmas. Si SQX cobra el `SizeBased` en cada pata, serían 10 USD por lote, y la ida y vuelta de 4.3 sería 15,49 USD (2,45 pips, comisión el 65 %) en vez de 10,49 USD.

`PercentageBased` se cobra **una vez** por operación, sobre el precio de apertura (verificado operación a operación el 2026-09-27, `knowhow/costs/commission-methods.md`). `SizeBased` cobra en el mismo sitio del código, pero su comprobación operación a operación está pendiente según la misma tarjeta.

### 3.8 El swap

**Regla** (dueño, 2026-10-01; `studies/data/spread/fundedswap.py:29-70`): cada lado es el **peor** de FTMO y Hantec, leído en vivo de sus servidores de MT5 ese día. «Peor» es el número más bajo: el más negativo si se cobra, el menos positivo si se abona.

**NIKKEI225, en % anual sobre el nocional** (`fundedswap.py:17-19`): `puntos MT5 × point ÷ precio × 36.000`.

| lado | FTMO (puntos MT5 por noche) | Hantec | peor | ficha |
|---|---|---|---|---|
| largo | −906,33 | −838,03 | FTMO | **−4,78 %** |
| corto | −302,11 | −355,65 | Hantec | **−1,87 %** |

Comprobación: 906,33 × 0,01 × 36.000 = 326.279; dividido entre 4,78 da un precio de 68.259. Es coherente con el NIKKEI de ese día. La ficha guarda `commission.brokers.ftmo.price_now` = 67.087,52 (2026-10-01, de la barstore, no el bid que leyó el servidor): con él salen 4,863 %, no 4,78 %, y el precio implícito (68.259) difiere un 1,7 % de ese `price_now` (cuentas del revisor).

Cómo lo cobra SQX: `tamaño × valor del punto × precio de apertura × (% / 100 / 360)` por noche, triple el **viernes** en los índices (la ficha lo declara; el resto, miércoles).

**USDJPY, en puntos de SQX por noche** (`fundedswap.py:12-14, 62`): dólares por lote y noche de la firma, divididos entre `valor del punto × paso del tick` del instrumento de SQX.

| lado | FTMO (puntos MT5) | Hantec | peor | ficha |
|---|---|---|---|---|
| largo | +2,56 | +3,55 | FTMO | **+2,57** |
| corto | −17,42 | −22,10 | Hantec | **−22,15** |

El paso del tick de USDJPY en el registro de SQX es 0,001, no 0,01 (lo he leído de `SQX_w1/user/data/data.db`, sólo lectura). Así +2,57 puntos son 2,57 × 0,001 × 631,337 = **+1,62 USD por lote y noche**, que es lo que FTMO abona (2,56 × 0,001 × 100.000 yenes ÷ 158,39). A mano, 2,56 puntos salen 1,616 USD y la ficha (2,57) da 1,6225 USD: la ficha difiere 0,2-0,4 % del cálculo a mano (también en el corto, −22,10 → −22,15) porque `fundedswap.py` convierte con `trade_tick_value/trade_tick_size` en vivo, no con el 100.000/158,39 de esta cuenta.

Esto no está verificado operación a operación: la única comprobación (2026-10-04, 1.050 operaciones largas de USDJPY, `knowhow/costs/swap-types.md`) encontró +26,1 USD por operación de residuo donde la ficha predice +5,4, sin explicación. El sesgo, si existe, es a favor de los largos.

El swap no bloquea, y es **la cifra de un día**: la ficha lo dice («cambia con los tipos»).

### 3.9 El rango del MC Retest

**Regla** (`core/assetranges.py:10-43`): si la ficha escribe los bordes, mandan. Si los deja vacíos (todas lo hacen desde el 2026-10-04), el rango es un múltiplo del coste del tramo en que corre la tarea: el `multiples` propio de la ficha o, si no tiene, el de la política, **0,5× a 2×** (`assets/_policy.yaml:248-254`). Si el rango sale más estrecho que 1 punto, el máximo se sube a mínimo + 1 (línea 41).

| | tramo | spread | deslizamiento |
|---|---|---|---|
| NIKKEI225 (0,5×–2×) | `build` | 152,06 – 608,22 | 53,22 – 212,88 |
| | `oos1` | 237,46 – 949,82 | 83,11 – 332,44 |
| USDJPY (0,5×–2,7×) | `build` | 0,255 – 1,377 | 0,09 – **1,09** |
| | `oos1` | 0,29 – 1,566 | 0,10 – **1,10** |

El preflight sólo imprime el rango de `build` (`core/assets.py:92`). Las tareas MCR 2 y 3 corren sobre `build`; MCR 8 lleva los costes de `oos1` y por tanto otro rango, que el informe no enseña.

**De dónde vendría un rango medido.** El estudio de spread calcula dos cosas que hoy no se usan:

- `verdict.mc_multiples` (`verdict.py:116-133`): los percentiles 2,5 y 97,5 del cociente «spread del día ÷ media del modelo». NIKKEI225: **0,27× a 1,99×**. USDJPY: **0,65× a 1,47×**.
- La banda `spread = a · precio^b` (`bands.py`). NIKKEI225: exponente de la media **b = −0,63** (el spread en puntos de Darwinex bajó al subir el precio); al último precio, banda de 172 a 898 puntos. USDJPY: b = +2,26.

La onboard ya no escribe ninguno de los dos (`onboard.py:101-104`).

### 3.10 La conversión de puntos MT5 → SQX

`to_sqx = point de MT5 ÷ tick_size de SQX`, guardado por activo y por firma en la ficha (`mt5_point.<firma>.to_sqx`). Una cifra leída en MT5 entra en SQX multiplicada por él.

| activo | firma | `point` MT5 | `tick_size` SQX | `to_sqx` | ejemplo |
|---|---|---|---|---|---|
| NIKKEI225 | FTMO, Hantec | 0,01 | 0,01 | **1** | 1.000 puntos en MT5 = 1.000 en SQX |
| USDJPY | FTMO, Hantec | 0,001 | 0,01 | **0,1** | spread de 8 en MT5 = 0,8 en SQX |
| EURUSD | FTMO, Hantec | 0,00001 | 0,0001 | **0,1** | spread de 2 en MT5 = 0,2 en SQX |
| UKOIL | FTMO | 0,001 | 0,001 | **1** | |
| UKOIL | **Hantec** | 0,01 | 0,001 | **10** | spread de 6 en MT5 = 60 en SQX |

No es siempre «dividir entre 10»: el Brent de Hantec se **multiplica** por 10.

Dos matices:

- **Ningún código lee `to_sqx`.** Es una nota para quien configura a mano. El paso 26 calcula la conversión con el `point` que el servidor da en ese momento y avisa si difiere del guardado (`mt5/verify/conditions.py:84-88`).
- **El swap en puntos es otra unidad.** En forex SQX lo cobra con el paso del tick (`TICKSTEP`), diez veces menor que el `tick_size`. El spread y el deslizamiento van en `tick_size`.

### 3.11 El aviso de calidad del feed

`core/assets.py:105-137` lee `AlgoData/feedQuality/<feed>/summary.json`, que escribe `python3 -m studies.data.feedQuality.scan`. Si el feed nunca se escaneó, no imprime nada.

**Qué cuenta como anomalía.** Para cada minuto, el movimiento del cierre se divide entre una escala propia de esa hora de la semana (una medida robusta de lo que suele moverse en esa hora, sobre las 52 semanas anteriores). Si el resultado llega a K, es un pico. K se fija por feed (15, 20, 25 o 30): el menor que deja menos de 52 picos de cierre al año en 2013-2019. Se marcan cinco cosas (`studies/data/feedQuality/summary.py:10, 45`):

- pico de cierre que se deshace en tres velas;
- pico de mecha que se deshace;
- congelado: 10 o más velas seguidas idénticas;
- hueco: 5 o más minutos de sesión sin vela;
- caída del proveedor: silencio de 5 a 179 minutos compartido por todos los feeds.

Un pico que **no** se deshace es «movimiento extremo» y no se marca: es mercado, no error.

**El año estable** (`summary.py:80-88`). G = huecos propios + caídas del proveedor de cada año. La base es la mediana de G desde 2013. Un año está bien si G ≤ máx(3 × base, 30). El año estable es el primero a partir del cual **todos** los siguientes están bien. Un año anterior es «calidad B» si G ≤ máx(10 × base, 30), e «inestable» si no.

**NIKKEI225** (K = 20; base = 238 huecos; umbral estable 714; umbral B 2.380):

| año | huecos | marcadas | grado |
|---|---|---|---|
| 2011 (desde septiembre) | 13 | 13 | B |
| 2012 | 887 | 887 | B |
| 2013 – 2016 | 200 a 309 | 204 a 674 | B |
| **2017** | **2.429** | 2.431 | **inestable** |
| 2018 | 357 | 362 | B |
| **2019** | **2.026** | 2.027 | B |
| 2020 | 543 | 551 | estable |
| 2021 – 2023 | 134 a 290 | 137 a 291 | estable |
| 2024 – 2026 | 13 a 38 | 18 a 52 | estable |

2019 rompe la racha (2.026 > 714), así que el primer año estable es 2020. Los años 2013-2016 y 2018 quedan como «B» aunque sus huecos estén por debajo de 714, porque van antes de un año malo.

El comando imprime para NIKKEI225:

```
calidad del feed NIKKEI225_M1: 291 anomalías marcadas por año (mediana desde 2013, K = 20), estable desde 2020
AVISO: la construcción empieza en 2011, antes del año estable 2020: esos años son calidad B y inestable.
episodios de congelado: 2014-09, 2014-10, 2014-11, 2014-12.
episodios de hueco: 2017-05, 2017-06, 2017-07, 2017-08, 2017-10, 2019-04, 2019-06, 2019-07, 2019-11, 2019-12, 2023-02.
```

La mediana anual es de 291 anomalías marcadas y la de huecos propios es 245 (dos medianas independientes sobre 2013-2025, `scan.py:37-39`; 245 + 3 + 1 no suma 291, y el año de la mediana, 2023, tiene 291 marcadas y 290 huecos); los picos que se deshacen son 3 de cierre y 1 de mecha al año. La «base 238» del año estable es otra mediana, de huecos más caídas e incluyendo 2026 parcial (`summary.py:82`). Un «episodio» es un mes con más de 5 veces la mediana de los 36 meses anteriores y al menos 5 sucesos (`summary.py:102-111`).

**USDJPY** (K = 30): 14 anomalías por año, estable desde 2005, sin aviso: la construcción empieza en 2008.

---

## 4. El criterio cargado y por qué

El paso 4 no tiene reglas en `pipeline/autopilot/criteria.yaml` ni hechos en `facts.py`: no juzga estrategias. Su criterio son las negativas del código y los números de las fichas.

### 4.1 Las negativas

| | qué | por qué bloquea |
|---|---|---|
| salida 3 | ficha que no cumple su clase | una ficha de forex con el swap en % o un índice sin `spread_oos2` produce tareas con un coste a cero sin que nadie lo vea |
| salida 3 | tramo anterior al primer dato | SQX corre la ventana corta sin quejarse y el número de operaciones por año sale falso |
| salida 2 | spread o comisión sin valor | días de máquina sobre backtests sin coste |

**Por qué el deslizamiento y el swap no bloquean.** `_classes.yaml` lo explica para el deslizamiento: «un 0 es una decisión declarada, a diferencia de un spread sin pactar». Para el swap no hay razón escrita; hoy todas las fichas lo llevan.

**Por qué la calidad del feed no bloquea.** Respuesta tuya 3.1 del encargo 17 (`core/assets.py:113-114`): avisa, nunca bloquea.

### 4.2 Los números de política que hay detrás de cada cifra

| número | valor | quién y cuándo | dónde |
|---|---|---|---|
| factor de seguridad sobre el spread | 1,0 (antes 1,25) | dueño, 2026-10-04 | `ledger/thresholds.yaml:1030` |
| parte del spread que es deslizamiento | 0,35 (antes 0,5) | dueño, 2026-10-04 | `studies/data/spread/config.yaml:92` |
| rango de MC Retest por defecto | 0,5× – 2× (antes 1× – 4×) | dueño, 2026-10-04 | `assets/_policy.yaml:248-254` |
| ancho mínimo del rango | 1 punto | agente | `core/assetranges.py:7` |
| comisión forex | 5 USD por lote | dueño, 2026-09-29 | cada ficha |
| comisión índices | 0 | dueño, 2026-09-29 | cada ficha |
| swap | el peor de FTMO y Hantec, de hoy | dueño, 2026-10-01 | `fundedswap.py` |
| modelo del spread hacia atrás en índices | `relativo` | dueño, 2026-09-27 | `config.yaml:82-89` |
| tolerancia de «relativo constante» | ± 20 % | — | `ledger/thresholds.yaml:727` |
| año estable: factor, factor B, suelo, año base | 3, 10, 30, 2013 | — | `ledger/thresholds.yaml:360-441` |

### 4.3 Qué cuesta una operación con lo cargado

**NIKKEI225, un lote, ida y vuelta en `build`:**

| concepto | cuenta | USD |
|---|---|---|
| spread | 304,11 × 0,01 × 0,063137 | 0,1920 |
| deslizamiento, dos patas | 2 × 106,44 × 0,01 × 0,063137 | 0,1344 |
| comisión | 0 | 0 |
| **total** | | **0,3264** |

Nocional del lote: 17.525,7 × 0,063137 = 1.106,5 USD. El total es el **0,0295 %**: 5,2 puntos de índice sobre un índice a 17.526. En `oos1` es el mismo 0,0295 % (0,51 USD sobre 1.728).

Una noche en largo: 1.106,5 × 4,78 % / 360 = 0,147 USD = **0,0133 %**. Es decir, **cada noche en largo cuesta el 45 % de una ida y vuelta completa**. Una semana (cinco noches, con la triple del viernes: siete cargos) cuesta 0,093 %, **3,1 veces** la fricción de entrar y salir. En una estrategia larga de varios días sobre el NIKKEI, el swap pesa más que el spread.

**USDJPY, un lote, ida y vuelta en `build`:**

| concepto | cuenta | USD |
|---|---|---|
| spread | 0,51 × 0,01 × 631,337 | 3,22 |
| deslizamiento, dos patas | 2 × 0,18 × 0,01 × 631,337 | 2,27 |
| comisión | 5,00 | 5,00 |
| **total** | | **10,49** |

Son 1,66 pips (un pip vale 6,31 USD con ese valor del punto) y el 0,0105 % de 100.000 USD. Casi la mitad es comisión (47,7 %). Eso si el `SizeBased 5` es ida y vuelta; si SQX lo cobra por pata (sin verificar, 3.7), el total es 15,49 USD = 2,45 pips y la comisión es el 65 %.

Una noche en largo **abona** 1,62 USD; en corto cobra 22,15 × 0,001 × 631,337 = 13,98 USD. Seis o siete noches en largo devuelven la fricción entera de la operación si ésta es de 10,49 USD (nueve o diez si es de 15,49).

### 4.4 Cuánto mueve el sorteo del MC Retest

Con el apartado 2.7:

| | rango (× coste base) | media del sorteo | repeticiones más caras que el backtest |
|---|---|---|---|
| NIKKEI225, spread y deslizamiento | 0,5 – 2 | 1,25 × | 67 % |
| USDJPY, spread | 0,5 – 2,7 | 1,60 × | 77 % |
| USDJPY, deslizamiento (`build`) | 0,5 – 6,06 | 3,28 × | 91 % |

---

## 5. Lo que no cuadra o no está medido

### 5.1 El método del spread de las fichas no tiene comando

Las 27 fichas dicen «recalibrado 2026-10-04 — … firma más ancha … media de 12 meses de sus ticks». No hay ningún módulo en el repositorio que lo calcule (busqué `ticks_hist` y `la más ancha`: sólo aparecen en las fichas y en una tarjeta de `knowhow/`). El único comando que escribe spreads, `studies.data.spread.onboard --write`, usa Darwinex y un modelo (`onboard.py:55-92`), y deja en el `why` «spread medio de Darwinex del tramo». Lo que escribe hoy el código no es el ×1,25 y la mitad de los textos: `plan()` usa el factor del ledger (1,0, `studies/data/spread/config.yaml:91`, `ledger/thresholds.yaml:1030-1031`) y el 35 % (`config.yaml:92`). Lo que sí pisa, y los textos no dicen, es la comisión forex de 8 USD (`config.yaml:121`, `onboard.py:77-79,122-123`, frente a los 5 USD de las 14 fichas forex), los tramos y el swap, salvo con `--spread-only`. Consecuencias:

- la próxima recalibración (los spreads de las firmas cambian de régimen: FTMO pasó de 4,4 a 11,8 unidades en el NIKKEI en un año) no se puede repetir igual;
- un alta nueva con `/asset-onboard` sale con el método antiguo, distinto del de las otras 27;
- la skill avisa de que `--spread-only` es «el modo por defecto para un activo existente».

### 5.2 Cinco documentos describen el método anterior

Los textos desfasados son éstos (skill, capítulo 59, `RULES.md`, `_classes.yaml`, `WORKFLOW.md`), no el cálculo de `onboard.py`, que ya usa 1,0 y 35 % (5.1).

| documento | dice | la ficha lleva |
|---|---|---|
| `.claude/skills/asset-onboard/SKILL.md` (tabla de reglas) | spread de Darwinex × 1,25; deslizamiento la mitad; comisión 8 USD por lote | firma más ancha × 1,0; 35 %; 5 USD |
| manual, cap. `59-spread-real.md` (líneas 7, 57, 151-152) | «ya con tu factor de seguridad de 1,25», «el slippage (la mitad)», «8 USD por lote» | lo mismo |
| `assets/RULES.md:52-58` (tabla de clases) | forex: **un** `spread`; no_forex: dos | las dos clases: tres, uno por tramo (`core/assetcheck.py:9-10`) |
| `assets/RULES.md:238-240` | UKOIL 90 puntos, «× 1,25» | UKOIL 52,44 / 55,63 / 58,24 |
| `assets/_classes.yaml` (nota del deslizamiento, las dos clases) | «es la mitad del spread de su tramo» | 35 % |
| `assets/_classes.yaml:57` (fórmula del swap de forex) | `… × tick_size × puntos` | SQX usa el paso del tick, diez veces menor (`knowhow/costs/swap-types.md`); con la fórmula escrita, el swap de USDJPY sería 16,2 USD por noche en vez de 1,62 (el largo), y el corto pagaría 139,8 USD en vez de 13,98 (multiplicado por diez los dos lados). Hoy ningún código la usa: las fichas y `fundedswap.py:57` están en `TICKSTEP`, el error vive sólo en la fórmula escrita |
| `assets/_classes.yaml` y `RULES.md:77-78` (comisión en %) | «si se cobra una o dos veces está SIN VERIFICAR» | verificado el 2026-09-27: una vez |
| `WORKFLOW.md`, fila del paso 4 | spread real «hoy XAUUSD y USDJPY»; sólo el Brent (109) y la plata (33) pasan del listón de 30 huecos | el estudio cubre 23 activos; NIKKEI225 tiene 245 huecos propios al año, AUS200 559, HK50 346, USOIL 148 |

### 5.3 La ficha del NIKKEI225 cobra en `build` y `oos1` menos de lo que nadie midió

En `oos1` Darwinex midió todos los días: media 732 puntos, percentil 2,5 de 501. La ficha cobra 475. En la parte medida de `build` (octubre de 2017 a 2019): media 747, percentil 2,5 de 516; la ficha cobra 304, y **ni el máximo del MC Retest (608) llega a la media medida**. En `oos2` es al revés: la ficha cobra 796 y Darwinex midió 458.

Lo que hay que tener presente para leerlo bien:

- Darwinex no es una firma de fondeo, y tu prioridad es el fondeo. Pero es la única fuente con ticks de 2017 a 2023. Eso no es un motivo para descontar su medida: en el único periodo con las dos fuentes (2025-2026) la firma más ancha cotiza entre 1,6 y 2,9 veces lo que Darwinex (calculado por el revisor: 1.000 puntos fijos de FundingPips contra la media de Darwinex de 2025, 343, y de 2026, 625, en `band_days.parquet`). La medida de Darwinex de 2017-2023 es por tanto más probablemente un suelo que un techo de lo que una firma habría cobrado.
- El cociente entre la ficha y la media medida de Darwinex es 0,41 en `build`, 0,65 en `oos1` y 1,74 en `oos2` (calculado por el revisor: spread de la ficha entre la media de los días medidos en cada tramo; sólo el 1,3 % de los días de `oos1` cotizó por debajo de la ficha, y el 94,9 % de los de `oos2`). El coste relativo a lo medido sube en escalón justo en las fronteras de los tramos: la caída de una estrategia de `oos1` a `oos2` mezcla pérdida de filo con subida de coste, y no se pueden separar.
- La tarjeta de `knowhow/` que justifica el cambio dice, en su título, lo contrario de lo que se aplicó: «los spreads de los índices son casi constantes en **puntos**, no en % del precio», y que llevar el % de hoy al precio de un tramo antiguo «infravalora el coste de un índice entre 2 y 4 veces». La decisión del 2026-10-04 está escrita debajo como tuya y deliberada («% a propósito»).
- La firma más ancha en % (FundingPips) cotiza hoy **unos 1.000 puntos** (10,000-10,060 unidades en 17 de 19 meses; FTMO está algo por encima en puntos, ≈1.090 desde abril, aunque su media de 12 meses en % es menor; calculado por el revisor). Un backtest de 2012 con el spread de hoy en puntos llevaría 1.000; con el % de hoy lleva 304.

No está medido cuántas estrategias de una población cambian de signo entre 304 y 747 puntos. El paso 8 tiene una lectura de «coste de equilibrio» (`c*`) que podría contestarlo sobre una cosecha ya hecha.

### 5.4 El swap abonado de hoy se aplica a toda la historia

`fundedswap.worst()` devuelve el swap del día. 16 de los 27 activos tienen un lado positivo: los cinco pares con yen y USDCAD, USDCHF, AUDNZD en largo; EURUSD, EURAUD, NZDUSD y cinco índices y metales en corto. `assets/RULES.md:235-237` recoge tu decisión para el crudo: el lado abonado se escribe 0, porque aplicarlo hacia atrás «era un regalo para todos los largos». Para los demás activos esa regla no existe.

Tamaño en USDJPY: +1,62 USD por lote y noche son +592 USD al año, el +0,59 % del nocional, abonado también en 2009-2015, cuando el diferencial de tipos entre dólar y yen era casi cero. Como por defecto las plantillas son largas, una construcción larga en un cruce del yen lo recibe entero.

En el otro sentido, el −4,78 % anual del NIKKEI largo también es de hoy. No hay ninguna serie histórica de swap en el proyecto.

Los dos errores no se compensan: caen en activos y direcciones distintas. El abono de hoy llevado atrás favorece a los largos del yen; el cargo de hoy llevado atrás perjudica a los largos del NIKKEI. Por operación, un largo de USDJPY que duerme tres noches recibe 4,86 USD (calculado por el revisor: 3 × 1,62), el 46 % de su fricción de 10,49 USD, o el 31 % si la fricción es de 15,49 USD (3.7).

### 5.5 El ancho mínimo convierte el rango de deslizamiento de forex en otro

`core/assetranges.py:41`: `max(2,7 × 0,18; 0,09 + 1) = 1,09`. El rango real es 0,09 a 1,09: de 0,5 a 6 veces el deslizamiento. La cadena `source` que imprime el preflight sigue diciendo «0.5x-2.7x el slippage de `build`». La media del sorteo es 3,3 veces la base y 9 de cada 10 repeticiones son más caras que el backtest.

El motivo del mínimo es real (SQX sortea en pasos de 0,1 puntos; con pocos pasos la tarea sale con muy poca dispersión (con un paso, ninguna); la tarjeta `knowhow/costs/mc-retest-ranges.md` pide al menos 5-10 pasos). Pero el efecto es que MCR 3 en forex es una prueba de estrés mucho más dura que en un índice, sin que esté dicho en ningún sitio. En el spread de USDJPY no ocurre (1,377 > 1,255).

El ancho mínimo no afecta sólo a USDJPY. Rehecho para los 27 activos (calculado por el revisor con `core.assetranges.mc_retest()` en memoria), ensancha el rango de deslizamiento de `build` en 10 pares, con este factor sobre el rango declarado: AUDUSD 5,05×, CADJPY 2,77×, EURGBP 4,35×, EURJPY 2,88×, EURUSD 9,59× (rótulo «0.5x-6.0x», es decir, de 0,5× a 9,6×: peor que el caso de USDJPY), GBPUSD 3,62×, NZDUSD 3,28×, USDCAD 5,5×, USDCHF 3,36× y USDJPY 6,06×. AUDJPY, AUDNZD, EURAUD y GBPJPY no.

Además, en cualquier activo el MC Retest de spread sortea un nivel constante para todo el backtest: mide qué pasa si el coste medio fuera otro, no qué pasa cuando el spread se abre a la hora en que la estrategia entra (no simula el rollover, la apertura ni una noticia). En índices el techo (608 en `build` en NIKKEI225) no llega a la media que Darwinex midió (747): la prueba de estrés más dura sigue siendo más barata que la realidad medida.

### 5.6 Las comprobaciones de las ventanas tienen huecos

- **B2 compara años** (`assetcheck.py:127-131`). Un `build: {from: 2011}` con datos desde 2011-09-19 pasaría, y la ventana se quedaría ocho meses corta. Hoy no ocurre en ningún activo: los que empiezan a mitad de año llevan la fecha exacta.
- **No se comprueba** que `from` sea anterior a `to`, que los tramos no se solapen, ni que sean contiguos.
- **A1 va a `stderr`** y el informe no lo incluye. `ui/daemon/launch/run.py:33-38` captura la salida y sólo enseña `stderr` si el comando falla: desde la ventana, ese aviso no se ve nunca.
- **`data:` es una foto.** Se refresca con `python3 -m core.assets --dataranges`. Si no se ejecuta tras actualizar los datos, A1 y B2 comparan contra un rango viejo.

### 5.7 Una comisión sin decidir rompe el informe

`report()` llama a `mc_retest()`, que llama a `sqx_settings()`, que hace `use("commission")[segment]` (`core/assetdata.py:210`). Con `use: null` eso es un `TypeError`. Lo he comprobado sustituyendo el valor en memoria. La ventana crea los activos nuevos con todos los costes en `null` (`assets/RULES.md:311-313`), pero también con `data: null`, y `validate()` (`assetcheck.py:124-125`) lo para antes con «SQX no tiene datos…», salida 3, sin imprimir nada. La traza aparece cuando `data:` ya está relleno (`core.assets --dataranges` o `sqx/data/update.py:123`): entonces el primer preflight de un activo nuevo acaba en traza, con salida 1, y no en «BLOQUEADO», salida 2. Con un valor `None` por tramo (en vez de `use: null`) sale «BLOQUEADO», salida 2. Con un **spread** sin decidir el informe sí funciona («SIN DECIDIR»).

### 5.8 La sesión no aparece en el preflight

El informe no imprime `session:` ni la comprueba. La ficha dice que una sesión vacía «bloquea la autoría», y lo hace el constructor, no este paso. Que la sesión sea **la del activo** no lo comprueba nadie: `XCUUSD` (cobre) lleva `session: XAGUSD_ftmo`, la de la plata. No sé si es deliberado; el cobre sólo se usa como mercado adicional.

### 5.9 El aviso de calidad del feed, leído despacio

- La frase «mediana desde 2013» está escrita a mano en `core/assets.py:122-123`; el año viene del ledger. Si lo cambias, la frase miente.
- Si un feed no tuviera año estable (`stable_from` vacío), la línea 129 compararía un número con nada. No lo he ejecutado.
- El «listón de 30» son dos números distintos con el mismo valor: el suelo del umbral de año estable y `gap.max_residual_per_year`, que decide si el veredicto del feed es `pass` o `watch` y la frase «sesión MAL declarada» (`feed.py:63-66`). El preflight no imprime los huecos propios por año.
- La sesión deducida para el NIKKEI225 (`Mon 03:00-23:01 … Fri 03:00-03:02, Fri 03:03-23:01`) parte el viernes en dos trozos con un minuto en medio. Con 245 huecos al año contra 2 del USDJPY, lo más probable es que el NIKKEI tenga pausas que la sesión no recoge, no un feed roto. No lo he validado.
- El escaneo de USDJPY es del 2026-09-26, anterior al renombrado de los feeds; su carpeta ya lleva el nombre nuevo.

### 5.10 Restos en las fichas

- `broker: Infinox` en NIKKEI225 y `broker: the5ers` en USDJPY: el instrumento es hoy el contrato de FTMO y Hantec.
- La nota de USDJPY que imprime el preflight es del 2026-09-23: «defaults de fábrica de SQX, comisión CERO incluida: el coste modelado infravalora el real ~10x». Ya no es verdad y sigue saliendo en cada lectura.
- `sqx_now` («SQX lleva hoy») es lo que el maestro llevaba cuando se escribió la ficha, no una lectura actual.
- El comentario «Convenciones de swap» de `_policy.yaml:159-163` quedó en medio de la lista de tramos (seis activos nuevos se añadieron debajo). El fichero se lee bien.

### 5.11 Lo que no está medido

- El spread de cualquier firma de fondeo antes de 2023 (Hantec), 2024 (FTMO) o 2025 (FundingPips).
- El spread de cualquier fuente antes de octubre de 2017: `build` de forex (2008-2017) es modelo en el 97,6 % de sus días.
- El swap histórico.
- De dónde sale el `multiples` propio de cada par (USDJPY 2,7; EURUSD 6,0). `RULES.md` dice «el peor mes de la firma más ancha». Con los ticks muestreados me sale 1,7 para FTMO en USDJPY (peor mes de 32 entre la media de 12) y 6,7 para FundingPips: **no he podido reproducir el 2,7**.
- Para el NIKKEI225, el peor mes de FundingPips (marzo de 2025, 15 unidades a 36.740) es 2,35 veces su media de 12 meses: por encima del techo de 2×. Es un mes con un solo día de ticks.
- La muestra de ticks de las firmas son **tres días por mes** (martes, miércoles y jueves de la segunda semana; unas 820-850 horas cotizadas por firma y activo). La media de 12 meses sale de unos 36 días: ningún lunes (apertura tras el fin de semana), ningún viernes (cierre, y el dato de empleo del primer viernes) ni ninguna primera semana de mes. El error de muestreo es pequeño (IC 95 % por bootstrap de meses: 0,0162-0,0185 % en NIKKEI225 y 0,0047-0,0056 % en USDJPY, es decir ±7-9 %; calculado por el revisor); el problema es llevar ese % 15 años atrás, que donde se pudo medir falla por 2,4 veces (5.3).
- El intervalo del 1,33 (de 1,08 a 1,72) es de 600 operaciones de tres firmas mezcladas; por firma, la ida y vuelta fue 1,17 (FTMO), 1,64 (FundingPips) y 1,13 (Hantec).

### 5.12 El spread tiene un perfil por hora y la ficha lo resume en una media

En forex la forma del coste en el día lo es casi todo, y el dossier (2.3, 2.4, 3.5) lo resume en una media. Cifras del revisor (calculadas sobre los 36 días de ticks de USDJPY en FTMO, dividiendo el spread cotizado por horas del servidor):

- La hora 0 del servidor es el 3,3 % del tiempo cotizado y el **29 % de la media**; su spread es 9,0 veces la media, y fuera de esa hora el spread es 0,73 veces la media.
- El primer tick de la vela de las 00:00 (n = 36) es 10,2 veces la media; el primer tick de las demás velas H1, 1,0.
- Darwinex, sobre 2017-2026 (`hours.parquet`), da lo mismo: multiplicador de la hora 0 de 5,1 en USDJPY y 1,85 en NIKKEI225; en NIKKEI225 de FTMO, la hora 1 está a 2,05 veces.
- `knowhow/costs/funded-tick-spread-vs-price.md` ya lo dice («the 97.5th percentile of the spread IS the rollover hour»).

Lo que hay, por tanto: la media de USDJPY no describe ninguna hora real. Una estrategia que nunca entra a las 00h paga en el backtest un 37 % de más (calculado por el revisor: 1 / 0,73); una que entra en la vela de las 00:00 (toda estrategia D1, y las H1 que disparen en esa vela) paga en la cuenta unas 9-10 veces lo que la ficha le cobra (0,77 puntos cobrados en `oos2` contra 7,2 medidos en esa hora). El techo del MC Retest de spread (2,7× en USDJPY) no llega a ese caso. El preflight no distingue a qué hora entra la estrategia, y la frase de 2.3 «para un coste manda la media» sólo es cierta si las entradas se reparten por igual a lo largo del día.

### 5.13 Efecto conjunto de los tres cambios del 2026-10-04

La tabla 4.2 da el antes y el después de cada número por separado, pero no su efecto conjunto. Para NIKKEI225, fricción total de una ida y vuelta (spread + dos deslizamientos), calculada por el revisor como spread × (1 + 2 × parte de deslizamiento): antes 607 × 2,0 = 1.213 / 916 × 2,0 = 1.831 / 559 × 2,0 = 1.118; hoy 304 × 1,7 = 517 / 475 × 1,7 = 807 / 796 × 1,7 = 1.353 (`build` / `oos1` / `oos2`). La fricción total de una operación bajó un 57 % en `build` y un 56 % en `oos1`, y subió un 21 % en `oos2`.

---

## 6. Cierre

### 6.1 Las comprobaciones, en una tabla

| | comprobación | efecto | hoy |
|---|---|---|---|
| B1 | esquema de la clase | salida 3 | 27 de 27 pasan |
| B2 | tramo anterior al primer dato (por año) | salida 3 | pasan |
| B3 | spread o comisión sin valor | salida 2 (comisión: traza) | pasan |
| A1 | tramo más allá del último dato | aviso en `stderr` | ninguno |
| A2 | tramo sin fechas | aviso | ninguno |
| A3 | rango MC Retest sin decidir | aviso | XAUUSD (`min_distance`) |
| A4 | calidad del feed | aviso | NIKKEI225 y los demás con construcción anterior a su año estable |
| — | coste provisional | marca en índice y registro | ninguno |
| — | sesión | no se mira aquí | — |

### 6.2 Las decisiones que te quedan

**1. Qué spread lleva la historia de un índice.** Hoy: el % de la firma más ancha por el precio del tramo.
- *Mantenerlo:* una sola regla para los 27 activos, coherente con «la fricción de 2026». Cuesta que `build` y `oos1` del NIKKEI225 corran con un spread por debajo de lo que Darwinex midió esos años (304 contra 747; 475 contra 732), y que un filo que sólo existe con costes bajos pase los pasos 6 a 16 y se caiga en `oos2`, donde la ficha cobra 796.
- *Fijo en puntos (1.000 hoy):* es lo que la firma cotiza. Cuesta descartar casi todo lo intradía en 2012, cuando 1.000 puntos eran el 0,11 % del precio.
- *Darwinex donde hay medida:* cifras medidas de 2017 a 2026. Cuesta volver a dos métodos según el año, y Darwinex no es tu firma.
- Antes de decidir conviene medir sobre una cosecha real cuántas estrategias cambian de signo entre las tres cifras.

**2. El lado abonado del swap.** Hoy se abona en 16 activos durante toda la historia.
- *Ponerlo a 0, como en el crudo:* ninguna estrategia gana por el carry de hoy aplicado a 2010. Cuesta que una estrategia larga en yen pierda un ingreso que hoy sí tendría.
- *Dejarlo:* el backtest reproduce la cuenta de hoy. Cuesta un sesgo a favor de los largos de USDJPY de +0,59 % anual por lote en toda la construcción.

**3. El comando que calcula el spread.** Hoy no existe para el método en vigor.
- *Escribirlo y retirar o adaptar la onboard:* la próxima recalibración y la próxima alta salen iguales que las 27. Cuesta una tarea de código y su capítulo.
- *Dejarlo:* cada recalibración depende de que alguien recuerde cómo se hizo, y `/asset-onboard --write` puede pisar una ficha con el método antiguo.

**4. El ancho mínimo del rango de MC Retest en forex.**
- *Dejarlo:* la tarea tiene dispersión. Cuesta que MCR 3 en forex sortee hasta 6 veces el deslizamiento base (hasta 9,6 en EURUSD; 10 pares ensanchados, 5.5), y que las fragilidades de un par y de un índice no sean comparables.
- *Declarar el rango de forex en la ficha:* cada par con su cifra. Cuesta 14 decisiones (14 pares forex; 10 ya llevan `multiples` propios y 4 —CADJPY, EURJPY, GBPJPY y NZDUSD— usan el defecto 0,5-2).

**5. Si la calidad del feed debe poder parar.** Hoy sólo avisa, y para el NIKKEI225 avisa de **toda** la construcción.
- *Que bloquee con construcción anterior al año estable:* dejaría fuera hoy al NIKKEI225 (estable desde 2020) y a varios índices. Antes habría que saber si los 245 huecos son pausas reales del mercado mal declaradas en la sesión; si lo son, el arreglo es la sesión, no la ventana.
- *Dejarlo en aviso:* nada se para. Cuesta que el aviso se imprima en cada corrida y nadie actúe.

**6. El techo de 2× del MC Retest.** Lo medido da 1,99× en Darwinex para el NIKKEI225 (día a día) y 2,35× en el peor mes muestreado de FundingPips.
- *Dejarlo en 2×:* una cifra para todos los índices. Cubre el caso medido de Darwinex por poco.
- *Volver a un múltiplo medido por activo:* el estudio ya lo calcula (`verdict.mc_multiples`) y nadie lo lee. Cuesta decidir de qué fuente.

**7. Limpieza que no cambia ningún número:** la nota vieja de USDJPY, `broker:`, la tabla de clases de `RULES.md`, las notas de `_classes.yaml`, la skill, el capítulo 59, la fila del paso 4 de `WORKFLOW.md`, la traza de la comisión sin decidir y la comparación por año de B2. No gana rendimiento; evita que la próxima sesión aplique la regla equivocada.

### 6.3 El límite que no cambia

El preflight comprueba que las cifras **existen** y que las ventanas **caben**. No comprueba que las cifras sean **ciertas**: un spread de 304 y uno de 747 pasan igual. Todo lo que los pasos 6 a 25 digan de una estrategia del NIKKEI225 está dicho a los costes de esta ficha, y el único paso que los contrasta con una cuenta real es el 26.
