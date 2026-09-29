# 36 · Licencia del reprecio: un retest DATATICK contra `studies.data.spread.report` — encargo autocontenido

**Tu oficio:** Python sobre `studies/data/spread/` y un lote pequeño en SQX (custodio).
**Tu encargo:** decidir si el reprecio de `studies.data.spread.report` — que hoy sustituye a un
retest DATATICK real sin haber sido contrastado con uno (OPEN.md #76) — predice de verdad lo que
SQX cobra cuando retestea sobre los ticks de Darwinex. Es un encargo de **licencia del método**, no
de una estrategia: se corre **una vez**, al final de la secuencia individual, sobre un puñado de
supervivientes ya existentes.

Lee `CLAUDE.md` · `CODESTYLE.md` · `studies/data/spread/README.md` y su
`POSSIBLE_IMPROVEMENTS.md` · `OPEN.md` #76 · `docs/AgentPDFs/WORKFLOW.md` (pasos 8, 20, 25, 25.5,
26) · `sqx/CLAUDE.md` (reglas 4, 6, 10 del `CLAUDE.md` raíz: proyecto propio, nunca el `Retester`
de serie) · `knowhow/export/` (formato de la exportación de operaciones) · `mt5/compare.py`
(`pair`, como referencia de emparejamiento operación a operación — no se usa MT5 aquí, sólo su
forma de comparar).

---

## 0 · De dónde sale

El dueño, 2026-09-27, al aplicar el spread real de Darwinex (OPEN.md #76): el reprecio
(`studies.data.spread.report`, paso 8 y paso 25 del `WORKFLOW.md`) cambia el spread plano de SQX
por el real, operación por operación, como sustituto barato de un retest a precisión DATATICK sobre
la feed de ticks (`*_DarwTick_*`). Es barato porque nunca ha corrido ese retest de verdad: el
`README.md` del módulo lo dice a las claras — *"no se ha contrastado con un retest DATATICK real...
que lo licenciaría como su sustituto"*. Este encargo es ese contraste, una sola vez, para poder
seguir usando el atajo con conocimiento de causa en vez de por fe.

## 1 · Qué se compara, y por qué no basta con mirar el spread medio

El reprecio de Python parte de las **velas** de Dukascopy con las que SQX ya construyó y retesteó
(`build`/`oos1`/`oos2` según el caso), y para cada operación busca en los ticks de Darwinex el
spread que estaba de pie en su entrada (larga) o su salida (corta) — o, donde no hay tick cerca
(antes de octubre 2017), el spread reconstruido del modelo (`studies/data/spread/model.py`) por
su multiplicador horario. **La pregunta de este encargo es si ese número, calculado en Python sobre
velas, coincide con el que SQX mismo cobraría si retesteara sobre los ticks de verdad** — la feed
`*_DarwTick_*`, a precisión DATATICK, donde el simulador rellena cada orden con el ask/bid real del
tick en vez de un spread declarado.

Dos maneras de fallar, y hay que distinguirlas:

- **El reprecio de Python está bien pero SQX simula distinto** (redondeo, el tick exacto que usa
  para rellenar, cómo trata un hueco de liquidez) — entonces el atajo necesita un factor de
  corrección, no se tira.
- **El reprecio de Python se equivoca de tick o de fórmula** — entonces se corrige el propio
  `reprice.py` antes de seguir confiando en él.

No se compara el spread medio del activo (eso ya está hecho en `scan.py`/`verdict.py`): se compara
el **P/L de cada operación**, que es lo que de verdad decide si una estrategia sigue ganando o no
tras el ajuste — la misma pregunta que responde el `report.py` cuando marca `action: mark`.

## 2 · El lote

**Pocas estrategias, adrede** (dueño: "un trabajo corto en un worker, sobre unas pocas estrategias
de una cosecha ya existente" — la frase que motiva este encargo en OPEN.md §76). Se reutiliza una
cosecha ya exportada (por ejemplo la de XAUUSD o USDJPY que `studies/screening/gate/` ya procesó):
de ahí se eligen 5-10 supervivientes que el reprecio ya marcó (algunas de las que "dejan de ganar"
y algunas que siguen ganando, para que la comparación cubra los dos casos) — la lista exacta es una
decisión de quien ejecute el encargo, documentada al cerrarlo.

## 3 · Pasos

1. **Elegir el lote** (§2) de una cosecha existente; anotar identidad y versión de cada
   estrategia (regla del `WORKFLOW.md`: el hash del `strategy_Portfolio.xml` normalizado, no el
   nombre).
2. **Proyecto propio en el custodio** (regla 10 del `CLAUDE.md` raíz): un `Test_` clonado del
   donante congelado de ese activo (`sqx/projects/builder.py`), nunca el `Builder`/`Retester` de
   serie. Cargar sólo esas estrategias — mismas que la exportación original, para no tocar nada de
   la búsqueda.
3. **Una tarea de retest sobre la feed `*_DarwTick_*`**, precisión DATATICK, misma ventana
   (`build`/`oos1`/`oos2` según qué tramo se está licenciando — probablemente `oos1` u `oos2`,
   que es donde vive la mayoría del histórico de ticks), **spread declarado en cero** (o el mínimo
   que SQX permita): el objetivo es que el simulador rellene cada orden con el ask/bid real del
   tick, no que sume un spread plano encima del real. Comisión y swap se dejan como ya declaraba el
   proyecto original, para no mezclar ese coste con el que se está validando.
4. **Exportar las operaciones** de esa tarea (`sqx/export/export_trades.py`).
5. **Correr `studies.data.spread.report`** sobre la exportación **original** (las mismas
   estrategias, mismas velas de Dukascopy, mismo tramo) para tener el P/L repreciado de Python
   lado a lado.
6. **Emparejar operación por operación** (mismo criterio que `mt5.compare.pair`: mismo lado, misma
   entrada dentro de una tolerancia — aquí debería ser exacta o casi, porque ambas parten del mismo
   backtest en velas) y comparar el P/L: diferencia media, dispersión, y si el veredicto por
   estrategia (`action: mark`) coincide entre los dos caminos.
7. **Retirar el `Test_` project** al terminar (regla 6): `python3 -m sqx.projects.retire <P>
   --role custodian --yes`, worker parado.
8. **Escribir la card de `knowhow/`** con lo que se descubrió (regla del proyecto: un hallazgo que
   se queda en la transcripción muere con la sesión) y, si toca, corregir `reprice.py` o
   `model.py` en el mismo encargo.

## 4 · Umbral de aceptación

**Pregunta abierta al dueño (regla 11 — no se supone)**: ¿qué diferencia por operación licencia el
atajo? Dos lecturas razonables, para elegir o proponer otra:

- **Absoluta**, en unidades de cuenta o en R, como en el encargo 34 (fila 2: ≤ 0,05 R por
  operación) — coherente con el resto del proyecto, que ya usa esa unidad para comparar dos
  fuentes de P/L.
- **Relativa al propio ajuste**: si el reprecio dice que una estrategia deja de ganar, el retest
  real tiene que decir lo mismo (coincidencia binaria de veredicto) — más laxo, pero es la pregunta
  que de verdad importa para el paso 8/25 (`action: mark`).

Como todo umbral del proyecto, va a `ledger/thresholds.yaml` con su `ledger:<clave>`
(`knowhow/eng/thresholds-live-in-the-ledger.md`), no como constante en el módulo.

## 5 · Salidas

1. Una tabla o pequeño informe (formato libre, en el `README.md` del módulo o en
   `AlgoData/spread/<feed>/`, nunca en el repo si son datos) con el P/L de cada operación por los
   dos caminos, la diferencia, y el veredicto de licencia.
2. La card de `knowhow/databanks/` o `knowhow/export/` (la que exista más cerca) con el resultado:
   licenciado, licenciado con un factor de corrección, o no licenciado y por qué.
3. Si `reprice.py` o `model.py` cambian, el commit lo dice — pero **no se hace commit**: se deja
   sin confirmar para el dueño, como manda la regla 12.
4. Una línea de estado para `OPEN.md` §76, que **no se edita en este encargo** — se entrega al que
   despache el encargo para que la pegue.

## 6 · Coste en tiempo y CPU

**Bajo, a propósito** (es la razón de que el dueño pida "pocas estrategias" y "un trabajo corto"):
una tarea de retest sobre 5-10 estrategias, un solo tramo, en el custodio — minutos, no una rejilla.
El lado Python (`report.py` sobre la misma cosecha) ya corre en 2-3 s por el `README.md` del
módulo. El coste real es el tiempo de un worker ocupado un rato, no CPU: se hace con el custodio
libre, un job y `bin/sqx-worker.sh stop` al terminar (regla 2 del `CLAUDE.md` raíz).

## 7 · Qué decide

Si el atajo de `studies.data.spread.report` sigue sirviendo, sin cambios, como sustituto de un
retest DATATICK en los pasos 8 y 25 de la secuencia — o si necesita un factor de corrección, o una
revisión de `reprice.py`/`model.py` antes de seguir usándose. Es una decisión sobre el **método**,
no sobre las estrategias del lote: estas se eligen sólo para poder medir el método, y su resultado
individual no vuelve a la cosecha de la que salieron.

**No construye el modelo de USDJPY que se apoya en el nivel de precio**
(`studies/data/spread/POSSIBLE_IMPROVEMENTS.md`): es una limitación distinta y ya conocida del
`relativo`/`volatilidad_precio`, que este encargo puede confirmar de paso (si el lote incluye
USDJPY y cae en años con el nivel extremo) pero no está aquí para arreglar.
