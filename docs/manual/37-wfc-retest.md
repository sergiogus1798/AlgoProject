# 37. El retest de las variantes para el WFC y el CSCV

Escribe en un proyecto custom de SQX **las tres tareas** que producen el material de los pasos 17
(Walk Forward Correlation) y 18 (CSCV): una por tramo —`build`, `oos1`, `oos2`—, cada una con el
spread y el slippage que le tocan, y cada una corriendo además los mercados adicionales.

### Qué pregunta responde

Ninguna, todavía. Esto no analiza: **prepara los backtests**. Lo que produce son tres databanks con
las mismas variantes corridas sobre tres tramos distintos, que es el material que luego leen
`strategies/walkForwardCorrelation/` (¿el in-sample predice el out-of-sample?) y su CSCV (¿mi forma
de elegir parámetros sobreajusta?).

Los dos estudios comparten configuración a propósito: leen el mismo panel y la misma equity diaria
del mismo lote. Si cada uno tuviera su bloque en `assets/_build.yaml` serían dos lotes distintos y
sus respuestas ya no hablarían del mismo objeto. Por eso hay **un solo bloque `wfc:`**.

### Cuándo lo usas, y cuándo no

Después de fabricar el lote de variantes (`/variants`, paso 16.5) y antes de correrlo. Nunca antes:
las variantes son los ficheros que se van a retestear.

⚠️ **Gasta `oos2`.** `assets/_policy.yaml` reserva ese tramo al WFC y a la WFM, y cada mirada lo
gasta. Esto es el WFC, así que es uno de sus dos consumidores legítimos — pero no se corre "para ver
qué sale", y el paso 19 sigue sin poder leerse hasta que 17, 18 y 19 estén los tres hechos.

### Antes de empezar

1. El proyecto tiene que ser **custom**, clonado con `sqx/projects/builder.py`, nunca el `Retester`
   de serie (regla dura 10).
2. El proyecto tiene que estar **cerrado**: SQX reescribe el `.cfx` al salir y se pierde el cambio
   en silencio (regla dura 4). El comando lo comprueba y se niega.
3. `python3 -m core.assets XAUUSD` en verde (regla dura 5).

### Cómo se ejecuta

```bash
python3 -m sqx.projects.wfc XAUUSD \
    --cfx ~/Desktop/SQX_w2/user/projects/XAUUSD_WFC/project.cfx \
    --timeframe M30 \
    --tasks Retest-Task1.xml,Retest-Task2.xml,Retest-Task5.xml
```

| flag | obligatorio | qué hace |
|---|---|---|
| `--cfx` | sí | el proyecto custom donde se escriben las tres tareas |
| `--timeframe` | sí | el timeframe del proyecto; es el que llevan los mercados adicionales |
| `--tasks` | sí | tres ficheros de tarea **en el orden de `wfc.tasks`**: build, oos1, oos2. Se les cambia el título al de la doctrina y se activan |
| `--json` | no | la misma salida en JSON |

Salida real sobre una copia del donante congelado:

```
XAUUSD  XAUUSD  <- WFC Variants (las tres leen el MISMO lote)
  ✓ WFC 1 IS     build 2008.01.01→2017.12.31  -> WFC Build  1 condicion(es) apagada(s)
      mercados: XAGUSD_DukasM1_Infinox, BRENTCMDUSD_ftmo
  ✓ WFC 2 OOS1   oos1  2018.01.01→2022.12.31  -> WFC OOS1   1 condicion(es) apagada(s)
      mercados: XAGUSD_DukasM1_Infinox, BRENTCMDUSD_ftmo
  ✓ WFC 3 OOS2   oos2  2023.01.01→2026.08.30  -> WFC OOS2   1 condicion(es) apagada(s)
      mercados: XAGUSD_DukasM1_Infinox, BRENTCMDUSD_ftmo
```

### Por qué tres tareas y no una

Una sola tarea de 2008 a 2026 llevaría **un** spread y **un** slippage para los dieciocho años, y
habría que elegir cuál miente menos. Con tres, cada tramo cobra lo suyo: comprobado en el `.cfx`
escrito, la tarea de `build` sale con spread 11.0 en la plata y slippage 2.5, y la de `oos2` con
22.0 y 5.

Y además sale gratis en información. Las tres leen el **mismo** databank de entrada (`WFC Variants`)
y cada una escribe el suyo (`WFC Build`, `WFC OOS1`, `WFC OOS2`), así que el corte in-sample /
out-of-sample deja de ser una fecha dentro de una curva y pasa a ser **de qué tarea vino** cada
curva. El `<OutOfSample>` de cada tarea se vacía justamente por eso: una tarea que corrió un tramo
entero *es* una muestra.

### Los mercados adicionales van dentro

`markets: true` en la doctrina. Cada una de las tres tareas lleva también el crosscheck
`RetestOnAdditionalMarkets` con los mercados de `assets/_markets.yaml`, cada uno con **sus** costes
y recortado a su `data_from` si empieza más tarde que el tramo — en la tarea de `build`, el Brent
corre 2013→2017 y la plata 2008→2017.

Son los **crossmarkets**, no los crossTF: un timeframe reescalado es la misma serie de precios
remuestreada, así que no añade grados de libertad a un CSCV.

⚠️ **El coste se multiplica por (1 + nº de mercados).** Con XAUUSD y sus dos mercados family, las
tres tareas son **nueve** backtests por variante. Mira el tamaño del lote antes de arrancar.

### Aquí tampoco se filtra nada

`wfc.conditions: []`. El comando apaga todas las condiciones de aceptación del crosscheck, fuerza
`DeleteFailedStrategies` a false y pone `retestSelected="false"`, y dice cuántas apagó. Una variante
descartada y una variante que perdió dinero son la misma cosa para el que cuenta, y entonces el PBO
no significa nada.

### Qué hay que hacer a mano todavía

Los tres databanks tienen que **existir** en el proyecto (`WFC Variants`, `WFC Build`, `WFC OOS1`,
`WFC OOS2`): SQX empareja por el nombre exacto y **ignora en silencio** un databank que ningún
`<Databank>` del `config.xml` declara. Créalos en la GUI del proyecto custom antes de correr nada, o
clona un donante que ya los lleve.

### Qué NO hace

No carga las variantes, no arranca el custodio y no cosecha nada. Eso es `/variants` y
`sqx/variants/execute.py`. Esto sólo deja el proyecto escrito.
