# 32. Configurar el MC Retest en SQX — las ocho tareas, escritas de una vez

> **Ojo con el nombre.** Esta página es la mitad de SQX del paso 13: **dejar las ocho tareas
> configuradas** dentro de un custom project. Leer los resultados es la página `11-retest-mc.md`
> (paso 14), y el Monte Carlo que reordena operaciones es la `07-montecarlo.md`, que es otra cosa.

### Qué pregunta responde

El MC Retest vuelve a correr el backtest entero mil veces cambiando **una sola cosa** cada vez: el
spread, el slippage, los parámetros, las velas. Ocho tareas, ocho preguntas distintas, y por eso se
sabe **cuál** de ellas rompe la estrategia.

Configurarlas a mano son ocho formularios de SQX con seis pestañas cada uno, y basta que en uno se
quede un método de más encendido para que esa tarea deje de poder atribuir nada. Este comando las
escribe las ocho desde el catálogo de `assets/_build.yaml`, con los rangos de perturbación del
activo, y dice en voz alta lo que ha dejado sin configurar y por qué.

### Cuándo lo usas, y cuándo no

**Úsalo** cuando ya tienes un custom project con su población dentro — después de la puerta OOS,
del crossmarket y del crossTF — y quieres dejarlo listo para lanzar el MC Retest.

**No lo uses** sobre el `Builder` ni el `Retester` de serie (regla dura 10), ni sobre una población
recién construida sin cribar: mil simulaciones por estrategia sobre diez mil estrategias es una
factura de CPU que no se paga para descartar lo que la puerta OOS descarta gratis.

### La regla de la distancia mínima

**`MCR 4 MinDist` sólo se configura si la población lleva órdenes stop o limit.** Decisión del
dueño, 2026-09-23, y es simple aritmética: la distancia mínima es lo cerca del precio que un bróker
te deja poner una orden **pendiente**. Si todas las entradas son a mercado no hay ninguna orden
esperando en el libro, así que esa tarea sortearía un número que nadie lee, y mil simulaciones
después diría que la estrategia es perfectamente robusta a algo que no le pasa.

El comando lo mira solo, en este orden:

1. **La población**, si el databank ya está construido: abre los `.sqx` y lee qué órdenes usan de
   verdad. Se para en cuanto encuentra la primera pendiente. 0,2 ms por estrategia.
2. **El generador**, si todavía no hay población: si la tarea Build no tiene encendidos
   `EnterAtStop` ni `EnterAtLimit`, la respuesta es no y es segura — lo que el generador no puede
   emitir no puede estar en el databank.
3. Si el generador **sí** puede emitirlas y aún no hay estrategias, la pregunta **no está
   resuelta**, y el comando no se la inventa: deja la tarea sin configurar y te dice que vuelvas a
   pasarlo después del build.

Lo mismo vale dentro de `MCR 8 Stress`, que lleva seis métodos a la vez: si no hay órdenes
pendientes se cae **ese método** y la tarea se escribe con los otros cinco. La condición es del
método, no de la tarea.

### Las tres cosas que se tocan por tarea

Todo está en `assets/_build.yaml`, bloque `mc_retest:`, y nada de esto vive en el código.

**`simulations`** — cuántas veces se vuelve a correr el backtest perturbado. **Cada tarea lleva el
suyo**, así que se puede abaratar una cara sin tocar las demás: `MCR 7 OHLC` a 250 y el resto a
1.000 es una línea. El coste es lineal — la mitad de simulaciones, la mitad de tiempo — y por debajo
de unas 200 el percentil de confianza que lee el paso 14 empieza a ser ruido.

**`precision`** — es `MCBacktestPrecision`, la fidelidad intrabarra de cada simulación, y **no** es
el `testPrecision` del backtest principal. Los dos valores van al revés de lo que sugiere la
palabra:

| valor | qué es | coste medido |
|---|---|---|
| `1` | **sólo el timeframe elegido.** Rápido y grosero: ve las velas M30 tal cual, sin mirar qué pasó dentro | 20–25 s |
| `2` | **un minuto.** Lento y fino: reconstruye cada vela desde barras de un minuto, así que respeta el orden real en que se tocaron máximo y mínimo | 50 s |

Mismas 1.000 simulaciones y misma ventana en los dos casos, medido el 2026-09-23. O sea: el número
alto es el preciso, y cuesta el doble.

**`segment`** — qué ventana se vuelve a correr. Dos formas y sólo dos:

```yaml
segment: build          # un tramo suelto, tal como lo define assets/_policy.yaml
segment: build..oos1    # DOS PUNTOS: una sola ventana continua que abarca los dos
```

`build..oos1` **no son tres puntos** y no es "los dos tramos por separado": es una ventana
continua del principio del primero al final del último —en XAUUSD, 2008.01.01 → 2022.12.31— y
además marca el segundo tramo como fuera de muestra dentro de la tarea, que es lo que hace que
`full_sample: true` signifique algo. Se cobra a los costes del **último** tramo, o sea al spread de
`oos`, el más caro de los dos declarados: una ventana que abarca las dos muestras se lee al precio
pesimista.

⛔ **`oos2` no vale**, ni suelto ni dentro de un rango. Está reservado al WFC y a la WFM y cada
mirada lo gasta; el comando se niega y dice por qué.

### Antes de empezar

- El proyecto tiene que existir y ser **custom** (`sqx.projects.builder`), clonado del donante
  congelado, que es el que trae las ocho tareas con sus nombres.
- El `.cfx` **no puede estar abierto** por una instancia de SQX: SQX lo reescribe al salir y se
  lleva el cambio por delante sin decir nada (regla dura 4). El comando lo comprueba y se niega.
- El activo tiene que tener sus costes pactados (`python3 -m core.assets <SIMBOLO>`), y sus rangos
  de perturbación decididos en `assets/symbols/<SIMBOLO>.yaml`, bajo `mc_retest:`. Un rango en
  `null` no bloquea nada: sólo se cae el método que lo necesitaba, y el comando lo canta.

No toca SQX ni ningún worker: sólo lee y reescribe un fichero. Tarda menos de un segundo.

### Cómo se ejecuta

```bash
python3 -m sqx.projects.mcretest XAUUSD \
    --cfx ~/Desktop/SQX_w2/user/projects/XAU_estudio/project.cfx \
    --input OOS
```

| flag | obligatorio | qué hace |
|---|---|---|
| `XAUUSD` | sí | el activo, para sus costes, sus ventanas y sus rangos de perturbación |
| `--cfx` | sí | el `project.cfx` del custom project |
| `--input` | sí | el databank que leen **las ocho**. No se adivina: es la población que se perturba |
| `--databank-dir` | no | la carpeta de ese databank, para mirar qué órdenes lleva. Por defecto, la del propio proyecto |
| `--json` | no | saca el resultado entero como JSON, para encadenarlo |

### Qué produce

Reescribe **el mismo `project.cfx`**, en sitio. Por cada tarea del catálogo:

- enciende el crosscheck `MonteCarloRetest` y deja activo **sólo** el método que le toca;
- escribe las mil simulaciones, la precisión y si corre sobre muestra completa;
- pone la ventana y los costes del tramo que esa tarea usa;
- **apaga todas sus condiciones de aceptación**;
- apunta su databank de entrada al que le has dicho.

La tarea que no se puede configurar se queda **inactiva y con el crosscheck apagado**, para que no
pueda correr por descuido pareciendo lo que no es.

### Cómo se lee el resultado

Salida real, sobre una copia del donante congelado y con la población del `OOS` del maestro:

```
XAUUSD  XAUUSD  <- OOS
  ordenes (population, 231 estrategias leidas): EnterAtMarket  ->  pendientes: no
  ✓ MCR 1 Bar      RandomizeStartingBar  build 2008.01.01→2017.12.31  1000 sims  1 condicion(es) apagada(s)
  ✓ MCR 2 Spread   RandomizeSpread  build 2008.01.01→2017.12.31  1000 sims  1 condicion(es) apagada(s)
  ✓ MCR 3 Slippage RandomizeSlippage  build 2008.01.01→2017.12.31  1000 sims  1 condicion(es) apagada(s)
  ⊘ MCR 4 MinDist  NO configurada — la poblacion no lleva ordenes stop ni limit
  ✓ MCR 5 Params   RandomizeStrategyParameters  build 2008.01.01→2017.12.31  1000 sims  1 condicion(es) apagada(s)
  ✓ MCR 6 Exits    RandomizeExitParameters  build 2008.01.01→2017.12.31  1000 sims  1 condicion(es) apagada(s)
  ✓ MCR 7 OHLC     RandomizeHistoryDataOHLC  build 2008.01.01→2017.12.31  1000 sims  1 condicion(es) apagada(s)
  ✓ MCR 8 Stress   RandomizeExitParameters+RandomizeHistoryDataOHLC+RandomizeSlippage+RandomizeSpread+RandomizeStrategyParameters  oos1 2008.01.01→2022.12.31  1000 sims  1 condicion(es) apagada(s)
      ⚠️ sin RandomizeMinDistance: la poblacion no lleva ordenes stop ni limit

Las ocho leen el MISMO databank: son ocho lecturas de una poblacion, no un embudo.
El veredicto se toma en Python (strategies/retest/) y se aplica con /curate.
```

Línea por línea:

**`ordenes (population, 231 estrategias leidas)`** — de dónde salió la respuesta. `population`
significa que abrió los `.sqx` de verdad; `generator` significa que todavía no hay población y se
ha mirado qué puede emitir el builder.

**`⊘ MCR 4 MinDist`** — la regla del dueño, aplicada. Esta población entra a mercado, así que esa
tarea no existe para este estudio.

**`build 2008.01.01→2017.12.31`** — las siete aisladas vuelven a correr **la muestra de
construcción**: preguntan si el ajuste del build fue frágil. La de estrés va sobre `oos1`, que aquí
significa la muestra entera 2008–2022 con el tramo 2018–2022 marcado como fuera de muestra, y se
cobra al spread de `oos`, que es el más caro de los dos declarados.

**`1 condicion(es) apagada(s)`** — la que convertía la tarea en un filtro. Con ella encendida SQX
borra lo que falla, cada tarea encadena en la siguiente y al final sólo sabes cuántas sobrevivieron:
nunca **a qué** murió cada una, que es lo único que ocho tareas aisladas existen para responder.

### Lo que cuesta correrlo

Medido el 2026-09-23 en el custodio (48 núcleos), **2 estrategias × 1.000 simulaciones por tarea**:

| tarea | precisión MC | tiempo |
|---|---|---|
| MCR 1 Bar | 1 | 25 s |
| MCR 2 Spread | 2 | 50 s |
| MCR 3 Slippage | 2 | 50 s |
| MCR 5 Params | 1 | 20 s |
| MCR 6 Exits | 2 | 50 s |
| MCR 7 OHLC | 2 | **149 s** |
| MCR 8 Stress | 2 | **227 s** |
| **total** | | **9 min 31 s** |

Dos cosas que decidir antes de lanzarlo sobre una población de verdad:

- **Escala con el número de estrategias.** Diez minutos son dos estrategias; cien son unas ocho
  horas. Esto va al final del embudo, sobre supervivientes, nunca sobre una población recién
  construida.
- **La precisión del MC es el factor dos.** Las dos tareas a precisión 1 tardan la mitad que sus
  hermanas a precisión 2 con el mismo trabajo. `MCR 7 OHLC` es cara por otro motivo: reconstruye el
  histórico entero en cada simulación. Y la de estrés, además, corre 15 años en vez de 10.

### Un ejemplo completo

```bash
$ python3 -m core.assets XAUUSD          # preflight obligatorio (regla dura 5)
...
AVISO: los rangos MC Retest min_distance no están decididos. No bloquea,
pero esa tarea del MC Retest no es interpretable hasta que el dueño los fije.

$ python3 -m sqx.projects.mcretest XAUUSD --cfx ~/Desktop/SQX_w2/user/projects/XAU_estudio/project.cfx --input OOS
```

Y después, para lanzarlo:

```bash
bin/sqx-worker.sh --role custodian start
python3 -c "from core import worker; worker.call('-project action=start name=XAU_estudio','custodian')"
```

Una sola cosa a la vez en el custodio, y `bin/sqx-worker.sh --role custodian stop` al acabar.

### Qué NO te dice

- **No dice si la estrategia es buena.** Deja las tareas configuradas; quien las corre es SQX y
  quien las lee es `strategies/retest/`.
- **No decide nada sobre la población.** Las condiciones de aceptación se apagan a propósito: esto
  produce evidencia, y el veredicto se toma después, en Python, y se aplica con `/curate`.
- **No comprueba que los rangos tengan sentido.** Que el spread se sortee entre 5 y 30 puntos es una
  decisión escrita en `assets/symbols/XAUUSD.yaml`; el comando la escribe, no la juzga.
- **No sustituye al build.** Si el proyecto no tiene población, el comando se configura igual, pero
  la pregunta de las órdenes pendientes puede quedarse sin resolver y lo dice.

### Si algo falla

**`el custodian tiene este proyecto abierto y reescribe el .cfx al salir`** — para el worker antes:
`bin/sqx-worker.sh --role custodian stop`. Es la regla dura 4 y no es negociable.

**`el proyecto no lleva la tarea MCR 3 Slippage`** — el proyecto no se clonó del donante congelado,
o se creó con `--only` y se quedó sin esas tareas. Se vuelve a crear con `sqx.projects.builder`
quedándose las `Retest`.

**`rango min_distance sin decidir en assets/symbols/XAUUSD.yaml`** — hay órdenes pendientes en la
población, así que la tarea sí hace falta, pero nadie ha dicho entre qué dos distancias sortear.
Ese número lo decides tú y va en el fichero del activo.

**`sin poblacion construida: el generador PUEDE emitir ordenes pendientes`** — el builder tiene
`EnterAtStop` o `EnterAtLimit` encendidos pero todavía no hay estrategias. Corre el build y vuelve
a pasar el comando; entonces la respuesta sale de la población y no de una suposición.
