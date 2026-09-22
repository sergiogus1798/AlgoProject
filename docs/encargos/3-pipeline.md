# ENCARGO 3 — `pipeline/`, el encadenador por estrategia

**Tu oficio:** Python. **Tu encargo es una carpeta nueva en la raíz del repositorio**, que no existe
todavía y que nadie más va a tocar.

No necesitas leer el plan grande. Lee `CODESTYLE.md` antes de escribir una línea.

---

## 0 · Lo que construyes

Encadena las etapas del estudio de robustez **por estrategia madre**: entra una madre, se ejecutan
sus etapas en orden, sale un veredicto, se borra lo innecesario, empieza la siguiente.

Con ~100 madres eso son **días de máquina desatendida**. Por eso la reanudabilidad y la higiene de
disco no son detalles de calidad: son el requisito.

Las etapas son, en orden: **sppUltra → diseño de variantes → fabricación → ejecución → recogida →
walk forward correlation → veredicto**. De esas, solo `strategies/sppUltra/` existe hoy.

---

## ⚠️ 1 · El aviso que vale más que el resto del encargo

**Esto es la cola de trabajos de un futuro demonio, aunque hoy sea un programa de línea de
comandos.** El proyecto va a acabar teniendo un proceso siempre vivo con una cola única, y esta
carpeta es su corazón.

Escrito como «script que encadena etapas», se tira cuando llegue ese momento. Escrito como **un
modelo de *trabajo* con su *libro mayor***, sobrevive y el demonio se reduce a ponerle un servidor
encima. **Cuesta lo mismo hoy.** En concreto significa tres cosas:

1. **El estado se escribe DURANTE cada etapa, no al terminarla.** Una etapa que corre 40 minutos y
   no dice nada hasta acabar es indistinguible de una colgada. Cada etapa va anotando
   `stages.<nombre>.progress` (0..100) más una línea de estado legible, mientras corre.
2. **Una etapa es una función con una firma común, registrada en un sitio.** Añadir la séptima etapa
   tiene que ser añadir una función y una fila, y nada más (`CODESTYLE.md` regla 5).
3. **El libro mayor sobrevive al borrado.** Pesa kilobytes; los datos que describe pesan gigas. Se
   borran los datos, se conserva el registro. **Eso es lo que hace que el borrado sea auditable** en
   vez de una pérdida.

El dueño ha dicho esto, y explica el punto 1 mejor que nada:

> *«No me gusta mirar a una pantalla donde no aparece nada preguntándome si el programa se ha
> colgado.»*

---

## 2 · Contrato C5 — `state.json`

Lo produces tú y es la interfaz con todo lo demás. Vive en
`AlgoData/pipeline/<proyecto>/<estrategia>/state.json`.

```json
{ "strategy": "Strategy 17.9.39",
  "stage": "collected",
  "stages": {
    "sppultra":  {"done_at": "...", "verdict": "proceed", "brief_hash": "...",
                  "progress": 100, "status": "8.412 permutaciones leídas"},
    "build":     {"progress": 37, "status": "1.850 de 5.000 variantes escritas"}
  } }
```

Reglas del contrato:

- **`progress` es monótono** dentro de una etapa. Nunca retrocede.
- **Se escribe mientras la etapa corre**, no al final.
- Una escritura **no puede corromper el fichero** si el proceso muere a mitad. Escritura atómica.
- **Lo lee otro proceso mientras tú escribes.** Un monitor de vida, y mañana un demonio.

---

## 3 · Los otros contratos — solo los consumes

**No los produces tú y no dependes de que existan: trabajas contra fixtures.** Definición completa
en `docs/AgentPDFs/protocolo-robustez-2026-09-21.md` §2.

| | fichero | quién lo produce |
|---|---|---|
| **C1** | `design_brief.json` — qué parámetros y con qué niveles | `strategies/sppUltra/` *(existe)* |
| **C2** | `manifest.parquet` — una fila por variante, la clave de unión del estudio | otro agente, en curso |
| **C3** | `metrics.parquet` — 41 métricas × {IS, OOS} | no existe aún |
| **C4** | `trades.parquet` — 12 columnas, bloques de 500 variantes | no existe aún |

⚠️ **No importes `sqx/variants/`.** Está siendo escrito por otro agente ahora mismo. Tu registro de
etapas apunta a funciones que hoy son *stubs* y mañana serán las de verdad: si la firma está bien
elegida, el cambio es una línea.

---

## 4 · Lo que el pipeline tiene que hacer bien

**Reanudar.** Se para en la madre 43 por un corte de luz, arranca otra vez, y continúa en la 43 por
la etapa que quedó a medias. Sin repetir lo hecho y sin saltarse nada.

**Borrar con red.** Entre madre y madre se borran gigas de variantes. Antes de borrar, lo que
justifica el borrado (las métricas, los trades, el veredicto) tiene que estar escrito y verificado.

⚠️ **La estrategia madre no se borra nunca.** En el manifiesto C2 va marcada con `origin = true`, y
el paso de recogida se niega a tocarla. Tu pipeline tampoco.

**Presupuesto de disco.** `perf/disk/` ya inventaría `AlgoData` y tiene presupuesto y política de
retención (`budget.py`, `retention.py`). **Úsalos, no los reimplementes.** Datos de hoy: `AlgoData`
son 2,5 GB de un presupuesto de 60, y la rama `raw` tiene 40 GB de los que 100 madres de trades
van a consumir ~20. El presupuesto es el que tiene que frenar la corrida, no el disco lleno.

**Los umbrales del veredicto son configuración.** Decisión del dueño, 2026-09-21: los decide el
usuario y son cambiables. **Cambiar un umbral no puede obligar a reprocesar** — el pipeline guarda
los números, no los juicios.

---

## 5 · Forma del módulo

Sigue la forma que ya usa `strategies/sppUltra/`, que es el patrón de la casa: un `config.yaml` con
todos los mandos agrupados por la capa que los lee, subcarpetas con nombre y con su propio
`README.md`, y un punto de entrada.

De `CODESTYLE.md`, lo que más va a morder aquí:

- **250 líneas por fichero, máximo.**
- **Cada carpeta con `.py` lleva un `README.md`** con la tabla de ficheros, y cada `.py` abre con
  una línea de docstring.
- **Sin código defensivo.** Si el dato está mal, que reviente: un traceback dice más que un salto
  silencioso. *(La excepción razonada es la escritura atómica del §2 — eso no es defensa contra
  datos malos, es un requisito del contrato. Si una regla te obliga a escribir código peor, dilo y
  explícalo; no la incumplas en silencio.)*
- **Nada de configurabilidad que nadie ha pedido.**
- **Ninguna ruta absoluta fuera de `core/paths.py`.**

⚠️ **No toques `core/`** en esta tanda: lo posee otro agente. Si necesitas un helper compartido,
escríbelo dentro de `pipeline/` y anótalo en tu entrega.

---

## 6 · Verificación

```bash
python3 tools/depmap.py && python3 tools/checks.py    # 0 problems
```

Y las dos que prueban que esto es un pipeline y no un script:

1. **El test de monotonía de `progress`.** Es el que convierte la convención del §2 en contrato.
   Que falle si una etapa retrocede o si escribe solo al terminar.
2. **Interrumpe y reanuda.** Mata el proceso a mitad de una etapa, arráncalo otra vez, y demuestra
   que continúa donde estaba y que el `state.json` no quedó corrupto. **Pega la salida.**

---

## 7 · Cómo cierras

`pipeline/` es un `__main__` nuevo, así que **la página de manual es parte de esta tarea, no un
extra**: `docs/manual/17-pipeline.md`, copiando `docs/manual/_PLANTILLA.md`, **en español**, con
capturas de salida real. `checks.py` falla si un `__main__` no aparece en ninguna página.

La plantilla exige cuatro secciones: *qué pregunta responde · cuándo lo usas y cuándo no · antes de
empezar · cómo se ejecuta*. La regla de oro de la plantilla es **lo escribe alguien que sabe, para
alguien que no**: si una frase solo se entiende sabiendo cómo está programado por dentro, está mal
escrita.

Devuelve: qué construiste y por qué esa forma · la salida de la §6 pegada · qué dejaste sin hacer ·
qué descubriste que merezca ir a `knowhow/`, escrito allí en esta misma tarea.

**Compartido con otros agentes:** `docs/DEPENDENCIES.md` se **regenera**, no se fusiona.
`requirements.txt`: añadir línea, nunca reordenar.
