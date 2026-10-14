# 68 · Adaptar el código y las comprobaciones al CODESTYLE del 2026-10-13

**Tu oficio:** ingeniería de herramientas sobre un Python que ya funciona: comprobaciones, hooks y
arreglos listados. Es trabajo significativo: se orquesta (`CODESTYLE.md` §13) — **Opus** parte y
comprueba, **Sonnet** escribe (regla 17). Son de Opus el diseño de las partes 6, 9, 14 y 16. Ningún
SQX, ningún dato nuevo. **El dueño lo quiere entero (2026-10-13, «mete TODO»): nada queda fuera.**
**Tu encargo:** que las reglas nuevas de `CODESTYLE.md` las compruebe una máquina y no la memoria de
un agente, y que el código viejo deje de incumplir las que son baratas de cumplir. Devuelves al dueño
**una tabla de recuentos antes y después** (avisos de ruff, generadores sin semilla, tests que corren
al entregar, métricas del trinquete) y la lista de los `B023` que eran bugs de verdad.

Lee `CODESTYLE.md` entero (174 → ~250 líneas; §4, §11, §12 y §13 son los nuevos) · `CLAUDE.md` reglas
12, 17, 20 y 21 · `.claude/hooks/README.md` · `tools/checks.py` · `tools/audit_tests.py` (cabecera).

## Estado del plan (lo actualiza cada sesión al cerrar)

| fase | qué | modelo | depende de | estado |
|---|---|---|---|---|
| F0 | decisiones del dueño: todas contestadas; D11 la propone Opus en F14 | dueño | — | hecho |
| F1 | los tests corren al entregar | Sonnet | D1 | hecho 2026-10-14 |
| F2 | hooks: lint ampliado al escribir, y cierre que no deja terminar en rojo | Sonnet | F1, D2 | hecho 2026-10-14 |
| F3 | trinquete en `checks.py` | Sonnet | — | hecho 2026-10-14 (`1e78492`) |
| F4 | ruff con `F401` y `B`; los 25 `B023` leídos | Sonnet | D3 | sin empezar |
| F5 | semillas | Sonnet | D4 | sin empezar |
| F6 | `assert` en los lectores con fichero dorado | Opus diseña, Sonnet escribe | D5 | sin empezar |
| F7 | menciones caducas del tope de 250 líneas | Sonnet | D6 | sin empezar |
| F8 | comprobador de tipos, por paquetes | Sonnet | F3, D7 | sin empezar |
| F9 | **los `-> dict` sin tipar, todos**, paquete a paquete | Opus orquesta, Sonnet escribe | F8, D8, D9 | sin empezar |
| F10 | límites por función (complejidad, argumentos) en el trinquete | Sonnet | F3 | hecho con F3 |
| F11 | código muerto: `vulture` de noche, y borrado de lo que halle | Sonnet | — | sin empezar |
| F12 | tabla del README generada del docstring | Sonnet | D10 | sin empezar |
| F13 | lockfile y versión de Python | Sonnet | — | sin empezar |
| F14 | canario nocturno de extremo a extremo | Opus diseña, Sonnet escribe | D11 | sin empezar |
| F15 | gorilla comprueba cada push | Sonnet | F1 | sin empezar |
| F16 | agente `reviewer` propio | Opus | — | hecho 2026-10-14 |
| F17 | convenciones que faltan en `CODESTYLE.md` | Sonnet | D12, D13 | hecho 2026-10-14 (§6) |
| F18 | `ruff format`, lo último | Sonnet | todo lo anterior | sin empezar |

### Bitácora

- 2026-10-13 — Encargo escrito tras la revisión de `CODESTYLE.md` con el dueño.
- 2026-10-13 — El dueño: «no lo dejes fuera lo de los dict, mete TODO». Añadidas F8 a F18.
- 2026-10-13 — El dueño contesta D7, D8, D9, D10, D12 y D13.
- 2026-10-13 — El dueño contesta D1, D2, D4, D5, D6 y D14: `ruff format` se hace al lanzar el encargo.
- 2026-10-13 — El dueño contesta D3: C.
- 2026-10-14 — Arranca la ejecución (sesión algoproject-7c, árbol limpio en `71c5e92`). El dueño: D6 sólo
  `discards.root()`, `portfolio_dir()` y `funding_dir()` vuelven a `core/paths.py`; D11 = de las
  operaciones exportadas al veredicto del paso 8; un commit por fase; sin Council. Línea base medida:
  ruff `F401,B` 344 (B905 235, F401 56, B023 25), C901 52, PLR0913 231, `default_rng()` 14,
  `np.random.*` 5, `-> dict` 1.377, `except` amplios 29, `ruff format` 1.511 ficheros, 330 tests.
- 2026-10-14 — F3+F10 hechos: el trinquete cuenta por AST (sólo públicas): `-> dict` 1.251, `except`
  amplios 57, `np.random.*` 12. F1 hecho: la suite entera tarda 487 s; `audit_tests.py --changed` corre
  sólo lo afectado y sale ≠ 0 en rojo. ASIDE: fuera 5 que ya pasan; entran `test_taxonomy` (8 bloques sin
  pesos de arquetipo desde `c81dcbb`: decisión de autoría) y `test_perf66_catalogue` (tolerancia de 20 ms,
  falla con carga).

## Objetivo — un comando

```bash
python3 tools/depmap.py && python3 tools/checks.py && python3 tools/audit_tests.py
```

Sale 0 sólo cuando el lint ampliado, el trinquete y todos los tests están en verde. **Comprueba
primero** que `tools/audit_tests.py` devuelve un código distinto de 0 cuando un test falla; si no lo
hace, arreglarlo es parte de F1.

## §0 De dónde sale

Sesión del 2026-10-13: el dueño pidió una valoración de `CODESTYLE.md` y aprobó los cambios («Me
gusta, dale»; «habrá que diseñar un encargo para adaptar todo el código»). Lo medido ese día sobre
1.674 ficheros `.py`:

- `checks.py` no ejecuta ningún test: los 331 de `tests/` sólo corren de noche (`audit_tests.py`).
- `ruff check . --select F401,B`: 344 avisos — 235 `B905`, 56 `F401` (con autofix), 25 `B023`,
  13 `B007`, 8 `B034`, 4 `B904`, 3 `B008`.
- 14 `default_rng()` sin semilla y 5 usos de la API antigua `np.random.*`.
- `-> dict` sin tipar: 1.375 funciones (otras 360 ya dicen `dict[K, V]`). Por paquete: `studies` 394,
  `ui` 310, `tests` 209, `portfolio` 152, `core` 75, `mt5` 55, `sqx` 53, `perf` 45, `engines` 31,
  `tools` 21, `pipeline` 16, `ledger` 14.
- 24 `except` amplios, 22 entradas en la lista ALLOW de `tools/layering.py`.
- `vulture` 2.16 está instalado; ni pyright ni mypy lo están.
- Ya existe un hook `PostToolUse`, `.claude/hooks/lint_py.sh`, con cuatro reglas de ruff.

## 1. Los tests corren al entregar (F1)

Ficheros: `tools/checks.py`, `tools/audit_tests.py`, `CODESTYLE.md` §8.

Hoy un agente puede romper un test, ver `checks.py` en verde y entregar. Mide primero cuánto tarda
`python3 tools/audit_tests.py` entero y pega el número; D1 se decide con él. El resultado es un modo
de `checks.py` (o un comando al lado) que corre los tests que tocan a lo cambiado, y `CODESTYLE.md`
§8 lo nombra en su línea de entrega.

## 2. Hooks (F2)

Ficheros: `.claude/hooks/lint_py.sh`, un hook nuevo de cierre, `.claude/settings.json`,
`.claude/hooks/README.md`.

- **Al escribir:** `lint_py.sh` pasa de sus cuatro reglas a las de `ruff.toml` (una sola lista, la
  del fichero; el hook deja de llevar la suya).
- **Al cerrar:** un hook `Stop` que, si la sesión cambió algún `.py`, corre `checks.py` y los tests
  de la parte 1. Dos trampas: el árbol es compartido (regla 12), así que el rojo de otra sesión no
  puede atrapar a ésta —mira sólo los ficheros que esta sesión tocó—; y un `Stop` que bloquea se
  llama a sí mismo: respeta `stop_hook_active` de la entrada del hook.

## 3. Trinquete (F3)

Ficheros: `tools/ratchet.py` (nuevo), su línea base `tools/ratchet.json`, una llamada en
`tools/checks.py`, fila en `tools/README.md`, `CODESTYLE.md` §8.

`checks.py` falla si **sube** alguno de estos recuentos respecto a la línea base, y la reescribe
cuando bajan: `-> dict` sin tipar en funciones públicas, `except` amplios, `default_rng()` sin
semilla, usos de `np.random.*` antiguo, entradas de ALLOW. Es lo que deja migrar por partes: cada
fase de abajo baja un recuento y el trinquete impide que vuelva a subir. `tools/` queda fuera del manual (`checks.py`, `DEVELOPER_ONLY`).

## 4. Ruff ampliado (F4)

Ficheros: `ruff.toml` y los que señale ruff.

1. `ruff check . --select F401 --fix`: los 56 imports sin usar. Cuidado con los `__init__.py` que
   reexportan: ahí el import se queda y se declara en `__all__`.
2. **Los 25 `B023`, uno a uno**: una función definida en un bucle que usa la variable del bucle. Cada
   uno es bug o no lo es; el que lo sea llega con su test (`CODESTYLE.md` §12.3). Devuelve la lista.
3. `B007`, `B034`, `B904`, `B008`: 28 arreglos mecánicos.
4. `B905` (D3, **C**): su recuento entra en el trinquete de la parte 3 y baja fichero a fichero. En
   cada `zip`: si las dos listas miden igual por construcción, `strict=True`; si no está claro, se
   corre el test del módulo con `strict=True` y un fallo se apunta en la lista que vuelve al dueño.
5. Añade a `select` de `ruff.toml` lo que haya quedado limpio.

## 5. Semillas (F5)

Ficheros: los 19 sitios (`grep -rn 'default_rng()' --include='*.py' .` y
`grep -rnE 'np\.random\.(seed|rand|randn|choice|normal|shuffle)\(' --include='*.py' .`).

`CODESTYLE.md` §11: la semilla es argumento de la función que sortea y se guarda con el resultado.
Pasar de la API antigua a `default_rng` **cambia los números** que salen: para cada uno de los 5,
di qué resultado guardado o test dorado depende de él antes de tocarlo.

## 6. `assert` en la puerta de los lectores (F6)

Ficheros: sólo los lectores que ya tienen fichero dorado en `tests/` — `.sqx`, `.cfx` y el retest.

`CODESTYLE.md` §4, «Check at the door, then trust». Opus escribe primero, para cada lector, la lista
de lo que afirma (forma, rango, columnas) y el dueño la ve (D5); Sonnet la escribe. Un `assert`
demasiado estricto para un workflow en marcha: por eso cada uno se prueba contra los ficheros dorados
**y** contra un proyecto real reciente de `AlgoData` antes de darse por bueno.

## 7. Menciones caducas del tope de 250 (F7)

`ui/daemon/filters/discards.py:12`, `ui/daemon/filters/README.md:47` y `portfolio/EXECUTION.md:19`
justifican dónde vive una función porque `core/paths.py` «está en su límite de 250 líneas». El tope
es 500 desde el 2026-10-13. Según D6.

## 8. Comprobador de tipos (F8)

Ficheros: su configuración en la raíz, `requirements.txt`, una llamada en `tools/checks.py`.

Sin él los type hints no los verifica nadie, y la parte 9 no tendría cómo probarse. Empieza por
`core/` y `engines/` en modo básico; el número de errores de cada paquete entra en el trinquete (no
puede subir) y los paquetes se añaden de uno en uno, en el orden de capas de `tools/layering.py`.
`sudo` pide contraseña en esta máquina: se instala con `pip --user`.

## 9. Los `-> dict` sin tipar, todos (F9)

Ficheros: los 1.375 sitios, **un paquete por pieza** — nunca dos piezas sobre el mismo fichero.

Cada función cae en una de tres clases, y sólo la primera pide escribir algo nuevo:

| clase | cómo se reconoce | qué se escribe |
|---|---|---|
| **registro** | claves fijas, escritas en el código (`{"pf": ..., "trades": ...}`) | un `TypedDict` en el módulo que lo produce; la firma lo nombra |
| **mapa** | claves que vienen de los datos (por estrategia, por símbolo) | `dict[str, float]`, `dict[str, Registro]`… |
| **de paso** | devuelve lo que otra función ya tipó | el tipo de esa función |

Un `TypedDict` es un `dict` en ejecución: **la migración sólo toca anotaciones, ningún
comportamiento**, y por eso es viable. Convertir a `@dataclass` cambiaría cada `x["k"]` por `x.k` en
todos los llamadores: eso es D8, no el camino por defecto.

Orden: el de las capas — `core`, `ledger`, `engines`, `sqx`, `perf`, `pipeline`, `mt5`, `portfolio`,
`studies`, `ui`, `tools`; `tests` según D9. Aceptación de cada pieza: el comprobador de tipos limpio
en ese paquete, sus tests en verde, y su recuento del trinquete a 0. Es la fase más larga con
diferencia: `studies` y `ui` solas son la mitad.

## 10. Límites por función (F10)

`C901` (complejidad) y `PLR0913` (número de argumentos) de ruff entran en el trinquete con el
recuento de hoy. No se reescribe ninguna función por esto: sólo no puede haber más.

## 11. Código muerto (F11)

`vulture` sobre el repo, de noche, dentro del `auditor` (`tools/audit_tests.py` es el modelo de cómo
se engancha). Lo que señale se borra según la regla 21: grep de cada llamador antes, y con sus citas
(README, manual, `knowhow/`, `OPEN.md`). Los falsos positivos —lo que llama Qt, FastAPI o un
`python3 -m`— van a una lista blanca con una línea de por qué.

## 12. La tabla del README, generada (F12)

Ficheros: un generador en `tools/`, los 204 `README.md` de carpetas de código, `CODESTYLE.md` §2.

Las columnas «file» y «what it does» salen del docstring de módulo; `checks.py` falla si están
caducas, como ya hace con `docs/DEPENDENCIES.md`. Las otras dos según D10.

## 13. Entorno reproducible (F13)

Un lockfile con las dependencias transitivas junto a `requirements.txt`, y la versión de Python
fijada en un solo sitio que `ruff.toml` y el comprobador de tipos lean. Gorilla instala del mismo.

## 14. Canario nocturno (F14)

Un recorrido mínimo de extremo a extremo, sin SQX, sobre una entrada fija guardada en `tests/fixtures`
y con salida dorada: si cambia, alguien rompió una costura entre módulos que ningún test de módulo
ve. Qué ruta recorre es D11. Se engancha al `auditor`.

## 15. Gorilla comprueba cada push (F15)

`bin/remote.sh gorilla` corre el Objetivo de este encargo tras un push: es la prueba real de
`CODESTYLE.md` §6, «tiene que funcionar en otra máquina». `remote.sh` ya no hace pull bajo un SQX en
marcha; comprueba además que no compite por CPU con un workflow de gorilla (regla 19).

## 16. Agente `reviewer` (F16)

`.claude/agents/reviewer.md`, de sólo lectura, Sonnet: recibe el diff, `CODESTYLE.md` y el objetivo
en una línea, y devuelve hallazgos como `file:line`. `CODESTYLE.md` §12.6 pasa a nombrarlo en vez
del subagente genérico. Con `/cron-agent` no: no es nocturno.

## 17. Convenciones que faltan (F17)

Dos párrafos en `CODESTYLE.md`, cuando el dueño conteste D12 y D13: `print` o `logging`, y en qué
zona horaria vive una marca de tiempo dentro del código.

## 18. `ruff format` (F18)

Lo último, y solo: reformatea unos 1.500 ficheros en un commit que no lleva nada más. El dueño lanza este
encargo con todo comiteado (2026-10-13), así que se hace sin volver a preguntar — pero `git status`
antes: si otra sesión dejó cambios sin comitear en un `.py`, se para y se dice. Después,
`format` entra en `checks.py` para que no se deshaga.

## Decisiones del dueño — pregúntalas (regla 11)

| código | qué se decide | A | B | recomendación |
|---|---|---|---|---|
| D1 | Qué tests corren al entregar | Sólo los que tocan a lo cambiado (`graphify affected`) | Los 331 siempre | A si el total pasa de un par de minutos; se decide con el tiempo medido en F1 |
| D2 | El hook de cierre, en rojo | Bloquea: la sesión no termina | Sólo avisa | A |
| D3 | Los 235 `zip` sin `strict` (`B905`) | No se selecciona la regla | `strict=True` en todos: revienta donde las longitudes difieran, que es un cambio de comportamiento | A; B sólo fichero a fichero, con su test |
| D4 | La semilla como argumento | Obligatoria, sin valor por defecto | Con un valor por defecto fijo | A en lo que guarda resultados; el executor lista los casos dudosos |
| D5 | Qué afirma cada lector | El dueño aprueba la lista antes de escribir | Opus decide y se ve en el diff | A |
| D6 | Las funciones que viven fuera de `core/paths.py` por el tope viejo | Se quedan; sólo se corrige la frase | Vuelven a `core/paths.py` | A |
| D7 | Qué comprobador de tipos | pyright (más rápido, mejor con `TypedDict`) | mypy (Python puro, instalación más simple) | A, si instala sin `sudo`; el executor lo prueba y lo dice |
| D8 | En qué se convierte un registro | `TypedDict`: sólo anotaciones, nada cambia al ejecutar | `@dataclass(frozen=True)`: cambia todos los llamadores | A |
| D9 | Los 209 `-> dict` de `tests/` | Fuera: el trinquete los congela | Dentro, los últimos | A |
| D10 | Columnas «run it» e «in → out» del README | Siguen a mano | Se generan también, de una convención nueva en el docstring | A |
| D11 | Qué ruta recorre el canario | De las operaciones exportadas al veredicto del paso 8 | Otra que nombre el dueño | lo propone Opus en F14 |
| D12 | `print` o `logging` (501 ficheros usan `print`, 1 `logging`) | `print` es la norma y se escribe así | `logging` en lo desatendido (`pipeline/`, agentes nocturnos) | A |
| D13 | Zona horaria de una marca de tiempo en el código | Reloj del feed (EETUS), sin tz, como hoy | UTC con tz y conversión en la frontera | la que el dueño diga; hoy no está escrita en ningún sitio |
| D14 | El día de `ruff format` | Lo fija el dueño con el árbol limpio | — | — |

**Contestadas por el dueño el 2026-10-13 — no se vuelven a preguntar:** D7 **A** (pyright) · D8 **A**
(`TypedDict`) · D9 **A** (`tests/` fuera, congelados por el trinquete) · D10 **A** («run it» e «in → out»
siguen a mano) · D12 **A** (`print` es la norma) · D13 **EETUS** (reloj del feed, sin tz).
D1 **A** (corren los tests que tocan a lo modificado, y los tests modificados) · D2 **A** (el cierre
bloquea) · D4 **A** (semilla obligatoria) · D5 **A** (el dueño aprueba la lista de cada lector) · D6 **B**
(el dueño: «lo que se adapte más a las nuevas guidelines» — con el tope en 500 las rutas vuelven a su
única casa, `core/paths.py`; grep de cada llamador antes, regla 21) · D14 **se hace dentro de este
encargo**: el dueño comitea todo el proyecto antes de lanzarlo, así que el árbol está limpio.
D3 **C** (trinquete: todo `zip` nuevo dice `strict=`, y los 235 viejos se revisan fichero a fichero con
su test; uno que hoy empareje longitudes distintas es un hallazgo para el dueño, no algo que se
arregla callando).
**Sigue abierta:** D11 (la propone Opus en F14).

## Lo que no tocas

- **El comportamiento**: salvo los `B023` que resulten bugs y las semillas, nada de este encargo
  cambia un número. Una fase que mueva un resultado guardado se para y lo dice.
- El master, los workers y `AlgoData` salvo lectura (parte 6).
- Los ficheros que otra sesión tenga cambiados: `git status` antes de cada parte.

## Cómo cierras

Qué hizo cada fase · la tabla de recuentos antes y después, con la salida del Objetivo pegada · la
lista de `B023` que eran bugs · qué quedó sin hacer y por qué · qué descubrió para `knowhow/eng/` ·
la revisión independiente de `CODESTYLE.md` §12.6 sobre el diff entero · los ficheros cambiados y
«¿Quieres hacer el commit?».

```
/loop Lee docs/encargos/68-adaptar-el-codigo-al-codestyle.md y ejecútalo entero. Tras cada iteración
corre el Objetivo; si sale 0, para el bucle; si no, arregla lo que falló y vuelve a correrlo.
```
