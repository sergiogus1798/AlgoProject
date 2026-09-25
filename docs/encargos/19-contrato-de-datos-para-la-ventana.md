# 19 · Reorganizar los módulos de estudio para que la ventana los pinte — el contrato de datos

**Para quién.** Una instancia que va a refactorizar o reorganizar `strategies/`, `tasks/`, `nulls/`
y `gate/`. Este fichero es lo que la ventana de escritorio (`ui/`) necesita de esa reorganización.
El resto del refactor —nombres, carpetas, deduplicación— es tuyo; **esto no se negocia**, porque
es lo que hace que los estudios se vean dentro de la ventana con widgets nativos y no en un
navegador.

**Por qué.** Decisión del dueño, 2026-09-25: los tres paneles Flask (`strategies/monteCarlo/
explorer/`, `strategies/retest/explorer/`, `strategies/crossmarket/explorer/`) se retiran y su
profundidad pasa a la zona «Estudios» de la ventana, pintada con **QtCharts y widgets propios**,
no con HTML embebido. Para eso el dato tiene que salir del módulo como **datos**, no como string
HTML. Hoy está atrapado dentro del HTML y solo el navegador lo puede leer.

**Qué NO perder.** `docs/AgentPDFs/paneles-flask-inventario-2026-09-25.md` lista todo lo que los
paneles ofrecen. Su última sección, los diez puntos, es el listón: la reorganización no puede
dejar ninguno sin sitio.

Antes de escribir Python: `CODESTYLE.md`. Al acabar: `python3 tools/depmap.py && python3
tools/checks.py`, y la página del manual de cada comando que cambie de nombre.

---

## 1. La forma de cada módulo de estudio

Cada módulo que juzga o describe estrategias (`monteCarlo`, `retest`, `crossmarket`, `crossTF`,
`sppUltra`, `parameterCloud`, `profitShape`, `entryQuality`, `exposure`, `walkForwardCorrelation`,
`walkForwardMatrix`, `nulls`, `gate`, y las cinco lecturas de `tasks.reports`) queda con **la misma
forma**, y la ventana los trata a todos igual:

```
<modulo>/
  config.yaml      todos los mandos, agrupados por sección, con comentario por mando
  tooltips.py      una frase por mando, en español, para el cajón de configuración de la ventana
  one.py           run(strategy, inputs, cfg) -> dict          UNA estrategia, datos puros
  many.py          run(inputs, cfg) -> dict                    la población entera (si el módulo la juzga)
  report.py        el comando python3 -m <modulo>.report       escribe el informe y el verdict.csv
  render/          dict -> HTML del informe por lotes          NO calcula nada
```

Reglas:

1. **`one.run` y `many.run` devuelven un dict de datos puros** (ver §2). Ningún string HTML,
   ningún objeto de matplotlib, ningún DataFrame: listas, dicts, números, strings. Serializable a
   JSON tal cual. Ese dict es lo que la ventana pide al demonio y pinta.
2. **`render/` consume ese dict y solo ese dict.** El informe por lotes y la ventana leen la misma
   estructura, así que no pueden discrepar. Hoy los paneles ya cumplen «el informe es byte a byte
   lo que se ve»; esto lo conserva cambiando quién es el dueño del dato.
3. **`cfg` entra como argumento y se firma en la salida**: el dict lleva `"config_hash"` de la
   configuración con la que se calculó. La ventana marca caducado un resultado cuya huella no
   coincide con el cajón (lo que hace hoy `monteCarlo/explorer/cache.py`).
4. **Un `--set seccion.clave=valor` por módulo**, con el mismo casteo que `gate.inputs.config`:
   el override toma el tipo del valor que sustituye. La ventana lanza los módulos con esos flags.
5. **Progreso por stdout**: la línea `PROGRESS <0..100> <estado>`, la del pipeline. Cualquier otra
   línea es el estado sin mover la barra.
6. **El veredicto de población es un CSV con `strategy` e `identity` y `verdict`** en
   `reports/<proyecto>/<databank>/<día>/<modulo>/`, con `manifest.json` que nombra la entrada que
   juzgó (ruta absoluta) y los overrides. La ventana empareja informe y entrada por ese manifest,
   nunca por la fecha de la carpeta.
7. **Los tres `jobs.py`, `scope.py` y `tooltips.py` duplicados** se unifican: `jobs` y `scope` en
   un solo sitio (el demonio ya tiene `ui/daemon/jobs.py`; `scope` = aplicar overrides a un
   `config.yaml`, hoy `gate.inputs.config`), y `tooltips.py` se queda uno por módulo porque las
   frases son del módulo.

## 2. El contrato de datos — seis tipos de dibujo y las tablas

Todo lo que los tres paneles dibujan cabe en seis tipos. Cada bloque del dict de salida es uno
de ellos, con `"kind"` como primera clave. La ventana tiene un widget por `kind`; un módulo que
emite un `kind` nuevo tiene que añadir el widget, así que **no se inventan tipos**: se pregunta.

```python
# 2.1 Distribución con la real marcada — histograma, mediana, banda, percentiles, valor real.
#     El dibujo base de todo: cada test de MC, cada modelo nulo de crossmarket, el mono.
{"kind": "distribution", "title": str, "unit": str,            # "USD", "%", "R", ""
 "bins": [float, ...], "counts": [int, ...],                    # el histograma ya agregado, NUNCA los draws
 "real": float, "median": float, "band": [float, float],        # p5–p95 o lo que diga cfg
 "percentiles": {"1": float, "5": float, ..., "99": float},
 "p": float | None, "note": str}                                # p-valor si el test lo tiene; una frase

# 2.2 Cono de equity con la real encima — familia A, entrada aleatoria, estrés, portfolio.
{"kind": "cone", "title": str, "unit": str,
 "x": ["YYYY-MM-DD" | int, ...],                               # fechas, o progreso normalizado 0..100
 "bands": {"2.5": [...], "25": [...], "50": [...], "75": [...], "97.5": [...]},
 "real": [float, ...], "split": "YYYY-MM-DD" | None}            # dónde empieza el OOS, si aplica

# 2.3 Rejilla de calor — barrido de ventana, SPP, WFM, nube de parámetros.
{"kind": "grid", "title": str,
 "rows": [str, ...], "cols": [str, ...], "values": [[float | None, ...], ...],
 "scale": "discrete" | "diverging" | "sequential",
 "levels": [float, ...] | None,                                 # cortes de la escala discreta; el dueño quiere escalas discretas
 "labels": [[str, ...], ...] | None}                            # texto por celda (p, tendencia)

# 2.4 Nube de puntos — WFC (dentro contra fuera), y cualquier x/y por combinación.
{"kind": "scatter", "title": str, "x_label": str, "y_label": str,
 "points": [{"x": float, "y": float, "label": str, "group": str}, ...],
 "quadrants": bool, "fit": {"slope": float, "intercept": float, "r": float} | None}

# 2.5 Barras — atribución entre tareas, embudo, potencia por bloque, contribución por mercado.
{"kind": "bars", "title": str, "unit": str,
 "items": [{"label": str, "value": float, "error": [float, float] | None, "state": str}, ...],
 "reference": float | None}                                     # la línea del control, el cero, el umbral

# 2.6 Curvas — varias series en el tiempo: equity por mercado, dos series de régimen, p por bloque.
{"kind": "lines", "title": str, "unit": str, "x": [...],
 "series": [{"label": str, "values": [float | None, ...], "role": "real" | "sim" | "reference"}, ...]}
```

Y dos que no son dibujos:

```python
# 2.7 Tabla — percentiles, la tabla de confianza de SQX, las ocho tareas, el glosario.
{"kind": "table", "title": str, "columns": [str, ...], "rows": [[...], ...],
 "align": ["left" | "right", ...], "note": str}

# 2.8 Veredicto categórico con su significado — la etiqueta NUNCA sola (catálogo §4).
{"kind": "verdict", "label": str, "state": "pass" | "fail" | "watch" | "info" | "none",
 "score": float | None, "meaning": str,                         # la frase que explica la etiqueta
 "parts": [{"label": str, "state": str, "value": float | None, "note": str}, ...]}   # las familias, las puertas
```

Reglas de los bloques:

- **Agregado, nunca crudo.** Un `distribution` lleva el histograma, no los 100.000 draws; un
  `cone` lleva los percentiles por punto, no las corridas. Es lo que hace que un resultado pese
  cientos de KB y no GB, y lo que hoy hace `monteCarlo/explorer/cache.py`.
- **Cada bloque lleva su `title` y su `note`** en español: la ventana no inventa texto.
- **`state` siempre es una de cinco palabras**: `pass`, `fail`, `watch`, `info`, `none`. Son las
  cinco de la escala de color de la ventana (`ui/desktop/theme.py`). Ni «MANTENER» ni «FAIL» ni
  «worth_it» en los bloques: esas palabras viven en el `verdict.csv`, que es para `/curate`, no
  para pintar. Un módulo que necesite una sexta palabra pregunta.
- **Nada de color en el dato.** El dato dice `state`; el color lo pone la ventana.

## 3. La forma del dict entero de una estrategia

```python
{"module": "monteCarlo", "strategy": str, "identity": str,      # SHA-256 del XML normalizado; el nombre no identifica
 "config_hash": str, "computed_at": "ISO", "wall_s": float,
 "verdict": {kind: verdict} | None,                              # None si el módulo describe y no juzga
 "tabs": [                                                       # las pestañas, en el orden en que se leen
   {"name": str, "title": str,
    "selectors": [{"key": str, "label": str, "options": [str, ...], "default": str}, ...],
    "blocks": [ ...bloques de §2... ]}],
 "warnings": [{"code": str, "state": str, "text": str}, ...],   # los avisos que colorean y no eliminan
 "glossary": [{"term": str, "text": str}, ...]}
```

**Selectores.** Un tab con `selectors` (mercado × modelo × estadístico, tamaño de bloque, métrica)
lleva **todos** sus bloques ya calculados, uno por combinación, marcados con
`"select": {"market": "EURUSD", "model": "block_shift", "stat": "sharpe"}`. La ventana filtra y
redibuja sin volver al módulo. Es el punto 3 del inventario y es lo que hace que cambiar un
desplegable sea instantáneo.

**Re-ejecutar una subprueba** (Monte Carlo) y **correr un mercado suelto** (crossmarket) son
entradas de `one.run` con un argumento `only=` (`only="C.fill"`, `only="EURUSD"`) que devuelven el
dict parcial; **fusionar** es responsabilidad del demonio, no del módulo.

## 4. Lo que la ventana ya lee hoy, y no puede moverse sin avisar

| qué | dónde lo lee `ui/` |
|---|---|
| `gate.inputs.config`, `gate/config.yaml` | `ui/daemon/gateview.py` |
| `core.assetdata`, `core.datapaths`, `core.paths` | todo el demonio |
| `sqx.templates.holes`, `sqx.templates.registry`, `sqx.blocks.palette`, `sqx.blocks.taxonomy` | zonas de plantillas y paletas |
| `reports/<P>/<D>/<día>/<módulo>/*.csv` con columna `strategy` | `ui/daemon/studies.py` |
| `harvest/<P>/<D>/<día>/{metrics,equity,trades}.parquet`, `missing_oos.csv`, `manifest.json` | `ui/daemon/gateview.py` |
| `reports/.../gate/{scorecard.parquet,funnel.csv,manifest.json}` | `ui/daemon/gateview.py` |
| los comandos `python3 -m gate.report`, `strategies.*.report`, `nulls.one`, `tasks.reports.decay` y sus flags | `ui/daemon/runs.py` |

Si algo de esta tabla cambia de nombre o de sitio, **se cambia también en el fichero de `ui/` que lo
lee, en el mismo commit**, y se comprueba con `bin/algoui`. Un import roto en el demonio es la
ventana entera sin abrir.

## 5. Orden sugerido

1. `monteCarlo`: es el más completo y ya tiene caché con huella; su dict sirve de plantilla.
2. `retest` y `crossmarket`, que comparten `jobs/scope/tooltips` con él.
3. `gate` y `nulls`, que la ventana ya usa: aquí se prueba que la tabla del §4 se respetó.
4. El resto, por el orden del catálogo (`catalogo-para-la-ui-2026-09-25.md` §3).

Los tres `serve.py` y los tres `page.html` se borran cuando su módulo tiene `one.run` emitiendo el
contrato y `render/` lo consume. No antes: hasta entonces son la única forma de mirar esos estudios.

## 6. Cómo se sabe que está hecho

- `python3 -c "from strategies.monteCarlo import one; import json; json.dumps(one.run(...))"`
  serializa sin error y cada bloque tiene un `kind` de los ocho.
- El informe por lotes de cada módulo, generado antes y después, **es idéntico** o su diferencia
  está explicada en el commit.
- `python3 tools/checks.py` en verde, y cada comando renombrado con su página del manual.
- Este fichero se borra: lo que valga de él pasa a `strategies/CLAUDE.md` como la forma de un
  módulo de estudio.
