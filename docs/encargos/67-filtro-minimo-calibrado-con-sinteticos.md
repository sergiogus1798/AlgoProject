# 67 · Filtro mínimo del Build calibrado con datos sintéticos

**Tu oficio:** diseño experimental y estadística sobre lo que el autopiloto ya escribe; SQX sólo a través
de `bin/workflow.sh`, del builder y del custodio. **Opus** para el diseño, la lectura y el umbral;
**Sonnet** para generar series, lanzar las corridas, esperar y tabular (regla 17).
**Tu encargo:** una decisión por celda (activo × timeframe) — **el umbral mínimo que una estrategia real
debe superar para ser aceptada por el Build** — medido en lo que encuentra por pura suerte una búsqueda de
una hora, sin filtros, sobre una serie sin ventaja. Cada umbral va **con su coste en estrategias** (a
cuántas reales deja fuera, cuánto tarda entonces el Build en llenar las 10.000) y **con el espacio de
búsqueda del que salió** (series, corridas, métrica, paleta). «El umbral no se distingue del ruido entre
corridas: no se pone filtro» es un resultado válido.

Lee `CLAUDE.md` (reglas 5, 6, 10, 13, 14, 15, 19) · `docs/encargos/58-mcpt-fabrica.md` (§0, §1: el
generador) · `docs/encargos/66-performance.md` (D24, N7b) · `docs/encargos/60-estudio-del-build.md`
(cabecera) · `knowhow/sqx-drive/import-csv-as-symbol.md` · `knowhow/research/ga-target-choice.md`
(cabecera) · `ledger/README.md`.

## Estado del plan (lo actualiza cada sesión al cerrar)

| fase | qué | modelo | depende de | estado |
|---|---|---|---|---|
| F0 | decisiones D1 a D8 contestadas; D24 del 66 resuelta (el Build para solo, de forma fiable) | dueño | — | sin empezar |
| F1 | una celda piloto: elegir activo × TF, comprobar `core.assets`, generar la serie sintética e importarla | Sonnet | F0 | sin empezar |
| F2 | la medida: N series × M corridas de una hora sin filtros, y el máximo y el percentil de cada una | Sonnet | F1, custodio libre | sin empezar |
| F3 | la dispersión entre corridas: resuelve A contra B (D1) | Opus | F2 | sin empezar |
| F4 | el umbral de la celda y su coste: filtro puesto en un Build real, estrategias que rechaza, minutos hasta 10.000 | Sonnet corre, Opus juzga | F3, custodio libre | sin empezar |
| F5 | dónde se guarda el umbral y quién lo reescribe; extender a las demás celdas | Opus | F4, el «sí» del dueño | sin empezar |

### Bitácora

- 2026-10-13 — Encargo escrito desde la respuesta N7b del dueño al 66.

## §0 De dónde sale

El encargo 66, decisión **D24**: el Build para solo cuando el databank llega a 10.000. Consecuencia
**N7b**: el paso 8 recibe entonces las **primeras** 10.000 aceptadas, no las mejores 10.000 en muestra
por Ret/DD. Hoy `assets/_build.yaml` (`databank:`) para por tiempo (`time-limit`, 180 min en `Trade_` y
`Research_`, 10 min en `Test_`) y el databank guarda las N mejores: lleno, una nueva entra sólo si mejora
a la peor. Sin ese recambio, el filtro de entrada es el único que protege al paso 8.

Dueño, 2026-10-13, textual:

> «Simplemente podemos hacer un test (o varios) con data sintetica, buildear durante 1 hora sin filtros, ver cuál es el mejor y poner eso como filtro minimo para luego construir hasta que se llenen las 10k, igual que woodrif.»

En claro: en datos sintéticos no hay ventaja que encontrar, así que lo mejor que halla una búsqueda de una
hora sin filtros es lo que produce la suerte de la búsqueda. Esa cifra pasa a ser el **filtro mínimo del
Build real**: una estrategia real debe superar lo que el azar encuentra sobre ruido para ser aceptada;
entonces el Build real corre hasta aceptar 10.000.

Decidido por el dueño, 2026-10-13: es **un encargo propio** (éste) y la calibración es **por activo y
timeframe**, no global.

Lo que ya existe (leído, no construido por este encargo):

- `docs/encargos/58-mcpt-fabrica.md` §0-§1 define el generador: volteo de signo alrededor de la deriva
  anual, por bloques. Conserva volatilidad, rachas, calendario, perfil horario, deriva anual y camino M1;
  los timestamps son idénticos al real y la zona horaria la misma. Destruye la dirección de un bloque al
  siguiente. Generar una serie cuesta 86 s; importarla en el custodio, 28 s.
- Dos series piloto existen en `AlgoData/scratch/synthetic/` (`XAUUSD_SYN01`, `USA500_SYN01`); la ficha
  `assets/symbols/XAUUSD_SYN01.yaml` y su fila en `assets/_policy.yaml` son de otra sesión y están sin
  comitear. **El generador aún no está en el repo** (58, F0: «sin empezar»). Antes de escribir nada,
  `ListAgents` y la tabla de estado del 58: puede estar en marcha.
- Las fichas sintéticas heredan sesión, huso y costes del activo real (`XAUUSD_SYN01`: sesión
  `XAUUSD_ftmo`, mismas ventanas). Eso es lo que el filtro necesita: el mismo coste que el real.

## §1 Medida (F1 a F3)

1. **Celda piloto.** Una sola, la que el dueño elija (D6). `python3 -m core.assets <SYMBOL>`, informa de
   los overrides aplicados y se para si sale distinto de cero (regla 5).
2. **Series.** N series sintéticas del mismo activo (D3), semillas `SeedSequence(root).spawn(N)`, en
   `AlgoData/` (regla 7), importadas en el custodio como en `knowhow/sqx-drive/import-csv-as-symbol.md`
   (`preflight.sh` antes; snapshot de `user/projects`, regla 1; en el master sólo con su GUI cerrado y por
   permiso del dueño del 2026-10-12, regla 2).
3. **Corridas.** Por serie, un proyecto `Test_<ACTIVO>_<TF>_<familia>_SYNkk_leaseWeb` creado por
   `sqx/projects/builder.py` (regla 10), misma configuración que el Build real **sin ningún filtro de
   aceptación** y parada a la hora (60 min). Custodio, **un job cada vez**, `/sqx-wait` (regla 18); nada
   pesado al lado. Un `Test_` se retira al acabar: `python3 -m sqx.projects.retire <P> --role <role> --yes`
   con el worker parado (regla 6).
4. **Lectura.** De cada databank: la métrica elegida (D2) de todas las aceptadas; guarda el máximo, p95,
   p99 y el número de estrategias aceptadas en la hora. El estudio es de lectura (databank → cifras); si
   hace falta un módulo, `/new-study`.
5. **Dispersión.** La variación del máximo y del p95 entre corridas y entre series. Decide A contra B
   (D1): el estadístico cuya dispersión sea menor, para el mismo coste de CPU, es el que sirve de umbral.

## §2 Coste y umbral (F4 y F5)

- Se pone el umbral como filtro de aceptación en un Build **real** de la celda (misma plantilla o
  Simple Strategy, misma dirección, misma paleta, regla 19 y `bin/workflow.sh`) y se mide: cuántas
  estrategias reales rechaza frente a un Build sin filtro; cuántos minutos tarda en llegar a 10.000
  aceptadas; cuántas de esas pasan después el paso 8 comparadas con las primeras 10.000 sin filtro.
- Salida al dueño, una tabla por celda: umbral · estadístico (A o B) · series y corridas de las que salió
  · estrategias reales rechazadas (n y %) · minutos hasta 10.000 · supervivientes del paso 8 con y sin
  filtro. Una ganancia sin su coste al lado no se entrega.
- Un filtro *dentro* del Build cambia lo que el algoritmo genético cría
  (`knowhow/research/is-filters-inside-the-build.md`: 70-98 % menos robustas por minuto que el mismo corte
  aplicado después). Hay que medir esa pérdida, no suponerla; si aparece, se informa y se vuelve a
  decidir D1 con ella delante.

## Decisiones del dueño — pregúntalas (regla 11)

**Contestadas por el dueño (2026-10-14)** — lo que sigue manda sobre la lista de abajo:
- **Aparcado por el dueño.** Recomendaciones aceptadas para cuando se retome: D1 → **p95**; D2 → **la métrica del Build**; D3 → **5 × 1 en la piloto, 3 × 1 en el resto**;
  D4 → **el generador del 58**; D5 → **plantilla y paleta del Build real**; D6 → **activo × TF × dirección × familia**, piloto USATEC H1 ruptura;
  D7 → **`ledger/thresholds.yaml`**; D8 → **convive con la fila 9 del 65** y comparte sus series.


| código | qué se decide | opciones | recomendación |
|---|---|---|---|
| D1 | Qué es «el mejor» de una corrida sintética | **A** la mejor estrategia sola, por la métrica que optimiza el Build · **B** un percentil alto (p. ej. p95) de esa métrica | **B.** El máximo de una corrida es una sola muestra de un extremo y se mueve mucho entre corridas. La primera medida del encargo (varias builds de una hora sobre series distintas del mismo activo × TF) lo zanja: muestra la dispersión de A y de B corrida a corrida. Si A resulta estable, A |
| D2 | Qué métrica | **A** la que el Build optimiza (el `<Ranking type>` del proyecto donante; `sqx/projects/buildcensus.py` lo lee; el valor no está en `_build.yaml`) · **B** Ret/DD en muestra, la que el paso 8 recibía hasta ahora | **A**, nombrándola en el paso 1 del encargo: el filtro y la selección del GA deben hablar el mismo idioma. Si coincide con Ret/DD, no hay diferencia. La decisión de qué métrica optimiza es del encargo 60 |
| D3 | Cuántas series sintéticas y cuántas corridas por celda | **A** 3 series × 1 corrida · **B** 5 series × 1 corrida (como el K = 5 del 58) · **C** 3 series × 2 corridas con semilla distinta | **B** en la celda piloto, para medir la dispersión de D1; si es pequeña, **A** en las demás. Una hora cada una y un job cada vez: 5 h de custodio por celda |
| D4 | Qué generador | **A** el del 58 (volteo de signo; conserva volatilidad, rachas, calendario, perfil horario, costes y sesión; destruye la dirección) · **B** otro (remuestreo por bloques, GARCH…) | **A**, el que ya hay y ya tiene piloto de viabilidad. Un generador nuevo es otro encargo. Depende de que el 58 F0-F1 lo validen |
| D5 | Plantilla y paleta de la corrida sintética | **A** la misma dirección, número de condiciones y paleta que el Build real de esa familia (reglas 13-15) · **B** una genérica, sin template | **A.** Un Build con otra paleta no es el mismo espacio de búsqueda y su techo de suerte no vale para el real. Esto fija que el umbral es por familia además de por activo y TF; hay que decirlo (D6) |
| D6 | Celda piloto y unidad del umbral | Celda: la que prefiera el dueño (la fila 9 del 65 usa USATEC H1 ruptura) · Unidad: **A** activo × TF × dirección × familia (la celda de `ledger/cells.py`) · **B** sólo activo × TF | Celda: **USATEC H1 ruptura**, para compartir la serie con la fila 9 del 65. Unidad: **A**, por D5 |
| D7 | Dónde vive el umbral y quién lo reescribe | **A** `ledger/thresholds.yaml`, una fila por celda con quién, cuándo y por qué, leída como `ledger:<key>`; sólo la reescribe este estudio y con el «sí» del dueño · **B** la ficha del activo en `assets/symbols/` | **A.** `ledger/` es donde viven los umbrales congelados (un umbral movido tras ver resultados es la forma más barata de sobreajustar; sin fecha y autor no se distingue). La ficha del activo guarda costes, no criterios |
| D8 | Relación con la fila 9 del 65 («Build sintético de USATEC H1 ruptura, K = 5») | **A** este encargo la sustituye: una sola serie de corridas sirve a la FDR y al umbral · **B** la fila 9 se queda y apunta aquí: sus series se reutilizan, pero la fila 9 corre el embudo completo hasta el paso 8 y éste sólo la primera hora | **B.** Son medidas distintas (el 65 fila 9 es el MCPT de la fábrica entera y para ello el Build es el real; aquí es una hora sin filtros). Se comparten las series `USATEC_SYN01..05` y se evita generarlas dos veces; la fila 9 gana un puntero a este encargo |

## Lo que no tocas

- El **master** (`SQX`, 5050): ni se construye ni se cambia lo que construye un proyecto (regla 3). Todo
  en `Test_`/`Research_` sobre un worker.
- El custodio recibe **un trabajo largo cada vez**; entre `start` y la cosecha sólo `-project action=status`
  (regla 3). Nada de CPU pesada junto a una corrida.
- Los datos sintéticos viven en `AlgoData/`, nunca en el repo (regla 7).
- `oos2`, `criteria.yaml` y los umbrales del paso 8: no se editan para salir de un atasco (regla 19).
- Los ficheros de otras sesiones sin comitear: `assets/symbols/XAUUSD_SYN01.yaml`, `assets/_policy.yaml`,
  `assets/INDEX.md`. Las fichas de las series nuevas las escribe `core.assetwrite`.
- **Depende de D24 (66).** Su Build que para solo aún no es fiable: la sesión 1 vio `databank-full` parar
  a los 50 (105,6 s CLI / 110 s GUI); la sesión 2 lo vio repetirse (63+ «Build finished because databank
  is full», sin «Task finished») hasta cerrar la sesión. Sin D24 resuelta, F4 y F5 no empiezan; F1 a F3
  (la hora sin filtros) paran por tiempo y no la necesitan.

## Objetivo — un comando

Es un encargo de diseño y medida: su fin no cabe en un comando que salga 0. Se queda con **Verificación**:
(1) la tabla de dispersión de F3 con A y B por serie; (2) la tabla de coste de F4 por celda, con las
cuatro cifras de §2; (3) una fila en `ledger/thresholds.yaml` por celda decidida, con `set_by`, fecha y
`why`; (4) `python3 tools/depmap.py && python3 tools/checks.py` sale 0 si se tocó código.

## Cómo cierras

Qué hizo · qué verificó, con las tablas pegadas · qué dejó sin hacer y por qué (una fase bloqueada por D24
o por una pregunta de arriba se queda en la tabla de estado con «bloqueado por …») · qué descubrió para
`knowhow/` (el valor del máximo sobre ruido por celda es un hecho nuevo: tarjeta 🔬) — los ficheros
cambiados y, como última línea, **¿Quieres hacer el commit?**
