# ENCARGO 4 — `sqx/variants/`, diseño y fabricación

**Tu oficio:** Python. **Tu encargo es una carpeta nueva dentro de `sqx/`** que no existe todavía y
que nadie más va a tocar.

No necesitas leer el plan grande. Lee, en este orden: `CODESTYLE.md` · `sqx/CLAUDE.md` ·
`knowhow/01-file-formats.md` · `knowhow/03-driving-sqx.md`.

---

## 0 · Antes de escribir una línea

```bash
python3 -m core.assets XAUUSD
```

**Es bloqueante.** Si sale con código distinto de cero, para y dilo. Regla dura 5 del proyecto: es
la comprobación de que el dueño ha acordado spread y comisión para ese símbolo. Reporta qué
sobreescrituras se aplican.

---

## 1 · Lo que construyes

Un `.sqx` es una estrategia con unos parámetros concretos. **No existe ningún verbo de `sqcli` que
cambie los parámetros de una estrategia** — comprobado contra la referencia completa de verbos. La
única forma de puntuar una combinación elegida es **escribirla en un `.sqx` y retestear ese
fichero**.

Tú construyes la fábrica: entra un diseño (contrato C1), salen **5.000 ficheros `.sqx`** y el
manifiesto que dice qué es cada uno (contrato C2).

**Tu encargo llega hasta ahí.** Cargarlos en SQX, lanzar el retest y recoger resultados es otro lote
y no es tuyo.

---

## 2 · Los contratos

### C1 — entra. Lo produce `strategies/sppUltra/`, que ya existe

```json
{ "strategy": "Strategy 17.9.39", "project": "XAUUSD", "source_databank": "SPP IS",
  "verdict": "proceed", "n_eff": 8412,
  "parameters": [ { "name": "DIPeriod1", "eta2": 0.184, "inert": false,
      "center": 67, "center_rule": "best_value", "levels": [55,61,67,73,79],
      "original": 64, "argmax_is": 71, "plateau_width": 12, "is_shift": false } ],
  "frozen": [ { "name": "CBlock_SqzMmnInt21", "value": 21, "reason": "exact_duplicates" } ],
  "strata": { "neighbourhood": 0.20, "factorial": 0.60, "coverage": 0.20 }, "n_target": 5000 }
```

**Trabaja contra un fixture.** No dependas de correr `sppUltra`.

### C2 — sale. **Es la clave de unión de todo el estudio**

Una fila por variante fabricada:

| columna | qué es |
|---|---|
| `variant_id` | `P00000`… y **escrito también dentro del `.sqx`** (nombre o comentario) |
| `sqx_name` | el nombre con el que SQX lo devuelve, tras un posible renombrado en colisión |
| `stratum` | `neighbourhood` · `factorial` · `coverage` · `canary` · `origin` |
| `param_<nombre>` | una columna por parámetro del diseño |
| `tuple_hash` | hash de la tupla, para detectar duplicados de fabricación |
| `origin` | `true` en la estrategia madre — **el borrado se niega a tocarla** |
| `canary_expect_netprofit`, `canary_expect_trades` | solo en los centinelas |

Formato **Parquet**. Definición completa en `docs/AgentPDFs/protocolo-robustez-2026-09-21.md` §2.

---

## 3 · Hechos ya medidos — **no los vuelvas a medir**

Todos 🔬 verificados y en `knowhow/`. Te ahorran días.

- **Los valores de parámetro viven en un solo sitio**: `strategy_Portfolio.xml`, en
  `<variable><id>NOMBRE</id>…<value>N</value></variable>`. Las reglas referencian la variable por
  nombre (`<Param key="#Period#" …>DICrossPeriod1</Param>`), así que **reescribir `<value>`
  reescribe la regla**. `settings.xml` **no** lleva los nombres de parámetro — grepeado, cero
  coincidencias.
- **Hay que renombrar dos campos, los dos en `settings.xml`**: `<ResultsGroup ResultName="…">` y
  `<StrategyName type="String">`. Si no, **todas las variantes caen bajo un mismo nombre**.
- **Escribir variantes es mecánico y está verificado de punta a punta** sobre `Strategy 17.9.39`: 8
  sustituciones, reempaquetar, leer de vuelta, valores correctos.
- **Pesos por forma de fichero**: íntegro (8 miembros) **5.215 KB** · sin `optimizationProfile.bin`
  **100 KB** · solo `META-INF` + `settings.xml` + `strategy_Portfolio.xml` + `lastSettings.xml` +
  `version.txt` **11,3 KB**. Para 5.000 variantes eso es la diferencia entre **57 MB y 26 GB**.
- **Una sola corrida de retest da las dos muestras.** Si el `Setup` abarca IS+OOS y el
  `<OutOfSample>` está puesto, sample 10 y sample 20 quedan en el mismo `.sqx`. **Un WFC necesita
  una corrida, no dos.**
- ⚠️ **`RExpectancy` lleva centinelas**: `99999.0` (3 filas) y `-1.0` (15 filas), todas con ~1
  operación. Son el 0,08 % — y **ganan el argmax sobre 5.000 variantes**. Filtra `|v| > 100` antes
  de cualquier ranking.
- ⚠️ **Dos columnas llevan un `?` literal en el nombre**: `CalmarRatio?` y
  `AnnualPctReturnDDRatio?`. Pedirlas sin el `?` devuelve una columna entera de NaN, sin error.
- **Nombres de proyecto: solo guiones bajos.** La API HTTP parte su comando por espacios.

---

## 4 · Los tres modos de fallo que este módulo existe para impedir

Los tres son **silenciosos**: no revientan, producen un estudio que parece bien y está mal. Que tu
diseño los haga imposibles, no improbables.

1. **Renombrado en colisión.** SQX puede devolver una estrategia con un nombre distinto del que le
   diste. Por eso C2 tiene `sqx_name` además de `variant_id`, y por eso el `variant_id` va **también
   dentro del fichero**: si el nombre externo cambia, la identidad sigue dentro.
2. **`<Fingerprint>` heredado.** Todas las variantes nacen del mismo padre. Si el databank deduplica
   por esa huella, 5.000 variantes se convierten en una y nadie se entera.
3. **Tupla ≠ fichero.** Que el fichero `P01234` contenga de verdad la combinación que el manifiesto
   dice. El `tuple_hash` de C2 existe para esto: duplicados de fabricación y desajustes se detectan
   contándolos, no confiando.

**Los centinelas (`canary`) son tu control positivo.** Variantes cuyo resultado conoces de antemano
(`canary_expect_netprofit`, `canary_expect_trades`): si no vuelven con lo esperado, la cadena está
rota en algún punto y te enteras antes de mirar 5.000 resultados.

---

## 5 · La decisión que no tienes que esperar

Dos preguntas siguen abiertas y las está respondiendo hoy otro agente, sobre la instalación real:

- ¿**carga SQX un `.sqx` de 5 miembros**, sin `orders.bin` ni curva de equity?
- ¿**deduplica el databank por el `<Fingerprint>` heredado**?

**No te bloquees.** La forma de fichero es **una constante, no una arquitectura**: programa las tres
formas, deja la elección en el `config.yaml`, y se fija cuando llegue la respuesta. La encontrarás
en `knowhow/01-file-formats.md`.

---

## 6 · Forma del módulo

Sigue la forma de `strategies/sppUltra/`, que es el patrón de la casa: `config.yaml` con todos los
mandos, subcarpetas con nombre y su propio `README.md`, punto de entrada separado de la librería.

Las fronteras naturales aquí, y conviene respetarlas porque son tres trabajos distintos:

| | qué decide |
|---|---|
| **diseño** | qué 5.000 combinaciones, repartidas por estrato. Matemática pura, sin tocar ficheros |
| **fabricación** | escribir los `.sqx`. Mecánica pura, sin decidir nada |
| **manifiesto** | qué se fabricó de verdad, leído de vuelta del disco — **no** de lo que se pretendía fabricar |

Esa tercera frontera es la que hace detectable el modo de fallo 3. El manifiesto describe lo que
hay, no lo que se quería.

De `CODESTYLE.md`: 250 líneas por fichero · `README.md` por carpeta con su tabla · docstring de una
línea en cada `.py` · **sin código defensivo** · sin configurabilidad que nadie pidió · ninguna ruta
absoluta fuera de `core/paths.py`.

⚠️ **No toques `core/`** en esta tanda: lo posee otro agente. Si necesitas un helper compartido,
escríbelo dentro de `sqx/variants/` y anótalo.

⚠️ **No cargues nada en SQX ni arranques ningún trabajo.** Tu encargo escribe ficheros en disco.
Ejecutarlos es otro lote.

---

## 7 · Verificación

```bash
python3 tools/depmap.py && python3 tools/checks.py    # 0 problems
python3 -m core.assets XAUUSD                         # sigue en 0
```

Y las dos que prueban que la fábrica fabrica:

1. **Golden test del reescrito de `.sqx`, en `tests/`.** `CODESTYLE.md` lo exige explícitamente para
   los parsers de `.sqx` y `.cfx`: *un parser que se rompe en silencio envenena todos los análisis de
   aguas abajo y nadie se entera en semanas.* Entrada guardada, salida esperada.
2. **Un lote pequeño de verdad**: fabrica 3 variantes, léelas de vuelta, y comprueba que los valores
   son los que pediste, que los dos campos de nombre están renombrados, y que el `tuple_hash` del
   manifiesto casa con el contenido real del fichero. **Pega la salida.**

---

## 8 · Cómo cierras

`sqx/variants/` trae un `__main__` nuevo, así que **la página de manual es parte de esta tarea**:
`docs/manual/18-variantes.md`, copiando `docs/manual/_PLANTILLA.md`, **en español**, con capturas de
salida real. `checks.py` falla si un `__main__` no aparece en ninguna página.

La plantilla exige: *qué pregunta responde · cuándo lo usas y cuándo no · antes de empezar · cómo se
ejecuta*. Y su regla de oro: **lo escribe alguien que sabe, para alguien que no.**

Devuelve: qué construiste y por qué esas fronteras · la salida de la §7 pegada · qué dejaste sin
hacer · qué hecho nuevo descubriste, escrito en `knowhow/01-file-formats.md` en esta misma tarea,
con su etiqueta 🔬 / 📓 / 🤔.

**Compartido con otros agentes:** `docs/DEPENDENCIES.md` se **regenera**, no se fusiona.
`requirements.txt`: añadir línea, nunca reordenar. `tests/` es tuyo en esta tanda.
