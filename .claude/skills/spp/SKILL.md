---
name: spp
description: Configure and run the two SPP tasks of a custom SQX project — the System Parameter Permutation grid over the in-sample and the out-of-sample window, at the owner's spread and steps, with every acceptance silenced so the profile is a map and not a filter. Use when the owner asks to set up, configure or run the SPP in SQX, the permutation profile, or step 15 of the workflow.
---

# /spp

Paso 15 del workflow, la mitad de SQX. Deja las tareas `SPP IS` y `SPP OOS` de un custom project
configuradas, y opcionalmente las corre en el custodio. Leer lo que producen es
`strategies/sppUltra/` (paso 16), que sale de ahí con el `design_brief.json` de las variantes.

## Lo único que hay que entender antes

**El SPP es `OptProfileSysParamPermutation`.** `SequentialOptimization` vive al lado, en el mismo
bloque `<CrossChecks>`, habla también de permutar parámetros y **no escribe perfil ninguno**.
Encender el equivocado costó 47 núcleos durante 91 minutos y no produjo nada (2026-09-22). El
comando enciende el correcto; no hay flag para equivocarse.

**Las dos tareas no se comparan entre sí.** Medido 2026-09-19: el SPP de IS y el de OOS de la misma
estrategia con ajustes idénticos comparten **6 tuplas de ~11.600**. SQX no recorre la misma rejilla
dos veces. Son dos lecturas del mismo entorno, y ésa es la razón de que exista la fábrica de
variantes del paso 16.5 — para comparar hay que fabricar las tuplas uno mismo.

**La aceptación va apagada, las dos.** Las condiciones de la tarea (19 en un clon del donante) y los
cuatro `Eval*Check` del propio crosscheck. Con ellos vivos SQX borra las estrategias cuyo mapa no le
gusta y `sppUltra` lee la superficie de una población ya seleccionada sin enterarse.

## Correrlo

```bash
python3 -m core.assets <SIMBOLO>                       # preflight, BLOQUEANTE
python3 -m sqx.projects.spp <SIMBOLO> \
    --cfx <install>/user/projects/<PROYECTO>/project.cfx --input <databank>
```

`--input` es la población que se permuta y no tiene default: normalmente los supervivientes del MC
Retest (paso 13-14). Preguntar al dueño si no está claro. La segunda tarea lee lo que escribió la
primera, y con la aceptación apagada eso es la población entera.

Antes de escribir: **el `.cfx` no puede estar abierto por una instancia** — SQX lo reescribe al
salir (regla dura 4). El comando se niega y dice qué parar.

Correrlo después, en el custodio y una sola cosa a la vez:

`<PROYECTO>` es el del workflow (`/template-run --workflow`): el comando de arriba deja su paso
como **el único activo**, porque `action=start` corre todas las tareas activas. El `stop` antes del
`start` no sobra: en un proyecto que ya corrió, un segundo `start` sin él no hace nada, en silencio.

```bash
bin/sqx-worker.sh --role custodian start
python3 -c "from core import worker; worker.call('-project action=stop name=<PROYECTO>','custodian')"
python3 -c "from core import worker; worker.call('-project action=start name=<PROYECTO>','custodian')"
# mientras corre, sólo -project action=status; el final es `Project finished` en el log de SQX
bin/sqx-worker.sh --role custodian stop
```

⚠️ Antes de tocar W2: `ListAgents`, `ls -lt <install>/user/projects` y el log. El `stop` mata lo de
cualquier sesión.

## Qué mirar en la salida

- **`tope 15,000 permutaciones`** — la línea que más importa. El donante trae `1000000001`, el
  centinela de SQX para **exhaustivo**; eso no es una tarea larga, es una tarea sin final. Se
  escribe siempre, nunca se hereda.
- **`±35 % en 18 pasos`** — ~4 % por paso, el default del dueño. Los 12 pasos sobre ±30 del donante
  son gruesos.
- **`19 condicion(es) y 2 chequeo(s) del SPP apagados`** — si sale `0` en las dos tareas, conviene
  comprobar el clon.
- Un **`⊘`** significa que el proyecto no lleva esa tarea; un **`⚠️ esta tarea corre ademas: …`**,
  que ese `.cfx` no pasó por la doctrina y correría otros crosschecks a la vez.

## Lo que cuesta, y por qué el silencio no es un cuelgue

Medido 2026-09-22 en el custodio, una madre real de XAUUSD con 22 parámetros: **media hora larga**,
y el log escribe una línea por parámetro en los tres primeros segundos y **nada más** hasta el
final. `-project action=status` dice `Total tested 0` todo el rato. La señal honesta de que trabaja
es la memoria de la JVM subiendo (23,6 → 36,9 GB). RSS plana y sin log es un cuelgue; RSS subiendo
es trabajo.

⚠️ **Una SPP a la vez por instalación.** El perfil son decenas de GB mientras se construye sobre un
heap de 48.

## Dónde se cambia qué

| qué | dónde |
|---|---|
| tope de permutaciones, ±%, finura del paso | `assets/_build.yaml`, bloque `spp:` |
| qué ventana corre cada tarea y a qué precisión | el mismo bloque, `tasks:` |
| los títulos `SPP IS` / `SPP OOS` | **contrato** con el donante y con `export_spp`. Cambiarlos deja la tarea sin encontrar |

⚠️ Dos divergencias declaradas, anotadas en `OPEN.md` §38 y pendientes del dueño: la precisión es
`1` y no el `2` de la doctrina (a 1 minuto no termina), y `SPP IS` corre sobre `build`, que es lo
que significa "in sample" y lo que hacen las tareas del maestro.

Manual: `docs/manual/33-spp.md`. Exportar el perfil: `docs/manual/08-spp.md`. Leerlo:
`docs/manual/15-sppultra.md`.
