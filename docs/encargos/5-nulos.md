# 5 · Nulos de entrada aleatoria — lo construido, lo medido y lo que queda

Encargo cerrado el 2026-09-22. Nace de una pregunta del dueño: **¿cómo sé que una estrategia tiene
suficientes operaciones para que su resultado no sea suerte?** — el test que Marty Tinsley describe
en un podcast, generando curvas de equity aleatorias y viendo cuántas operaciones hacen falta para
que una con ventaja se despegue del ruido.

Lo entregado es `nulls/`, su página de manual (`docs/manual/26-nulos.md`) y siete hechos medidos
que están en `knowhow/research/random-entry-nulls.md` y `knowhow/export/`. **Donde este documento y
`knowhow/` discrepen, manda `knowhow/`.**

---

## 1 · Por qué el test de Tinsley no se implementó tal cual

Su generador es sintético: ±1R, p=0.5, media cero por construcción. Comparado contra su propio
generador al 55/45 es impecable, y su conclusión —hacen falta ~600 operaciones para ver un edge
del 10 % con potencia del 80 %— es correcta. **Es un estudio de potencia.**

Deja de valer en cuanto se le enchufa una estrategia real, por dos motivos:

- Tus operaciones no son apuestas justas de ±1R.
- El oro no es driftless. Un mono entrando al azar en XAUUSD **no** tiene retorno cero.

De ahí la decisión de diseño que gobierna todo el módulo: **el null no es una moneda, es un mono
con tu mismo conjunto de oportunidades** — mismas velas, misma ventana, mismos costes, misma
huella de trading — que decide al azar solo aquello que se está poniendo a prueba.

## 2 · La idea que ordena el módulo

> **Lo que le dejas fijo al null, se lo regalas.**

Un null no mide edge: lo **atribuye**. Empareja todo y el null es tu estrategia (p = 0.5, no has
medido nada). Empareja nada y es el mono. La diferencia entre dos peldaños consecutivos es lo que
valía ese canal. Por eso `model.RANDOMISES` es una tabla y no un comentario, y por eso el informe
emite una escalera y no un número.

| peldaño | aleatoriza |
|---|---|
| `timing` | cuándo entra cada operación |
| `timing_holds` | cuándo entra, y cuánto aguanta |
| `timing_sizing` | cuándo entra, y el tamaño por volatilidad |
| `free` | cuándo, cuánto y cuán grande — solo sobreviven el número de operaciones y el coste |

## 3 · Lo que se midió, y las dos veces que me equivoqué

**Error 1 — supuse que el mono heredaría la deriva del oro y sería el listón duro.** Falso. Con
ocupación del 7,4 %, el mono captura ~2.867 $ de la subida y paga ~7.756 $ de coste: pierde. Su
media es negativa en el **100 %** de las 757 estrategias. Batir al mono es un listón **más bajo**
que batir a cero.

**Error 2 — concluí que MinTRL domina al mono y que el mono era redundante.** Era un artefacto de
haber elegido el Sharpe, que es invariante de escala. El dueño lo vio antes que yo: las dos
poblaciones de operaciones **no son la misma**.

| por operación | estrategia | mono |
|---|---|---|
| desviación | 491 $ | 661 $ (36 % más volátil) |
| skew | +0.53 | −0.78 |
| curtosis | 6.4 | 27.0 |

`mean/std` divide fuera justo esa diferencia. Con otro estadístico el veredicto se mueve entre 40
y 85 puntos, de la misma simulación:

| estadístico | pasan a p<0.05 |
|---|---|
| `dd` | 84.5 % |
| `sharpe` | 77.4 % |
| `retdd` | 76.9 % |
| `pf` | 55.2 % |
| `net` | **39.5 %** |

**La elección del estadístico decide el veredicto más que la elección del null.** El módulo
imprime cinco y no elige.

Y contra MinTRL (202/757 = 26,7 %): con `sharpe` la contención es total (0 excepciones, es el
mismo eje con otro centrado), con `net` **los dos tests se cruzan en las dos direcciones** — 48
pasan MinTRL y fallan el mono, 145 al revés. Miden cosas distintas.

## 4 · El hallazgo que salvó el estudio

La puerta de reconciliación saltó en la primera corrida: 0.87–0.91 contra un suelo de 0.99. **SQX
rellena a la apertura de la vela, no al cierre**, en la entrada y en la salida. `open-open`
reconcilia a **1.0000** y la segunda mejor convención a 0.9629.

Con el fill equivocado, `net` daba 21,5 % en vez de 39,5 %. Un 4-13 % de correlación perdida movía
el veredicto 18 puntos **sin que nada saltara**, salvo esa puerta. Es la razón de que
`calibrate.convention()` mida el relleno por estrategia en lugar de suponerlo.

## 5 · Dónde encaja en el flujo

Se evaluaron cinco sitios. Sobreviven dos, y el dueño eligió el primero:

- **P1 · tras el OOS, sobre la población** — la criba. Corre antes de que el pipeline arranque, así
  que lo que muere no consume ni un minuto de `sppultra` ni de las 5.000 variantes. Es además el
  único sitio donde existen las cantidades de población (supervivencia, dispersión transversal,
  corrección por multiplicidad) que cualquier umbral necesita.
- **P2 · `pipeline`, antes de `sppultra`** — tres líneas de `must:` en `recipe.yaml` reusando el
  mismo módulo, **cuando P1 haya fijado el umbral**. No es un segundo desarrollo.

Descartados: **P0** (generación IS: el null está contaminado y `M` no se conoce), **P3** (sobre las
5.000 variantes: una vecindad de parámetros de una estrategia con edge no es un mono, y eso ya lo
contestan `sppUltra` y `walkForwardCorrelation`), **P4** (portfolio: aleatorizar una cartera es
aleatorizar qué entra y con qué peso, otro objeto, se diseña cuando exista la cartera).

**Muestras.** La puerta corre sobre `oos1` y solo `oos1`. La escalera de atribución puede correr
también sobre IS, porque atribuir necesita potencia (el doble de operaciones) y porque la selección
infló el **nivel** en IS pero no obviamente **de qué canal** venía el edge. `oos2` no se toca:
`assets/_policy.yaml` lo reserva a WFC/WFM y cada mirada lo gasta — lo que deja un holdout limpio
para confirmar lo que P1 seleccione.

## 6 · Lo que queda

1. **El export completo de operaciones.** Hoy el módulo corre sobre las 757 de `MC_Trades`. Para
   las 10.000 hay que exportarlas: ~265 MB de Parquet (nada), pero el tiempo de `orderstocsv` en
   SQX **no está medido** y es lo único sin cuantificar del plan.
2. ~~El punto de entrada de P1~~ **construido 2026-09-23**: `engines/inference/excess.py` +
   `tasks/reports/nulls.py`. Reporta observado contra esperado por azar, el exceso, la estimación
   de Storey, cuántas son nombrables bajo Benjamini-Hochberg, y detecta solo si la muestra fue
   preseleccionada. ⚠️ Corrido sobre `MC Trades` salta ese aviso: el 100 % de esas 757 gana dinero
   en OOS1, porque descienden de la tarea #2 del proyecto, que lleva tres condiciones de
   aceptación sobre `main/OOS`. **El exceso ahí mide el filtro, no el generador.** Queda
   pendiente de una databank sin esas condiciones.
3. **El período del ATR desde el `.sqx`**, para que el peldaño con sizing emparejado recalcule
   `c/ATR(entrada aleatoria)` en vez de reutilizar el tamaño real — que hoy filtra un poco de
   cuándo eligió entrar la estrategia. `CV(Size × ATR)` baja de 0.38 a 0.12 y nunca a 0: la familia
   está identificada, los parámetros no.
4. **Calibrar `barrier.intrabar` el día que haya SL/TP.** El escaneo está probado contra un bucle
   explícito (0 discrepancias sobre barreras sintéticas), pero *qué barrera gana cuando una vela
   toca las dos* no se puede leer de un corpus que no lleva barreras.
5. **Los issues 17 y 18 de `OPEN.md`**, que son para `crossmarket`, `monteCarlo` y `retest`.
   Módulos terminados: cambiar lo que reporta un estudio cerrado es decisión del dueño.

## 6bis · El hallazgo que condiciona el punto 2

🔬 Leído del `.cfx` el 2026-09-23 (solo lectura). La cadena del proyecto XAUUSD:

```
#1 Build   -> 'Results'    25 condiciones,  0 sobre main/OOS
#2 Retest  -> 'OOS'        24 condiciones,  3 sobre main/OOS   <-- aqui
#4 Retest  -> 'MC Trades'  21 condiciones,  0 sobre main/OOS
```

Las tres: `AnnualPctReturn(OOS) > 0`, `AnnualPctReturn(OOS) > AnnualPctReturn(IS)` y
`DrawdownPct(OOS) < DrawdownPct(IS)`. Todo lo que viene después desciende de ahí, y se ve en los
datos: `MC_Trades` tiene el **99,9 %** de sus 757 con beneficio OOS positivo, mientras que el
export de métricas de la databank `OOS` (10.000 filas, 2026-09-03) solo el **26,9 %**.

No es un problema de configuración — es saber qué población es cuál. `tasks/reports/nulls.py`
lo detecta por su cuenta desde los datos, porque la configuración dice lo que la tarea hace **hoy**
y la databank se llenó cuando se llenó.

## 7 · Coste

757 estrategias × 4 peldaños × 2.500 tiradas: **2 min 37 s**. Extrapolado a 10.000: ~35 minutos.
No toca SQX. El sizing no compone sobre el equity, así que los runs no tienen dependencia
secuencial y el problema es vergonzosamente paralelo — esa medida es la que permitió no escribir
un simulador trade a trade.
