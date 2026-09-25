# 31. crossTF — ¿el edge aguanta si lo miras en un reloj más lento?

### Qué pregunta responde

Coges una estrategia hecha en H1 y la miras en H4. Si lo que gana en H1 es una ventaja de
verdad, debería seguir estando ahí cuando solo puedes actuar cada cuatro horas en vez de cada
hora. Si desaparece, o era una ventaja de temporización tan fina que no la vas a poder ejecutar,
o no era una ventaja.

El módulo hace esa comparación **dos veces, de dos maneras distintas**, porque son dos preguntas
diferentes y solo una es un test de robustez:

| | qué le haces a la estrategia | qué significa que falle |
|---|---|---|
| **escalada** | le divides los períodos entre 4 (una media de 20 horas sigue siendo de 20 horas) | **evidencia en contra de la estrategia** |
| **sin escalar** | la dejas igual (una media de 20 velas pasa a ser de 80 horas) | **nada sobre la estrategia** — eso pregunta si el mercado es autosemejante, que es otro tema |

### Cuándo lo usas, y cuándo no

**Sí:** sobre un puñado de supervivientes que ya han pasado la puerta OOS. Es un test caro por
estrategia y su sitio es el final del embudo, no el principio.

**No:** sobre una población de miles recién construida. Y **no** como puerta binaria: la
recomendación es leerlo como una puntuación más, porque H1 y H4 son la misma serie de precios
remuestreada y la evidencia que aporta está muy correlacionada con la que ya te dio la puerta.

**No para bajar a D1 desde H1.** Se puede fabricar, pero el escalado divide entre 24 y los
períodos reales se destruyen: medido sobre las tres madres de 2026-09-22, los parámetros se
mueven entre un 140 % y un 586 % y **todos** quedan pegados al mínimo del constructor. Una
variante así no es la estrategia escalada, es otra estrategia. D1 solo tiene sentido en la fila
sin escalar de la madre.

### Antes de empezar

1. Las madres, en una carpeta, como `.sqx`. No se tocan: el módulo solo lee.
2. `python3 -m core.assets XAUUSD` en verde, antes de tocar ninguna tarea de SQX.
3. La tarea de retest configurada con los mercados adicionales que toquen. Los `<Setup>` van
   **en el mismo orden** que `run.blocks` de `studies/transfer/crossTF/config.yaml`, y con
   `<AcceptanceSettings use="false">`: queremos evidencia, no un filtro de selección.
4. El worker custodio parado antes de arrancar nada, y comprobar que no lo está usando otra
   sesión (`ls -lt user/projects` y el log).

### Cómo se ejecuta

Son tres pasos: fabricar, correr, leer.

**1 · Fabricar las hermanas escaladas**

```bash
python3 -m sqx.variants.scale \
  --mothers ~/Desktop/AlgoData/projectsBackup/madres-2026-09-22 \
  --project XAUUSD --source H1 --targets H4
```

| flag | obligatorio | qué hace |
|---|---|---|
| `--mothers` | sí | carpeta con los `.sqx` originales |
| `--project` | sí | de qué proyecto vienen; da nombre al árbol de salida |
| `--out` | no | solo para sacarlo fuera del sitio declarado; normalmente no se usa |
| `--source` | no (H1) | el timeframe en el que se construyeron las madres |
| `--targets` | no (H4) | a qué timeframes se escalan; acepta varios |

Segundos. No toca SQX, se puede lanzar con la GUI abierta.

**2 · Configurar la tarea, correrla y exportarla**

```bash
python3 -m core.assets XAUUSD                            # regla dura 5, bloqueante
python3 -m sqx.projects.crosstf XAUUSD \
    --cfx ~/Desktop/SQX_w2/user/projects/XAUUSD_CrossTF/project.cfx \
    --task Retest-Task4.xml
```

| flag | obligatorio | qué hace |
|---|---|---|
| `--cfx` | sí | el proyecto **custom**, nunca el `Retester` de serie (regla dura 10) |
| `--task` | sí | la tarea de retest donde va el cross-check |
| `--timeframes` | no | los timeframes extra, **en el orden en que serán los bloques 1, 2...**; por defecto, los de la doctrina |

Lo demás sale de `crosstf:` en `assets/_build.yaml` y no se pasa por línea de comandos:
`timeframes: [H4]`, `segment: build..oos1`, `precision: 2` y `conditions: []`.

⚠️ **Las fechas de los `<Setup>` extra son inertes.** La máscara `<MainTestValues>` lleva
`dates="true"`, así que la ventana que se corre de verdad es la del **test principal de esa tarea**.
Para que el cross-TF corra sobre `build..oos1` hay que configurar la tarea con ese segmento. El
comando la lee y avisa si no cuadra:

```
⚠️  la tarea corre 2018.01.01 a 2022.12.31, no 2008.01.01 a 2022.12.31. Las fechas de los <Setup>
extra son INERTES (MainTestValues dates="true"): manda el test principal. Configura la tarea con el
segmento `build..oos1` o los timeframes se leeran sobre otra ventana.
```

Si sale esa línea, arregla la tarea **antes** de correr nada.

### Aquí tampoco se filtra nada

El comando apaga **todas** las condiciones de aceptación del crosscheck y fuerza
`DeleteFailedStrategies` a false — `crosstf.conditions: []`, decisión del dueño del 2026-09-24 —, y
dice cuántas apagó. Con una condición viva, SQX no escribe en el databank de salida la estrategia
que no la cumple, y el análisis se queda sin las muertas. Esto mide; el corte se hace en Python y se
aplica con `/curate`.

El comando termina imprimiendo la línea de `run.blocks` que tienes que pegar en
`studies/transfer/crossTF/config.yaml`. **Pégala**: si no coincide con el orden real de los `<Setup>`,
cada celda se valora sobre las barras equivocadas y no falla nada.

Luego cargas las madres *y* las hermanas en el databank, corres la tarea, y exportas con:

```bash
python3 sqx/export/export_retest.py --project XAUUSD --databank CrossTF
```

**3 · Leer**

```bash
python3 -m studies.transfer.crossTF.report \
  --export  ~/Desktop/AlgoData/exports/XAUUSD/CrossTF/2026-09-23/trades.parquet \
  --scaling ~/Desktop/AlgoData/crosstf/madres-2026-09-22/scaling.parquet
```

### Qué produce

Todo en `~/Desktop/AlgoData/crosstf/<proyecto>/<fecha>/`, fechado e inmutable (regla dura 7:
los datos pesados nunca en el repo). **Esa carpeta es la carga del databank**, tal cual:

- `<madre>_ScaledH4.sqx` — una por madre y timeframe destino. 14 KB cada una.
- `<madre>.sqx` — **las madres, copiadas ahí al lado sin tocar**, porque el estudio necesita
  también sus celdas `baseline` y `control`. Así se carga una carpeta y no dos.
- `scaling.parquet` — qué parámetro se movió y a cuánto, por hermana. **Es el registro de lo
  que se hizo**: sin él, un `.sqx` escalado es indistinguible de uno cualquiera.
- `--out` de `report.py`, opcional: el panel entero en Parquet.

Nada se sobrescribe salvo que apuntes dos veces a la misma carpeta.

### Cómo se lee el resultado

El paso 1 imprime lo que ha movido:

```
3 mothers x 2 targets -> 6 siblings
                      name  ratio  n_scaled  max_rounding_shift  clamped
Strategy 10.13.25_ScaledH4    4.0         2            0.090909    False
Strategy 10.13.30_ScaledH4    4.0         6            0.200000    False
Strategy 29.30.36_ScaledH4    4.0         4            0.142857    False
Strategy 10.13.25_ScaledD1   24.0         2            1.400000     True
Strategy 10.13.30_ScaledD1   24.0         6            4.333333     True
Strategy 29.30.36_ScaledD1   24.0         4            5.857143     True

int parameters left untouched (10) -- review the whitelist:
  BBBarOpensShift1, CBlock_WssShfInt21, CloseDShift1, IchimokuSnkSpnCrsBshSgnStr1, ...
```

Las dos columnas que deciden si la fila sirve para algo:

- **`max_rounding_shift`** — cuánto se desvió el parámetro peor por culpa del redondeo. Un
  período de 9 entre 4 es 2,25 y hay que escribir 2: eso es un 11 % de cambio **encima** del
  cambio de timeframe. Por debajo de 0,15 se lee; por encima, lo que veas podría ser el
  redondeo y no el timeframe. **Menos es mejor.**
- **`clamped`** — un período que habría quedado por debajo de 2 y se ha pegado al mínimo.
  `True` invalida la fila entera: ahí ya no hay escalado, hay un tope.

La última línea lista los parámetros enteros que la whitelist **no** ha tocado. Están ahí para
revisarlos, no porque haya fallado nada: la mayoría son shifts y selectores categóricos, que no
deben escalarse.

El paso 3 imprime tres bloques. Primero la madre en cada timeframe sin escalar, **sin
veredicto**, porque esa fila no juzga a la estrategia. Después las hermanas escaladas, cada una
con su lectura:

| lectura | qué pasó |
|---|---|
| `survives` | gana a su propio nulo de temporización en H4 — el edge es suyo |
| `inherited` | es rentable en H4 pero no se distingue de entrar al azar allí: está heredando H1 |
| `fails` | no aguanta |
| `control_failed` | **la celda de control se hundió**: lo que la rompió fue cambiarle los períodos, no el timeframe. No es un veredicto sobre timeframes |
| `unusable` | el redondeo o el tope movieron los parámetros demasiado; no se puede atribuir nada |

`control_failed` es la razón de ser del diseño. La hermana escalada se corre **también en H1**,
su timeframe de origen, y esa celda dice qué costó el cambio de parámetros por sí solo. Sin ella,
«se murió en H4» y «se murió cuando le cambiaste el 9 por un 2» son la misma observación.

### Un ejemplo completo

Fabricación real sobre las tres madres, mirando una por dentro antes y después:

```
MADRE H1  (7 miembros, 101.9 KB)          HIJA H4  (5 miembros, 14.4 KB)
   CBlock_KSBreakOPrd11        = 20          CBlock_KSBreakOPrd11        = 5
   CBlock_KSBreakOPrd21        = 50          CBlock_KSBreakOPrd21        = 12
   IchimokuSnkSpnCrsBshTnkPrd1 = 9           IchimokuSnkSpnCrsBshTnkPrd1 = 2
   IchimokuSnkSpnCrsBshKjnPrd1 = 26          IchimokuSnkSpnCrsBshKjnPrd1 = 6
   IchimokuSnkSpnCrsBshSnkPrd1 = 36          IchimokuSnkSpnCrsBshSnkPrd1 = 9
   IchimokuSnkSpnCrsBshSgnStr1 = 1           IchimokuSnkSpnCrsBshSgnStr1 = 1   <- intacto
   IchimokuSnkSpnCrsBshShf1    = 1           IchimokuSnkSpnCrsBshShf1    = 1   <- intacto
   ExitAfterBars1              = 10          ExitAfterBars1              = 2
   fingerprint = SI                          fingerprint = no, stamp = CTF001H4
```

Los períodos bajan; el shift y el selector de fuerza de señal se quedan. El `<Fingerprint>`
heredado desaparece — si se quedara, el databank podría fundir todas las hermanas en una.

### Qué NO te dice

- **No te dice que la estrategia sea buena.** Dice si su ventaja sobrevive a mirarla más
  despacio. Una estrategia mala puede pasar el test perfectamente.
- **La celda H4 no es «la misma estrategia, reloj más lento».** Por decisión del dueño
  (2026-09-23) solo se escalan períodos y salidas por barras. Los `StopLossCoef` y
  `ProfitTargetCoef` se escriben tal cual, y como multiplican un rango que crece al agregar
  velas, **el stop en H4 es físicamente el doble de ancho en precio**. Es una propiedad
  declarada de la comparación, no un fallo — pero no la describas como limpia.
- **H1 y H4 no son muestras independientes.** Una vela H4 está hecha de las mismas cuatro velas
  H1. Esto aporta mucha menos información que probar en otro mercado, y por eso el veredicto se
  apoya en el nulo de cada timeframe y no en «¿es rentable?».
- **No dice nada sobre datos no vistos.** Si el retest cae dentro de la ventana en la que se
  seleccionó la estrategia, sigue siendo ventana seleccionada.

### Si algo falla

- **Todas las celdas dan los mismos números.** El separador de bloques no ha funcionado. Los
  bloques se parten por el ticket reiniciándose en 1, no por la columna `Symbol`, que es la
  misma en todos los timeframes de un activo. Comprueba que el export es `data=all`.
- **`KeyError` con un timeframe.** `run.blocks` no coincide con el orden de los `<Setup>` de la
  tarea. `report.py` imprime el mapeo en la primera línea: léelo antes que ningún número.
- **Casi todo sale `unusable`.** Las madres tienen períodos cortos. Es un resultado, no un
  error: mira `max_rounding_shift` en `scaling.parquet` y decide si 0,15 es la tolerancia que
  quieres, en vez de subirla sin mirar.
