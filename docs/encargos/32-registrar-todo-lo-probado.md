# 32 · Registrar todo lo probado, no sólo el ganador — encargo autocontenido

**Tu oficio:** Python, sobre todo en `ledger/` y en los comandos que barren algo.
**Tu encargo es que ningún barrido de parámetros, umbrales o configuraciones pueda terminar sin
dejar escrito todo lo que se probó.** Cuántas cosas se probaron es lo que decide cuánto hay que
descontar al ganador. Si sólo queda el ganador, la corrección por pruebas múltiples se hace a ciegas.

Lee `CLAUDE.md` · `CODESTYLE.md` · `ledger/README.md` · `ledger/study.py` · `ledger/record.py` ·
`ledger/trials.py` · `core/study/CONTRACT.md` · `studies/CLAUDE.md` · `knowhow/eng/thresholds-live-in-the-ledger.md`.

---

## 0 · De dónde sale

Del plugin WinRateEdge, guía *Parameter Sweeps and Multiple Testing*, §8, paso 6: «Documenta todo lo que
probaste, no sólo el que funcionó. Te protege de mentirte sobre el riesgo real de falso positivo». La misma
idea está en Aronson (una regla sacada de un libro trae dentro los ensayos ocultos de su autor, pp. 390-391),
en Seykota (cada capa añadida a un sistema es un ensayo más) y en el protocolo de Arnott, Harvey y Markowitz.
El dueño, 2026-09-28: apúntalo como encargo.

## 1 · Lo que ya se registra y lo que no

**Lo que ya queda escrito:**

- La **búsqueda genética de SQX** deja en el ledger cuántas estrategias entran y salen de cada build.
- La **fábrica de variantes** guarda su diseño entero (`design.json`, `plan.csv`) y el SPP guarda todas sus
  permutaciones (`spp.parquet`).
- Cada informe de estudio guarda el hash de su configuración, y la columna `config_hash` existe en el ledger.
- Las plantillas probadas por activo y timeframe quedan en `AlgoData/templates/runs.csv`.

**Lo que se pierde hoy:**

- **Los valores concretos probados.** Las filas del ledger (`ledger/study.py`, `COLUMNS`) llevan `n_in`,
  `n_out`, el criterio y los umbrales, pero no qué niveles de qué parámetro se probaron ni cuál se eligió.
- **Las reejecuciones de un estudio con `--set`.** Correr la puerta tres veces con tres umbrales distintos
  y quedarse con la tercera es un barrido de tres. Hoy sólo se nota si alguien compara hashes a mano.
- **Los barridos de quien trabaja**, sea el dueño, una sesión o un agente: probar percentiles, cambiar un
  umbral, probar otra plantilla parecida o descartar un bloque tras mirarlo. Nada de eso deja rastro.
- **La procedencia de una idea**: si una plantilla sale de un libro, trae los ensayos del autor.

## 2 · Objetivos

1. **Una fila de ledger por cada cosa evaluada** en cualquier barrido: qué parámetro o umbral, qué valor,
   qué salió, y si fue el elegido.
2. **Detectar las reejecuciones**: un estudio corrido otra vez sobre la misma entrada con otra configuración
   cuenta como un ensayo más, y el ledger lo sabe solo.
3. **Que el recuento llegue a la corrección.** `ledger/trials.py` usa estos ensayos para el N y la sigma del
   Sharpe deflactado, y el informe del ledger enseña «probados K, elegido 1».
4. **Que se vea.** Donde la ventana enseñe un resultado elegido de un barrido, al lado pone cuántos se
   probaron.

## 3 · Cómo se construye

### 3.1 · El registro de lo probado

Un contrato nuevo en `ledger/`, **L2 · lo probado**, con su fichero por estudio al lado del ledger actual:

| columna | qué es |
|---|---|
| `study`, `ts`, `step`, `launched_by` | como en el ledger |
| `search_id` | el barrido al que pertenece esta prueba; todas las pruebas de un barrido lo comparten |
| `kind` | `parameter`, `threshold`, `config`, `template`, `block` |
| `name` y `value` | qué se probó y con qué valor |
| `input_hash` | la huella de los datos sobre los que se probó |
| `config_hash` | la huella de la configuración entera |
| `score` y `score_unit` | lo que salió, en la unidad que pide `trials.accumulated` |
| `chosen` | si fue el elegido |
| `provenance` | de dónde salió la idea: propia, un libro con su página, un paper, la web |

Un `search_id` agrupa, así que la fila L1 que ya escribe cada búsqueda sigue siendo una por búsqueda y los
módulos que ya la escriben no se rompen.

### 3.2 · Quién lo escribe

1. **Una función única** en `ledger/record.py` para abrir un barrido, apuntar cada prueba y cerrarlo con el
   elegido. Ningún módulo escribe el fichero a mano.
2. **Los comandos que barren por dentro**, como `atrCalculator` con sus percentiles o cualquier estudio con
   una lista de valores en su `config.yaml`, llaman a esa función.
3. **Las reejecuciones.** El contrato de estudio (`core/study/`) conoce el hash de la entrada y el de la
   configuración de cada corrida. Al escribir un informe, si ya hay otro con la misma entrada y otra
   configuración, se apunta la corrida nueva en el mismo `search_id` que la anterior, sin que nadie lo pida.
4. **Los barridos a mano.** Una orden corta, por ejemplo `python3 -m ledger.tried --study <S> --name <p>
   --values 1,2,3 --chosen 2 --why "<motivo>"`, para lo que se prueba fuera de un comando. La skill
   `/doc` y las instrucciones de las sesiones recuerdan usarla.
5. **La procedencia** se pide al crear una plantilla (`/sqx-strategy-template`) y se guarda en
   `AlgoData/templates/registry.csv` y en la fila.

### 3.3 · Qué hace con ello la corrección

`ledger/trials.py` ya acumula momentos de todas las búsquedas. Con L2, el N incluye las pruebas de los
barridos, y el informe de `ledger.report` añade una tabla por estudio: barridos, pruebas por barrido y
elegido. Una prueba en las mismas unidades que las demás entra en la sigma; una en otra unidad se cuenta
pero no se mezcla, como ya hace `accumulated`.

## 4 · Decisiones del dueño antes de construir — pregúntalas (regla dura 11)

1. **¿Cuentan como ensayos los barridos que sólo miran y no eligen?** Por ejemplo, un estudio que enseña
   cuatro percentiles lado a lado sin elegir ninguno. Propuesta: se apuntan con `chosen` vacío, y cuentan
   para el N sólo si después alguien eligió uno.
2. **¿Cuentan las reejecuciones por un error de código?** Una corrida repetida porque la anterior falló no
   es un ensayo. Propuesta: la orden de reejecución lleva un `--fix` que la marca y no cuenta.
3. **¿Se apuntan los barridos antiguos?** Propuesta: sólo desde ahora. Lo anterior ya está en los ficheros
   de la fábrica y del SPP, y `ledger.backfill` puede rescatar lo que se pueda, marcado `backfill`.

## 5 · Verificación

1. **Un barrido de tres valores deja tres filas** y un elegido, y el informe dice «probados 3, elegido 1».
2. **Una reejecución con `--set` se detecta sola**: dos corridas de la puerta con dos umbrales sobre la
   misma cosecha quedan en el mismo `search_id`.
3. **El N sube.** Un test donde un barrido de diez valores sube el N de `trials.accumulated` y baja el Sharpe
   deflactado del elegido, y un barrido con `chosen` vacío no lo mueve.
4. **Nada se rompe**: `tests/test_thresholds.py` y los tests del ledger siguen en verde.

## 6 · Cómo cierras

- Capítulo de manual para `ledger.tried` y la tabla nueva de `ledger.report`, en `AlgoData/manual-fuentes/`
  (regla dura 8).
- El contrato L2 en `ledger/README.md`.
- Una línea en `CLAUDE.md`, en «Standing rules», que diga que todo barrido se apunta con `ledger.tried`, para
  que las sesiones y los agentes lo hagan. Es un cambio de instrucciones: enséñaselo al dueño antes.
- `python3 tools/depmap.py && python3 tools/checks.py`.
- Lista de ficheros cambiados y **¿Quieres hacer el commit?** (regla dura 12).
