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

---

# El workflow completo, funcionando — 2026-09-22, 09:30

**Tu frase, ejecutada en un comando:**

```bash
python3 -m pipeline.run --project XAUUSD --databank SPP_IS --strategy "Strategy 17.9.39"
```

Coge la estrategia del XAUUSD del maestro, la reconoce con el SPP IS, saca el grid, fabrica 2.000
permutaciones repartidas por todo el diseño, **las retestea de verdad en IS y OOS** en el custodio,
une el panel al manifiesto y dibuja el walk forward correlation. Arranca el custodio y lo vuelve a
parar. El maestro no se toca. **2 min 16 s, 28 MB, exit 0.**

## Lo que estaba roto y por qué no daba error

Dos comportamientos de SQX, los dos silenciosos, y entre los dos consumieron dos días:

1. **`-project action=startOnlyTask` dice que arranca y no testea NADA.** Ni error, ni log, ni
   `Project finished`. `action=start` sobre el mismo proyecto, el mismo databank y el mismo instante
   sí ejecuta. *(Solo es seguro en un proyecto de una tarea. En uno con Build y GoToTask arranca
   generación perpetua.)*
2. **Una tarea Retest sin `<Databanks retestSelected="false">` retestea la selección, la selección
   está vacía, y reporta 0.** Un arnés hecho a mano no lleva ese atributo; una tarea que ha corrido
   de verdad sí. **Los arneses se hacen copiando una tarea que funciona, no editando una que no.**

Lo encontré diffeando estructuralmente la tarea del donante contra la mía.

## La pregunta que bloqueaba el estudio: RESUELTA

**Sí, un retest reescribe los `SQStats` heredados.** Antes del retest las tres variantes exportaban
la fila del padre al decimal; después:

| variante | `DICrossPeriod1` | neto IS | ops IS | neto OOS | ops OOS |
|---|---|---|---|---|---|
| `P00000` (origen) | 67 | **+26.138,78** | 755 | **+14.622,08** | 423 |
| `P00001` | 43 | **+43.647,37** | 1.077 | **−6.988,39** | 588 |
| `P00002` | 94 | **−33.472,63** | 843 | **−12.962,25** | 497 |

Y **una sola corrida da las dos muestras**. Un WFC necesita una corrida, no dos.

## El primer resultado de verdad

`Strategy 17.9.39`, XAUUSD M30, IS 2008–2017 / OOS 2018–2022, 2.000 tuplas retesteadas:

> **rho 0,19 · intervalo 95 % [0,13, 0,25] · `no_fiable`**

El intervalo **no toca el cero** (la relación existe) y está **entero por debajo de 0,30** (es
demasiado débil para ordenar nada). Elegir parámetros por su beneficio dentro de muestra, en esta
estrategia, no compra prácticamente nada fuera.

Y el dato metodológico que más me importa: **rho apenas se movió al multiplicar por 180 los puntos**
(0,18 con 11 → 0,19 con 2.000). Lo que cambió fue la anchura del intervalo. Con once puntos el
número ya era el correcto y no servía para nada. **Informa el intervalo, no el coeficiente.**

La mitad de cualquier lote sale inutilizable por operar poco: pide el doble de puntos de los que
quieres.

## Tres bugs que destapó la primera corrida real

- **El manifiesto leía el nombre equivocado.** SQX nombra la entrada del databank por el **fichero**
  (`P00000.sqx` → `P00000`), no por `<StrategyName>` ni por `ResultName`, que decían
  `Strategy 17.9.39 P00000`. Todos los joins salían vacíos, en silencio.
- **La fábrica no vaciaba su carpeta.** Un lote más pequeño adoptaba los ficheros del anterior y el
  manifiesto describía los dos.
- **`--limit` coge la cabeza del plan**, que son todo controles y un racimo denso. El nuevo
  `--sample` reparte las picadas, que es lo que necesita un lote pequeño.

## Cómo sé que no se va a romper en silencio otra vez

- `collect.py` cuenta cuántos resultados distintos devolvieron los controles y **aborta si todos
  coinciden** — que es exactamente cómo se ve un lote que nunca corrió.
- `pipeline.verify.selftest` tiene una tercera prueba: **cada campo que una fila graba en el libro
  mayor tiene que ser uno que su stub sepa escribir.** Verificado metiendo un campo inventado: lo
  caza y lo nombra.
- `checks.py` 252 ficheros, 0 problemas. `test_variants`, `test_surface` y `selftest` en verde.

## Estado

Maestro intacto (7.546 `.sqx`), W1 intacto (66), ningún proceso SQX vivo, `AlgoData` 7,27 GB de 90.

El informe está en
`~/Desktop/AlgoData/pipeline/XAUUSD/Strategy_17-9-39/wfc.html` — **ábrelo, es el gráfico**. 1.000
puntos, el origen marcado en cuadrado rojo, las dos rayas del cero, y debajo la tabla con los doce
mejores y los doce peores.

Documentado en `docs/manual/19-wfc.md`. Cinco commits en local; **el push sigue pendiente de tus
credenciales** (`git push origin data/bar-library`). `.claude/settings.json` sigue sin commitear a
propósito: es tu cambio de permisos.

## Lo siguiente, cuando quieras

Una estrategia no distingue "los parámetros de esta no significan nada" de "la generación de XAUUSD
produce estrategias cuyos parámetros no significan nada". La cadena ya corre desatendida, así que la
respuesta es lanzarla sobre el databank entero — quitando `--strategy` corre todas. Con ~100 madres
son unas cuatro horas y 2,8 GB.
