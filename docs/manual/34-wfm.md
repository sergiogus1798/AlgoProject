# 34. Configurar la Walk Forward Matrix en SQX — la última bala

> **Ojo con el nombre.** Esta página es la mitad de SQX del paso 19: **dejar la tarea `WFM`
> configurada** dentro de un custom project. Sacar lo que produce es `09-wfm.md`, y leerlo —si
> predice o no— es `14-walkforwardmatrix.md` (que forma parte del paso 20).

### Qué pregunta responde

La Walk Forward Matrix reoptimiza la estrategia sobre una ventana que se desliza y corre cada
elección sobre el tramo siguiente, **30 veces con particiones distintas**: 5 porcentajes de fuera de
muestra (20 a 40 %) por 6 números de pasadas (6 a 16). La pregunta es si lo que optimiza bien
predice lo que va bien después, y las 30 celdas existen para que la respuesta no dependa de haber
elegido una partición con suerte.

### ⚠️ Dos reglas del dueño que este comando hace cumplir

**1. Acaba en `oos2`, y `oos2` es una puerta de un solo sentido.** La ventana es `build..oos2`, o
sea todo el histórico, pero lo que se gasta es la cola: `assets/_policy.yaml` reserva ese tramo para
el WFC y la WFM. Todo lo demás en el proyecto se niega a tocarlo —`configure.py`
aborta si se lo pides—; esta tarea es la excepción, porque es aquello **para lo que** está
reservado. Cada mirada lo gasta y no se repite.

**2. No se LEE hasta que 17, 18 y 19 estén los tres hechos.** Del 7 al 16 se mira `oos1` una y otra
vez, así que para cuando se llega aquí ese tramo está quemado y `oos2` es lo único virgen. Si se
leen el WFC y el CSCV antes de decidir si se corre la WFM —y con qué parámetros—, esa decisión ya
está contaminada por lo visto, y la última bala se gasta en un test elegido a posteriori. El comando
lo dice cada vez que se ejecuta; forzarlo de verdad es trabajo del ledger, que todavía no existe.

### Cuándo lo usas, y cuándo no

**Úsalo** cuando quedan pocos supervivientes, has hecho ya el 16.5/17 (variantes y WFC) y el 18
(CSCV), y no has mirado ninguno de sus resultados.

**No lo uses** para "ver qué sale" sobre una población grande. No es una cuestión de CPU: es que
mirar gasta la muestra, y no hay otra.

### La rejilla que escribe

| ajuste | valor | de dónde sale |
|---|---|---|
| ventana | `build..oos2` — 2008.01.01 → 2026.08.30 en XAUUSD | `wfm.segment` |
| a qué precio se cobra | al tramo **`oos1`**, el intermedio — no al último de la ventana | `wfm.costs_segment` |
| `Param1` — % de cada pasada fuera de muestra | 20 → 40 de 5 en 5 (5 columnas) | `wfm.oos_pct` |
| `Param2` — número de pasadas | 6 → 16 de 2 en 2 (6 filas) | `wfm.runs` |
| celdas | **30** | el producto de los dos |
| `MaxTests` | 5.000 por paso y celda | `wfm.max_tests` |
| `±distribution` y el paso | ±35 %, un 4 % por paso → `maxSteps=18` | `wfm.distribution_pct`, `wfm.step_pct` |
| tipo de periodo | `percent` (=10) — **fijo**: los periodos van por nº de pasadas y % de OOS, nunca por días ni barras | `wfm.period_type` |
| tipo de optimización | `floating` (=15) — **fijo**: la ventana se desliza manteniendo su longitud | `wfm.optimization_type` |
| fidelidad del walk-forward | `exact_is_exact_oos` (=2) — "Exact IS, Exact OOS" | `wfm.wf_type` |
| qué se permuta | los parámetros **recomendados** por SQX, nada más | fijo |
| precisión | 2 (1 minuto) | `wfm.precision`, igual que la doctrina |

La ventana empieza en `build` a propósito: un walk-forward necesita histórico DELANTE del tramo
reservado, porque la primera pasada tiene que optimizar sobre algo antes de poder correr sobre nada.
Lo que se gasta es el final, `oos2`.

**El cobro es la excepción del proyecto.** Los demás spans se cobran al último tramo (el precio
pesimista); éste se cobra a `oos1`, el intermedio, por decisión del dueño (2026-09-24): son 18,7
años de los que `oos2` es la cola de 3,7, y cobrar quince años al precio de cuatro no describe nada.
Hoy `oos1` y `oos2` comparten `spread_oos` —10 puntos y slippage 5 en XAUUSD— así que el número sale
idéntico; la línea decide el día que el activo declare un spread propio para `oos2`. Un intermedio
de verdad, entre los 5 de `is` y los 10 de `oos`, habría que declararlo en
`assets/symbols/<SIM>.yaml`: esa cifra la pone el dueño, no el catálogo.

**La fidelidad es el atributo `type` del elemento `<WalkForward>`**, que SQX llama "Walk-Forward
type" y que aquí va en `exact_is_exact_oos` (decisión del dueño, 2026-09-24). Lo que cambia respecto
al default de SQX no son los decimales: es **quién elige los parámetros de cada paso**. Con
`simulated IS`, el ganador de cada paso sale de recortar a su ventana una única tanda de backtests
sobre el rango entero —arrastrando el camino de la equity, que con sizing por ATR no es neutro, y
los trades abiertos antes del borde—; con `exact`, cada paso hace su propia optimización sobre su
ventana, que es lo que harías en vivo al reoptimizar. La pregunta de la WFM es si la optimización
**predice** el tramo siguiente, y con IS simulado la "optimización" es un recorte.

No es territorio nuevo: la WFM que ya corrió el maestro llevaba `type="2"` con `MaxTests` 500 sobre
cinco años, y terminó.

**Y por eso `MaxTests` bajó de 15.000 a 5.000.** Los dos mandos compran cosas distintas: `MaxTests`
compra una elección mejor por paso y **nada que se pueda leer después** —SQX guarda sólo el ganador
de cada paso, no la población que probó (medido, `knowhow/sqx-format/wfm-in-settings-xml.md`)—, mientras que
`wf_type` cambia lo que significa el número que sí se guarda. Habiendo que elegir dónde van los
núcleos, van a la exactitud. Cuenta la factura antes de lanzar: son 5.000 backtests por paso, por
los 6–16 pasos de cada celda, por 30 celdas, por estrategia, a precisión 2.

### El criterio: cuándo aprueba una casilla y cuándo aprueba la estrategia

Esto es lo que la tarea del maestro NO tenía —corría con el elemento de condiciones vacío, y con
cero condiciones SQX aprueba todas las casillas con un 100— y es lo que ahora escribe el comando.
Decodificado del propio SQX el 2026-09-24 (`knowhow/conditions/wfm-acceptance.md` tiene la disección):

```
score de la casilla = round(condiciones cumplidas / condiciones activas * 100)
casilla aprobada    = score >= threshold_pct          (80 %)
estrategia aprobada = hay un rectángulo de 4x4 casillas, en alguna de sus 6 posiciones,
                      con 12 o más aprobadas          (grid_passing_size, min_squares)
```

Las diez condiciones, agrupadas por la pregunta que hacen:

| pregunta | condición | la cumplen |
|---|---|---|
| ¿gana dinero en lo que no vio? | `WF Net profit (OOS) > 0` | 66 % |
| | `WF Profit factor (OOS) > 1,05` | 45 % |
| ¿se parece el fuera de muestra a lo que prometía la optimización? | `Stability Profit factor > 60 %` | 80 % |
| | `Stability Net profit > 20 %` | 30 % |
| | `Stability Max DD % < 150 %` | 79 % |
| ¿reoptimizar conserva la forma del original? | `Score Profit factor > 85 %` | 83 % |
| ¿está repartido el resultado entre pasadas? | `% de pasadas rentables > 50` | 51 % |
| | `máximo beneficio en una pasada < 50 % del total` | 11 % |
| | `mínimo de trades en una pasada > 20` | 55 % |
| | `máximo DD % en una pasada <= 25` | 100 % |

La columna *"la cumplen"* es el porcentaje de las **150 casillas reales** del databank `WFM` del
maestro (5 estrategias x 30 celdas) que pasan ese umbral: es la calibración, y está ahí para que se
vea qué condición separa y cuál no. Con este juego y `threshold_pct: 80`, 2 de esas 5 estrategias
encuentran el área 4x4 con 12 y 3 no.

⚠️ **Los defaults de SQX habrían tirado todo.** Su `Stability Net profit > 60` lo cumple el 1 % de
esas casillas —la mediana está en 8,6 %, porque el tramo de optimización es justo el que se eligió
por ser el mejor— y su `% de pasadas rentables > 70`, el 9 %.

⚠️ **Y esto YA FILTRA.** Con condiciones activas SQX descarta a quien no encuentre el área y no lo
escribe en el databank de salida (`Cross Check filter in 'WF matrix'`), sin que
`DeleteFailedStrategies` tenga nada que decir. Es distinto del resto del proyecto, donde el veredicto
se toma en Python. Para volver al modo mapa —puntuar las 30 casillas y no tirar a nadie— se pone
`min_squares: 0` en `_build.yaml`: el rectángulo siempre cumple "0 o más".

Los umbrales se tocan en `assets/_build.yaml`, bloque `wfm.conditions`. Cada línea es
`{read, metric, op, value}`, donde `read` elige de dónde sale el número: `oos` (las pasadas fuera de
muestra concatenadas), `stability` (OOS contra optimización, en %), `score` (la WF contra el
backtest original, en %) o `special` (las cuatro columnas que SQX calcula pasada a pasada).

### Antes de empezar

- El proyecto tiene que ser **custom** y llevar la tarea titulada `WFM`, que viene del donante
  congelado. Si no la lleva, el comando se niega en vez de fabricarla: el bloque y sus condiciones
  vienen de una tarea que escribió SQX.
- El `.cfx` **no puede estar abierto** por una instancia (regla dura 4). El comando lo comprueba.
- Costes pactados: `python3 -m core.assets <SIMBOLO>` (regla dura 5).
- La ventana `oos2` del activo tiene que estar decidida en `assets/_policy.yaml`. En los activos con
  `from: null` no hay ventana y el comando revienta — que es lo correcto.

No toca SQX ni ningún worker: reescribe un fichero y tarda menos de un segundo.

### Cómo se ejecuta

```bash
python3 -m core.assets XAUUSD                       # preflight, BLOQUEANTE
python3 -m sqx.projects.wfm XAUUSD \
    --cfx ~/Desktop/SQX_w2/user/projects/XAUUSD_estudio/project.cfx \
    --input "SPP OOS"
```

| flag | obligatorio | qué hace |
|---|---|---|
| `<SIMBOLO>` | sí | el activo, para sus costes y su ventana `oos2` |
| `--cfx` | sí | el `project.cfx` del custom project |
| `--input` | sí | el databank que lee: los supervivientes que han llegado al paso 19 |
| `--json` | no | lo mismo como JSON |

### Qué produce

Reescribe **en el sitio** el `project.cfx`: la tarea `WFM` queda activa, con el crosscheck
`WalkForwardMatrix` encendido, la rejilla de 30 celdas escrita, la ventana `build..oos2` a los costes de `oos1` —también en `<Resources><Symbol>`, que es qué barras carga la tarea—, las condiciones
del donante apagadas y las diez del catálogo escritas. Su salida va al databank `WFM`.

### Cómo se lee el resultado

```
XAUUSD  XAUUSD  SPP OOS → WFM
  ✓ WFM  build..oos2 2008.01.01→2026.08.30  30 celdas (6 pasadas x 5 % OOS), tope 5000 tests
         por paso, 18 pasos de parametro, precision 2
      cobrada al tramo oos1: spread 10.0 — NO al ultimo tramo de la ventana
      fidelidad "Exact IS, Exact OOS (slow)" — 5000 tests por paso x 30 celdas, y cada paso
         es una optimizacion propia
      13 condicion(es) del donante apagadas y 10 propias escritas: una casilla aprueba con
         80 % de ellas cumplidas
      la estrategia pasa si encuentra 12 casillas aprobadas en un area de 4x4 — 6 posiciones
         posibles. ⚠️ ESTO FILTRA: SQX descarta a quien no lo encuentre y no lo escribe en el
         databank de salida

⚠️ build..oos2 acaba en un tramo RESERVADO para WFC, WFM: cada mirada lo gasta y no se repite.
⚠️ Y no se LEE hasta que 17, 18 y 19 esten los tres hechos.
```

- **`2008.01.01→2026.08.30`** — comprueba las fechas. Si el final no es el de `oos2`, la tarea no
  está mirando el tramo reservado; si el principio es 2023, el walk-forward se queda sin histórico
  para su primera optimización.
- **`cobrada al tramo oos1`** — si dice `oos2`, alguien cambió `costs_segment` y la ventana entera
  está corriendo al precio del tramo más caro.
- **`30 celdas`** — si sale otro número, alguien tocó los ejes en `_build.yaml`. No es un error; es
  un estudio distinto, y `strategies/walkForwardMatrix/` te dirá cuántas celdas leyó.
- **`13 del donante apagadas y 10 propias escritas`** — el 13 es lo normal en un clon del donante y
  un **0 es un aviso**: ese `.cfx` no viene del donante o alguien ya lo editó. Si el segundo número
  no es el de `wfm.conditions`, la matriz está juzgando con otra cosa.
- **`⚠️ ESTO FILTRA`** — con `min_squares` distinto de 0 la tarea tira estrategias. Si lo que
  querías era el mapa, para y pon `min_squares: 0`.
- **`⚠️ esta tarea corre ademas: …`** — ese `.cfx` no pasó por la doctrina y correría otros
  crosschecks a la vez, cada uno con su factura. Vuelve a clonar con `sqx.projects.builder`.

### Un ejemplo completo

```bash
python3 -m core.assets XAUUSD
python3 -m sqx.projects.wfm XAUUSD --cfx ~/Desktop/SQX_w2/user/projects/XAUUSD_estudio/project.cfx \
    --input "SPP OOS"

bin/sqx-worker.sh --role custodian start
python3 -c "from core import worker; worker.call('-project action=start name=XAUUSD_estudio','custodian')"
# ... termina ...
bin/sqx-worker.sh --role custodian stop

# el paso 20 empieza aquí, y sólo si el 17 y el 18 ya están hechos:
python3 -m sqx.export.export_wfm --project XAUUSD_estudio --databank WFM --role custodian
python3 -m strategies.walkForwardMatrix.report --project XAUUSD_estudio --databank WFM
```

### Qué NO te dice

- **No dice si la estrategia gana dinero fuera de muestra.** Dice si su optimización **predice** su
  resultado posterior. Una estrategia puede ser rentable y completamente ciega a la vez.
- **No guarda la población de cada optimización**, sólo el ganador de cada paso. Lo más parecido a
  "cada juego de parámetros con su resultado IS y OOS" son los pasos del walk-forward, no el
  optimizador.
- **El último paso de cada celda no tiene resultado fuera de muestra**: se optimiza sobre la cola
  del histórico y ya no queda nada delante. El análisis los tira, y tirarlos es correcto.
- **No sustituye al WFC ni al CSCV.** Los tres se leen juntos, en el paso 20, y por eso el orden
  importa.

### Si algo falla

| lo que sale | qué significa |
|---|---|
| `el proyecto no lleva la tarea WFM` | el clon se hizo sin ella. Clona con `--tasks Retest` y el `--only` que la incluya |
| `el custodian tiene este proyecto abierto…` | párala antes; si no, SQX reescribe el `.cfx` al salir |
| un `KeyError` o fechas vacías | el activo tiene `oos2: {from: null}` en `_policy.yaml`. Sin ventana decidida no hay WFM |
| `un area de NxN no cabe en una matriz de …` | `grid_passing_size` es mayor que el eje más corto. SQX no avisaría: se quedaría con la mejor casilla suelta y descartaría todo |
| `min_squares N es imposible en un area de …` | pides más casillas de las que tiene el rectángulo |
| en el análisis, celdas con muy pocos pasos | `oos2` es corto (3,7 años en XAUUSD). 16 pasadas sobre esa ventana dejan tramos diminutos: míralo antes de leer una correlación por celda |
