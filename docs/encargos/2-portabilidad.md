# ENCARGO 2 — Portabilidad y roles de instalación

**Tu oficio:** Python. **Tu encargo es un refactor pequeño y de alto apalancamiento**: hoy el
proyecto solo sabe hablar con *un* worker de SQX, y hacen falta dos con papeles distintos. Además
arreglas tres rutas escritas a fuego que `checks.py` nunca ha podido ver.

No necesitas leer el plan grande. Lee `CODESTYLE.md` y el `README.md` de `core/`.

---

## 0 · Por qué esto importa

La topología decidida el 2026-09-21 es de **tres instalaciones por PC**, no dos:

| | install | puerto | papel |
|---|---|---|---|
| **M** | `~/Desktop/SQX` | 5050 | el maestro del dueño. **Solo lectura** |
| **W1** | `~/Desktop/SQX_w1` | **5060** | **conductor**: trabajos cortos, siempre vivo |
| **W2** | `~/Desktop/SQX_w2` | **5070** | **custodio**: un trabajo largo cada vez |

Hoy `core/paths.py` expone un único `WORKER` y un único `WORKER_PORT`. Mientras siga así, **el
custodio no se puede pilotar desde Python** y el lote que ejecuta las 5.000 variantes está
bloqueado. Eso es lo que desbloqueas.

Razonamiento completo en `knowhow/03-driving-sqx.md`, sección *The three-install topology*. No
necesitas estar de acuerdo con él, solo implementarlo.

---

## 1 · El radio de impacto, ya verificado

Son **tres ficheros consumidores**. No hay más; no hace falta que los busques:

| fichero | qué usa |
|---|---|
| `core/worker.py` | `WORKER_PORT`, `WORKER_SH` |
| `core/exportdrv.py` | `WORKER`, `WORKER_SH`, `STAGING`, `VIEWS_REL` |
| `sqx/export/archive_logs.py` | `WORKER` (junto a `MASTER`) |

**La compatibilidad hacia atrás es requisito, no cortesía.** Los tres tienen que seguir funcionando
**sin editarlos**. Si tu diseño obliga a tocarlos, el diseño está mal.

---

## 2 · Los seis cambios

### 2.1 · `config/machine.yaml` y `config/machine.example.yaml`

Añade los workers como un mapa de **rol → ruta y puerto**. Conserva `sqx_worker` y `worker_port`
tal cual: son el conductor, y son lo que hace que lo viejo siga funcionando.

Documenta en el ejemplo que `custodian` es **opcional** — una máquina con dos installs es una
configuración válida (ver `docs/SETUP-NEW-MACHINE.md`), y ese es el caso del PC pequeño.

### 2.2 · `core/paths.py`

- `WORKERS`: mapa de rol → ruta y puerto, leído de `machine.yaml`.
- `WORKER`, `WORKER_PORT` y `STAGING` **siguen existiendo**, como el conductor.
- Un acceso por rol para la ruta y para el área de *staging*, en el estilo de las funciones que ya
  hay ahí (`project_dir`, `databank_dir`, `view_file` — todas toman `install: Path = MASTER`).

⚠️ `core/paths.py` es **el único módulo del proyecto autorizado a saber dónde vive nada**. No
repartas ese conocimiento.

### 2.3 · `core/worker.py`

`call`, `start`, `stop` y `wait_ready` pasan a aceptar el rol, **con el conductor por defecto**, para
que ninguna llamada existente cambie.

`require_posix()` se queda como está.

### 2.4 · `bin/sqx-worker.sh` y `bin/clone-sqx-worker.sh`

Hoy llevan esto escrito a fuego arriba del todo:

```bash
MASTER="/home/sergioguslw/Desktop/SQX"
WORKER="/home/sergioguslw/Desktop/SQX_w1"
```

En otra máquina operan sobre rutas que no existen — o peor, sobre el install equivocado.

**La forma limpia: que el shell le pregunte a Python.** Un `python3 -c "from core.paths import …"`
que emita las rutas y el puerto del rol pedido. Así `paths.py` sigue siendo el único que sabe dónde
vive nada, y **no hay que parsear YAML en bash**.

`sqx-worker.sh` tiene que poder arrancar, parar y consultar **cualquiera de los dos workers por
rol**, conservando su comportamiento actual cuando no se le pasa ninguno.

⚠️ **No cambies la lógica de sincronización de barras.** Está bien pensada y la razón está escrita en
el propio script: se sincroniza **al arrancar**, porque en ese instante el worker está parado por
definición, así que la copia siempre es segura y siempre está al día. Y compara los ficheros
`.version`, **no** los `.db`: H2 reescribe la cabecera de una base cada vez que la abre, así que los
bytes divergen en la primera ejecución aunque las barras sean idénticas.

⚠️ Cada install necesita **su propia copia** de los tres ficheros H2 (bloqueo exclusivo); `History/`
va por symlink y se comparte.

### 2.5 · `tools/checks.py`

`hardcoded_paths()` recibe hoy la lista de `depmap.py_files()`, que **solo devuelve `.py`**. Por eso
las rutas de los `.sh` llevan ahí desde siempre sin que nadie las viera.

Haz que inspeccione también `bin/*.sh`. Mismo criterio, mismo formato de mensaje.

### 2.6 · `docs/SETUP-NEW-MACHINE.md`

Su §2 dice hoy *«Two is the working minimum, and it is what the code assumes today»*, y ya es falso.
Reescríbela con los tres papeles, sus heaps, sus `coreUsage` y sus puertos — están en
`knowhow/03-driving-sqx.md`.

Actualiza también §4 (el clonado, que ahora es parametrizable) y la §9 (qué devolver).

**Deja la §7 (Windows) como está.** Sigue siendo verdad.

---

## 3 · Lo que NO es tuyo

- **Portar `sqx-worker.sh` entero a Python.** Los dos PCs del dueño son Linux. El fichero se queda
  en bash; solo deja de llevar rutas a fuego.
- **Crear el install `SQX_w2`.** Eso lo hace un agente de sistema con la GUI del maestro cerrada.
  Tu código tiene que funcionar **igual de bien si el custodio todavía no existe**.
- **Tocar `sqx/variants/` o `pipeline/`.** Hay dos agentes trabajando ahí ahora mismo.

---

## 4 · Verificación

```bash
python3 tools/depmap.py && python3 tools/checks.py    # 0 problems, con los .sh ya incluidos
grep -c "Desktop/SQX" bin/*.sh                        # 0
python3 -c "from core.paths import MASTER, WORKER, WORKER_PORT, DATA; print(MASTER, WORKER, WORKER_PORT, DATA)"
python3 tests/test_surface.py                         # sigue verde
```

Y la prueba que de verdad importa, porque es el requisito del §1:

> **Los tres consumidores importan y funcionan sin haber sido editados.** Demuéstralo: impórtalos y
> ejecuta lo que se pueda ejecutar sin SQX levantado.

Prueba también, aunque sea a mano, que `checks.py` **detecta** una ruta absoluta metida a propósito
en un `.sh` — si no la pilla, el cambio 2.5 no sirve de nada.

Si tienes el worker disponible: `bin/sqx-worker.sh start` → `curl` a 5060 → `stop`. Si no, dilo y no
lo inventes.

---

## 5 · Cómo cierras

No hay `__main__` nuevo, así que **no hace falta página de manual**. Sí hace falta lo demás:

1. **Qué cambiaste**, fichero a fichero, y por qué esa forma y no otra.
2. **La salida de la §4 pegada**, no un resumen.
3. **Confirmación explícita** de que los tres consumidores no se tocaron.
4. **Qué dejaste sin hacer.**
5. Si descubres algo no obvio sobre cómo se conduce SQX o sobre portabilidad, a
   `knowhow/03-driving-sqx.md` o `knowhow/07-practices.md` **en esta misma tarea**, con su etiqueta
   🔬 / 📓 / 🤔.

**Compartido con otros agentes:** `docs/DEPENDENCIES.md` se **regenera**, no se fusiona — si hay
conflicto, `python3 tools/depmap.py` y se queda lo que salga. `requirements.txt`: añadir línea,
nunca reordenar.
