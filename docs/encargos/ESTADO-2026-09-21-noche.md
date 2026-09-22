# Estado al parar — 2026-09-21, 22:05

Sesión de verificación de los cuatro encargos. **Parada por límite de créditos del dueño**, con
reanudación autónoma programada. Esto es lo que hay que saber para continuar sin releerlo todo.

## Hecho y verificado (no rehacer)

- **Encargos 1, 2, 3 y 4**: todos pasan su propia verificación. Detalle en el transcript; lo que
  importa está ya en `knowhow/`.
- **Arreglos cerrados esta sesión**: 3 (presupuesto de disco), 5 (forma `minimal`), 7 (archivador
  de logs cubre todos los roles), 8 (`check` exime las dos `.version` reestampadas y vuelve a
  salir 0).
- **Punto 4 (encaje pipeline↔variantes): hecho, falta cerrar la verificación.**
  `sqx.variants.make` acepta `--out` y escribe `design.json` y `build.json`; `recipe.yaml` apunta
  `design` y `build` al comando real. Corrida real completa: 5.000 `.sqx`, 70,0 MB, 17 s, 0
  desajustes, y `pipeline.cleanup --apply` liberó los 70 MB dejando el libro mayor de 520 KB.

## Lo único pendiente de la tanda de arreglos

`python3 -m pipeline.verify.selftest` — **estaba corriendo cuando paré y no vi el resultado.**
Cambié `pipeline/verify/fixture.py` para que el arnés siga usando `stubs/placeholder.py` en vez de
los comandos reales (si no, exige un export de SQX real), y añadí `n`/`shortfall` a `SHAPE["design"]`
en `pipeline/stubs/placeholder.py` porque la fila `design` los pide en `record`.

**FALLA. Medido justo antes de parar, no es una sospecha:**

```
verdict: exited 2
exit=124        <- y ademas se comio el timeout de 280 s
```

Dos sintomas, quiza una sola causa: la etapa `verdict` sale 2 sobre el fixture, y el arnes tarda
muchisimo mas de lo que deberia tardar con stubs (el conjunto entero eran ~2 s antes de mis
cambios). Sospecha principal: el `BRIEF` de `pipeline/verify/fixture.py` es un dict minimo
(`parameters: []`, sin `source`) y `pipeline/stages/verdict.py` lee de el campos que ya no
encuentra, o `design.json` cambio de forma al escribirlo ahora `make.py` en vez del stub.

**Primer paso al volver, y es lo unico que bloquea la tanda:** reproducir
`python3 -m pipeline.verify.selftest`, leer por que `verdict` sale 2, y arreglarlo. Luego
`python3 tools/depmap.py && python3 tools/checks.py`.

Lo que si pasa verde ahora mismo: `tools/checks.py` (0 problems), `tests/test_variants.py`,
`tests/test_surface.py`, y la corrida real de `pipeline.run` de punta a punta.

## Decisiones del dueño ya tomadas

- Punto 6: `Bash(*)`/`Edit(*)`/`Write(*)` en `.claude/settings.json` **son suyos y a propósito** —
  quiere que los agentes trabajen con más autonomía. No es un hallazgo, no revertir.
- Punto 9: los costes de XAUUSD **se quedan provisionales**. No tocar `assets/`.
- Los datos gordos van a `AlgoData/`, siempre. El presupuesto se mueve, los datos no.

## Lo grande que sigue abierto

1. 🔴 **Los `SQStats` heredados.** Una variante recién fabricada exporta las métricas del padre —
   las tres formas de fichero conservan `settings.xml`. 5.000 variantes leídas hoy darían 5.000
   copias de una fila y parecerían correctas. Escrito en `knowhow/01-file-formats.md`.
2. 🔴 **La medición que lo resuelve, y que nadie ha hecho:** un retest real sobre 3 variantes, en el
   custodio. `Retester` en W2 es un arnés de **1 tarea Retest, sin Build ni `GoToTask`** — seguro.
   Hay que recablear su `Setup` al feed del donante (`AlgoData/donors/XAUUSD_base_2026-09-21/`).
   El dueño ofreció el proyecto XAUUSD del maestro como base y autorizó copiarlo o clonarlo.
   **Regla dura 3 sigue en pie: no arrancar builds. El donante tiene 17 tareas y un bucle.**
3. 🟠 Pre-registro del holdout sin firmar (`docs/preregistro/`) — decisión del dueño, no de un agente.

## Reglas que mordieron esta sesión

- `-databank action=count` hace un sync-from-files y **destruye** lo que `action=load` acaba de
  cargar. Verificar cargas con `action=export`. (En `knowhow/01-file-formats.md`.)
- Los verbos de databank usan `name=`, no `databank=`.

---

# Sesión nocturna autónoma — 2026-09-22, 06:30 a 07:05

## 1 · El `selftest` que quedó rojo: arreglado

Era mío. `fixture.chain()` sustituía **todas** las etapas por `stubs/placeholder.py`, incluida
`verdict`, y el placeholder no conoce ese nombre → `argparse` salía 2 y el arnés se colgaba después.
Ahora solo sustituye las etapas cuyo nombre está en `placeholder.SHAPE`; `verdict` es módulo de esta
misma carpeta, lee solo el libro mayor, y corre de verdad contra el fixture, que es lo correcto.

```
0 problemas
EXIT=0
```

**Todo verde:** `tools/checks.py` 247 ficheros 0 problemas · `tests/test_variants.py` ok ·
`tests/test_surface.py` ok · `pipeline.verify.selftest` 0 problemas. Maestro intacto (7.546 `.sqx`),
W1 intacto (66), W2 sin `.sqx` propios.

## 2 · El retest: NO resuelto, pero el bloqueo ya no es donde parecía

Monté el arnés en el custodio: `Retester` de W2 recableado a XAUUSD M30 con el `Setup`, el `Chart` y
el `OutOfSample` del donante congelado, sin cross-checks y con las 30 condiciones de aceptación
desactivadas para que no filtre nada.

**La tarea arranca y no testea nada, en silencio.** `Total tested 0`, `In databank 3`, `0 ms`, sin
error y sin `Project finished`.

**El control es lo que salva la noche:** cargué el **padre íntegro** (126 KB, el `.sqx` original del
export) él solo, y tampoco se retestea. `Total tested 0` igual.

> Es decir: **el problema no es la forma del fichero que fabrica `sqx/variants/`.** Es el arnés o la
> ejecución de tareas en `sqcli` headless. La forma mínima de 70 MB se queda.

Descartado además: las barras M30 de XAUUSD están (symlink a `History` del maestro), el símbolo
resuelve, y no hay ni un error en el log de la corrida.

**Siguiente paso, y es barato:** el `Retest-Task1` del XAUUSD del maestro **sí** ha producido
databanks alguna vez. Diffear su XML contra el recableado, elemento a elemento, es el camino más
corto. *(Diffear el fichero. No arrancar el proyecto del maestro.)*

## 3 · Las filas stub: NO tocadas, a propósito

`ran`, `collected` y `wfc` siguen en placeholder. `ran` **es** la ejecución del retest: sin retest
funcionando no hay nada que construir ahí, y construirlo a ciegas sería inventarse el contrato. Todo
lo de aguas abajo (C3, C4, el WFC, el veredicto real) cuelga de esa misma medición.

## 4 · Tres hechos nuevos, ya en `knowhow/01-file-formats.md`

- 🔬 **SQX renombra en colisión añadiendo `(N)`.** Cargar la misma carpeta dos veces dio `P00000…`
  y `P00000(1)…`. Es el modo de fallo 1 del encargo 4 visto en vivo, y justifica que el `variant_id`
  vaya también **dentro** del fichero.
- 🔬 **Un cross-check desactivado sigue resolviendo su símbolo**, y si no existe mata la tarea sin
  hacerla fallar. Me costó dos intentos: `Symbol 'EURUSD_M1_dukas' doesn't exist`.
- 🔬 **`loadconfig` se lleva solo la tarea, no el proyecto**, y SQX lo funde en `project.cfx` al
  salir. La regla dura 4 por el otro lado: la reescritura al salir no es solo un peligro, es también
  cómo un `loadconfig` se vuelve permanente.

## 5 · Estado del repositorio

Cuatro commits agrupados por tema, **en local**:

```
6502b1c docs: what the four commissions found, and what is still open
13b1c4f fix(logs,disk): archive every install, and budget what the data root now holds
692528e feat(portability): installs by role, and no absolute path left in bin/
0ff06f3 feat(pipeline,variants): the variant factory and the stage chainer
```

⚠️ **El push falló**: `could not read Username for 'https://github.com'`. La sesión no es
interactiva y no hay credenciales. **Hay que hacer `git push origin data/bar-library` a mano.**

⚠️ **`.claude/settings.json` lo dejé sin commitear a propósito.** Es tu cambio de permisos y es
deliberado; no me pareció que me tocara a mí meterlo en la historia del repo. Commitéalo tú si
quieres que viaje.

## 6 · Lo que toqué fuera del repo

- `SQX_w2/user/projects/Retester/project.cfx` — recableado a XAUUSD M30. Copia del original en
  `AlgoData/snapshots/2026-09-21/w2-retester-before/project.cfx` (md5 `593ea6ac…`).
- Databank `RetestOut` creado en `Retester` de W2.
- El maestro **no se tocó**. Ningún build arrancado. Los dos workers parados al terminar.
