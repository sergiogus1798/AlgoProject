# EL WORKFLOW — los 25 pasos, de la idea a la estrategia superviviente

**Esto lo dictó el dueño el 2026-09-23 y es la espina dorsal del proyecto.** Documento vivo, sin
fecha en el nombre: se actualiza, no se sustituye. Cualquier sesión que vaya a construir algo mira
aquí primero en qué paso está y qué contrato tiene que cumplir.

Qué NO es: `plan-ejecucion-2026-09-21.md` reparte el trabajo entre agentes y
`protocolo-robustez-2026-09-21.md` detalla los contratos internos del tramo de robustez. Esto es la
**secuencia**, y manda sobre el orden que digan los otros dos.

Estados: ✅ construido y medido · 🟡 existe, sin cerrar · ⬜ sin empezar · 🔴 bloqueado por un dato
que sólo el dueño puede dar.

---

## La secuencia

| # | paso | dónde | estado |
|---|---|---|---|
| 1 | **Idea en el chat** | — | — |
| 2 | **Vocabulario** — ¿existe el bloque? si no, se crea e instala | `sqx/inspect/vocabulary.py`, `sqx/blocks/install.py` | ✅ |
| 3 | **Plantilla** — bloque fijo + hueco aleatorio, con registro de lo ya probado | `sqx/templates/`, `/sqx-strategy-template` | ✅ |
| 4 | **Preflight** — costes, ventanas y rangos, BLOQUEANTE | `core/assets.py` | ✅ · ⬜ aviso de calidad del feed (encargo 17), EN PAUSA — consulta externa pendiente, `docs/AgentPDFs/consulta-calidad-del-feed-2026-09-26.md` |
| 5 | **Creación del custom project** | `sqx/projects/builder.py` | ✅ |
| 6 | **Configuración del build** | `assets/_build.yaml`, `sqx/projects/doctrine.py` | 🔴 filtros · ⬜ building blocks |
| 7 | **Retest OOS en SQX** | tarea propia, costes de `oos1` | ✅ |
| 8 | **Análisis IS/OOS en Python** — incluye la criba de edge por coste (encargo 11): el bruto por operación reconstruido de `Profit/Loss + comisión + coste de spread modelado`, en spreads de hoy (media y mediana) y como `c*` de breakeven, sobre la cosecha de la puerta | `studies/screening/gate/`, `/oos-gate` → `/curate`; edge por coste en `studies/readings/edgeCost/report.py --project P --databank D --feed F`, manual `50-edge-por-coste.md` | 🟡 umbrales laxos de la puerta · ✅ edge por coste — corre encadenado tras `gate.report` sobre su misma cosecha, sin import entre estudios · ⚠️ costes de `assets/` PROVISIONAL heredados, XAUUSD `costs_provisional` (OPEN.md #26) · ⬜ atribución de calidad del feed (encargo 17), EN PAUSA — misma consulta que el paso 4 |
| 9 | **Retest crossmarkets en SQX** | `sqx/projects/crossmarket.py` | 🔴 faltan costes |
| 10 | **Análisis crossmarkets en Python** | `studies/transfer/crossmarket/` | 🟡 sin skill |
| 10.5 | **Preparación crossTF** — generación de variantes escaladas | `sqx/variants/scale.py`, `/crosstf` | 🟡 |
| 11 | **Retest crossTimeframes en SQX** | `/crosstf` | 🟡 |
| 12 | **Análisis crossTFs en Python** | `studies/transfer/crossTF/` | 🟡 |
| 13 | **MC Retest en SQX** | `sqx/projects/mcretest.py`, `/mcretest`; catálogo en `assets/_build.yaml` | ✅ |
| 14 | **Análisis MC Retest en Python** | `studies/breakage/mcRetest/` | 🟡 |
| 15 | **SPPs en SQX** | `sqx/projects/spp.py`, `/spp`; catálogo en `assets/_build.yaml` | ✅ |
| 16 | **Análisis SPPs en Python** | `studies/breakage/spp/` | ✅ |
| 16.5 | **Preparación de variantes para el WFC** | `sqx/variants/make.py`, `/variants` | ✅ · ⚠️ corre en el `Retester` de serie, OPEN.md §38 |
| 17 | **Walk Forward Correlation** | `studies/optimisation/wfc/report.py` | ✅ |
| 18 | **CSCV** | `studies/optimisation/cscv/report.py` | ✅ |
| 18.5 | **Superficies por mercado** — la misma región de parámetros, ¿es la buena en los 9 mercados de `_markets.yaml`? `rho` de Spearman y Jaccard del decil superior entre cada par, sobre el lote del 16.5 retesteado con los cross-checks | `studies/optimisation/marketSurfaces/report.py`, manual `52-superficies-mercado.md` | ✅ · ⚠️ costes de los 9 pares = defaults de SQX con comisión CERO (`costs_provisional`) · lee `build` y `oos1`, **no** `oos2` |
| 19 | **Walk Forward Matrix en SQX** | `sqx/projects/wfm.py`, `/wfm`; el análisis es `studies/optimisation/wfm/` | ✅ la tarea · 🔴 no se lee hasta tener 17 y 18 |
| 20 | **Análisis conjunto de 17, 18, 18.5 y 19 — CIEGO hasta tener los cuatro** | — | ⬜ |
| 21 | **Exposición contra el buy and hold** — qué tiempo de mercado costó lo que ganó | `studies/closing/exposure/`, `docs/manual/38-exposicion.md` | ✅ |
| 22 | **Mapa condicional** — clasifica cada operación por el estado del mercado al entrar (volatilidad realizada, tendencia, día de la semana) y lee el P&L celda a celda; fabrica hipótesis, no filtra | `studies/readings/conditionalMap/`, manual `53-mapa-condicional.md` | 🟡 · ⬜ sesión (Asia/Londres/Nueva York/solape) pendiente de que el dueño fije las horas UTC — ver `_coord/BOARD.md` |
| 23 | **Estructura** — por superviviente: una ablación por condición de entrada y la inversión de la orden en las mismas entradas. ¿Qué condición aporta por operación contra un recorte al azar, cuál es redundante, y vive el filo en la dirección? Diagnóstico, nunca selección | `sqx.structural.make` → `sqx.variants.execute` (custodio) → `sqx.structural.keep` → `sqx.export.export_retest` → `studies/readings/structure/report.py`, manual `51-estructura.md` | ✅ · lee `build` y `oos1`; `oos2` lo rechaza `ledger.gate` · sin stops: la inversión se niega si la madre ya lleva stop/target (por eso va antes del 24) · D3 (mono dentro de SQX) cerrado como imposible |
| 24 | **El stop loss para MT5** — a cuántos ATR, leído del MAE de las operaciones, **sin optimizar** | `studies/closing/atrCalculator/`, encargo `docs/encargos/20-atr-calculator.md` | ⬜ |
| 25 | **Edge por coste, por estrategia** — la misma lectura sobre el export de trades de la versión que se va a operar, para confirmar que el edge sigue por encima del umbral con el stop puesto | `studies/readings/edgeCost/report.py ... --strategy "<nombre>"`, mismo manual `50-edge-por-coste.md` | ✅ · misma forma de columnas que el export de la puerta, ningún cambio de código entre los dos usos |

**Tres lecturas adicionales que no son pasos nuevos y no renumeran nada.** Dos sobre una
estrategia y su lista de operaciones, gratis y sin SQX: `studies/readings/profitShape/` (manual
`40-forma-del-beneficio.md`) dice de qué pocas operaciones y qué pocos meses depende el resultado,
si las operaciones se agrupan —y entonces el Monte Carlo de cartera tiene que remuestrear por
bloques— y si la media cambió dentro de la muestra; `studies/readings/entryQuality/` (manual
`42-calidad-de-la-entrada.md`) aísla la **entrada** del resto midiendo el recorrido a favor y en
contra contra entradas al azar a las mismas horas, y lo que cuesta llegar tarde. Las dos salen del
PDF `TRADE_LEVEL_TESTS.pdf` del dueño. Y la tercera, sobre el lote de variantes:
`studies/optimisation/cloud/` (manual `39-nube-de-parametros.md`) lee las variantes del 16.5 como lo
que son —una superficie— y dice si la madre está en un pico o en una meseta, qué parámetros mandan,
si hay superficie que leer y si su forma aguanta año a año. Es gratis, no toca SQX, **corta las
curvas donde empieza `oos2`** y no elige nada: sale del PDF `PARAMETER_SPACE_TESTS.pdf` del dueño,
cuya sección E prohíbe expresamente sustituir la madre por el mejor clon.

Del 26 en adelante empieza la cartera. **Primero las estrategias individuales.**

## El paso 21 — la dicotomía rendimiento/exposición

Encargo del dueño, 2026-09-24, y cierra la secuencia individual:

> *«Una estrategia que saque 5 %, pero solo se exponga al mercado 1 hora a la semana, me parecería
> mejor que sacar un 10 % con el buy and hold.»*

Los pasos 1 a 20 preguntan si la ventaja es **real**. El 21 pregunta qué **forma** tiene: el mismo
retorno conseguido con el 4 % de ocupación no es el mismo objeto que conseguido estando dentro
siempre, porque las horas fuera no tienen gap, ni noticia, ni drawdown, ni capital inmovilizado.

Mide tres cosas y no las confunde: lo que ganó **en total** contra un buy and hold **al mismo
riesgo**, lo que gana **por hora expuesta**, y cuánto del movimiento del mercado ocurrió mientras
tenía posición — que es lo que separa una ventaja propia de estar presente en los tramos buenos.

**La alfa y la beta están aparcadas ahí, a propósito.** Decisión del dueño del mismo día: primero
se cierra la secuencia individual. Si algún día se construye la regresión, va en
`studies/closing/exposure/`, que ya tiene montada su antesala.

## El paso 24 — el stop loss que MT5 exige

Encargo del dueño, 2026-09-25/26. La cadena construye **sin stop a propósito**: un stop es un
parámetro más y cada parámetro es sitio para el sobreajuste. Pero MT5 lo exige, así que al final
de la secuencia individual se le pone uno a la estrategia que ya sobrevivió todo.

> *«No quiero que sea una optimización ni nada.»*

El stop es un **colchón**: corta las pérdidas largas que ya no se recuperan y deja a la estrategia
el aire que necesita contra el ruido. Su distancia, `SL = X·ATR`, se **lee** del MAE de las
operaciones —cuánto se fueron en contra las ganadoras, a partir de dónde ya no se recupera casi
ninguna— con una regla fijada antes de mirar. No se barre una rejilla ni se elige la X que más
gana. X sale **sólo del IS**, como percentil de las ganadoras (80, 85, 90 y 95, cuatro sub-estudios), con
ATR(20). `oos1` y `oos2` dicen si se transfiere. El coste y la estabilidad los mide SQX con sus propios
spread y slippage: variantes un poco por encima y por debajo de cada X, buscando meseta, no máximo.
Después, si hace falta, se repite alguno de los tests anteriores sobre la versión con stop, y nada
más. Detalle en `docs/encargos/20-atr-calculator.md`.

## El Monte Carlo de bootstrap está FUERA, a propósito

Decisión del dueño, 2026-09-23, y el razonamiento merece quedar escrito porque es correcto:

> Todos esos tests que hay antes están dedicados a intentar descartar que la estrategia haya tenido
> suerte en el backtest. Mientras que el Monte Carlo sólo resuelve los trades de un backtest
> estático, no dice nada del edge.

Remuestrear los trades realizados mide la dispersión de **una muestra ya seleccionada**. Si la
estrategia llegó ahí por haber sobrevivido a una búsqueda, el bootstrap hereda esa selección entera
y no puede verla: reordenar trades afortunados da secuencias afortunadas.

**El módulo `portfolio/common/monteCarlo/` se mantiene**: en la cartera responde otra pregunta —
dimensionamiento y riesgo de ruina dada una distribución de trades— y ahí sí es la herramienta.

## Qué segmento toca cada paso

Sale de `assets/_policy.yaml` y no se negocia por paso:

- `build` — sólo el paso 6. Es la única muestra que el generador ve. El paso 22 (mapa condicional)
  también lo lee, pero sólo para congelar sus cortes de tercil — clasifica la muestra de
  `run.sample` (por defecto `oos1`), nunca la construye contra ella.
- `oos1` — del 7 al 16, el paso 18.5 (superficies por mercado, junto con `build`), el paso 22
  (mapa condicional) y el paso 23 (tests estructurales, junto con `build`).
- `oos2` — **RESERVADO** para 17 y 19 (WFC y WFM). Es una puerta de un solo sentido: cada mirada
  lo gasta. El paso 18.5 lee `build` y `oos1` deliberadamente y **no** pide `oos2` (front D,
  recomendación 2026-09-26); el paso 23 tampoco: `ledger.gate` se lo rechaza. Ningún otro paso
  anterior a 20 lo toca.

## El contrato que une los pasos pares

Todo paso de Python que juzgue estrategias emite **un CSV con `strategy` y `verdict`**, y `/curate`
lo aplica sobre el databank para que el siguiente paso de SQX sólo vea a los supervivientes. Da
igual qué haya juzgado: el mecanismo no cambia. `identity` es opcional pero recomendada — el nombre
no identifica, SQX renombra en colisión.

⚠️ La identidad es el SHA-256 del `strategy_Portfolio.xml` **normalizado**. Un retest reescribe
`makeExternal` en cada variable: con el hash crudo, el emparejamiento build↔retest casa 0 de 115.

## Decisiones del dueño sobre la secuencia — 2026-09-23

### El paso 20 va ciego, y por eso el orden importa

Los pasos 17, 18 y 19 **no se miran hasta que los tres estén hechos**. La razón no es estética:

> Una vez miramos una ventana de OOS la quemamos, y esas pruebas se hacen con los datos que ya
> habíamos visto **y además la última bala del `oos2`**.

Del 7 al 16 se mira `oos1` una y otra vez, así que para cuando se llega al 17 ese tramo está
gastado. `oos2` es lo único virgen que queda, y sólo se dispara una vez. Si se leen los resultados
de 17 y 18 antes de correr el 19, la decisión de si correrlo —y con qué parámetros— ya está
contaminada por lo que se vio, y la última bala se gasta en un test elegido a posteriori.

**Esto ha de estar forzado por el ledger, no por la buena voluntad de quien lo corra.**

✅ **Construido el 2026-09-24.** `ledger/gate.py` se niega: `allow(paso, segmento, activo)` lanza si
un paso mira un tramo que `_policy.yaml` reserva para otro, y `allow_read` lanza si se piden los
resultados de 17, 18 o 19 sin que los tres estén registrados. Manual: `docs/manual/43-ledger.md`.

#### Qué significa «los tres a la vez» — aclarado 2026-09-24

No significa correrlos en paralelo. **Corren secuencialmente, y así se quiere**: el 17, el 18 y el 19
uno detrás de otro. Lo que tiene que ser simultáneo es **la lectura**:

> Cuando digo que quiero ver el WFC + WFM + CSCV a la vez, me refiero al mismo tiempo y una vez ya
> sepamos que el programa funciona bien. La cosa es que, cuando en un futuro hagamos una UI, los
> resultados de las 3 pruebas se mostrarán a la vez, o al menos no ver uno mientras se está
> simulando la siguiente prueba.

Consecuencia para quien programe la ventana de `ui/`: los tres resultados se **retienen** hasta que
los tres existen, y no se pinta ninguno mientras el siguiente está corriendo. Es la misma regla
ciega del paso 20, pero dicha en términos de interfaz — y es la interfaz la que la tiene que forzar,
no la disciplina de quien mira.

## Un manifiesto global de la cadena — acordado

Un solo registro por estudio que diga, paso a paso, cuántas estrategias entran y cuántas salen. Sin
él, al llegar al 17 nadie sabe si quedan tres supervivientes de diez mil o de cincuenta — y esa
diferencia **es** el resultado, no un detalle de contabilidad.

### 🔭 Antes de correr el workflow entero por primera vez: pasar una población NULA

**Recordatorio para el dueño, pedido por él el 2026-09-23.**

La cadena son seis filtros en serie sobre la misma población, y cada uno ajusta su umbral mirando
lo que mató el anterior. Eso es selección múltiple: el superviviente del paso 20 ha pasado por una
búsqueda tan intensa como la del builder, sólo que esa búsqueda **la hacemos nosotros**.

Habrá métricas y requisitos de rendimiento cuantificables, y eso es necesario. No es suficiente:
un umbral cuantificado sigue sin decir cuántas estrategias sin ningún edge lo cruzarían por azar.

Lo que sí lo dice: **meter por la cadena entera una población de estrategias de entrada aleatoria**
y contar cuántas llegan al paso 20. Si de diez mil monos llegan 4 y de diez mil tuyas llegan 5, ya
sabes lo que vale ese 5. La máquina del mono ya existe (`studies/screening/gate/monkey.py`) y hoy sólo se usa en el
paso 8; llevarla de punta a punta es el control que hace interpretable todo lo demás.

Hacerlo **antes** del primer pase completo, no después: después ya se sabe qué sobrevivió, y el
número de monos se convierte en una cifra que se compara con un resultado conocido.

## Lo que bloquea hoy

| | qué falta, y de quién depende |
|---|---|
| 🔴 | **`assets/_study.yaml`** — los umbrales de aceptación del paso 6 y sobre qué muestra (`sampleType`) se miden. Del dueño |
| 🔴 | **costes de `XAGUSD_DukasM1_Infinox` y `BRENTCMDUSD_ftmo`**, y el `data_from` del Brent. Sin ellos el paso 9 se niega a escribirse. Del dueño |
| ⬜ | **los building blocks** del paso 6: qué indicadores entran en el hueco aleatorio |
| ⬜ | el paso 20, que no existe |
| ⬜ | **las horas UTC de cada sesión** (Asia/Londres/Nueva York/solape) — sin ellas el paso 22 no puede añadir el corte de sesión; el campo `session` de `assets/symbols/` sólo da la semana de mercado abierto, no la partición del día. Del dueño |
| 🔴 | **calidad del feed** (encargo 17) — EN PAUSA pendiente de una consulta externa (`docs/AgentPDFs/consulta-calidad-del-feed-2026-09-26.md`); afecta el aviso del paso 4 y la criba de atribución del paso 8. Del dueño |
