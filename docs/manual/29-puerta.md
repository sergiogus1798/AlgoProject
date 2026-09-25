# 29. La puerta OOS — de un databank entero a una lista de supervivientes

## Qué pregunta responde

Has construido un montón de estrategias en un periodo y las has reteseado en el siguiente. Como SQX
solo admite **un spread y un slippage por backtest**, y estas ventanas son de años sobre un activo
que cambia mucho de precio, eso son dos tareas distintas y por tanto **dos databanks**: el de
construcción y el de retesteo. Ahora tienes esos dos y no sabes qué estrategias merecen tu tiempo. La puerta las pasa por
una **cascada de cribas**: primero las baratas, que tumban mucho; al final las caras, que solo ven a
las que llegan vivas. Sale una lista de supervivientes, y para cada muerta, **en qué criba murió y
con qué número**.

La puerta los **junta por estrategia** —por su identidad, no por su nombre— y los juzga juntos.

No es un filtro de métricas. Un filtro de métricas ya lo hace SQX con sus condiciones de aceptación.
Esto añade lo que SQX no mira: cuánto se degradó respecto al periodo de construcción, si bate a un
mono que operase el mismo mercado, y si tus 200 supervivientes son en realidad 30 repetidas.

## Cuándo lo usas, y cuándo no

**Lo usas** cuando un proyecto propio ha terminado su tarea de build y su retest OOS, y quieres saber
qué queda antes de gastar días de máquina en el protocolo de robustez.

**No lo uses para juzgar al generador.** Si la tarea de build llevaba condiciones de aceptación sobre
el periodo OOS, esa población ya fue filtrada por la muestra que la puerta va a juzgar, y las cribas
salen casi inertes. Se ve en el ejemplo de abajo: en `XAUUSD/OOS` sobreviven 228 de 231, y no porque
sean buenas, sino porque solo entraron las que ya habían pasado ese corte. Para leer el resultado
como un juicio hace falta un databank cuyo OOS **no** fuese condición de aceptación.

**No decide nada por ti.** Escribe el veredicto; borrar es otro comando (página 27).

## Antes de empezar

- **Los dos databanks** tienen que existir en el mismo proyecto, con sus `.sqx` en disco.
- La cosecha arranca y para el **conductor** (worker de 5060), una vez por lado. No corras otra cosa
  en él a la vez.
- Si el proyecto vive en un worker en vez de en el maestro, pásale `--role custodian`.
- Las barras M1 del feed tienen que estar en la librería (`python3 -m sqx.export.sync_bars --check`).

### Cómo se emparejan las dos mitades

Por la **identidad** de la estrategia: el SHA-256 de su definición interna, que no cambia al
reetestearla en otra ventana con otros costes (comprobado: 5 de 5 en un par real). **No por el
nombre**, y esto no es teórico: `Strategy 17.8.29` existe en dos databanks de este mismo proyecto y
son estrategias completamente distintas, de plantillas distintas.

De ahí salen tres grupos, y los tres importan:

| grupo | qué es | qué hace la puerta |
|---|---|---|
| emparejadas | están en los dos databanks | las juzga |
| **sin OOS** | están en el de build y **no** en el de retesteo | **las descarta** (criba `presencia`) |
| solo en OOS | están en el de retesteo y no en el de build | las ignora y las cuenta en el manifest |

El grupo del medio es el importante: si SQX tiró una estrategia del retesteo porque saltó una de sus
banderas rojas —demasiados trades ambiguos, o cualquier otra— esa decisión ya está tomada, y la
estrategia se va. Y como el emparejamiento ocurre **antes** de exportar nada, no se gasta ni un
segundo de máquina en ellas.

## Cómo se ejecuta

Son **dos comandos**: uno saca los datos de SQX una sola vez, el otro juzga y se puede repetir
tantas veces como quieras sin volver a tocar SQX.

```bash
python3 -m gate.harvest --project XAU_ISOOS_ejemplo --databank Results --oos-databank OOS --role custodian
python3 -m gate.report  --project XAU_ISOOS_ejemplo --databank Results --feed XAUUSD_DukasM1_Infinox
```

`--databank` es siempre **el de construcción**, en los dos comandos: es el que da nombre a la carpeta
de la cosecha, y el que define la población que entra.

### `gate.harvest` — la cosecha

| flag | obligatorio | qué hace |
|---|---|---|
| `--project` | sí | proyecto tal y como aparece en SQX |
| `--databank` | sí | el databank **de construcción** (IS), con sus espacios |
| `--oos-databank` | sí | el databank **de retesteo** (OOS) |
| `--role` | no | `conductor` o `custodian` si el proyecto vive en un worker; sin él, el maestro |
| `--view` | no | vista del databank con la que exportar; por defecto `Export Data View` |
| `--limit` | no | una muestra aleatoria de N **parejas**, para una prueba |

**Toca SQX**: copia los `.sqx`, arranca el conductor, exporta y lo para — **una vez por lado**. Unas
230 estrategias por lado tardan unos 5 minutos cada uno. No lo lances con otra cosa usando el
conductor.

### `gate.report` — el juicio

| flag | obligatorio | qué hace |
|---|---|---|
| `--project`, `--databank` | sí | de qué cosecha lee (el databank **de build**); coge siempre la más reciente |
| `--feed` | sí | feed de SQX con el que se le pagan las barras al mono, p. ej. `XAUUSD_DukasM1_Infinox` |
| `--set` | no | cambia un umbral sin editar el fichero: `--set degradacion.min_t=1.65` |

**No toca SQX en absoluto.** Sobre 231 estrategias tardó segundos: la cosecha se lee en 0,3 s y el
mono cuesta 0,1 s por estrategia con 2.000 corridas nulas. Puedes reejecutarlo con otros umbrales
todas las veces que quieras.

## Qué produce

**La cosecha** — `~/Desktop/AlgoData/harvest/<proyecto>/<databank de build>/<fecha>/`, fechada e
inmutable. Todo va indexado por **identidad**, no por nombre:

| fichero | qué es |
|---|---|
| `metrics.parquet` | una fila por estrategia y **cada métrica dos veces**: `[IS]` del databank de build y `[OOS]` del de retesteo. Más `strategy` y `strategy_build`, los dos nombres |
| `trades.parquet` | todos los trades de los dos lados, con una columna `sample` que dice de cuál viene cada uno |
| `equity.parquet` | la equity diaria de cada lado, igual con su `sample` |
| `missing_oos.csv` | las que están en el build y no en el retesteo: identidad y nombre |
| `manifest.json` | los dos databanks, la clave del join, y cuántas emparejaron |

Los `.sqx` copiados y los CSV intermedios **se borran**: pesan diez veces más que el Parquet.

⚠️ Si la cosecha imprime `AVISO: columnas (OOS) con datos`, ese databank **no** corrió una sola
ventana: llevaba su propio corte IS/OOS dentro, y la puerta está tirando la mitad de sus números.
Es el aviso de que le has dado un databank de otro tipo.

**El juicio** — `~/Desktop/AlgoData/reports/<proyecto>/<databank de build>/<fecha>/gate/`:

| fichero | qué es |
|---|---|
| `scorecard.parquet` | una fila por estrategia y tres columnas por criba: el valor, si pasó y la nota |
| `verdict.csv` | para el databank **de retesteo** — la población que sigue adelante |
| `verdict_build.csv` | para el databank **de construcción** — el único que puede nombrar a las que SQX tiró del retesteo, porque allí no tienen nombre |
| `funnel.csv` | el embudo: por criba, cuántas entran, pasan y mueren |
| `resumen.md` | el embudo con los umbrales que estaban puestos y por qué existe cada criba |

## Cómo se lee el resultado

Lo primero que se mira es el embudo que imprime por pantalla. Éste es un proyecto real con las dos
tareas separadas — 120 estrategias construidas, 115 que llegaron al retesteo:

```
115 emparejadas + 5 sin OOS, ventana 2017-11-29 -> 2022-12-29

presencia      hard  entran   120 pasan   115 mueren     5
sanidad        hard  entran   115 pasan   112 mueren     3
estaticas      hard  entran   112 pasan    64 mueren    48
degradacion    hard  entran    64 pasan    45 mueren    19
forma          hard  entran    45 pasan    45 mueren     0
mono           hard  entran    45 pasan    45 mueren     0
familia        soft  entran    45 pasan     0 mueren     0
redundancia    soft  entran    45 pasan    45 mueren     0

45 de 120 sobreviven
```

Se lee de arriba abajo: **qué criba está haciendo el trabajo**. Aquí, dos:

| criba | qué mató | qué dice |
|---|---|---|
| `presencia` | 5 | SQX las tiró del retesteo por sus propias banderas rojas. Comprobado: faltan también por nombre, no es un fallo de emparejamiento |
| `sanidad` | 3 | pocos trades o trades idénticos a otra |
| **`estaticas`** | **48 de 112** | el 43 % simplemente **pierde dinero** fuera de muestra, con el umbral más laxo que existe |
| `degradacion` | 19 | de las que ganan, casi un tercio no aguanta su propio error estándar |
| `mono` | 0 | con `max_p: 0.50`. Pero la mediana de p entre los 45 supervivientes es **0,10**, y **sólo 5 de 45 batirían al mono al 5 %** |

Y esos 45 supervivientes conservan una **mediana del 45 % de su Sharpe** de construcción, que es lo que
se parece a la realidad. Compáralo con una población que ya venía filtrada por su propio OOS
(`XAUUSD/OOS`): allí el 99 % ganaba dinero, la retención mediana era **1,00** y el mono no mataba a
nadie. Esos números no eran buenos, eran el filtro mirándose al espejo.

`redundancia` agrupa por la **estructura** de la estrategia — los bloques de su XML y su orden,
ignorando los valores de los parámetros. Aquí los 45 supervivientes son **13 formas distintas, y una
sola se lleva 24 de ellas**. No elimina a nadie, pero es lo que hay que saber antes de montar una
cartera con "45 estrategias".

Una criba que mata 0 está puesta demasiado laxa **o** la población ya venía filtrada por eso mismo.
Distinguir las dos cosas es mirar la distribución de su columna en el `scorecard.parquet`.

La columna `reason` del `verdict.csv` dice de qué murió cada descartada:

```
Strategy 21.30.45,DESCARTAR,...,presencia = 0 | SQX no la dejo en el databank OOS
Strategy 21.17.26,DESCARTAR,...,degradacion = 0.7249 | t=0.58 anos+=3 conc=1.06
Strategy 18.22.27,DESCARTAR,...,sanidad = 300 | trades identicos a otra estrategia
```

Las dos últimas son el caso que justifica la criba `sanidad`: **estrategias con los trades byte a
byte idénticos** bajo nombres y hashes de fichero distintos. No son dos observaciones, son una.

## Un ejemplo completo

```bash
$ python3 -m gate.harvest --project XAU_ISOOS_ejemplo --databank Results \
      --oos-databank OOS --role custodian
Results: 120 · OOS: 115 · emparejadas 115 (0 por nombre) · sin OOS 5 · solo en OOS 0
bloque con datos: build=(IS) · retesteo=(OOS)
wrote /home/sergioguslw/Desktop/AlgoData/harvest/XAU_ISOOS_ejemplo/Results/2026-09-23

$ python3 -m gate.report --project XAU_ISOOS_ejemplo --databank Results \
      --feed XAUUSD_DukasM1_Infinox
115 emparejadas + 5 sin OOS, ventana 2017-11-29 -> 2022-12-29
presencia      hard  entran   120 pasan   115 mueren     5
...
45 de 120 sobreviven -> .../reports/XAU_ISOOS_ejemplo/Results/2026-09-23/gate
```

Probar un umbral más duro sin volver a tocar SQX:

```bash
$ python3 -m gate.report --project XAU_ISOOS_ejemplo --databank Results \
      --feed XAUUSD_DukasM1_Infinox --set mono.max_p=0.05 --set degradacion.min_t=1.65
```

Y aplicar el resultado dentro de SQX (página 27, con el install parado). Ojo con **cuál** de los dos
veredictos aplicas a **cuál** databank:

```bash
$ python3 -m sqx.curate.apply_verdict --project XAU_ISOOS_ejemplo --databank OOS --role custodian \
      --verdict ~/Desktop/AlgoData/reports/XAU_ISOOS_ejemplo/Results/2026-09-23/gate/verdict.csv --apply
```

## Qué NO te dice

- **No te dice que las supervivientes sean buenas.** Te dice que no murieron con los umbrales que
  tenías puestos. Hoy son deliberadamente laxos.
- **No deshace la preselección.** Si el build ya filtraba por OOS, la puerta mide ese filtro, no la
  estrategia. Lo avisa el `resumen.md`, pero no lo puede arreglar.
- **No te dice por qué SQX tiró una estrategia del retesteo.** La criba `presencia` sabe que no está,
  no por qué. Eso está en el log del proyecto y en las banderas rojas de SQX.
- **No compara los costes de las dos tareas.** Cada mitad lleva el spread y el slippage que su tarea
  cobró, y eso es lo que quieres; pero si los pusiste mal en una de las dos, la degradación que mide
  la puerta es la de tus costes, no la del mercado.
- **El mono solo lee un escalón y un estadístico.** El escalón `timing` aleatoriza *cuándo* entra
  cada trade y nada más, y el estadístico por defecto es `sharpe`. Con `net` el mismo corpus da un
  resultado muy distinto (51 % contra 21,5 % de supervivientes, medido el 2026-09-22). El estadístico
  mueve el veredicto más que el nulo: página 26.
- **`redundancia` no dice que dos estrategias correlacionadas sean la misma.** Dice que a efectos de
  cartera aportan casi lo mismo durante ESE periodo.
- **Nada de esto sustituye al protocolo de robustez** (páginas 15, 17, 18, 19): la puerta elige a
  quién dedicarle esos días de máquina.

## Si algo falla

- `KeyError: 'custodian'` — le has pasado un `--role` que no está en `config/machine.yaml`.
- `emparejadas 0` — los dos databanks no comparten ninguna estrategia. O te has equivocado de
  databank, o las del retesteo se regeneraron y ya no son las mismas: la identidad es la definición,
  y una estrategia reconstruida es otra estrategia.
- `KeyError: 'OOS'` al cargar la cosecha — esa cosecha es del formato viejo, de un solo databank.
  Vuelve a cosechar.
- El embudo dice `entran 0` en `estaticas` — la consulta de `keep` nombra una columna que esa vista
  no exporta. Mira las columnas reales en el `metrics.parquet` de la cosecha.
- `SystemExit` dentro del mono, hablando de `max_hold` — alguna estrategia mantiene una posición más
  barras de las que el escáner mira hacia delante. Es una negativa a propósito, no un fallo: subir
  `barrier.max_hold` en `nulls/config.yaml` es la decisión que hay que tomar a mano.
- La cosecha se queda colgada arrancando el conductor — otra sesión lo está usando. `ss -ltnp | grep
  5060`.
