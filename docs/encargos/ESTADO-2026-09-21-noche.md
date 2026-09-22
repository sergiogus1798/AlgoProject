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
