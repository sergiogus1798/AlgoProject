# 8 · El libro mayor global de la búsqueda — encargo autocontenido

**Tu oficio:** Python. **Tu encargo es elevar un ledger que ya existe**, de una madre a todo el
estudio, y cablear a él las dos correcciones por multiplicidad que ya están escritas.

Lee `CODESTYLE.md` · `pipeline/ledger/README.md` · `docs/AgentPDFs/WORKFLOW.md`. No necesitas más.

**Es el primero de los seis y es el cimiento.** Los otros cinco escriben en él. Hasta que exista,
cada test nuevo que se añada a la cadena empeora el sesgo de selección sin dejar rastro.

## ✅ ESTADO — construido el 2026-09-24, salvo una cosa

Existe `ledger/`, con su página de manual `docs/manual/43-ledger.md` (el encargo pedía la 39, que ya
estaba ocupada por la nube de parámetros) y su test `tests/test_ledger.py`.

| pedido | estado |
|---|---|
| §2.1 una fila por búsqueda, contrato L1 | ✅ `ledger/record.py`, JSONL append-only bajo el data root |
| §2.2 `N` y `V[SR]` acumulados por familia | ✅ `ledger/trials.accumulated`, agrupación **exacta** desde los momentos guardados |
| §2.2 el mapa de datos gastados | ✅ `ledger/spend.py` |
| §2.3 la puerta de un solo sentido | ✅ `ledger/gate.py` — lanza, y corre **antes** de escribir la fila |
| §2.4 umbrales versionados | 🟡 `ledger/thresholds.yaml` existe con 13 umbrales y su procedencia, y `--check-thresholds` comprueba que el código usa esos mismos números. **Los módulos siguen leyendo de su propio `config.yaml`**: migrarlos es lo que queda |
| §2.5 `n_eff` global | ✅ `core/surface/trials.py` — el conteo salió de `walkForwardCorrelation/verdict/` para que lo puedan usar los dos; `ledger/trials.population_n_eff` lo aplica a una población entera |
| §4.1 reconstruir un estudio existente | ✅ `XAU_ISOOS_ejemplo` reconstruido: 120 → 45 en ocho cribas |
| §4.2 la puerta lanza | ✅ probado sobre la política real y en el test |
| §4.3 el DSR se mueve con el `N` global | 🟡 **no se mueve en el estudio real, y el motivo importa**: sólo una de sus ocho búsquedas registró la distribución de sus candidatos, porque el `backfill` únicamente recupera lo que la puerta dejó escrito. El mecanismo está probado en `tests/test_ledger.py`: de N=1.600 a N=2.000 el listón sube 0,1995 → 0,2031 y el DSR baja **0,6301 → 0,6000** |

**Lo que queda, y es de quien lo coja:** que cada módulo lea su umbral de `thresholds.yaml` en vez
de su `config.yaml`. Son siete módulos en funcionamiento y ninguno tiene hoy una prueba de que
sigue haciendo lo mismo, así que se migra de uno en uno con su comprobación, no de golpe. Mientras
tanto, `python3 -m ledger.report --check-thresholds` es lo que impide que las dos copias diverjan.

---

## 0 · El problema, en una frase del dueño

> *«Al llegar al 17 nadie sabe si quedan tres supervivientes de diez mil o de cincuenta — y esa
> diferencia **es** el resultado, no un detalle de contabilidad.»*

Hoy cada paso de la cadena cuenta su propio embudo y lo olvida. El DSR que ya calculamos pregunta
«¿cuántas cosas se probaron?» y se le responde con las variantes de **una** madre, no con todo lo
que el pipeline ha probado nunca. El número está sistemáticamente subestimado, y siempre en la
dirección que hace que los resultados parezcan mejores.

## 1 · Lo que ya existe y NO se reescribe

| pieza | qué da | dónde |
|---|---|---|
| ledger por madre (contrato C5) | `state.json` atómico, progreso durante la etapa, `brief_hash` | `pipeline/ledger/state.py` |
| `n_eff` por clustering de correlaciones | trials independientes, silueta, el caso «un clúster de uno» | `strategies/walkForwardCorrelation/verdict/trials.py` |
| DSR | `deflated_sharpe(sharpe, sigma_sr, n_eff, n_obs, skew, kurtosis)` | `core/surface/plateau.py` |
| PSR y MinTRL | | `core/significance.py` |
| embudo de la puerta | cuántas entran y salen de cada criba, con sus umbrales | `gate/cascade.py` |
| manifiesto de variantes | una fila por `.sqx` real, `tuple_hash` | `sqx/variants/manifest.py` |
| segmentos y su papel | `build` / `oos1` / `oos2`, con `reserved_for` | `assets/_policy.yaml` |

**Tu trabajo no es matemática nueva.** Es contabilidad, y es la contabilidad la que hoy falta.

## 2 · Lo que construyes — `ledger/`, carpeta nueva en la raíz

Un registro **por estudio**, no por madre. Un estudio es: un símbolo, un timeframe, una plantilla o
familia de plantillas, y todo lo que se ha hecho con ellos desde la primera construcción.

### 2.1 · Una fila por búsqueda

Una *búsqueda* es cualquier cosa que mire datos y reduzca una población: un build de SQX, un retest,
una criba de Python, un cambio de umbral aplicado con `/curate`. Cada fila lleva:

```
study_id · timestamp · paso del WORKFLOW (1..20) · qué lo lanzó (comando, skill, agente)
config_hash · symbol · timeframe · segmento mirado (build/oos1/oos2) · ventana exacta
n_in · n_out · criterio aplicado y sus umbrales
sharpe_mean · sharpe_std · sharpe_max   ← la distribución, no sólo el ganador
seeds usadas (para lo que sea aleatorio: monos, bootstrap, variantes)
```

`sharpe_std` sobre los candidatos de esa búsqueda **es la `sigma_sr` que el DSR pide**. Hoy se
estima dentro de un lote de variantes; ahí es donde está subestimada.

### 2.2 · Dos salidas, que son la razón de existir del módulo

- **`N` y `V[SR]` acumulados por familia de estrategias**, listos para alimentar
  `plateau.deflated_sharpe`. «Familia» = mismo símbolo + misma plantilla. Suma las búsquedas de
  todos los pasos, no las de una.
- **El mapa de datos gastados**: qué tramos de historia ha mirado alguna búsqueda, cuántas veces, y
  **cuánto queda virgen**. Es la única forma de saber si el `oos2` sigue siendo un holdout.

### 2.3 · La puerta de un solo sentido — esto es lo que el dueño pidió forzado, no confiado

`assets/_policy.yaml` reserva `oos2` para WFC y WFM. El ledger tiene que **negarse** a registrar —
y por tanto a dejar correr — una búsqueda sobre `oos2` que no sea el paso 17 o el 19, y tiene que
negarse a servir los resultados de 17, 18 y 19 hasta que los tres estén hechos. El paso 20 va
ciego por decisión del dueño del 2026-09-23, y hoy eso depende de la buena voluntad de quien lo
corra.

Forma concreta: una función `ledger.gate(step, segment, study)` que los módulos llamen **antes** de
mirar datos, y que lance. Sin código defensivo alrededor: que reviente.

### 2.4 · Umbrales versionados que los agentes leen y no editan

Un `ledger/thresholds.yaml` con las cotas de cada paso, su fecha y quién las fijó. Los módulos lo
leen; ningún módulo lo escribe. Un umbral movido después de ver los resultados es la forma más
barata de sobreajustar una cadena entera, y sin fecha no se distingue de uno fijado de antemano.

### 2.5 · `n_eff` global

`trials.independent()` agrupa variantes correlacionadas de una madre. Extiéndelo para aceptar el
panel de **toda la población superviviente** — es la misma matriz de equity diaria que
`gate/collect.py` ya cosecha — y deja que el DSR se alimente de ese `n_eff` global.

⚠️ El detalle que no se puede perder: **una variante sola en su clúster puntúa cero en la silueta**,
por convención y con motivo — sin eso, el recuento que gana es 2 en vez de 21 (medido 2026-09-22).

## 3 · Lo que NO es tuyo

- **Reescribir `pipeline/ledger/`.** Lo consumes y lo elevas; el contrato C5 por madre se queda.
- **Cambiar ningún umbral existente.** Los mueves de donde estén a `thresholds.yaml`, con su valor
  actual intacto y una nota de quién lo puso. Cambiarlos es del dueño.
- **Tocar la configuración de los proyectos del maestro.** Regla dura 3.

## 4 · Verificación

```bash
python3 tools/depmap.py && python3 tools/checks.py    # 0 problems
```

Y las tres que prueban que esto es un ledger y no un CSV:

1. **Reconstruye hacia atrás un estudio que ya existe** — `XAU_ISOOS_ejemplo` tiene build (120) y
   OOS (115), y la puerta tiene su embudo escrito. El ledger tiene que poder decir su `N` sin que
   nadie se lo teclee.
2. **La puerta del `oos2` lanza.** Pide una búsqueda del paso 8 sobre `oos2` y demuestra que se
   niega. Pega la traza.
3. **El DSR se mueve al alimentarlo con el `N` global.** Enseña el mismo veredicto con el `N` de un
   lote y con el `N` acumulado. Si no se mueve, o el estudio es pequeño o el cableado está mal:
   averigua cuál y dilo.

## 5 · Cómo cierras

Hay `__main__` nuevo → **la página de manual es parte de esta tarea** (regla dura 8): copia
`docs/manual/_PLANTILLA.md` a `docs/manual/39-ledger.md`, en español, con salida real pegada.

Devuelve: qué construiste y por qué esa forma · la salida de la §4 pegada · qué dejaste sin hacer ·
qué descubriste que merezca ir a `knowhow/`, escrito allí **en esta misma tarea**.
