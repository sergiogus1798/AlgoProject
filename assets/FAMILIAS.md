# Familias y paletas favorables por activo

Qué clase de estrategia tiene más a favor cada activo, **ordenada de más a menos favorable**, con qué
paleta de bloques construirla, **marco por marco** (M15, M30, H1, H4) y **junto a lo que dice la
bibliografía**. Lo que no llega al listón **no se lista** como favorable: aparece, si acaso, en «ni lo
intentes», o en la vista por marco con un «—» delante.

- **De dónde sale.** Del perfil de mercado (`studies/research/marketProfile/`, capítulo 82 del
  manual), ficheros `scores.csv` y `measures.csv` de `AlgoData/research/profiles/`. Las tablas las
  imprimen `python3 -m studies.research.marketProfile.report --favourable` (apartados 1, 2, 4, 5 y 6)
  y `--bibliography` (apartado 7). Los párrafos son juicio escrito a mano sobre esos números; lo que
  añade conocimiento de mercado va marcado *«criterio, no medido»* y nunca contradice una medida.
- **Estado:** generado el 2026-10-02 con el perfil **ampliado** de ese día: 19 activos, M15/M30/H1/H4,
  largo y corto, 7 familias (1.064 celdas-familia), **99 medidas** (las 31 originales más 68 nuevas:
  horizontes de semanas y meses, contexto de D1, régimen de volatilidad, salidas por objetivo y por
  trailing, y las reglas de la bibliografía) = **14.364 pruebas**, 3.000 sorteos por celda. Si se
  rehace el perfil, se rehace este documento.
- **Sin reloj.** Ninguna regla que necesite la hora, una franja de sesión, el día de la semana o el
  calendario entra en los rankings ni llega al tablero (tu decisión del 2026-10-02). Lo que se midió
  con reloj está en el apartado 6.3, para que no se pierda. La familia `sesion` queda representada
  sólo por su medida de precios (`prev_day_break`: máximo y mínimo del día anterior).
- **Contexto de D1.** Las medidas nuevas leen D1 como filtro desde M15-H4 (permitido): una vela sólo
  ve los días **ya cerrados**, nunca el suyo (`tests/test_marketprofile.py` lo comprueba).
- **Claves literales** (para `grep`): los activos (`XAUUSD`), las familias (`tendencia`, `ruptura`,
  `reversion`, `momentum`, `volatilidad`, `patron`, `sesion`), las paletas
  (`sqx/blocks/palettes/<nombre>.yaml`) y los identificadores de la bibliografía (`REV-37a`).

## Avisos — léelos una vez

1. **Todo es dentro de muestra.** Sólo el tramo `build` de cada activo (2008-2017 en forex y
   metales; hacia 2012-2019 en índices y crudos). Nunca `oos1` ni `oos2`.
2. **Nadie ha comprobado aún que el perfil prediga supervivientes.** Dice dónde hay estructura en
   el precio, no qué plantilla sobrevive.
3. **La familia `volatilidad` no informa por su puntuación** (~33 en casi todas las celdas: la nula
   no conserva el agrupamiento de la volatilidad). Sólo cuentan sus medidas con operaciones.
4. **Los costes de `XAGUSD`, `UKOIL` y `USOIL` son provisionales**; su «efecto en × coste» se moverá.
5. **El efecto de los largos es bruto de deriva.** La p la descuenta (la nula tiene la misma
   deriva); el múltiplo no. En índices (deriva de +7 a +16 % al año en build) casi cualquier largo
   mantenido días «paga» 5-30× el coste: mira la p, no el múltiplo. Tampoco incluye el swap, y las
   reglas nuevas que mantienen días pasan noches.
6. **Una fila habla por la medida líder de la familia en esa celda** (la que mejor paga entre las
   que pasan; si ninguna pasa, la de p corregida más pequeña).
7. **Las operaciones al año de las medidas originales `look*` y `channel*` cuentan señales
   solapadas**, no operaciones de una estrategia; las medidas nuevas llevan una posición a la vez.

## La nota

Cuatro filtros del perfil, leídos de la medida líder: **significativa** (p corregida por
Benjamini-Hochberg ≤ 0,05 sobre las 14.364 pruebas), **paga** (efecto medio ≥ 2× el coste de ida y
vuelta), **estable** (signo bueno en más de la mitad de los años) y **frecuente** (≥ 40 operaciones
al año; tu mínimo).

| nota | qué exige | cómo leerla |
|---|---|---|
| **A** | los cuatro filtros | celda donde pedir una idea ya |
| **B** | significativa y paga ≥ 2×, pero **pocas operaciones** o **frágil** (se dice cuál) | el efecto es real; así medido no da para una estrategia |
| **C** | estable y frecuente, con **una** flaqueza: significativa pero paga entre 1× y 2×; o paga ≥ 2× con p cruda ≤ 0,05 que no sobrevive a la corrección | sugerente. Un build aquí es una apuesta, no una consecuencia |
| — | todo lo demás | **no se lista** (pero se ve en la vista por marco) |

Orden dentro de un activo: la nota; a igual nota, primero lo significativo; después el múltiplo.

**«Ni lo intentes»** (medido, familias sin ninguna celda con nota en ese activo):
`estructura real que no paga el coste` — significativa pero el efecto no llega a 0,5× el coste, en
al menos la mitad de las celdas; `ninguna celda llega a medio coste`; `signo contrario` — p cruda
≥ 0,95 y efecto ≤ −1× el coste, sólo en las celdas que se nombran.

## Las paletas

La **condición fija** de la plantilla sale de la paleta de la familia; el **hueco libre** sortea de
otras paletas según las dos reglas del director (`studies/research/board/config.yaml`):
ortogonalidad (peso 3), tendencia con contratendencia y nunca dos iguales (peso 2), mismo dato con
otra lectura (peso 1). `sesion_base` es desde hoy una paleta **sin reloj** (rango y apertura de la
sesión y niveles del día leídos como precios). El detalle bloque a bloque:
`python3 -m studies.research.board.palette <familia>`. Una sola dirección por plantilla y todo a mercado.

| familia de la condición fija | su paleta | el hueco libre sortea de (peso) |
|---|---|---|
| `ruptura` | `ruptura_base_v2` | sesion_base (3), volatilidad_base (3), reversion_base_v2 (2), patron_base (1) |
| `reversion` | `reversion_base_v2` | sesion_base (3), volatilidad_base (3), momentum_base (2), ruptura_base_v2 (2), tendencia_base_v2 (2), patron_base (1) |
| `tendencia` | `tendencia_base_v2` | sesion_base (3), volatilidad_base (3), reversion_base_v2 (2), patron_base (1) |
| `momentum` | `momentum_base` | sesion_base (3), volatilidad_base (3), reversion_base_v2 (2), patron_base (1) |
| `volatilidad` | `volatilidad_base` | momentum_base (3), patron_base (3), reversion_base_v2 (3), ruptura_base_v2 (3), sesion_base (3), tendencia_base_v2 (3) |
| `patron` | `patron_base` | sesion_base (3), volatilidad_base (3), momentum_base (1), reversion_base_v2 (1), ruptura_base_v2 (1), tendencia_base_v2 (1) |
| `sesion` | `sesion_base` | momentum_base (3), patron_base (3), reversion_base_v2 (3), ruptura_base_v2 (3), tendencia_base_v2 (3), volatilidad_base (3) |


## 1. Resumen: activo → qué generar, según la prior y lo medido

Cada celda: familia principal / secundaria de la prior en ese marco, con su estado medido: ✔ a favor · ○ sin evidencia · ✖ en contra.

| activo | M15 | M30 | H1 | H4 | veredicto desnudo (nota) | barrido: variantes en meseta |
|---|---|---|---|---|---|---|
| `AUDJPY` | volatilidad ○ / ruptura ○ | ruptura ○ / momentum ○ | pullback ○ / momentum ○ | tendencia ○ / pullback ○ | nada favorable medido | ninguna |
| `AUDUSD` | reversion ✔ | reversion ✔ | reversion ✔ / pullback ○ | tendencia ○ / pullback ○ | reversion (B, H4 short) | ninguna |
| `CADJPY` | volatilidad ○ / ruptura ○ | ruptura ○ / momentum ○ | pullback ○ / momentum ✖ | tendencia ○ / pullback ○ | nada favorable medido | ninguna |
| `DAX40` | ruptura ○ / volatilidad ✖ | ruptura ○ / volatilidad ✖ | ruptura ○ / pullback ○ | tendencia ○ / pullback ○ | momentum (C, H4 long) | ninguna |
| `DJ30` | reversion ○ / volatilidad ✖ | reversion ○ / pullback ○ | pullback ○ / reversion ○ | pullback ○ / tendencia ○ | ruptura (A, H1 long), momentum (C, M30 short) | ninguna |
| `EURJPY` | volatilidad ○ / ruptura ○ | ruptura ○ / momentum ✔ | pullback ✔ / momentum ○ | tendencia ○ / pullback ○ | tendencia (C, H1 long), momentum (C, M30 long) | ninguna |
| `EURUSD` | reversion ✔ | reversion ✔ | reversion ✔ / pullback ○ | tendencia ○ / pullback ○ | momentum (A, M15 short), volatilidad (C, H4 short) | ninguna |
| `GBPJPY` | volatilidad ○ / ruptura ○ | ruptura ○ / momentum ○ | pullback ○ / momentum ✔ | tendencia ○ / pullback ○ | momentum (B, H1 long), ruptura (C, H1 long) | ninguna |
| `GBPUSD` | reversion ✖ / volatilidad ○ | ruptura ○ / reversion ✖ | pullback ○ / ruptura ○ | tendencia ○ / pullback ○ | nada favorable medido | ninguna |
| `NIKKEI225` | volatilidad ○ / reversion ○ | ruptura ○ / volatilidad ✖ | ruptura ○ / pullback ○ | tendencia ○ / ruptura ✔ | momentum (B, H4 long), ruptura (C, H4 long) | ninguna |
| `UKOIL` | sin prior | sin prior | sin prior | sin prior | nada favorable medido | ninguna |
| `USA500` | reversion ○ / volatilidad ○ | reversion ○ / pullback ○ | pullback ○ / reversion ✔ | pullback ○ / tendencia ○ | reversion (C, H1 long), momentum (C, M15 long) | ninguna |
| `USATEC` | ruptura ○ / reversion ○ | ruptura ○ / pullback ○ | pullback ○ / momentum ○ | momentum ○ / tendencia ○ | momentum (C, M15 long) | ninguna |
| `USDCAD` | reversion ✔ | reversion ✔ | reversion ✔ / pullback ○ | tendencia ○ / pullback ✔ | reversion (C, H1 long) | ninguna |
| `USDCHF` | sin prior | sin prior | sin prior | sin prior | momentum (B, H1 short) | ninguna |
| `USDJPY` | volatilidad ○ / ruptura ○ | ruptura ○ / momentum ✔ | pullback ○ / momentum ✔ | tendencia ○ / pullback ✔ | reversion (C, H1 long), momentum (C, M30 long) | ninguna |
| `USOIL` | sin prior | sin prior | sin prior | sin prior | nada favorable medido | ninguna |
| `XAGUSD` | reversion ○ | volatilidad ○ / reversion ○ | ruptura ○ / volatilidad ○ | ruptura ○ / tendencia ○ | momentum (B, H4 long) | ninguna |
| `XAUUSD` | volatilidad ○ / ruptura ○ | ruptura ✔ / volatilidad ○ | ruptura ✔ / pullback ○ | tendencia ○ / momentum ✔ | momentum (C, M15 long), ruptura (C, H1 long) | ninguna |

**Cómo leer esta tabla.** El orden lo pone **tu prior** (`AlgoData/research/literature/familias-por-activo-prior-2026-10-02.md`); lo medido la anota. Regla de la propia prior: *si la prior y el dato coinciden, genera esa familia; si discrepan, fíate del dato pero exige más evidencia fuera de muestra.* Lo «medido en contra» **no se quita**: se queda marcado, porque el conflicto es lo que hay que ver.

**Lo que hay que saber antes de leer nada más** (auditoría del 2026-10-02, `knowhow/research/market-profile-blind-spots.md`):

- **Veredicto desnudo:** 2 de 1.064 celdas-familia pasan los cuatro filtros con 14.364 pruebas (EURUSD M15 corto `momentum`; DJ30 H1 largo `ruptura` con filtro de tendencia D1). Con la corrección por familia pasan 4, todas de `reversion` (apartado 6.2).
- **Con salida razonable:** el barrido de 53.352 variantes (apartado 7) añade 3 variantes que pasan y **ninguna en meseta**. La salida fija desnuda no era lo que escondía los efectos.
- **Reversión: existe en todas partes y no paga.** Tres cierres seguidos en contra (`run3_fade`) es significativo en el 87 % de las celdas; RSI(2) con salida a la media, en el 63-68 % de M15-M30. El efecto mediano de lo significativo es 0,2× el coste (máximo 1,0×). Eso es «la reversión es menor que el spread», no «no hay reversión».
- **Tendencia: no aparece a ningún horizonte en un solo activo.** En las medidas de horizonte largo (100-200 velas, 20 a 252 días) la tasa de p cruda ≤ 0,05 es del 0,8 % (el azar da un 5 %). Mantenida semanas paga varias veces el coste, pero son 3-12 operaciones al año y no se distingue de la deriva.
- **Índices, compra de caídas en largo:** paga de 6 a 18× el coste en USA500, USATEC, DJ30 y NIKKEI225 (RSI(2) de D1 < 10 sobre SMA200), y es negativa en DAX40; son 5-8 operaciones al año y p cruda 0,07-0,17: visible en dinero, invisible en estadística con 8 años de un solo activo.


## 2. Al revés: familia → activos donde el veredicto desnudo le pone nota

| familia | activos donde aparece, el mejor primero |
|---|---|
| `ruptura` | DJ30 (A, H1 long, 3.1×), XAUUSD (C, H1 long, 3.7×), GBPJPY (C, H1 long, 3.2×), NIKKEI225 (C, H4 long, 2.2×) |
| `momentum` | EURUSD (A, M15 short, 2.3×), NIKKEI225 (B, H4 long, 25.8×), XAGUSD (B, H4 long, 4.9×), GBPJPY (B, H1 long, 3.9×), USDCHF (B, H1 short, 2.4×), DAX40 (C, H4 long, 4.0×), USDJPY (C, M30 long, 3.3×), USATEC (C, M15 long, 2.9×), USA500 (C, M15 long, 2.9×), EURJPY (C, M30 long, 2.6×), XAUUSD (C, M15 long, 1.5×), DJ30 (C, M30 short, 1.4×) |
| `reversion` | AUDUSD (B, H4 short, 9.4×), USA500 (C, H1 long, 3.1×), USDJPY (C, H1 long, 1.0×), USDCAD (C, H1 long, 1.0×) |
| `volatilidad` | EURUSD (C, H4 short, 3.8×) |
| `tendencia` | EURJPY (C, H1 long, 3.5×) |

## 3. Activo por activo

### `AUDJPY`

**Ranking según la prior, marco por marco, con lo medido al lado** (Alta antes que Media; a igual nivel, lo medido a favor antes; lo medido en contra se queda, marcado):

| marco | nº | familia | prior | estado | veredicto desnudo (mejor medida) | con salida razonable (barrido aparte) | cociente de varianzas frente a la familia principal |
|---|---|---|---|---|---|---|---|
| M15 | 1 | `ruptura` | secundaria; matriz: Alta | «sin evidencia medida» | short · `channel100_hold24` · 0.3× · p corr. 0.95 (cruda 0.193) · 340/año | no pasa: short · `channel_d` 20 · hold4x · 4.6× · meseta 2/3 · p 0.89 · 11/año | VR(8) 0.959, <1 en 9 de 10 años; VR(32) 0.920 — la prior no afirma signo |
| M15 | 2 | `volatilidad` | principal; matriz: Media | «sin evidencia medida» | short · `noise_k05_nr4` · 2.3× · p corr. 0.47 (cruda 0.038) · 21/año | — |  |
| M30 | 1 | `ruptura` | principal; matriz: Alta | «sin evidencia medida» | short · `channel55_trail` · 1.2× · p corr. 0.53 (cruda 0.046) · 86/año | no pasa: short · `channel_d` 55 · hold2x · 10.5× · meseta 2/3 · p 0.79 · 6/año | VR(8) 0.955, <1 en 9 de 10 años; VR(32) 0.935 — **discrepa** |
| M30 | 2 | `momentum` | secundaria; matriz: Alta | «sin evidencia medida» | long · `noise_k03` · 0.3× · p corr. 0.82 (cruda 0.123) · 146/año | no pasa: short · `big_bar` 2 · low20 · 0.2× · meseta 1/2 · p 0.89 · 70/año |  |
| H1 | 1 | `pullback` | principal; matriz: Alta | «sin evidencia medida» | long · `down3_up200_sma5` · 0.4× · p corr. 0.16 (cruda 0.008) · 161/año | no pasa: long · `pullback` 30 · trail2 · 1.2× · meseta 0/2 · p 0.30 · 85/año | VR(8) 0.938, <1 en 9 de 10 años; VR(32) 0.924 — la prior no afirma signo |
| H1 | 2 | `momentum` | secundaria; matriz: Alta | «sin evidencia medida» | long · `bar3atr` · 1.4× · p corr. 0.71 (cruda 0.083) · 9/año | no pasa: long · `big_bar` 3 · hold0.5x · 1.3× · meseta 0/2 · p 0.74 · 9/año |  |
| H4 | 1 | `tendencia` | principal; matriz: Alta | «sin evidencia medida» | short · `tsmom_d60_volup_run` · 23.2× · p corr. 0.92 (cruda 0.175) · 3/año | no pasa: short · `band` 1 · trail4 · 3.1× · meseta 2/3 · p 0.89 · 20/año | VR(8) 0.977, <1 en 8 de 10 años; VR(32) 0.933 — **discrepa** |
| H4 | 2 | `pullback` | secundaria; matriz: Alta | «sin evidencia medida» | short · `extreme2_up200` · 3.9× · p corr. 0.65 (cruda 0.066) · 13/año | no pasa: short · `pullback` 20 · hold4x · 5.3× · meseta 3/3 · p 0.87 · 13/año |  |

Paleta para `pullback`: tendencia_base_v2 (contexto) + reversion_base_v2 (disparo) — el contexto de tendencia como condición fija y el disparo de reversión en el hueco, por las dos reglas.

**Veredicto desnudo** (los cuatro filtros sobre la medida líder de cada una de las siete familias): nada con nota.

**Ni lo intentes (medido):** `patron` (estructura real que no paga el coste: 6 de 8 celdas, máximo 0.28×); `reversion` (estructura real que no paga el coste: 4 de 8 celdas, máximo 3.86×).

Coste/ATR: M15 0.34, M30 0.24, H1 0.17, H4 0.08 · deriva en build -1.1 %/año.

**Bibliografía que lo nombra:** `SES-33-fx-range-by-session` «descartado por usar reloj»; `CARRY-48-crash-asymmetry-short` «medido»; `CARRY-49-high-vix-then-long` «medido» — detalle en el apartado 8.

### `AUDUSD`

*Prior: fila «AUDUSD, NZDUSD, USDCAD» de la prior.*

**Ranking según la prior, marco por marco, con lo medido al lado** (Alta antes que Media; a igual nivel, lo medido a favor antes; lo medido en contra se queda, marcado):

| marco | nº | familia | prior | estado | veredicto desnudo (mejor medida) | con salida razonable (barrido aparte) | cociente de varianzas frente a la familia principal |
|---|---|---|---|---|---|---|---|
| M15 | 1 | `reversion` | principal; matriz: Media | «medido a favor (desnudo nota C)» | long · `ibs_low_1d` · 3.0× · p corr. 0.25 (cruda 0.015) · 55/año · nota C | no pasa: short · `ibs_low` 0.1 · hold2x · 3.8× · meseta 2/3 · p 0.86 · 23/año | VR(8) 0.936, <1 en 10 de 10 años; VR(32) 0.901 — **coincide** |
| M30 | 1 | `reversion` | principal; matriz: Media | «medido a favor (desnudo nota C)» | long · `ibs_low_1d` · 3.1× · p corr. 0.17 (cruda 0.009) · 55/año · nota C | no pasa: short · `ibs_low` 0.1 · hold2x · 4.0× · meseta 2/3 · p 0.76 · 23/año | VR(8) 0.929, <1 en 10 de 10 años; VR(32) 0.909 — **coincide** |
| H1 | 1 | `reversion` | principal; matriz: Media | «medido a favor (desnudo nota C)» | long · `ibs_low_1d` · 3.0× · p corr. 0.23 (cruda 0.014) · 55/año · nota C | no pasa: short · `ibs_low` 0.1 · hold2x · 4.0× · meseta 2/3 · p 0.80 · 23/año | VR(8) 0.932, <1 en 10 de 10 años; VR(32) 0.906 — **coincide** |
| H1 | 2 | `pullback` | secundaria; matriz: Media | «sin evidencia medida» | short · `rsi2_up200_sma5` · 0.7× · p corr. 0.41 (cruda 0.031) · 148/año | no pasa: long · `rsi_up100` 20 · mean5 · 0.5× · meseta 0/1 · p 0.23 · 261/año |  |
| H4 | 1 | `tendencia` | principal; matriz: Media | «sin evidencia medida» | long · `tsmom_d252_run` · 14.4× · p corr. 0.37 (cruda 0.027) · 3/año | no pasa: short · `tsmom_d` 60 · hold4x · 2.2× · meseta 1/3 · p 0.89 · 34/año | VR(8) 0.962, <1 en 8 de 10 años; VR(32) 0.933 — **discrepa** |
| H4 | 2 | `pullback` | secundaria; matriz: Media | «sin evidencia medida» | long · `extreme2_up200` · 5.1× · p corr. 0.21 (cruda 0.012) · 15/año | no pasa: short · `rsi_up100` 5 · hold1x · 2.1× · meseta 3/3 · p 0.89 · 21/año |  |
| H4 | 3 | `reversion` | no está en la celda de H4; matriz: Media | «medido a favor (desnudo nota B)» | short · `extreme3` · 9.4× · p corr. 0.04 (cruda 0.001) · 15/año · nota B | no pasa: short · `extreme` 3 · hold1x · 5.5× · meseta 3/3 · p 0.61 · 12/año |  |

Paleta para `pullback`: tendencia_base_v2 (contexto) + reversion_base_v2 (disparo) — el contexto de tendencia como condición fija y el disparo de reversión en el hueco, por las dos reglas.

**Veredicto desnudo** (los cuatro filtros sobre la medida líder de cada una de las siete familias):
1. **`reversion` — nota B** · H4 short · `extreme3` (cierre a 3 ATR de su media; en contra, 8 velas) · 9.36× el coste · p corr. 0.038 (cruda 0.001) · estabilidad 0.90 · 15 op/año · flaqueza: pocas operaciones  
   Paleta: `reversion_base_v2`. Hueco libre: sesion_base (3), volatilidad_base (3), momentum_base (2), ruptura_base_v2 (2), tendencia_base_v2 (2), patron_base (1).

**Ni lo intentes (medido):** `patron` (estructura real que no paga el coste: 7 de 8 celdas, máximo 0.42×).

Coste/ATR: M15 0.24, M30 0.17, H1 0.12, H4 0.06 · deriva en build -1.2 %/año.

**Bibliografía que lo nombra:** `TR-11-fitschen-d1-usd-pairs-trend` «medido»; `SES-31-fx-fix-reversals` «descartado por usar reloj»; `SES-33-fx-range-by-session` «descartado por usar reloj»; `CARRY-49-high-vix-then-long` «medido» — detalle en el apartado 8.

### `CADJPY`

*Prior: la prior no lo nombra: tratado como cruce del yen, como dice su grupo.*

**Ranking según la prior, marco por marco, con lo medido al lado** (Alta antes que Media; a igual nivel, lo medido a favor antes; lo medido en contra se queda, marcado):

| marco | nº | familia | prior | estado | veredicto desnudo (mejor medida) | con salida razonable (barrido aparte) | cociente de varianzas frente a la familia principal |
|---|---|---|---|---|---|---|---|
| M15 | 1 | `ruptura` | secundaria; matriz: Alta | «sin evidencia medida» | short · `channel100_hold24` · 0.3× · p corr. 0.97 (cruda 0.209) · 343/año | no pasa: short · `channel_d` 20 · hold2x · 5.9× · meseta 3/4 · p 0.82 · 14/año | VR(8) 0.944, <1 en 10 de 10 años; VR(32) 0.910 — la prior no afirma signo |
| M15 | 2 | `volatilidad` | principal; matriz: Media | «sin evidencia medida» | short · `noise_k05_nr4` · 1.9× · p corr. 0.54 (cruda 0.047) · 22/año | — |  |
| M30 | 1 | `ruptura` | principal; matriz: Alta | «sin evidencia medida» | short · `channel55_trail` · 0.7× · p corr. 0.97 (cruda 0.217) · 92/año | no pasa: short · `channel_d` 20 · hold2x · 5.7× · meseta 3/4 · p 0.82 · 14/año | VR(8) 0.945, <1 en 9 de 10 años; VR(32) 0.911 — **discrepa** |
| M30 | 2 | `momentum` | secundaria; matriz: Alta | «sin evidencia medida» | long · `noise_k05` · 1.0× · p corr. 0.28 (cruda 0.018) · 86/año | no pasa: long · `big_bar` 3 · hold1x · 1.3× · meseta 0/3 · p 0.32 · 25/año |  |
| H1 | 1 | `pullback` | principal; matriz: Alta | «sin evidencia medida» | long · `rsi2_up200_sma5` · 0.5× · p corr. 0.15 (cruda 0.008) · 154/año | no pasa: long · `rsi_up100` 10 · mean5 · 0.5× · meseta 0/2 · p 0.11 · 156/año | VR(8) 0.929, <1 en 9 de 10 años; VR(32) 0.920 — la prior no afirma signo |
| H1 | 2 | `momentum` | secundaria; matriz: Alta | «⚠️ **medido en contra**» | long · `noise_k03` · 0.7× · p corr. 0.32 (cruda 0.021) · 137/año | no pasa: short · `big_bar` 3 · hold2x · 1.8× · meseta 0/3 · p 0.89 · 16/año |  |
| H4 | 1 | `tendencia` | principal; matriz: Alta | «sin evidencia medida» | long · `chan_30_40_run` · 3.5× · p corr. 0.67 (cruda 0.073) · 10/año | no pasa: short · `tsmom_d` 60 · trail4 · 1.6× · meseta 1/3 · p 0.89 · 17/año | VR(8) 0.967, <1 en 7 de 10 años; VR(32) 0.955 — **discrepa** |
| H4 | 2 | `pullback` | secundaria; matriz: Alta | «sin evidencia medida» | short · `extreme2_up200` · 3.4× · p corr. 0.76 (cruda 0.099) · 13/año | no pasa: long · `pullback` 14 · trail2 · 3.1× · meseta 2/2 · p 0.61 · 24/año |  |

Paleta para `pullback`: tendencia_base_v2 (contexto) + reversion_base_v2 (disparo) — el contexto de tendencia como condición fija y el disparo de reversión en el hueco, por las dos reglas.

**Veredicto desnudo** (los cuatro filtros sobre la medida líder de cada una de las siete familias): nada con nota.

**Ni lo intentes (medido):** `patron` (estructura real que no paga el coste: 6 de 8 celdas, máximo 0.39×); `reversion` (estructura real que no paga el coste: 4 de 8 celdas, máximo 3.37×).

Coste/ATR: M15 0.31, M30 0.22, H1 0.15, H4 0.08 · deriva en build -2.4 %/año.

**Bibliografía que lo nombra:** `SES-33-fx-range-by-session` «descartado por usar reloj»; `REV-42-fitschen-fx-crosses-counter-trend` «medido»; `CARRY-48-crash-asymmetry-short` «medido»; `CARRY-49-high-vix-then-long` «medido» — detalle en el apartado 8.

### `DAX40`

**Ranking según la prior, marco por marco, con lo medido al lado** (Alta antes que Media; a igual nivel, lo medido a favor antes; lo medido en contra se queda, marcado):

| marco | nº | familia | prior | estado | veredicto desnudo (mejor medida) | con salida razonable (barrido aparte) | cociente de varianzas frente a la familia principal |
|---|---|---|---|---|---|---|---|
| M15 | 1 | `ruptura` | principal; matriz: Alta | «sin evidencia medida» | long · `channel200_hold48` · 2.9× · neto de deriva 2.2× · p corr. 0.67 (cruda 0.072) · 216/año | no pasa: long · `channel_d` 55 · trail4 · 4.2× · meseta 2/2 · p 0.64 · 21/año | VR(8) 0.954, <1 en 5 de 7 años; VR(32) 0.926 — **discrepa** |
| M15 | 2 | `volatilidad` | secundaria; matriz: Alta | «⚠️ **medido en contra**» | short · `noise_k05_nr4` · 0.9× · p corr. 0.99 (cruda 0.244) · 21/año | — |  |
| M30 | 1 | `ruptura` | principal; matriz: Alta | «sin evidencia medida» | long · `channel100_hold24` · 2.3× · neto de deriva 1.7× · p corr. 0.83 (cruda 0.126) · 160/año | no pasa: long · `channel_d` 55 · trail2 · 3.2× · meseta 2/2 · p 0.72 · 23/año | VR(8) 0.933, <1 en 4 de 7 años; VR(32) 0.933 — sin signo estable |
| M30 | 2 | `volatilidad` | secundaria; matriz: Alta | «⚠️ **medido en contra**» | short · `narrow_break` · 0.1× · p corr. 0.98 (cruda 0.234) · 477/año | — |  |
| H1 | 1 | `ruptura` | principal; matriz: Alta | «sin evidencia medida» | long · `channel55_up200` · 2.6× · neto de deriva 2.1× · p corr. 0.76 (cruda 0.099) · 40/año | no pasa: long · `channel` 55 · trail4 · 2.4× · meseta 3/3 · p 0.89 · 34/año | VR(8) 0.945, <1 en 4 de 7 años; VR(32) 0.934 — sin signo estable |
| H1 | 2 | `pullback` | secundaria; matriz: Media | «sin evidencia medida» | short · `extreme2_up200_mean` · 3.2× · p corr. 0.78 (cruda 0.108) · 29/año | no pasa: long · `rsi_up200` 10 · hold4x · 0.5× · meseta 2/3 · p 0.90 · 54/año |  |
| H4 | 1 | `tendencia` | principal; matriz: Media | «sin evidencia medida» | short · `fast_d5_20_quiet_run` · 24.8× · p corr. 0.66 (cruda 0.069) · 5/año | no pasa: long · `band` 1 · hold2x · 5.8× · meseta 4/4 · p 0.89 · 47/año | VR(8) 0.965, <1 en 6 de 7 años; VR(32) 0.941 — **discrepa** |
| H4 | 2 | `pullback` | secundaria; matriz: Media | «sin evidencia medida» | short · `rsi2_up200_sma5` · 4.0× · p corr. 0.65 (cruda 0.068) · 26/año | no pasa: long · `pullback` 20 · trail2 · 4.5× · meseta 3/3 · p 0.89 · 20/año |  |

Paleta para `pullback`: tendencia_base_v2 (contexto) + reversion_base_v2 (disparo) — el contexto de tendencia como condición fija y el disparo de reversión en el hueco, por las dos reglas.

**Veredicto desnudo** (los cuatro filtros sobre la medida líder de cada una de las siete familias):
1. **`momentum` — nota C** · H4 long · `bar1atr` (vela de cuerpo > 1 ATR; a favor, 4 velas) · 4.01× el coste · p corr. 0.412 (cruda 0.031) · estabilidad 0.86 · 77 op/año · flaqueza: no significativa tras corregir  
   Paleta: `momentum_base`. Hueco libre: sesion_base (3), volatilidad_base (3), reversion_base_v2 (2), patron_base (1).

**Ni lo intentes (medido):** `patron` (estructura real que no paga el coste: 6 de 8 celdas, máximo 0.50×).

Coste/ATR: M15 0.18, M30 0.12, H1 0.09, H4 0.04 · deriva en build +6.8 %/año.

**Bibliografía que lo nombra:** `MOM-21b-noise-area-clock-free` «medido»; `MOM-23-opening-gap-eurostoxx` «descartado por usar reloj»; `SES-29-overnight-vs-intraday-indices` «descartado por usar reloj»; `REV-36a-index-daily-ar1` «medido»; `REV-36c-index-weekly-ar1` «medido»; `REV-37a-ibs-long` «medido»; `REV-38b-rsi2-intraday-bars` «medido» — detalle en el apartado 8.

### `DJ30`

**Ranking según la prior, marco por marco, con lo medido al lado** (Alta antes que Media; a igual nivel, lo medido a favor antes; lo medido en contra se queda, marcado):

| marco | nº | familia | prior | estado | veredicto desnudo (mejor medida) | con salida razonable (barrido aparte) | cociente de varianzas frente a la familia principal |
|---|---|---|---|---|---|---|---|
| M15 | 1 | `reversion` (largo) | principal; matriz: Alta | «sin evidencia medida» | long · `extreme2_voldn_mean` · 0.8× · neto de deriva 0.5× · p corr. 0.74 (cruda 0.095) · 163/año | no pasa: long · `ibs_low` 0.2 · hold2x · 4.9× · meseta 4/4 · p 0.89 · 33/año | VR(8) 0.991, <1 en 4 de 7 años; VR(32) 1.004 — sin signo estable |
| M15 | 2 | `volatilidad` | secundaria; matriz: Media | «⚠️ **medido en contra**» | long · `noise_k05_nr4` · 4.5× · neto de deriva 3.7× · p corr. 0.30 (cruda 0.020) · 22/año | — |  |
| M30 | 1 | `reversion` (largo) | principal; matriz: Alta | «sin evidencia medida» | long · `extreme2_voldn_mean` · 2.0× · neto de deriva 1.4× · p corr. 0.42 (cruda 0.033) · 86/año | no pasa: long · `ibs_low` 0.2 · hold2x · 5.0× · meseta 4/4 · p 0.89 · 33/año | VR(8) 0.999, <1 en 5 de 7 años; VR(32) 1.005 — **coincide** |
| M30 | 2 | `pullback` (largo) | secundaria; matriz: Alta | «sin evidencia medida» | long · `connors_d1` · 11.2× · neto de deriva 6.4× · p corr. 0.90 (cruda 0.164) · 8/año | no pasa: long · `rsi_up200` 5 · trail4 · 1.7× · meseta 0/2 · p 0.89 · 130/año |  |
| H1 | 1 | `pullback` (largo) | principal; matriz: Alta | «sin evidencia medida» | long · `connors_d1` · 12.3× · neto de deriva 7.6× · p corr. 0.83 (cruda 0.129) · 8/año | no pasa: long · `rsi_up200` 10 · trail4 · 2.9× · meseta 2/3 · p 0.89 · 70/año | VR(8) 0.996, <1 en 5 de 7 años; VR(32) 0.951 — la prior no afirma signo |
| H1 | 2 | `reversion` (largo) | secundaria; matriz: Alta | «sin evidencia medida» | long · `weak_d20_mean` · 27.5× · neto de deriva 14.2× · p corr. 0.81 (cruda 0.119) · 9/año | no pasa: long · `ibs_low` 0.2 · hold2x · 4.2× · meseta 4/4 · p 0.89 · 33/año |  |
| H1 | 3 | `ruptura` | no está en la celda de H1; matriz: Media | «medido a favor (desnudo nota A)» | long · `channel55_up200` · 3.1× · neto de deriva 2.6× · p corr. 0.03 (cruda 0.001) · 71/año · nota A | no pasa: long · `channel_d` 20 · hold2x · 7.8× · meseta 4/4 · p 0.52 · 23/año |  |
| H4 | 1 | `pullback` (largo) | principal; matriz: Alta | «sin evidencia medida» | long · `connors_d1` · 12.3× · neto de deriva 7.6× · p corr. 0.84 (cruda 0.134) · 8/año | no pasa: long · `pullback` 20 · stop2_hold2x · 4.9× · meseta 2/2 · p 0.89 · 30/año | VR(8) 0.950, <1 en 4 de 7 años; VR(32) 0.892 — la prior no afirma signo |
| H4 | 2 | `tendencia` | secundaria; matriz: Media | «sin evidencia medida» | long · `fast_d5_20_run` · 44.9× · neto de deriva 24.9× · p corr. 0.67 (cruda 0.073) · 8/año | no pasa: long · `band` 1 · hold1x · 3.8× · meseta 4/4 · p 0.86 · 82/año |  |

Paleta para `pullback`: tendencia_base_v2 (contexto) + reversion_base_v2 (disparo) — el contexto de tendencia como condición fija y el disparo de reversión en el hueco, por las dos reglas.

**Veredicto desnudo** (los cuatro filtros sobre la medida líder de cada una de las siete familias):
1. **`ruptura` — nota A** · H1 long · `channel55_up200` (entra: cierre sobre el máximo de 55 velas y cierre D1 sobre su SMA200; sale: 8 velas (escrita para largos; en corto, su espejo)) · 3.14× el coste · p corr. 0.030 (cruda 0.001) · estabilidad 1.00 · 71 op/año · también: M30 long C 3.4×; M15 long C 3.1×  
   Paleta: `ruptura_base_v2`. Hueco libre: sesion_base (3), volatilidad_base (3), reversion_base_v2 (2), patron_base (1).
2. **`momentum` — nota C** · M30 short · `bar2atr` (vela de cuerpo > 2 ATR; a favor, 4 velas) · 1.45× el coste · p corr. 0.021 (cruda 0.001) · estabilidad 0.71 · 141 op/año · flaqueza: paga 1-2× · también: M30 long C 3.9×  
   Paleta: `momentum_base`. Hueco libre: sesion_base (3), volatilidad_base (3), reversion_base_v2 (2), patron_base (1).

**Ni lo intentes (medido):** `patron` (estructura real que no paga el coste: 5 de 8 celdas, máximo 0.18×).

Coste/ATR: M15 0.23, M30 0.16, H1 0.11, H4 0.06 · deriva en build +10.2 %/año.

**Bibliografía que lo nombra:** `MOM-21b-noise-area-clock-free` «medido»; `SES-29-overnight-vs-intraday-indices` «descartado por usar reloj»; `REV-36a-index-daily-ar1` «medido»; `REV-37a-ibs-long` «medido»; `REV-37b-ibs-short` «medido»; `REV-38b-rsi2-intraday-bars` «medido» — detalle en el apartado 8.

### `EURJPY`

**Ranking según la prior, marco por marco, con lo medido al lado** (Alta antes que Media; a igual nivel, lo medido a favor antes; lo medido en contra se queda, marcado):

| marco | nº | familia | prior | estado | veredicto desnudo (mejor medida) | con salida razonable (barrido aparte) | cociente de varianzas frente a la familia principal |
|---|---|---|---|---|---|---|---|
| M15 | 1 | `ruptura` | secundaria; matriz: Alta | «sin evidencia medida» | long · `donchian_d20_opp` · 14.6× · p corr. 0.81 (cruda 0.119) · 5/año | no pasa: long · `channel_d` 55 · hold1x · 7.6× · meseta 3/3 · p 0.02 · 13/año | VR(8) 0.963, <1 en 8 de 10 años; VR(32) 0.926 — la prior no afirma signo |
| M15 | 2 | `volatilidad` | principal; matriz: Media | «sin evidencia medida» | long · `donchian_d20_squeeze` · 6.2× · p corr. 1.00 (cruda 0.263) · 5/año | — |  |
| M30 | 1 | `momentum` | secundaria; matriz: Alta | «medido a favor (desnudo nota C)» | long · `bar2atr_trail` · 2.6× · p corr. 0.07 (cruda 0.003) · 72/año · nota C | no pasa: long · `big_bar` 2 · trail2 · 1.8× · meseta 2/3 · p 0.23 · 81/año | VR(8) 0.973, <1 en 8 de 10 años; VR(32) 0.935 — **discrepa** |
| M30 | 2 | `ruptura` | principal; matriz: Alta | «sin evidencia medida» | long · `channel55_up200` · 0.7× · p corr. 0.38 (cruda 0.028) · 88/año | no pasa: long · `channel_d` 55 · hold1x · 7.0× · meseta 3/3 · p 0.15 · 13/año |  |
| H1 | 1 | `pullback` | principal; matriz: Alta | «medido a favor (desnudo nota C)» | long · `pullback_mom60_trail` · 3.5× · p corr. 0.11 (cruda 0.005) · 58/año · nota C | no pasa: long · `pullback` 20 · trail4 · 4.9× · meseta 3/3 · p 0.33 · 42/año | VR(8) 0.939, <1 en 8 de 10 años; VR(32) 0.915 — la prior no afirma signo |
| H1 | 2 | `momentum` | secundaria; matriz: Alta | «sin evidencia medida» | long · `bar2atr_up200` · 2.4× · p corr. 0.09 (cruda 0.004) · 21/año | no pasa: long · `big_bar` 3 · hold1x · 3.8× · meseta 2/3 · p 0.29 · 10/año |  |
| H4 | 1 | `tendencia` | principal; matriz: Alta | «sin evidencia medida» | long · `tsmom_d60_run` · 16.9× · p corr. 0.67 (cruda 0.073) · 7/año | no pasa: short · `tsmom_d` 60 · trail4 · 14.1× · meseta 3/3 · p 0.81 · 14/año | VR(8) 0.953, <1 en 7 de 10 años; VR(32) 0.929 — **discrepa** |
| H4 | 2 | `pullback` | secundaria; matriz: Alta | «sin evidencia medida» | long · `extreme2_up200_mean` · 8.9× · p corr. 0.15 (cruda 0.008) · 11/año | no pasa: long · `rsi_up100` 10 · trail2 · 5.1× · meseta 3/3 · p 0.38 · 34/año |  |

Paleta para `pullback`: tendencia_base_v2 (contexto) + reversion_base_v2 (disparo) — el contexto de tendencia como condición fija y el disparo de reversión en el hueco, por las dos reglas.

**Veredicto desnudo** (los cuatro filtros sobre la medida líder de cada una de las siete familias):
1. **`tendencia` — nota C** · H1 long · `pullback_mom60_trail` (entra: el cierre vuelve a cruzar sobre su media de 20 y cierre D1 > el de hace 60 días; sale: trailing de 3 ATR de la vela (escrita para largos; en corto, su espejo)) · 3.51× el coste · p corr. 0.114 (cruda 0.005) · estabilidad 0.70 · 58 op/año · flaqueza: no significativa tras corregir  
   Paleta: `tendencia_base_v2`. Hueco libre: sesion_base (3), volatilidad_base (3), reversion_base_v2 (2), patron_base (1).
2. **`momentum` — nota C** · M30 long · `bar2atr_trail` (entra: vela con cuerpo > 2 ATR; sale: trailing de 3 ATR de la vela (escrita para largos; en corto, su espejo)) · 2.64× el coste · p corr. 0.066 (cruda 0.003) · estabilidad 0.70 · 72 op/año · flaqueza: no significativa tras corregir  
   Paleta: `momentum_base`. Hueco libre: sesion_base (3), volatilidad_base (3), reversion_base_v2 (2), patron_base (1).

**Ni lo intentes (medido):** `patron` (estructura real que no paga el coste: 6 de 8 celdas, máximo 0.89×); `reversion` sólo en M15 long; M30 short (estructura real que no paga el coste); `sesion` (ninguna celda llega a medio coste: 8 de 8 celdas, máximo -1.42×).

Coste/ATR: M15 0.22, M30 0.15, H1 0.11, H4 0.05 · deriva en build -1.9 %/año.

**Bibliografía que lo nombra:** `SES-33-fx-range-by-session` «descartado por usar reloj»; `CARRY-48-crash-asymmetry-short` «medido» — detalle en el apartado 8.

### `EURUSD`

**Ranking según la prior, marco por marco, con lo medido al lado** (Alta antes que Media; a igual nivel, lo medido a favor antes; lo medido en contra se queda, marcado):

| marco | nº | familia | prior | estado | veredicto desnudo (mejor medida) | con salida razonable (barrido aparte) | cociente de varianzas frente a la familia principal |
|---|---|---|---|---|---|---|---|
| M15 | 1 | `reversion` | principal; matriz: Alta | «medido a favor (desnudo nota C)» | short · `day_down_volhigh_1d` · 8.1× · p corr. 0.06 (cruda 0.002) · 46/año · nota C | no pasa: short · `ibs_low` 0.2 · trail2 · 0.9× · meseta 1/3 · p 0.65 · 298/año | VR(8) 0.976, <1 en 9 de 10 años; VR(32) 0.977 — **coincide** |
| M15 | 2 | `momentum` | no está en la celda de M15; matriz: Baja | «**la medida contradice la prior** — medido a favor (desnudo nota A)» | short · `bar3atr` · 2.3× · p corr. 0.02 (cruda 0.001) · 67/año · nota A | pico: short · `big_bar` 3 · hold1x · 2.4× · meseta 0/3 · p 0.02 · 64/año |  |
| M30 | 1 | `reversion` | principal; matriz: Alta | «medido a favor (desnudo nota C)» | short · `day_down_volhigh_1d` · 8.1× · p corr. 0.05 (cruda 0.002) · 46/año · nota C | no pasa: short · `ibs_low` 0.2 · hold0.5x · 1.7× · meseta 1/3 · p 0.84 · 110/año | VR(8) 0.994, <1 en 6 de 10 años; VR(32) 0.986 — **coincide** |
| H1 | 1 | `reversion` | principal; matriz: Alta | «medido a favor (desnudo nota C)» | short · `day_down_volhigh_1d` · 8.2× · p corr. 0.08 (cruda 0.003) · 46/año · nota C | no pasa: short · `rsi_low` 5 · hold2x · 2.8× · meseta 1/3 · p 0.40 · 156/año | VR(8) 0.984, <1 en 6 de 10 años; VR(32) 0.980 — **coincide** |
| H1 | 2 | `pullback` | secundaria; matriz: Media | «sin evidencia medida» | short · `down3_up200_sma5` · 1.4× · p corr. 0.16 (cruda 0.008) · 160/año | no pasa: short · `rsi_up200` 5 · hold2x · 3.3× · meseta 2/3 · p 0.65 · 72/año |  |
| H4 | 1 | `tendencia` | principal; matriz: Media | «sin evidencia medida» | long · `fast_d5_20_quiet_run` · 22.9× · p corr. 0.76 (cruda 0.099) · 6/año | no pasa: short · `band` 1 · hold4x · 8.2× · meseta 3/3 · p 0.89 · 35/año | VR(8) 1.009, <1 en 4 de 10 años; VR(32) 1.011 — **coincide** |
| H4 | 2 | `pullback` | secundaria; matriz: Media | «sin evidencia medida» | short · `extreme2_up200` · 7.3× · p corr. 0.84 (cruda 0.131) · 13/año | no pasa: short · `pullback` 20 · hold4x · 14.9× · meseta 3/3 · p 0.87 · 17/año |  |

Paleta para `pullback`: tendencia_base_v2 (contexto) + reversion_base_v2 (disparo) — el contexto de tendencia como condición fija y el disparo de reversión en el hueco, por las dos reglas.

**Veredicto desnudo** (los cuatro filtros sobre la medida líder de cada una de las siete familias):
1. **`momentum` — nota A** · M15 short · `bar3atr` (vela de cuerpo > 3 ATR; a favor, 4 velas) · 2.30× el coste · p corr. 0.021 (cruda 0.001) · estabilidad 0.80 · 67 op/año · también: H4 short C 5.1×; M30 short C 3.0×; H1 long C 2.1×  
   Paleta: `momentum_base`. Hueco libre: sesion_base (3), volatilidad_base (3), reversion_base_v2 (2), patron_base (1).
2. **`volatilidad` — nota C** · H4 short · `narrow_break` (ruptura de la vela más estrecha de 7, 4 velas) · 3.80× el coste · p corr. 0.538 (cruda 0.047) · estabilidad 0.90 · 62 op/año · flaqueza: no significativa tras corregir  
   Paleta: `volatilidad_base`. Hueco libre: momentum_base (3), patron_base (3), reversion_base_v2 (3), ruptura_base_v2 (3), sesion_base (3), tendencia_base_v2 (3).

**Ni lo intentes (medido):** `patron` (estructura real que no paga el coste: 6 de 8 celdas, máximo 0.87×); `sesion` (ninguna celda llega a medio coste: 8 de 8 celdas, máximo 0.24×).

Coste/ATR: M15 0.14, M30 0.10, H1 0.07, H4 0.03 · deriva en build -1.9 %/año.

**Bibliografía que lo nombra:** `TR-11-fitschen-d1-usd-pairs-trend` «medido»; `SES-31-fx-fix-reversals` «descartado por usar reloj»; `SES-33-fx-range-by-session` «descartado por usar reloj» — detalle en el apartado 8.

### `GBPJPY`

**Ranking según la prior, marco por marco, con lo medido al lado** (Alta antes que Media; a igual nivel, lo medido a favor antes; lo medido en contra se queda, marcado):

| marco | nº | familia | prior | estado | veredicto desnudo (mejor medida) | con salida razonable (barrido aparte) | cociente de varianzas frente a la familia principal |
|---|---|---|---|---|---|---|---|
| M15 | 1 | `ruptura` | secundaria; matriz: Alta | «sin evidencia medida» | long · `channel100_hold24` · 0.7× · p corr. 0.34 (cruda 0.024) · 364/año | no pasa: short · `channel_d` 20 · hold1x · 4.9× · meseta 4/4 · p 0.56 · 21/año | VR(8) 0.967, <1 en 9 de 10 años; VR(32) 0.942 — la prior no afirma signo |
| M15 | 2 | `volatilidad` | principal; matriz: Media | «sin evidencia medida» | long · `noise_k05_nr4` · 0.6× · p corr. 0.98 (cruda 0.233) · 20/año | — |  |
| M30 | 1 | `ruptura` | principal; matriz: Alta | «sin evidencia medida» | long · `channel55` · 0.8× · p corr. 0.05 (cruda 0.002) · 254/año | no pasa: short · `channel_d` 20 · hold1x · 4.3× · meseta 3/4 · p 0.74 · 20/año | VR(8) 0.991, <1 en 9 de 10 años; VR(32) 0.951 — **discrepa** |
| M30 | 2 | `momentum` | secundaria; matriz: Alta | «sin evidencia medida» | long · `bar2atr_up200` · 0.8× · p corr. 0.27 (cruda 0.017) · 44/año | no pasa: long · `big_bar` 3 · stop2_hold2x · 1.5× · meseta 0/1 · p 0.41 · 25/año |  |
| H1 | 1 | `momentum` | secundaria; matriz: Alta | «medido a favor (desnudo nota B)» | long · `bar3atr` · 3.9× · p corr. 0.01 (cruda 0.000) · 13/año · nota B | no pasa: long · `big_bar` 3 · hold1x · 3.7× · meseta 2/3 · p 0.02 · 13/año | VR(8) 0.956, <1 en 9 de 10 años; VR(32) 0.976 — la prior no afirma signo |
| H1 | 2 | `pullback` | principal; matriz: Alta | «sin evidencia medida» | long · `rsi2_up200_sma5` · 0.6× · p corr. 0.07 (cruda 0.003) · 155/año | no pasa: short · `rsi_up100` 20 · hold4x · 2.2× · meseta 1/2 · p 0.89 · 78/año |  |
| H4 | 1 | `tendencia` | principal; matriz: Alta | «sin evidencia medida» | long · `chan_30_40_run` · 7.9× · p corr. 0.29 (cruda 0.019) · 10/año | no pasa: short · `band` 1 · trail4 · 7.5× · meseta 3/3 · p 0.89 · 20/año | VR(8) 0.989, <1 en 6 de 10 años; VR(32) 0.996 — **discrepa** |
| H4 | 2 | `pullback` | secundaria; matriz: Alta | «sin evidencia medida» | short · `pullback_mom60_trail` · 11.2× · p corr. 0.66 (cruda 0.070) · 15/año | no pasa: short · `pullback` 20 · low20 · 15.8× · meseta 2/2 · p 0.62 · 13/año |  |

Paleta para `pullback`: tendencia_base_v2 (contexto) + reversion_base_v2 (disparo) — el contexto de tendencia como condición fija y el disparo de reversión en el hueco, por las dos reglas.

**Veredicto desnudo** (los cuatro filtros sobre la medida líder de cada una de las siete familias):
1. **`momentum` — nota B** · H1 long · `bar3atr` (vela de cuerpo > 3 ATR; a favor, 4 velas) · 3.91× el coste · p corr. 0.011 (cruda 0.000) · estabilidad 0.90 · 13 op/año · flaqueza: pocas operaciones  
   Paleta: `momentum_base`. Hueco libre: sesion_base (3), volatilidad_base (3), reversion_base_v2 (2), patron_base (1).
2. **`ruptura` — nota C** · H1 long · `channel55_trail` (entra: cierre sobre el máximo de 55 velas; sale: trailing de 3 ATR de la vela (escrita para largos; en corto, su espejo)) · 3.17× el coste · p corr. 0.066 (cruda 0.003) · estabilidad 0.70 · 44 op/año · flaqueza: no significativa tras corregir  
   Paleta: `ruptura_base_v2`. Hueco libre: sesion_base (3), volatilidad_base (3), reversion_base_v2 (2), patron_base (1).

**Ni lo intentes (medido):** `patron` (estructura real que no paga el coste: 6 de 8 celdas, máximo 0.20×); `reversion` (estructura real que no paga el coste: 4 de 8 celdas, máximo 13.96×).

Coste/ATR: M15 0.28, M30 0.19, H1 0.14, H4 0.07 · deriva en build -3.8 %/año.

**Bibliografía que lo nombra:** `SES-33-fx-range-by-session` «descartado por usar reloj»; `REV-42-fitschen-fx-crosses-counter-trend` «medido»; `CARRY-48-crash-asymmetry-short` «medido» — detalle en el apartado 8.

### `GBPUSD`

**Ranking según la prior, marco por marco, con lo medido al lado** (Alta antes que Media; a igual nivel, lo medido a favor antes; lo medido en contra se queda, marcado):

| marco | nº | familia | prior | estado | veredicto desnudo (mejor medida) | con salida razonable (barrido aparte) | cociente de varianzas frente a la familia principal |
|---|---|---|---|---|---|---|---|
| M15 | 1 | `volatilidad` | secundaria; matriz: Media | «sin evidencia medida» | short · `donchian_d20_squeeze` · 19.1× · p corr. 1.00 (cruda 0.408) · 6/año | — | VR(8) 0.945, <1 en 9 de 10 años; VR(32) 0.936 — **coincide** |
| M15 | 2 | `reversion` | principal; matriz: Media | «⚠️ **medido en contra**» | short · `rsi2_sma5` · 0.4× · p corr. 0.01 (cruda 0.000) · 1287/año | no pasa: short · `rsi_low` 20 · mean5 · 0.4× · meseta 0/1 · p 0.00 · 2113/año |  |
| M30 | 1 | `ruptura` | principal; matriz: Media | «sin evidencia medida» | short · `channel55_volup` · 0.9× · p corr. 0.98 (cruda 0.235) · 66/año | no pasa: short · `channel_d` 55 · hold1x · 2.2× · meseta 2/3 · p 0.89 · 13/año | VR(8) 0.986, <1 en 8 de 10 años; VR(32) 0.945 — **discrepa** |
| M30 | 2 | `reversion` | secundaria; matriz: Media | «⚠️ **medido en contra**» | short · `rsi2_sma5` · 0.7× · p corr. 0.01 (cruda 0.000) · 651/año | no pasa: short · `rsi_low` 10 · mean5 · 0.7× · meseta 0/2 · p 0.00 · 639/año |  |
| H1 | 1 | `pullback` | principal; matriz: Media | «sin evidencia medida» | short · `down3_up200_sma5` · 0.9× · p corr. 0.23 (cruda 0.014) · 167/año | no pasa: short · `rsi_up100` 10 · trail4 · 3.7× · meseta 2/3 · p 0.89 · 57/año | VR(8) 0.966, <1 en 7 de 10 años; VR(32) 0.969 — la prior no afirma signo |
| H1 | 2 | `ruptura` | secundaria; matriz: Media | «sin evidencia medida» | short · `donchian_d85_opp` · 67.6× · p corr. 1.00 (cruda 1.000) · 3/año | no pasa: short · `channel_d` 20 · hold4x · 2.6× · meseta 3/3 · p 0.89 · 13/año |  |
| H4 | 1 | `tendencia` | principal; matriz: Media | «sin evidencia medida» | long · `chan_30_40_run` · 5.0× · p corr. 0.66 (cruda 0.071) · 10/año | no pasa: short · `tsmom_d` 120 · trail4 · 13.1× · meseta 2/2 · p 0.89 · 15/año | VR(8) 0.975, <1 en 5 de 10 años; VR(32) 0.966 — sin signo estable |
| H4 | 2 | `pullback` | secundaria; matriz: Media | «sin evidencia medida» | long · `down3_up200_sma5` · 2.3× · p corr. 0.10 (cruda 0.004) · 37/año | no pasa: short · `rsi_up100` 5 · hold2x · 8.7× · meseta 3/3 · p 0.73 · 19/año |  |

Paleta para `pullback`: tendencia_base_v2 (contexto) + reversion_base_v2 (disparo) — el contexto de tendencia como condición fija y el disparo de reversión en el hueco, por las dos reglas.

**Veredicto desnudo** (los cuatro filtros sobre la medida líder de cada una de las siete familias): nada con nota.

**Ni lo intentes (medido):** `patron` (estructura real que no paga el coste: 7 de 8 celdas, máximo 0.42×); `reversion` sólo en M15 long; M15 short; M30 long (estructura real que no paga el coste).

Coste/ATR: M15 0.25, M30 0.17, H1 0.12, H4 0.06 · deriva en build -3.9 %/año.

**Bibliografía que lo nombra:** `MOM-24-opening-gap-gbpusd` «descartado por usar reloj»; `SES-31-fx-fix-reversals` «descartado por usar reloj»; `SES-33-fx-range-by-session` «descartado por usar reloj»; `REV-43-fitschen-fx-all-pairs-buy-weak` «medido» — detalle en el apartado 8.

### `NIKKEI225`

**Ranking según la prior, marco por marco, con lo medido al lado** (Alta antes que Media; a igual nivel, lo medido a favor antes; lo medido en contra se queda, marcado):

| marco | nº | familia | prior | estado | veredicto desnudo (mejor medida) | con salida razonable (barrido aparte) | cociente de varianzas frente a la familia principal |
|---|---|---|---|---|---|---|---|
| M15 | 1 | `volatilidad` | principal; matriz: Alta | «sin evidencia medida» | long · `noise_k05_nr4` · 2.3× · neto de deriva 2.0× · p corr. 0.53 (cruda 0.046) · 16/año | — | VR(8) 0.995, <1 en 4 de 8 años; VR(32) 1.012 — la prior no afirma signo |
| M15 | 2 | `reversion` | secundaria; matriz: Media | «sin evidencia medida» | short · `down3_sma5` · 0.0× · p corr. 0.70 (cruda 0.079) · 810/año | no pasa: long · `ibs_low` 0.2 · hold4x · 5.8× · meseta 3/3 · p 0.89 · 22/año |  |
| M30 | 1 | `ruptura` | principal; matriz: Alta | «sin evidencia medida» | long · `channel55_up200` · 0.4× · neto de deriva 0.3× · p corr. 0.74 (cruda 0.093) · 105/año | no pasa: long · `channel_d` 20 · hold4x · 4.9× · meseta 3/3 · p 0.89 · 13/año | VR(8) 1.016, <1 en 3 de 8 años; VR(32) 1.014 — **coincide** |
| M30 | 2 | `volatilidad` | secundaria; matriz: Alta | «⚠️ **medido en contra**» | long · `noise_k05_nr4` · 2.3× · neto de deriva 1.9× · p corr. 0.59 (cruda 0.058) · 16/año | — |  |
| H1 | 1 | `ruptura` | principal; matriz: Alta | «sin evidencia medida» | long · `channel55_trail` · 2.3× · neto de deriva 1.6× · p corr. 0.48 (cruda 0.040) · 37/año | no pasa: long · `channel_d` 20 · hold4x · 1.0× · meseta 3/3 · p 0.90 · 13/año | VR(8) 1.036, <1 en 2 de 8 años; VR(32) 1.017 — **coincide** |
| H1 | 2 | `pullback` | secundaria; matriz: Media | «sin evidencia medida» | short · `down3_up200_sma5` · 0.3× · p corr. 0.89 (cruda 0.160) · 72/año | no pasa: long · `pullback` 20 · trail2 · 1.5× · meseta 1/3 · p 0.82 · 86/año |  |
| H4 | 1 | `ruptura` | secundaria; matriz: Alta | «medido a favor (desnudo nota C)» | long · `channel55` · 2.2× · neto de deriva 1.6× · p corr. 0.55 (cruda 0.049) · 43/año · nota C | no pasa: long · `channel` 55 · trail2 · 5.0× · meseta 3/3 · p 0.70 · 15/año | VR(8) 0.989, <1 en 4 de 8 años; VR(32) 0.839 — sin signo estable |
| H4 | 2 | `tendencia` | principal; matriz: Media | «sin evidencia medida» | long · `tsmom_d120_run` · 24.1× · neto de deriva 20.6× · p corr. 0.59 (cruda 0.056) · 4/año | no pasa: long · `tsmom_d` 60 · trail2 · 1.8× · meseta 3/3 · p 0.89 · 49/año |  |
| H4 | 3 | `momentum` | no está en la celda de H4; matriz: Media | «medido a favor (desnudo nota B)» | long · `bar2atr_trail` · 25.8× · neto de deriva 20.5× · p corr. 0.05 (cruda 0.002) · 5/año · nota B | no pasa: long · `big_bar` 2 · hold2x · 12.9× · meseta 4/4 · p 0.84 · 6/año |  |

Paleta para `pullback`: tendencia_base_v2 (contexto) + reversion_base_v2 (disparo) — el contexto de tendencia como condición fija y el disparo de reversión en el hueco, por las dos reglas.

**Veredicto desnudo** (los cuatro filtros sobre la medida líder de cada una de las siete familias):
1. **`momentum` — nota B** · H4 long · `bar2atr_trail` (entra: vela con cuerpo > 2 ATR; sale: trailing de 3 ATR de la vela (escrita para largos; en corto, su espejo)) · 25.83× el coste · p corr. 0.045 (cruda 0.002) · estabilidad 0.88 · 5 op/año · flaqueza: pocas operaciones  
   Paleta: `momentum_base`. Hueco libre: sesion_base (3), volatilidad_base (3), reversion_base_v2 (2), patron_base (1).
2. **`ruptura` — nota C** · H4 long · `channel55` (ruptura del canal de 55 velas, mantenida 8) · 2.16× el coste · p corr. 0.545 (cruda 0.049) · estabilidad 0.88 · 43 op/año · flaqueza: no significativa tras corregir  
   Paleta: `ruptura_base_v2`. Hueco libre: sesion_base (3), volatilidad_base (3), reversion_base_v2 (2), patron_base (1).

**Ni lo intentes (medido):** `patron` (estructura real que no paga el coste: 5 de 8 celdas, máximo 0.39×).

Coste/ATR: M15 0.41, M30 0.29, H1 0.20, H4 0.10 · deriva en build +11.8 %/año.

**Bibliografía que lo nombra:** `MOM-21b-noise-area-clock-free` «medido»; `SES-29-overnight-vs-intraday-indices` «descartado por usar reloj»; `REV-36a-index-daily-ar1` «medido»; `REV-36c-index-weekly-ar1` «medido»; `REV-38b-rsi2-intraday-bars` «medido» — detalle en el apartado 8.

### `UKOIL`

**La prior no cubre este activo.** Se ordena sólo con lo medido y con la bibliografía.

**Veredicto desnudo** (los cuatro filtros sobre la medida líder de cada una de las siete familias): nada con nota.

**Por marco** (veredicto desnudo, la mejor dirección):

| familia | M15 | M30 | H1 | H4 |
|---|---|---|---|---|
| `momentum` | — short · `bar3atr` · 0.2× · p 0.02 · 81/año | — short · `bar2atr_up200` · 0.3× · p 0.16 · 75/año | — short · `bar2atr_hold16` · 0.4× · p 0.72 · 57/año | — short · `bar2atr_hold16` · 0.6× · p 1.00 · 15/año |
| `patron` | — long · `run3_fade` · 0.0× · p 0.01 · 2127/año | — long · `run3_fade` · 0.0× · p 0.01 · 1099/año | — long · `run3_fade` · 0.0× · p 0.02 · 563/año | — short · `run3_fade` · 0.1× · p 0.36 · 178/año |
| `reversion` | — short · `extreme2_mean` · 0.2× · p 0.33 · 347/año | — short · `extreme2_hold24` · 0.3× · p 0.90 · 169/año | — short · `extreme2_up200` · 0.4× · p 0.74 · 50/año | — long · `extreme3` · 1.1× · p 0.57 · 23/año |
| `ruptura` | — short · `carry_crash_10d` · 25.2× · p 1.00 · 0/año | — short · `channel55_up200` · 0.2× · p 0.89 · 74/año | — short · `channel100_hold24` · 0.4× · p 0.99 · 79/año | — short · `channel100_hold24` · 3.0× · p 0.31 · 27/año |
| `sesion` | — short · `prev_day_break` · -0.3× · p 1.00 · 49/año | — short · `prev_day_break` · -0.4× · p 1.00 · 48/año | — short · `prev_day_break` · -0.2× · p 1.00 · 45/año | — short · `prev_day_break` · -0.0× · p 1.00 · 38/año |
| `tendencia` | — short · `tsmom_d120_run` · 4.4× · p 0.80 · 4/año | — short · `tsmom_d120_run` · 4.3× · p 0.83 · 4/año | — long · `strong_d20_21d` · 4.6× · p 0.29 · 6/año | — short · `tsmom_d120_run` · 4.5× · p 0.80 · 4/año |
| `volatilidad` | — short · `donchian_d20_squeeze` · 8.2× · p 1.00 · 5/año | — short · `donchian_d20_squeeze` · 7.7× · p 1.00 · 5/año | — short · `donchian_d20_squeeze` · 10.9× · p 0.83 · 5/año | — long · `donchian_d20_squeeze` · 2.6× · p 0.90 · 5/año |

**Con salida razonable** (barrido aparte):

| familia | M15 | M30 | H1 | H4 |
|---|---|---|---|---|
| `momentum` | — short · `big_bar` 3 · hold1x · 0.2× · 0/3 · p 0.11 | — short · `big_bar` 2 · hold0.5x · 0.2× · 0/3 · p 0.01 | — short · `big_bar` 1 · hold2x · 0.2× · 0/3 · p 0.56 | — short · `big_bar` 1 · trail4 · 0.9× · 1/2 · p 0.89 |
| `reversion` | — short · `extreme` 3 · mean20 · 0.2× · 0/1 · p 0.36 | — short · `rsi_up200` 5 · stop2_hold2x · 0.3× · 0/1 · p 0.40 | — long · `down_run` 4 · hold2x · 0.3× · 0/3 · p 0.27 | — long · `extreme` 3 · mean5 · 1.0× · 0/1 · p 0.33 |
| `ruptura` | — short · `channel_d` 55 · hold2x · 3.6× · 2/3 · p 0.25 | — short · `channel_d` 55 · hold2x · 3.6× · 3/3 · p 0.25 | — short · `channel_d` 55 · hold4x · 6.5× · 2/2 · p 0.18 | — short · `channel_d` 55 · trail2 · 5.2× · 2/2 · p 0.29 |
| `sesion` | — short · `prev_day` 1 · hold0.5x · 0.1× · 0/2 · p 0.86 | — short · `prev_day` 2 · hold1x · 0.2× · 0/4 · p 0.57 | — long · `prev_day` 2 · hold2x · 0.2× · 0/4 · p 0.62 | — short · `prev_day` 3 · trail4 · 1.7× · 0/2 · p 0.89 |
| `tendencia` | — short · `tsmom_d` 20 · hold4x · 1.1× · 0/2 · p 0.89 | — short · `pullback` 20 · hold0.5x · 0.1× · 0/3 · p 0.84 | — short · `pullback` 14 · under20 · 0.1× · 0/1 · p 0.83 | — short · `pullback` 20 · trail4 · 2.5× · 1/3 · p 0.89 |

**Ni lo intentes (medido):** `momentum` sólo en M15 short (estructura real que no paga el coste); `patron` (estructura real que no paga el coste: 5 de 8 celdas, máximo 0.12×); `reversion` sólo en M30 long (estructura real que no paga el coste); `sesion` (ninguna celda llega a medio coste: 8 de 8 celdas, máximo -0.03×).

Coste/ATR: M15 1.21, M30 0.84, H1 0.59, H4 0.30 · deriva en build -7.4 %/año.

**Bibliografía que lo nombra:** `TR-05-fast-trend-commodities` «medido»; `TR-08a-fitschen-h1-commodities-10bars` «medido»; `TR-08b-fitschen-h1-commodities-10days` «medido»; `TR-12-chan-crude-30-40` «medido»; `MOM-25-crude-first-half-hour` «descartado por usar reloj» — detalle en el apartado 8.

### `USA500`

**Ranking según la prior, marco por marco, con lo medido al lado** (Alta antes que Media; a igual nivel, lo medido a favor antes; lo medido en contra se queda, marcado):

| marco | nº | familia | prior | estado | veredicto desnudo (mejor medida) | con salida razonable (barrido aparte) | cociente de varianzas frente a la familia principal |
|---|---|---|---|---|---|---|---|
| M15 | 1 | `reversion` (largo) | principal; matriz: Alta | «sin evidencia medida» | long · `rsi2_voldn_sma5` · 0.3× · neto de deriva 0.2× · p corr. 0.21 (cruda 0.012) · 502/año | no pasa: long · `ibs_low` 0.2 · hold1x · 5.4× · meseta 4/4 · p 0.84 · 38/año | VR(8) 0.978, <1 en 6 de 8 años; VR(32) 0.965 — **coincide** |
| M15 | 2 | `volatilidad` | secundaria; matriz: Media | «sin evidencia medida» | long · `noise_k05_nr4` · 3.1× · neto de deriva 2.3× · p corr. 0.68 (cruda 0.074) · 20/año | — |  |
| M30 | 1 | `reversion` (largo) | principal; matriz: Alta | «sin evidencia medida» | long · `extreme2_voldn_mean` · 1.5× · neto de deriva 1.0× · p corr. 0.39 (cruda 0.029) · 82/año | no pasa: long · `ibs_low` 0.2 · hold1x · 5.3× · meseta 4/4 · p 0.84 · 38/año | VR(8) 0.979, <1 en 4 de 8 años; VR(32) 0.968 — sin signo estable |
| M30 | 2 | `pullback` (largo) | secundaria; matriz: Alta | «sin evidencia medida» | long · `extreme2_up200` · 0.7× · neto de deriva 0.4× · p corr. 0.86 (cruda 0.144) · 148/año | no pasa: long · `rsi_up200` 10 · trail4 · 1.7× · meseta 0/3 · p 0.89 · 151/año |  |
| H1 | 1 | `reversion` (largo) | secundaria; matriz: Alta | «medido a favor (desnudo nota C)» | long · `extreme2_voldn_mean` · 3.1× · neto de deriva 2.0× · p corr. 0.47 (cruda 0.039) · 42/año · nota C | no pasa: long · `ibs_low` 0.2 · hold1x · 5.1× · meseta 4/4 · p 0.84 · 39/año | VR(8) 0.975, <1 en 5 de 8 años; VR(32) 0.919 — la prior no afirma signo |
| H1 | 2 | `pullback` (largo) | principal; matriz: Alta | «sin evidencia medida» | long · `connors_d1` · 13.0× · neto de deriva 7.2× · p corr. 0.86 (cruda 0.141) · 8/año | no pasa: long · `rsi_up200` 10 · trail4 · 3.1× · meseta 2/3 · p 0.89 · 72/año |  |
| H4 | 1 | `pullback` (largo) | principal; matriz: Alta | «sin evidencia medida» | long · `connors_d1` · 13.8× · neto de deriva 8.0× · p corr. 0.82 (cruda 0.122) · 8/año | no pasa: long · `rsi_up200` 10 · hold2x · 4.3× · meseta 4/4 · p 0.89 · 34/año | VR(8) 0.922, <1 en 8 de 8 años; VR(32) 0.826 — la prior no afirma signo |
| H4 | 2 | `tendencia` | secundaria; matriz: Media | «sin evidencia medida» | long · `fast_d5_20_run` · 32.3× · neto de deriva 18.3× · p corr. 0.40 (cruda 0.030) · 8/año | no pasa: long · `band` 1 · hold2x · 4.8× · meseta 4/4 · p 0.89 · 46/año |  |

Paleta para `pullback`: tendencia_base_v2 (contexto) + reversion_base_v2 (disparo) — el contexto de tendencia como condición fija y el disparo de reversión en el hueco, por las dos reglas.

**Veredicto desnudo** (los cuatro filtros sobre la medida líder de cada una de las siete familias):
1. **`reversion` — nota C** · H1 long · `extreme2_voldn_mean` (entra: cierre a 2 ATR bajo su media de 20 y ATR D1(10) < ATR D1(100); sale: cierre sobre su media de 20 o 40 velas (escrita para largos; en corto, su espejo)) · 3.06× el coste · p corr. 0.475 (cruda 0.039) · estabilidad 0.88 · 42 op/año · flaqueza: no significativa tras corregir  
   Paleta: `reversion_base_v2`. Hueco libre: sesion_base (3), volatilidad_base (3), momentum_base (2), ruptura_base_v2 (2), tendencia_base_v2 (2), patron_base (1).
2. **`momentum` — nota C** · M15 long · `noise_k07` (entra: cierre > apertura del día + 0,7 ATR D1; sale: cierre bajo la apertura del día o 1 día(s) de velas (escrita para largos; en corto, su espejo)) · 2.87× el coste · p corr. 0.528 (cruda 0.046) · estabilidad 0.88 · 47 op/año · flaqueza: no significativa tras corregir  
   Paleta: `momentum_base`. Hueco libre: sesion_base (3), volatilidad_base (3), reversion_base_v2 (2), patron_base (1).

**Ni lo intentes (medido):** `patron` (estructura real que no paga el coste: 7 de 8 celdas, máximo 0.24×).

Coste/ATR: M15 0.27, M30 0.19, H1 0.13, H4 0.07 · deriva en build +11.3 %/año.

**Bibliografía que lo nombra:** `MOM-18-first-last-half-hour-us` «descartado por usar reloj»; `MOM-21a-noise-area-breakout` «descartado por usar reloj»; `MOM-21b-noise-area-clock-free` «medido»; `VOL-22-narrow-range-then-intraday-trend` «medido»; `SES-28-overnight-drift-us-index` «descartado por usar reloj»; `SES-29-overnight-vs-intraday-indices` «descartado por usar reloj»; `CAL-34-turn-of-month` «descartado por usar reloj»; `CAL-35-pre-fomc-drift` «descartado por usar reloj»; `REV-36a-index-daily-ar1` «medido»; `REV-36c-index-weekly-ar1` «medido»; `REV-37a-ibs-long` «medido»; `REV-37b-ibs-short` «medido»; `REV-38a-rsi2-daily` «medido»; `REV-38b-rsi2-intraday-bars` «medido»; `REV-40-fitschen-stocks-daily-counter-trend` «medido»; `REV-41-williams-pullback-in-uptrend` «medido»; `REV-46-chan-gap-fade-with-trend-filter` «descartado por usar reloj» — detalle en el apartado 8.

### `USATEC`

**Ranking según la prior, marco por marco, con lo medido al lado** (Alta antes que Media; a igual nivel, lo medido a favor antes; lo medido en contra se queda, marcado):

| marco | nº | familia | prior | estado | veredicto desnudo (mejor medida) | con salida razonable (barrido aparte) | cociente de varianzas frente a la familia principal |
|---|---|---|---|---|---|---|---|
| M15 | 1 | `ruptura` | principal; matriz: Alta | «sin evidencia medida» | long · `channel20` · 0.6× · neto de deriva 0.3× · p corr. 0.53 (cruda 0.046) · 757/año | no pasa: long · `channel_d` 20 · hold4x · 12.1× · meseta 3/3 · p 0.89 · 17/año | VR(8) 1.000, <1 en 4 de 8 años; VR(32) 1.020 — sin signo estable |
| M15 | 2 | `reversion` | secundaria; matriz: Media | «sin evidencia medida» | long · `out10_counter` · 48.1× · neto de deriva 24.7× · p corr. 0.54 (cruda 0.048) · 9/año | no pasa: long · `ibs_low` 0.2 · hold2x · 15.1× · meseta 4/4 · p 0.75 · 29/año |  |
| M30 | 1 | `ruptura` | principal; matriz: Alta | «sin evidencia medida» | short · `channel55_up200` · 3.7× · p corr. 0.65 (cruda 0.067) · 14/año | no pasa: long · `channel_d` 20 · hold4x · 11.9× · meseta 3/3 · p 0.89 · 17/año | VR(8) 1.017, <1 en 2 de 8 años; VR(32) 1.023 — **coincide** |
| M30 | 2 | `pullback` (largo) | secundaria; matriz: Alta | «sin evidencia medida» | long · `connors_d1` · 16.6× · neto de deriva 9.5× · p corr. 0.73 (cruda 0.090) · 8/año | no pasa: long · `pullback` 20 · trail4 · 2.9× · meseta 2/3 · p 0.89 · 114/año |  |
| H1 | 1 | `pullback` (largo) | principal; matriz: Alta | «sin evidencia medida» | long · `connors_d1` · 17.6× · neto de deriva 10.7× · p corr. 0.66 (cruda 0.070) · 8/año | no pasa: long · `pullback` 20 · trail4 · 5.5× · meseta 3/3 · p 0.89 · 55/año | VR(8) 1.022, <1 en 3 de 8 años; VR(32) 0.959 — la prior no afirma signo |
| H1 | 2 | `momentum` | secundaria; matriz: Alta | «sin evidencia medida» | short · `bar1atr` · 0.1× · p corr. 0.66 (cruda 0.072) · 290/año | no pasa: long · `big_bar` 1 · trail2 · 3.5× · meseta 2/2 · p 0.81 · 132/año |  |
| H4 | 1 | `momentum` | principal; matriz: Alta | «sin evidencia medida» | short · `bar2atr_hold16` · 4.4× · p corr. 0.37 (cruda 0.026) · 14/año | no pasa: long · `big_bar` 1 · trail4 · 24.5× · meseta 2/2 · p 0.89 · 16/año | VR(8) 0.932, <1 en 7 de 8 años; VR(32) 0.829 — **discrepa** |
| H4 | 2 | `tendencia` | secundaria; matriz: Media | «sin evidencia medida» | short · `chan_30_40_run` · 10.2× · p corr. 0.64 (cruda 0.066) · 5/año | no pasa: long · `band` 1 · hold2x · 7.3× · meseta 4/4 · p 0.89 · 48/año |  |

Paleta para `pullback`: tendencia_base_v2 (contexto) + reversion_base_v2 (disparo) — el contexto de tendencia como condición fija y el disparo de reversión en el hueco, por las dos reglas.

**Veredicto desnudo** (los cuatro filtros sobre la medida líder de cada una de las siete familias):
1. **`momentum` — nota C** · M15 long · `noise_k07` (entra: cierre > apertura del día + 0,7 ATR D1; sale: cierre bajo la apertura del día o 1 día(s) de velas (escrita para largos; en corto, su espejo)) · 2.90× el coste · p corr. 0.451 (cruda 0.036) · estabilidad 0.75 · 47 op/año · flaqueza: no significativa tras corregir  
   Paleta: `momentum_base`. Hueco libre: sesion_base (3), volatilidad_base (3), reversion_base_v2 (2), patron_base (1).

**Ni lo intentes (medido):** `patron` (estructura real que no paga el coste: 5 de 8 celdas, máximo 0.32×).

Coste/ATR: M15 0.19, M30 0.14, H1 0.10, H4 0.05 · deriva en build +16.1 %/año.

**Bibliografía que lo nombra:** `TR-09-fitschen-h1-stocks` «medido»; `MOM-21b-noise-area-clock-free` «medido»; `NEG-27-mnq-ohlcv-intraday-momentum` «descartado por usar reloj»; `SES-29-overnight-vs-intraday-indices` «descartado por usar reloj»; `REV-36a-index-daily-ar1` «medido»; `REV-37a-ibs-long` «medido»; `REV-37b-ibs-short` «medido»; `REV-38a-rsi2-daily` «medido»; `REV-38b-rsi2-intraday-bars` «medido»; `REV-40-fitschen-stocks-daily-counter-trend` «medido» — detalle en el apartado 8.

### `USDCAD`

*Prior: fila «AUDUSD, NZDUSD, USDCAD» de la prior.*

**Ranking según la prior, marco por marco, con lo medido al lado** (Alta antes que Media; a igual nivel, lo medido a favor antes; lo medido en contra se queda, marcado):

| marco | nº | familia | prior | estado | veredicto desnudo (mejor medida) | con salida razonable (barrido aparte) | cociente de varianzas frente a la familia principal |
|---|---|---|---|---|---|---|---|
| M15 | 1 | `reversion` | principal; matriz: Media | «medido a favor (desnudo nota C)» | long · `day_down_volhigh_1d` · 3.1× · p corr. 0.35 (cruda 0.025) · 42/año · nota C | no pasa: long · `ibs_low` 0.1 · hold2x · 1.0× · meseta 1/3 · p 0.89 · 31/año | VR(8) 0.926, <1 en 10 de 10 años; VR(32) 0.882 — **coincide** |
| M30 | 1 | `reversion` | principal; matriz: Media | «medido a favor (desnudo nota C)» | long · `keltner225_mean` · 1.4× · p corr. 0.03 (cruda 0.001) · 161/año · nota C | no pasa: long · `ibs_low` 0.1 · hold2x · 1.0× · meseta 1/3 · p 0.89 · 31/año | VR(8) 0.929, <1 en 10 de 10 años; VR(32) 0.882 — **coincide** |
| H1 | 1 | `reversion` | principal; matriz: Media | «medido a favor (desnudo nota C)» | long · `rsi2_sma5` · 1.0× · p corr. 0.01 (cruda 0.000) · 327/año · nota C | no pasa: long · `extreme` 2 · mean20 · 1.8× · meseta 1/2 · p 0.32 · 95/año | VR(8) 0.914, <1 en 10 de 10 años; VR(32) 0.908 — **coincide** |
| H1 | 2 | `pullback` | secundaria; matriz: Media | «sin evidencia medida» | long · `down3_up200_sma5` · 0.8× · p corr. 0.23 (cruda 0.014) · 177/año | no pasa: long · `rsi_up100` 10 · mean20 · 1.5× · meseta 1/2 · p 0.23 · 141/año |  |
| H4 | 1 | `pullback` | secundaria; matriz: Media | «medido a favor (desnudo nota C)» | long · `down3_up200_sma5` · 3.1× · p corr. 0.06 (cruda 0.002) · 43/año · nota C | no pasa: long · `rsi_up200` 10 · hold1x · 2.5× · meseta 2/4 · p 0.86 · 40/año | VR(8) 0.938, <1 en 10 de 10 años; VR(32) 0.948 — **discrepa** |
| H4 | 2 | `tendencia` | principal; matriz: Media | «sin evidencia medida» | short · `chan_30_40_run` · 5.0× · p corr. 0.68 (cruda 0.075) · 9/año | no pasa: long · `band` 1 · hold2x · 2.4× · meseta 2/4 · p 0.89 · 54/año |  |

Paleta para `pullback`: tendencia_base_v2 (contexto) + reversion_base_v2 (disparo) — el contexto de tendencia como condición fija y el disparo de reversión en el hueco, por las dos reglas.

**Veredicto desnudo** (los cuatro filtros sobre la medida líder de cada una de las siete familias):
1. **`reversion` — nota C** · H1 long · `rsi2_sma5` (entra: RSI(2) de la vela < 10; sale: cierre sobre su SMA5 o 10 velas (escrita para largos; en corto, su espejo)) · 1.01× el coste · p corr. 0.011 (cruda 0.000) · estabilidad 0.80 · 327 op/año · flaqueza: paga 1-2× · también: H4 long C 3.1×  
   Paleta: `reversion_base_v2`. Hueco libre: sesion_base (3), volatilidad_base (3), momentum_base (2), ruptura_base_v2 (2), tendencia_base_v2 (2), patron_base (1).

**Ni lo intentes (medido):** `patron` (estructura real que no paga el coste: 6 de 8 celdas, máximo 0.82×).

Coste/ATR: M15 0.26, M30 0.18, H1 0.13, H4 0.06 · deriva en build +2.3 %/año.

**Bibliografía que lo nombra:** `SES-31-fx-fix-reversals` «descartado por usar reloj»; `SES-33-fx-range-by-session` «descartado por usar reloj»; `REV-43-fitschen-fx-all-pairs-buy-weak` «medido»; `REV-44-chan-usdcad-half-life` «la bibliografía lo afirma y aquí no se mide» — detalle en el apartado 8.

### `USDCHF`

**La prior no cubre este activo.** Se ordena sólo con lo medido y con la bibliografía.

**Veredicto desnudo** (los cuatro filtros sobre la medida líder de cada una de las siete familias):
1. **`momentum` — nota B** · H1 short · `bar2atr_volup` (entra: vela con cuerpo > 2 ATR y ATR D1(10) > ATR D1(100); sale: 4 velas (escrita para largos; en corto, su espejo)) · 2.40× el coste · p corr. 0.045 (cruda 0.002) · estabilidad 0.70 · 24 op/año · flaqueza: pocas operaciones  
   Paleta: `momentum_base`. Hueco libre: sesion_base (3), volatilidad_base (3), reversion_base_v2 (2), patron_base (1).

**Por marco** (veredicto desnudo, la mejor dirección):

| familia | M15 | M30 | H1 | H4 |
|---|---|---|---|---|
| `momentum` | — long · `bar3atr` · 1.2× · p 0.05 · 68/año | — long · `bar3atr` · 1.5× · p 0.36 · 44/año | **B** short · `bar2atr_volup` · 2.4× · p 0.05 · 24/año | — short · `bar2atr_trail` · 11.3× · p 0.64 · 11/año |
| `patron` | — short · `run3_fade` · 0.1× · p 0.01 · 2549/año | — short · `run3_fade` · 0.2× · p 0.01 · 1311/año | — long · `run3_fade` · 0.3× · p 0.01 · 643/año | — long · `run3_fade` · -0.0× · p 0.13 · 178/año |
| `reversion` | — short · `rsi2_sma5` · 0.3× · p 0.01 · 1294/año | — short · `rsi2_sma5` · 0.5× · p 0.01 · 649/año | — long · `down3_sma5` · 0.6× · p 0.03 · 334/año | — short · `rsi2_voldn_sma5` · 0.9× · p 0.91 · 52/año |
| `ruptura` | — long · `carry_crash_10d` · 112.7× · p 1.00 · 0/año | — long · `carry_crash_10d` · 118.4× · p 1.00 · 0/año | — long · `carry_crash_10d` · 118.4× · p 1.00 · 0/año | — long · `channel200_hold48` · 6.5× · p 0.89 · 19/año |
| `sesion` | — short · `prev_day_break` · -1.6× · p 1.00 · 52/año | — short · `prev_day_break` · -0.6× · p 1.00 · 49/año | — short · `prev_day_break` · -0.0× · p 1.00 · 45/año | — short · `prev_day_break` · -0.3× · p 1.00 · 38/año |
| `tendencia` | — short · `fast_d5_20_quiet_run` · 11.7× · p 0.84 · 6/año | — short · `fast_d5_20_quiet_run` · 11.6× · p 0.87 · 6/año | — short · `fast_d5_20_quiet_run` · 11.7× · p 0.87 · 6/año | — short · `fast_d5_20_quiet_run` · 12.6× · p 0.80 · 6/año |
| `volatilidad` | — long · `donchian_d20_squeeze` · 4.1× · p 1.00 · 6/año | — long · `donchian_d20_squeeze` · 3.0× · p 1.00 · 6/año | — long · `donchian_d20_squeeze` · 2.6× · p 1.00 · 6/año | — long · `donchian_d20_squeeze` · 6.8× · p 0.99 · 6/año |

**Con salida razonable** (barrido aparte):

| familia | M15 | M30 | H1 | H4 |
|---|---|---|---|---|
| `momentum` | — long · `big_bar` 3 · hold1x · 1.3× · 0/3 · p 0.18 | — short · `big_bar` 3 · trail2 · 1.5× · 0/2 · p 0.44 | — long · `big_bar` 3 · hold4x · 2.8× · 1/2 · p 0.58 | — short · `big_bar` 2 · trail4 · 17.3× · 2/3 · p 0.51 |
| `reversion` | — short · `ibs_low` 0.3 · hold1x · 1.0× · 1/3 · p 0.86 | — short · `ibs_low` 0.3 · hold1x · 1.1× · 1/3 · p 0.89 | — short · `ibs_low` 0.3 · hold1x · 1.1× · 1/3 · p 0.88 | — long · `extreme` 3 · hold4x · 5.9× · 2/2 · p 0.89 |
| `ruptura` | — short · `channel_d` 20 · hold1x · 1.6× · 0/4 · p 0.89 | — short · `channel_d` 20 · hold0.5x · 1.2× · 1/3 · p 0.86 | — short · `channel_d` 20 · hold1x · 3.7× · 2/4 · p 0.44 | — long · `channel_d` 55 · hold4x · 12.5× · 1/2 · p 0.15 |
| `sesion` | — short · `prev_day` 3 · trail4 · 0.4× · 0/2 · p 0.89 | — short · `prev_day` 3 · hold4x · 1.0× · 0/2 · p 0.77 | — short · `prev_day` 3 · hold2x · 1.5× · 0/3 · p 0.57 | — short · `prev_day` 2 · hold2x · 2.5× · 2/4 · p 0.84 |
| `tendencia` | — short · `pullback` 30 · hold4x · 0.1× · 0/2 · p 0.89 | — short · `tsmom_d` 20 · hold4x · 0.4× · 0/2 · p 0.89 | — long · `pullback` 14 · hold2x · 0.7× · 0/3 · p 0.77 | — short · `band` 1 · trail4 · 6.6× · 2/3 · p 0.89 |

**Ni lo intentes (medido):** `patron` (estructura real que no paga el coste: 6 de 8 celdas, máximo 0.25×); `reversion` (estructura real que no paga el coste: 4 de 8 celdas, máximo 0.92×); `sesion` (ninguna celda llega a medio coste: 8 de 8 celdas, máximo -0.03×).

Coste/ATR: M15 0.31, M30 0.22, H1 0.15, H4 0.07 · deriva en build -1.5 %/año.

**Bibliografía que lo nombra:** `SES-31-fx-fix-reversals` «descartado por usar reloj»; `SES-33-fx-range-by-session` «descartado por usar reloj»; `REV-43-fitschen-fx-all-pairs-buy-weak` «medido» — detalle en el apartado 8.

### `USDJPY`

**Ranking según la prior, marco por marco, con lo medido al lado** (Alta antes que Media; a igual nivel, lo medido a favor antes; lo medido en contra se queda, marcado):

| marco | nº | familia | prior | estado | veredicto desnudo (mejor medida) | con salida razonable (barrido aparte) | cociente de varianzas frente a la familia principal |
|---|---|---|---|---|---|---|---|
| M15 | 1 | `volatilidad` | principal; matriz: Media | «sin evidencia medida» | long · `noise_k05_nr4` · 1.5× · p corr. 0.91 (cruda 0.173) · 23/año | — | VR(8) 0.950, <1 en 10 de 10 años; VR(32) 0.910 — la prior no afirma signo |
| M15 | 2 | `ruptura` | secundaria; matriz: Media | «sin evidencia medida» | long · `channel100_hold24` · 0.4× · p corr. 0.98 (cruda 0.232) · 364/año | no pasa: long · `channel_d` 10 · hold2x · 5.3× · meseta 3/3 · p 0.55 · 25/año |  |
| M30 | 1 | `momentum` | secundaria; matriz: Alta | «medido a favor (desnudo nota C)» | long · `bar2atr_trail` · 3.3× · p corr. 0.05 (cruda 0.002) · 77/año · nota C | no pasa: long · `big_bar` 2 · trail2 · 2.4× · meseta 1/3 · p 0.20 · 86/año | VR(8) 0.958, <1 en 9 de 10 años; VR(32) 0.922 — **discrepa** |
| M30 | 2 | `ruptura` | principal; matriz: Media | «sin evidencia medida» | long · `channel55_trail` · 2.3× · p corr. 0.17 (cruda 0.009) · 90/año | no pasa: long · `channel_d` 20 · hold1x · 4.9× · meseta 3/4 · p 0.36 · 23/año |  |
| H1 | 1 | `momentum` | secundaria; matriz: Alta | «medido a favor (desnudo nota C)» | long · `noise_k05` · 2.7× · p corr. 0.09 (cruda 0.004) · 79/año · nota C | no pasa: long · `big_bar` 3 · hold1x · 3.8× · meseta 2/3 · p 0.36 · 16/año | VR(8) 0.940, <1 en 9 de 10 años; VR(32) 0.924 — la prior no afirma signo |
| H1 | 2 | `pullback` | principal; matriz: Alta | «sin evidencia medida» | short · `rsi2_up200_sma5` · 1.2× · p corr. 0.06 (cruda 0.002) · 153/año | no pasa: long · `pullback` 20 · under20 · 1.5× · meseta 1/2 · p 0.25 · 164/año |  |
| H4 | 1 | `pullback` | secundaria; matriz: Alta | «medido a favor (desnudo nota C)» | short · `williams_pullback_1d` · 2.7× · p corr. 0.47 (cruda 0.038) · 46/año · nota C | no pasa: short · `rsi_up200` 5 · hold2x · 5.0× · meseta 2/3 · p 0.86 · 20/año | VR(8) 0.972, <1 en 4 de 10 años; VR(32) 0.925 — sin signo estable |
| H4 | 2 | `tendencia` | principal; matriz: Alta | «sin evidencia medida» | short · `chan_30_40_run` · 7.4× · p corr. 0.42 (cruda 0.032) · 11/año | no pasa: long · `band` 1 · under20 · 3.4× · meseta 2/2 · p 0.80 · 46/año |  |

Paleta para `pullback`: tendencia_base_v2 (contexto) + reversion_base_v2 (disparo) — el contexto de tendencia como condición fija y el disparo de reversión en el hueco, por las dos reglas.

**Veredicto desnudo** (los cuatro filtros sobre la medida líder de cada una de las siete familias):
1. **`reversion` — nota C** · H1 long · `down3_sma5` (entra: 3 cierres bajistas seguidos; sale: cierre sobre su SMA5 o 10 velas (escrita para largos; en corto, su espejo)) · 1.03× el coste · p corr. 0.011 (cruda 0.000) · estabilidad 0.80 · 328 op/año · flaqueza: paga 1-2× · también: M15 long C 1.0×; H4 long C 3.8×; H4 short C 2.7×  
   Paleta: `reversion_base_v2`. Hueco libre: sesion_base (3), volatilidad_base (3), momentum_base (2), ruptura_base_v2 (2), tendencia_base_v2 (2), patron_base (1).
2. **`momentum` — nota C** · M30 long · `bar2atr_trail` (entra: vela con cuerpo > 2 ATR; sale: trailing de 3 ATR de la vela (escrita para largos; en corto, su espejo)) · 3.34× el coste · p corr. 0.052 (cruda 0.002) · estabilidad 0.80 · 77 op/año · flaqueza: no significativa tras corregir · también: H1 long C 2.7×; H4 long C 2.6×  
   Paleta: `momentum_base`. Hueco libre: sesion_base (3), volatilidad_base (3), reversion_base_v2 (2), patron_base (1).

**Ni lo intentes (medido):** `patron` (estructura real que no paga el coste: 5 de 8 celdas, máximo 0.55×); `sesion` (ninguna celda llega a medio coste: 8 de 8 celdas, máximo 0.15×).

Coste/ATR: M15 0.20, M30 0.14, H1 0.10, H4 0.05 · deriva en build +0.1 %/año.

**Bibliografía que lo nombra:** `SES-31-fx-fix-reversals` «descartado por usar reloj»; `SES-32-jpy-local-hours` «descartado por usar reloj»; `SES-33-fx-range-by-session` «descartado por usar reloj»; `REV-43-fitschen-fx-all-pairs-buy-weak` «medido»; `CARRY-48-crash-asymmetry-short` «medido» — detalle en el apartado 8.

### `USOIL`

**La prior no cubre este activo.** Se ordena sólo con lo medido y con la bibliografía.

**Veredicto desnudo** (los cuatro filtros sobre la medida líder de cada una de las siete familias): nada con nota.

**Por marco** (veredicto desnudo, la mejor dirección):

| familia | M15 | M30 | H1 | H4 |
|---|---|---|---|---|
| `momentum` | — short · `bar3atr` · 0.1× · p 0.22 · 93/año | — short · `bar1atr` · 0.1× · p 0.07 · 919/año | — short · `bar3atr` · 0.2× · p 0.65 · 33/año | — short · `bar2atr_hold16` · 1.0× · p 0.89 · 15/año |
| `patron` | — long · `run3_fade` · 0.0× · p 0.01 · 2151/año | — long · `run3_fade` · 0.0× · p 0.01 · 1124/año | — long · `run3_fade` · 0.0× · p 0.01 · 582/año | — short · `run3_fade` · 0.0× · p 0.21 · 176/año |
| `reversion` | — short · `extreme3` · 0.1× · p 0.52 · 295/año | — short · `d1_down3_1d` · 0.4× · p 0.96 · 30/año | — short · `d1_down3_1d` · 0.4× · p 0.93 · 30/año | — long · `extreme3` · 0.8× · p 0.52 · 22/año |
| `ruptura` | — short · `donchian_d20_opp` · 8.9× · p 0.95 · 5/año | — short · `donchian_d20_opp` · 8.5× · p 0.95 · 5/año | — short · `donchian_d20_opp` · 9.2× · p 0.92 · 4/año | — short · `channel55_trail` · 3.6× · p 0.30 · 11/año |
| `sesion` | — short · `prev_day_break` · 0.2× · p 1.00 · 49/año | — short · `prev_day_break` · 0.2× · p 1.00 · 47/año | — short · `prev_day_break` · 0.3× · p 1.00 · 44/año | — short · `prev_day_break` · 0.4× · p 1.00 · 38/año |
| `tendencia` | — long · `strong_d20_21d` · 2.2× · p 0.72 · 7/año | — long · `strong_d20_21d` · 2.1× · p 0.72 · 7/año | — long · `strong_d20_21d` · 1.8× · p 0.76 · 7/año | — short · `pullback_mom60_trail` · 3.4× · p 0.55 · 13/año |
| `volatilidad` | — short · `noise_k05_nr4` · 0.4× · p 0.64 · 24/año | — long · `donchian_d20_squeeze` · 0.8× · p 1.00 · 5/año | — short · `noise_k05_nr4` · 0.4× · p 0.61 · 22/año | — short · `noise_k05_nr4` · 0.2× · p 0.95 · 19/año |

**Con salida razonable** (barrido aparte):

| familia | M15 | M30 | H1 | H4 |
|---|---|---|---|---|
| `momentum` | — short · `big_bar` 3 · hold1x · 0.1× · 0/3 · p 0.40 | — short · `big_bar` 2 · hold0.5x · 0.2× · 0/3 · p 0.01 | — short · `big_bar` 3 · trail2 · 0.5× · 0/2 · p 0.45 | — short · `big_bar` 3 · trail4 · 7.2× · 1/2 · p 0.74 |
| `reversion` | — short · `extreme` 3 · hold2x · 0.1× · 0/3 · p 0.62 | — short · `rsi_up100` 5 · hold4x · 0.3× · 0/2 · p 0.83 | — short · `rsi_up100` 5 · hold0.5x · 0.2× · 0/2 · p 0.61 | — short · `extreme` 3 · mean5 · 0.5× · 0/1 · p 0.72 |
| `ruptura` | — short · `channel_d` 55 · hold4x · 3.5× · 1/2 · p 0.72 | — short · `channel_d` 55 · hold4x · 3.5× · 1/2 · p 0.78 | — short · `channel_d` 20 · hold4x · 1.9× · 1/3 · p 0.89 | — short · `channel_d` 20 · trail2 · 1.7× · 3/3 · p 0.74 |
| `sesion` | — short · `prev_day` 3 · hold1x · 0.1× · 0/3 · p 0.65 | — short · `prev_day` 3 · hold0.5x · 0.2× · 0/2 · p 0.47 | — short · `prev_day` 2 · hold4x · 0.4× · 0/3 · p 0.89 | — short · `prev_day` 3 · trail4 · 1.8× · 0/2 · p 0.89 |
| `tendencia` | — long · `tsmom_d` 60 · stop2_hold2x · 0.1× · 0/2 · p 0.82 | — short · `pullback` 30 · hold4x · 0.5× · 0/2 · p 0.61 | — short · `pullback` 30 · trail2 · 0.6× · 0/2 · p 0.39 | — short · `pullback` 20 · low20 · 3.6× · 2/2 · p 0.86 |

**Ni lo intentes (medido):** `patron` (estructura real que no paga el coste: 6 de 8 celdas, máximo 0.05×); `sesion` (ninguna celda llega a medio coste: 8 de 8 celdas, máximo 0.42×).

Coste/ATR: M15 1.44, M30 1.00, H1 0.70, H4 0.34 · deriva en build -5.8 %/año.

**Bibliografía que lo nombra:** `TR-05-fast-trend-commodities` «medido»; `TR-08a-fitschen-h1-commodities-10bars` «medido»; `TR-08b-fitschen-h1-commodities-10days` «medido»; `TR-12-chan-crude-30-40` «medido»; `MOM-25-crude-first-half-hour` «descartado por usar reloj» — detalle en el apartado 8.

### `XAGUSD`

**Ranking según la prior, marco por marco, con lo medido al lado** (Alta antes que Media; a igual nivel, lo medido a favor antes; lo medido en contra se queda, marcado):

| marco | nº | familia | prior | estado | veredicto desnudo (mejor medida) | con salida razonable (barrido aparte) | cociente de varianzas frente a la familia principal |
|---|---|---|---|---|---|---|---|
| M15 | 1 | `reversion` | principal; matriz: Media | «sin evidencia medida» | short · `extreme2_mean` · 0.4× · p corr. 0.02 (cruda 0.001) · 277/año | no pasa: long · `ibs_low` 0.1 · hold2x · 0.3× · meseta 1/3 · p 0.89 · 19/año | VR(8) 0.771, <1 en 10 de 10 años; VR(32) 0.728 — **coincide** |
| M30 | 1 | `volatilidad` | principal; matriz: Alta | «sin evidencia medida» | long · `noise_k05_nr4` · 1.0× · p corr. 0.93 (cruda 0.183) · 25/año | — | VR(8) 0.840, <1 en 10 de 10 años; VR(32) 0.824 — la prior no afirma signo |
| M30 | 2 | `reversion` | secundaria; matriz: Media | «sin evidencia medida» | short · `rsi2_sma5` · 0.3× · p corr. 0.01 (cruda 0.000) · 611/año | no pasa: long · `ibs_low` 0.1 · hold2x · 0.1× · meseta 1/3 · p 0.89 · 19/año |  |
| H1 | 1 | `ruptura` | principal; matriz: Alta | «sin evidencia medida» | long · `channel55_up200` · 0.7× · p corr. 0.65 (cruda 0.068) · 40/año | no pasa: long · `channel_d` 55 · hold2x · 4.5× · meseta 3/3 · p 0.38 · 10/año | VR(8) 0.889, <1 en 10 de 10 años; VR(32) 0.904 — **discrepa** |
| H1 | 2 | `volatilidad` | secundaria; matriz: Alta | «sin evidencia medida» | long · `noise_k05_nr4` · 0.7× · p corr. 1.00 (cruda 0.257) · 24/año | — |  |
| H4 | 1 | `ruptura` | principal; matriz: Alta | «sin evidencia medida» | long · `channel55_up200` · 4.2× · p corr. 0.34 (cruda 0.024) · 14/año | no pasa: long · `channel_d` 20 · hold2x · 3.5× · meseta 4/4 · p 0.57 · 15/año | VR(8) 0.990, <1 en 7 de 10 años; VR(32) 0.965 — **discrepa** |
| H4 | 2 | `tendencia` | secundaria; matriz: Media | «sin evidencia medida» | short · `chan_30_40_run` · 5.6× · p corr. 0.62 (cruda 0.062) · 7/año | no pasa: long · `band` 1 · trail2 · 1.9× · meseta 1/3 · p 0.89 · 33/año |  |
| H4 | 3 | `momentum` | no está en la celda de H4; matriz: Media | «medido a favor (desnudo nota B)» | long · `bar2atr_up200` · 4.9× · p corr. 0.03 (cruda 0.001) · 5/año · nota B | no pasa: long · `big_bar` 2 · trail2 · 4.7× · meseta 2/3 · p 0.59 · 12/año |  |

Paleta para `pullback`: tendencia_base_v2 (contexto) + reversion_base_v2 (disparo) — el contexto de tendencia como condición fija y el disparo de reversión en el hueco, por las dos reglas.

**Veredicto desnudo** (los cuatro filtros sobre la medida líder de cada una de las siete familias):
1. **`momentum` — nota B** · H4 long · `bar2atr_up200` (entra: vela con cuerpo > 2 ATR y cierre D1 sobre su SMA200; sale: 4 velas (escrita para largos; en corto, su espejo)) · 4.93× el coste · p corr. 0.030 (cruda 0.001) · estabilidad 0.71 · 5 op/año · flaqueza: pocas operaciones  
   Paleta: `momentum_base`. Hueco libre: sesion_base (3), volatilidad_base (3), reversion_base_v2 (2), patron_base (1).

**Ni lo intentes (medido):** `patron` (estructura real que no paga el coste: 6 de 8 celdas, máximo 0.15×); `reversion` (estructura real que no paga el coste: 4 de 8 celdas, máximo 1.20×).

Coste/ATR: M15 0.36, M30 0.27, H1 0.20, H4 0.10 · deriva en build +1.4 %/año.

**Bibliografía que lo nombra:** `TR-05-fast-trend-commodities` «medido»; `TR-08a-fitschen-h1-commodities-10bars` «medido»; `TR-08b-fitschen-h1-commodities-10days` «medido»; `MOM-26-metals-late-session-half-hours` «descartado por usar reloj» — detalle en el apartado 8.

### `XAUUSD`

**Ranking según la prior, marco por marco, con lo medido al lado** (Alta antes que Media; a igual nivel, lo medido a favor antes; lo medido en contra se queda, marcado):

| marco | nº | familia | prior | estado | veredicto desnudo (mejor medida) | con salida razonable (barrido aparte) | cociente de varianzas frente a la familia principal |
|---|---|---|---|---|---|---|---|
| M15 | 1 | `volatilidad` | principal; matriz: Alta | «sin evidencia medida» | long · `noise_k05_nr4` · 2.4× · p corr. 0.66 (cruda 0.069) · 27/año | — | VR(8) 0.985, <1 en 7 de 10 años; VR(32) 0.977 — la prior no afirma signo |
| M15 | 2 | `ruptura` | secundaria; matriz: Alta | «sin evidencia medida» | long · `channel55_up200` · 0.2× · p corr. 1.00 (cruda 0.261) · 202/año | no pasa: short · `channel_d` 20 · hold2x · 3.2× · meseta 4/4 · p 0.89 · 14/año |  |
| M30 | 1 | `ruptura` | principal; matriz: Alta | «medido a favor (desnudo nota C)» | long · `channel55_trail` · 2.1× · p corr. 0.28 (cruda 0.018) · 93/año · nota C | no pasa: short · `channel_d` 55 · hold2x · 9.0× · meseta 3/3 · p 0.76 · 7/año | VR(8) 0.985, <1 en 5 de 10 años; VR(32) 0.976 — sin signo estable |
| M30 | 2 | `volatilidad` | secundaria; matriz: Alta | «sin evidencia medida» | long · `noise_k05_nr4` · 1.2× · p corr. 0.98 (cruda 0.236) · 25/año | — |  |
| H1 | 1 | `ruptura` | principal; matriz: Alta | «medido a favor (desnudo nota C)» | long · `channel55_trail` · 3.7× · p corr. 0.32 (cruda 0.022) · 46/año · nota C | no pasa: short · `channel_d` 20 · trail4 · 7.0× · meseta 3/3 · p 0.67 · 11/año | VR(8) 0.983, <1 en 6 de 10 años; VR(32) 1.016 — **discrepa** |
| H1 | 2 | `pullback` | secundaria; matriz: Alta | «sin evidencia medida» | long · `down3_up200_sma5` · 0.5× · p corr. 0.82 (cruda 0.123) · 168/año | no pasa: long · `rsi_up100` 5 · hold2x · 2.4× · meseta 1/3 · p 0.48 · 81/año |  |
| H4 | 1 | `momentum` | secundaria; matriz: Alta | «medido a favor (desnudo nota C)» | long · `bar1atr` · 2.3× · p corr. 0.41 (cruda 0.031) · 91/año · nota C | no pasa: long · `big_bar` 2 · hold1x · 5.7× · meseta 4/4 · p 0.32 · 15/año | VR(8) 1.024, <1 en 5 de 10 años; VR(32) 1.001 — sin signo estable |
| H4 | 2 | `tendencia` | principal; matriz: Alta | «sin evidencia medida» | long · `tsmom_d252_run` · 22.3× · p corr. 0.74 (cruda 0.091) · 4/año | no pasa: long · `band` 1 · hold2x · 3.1× · meseta 3/4 · p 0.89 · 55/año |  |

Paleta para `pullback`: tendencia_base_v2 (contexto) + reversion_base_v2 (disparo) — el contexto de tendencia como condición fija y el disparo de reversión en el hueco, por las dos reglas.

**Veredicto desnudo** (los cuatro filtros sobre la medida líder de cada una de las siete familias):
1. **`momentum` — nota C** · M15 long · `bar3atr` (vela de cuerpo > 3 ATR; a favor, 4 velas) · 1.54× el coste · p corr. 0.030 (cruda 0.001) · estabilidad 0.70 · 80 op/año · flaqueza: paga 1-2× · también: H1 long C 3.9×; M30 long C 2.8×  
   Paleta: `momentum_base`. Hueco libre: sesion_base (3), volatilidad_base (3), reversion_base_v2 (2), patron_base (1).
2. **`ruptura` — nota C** · H1 long · `channel55_trail` (entra: cierre sobre el máximo de 55 velas; sale: trailing de 3 ATR de la vela (escrita para largos; en corto, su espejo)) · 3.75× el coste · p corr. 0.322 (cruda 0.022) · estabilidad 0.70 · 46 op/año · flaqueza: no significativa tras corregir · también: M30 long C 2.1×  
   Paleta: `ruptura_base_v2`. Hueco libre: sesion_base (3), volatilidad_base (3), reversion_base_v2 (2), patron_base (1).

**Ni lo intentes (medido):** `patron` (estructura real que no paga el coste: 6 de 8 celdas, máximo 0.59×); `reversion` sólo en M15 long; M15 short; M30 long (estructura real que no paga el coste).

Coste/ATR: M15 0.21, M30 0.15, H1 0.10, H4 0.05 · deriva en build +4.5 %/año.

**Bibliografía que lo nombra:** `TR-05-fast-trend-commodities` «medido»; `TR-08a-fitschen-h1-commodities-10bars` «medido»; `TR-08b-fitschen-h1-commodities-10days` «medido»; `MOM-26-metals-late-session-half-hours` «descartado por usar reloj»; `SES-30-gold-overnight` «descartado por usar reloj»; `GOLD-51-real-yields-and-dollar` «la bibliografía lo afirma y aquí no se mide» — detalle en el apartado 8.

## 4. Tabla completa del veredicto desnudo (la que imprime `--favourable`)

| activo | nº | familia | nota | celda | medida | efecto | p corr. | p cruda | estab. | op/año | flaqueza | también en | paleta | hueco libre (peso) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `AUDUSD` | 1 | `reversion` | **B** | H4 short | `extreme3` | 9.36× | 0.038 | 0.001 | 0.90 | 15 | pocas operaciones | — | `reversion_base_v2` | sesion_base (3), volatilidad_base (3), momentum_base (2), ruptura_base_v2 (2), tendencia_base_v2 (2), patron_base (1) |
| `DAX40` | 1 | `momentum` | **C** | H4 long | `bar1atr` | 4.01× | 0.412 | 0.031 | 0.86 | 77 | no significativa tras corregir | — | `momentum_base` | sesion_base (3), volatilidad_base (3), reversion_base_v2 (2), patron_base (1) |
| `DJ30` | 1 | `ruptura` | **A** | H1 long | `channel55_up200` | 3.14× | 0.030 | 0.001 | 1.00 | 71 | — | M30 long C 3.4×; M15 long C 3.1× | `ruptura_base_v2` | sesion_base (3), volatilidad_base (3), reversion_base_v2 (2), patron_base (1) |
| `DJ30` | 2 | `momentum` | **C** | M30 short | `bar2atr` | 1.45× | 0.021 | 0.001 | 0.71 | 141 | paga 1-2× | M30 long C 3.9× | `momentum_base` | sesion_base (3), volatilidad_base (3), reversion_base_v2 (2), patron_base (1) |
| `EURJPY` | 1 | `tendencia` | **C** | H1 long | `pullback_mom60_trail` | 3.51× | 0.114 | 0.005 | 0.70 | 58 | no significativa tras corregir | — | `tendencia_base_v2` | sesion_base (3), volatilidad_base (3), reversion_base_v2 (2), patron_base (1) |
| `EURJPY` | 2 | `momentum` | **C** | M30 long | `bar2atr_trail` | 2.64× | 0.066 | 0.003 | 0.70 | 72 | no significativa tras corregir | — | `momentum_base` | sesion_base (3), volatilidad_base (3), reversion_base_v2 (2), patron_base (1) |
| `EURUSD` | 1 | `momentum` | **A** | M15 short | `bar3atr` | 2.30× | 0.021 | 0.001 | 0.80 | 67 | — | H4 short C 5.1×; M30 short C 3.0×; H1 long C 2.1× | `momentum_base` | sesion_base (3), volatilidad_base (3), reversion_base_v2 (2), patron_base (1) |
| `EURUSD` | 2 | `volatilidad` | **C** | H4 short | `narrow_break` | 3.80× | 0.538 | 0.047 | 0.90 | 62 | no significativa tras corregir | — | `volatilidad_base` | momentum_base (3), patron_base (3), reversion_base_v2 (3), ruptura_base_v2 (3), sesion_base (3), tendencia_base_v2 (3) |
| `GBPJPY` | 1 | `momentum` | **B** | H1 long | `bar3atr` | 3.91× | 0.011 | 0.000 | 0.90 | 13 | pocas operaciones | — | `momentum_base` | sesion_base (3), volatilidad_base (3), reversion_base_v2 (2), patron_base (1) |
| `GBPJPY` | 2 | `ruptura` | **C** | H1 long | `channel55_trail` | 3.17× | 0.066 | 0.003 | 0.70 | 44 | no significativa tras corregir | — | `ruptura_base_v2` | sesion_base (3), volatilidad_base (3), reversion_base_v2 (2), patron_base (1) |
| `NIKKEI225` | 1 | `momentum` | **B** | H4 long | `bar2atr_trail` | 25.83× | 0.045 | 0.002 | 0.88 | 5 | pocas operaciones | — | `momentum_base` | sesion_base (3), volatilidad_base (3), reversion_base_v2 (2), patron_base (1) |
| `NIKKEI225` | 2 | `ruptura` | **C** | H4 long | `channel55` | 2.16× | 0.545 | 0.049 | 0.88 | 43 | no significativa tras corregir | — | `ruptura_base_v2` | sesion_base (3), volatilidad_base (3), reversion_base_v2 (2), patron_base (1) |
| `USA500` | 1 | `reversion` | **C** | H1 long | `extreme2_voldn_mean` | 3.06× | 0.475 | 0.039 | 0.88 | 42 | no significativa tras corregir | — | `reversion_base_v2` | sesion_base (3), volatilidad_base (3), momentum_base (2), ruptura_base_v2 (2), tendencia_base_v2 (2), patron_base (1) |
| `USA500` | 2 | `momentum` | **C** | M15 long | `noise_k07` | 2.87× | 0.528 | 0.046 | 0.88 | 47 | no significativa tras corregir | — | `momentum_base` | sesion_base (3), volatilidad_base (3), reversion_base_v2 (2), patron_base (1) |
| `USATEC` | 1 | `momentum` | **C** | M15 long | `noise_k07` | 2.90× | 0.451 | 0.036 | 0.75 | 47 | no significativa tras corregir | — | `momentum_base` | sesion_base (3), volatilidad_base (3), reversion_base_v2 (2), patron_base (1) |
| `USDCAD` | 1 | `reversion` | **C** | H1 long | `rsi2_sma5` | 1.01× | 0.011 | 0.000 | 0.80 | 327 | paga 1-2× | H4 long C 3.1× | `reversion_base_v2` | sesion_base (3), volatilidad_base (3), momentum_base (2), ruptura_base_v2 (2), tendencia_base_v2 (2), patron_base (1) |
| `USDCHF` | 1 | `momentum` | **B** | H1 short | `bar2atr_volup` | 2.40× | 0.045 | 0.002 | 0.70 | 24 | pocas operaciones | — | `momentum_base` | sesion_base (3), volatilidad_base (3), reversion_base_v2 (2), patron_base (1) |
| `USDJPY` | 1 | `reversion` | **C** | H1 long | `down3_sma5` | 1.03× | 0.011 | 0.000 | 0.80 | 328 | paga 1-2× | M15 long C 1.0×; H4 long C 3.8×; H4 short C 2.7× | `reversion_base_v2` | sesion_base (3), volatilidad_base (3), momentum_base (2), ruptura_base_v2 (2), tendencia_base_v2 (2), patron_base (1) |
| `USDJPY` | 2 | `momentum` | **C** | M30 long | `bar2atr_trail` | 3.34× | 0.052 | 0.002 | 0.80 | 77 | no significativa tras corregir | H1 long C 2.7×; H4 long C 2.6× | `momentum_base` | sesion_base (3), volatilidad_base (3), reversion_base_v2 (2), patron_base (1) |
| `XAGUSD` | 1 | `momentum` | **B** | H4 long | `bar2atr_up200` | 4.93× | 0.030 | 0.001 | 0.71 | 5 | pocas operaciones | — | `momentum_base` | sesion_base (3), volatilidad_base (3), reversion_base_v2 (2), patron_base (1) |
| `XAUUSD` | 1 | `momentum` | **C** | M15 long | `bar3atr` | 1.54× | 0.030 | 0.001 | 0.70 | 80 | paga 1-2× | H1 long C 3.9×; M30 long C 2.8× | `momentum_base` | sesion_base (3), volatilidad_base (3), reversion_base_v2 (2), patron_base (1) |
| `XAUUSD` | 2 | `ruptura` | **C** | H1 long | `channel55_trail` | 3.75× | 0.322 | 0.022 | 0.70 | 46 | no significativa tras corregir | M30 long C 2.1× | `ruptura_base_v2` | sesion_base (3), volatilidad_base (3), reversion_base_v2 (2), patron_base (1) |

## 5. Lo medido como malo

`familia` = la familia entera en ese activo; `celda` = sólo las celdas que se nombran.

| activo | familia | alcance | por qué | celdas | lo máximo que paga |
|---|---|---|---|---|---|
| `AUDJPY` | `patron` | familia | estructura real que no paga el coste | 6 de 8 | 0.28× |
| `AUDJPY` | `reversion` | familia | estructura real que no paga el coste | 4 de 8 | 3.86× |
| `AUDUSD` | `patron` | familia | estructura real que no paga el coste | 7 de 8 | 0.42× |
| `CADJPY` | `patron` | familia | estructura real que no paga el coste | 6 de 8 | 0.39× |
| `CADJPY` | `reversion` | familia | estructura real que no paga el coste | 4 de 8 | 3.37× |
| `DAX40` | `patron` | familia | estructura real que no paga el coste | 6 de 8 | 0.50× |
| `DJ30` | `patron` | familia | estructura real que no paga el coste | 5 de 8 | 0.18× |
| `EURJPY` | `patron` | familia | estructura real que no paga el coste | 6 de 8 | 0.89× |
| `EURJPY` | `reversion` | celda | estructura real que no paga el coste | 2 de 8 (M15 long; M30 short) | 8.86× |
| `EURJPY` | `sesion` | familia | ninguna celda llega a medio coste | 8 de 8 | -1.42× |
| `EURUSD` | `patron` | familia | estructura real que no paga el coste | 6 de 8 | 0.87× |
| `EURUSD` | `sesion` | familia | ninguna celda llega a medio coste | 8 de 8 | 0.24× |
| `GBPJPY` | `patron` | familia | estructura real que no paga el coste | 6 de 8 | 0.20× |
| `GBPJPY` | `reversion` | familia | estructura real que no paga el coste | 4 de 8 | 13.96× |
| `GBPUSD` | `patron` | familia | estructura real que no paga el coste | 7 de 8 | 0.42× |
| `GBPUSD` | `reversion` | celda | estructura real que no paga el coste | 3 de 8 (M15 long; M15 short; M30 long) | 7.16× |
| `NIKKEI225` | `patron` | familia | estructura real que no paga el coste | 5 de 8 | 0.39× |
| `UKOIL` | `momentum` | celda | estructura real que no paga el coste | 1 de 8 (M15 short) | 0.56× |
| `UKOIL` | `patron` | familia | estructura real que no paga el coste | 5 de 8 | 0.12× |
| `UKOIL` | `reversion` | celda | estructura real que no paga el coste | 1 de 8 (M30 long) | 1.12× |
| `UKOIL` | `sesion` | familia | ninguna celda llega a medio coste | 8 de 8 | -0.03× |
| `USA500` | `patron` | familia | estructura real que no paga el coste | 7 de 8 | 0.24× |
| `USATEC` | `patron` | familia | estructura real que no paga el coste | 5 de 8 | 0.32× |
| `USDCAD` | `patron` | familia | estructura real que no paga el coste | 6 de 8 | 0.82× |
| `USDCHF` | `patron` | familia | estructura real que no paga el coste | 6 de 8 | 0.25× |
| `USDCHF` | `reversion` | familia | estructura real que no paga el coste | 4 de 8 | 0.92× |
| `USDCHF` | `sesion` | familia | ninguna celda llega a medio coste | 8 de 8 | -0.03× |
| `USDJPY` | `patron` | familia | estructura real que no paga el coste | 5 de 8 | 0.55× |
| `USDJPY` | `sesion` | familia | ninguna celda llega a medio coste | 8 de 8 | 0.15× |
| `USOIL` | `patron` | familia | estructura real que no paga el coste | 6 de 8 | 0.05× |
| `USOIL` | `sesion` | familia | ninguna celda llega a medio coste | 8 de 8 | 0.42× |
| `XAGUSD` | `patron` | familia | estructura real que no paga el coste | 6 de 8 | 0.15× |
| `XAGUSD` | `reversion` | familia | estructura real que no paga el coste | 4 de 8 | 1.20× |
| `XAUUSD` | `patron` | familia | estructura real que no paga el coste | 6 de 8 | 0.59× |
| `XAUUSD` | `reversion` | celda | estructura real que no paga el coste | 3 de 8 (M15 long; M15 short; M30 long) | 4.11× |

## 6. Todos los marcos, la corrección alternativa y lo descartado por usar reloj

### 6.1 Cada activo × familia en M15, M30, H1 y H4 (veredicto desnudo)

| activo | familia | M15 | M30 | H1 | H4 |
|---|---|---|---|---|---|
| `AUDJPY` | `momentum` | — short · `bar2atr_volup` · 0.5× · p 0.56 · 67/año | — short · `noise_k10` · 1.2× · p 0.98 · 29/año | — long · `bar3atr` · 1.4× · p 0.71 · 9/año | — long · `bar2atr_up200` · 4.9× · p 1.00 · 2/año |
| `AUDJPY` | `patron` | — short · `run3_fade` · 0.1× · p 0.01 · 2776/año | — short · `run3_fade` · 0.1× · p 0.01 · 1415/año | — long · `run3_fade` · 0.2× · p 0.01 · 647/año | — long · `run3_follow` · 0.3× · p 1.00 · 198/año |
| `AUDJPY` | `reversion` | — long · `rsi2_voldn_sma5` · 0.2× · p 0.01 · 783/año | — long · `rsi2_voldn_sma5` · 0.4× · p 0.01 · 393/año | — long · `down3_sma5` · 0.5× · p 0.07 · 327/año | — short · `extreme2_up200` · 3.9× · p 0.65 · 13/año |
| `AUDJPY` | `ruptura` | — long · `donchian_d85_opp` · 2.6× · p 0.98 · 3/año | — long · `donchian_d85_opp` · 2.5× · p 0.97 · 3/año | — long · `donchian_d85_opp` · 4.0× · p 0.95 · 3/año | — long · `carry_crash_10d` · 66.4× · p 1.00 · 0/año |
| `AUDJPY` | `sesion` | — short · `prev_day_break` · 0.6× · p 1.00 · 51/año | — short · `prev_day_break` · 0.7× · p 1.00 · 49/año | — short · `prev_day_break` · 0.4× · p 1.00 · 47/año | — short · `prev_day_break` · -0.2× · p 1.00 · 40/año |
| `AUDJPY` | `tendencia` | — short · `sma50_200_run` · 1.3× · p 0.82 · 75/año | — short · `tsmom_d60_volup_run` · 21.3× · p 0.94 · 3/año | — long · `pullback_mom60_trail` · 1.3× · p 0.48 · 64/año | — short · `tsmom_d60_volup_run` · 23.2× · p 0.92 · 3/año |
| `AUDJPY` | `volatilidad` | — long · `donchian_d20_squeeze` · 2.3× · p 1.00 · 6/año | — long · `donchian_d20_squeeze` · 3.1× · p 1.00 · 6/año | — long · `donchian_d20_squeeze` · 3.4× · p 1.00 · 6/año | — long · `donchian_d20_squeeze` · 4.0× · p 1.00 · 6/año |
| `AUDUSD` | `momentum` | — short · `bar2atr_volup` · 0.7× · p 0.51 · 74/año | — short · `bar3atr` · 1.4× · p 0.45 · 29/año | — short · `bar2atr` · 1.3× · p 0.55 · 50/año | — short · `bar2atr_trail` · 18.8× · p 0.55 · 7/año |
| `AUDUSD` | `patron` | — short · `run3_fade` · 0.1× · p 0.01 · 2679/año | — short · `run3_fade` · 0.2× · p 0.01 · 1373/año | — short · `run3_fade` · 0.2× · p 0.01 · 705/año | — long · `inside` · 0.4× · p 0.04 · 123/año |
| `AUDUSD` | `reversion` | — long · `rsi2_up200_sma5` · 0.5× · p 0.01 · 618/año | — long · `down3_up200_sma5` · 0.7× · p 0.01 · 319/año | — long · `rsi2_voldn_sma5` · 0.8× · p 0.02 · 202/año | **B** short · `extreme3` · 9.4× · p 0.04 · 15/año |
| `AUDUSD` | `ruptura` | — short · `donchian_d20_opp` · 18.9× · p 0.92 · 5/año | — short · `donchian_d20_opp` · 20.0× · p 0.88 · 5/año | — short · `donchian_d20_opp` · 18.4× · p 0.96 · 5/año | — short · `donchian_d20_trail` · 39.7× · p 0.93 · 4/año |
| `AUDUSD` | `sesion` | — short · `prev_day_break` · 0.5× · p 1.00 · 51/año | — short · `prev_day_break` · 0.0× · p 1.00 · 50/año | — short · `prev_day_break` · 0.3× · p 1.00 · 48/año | — short · `prev_day_break` · -1.0× · p 1.00 · 42/año |
| `AUDUSD` | `tendencia` | — short · `tsmom_d60_volup_run` · 25.4× · p 0.97 · 4/año | — short · `tsmom_d60_volup_run` · 25.6× · p 0.97 · 4/año | — short · `tsmom_d60_volup_run` · 25.2× · p 0.96 · 4/año | — long · `tsmom_d252_run` · 14.4× · p 0.37 · 3/año |
| `AUDUSD` | `volatilidad` | — short · `noise_k05_nr4` · 3.5× · p 0.34 · 21/año | — short · `noise_k05_nr4` · 4.0× · p 0.14 · 20/año | — short · `noise_k05_nr4` · 3.7× · p 0.18 · 19/año | — short · `donchian_d20_squeeze` · 21.0× · p 0.91 · 5/año |
| `CADJPY` | `momentum` | — long · `noise_k05` · 0.9× · p 0.36 · 90/año | — long · `noise_k05` · 1.0× · p 0.28 · 86/año | — long · `noise_k03` · 0.7× · p 0.32 · 137/año | — long · `bar2atr_up200` · 2.9× · p 0.79 · 4/año |
| `CADJPY` | `patron` | — short · `run3_fade` · 0.1× · p 0.01 · 2699/año | — short · `run3_fade` · 0.1× · p 0.01 · 1371/año | — long · `run3_fade` · 0.2× · p 0.01 · 659/año | — short · `run3_follow` · 0.4× · p 0.92 · 186/año |
| `CADJPY` | `reversion` | — short · `rsi2_voldn_sma5` · 0.3× · p 0.01 · 781/año | — long · `rsi2_voldn_sma5` · 0.4× · p 0.01 · 385/año | — long · `down3_sma5` · 0.5× · p 0.07 · 330/año | — short · `extreme2_up200` · 3.4× · p 0.76 · 13/año |
| `CADJPY` | `ruptura` | — short · `channel100_hold24` · 0.3× · p 0.97 · 343/año | — long · `carry_crash_10d` · 51.7× · p 1.00 · 0/año | — short · `channel55_volup` · 2.5× · p 0.25 · 29/año | — short · `carry_crash_opp5` · 148.6× · p 1.00 · 0/año |
| `CADJPY` | `sesion` | — short · `prev_day_break` · 0.2× · p 1.00 · 53/año | — short · `prev_day_break` · 0.1× · p 1.00 · 51/año | — short · `prev_day_break` · 0.0× · p 1.00 · 48/año | — short · `prev_day_break` · 0.8× · p 1.00 · 38/año |
| `CADJPY` | `tendencia` | — short · `chan_30_40_run` · 5.7× · p 0.76 · 8/año | — short · `chan_30_40_run` · 6.0× · p 0.70 · 8/año | — short · `chan_30_40_run` · 5.7× · p 0.75 · 8/año | — short · `chan_30_40_run` · 5.1× · p 0.80 · 8/año |
| `CADJPY` | `volatilidad` | — short · `noise_k05_nr4` · 1.9× · p 0.54 · 22/año | — short · `noise_k05_nr4` · 1.8× · p 0.61 · 20/año | — short · `noise_k05_nr4` · 2.0× · p 0.61 · 19/año | — short · `narrow_break` · 1.5× · p 0.75 · 64/año |
| `DAX40` | `momentum` | — long · `bar2atr_volup` · 0.8× · p 0.72 · 98/año | — long · `bar2atr_trail` · 1.1× · p 1.00 · 101/año | — long · `bar2atr_trail` · 2.7× · p 1.00 · 40/año | **C** long · `bar1atr` · 4.0× · p 0.41 · 77/año |
| `DAX40` | `patron` | — long · `run3_fade` · 0.2× · p 0.01 · 1818/año | — short · `run3_fade` · 0.2× · p 0.01 · 1072/año | — long · `run3_fade` · 0.5× · p 0.01 · 483/año | — long · `run3_fade` · 0.1× · p 0.55 · 124/año |
| `DAX40` | `reversion` | — long · `down3_sma5` · 0.3× · p 0.51 · 935/año | — long · `ibs_low_volhigh_up_1d` · 12.6× · p 0.76 · 10/año | — short · `ibs_low_volhigh_up_1d` · 6.4× · p 0.74 · 11/año | — long · `ibs_low_volhigh_up_1d` · 11.5× · p 0.83 · 10/año |
| `DAX40` | `ruptura` | — long · `channel200_hold48` · 2.9× · p 0.67 · 216/año | — long · `channel100_hold24` · 2.3× · p 0.83 · 160/año | — long · `channel55_up200` · 2.6× · p 0.76 · 40/año | — long · `channel55` · 7.0× · p 0.40 · 35/año |
| `DAX40` | `sesion` | — long · `prev_day_break` · 1.4× · p 1.00 · 52/año | — long · `prev_day_break` · 0.9× · p 1.00 · 51/año | — long · `prev_day_break` · 0.9× · p 1.00 · 47/año | — long · `prev_day_break` · 3.7× · p 1.00 · 36/año |
| `DAX40` | `tendencia` | — short · `fast_d5_20_quiet_run` · 23.7× · p 0.69 · 5/año | — short · `fast_d5_20_quiet_run` · 23.8× · p 0.66 · 5/año | — short · `fast_d5_20_quiet_run` · 24.7× · p 0.63 · 5/año | — short · `fast_d5_20_quiet_run` · 24.8× · p 0.66 · 5/año |
| `DAX40` | `volatilidad` | — long · `donchian_d20_squeeze` · 31.3× · p 1.00 · 5/año | — long · `donchian_d20_squeeze` · 31.4× · p 1.00 · 5/año | — long · `donchian_d20_squeeze` · 27.4× · p 1.00 · 5/año | — long · `narrow_break` · 2.0× · p 1.00 · 67/año |
| `DJ30` | `momentum` | — long · `bar3atr` · 1.0× · p 0.41 · 64/año | **C** long · `bar2atr_trail` · 3.9× · p 0.37 · 90/año | — long · `noise_k07` · 3.1× · p 0.74 · 45/año | — short · `bar2atr_hold16` · 6.4× · p 0.40 · 12/año |
| `DJ30` | `patron` | — long · `run3_fade` · 0.1× · p 0.01 · 1924/año | — long · `run3_fade` · 0.1× · p 0.01 · 969/año | — long · `run3_fade` · 0.2× · p 0.08 · 493/año | — short · `run3_fade` · -0.2× · p 0.33 · 180/año |
| `DJ30` | `reversion` | — long · `extreme2_voldn_mean` · 0.8× · p 0.74 · 163/año | — long · `extreme2_voldn_mean` · 2.0× · p 0.42 · 86/año | — long · `weak_d20_mean` · 27.5× · p 0.81 · 9/año | — long · `weak_d20_mean` · 26.6× · p 0.83 · 9/año |
| `DJ30` | `ruptura` | **C** long · `channel200_hold48` · 3.1× · p 0.27 · 262/año | **C** long · `channel100_hold24` · 3.4× · p 0.11 · 199/año | **A** long · `channel55_up200` · 3.1× · p 0.03 · 71/año | — long · `channel55_up200` · 6.9× · p 0.24 · 24/año |
| `DJ30` | `sesion` | — long · `prev_day_break` · 4.7× · p 1.00 · 52/año | — long · `prev_day_break` · 4.9× · p 1.00 · 50/año | — long · `prev_day_break` · 4.8× · p 1.00 · 48/año | — long · `prev_day_break` · 5.4× · p 1.00 · 40/año |
| `DJ30` | `tendencia` | — long · `fast_d5_20_run` · 44.7× · p 0.73 · 8/año | — long · `fast_d5_20_run` · 44.9× · p 0.74 · 8/año | — long · `fast_d5_20_run` · 44.9× · p 0.71 · 8/año | — long · `fast_d5_20_run` · 44.9× · p 0.67 · 8/año |
| `DJ30` | `volatilidad` | — long · `noise_k05_nr4` · 4.5× · p 0.30 · 22/año | — long · `noise_k05_nr4` · 4.0× · p 0.47 · 22/año | — long · `noise_k05_nr4` · 3.3× · p 0.65 · 20/año | — long · `donchian_d20_squeeze` · 48.8× · p 0.88 · 6/año |
| `EURJPY` | `momentum` | — long · `bar2atr_volup` · 1.0× · p 0.10 · 71/año | **C** long · `bar2atr_trail` · 2.6× · p 0.07 · 72/año | — long · `bar2atr_up200` · 2.4× · p 0.09 · 21/año | — short · `bar2atr_volup` · 7.2× · p 0.96 · 5/año |
| `EURJPY` | `patron` | — long · `run3_fade` · 0.1× · p 0.01 · 2568/año | — short · `run3_fade` · 0.2× · p 0.01 · 1375/año | — long · `run3_fade` · 0.3× · p 0.01 · 646/año | — short · `engulfing` · 0.9× · p 0.59 · 131/año |
| `EURJPY` | `reversion` | — long · `rsi2_voldn_sma5` · 0.3× · p 0.01 · 754/año | — long · `down3_up200_sma5` · 0.5× · p 0.05 · 288/año | — long · `down3_up200_sma5` · 0.8× · p 0.06 · 140/año | — long · `extreme2_up200_mean` · 8.9× · p 0.15 · 11/año |
| `EURJPY` | `ruptura` | — long · `donchian_d20_opp` · 14.6× · p 0.81 · 5/año | — short · `channel55_trail` · 1.2× · p 0.91 · 91/año | — short · `channel55` · 1.0× · p 0.86 · 130/año | — long · `channel200_hold48` · 20.3× · p 0.14 · 20/año |
| `EURJPY` | `sesion` | — short · `prev_day_break` · -1.4× · p 1.00 · 54/año | — short · `prev_day_break` · -1.5× · p 1.00 · 52/año | — short · `prev_day_break` · -1.7× · p 1.00 · 49/año | — short · `prev_day_break` · -1.5× · p 1.00 · 41/año |
| `EURJPY` | `tendencia` | — short · `tsmom_d60_run` · 31.8× · p 0.66 · 7/año | — short · `tsmom_d60_run` · 31.8× · p 0.66 · 7/año | **C** long · `pullback_mom60_trail` · 3.5× · p 0.11 · 58/año | — short · `tsmom_d120_run` · 34.3× · p 0.78 · 4/año |
| `EURJPY` | `volatilidad` | — long · `donchian_d20_squeeze` · 6.2× · p 1.00 · 5/año | — long · `donchian_d20_squeeze` · 5.4× · p 1.00 · 5/año | — long · `donchian_d20_squeeze` · 2.9× · p 1.00 · 5/año | — short · `donchian_d20_squeeze` · 9.7× · p 1.00 · 6/año |
| `EURUSD` | `momentum` | **A** short · `bar3atr` · 2.3× · p 0.02 · 67/año | **C** short · `bar3atr` · 3.0× · p 0.07 · 41/año | **C** long · `bar2atr` · 2.1× · p 0.17 · 75/año | **C** short · `noise_k07` · 5.1× · p 0.13 · 43/año |
| `EURUSD` | `patron` | — long · `run3_fade` · 0.2× · p 0.01 · 2613/año | — short · `run3_fade` · 0.3× · p 0.01 · 1336/año | — short · `run3_fade` · 0.5× · p 0.01 · 679/año | — long · `inside` · 0.9× · p 1.00 · 148/año |
| `EURUSD` | `reversion` | — long · `rsi2_up200_sma5` · 0.7× · p 0.01 · 593/año | — long · `rsi2_voldn_sma5` · 0.9× · p 0.01 · 378/año | — short · `ibs_low_volhigh_1d` · 11.1× · p 0.07 · 19/año | — short · `ibs_low_volhigh_1d` · 9.4× · p 0.15 · 19/año |
| `EURUSD` | `ruptura` | — short · `donchian_d20_opp` · 39.7× · p 0.95 · 5/año | — short · `channel55_volup` · 1.2× · p 0.89 · 67/año | — short · `channel55_volup` · 2.6× · p 0.81 · 36/año | — short · `channel200_hold48` · 32.1× · p 0.69 · 20/año |
| `EURUSD` | `sesion` | — short · `prev_day_break` · 0.1× · p 1.00 · 53/año | — short · `prev_day_break` · -0.9× · p 1.00 · 51/año | — short · `prev_day_break` · -1.9× · p 1.00 · 48/año | — short · `prev_day_break` · 0.2× · p 1.00 · 41/año |
| `EURUSD` | `tendencia` | — long · `fast_d5_20_quiet_run` · 24.1× · p 0.73 · 6/año | — long · `fast_d5_20_quiet_run` · 24.7× · p 0.69 · 6/año | — long · `fast_d5_20_quiet_run` · 24.1× · p 0.71 · 6/año | — short · `tsmom_d120_run` · 47.7× · p 0.86 · 4/año |
| `EURUSD` | `volatilidad` | — short · `donchian_d20_squeeze` · 11.9× · p 1.00 · 6/año | — short · `donchian_d20_squeeze` · 10.5× · p 1.00 · 6/año | — short · `noise_k05_nr4` · 2.3× · p 0.99 · 19/año | **C** short · `narrow_break` · 3.8× · p 0.54 · 62/año |
| `GBPJPY` | `momentum` | — short · `noise_k10` · 0.4× · p 1.00 · 28/año | — short · `bar2atr_trail` · 1.2× · p 0.96 · 86/año | **B** long · `bar3atr` · 3.9× · p 0.01 · 13/año | — long · `bar2atr_up200` · 4.9× · p 0.66 · 5/año |
| `GBPJPY` | `patron` | — short · `run3_fade` · 0.1× · p 0.01 · 2719/año | — long · `run3_fade` · 0.1× · p 0.01 · 1304/año | — short · `run3_fade` · 0.2× · p 0.01 · 706/año | — short · `run3_follow` · 0.2× · p 1.00 · 174/año |
| `GBPJPY` | `reversion` | — short · `rsi2_voldn_sma5` · 0.3× · p 0.01 · 764/año | — short · `rsi2_sma5` · 0.4× · p 0.02 · 655/año | — long · `rsi2_up200_sma5` · 0.6× · p 0.07 · 155/año | — short · `connors_d1` · 14.0× · p 0.93 · 5/año |
| `GBPJPY` | `ruptura` | — short · `carry_crash_opp5` · 47.9× · p 1.00 · 1/año | — short · `channel55_trail` · 1.4× · p 0.87 · 90/año | **C** long · `channel55_trail` · 3.2× · p 0.07 · 44/año | — long · `channel200_hold48` · 13.0× · p 0.20 · 18/año |
| `GBPJPY` | `sesion` | — short · `prev_day_break` · 2.9× · p 0.97 · 50/año | — short · `prev_day_break` · 3.1× · p 0.96 · 48/año | — short · `prev_day_break` · 3.9× · p 0.86 · 45/año | — short · `prev_day_break` · 4.4× · p 0.86 · 38/año |
| `GBPJPY` | `tendencia` | — short · `tsmom_d120_run` · 44.1× · p 0.69 · 4/año | — long · `chan_30_40_run` · 7.9× · p 0.22 · 10/año | — short · `sma50_200_run` · 10.3× · p 0.59 · 18/año | — long · `chan_30_40_run` · 7.9× · p 0.29 · 10/año |
| `GBPJPY` | `volatilidad` | — short · `donchian_d20_squeeze` · 6.9× · p 1.00 · 6/año | — short · `donchian_d20_squeeze` · 6.8× · p 1.00 · 6/año | — short · `donchian_d20_squeeze` · 8.4× · p 1.00 · 6/año | — short · `donchian_d20_squeeze` · 8.6× · p 1.00 · 5/año |
| `GBPUSD` | `momentum` | — long · `bar3atr` · 0.7× · p 0.18 · 73/año | — long · `bar3atr` · 1.4× · p 0.07 · 48/año | — long · `bar3atr` · 1.3× · p 0.53 · 23/año | — short · `bar2atr_trail` · 18.6× · p 0.58 · 10/año |
| `GBPUSD` | `patron` | — short · `run3_fade` · 0.2× · p 0.01 · 2613/año | — short · `run3_fade` · 0.2× · p 0.01 · 1324/año | — short · `run3_fade` · 0.3× · p 0.01 · 679/año | — short · `run3_fade` · 0.4× · p 0.04 · 185/año |
| `GBPUSD` | `reversion` | — short · `rsi2_up200_sma5` · 0.4× · p 0.01 · 629/año | — short · `rsi2_sma5` · 0.7× · p 0.01 · 651/año | — long · `extreme2_up200` · 0.9× · p 0.70 · 55/año | — short · `extreme3` · 7.2× · p 0.14 · 16/año |
| `GBPUSD` | `ruptura` | — short · `donchian_d85_opp` · 55.5× · p 1.00 · 3/año | — short · `channel55_volup` · 0.9× · p 0.98 · 66/año | — short · `donchian_d85_opp` · 67.6× · p 1.00 · 3/año | — short · `channel20` · 4.2× · p 0.60 · 59/año |
| `GBPUSD` | `sesion` | — short · `prev_day_break` · 1.8× · p 1.00 · 52/año | — short · `prev_day_break` · 1.9× · p 1.00 · 50/año | — short · `prev_day_break` · 0.9× · p 1.00 · 48/año | — short · `prev_day_break` · 3.5× · p 1.00 · 39/año |
| `GBPUSD` | `tendencia` | — short · `tsmom_d120_run` · 56.8× · p 0.84 · 3/año | — short · `tsmom_d120_run` · 56.1× · p 0.87 · 3/año | — short · `tsmom_d120_run` · 56.2× · p 0.88 · 3/año | — short · `tsmom_d120_run` · 55.1× · p 0.86 · 3/año |
| `GBPUSD` | `volatilidad` | — short · `donchian_d20_squeeze` · 19.1× · p 1.00 · 6/año | — short · `donchian_d20_squeeze` · 19.2× · p 1.00 · 6/año | — short · `donchian_d20_squeeze` · 21.0× · p 1.00 · 6/año | — short · `donchian_d20_squeeze` · 19.0× · p 1.00 · 6/año |
| `NIKKEI225` | `momentum` | — long · `noise_k05` · 1.6× · p 0.59 · 73/año | — long · `noise_k05` · 2.0× · p 0.41 · 70/año | — long · `noise_k10` · 2.6× · p 0.34 · 17/año | **B** long · `bar2atr_trail` · 25.8× · p 0.05 · 5/año |
| `NIKKEI225` | `patron` | — long · `run3_fade` · 0.0× · p 0.01 · 1396/año | — short · `run3_fade` · 0.0× · p 0.01 · 882/año | — long · `run3_fade` · 0.1× · p 0.01 · 404/año | — long · `run3_fade` · 0.4× · p 0.95 · 115/año |
| `NIKKEI225` | `reversion` | — long · `d1_down3_1d` · 3.1× · p 0.84 · 20/año | — long · `d1_down3_1d` · 3.1× · p 0.83 · 20/año | — long · `ibs_low_volhigh_up_1d` · 7.0× · p 0.86 · 11/año | — long · `extreme2_up200` · 6.7× · p 0.59 · 17/año |
| `NIKKEI225` | `ruptura` | — long · `carry_crash_10d` · 70.5× · p 1.00 · 0/año | — long · `channel55_up200` · 0.4× · p 0.74 · 105/año | — short · `carry_crash_10d` · 14.7× · p 1.00 · 1/año | **C** long · `channel55` · 2.2× · p 0.55 · 43/año |
| `NIKKEI225` | `sesion` | — long · `prev_day_break` · 1.1× · p 1.00 · 49/año | — long · `prev_day_break` · 1.1× · p 1.00 · 47/año | — long · `prev_day_break` · 1.7× · p 1.00 · 43/año | — long · `prev_day_break` · 1.1× · p 1.00 · 39/año |
| `NIKKEI225` | `tendencia` | — long · `tsmom_d120_run` · 23.0× · p 0.59 · 4/año | — long · `tsmom_d120_run` · 23.5× · p 0.59 · 4/año | — long · `tsmom_d120_run` · 23.8× · p 0.59 · 4/año | — long · `tsmom_d120_run` · 24.1× · p 0.59 · 4/año |
| `NIKKEI225` | `volatilidad` | — long · `noise_k05_nr4` · 2.3× · p 0.53 · 16/año | — long · `noise_k05_nr4` · 2.3× · p 0.59 · 16/año | — long · `noise_k05_nr4` · 2.0× · p 0.76 · 15/año | — long · `donchian_d20_squeeze` · 9.8× · p 1.00 · 6/año |
| `UKOIL` | `momentum` | — short · `bar3atr` · 0.2× · p 0.02 · 81/año | — short · `bar2atr_up200` · 0.3× · p 0.16 · 75/año | — short · `bar2atr_hold16` · 0.4× · p 0.72 · 57/año | — short · `bar2atr_hold16` · 0.6× · p 1.00 · 15/año |
| `UKOIL` | `patron` | — long · `run3_fade` · 0.0× · p 0.01 · 2127/año | — long · `run3_fade` · 0.0× · p 0.01 · 1099/año | — long · `run3_fade` · 0.0× · p 0.02 · 563/año | — short · `run3_fade` · 0.1× · p 0.36 · 178/año |
| `UKOIL` | `reversion` | — short · `extreme2_mean` · 0.2× · p 0.33 · 347/año | — short · `extreme2_hold24` · 0.3× · p 0.90 · 169/año | — short · `extreme2_up200` · 0.4× · p 0.74 · 50/año | — long · `extreme3` · 1.1× · p 0.57 · 23/año |
| `UKOIL` | `ruptura` | — short · `carry_crash_10d` · 25.2× · p 1.00 · 0/año | — short · `channel55_up200` · 0.2× · p 0.89 · 74/año | — short · `channel100_hold24` · 0.4× · p 0.99 · 79/año | — short · `channel100_hold24` · 3.0× · p 0.31 · 27/año |
| `UKOIL` | `sesion` | — short · `prev_day_break` · -0.3× · p 1.00 · 49/año | — short · `prev_day_break` · -0.4× · p 1.00 · 48/año | — short · `prev_day_break` · -0.2× · p 1.00 · 45/año | — short · `prev_day_break` · -0.0× · p 1.00 · 38/año |
| `UKOIL` | `tendencia` | — short · `tsmom_d120_run` · 4.4× · p 0.80 · 4/año | — short · `tsmom_d120_run` · 4.3× · p 0.83 · 4/año | — long · `strong_d20_21d` · 4.6× · p 0.29 · 6/año | — short · `tsmom_d120_run` · 4.5× · p 0.80 · 4/año |
| `UKOIL` | `volatilidad` | — short · `donchian_d20_squeeze` · 8.2× · p 1.00 · 5/año | — short · `donchian_d20_squeeze` · 7.7× · p 1.00 · 5/año | — short · `donchian_d20_squeeze` · 10.9× · p 0.83 · 5/año | — long · `donchian_d20_squeeze` · 2.6× · p 0.90 · 5/año |
| `USA500` | `momentum` | **C** long · `noise_k07` · 2.9× · p 0.53 · 47/año | — long · `noise_k07` · 2.6× · p 0.73 · 45/año | — long · `noise_k07` · 2.3× · p 0.88 · 42/año | — long · `bar2atr_trail` · 15.4× · p 1.00 · 8/año |
| `USA500` | `patron` | — long · `run3_fade` · 0.1× · p 0.01 · 1517/año | — long · `run3_fade` · 0.1× · p 0.01 · 792/año | — long · `run3_fade` · 0.2× · p 0.05 · 409/año | — short · `run3_fade` · -0.0× · p 0.01 · 147/año |
| `USA500` | `reversion` | — long · `rsi2_voldn_sma5` · 0.3× · p 0.21 · 502/año | — long · `extreme2_voldn_mean` · 1.5× · p 0.39 · 82/año | **C** long · `extreme2_voldn_mean` · 3.1× · p 0.47 · 42/año | — long · `extreme2_voldn_mean` · 13.7× · p 0.56 · 12/año |
| `USA500` | `ruptura` | — long · `donchian_d85_opp` · 30.5× · p 0.89 · 4/año | — long · `donchian_d85_opp` · 27.6× · p 0.95 · 4/año | — long · `channel55_volup` · 1.9× · p 0.75 · 37/año | — long · `donchian_d85_opp` · 34.6× · p 0.83 · 5/año |
| `USA500` | `sesion` | — long · `prev_day_break` · 1.4× · p 1.00 · 53/año | — long · `prev_day_break` · 2.1× · p 1.00 · 50/año | — long · `prev_day_break` · 2.3× · p 1.00 · 47/año | — long · `prev_day_break` · 3.9× · p 1.00 · 38/año |
| `USA500` | `tendencia` | — long · `fast_d5_20_run` · 33.3× · p 0.50 · 8/año | — long · `fast_d5_20_run` · 33.2× · p 0.48 · 8/año | — long · `fast_d5_20_run` · 33.1× · p 0.50 · 8/año | — long · `fast_d5_20_run` · 32.3× · p 0.40 · 8/año |
| `USA500` | `volatilidad` | — long · `noise_k05_nr4` · 3.1× · p 0.68 · 20/año | — long · `noise_k05_nr4` · 2.9× · p 0.74 · 19/año | — long · `donchian_d20_squeeze` · 48.7× · p 0.75 · 6/año | — long · `donchian_d20_squeeze` · 43.6× · p 0.74 · 6/año |
| `USATEC` | `momentum` | **C** long · `noise_k07` · 2.9× · p 0.45 · 47/año | — short · `bar3atr` · 1.4× · p 0.34 · 51/año | — long · `noise_k05` · 2.7× · p 0.84 · 72/año | — long · `bar2atr_trail` · 23.0× · p 1.00 · 8/año |
| `USATEC` | `patron` | — long · `run3_fade` · 0.1× · p 0.01 · 1677/año | — long · `run3_fade` · 0.0× · p 0.01 · 851/año | — long · `run3_fade` · 0.1× · p 0.10 · 427/año | — long · `run3_fade` · 0.3× · p 0.74 · 99/año |
| `USATEC` | `reversion` | — long · `out10_counter` · 48.1× · p 0.54 · 9/año | — long · `out10_counter` · 48.2× · p 0.52 · 9/año | — long · `rsi2_voldn_sma5` · 1.2× · p 0.53 · 129/año | — long · `out10_counter` · 50.1× · p 0.57 · 9/año |
| `USATEC` | `ruptura` | — long · `channel20` · 0.6× · p 0.53 · 757/año | — short · `channel55_up200` · 3.7× · p 0.65 · 14/año | — long · `donchian_d20_trail` · 47.1× · p 0.86 · 5/año | — long · `donchian_d20_volup` · 7.1× · p 0.48 · 4/año |
| `USATEC` | `sesion` | — long · `prev_day_break` · 4.7× · p 1.00 · 52/año | — long · `prev_day_break` · 4.7× · p 1.00 · 49/año | — long · `prev_day_break` · 4.8× · p 1.00 · 47/año | — long · `prev_day_break` · 7.7× · p 1.00 · 37/año |
| `USATEC` | `tendencia` | — long · `tsmom_d60_run` · 82.9× · p 0.59 · 4/año | — long · `tsmom_d60_run` · 83.3× · p 0.55 · 4/año | — long · `tsmom_d60_run` · 82.1× · p 0.64 · 4/año | — long · `tsmom_d60_run` · 82.0× · p 0.65 · 4/año |
| `USATEC` | `volatilidad` | — long · `noise_k05_nr4` · 4.4× · p 0.60 · 23/año | — long · `noise_k05_nr4` · 4.0× · p 0.75 · 22/año | — long · `noise_k05_nr4` · 4.7× · p 0.53 · 21/año | — long · `noise_k05_nr4` · 4.1× · p 0.95 · 18/año |
| `USDCAD` | `momentum` | — short · `bar3atr` · 0.1× · p 1.00 · 52/año | — short · `bar2atr_volup` · 0.7× · p 0.79 · 52/año | — short · `bar2atr_volup` · 0.2× · p 1.00 · 27/año | — long · `bar3atr` · 6.5× · p 0.05 · 3/año |
| `USDCAD` | `patron` | — long · `run3_fade` · 0.1× · p 0.01 · 2634/año | — long · `run3_fade` · 0.2× · p 0.01 · 1328/año | — long · `run3_fade` · 0.3× · p 0.01 · 683/año | — long · `run3_fade` · 0.8× · p 0.06 · 176/año |
| `USDCAD` | `reversion` | — long · `keltner225_mean` · 0.9× · p 0.01 · 307/año | — long · `rsi2_voldn_sma5` · 0.6× · p 0.01 · 368/año | **C** long · `rsi2_sma5` · 1.0× · p 0.01 · 327/año | **C** long · `down3_up200_sma5` · 3.1× · p 0.06 · 43/año |
| `USDCAD` | `ruptura` | — short · `carry_crash_10d` · 30.3× · p 1.00 · 0/año | — short · `carry_crash_opp5` · 256.4× · p 1.00 · 0/año | — short · `carry_crash_opp5` · 253.1× · p 1.00 · 0/año | — short · `carry_crash_opp5` · 253.1× · p 1.00 · 0/año |
| `USDCAD` | `sesion` | — long · `prev_day_break` · 1.7× · p 1.00 · 50/año | — long · `prev_day_break` · 1.0× · p 1.00 · 48/año | — long · `prev_day_break` · 1.2× · p 1.00 · 45/año | — long · `prev_day_break` · 1.9× · p 1.00 · 38/año |
| `USDCAD` | `tendencia` | — long · `fast_d5_20_run` · 12.1× · p 0.98 · 9/año | — long · `fast_d5_20_run` · 12.2× · p 0.98 · 9/año | — long · `fast_d5_20_run` · 12.2× · p 0.98 · 9/año | — long · `tsmom_d120_run` · 28.5× · p 0.98 · 4/año |
| `USDCAD` | `volatilidad` | — long · `noise_k05_nr4` · 0.3× · p 1.00 · 26/año | — long · `noise_k05_nr4` · 0.2× · p 1.00 · 25/año | — long · `noise_k05_nr4` · 0.3× · p 1.00 · 23/año | — long · `noise_k05_nr4` · 2.4× · p 0.80 · 20/año |
| `USDCHF` | `momentum` | — long · `bar3atr` · 1.2× · p 0.05 · 68/año | — long · `bar3atr` · 1.5× · p 0.36 · 44/año | **B** short · `bar2atr_volup` · 2.4× · p 0.05 · 24/año | — short · `bar2atr_trail` · 11.3× · p 0.64 · 11/año |
| `USDCHF` | `patron` | — short · `run3_fade` · 0.1× · p 0.01 · 2549/año | — short · `run3_fade` · 0.2× · p 0.01 · 1311/año | — long · `run3_fade` · 0.3× · p 0.01 · 643/año | — long · `run3_fade` · -0.0× · p 0.13 · 178/año |
| `USDCHF` | `reversion` | — short · `rsi2_sma5` · 0.3× · p 0.01 · 1294/año | — short · `rsi2_sma5` · 0.5× · p 0.01 · 649/año | — long · `down3_sma5` · 0.6× · p 0.03 · 334/año | — short · `rsi2_voldn_sma5` · 0.9× · p 0.91 · 52/año |
| `USDCHF` | `ruptura` | — long · `carry_crash_10d` · 112.7× · p 1.00 · 0/año | — long · `carry_crash_10d` · 118.4× · p 1.00 · 0/año | — long · `carry_crash_10d` · 118.4× · p 1.00 · 0/año | — long · `channel200_hold48` · 6.5× · p 0.89 · 19/año |
| `USDCHF` | `sesion` | — short · `prev_day_break` · -1.6× · p 1.00 · 52/año | — short · `prev_day_break` · -0.6× · p 1.00 · 49/año | — short · `prev_day_break` · -0.0× · p 1.00 · 45/año | — short · `prev_day_break` · -0.3× · p 1.00 · 38/año |
| `USDCHF` | `tendencia` | — short · `fast_d5_20_quiet_run` · 11.7× · p 0.84 · 6/año | — short · `fast_d5_20_quiet_run` · 11.6× · p 0.87 · 6/año | — short · `fast_d5_20_quiet_run` · 11.7× · p 0.87 · 6/año | — short · `fast_d5_20_quiet_run` · 12.6× · p 0.80 · 6/año |
| `USDCHF` | `volatilidad` | — long · `donchian_d20_squeeze` · 4.1× · p 1.00 · 6/año | — long · `donchian_d20_squeeze` · 3.0× · p 1.00 · 6/año | — long · `donchian_d20_squeeze` · 2.6× · p 1.00 · 6/año | — long · `donchian_d20_squeeze` · 6.8× · p 0.99 · 6/año |
| `USDJPY` | `momentum` | — long · `bar2atr` · 0.6× · p 0.11 · 219/año | **C** long · `bar2atr_trail` · 3.3× · p 0.05 · 77/año | **C** long · `noise_k05` · 2.7× · p 0.09 · 79/año | **C** long · `noise_k03` · 2.6× · p 0.10 · 107/año |
| `USDJPY` | `patron` | — long · `run3_fade` · 0.1× · p 0.01 · 2483/año | — short · `run3_fade` · 0.1× · p 0.01 · 1350/año | — long · `run3_fade` · 0.5× · p 0.01 · 631/año | — short · `run3_follow` · 0.5× · p 0.88 · 180/año |
| `USDJPY` | `reversion` | **C** long · `keltner225_mean` · 1.0× · p 0.01 · 311/año | — long · `down3_up200_sma5` · 0.7× · p 0.01 · 307/año | **C** long · `down3_sma5` · 1.0× · p 0.01 · 328/año | **C** long · `day_down_volhigh_1d` · 3.8× · p 0.32 · 46/año |
| `USDJPY` | `ruptura` | — short · `donchian_d20_volup` · 37.5× · p 1.00 · 2/año | — short · `donchian_d20_volup` · 33.8× · p 1.00 · 2/año | — short · `channel55_volup` · 1.6× · p 0.93 · 26/año | — long · `channel200_hold48` · 31.8× · p 0.11 · 21/año |
| `USDJPY` | `sesion` | — long · `prev_day_break` · 0.2× · p 1.00 · 50/año | — long · `prev_day_break` · -0.9× · p 1.00 · 48/año | — long · `prev_day_break` · -1.8× · p 1.00 · 47/año | — long · `prev_day_break` · -2.6× · p 1.00 · 40/año |
| `USDJPY` | `tendencia` | — short · `chan_30_40_run` · 6.8× · p 0.55 · 11/año | — short · `chan_30_40_run` · 7.4× · p 0.46 · 11/año | — short · `chan_30_40_run` · 6.9× · p 0.52 · 11/año | — short · `chan_30_40_run` · 7.4× · p 0.42 · 11/año |
| `USDJPY` | `volatilidad` | — long · `noise_k05_nr4` · 1.5× · p 0.91 · 23/año | — long · `noise_k05_nr4` · 1.6× · p 0.92 · 22/año | — long · `donchian_d20_squeeze` · 2.4× · p 1.00 · 6/año | — long · `narrow_break` · 1.7× · p 0.63 · 71/año |
| `USOIL` | `momentum` | — short · `bar3atr` · 0.1× · p 0.22 · 93/año | — short · `bar1atr` · 0.1× · p 0.07 · 919/año | — short · `bar3atr` · 0.2× · p 0.65 · 33/año | — short · `bar2atr_hold16` · 1.0× · p 0.89 · 15/año |
| `USOIL` | `patron` | — long · `run3_fade` · 0.0× · p 0.01 · 2151/año | — long · `run3_fade` · 0.0× · p 0.01 · 1124/año | — long · `run3_fade` · 0.0× · p 0.01 · 582/año | — short · `run3_fade` · 0.0× · p 0.21 · 176/año |
| `USOIL` | `reversion` | — short · `extreme3` · 0.1× · p 0.52 · 295/año | — short · `d1_down3_1d` · 0.4× · p 0.96 · 30/año | — short · `d1_down3_1d` · 0.4× · p 0.93 · 30/año | — long · `extreme3` · 0.8× · p 0.52 · 22/año |
| `USOIL` | `ruptura` | — short · `donchian_d20_opp` · 8.9× · p 0.95 · 5/año | — short · `donchian_d20_opp` · 8.5× · p 0.95 · 5/año | — short · `donchian_d20_opp` · 9.2× · p 0.92 · 4/año | — short · `channel55_trail` · 3.6× · p 0.30 · 11/año |
| `USOIL` | `sesion` | — short · `prev_day_break` · 0.2× · p 1.00 · 49/año | — short · `prev_day_break` · 0.2× · p 1.00 · 47/año | — short · `prev_day_break` · 0.3× · p 1.00 · 44/año | — short · `prev_day_break` · 0.4× · p 1.00 · 38/año |
| `USOIL` | `tendencia` | — long · `strong_d20_21d` · 2.2× · p 0.72 · 7/año | — long · `strong_d20_21d` · 2.1× · p 0.72 · 7/año | — long · `strong_d20_21d` · 1.8× · p 0.76 · 7/año | — short · `pullback_mom60_trail` · 3.4× · p 0.55 · 13/año |
| `USOIL` | `volatilidad` | — short · `noise_k05_nr4` · 0.4× · p 0.64 · 24/año | — long · `donchian_d20_squeeze` · 0.8× · p 1.00 · 5/año | — short · `noise_k05_nr4` · 0.4× · p 0.61 · 22/año | — short · `noise_k05_nr4` · 0.2× · p 0.95 · 19/año |
| `XAGUSD` | `momentum` | — short · `noise_k07` · 1.0× · p 0.84 · 49/año | — short · `noise_k07` · 1.1× · p 0.69 · 46/año | — long · `bar3atr` · 1.4× · p 0.80 · 21/año | **B** long · `bar2atr_up200` · 4.9× · p 0.03 · 5/año |
| `XAGUSD` | `patron` | — short · `run3_fade` · 0.0× · p 0.01 · 2167/año | — short · `run3_fade` · 0.1× · p 0.01 · 1150/año | — long · `run3_fade` · 0.1× · p 0.01 · 590/año | — short · `run3_fade` · 0.1× · p 0.13 · 182/año |
| `XAGUSD` | `reversion` | — short · `extreme2_up200_mean` · 0.6× · p 0.01 · 160/año | — short · `rsi2_sma5` · 0.3× · p 0.01 · 611/año | — long · `down3_up200_sma5` · 0.6× · p 0.04 · 129/año | — long · `extreme3` · 1.2× · p 0.93 · 14/año |
| `XAGUSD` | `ruptura` | — long · `donchian_d20_opp` · 11.9× · p 0.94 · 5/año | — short · `donchian_d20_trail` · 16.9× · p 0.89 · 4/año | — short · `channel200_hold48` · 3.3× · p 0.77 · 48/año | — long · `channel55_up200` · 4.2× · p 0.34 · 14/año |
| `XAGUSD` | `sesion` | — long · `prev_day_break` · 0.6× · p 1.00 · 49/año | — long · `prev_day_break` · 0.6× · p 1.00 · 46/año | — long · `prev_day_break` · 0.0× · p 1.00 · 44/año | — long · `prev_day_break` · 0.5× · p 1.00 · 37/año |
| `XAGUSD` | `tendencia` | — short · `tsmom_d120_run` · 8.2× · p 0.73 · 5/año | — short · `tsmom_d120_run` · 8.0× · p 0.74 · 5/año | — short · `tsmom_d20_run` · 8.4× · p 0.73 · 11/año | — short · `chan_30_40_run` · 5.6× · p 0.62 · 7/año |
| `XAGUSD` | `volatilidad` | — short · `donchian_d20_squeeze` · 1.3× · p 1.00 · 6/año | — long · `noise_k05_nr4` · 1.0× · p 0.93 · 25/año | — short · `donchian_d20_squeeze` · 2.7× · p 1.00 · 6/año | — long · `noise_k05_nr4` · 1.2× · p 0.84 · 20/año |
| `XAUUSD` | `momentum` | **C** long · `bar3atr` · 1.5× · p 0.03 · 80/año | **C** long · `bar2atr_trail` · 2.8× · p 0.05 · 103/año | **C** long · `bar2atr_hold16` · 3.9× · p 0.07 · 70/año | — short · `bar2atr` · 11.0× · p 0.05 · 18/año |
| `XAUUSD` | `patron` | — long · `run3_fade` · 0.1× · p 0.01 · 2571/año | — long · `run3_fade` · 0.2× · p 0.01 · 1265/año | — long · `run3_fade` · 0.2× · p 0.01 · 639/año | — short · `run3_fade` · 0.6× · p 0.03 · 186/año |
| `XAUUSD` | `reversion` | — long · `rsi2_up200_sma5` · 0.4× · p 0.01 · 683/año | — long · `rsi2_voldn_sma5` · 0.5× · p 0.02 · 397/año | — long · `rsi2_sma5` · 0.8× · p 0.10 · 316/año | — long · `d1_down3_1d` · 4.1× · p 0.66 · 25/año |
| `XAUUSD` | `ruptura` | — short · `donchian_d20_trail` · 4.4× · p 1.00 · 5/año | **C** long · `channel55_trail` · 2.1× · p 0.28 · 93/año | **C** long · `channel55_trail` · 3.7× · p 0.32 · 46/año | — short · `carry_crash_opp5` · 62.1× · p 1.00 · 0/año |
| `XAUUSD` | `sesion` | — long · `prev_day_break` · 2.5× · p 0.96 · 51/año | — long · `prev_day_break` · 2.3× · p 0.99 · 49/año | — long · `prev_day_break` · 3.5× · p 0.90 · 45/año | — long · `prev_day_break` · 3.2× · p 1.00 · 38/año |
| `XAUUSD` | `tendencia` | — long · `look100_hold24` · 0.5× · p 0.38 · 12647/año | — long · `look48_hold4` · 0.2× · p 0.16 · 6325/año | — long · `look48_hold4` · 0.3× · p 0.46 · 3207/año | — long · `tsmom_d252_run` · 22.3× · p 0.74 · 4/año |
| `XAUUSD` | `volatilidad` | — short · `donchian_d20_squeeze` · 4.8× · p 1.00 · 5/año | — short · `donchian_d20_squeeze` · 2.1× · p 1.00 · 5/año | — long · `donchian_d20_squeeze` · 4.7× · p 1.00 · 6/año | — long · `donchian_d20_squeeze` · 10.9× · p 1.00 · 6/año |

### 6.2 La corrección alternativa — tú eliges

El veredicto de cabecera corrige las 14.364 pruebas juntas (umbral efectivo: p cruda ≤ 0,0017). No es
la opción dura que parece: las familias densas (`patron`, la estructura de `reversion`, `volatilidad`)
meten cientos de p diminutas y suben el umbral para todas; `tendencia` y `ruptura`, corregidas solas,
necesitarían p ≤ 0,00001 y no nombran nada. La alternativa defendible es **Benjamini-Hochberg dentro de
cada familia**: cada familia responde a su propia pregunta con su propio 5 %. A favor: no deja que una
familia viva del umbral de otra. En contra: es más dura con las familias dispersas y más blanda con
`reversion`. Por activo se probó también: pasarían 6 medidas en vez de 2 (EURUSD, USDCAD, USDJPY, XAUUSD). **La elección es tuya; el código no cambia sola.**


Con la corrección alternativa (Benjamini-Hochberg dentro de cada familia): 4 celdas-familia pasan los cuatro filtros, frente a 2 con la corrección de cabecera; 11 cambian de nota.

| activo | celda | familia | medida | efecto | p cruda | p corr. (todas) | p corr. (familia) | nota | nota alternativa |
|---|---|---|---|---|---|---|---|---|---|
| `DJ30` | M30 short | `momentum` | `bar2atr` | 1.45× | 0.001 | 0.021 | 0.257 | C | — |
| `DJ30` | H1 long | `ruptura` | `channel55_up200` | 3.14× | 0.001 | 0.030 | 1.000 | A | C |
| `EURUSD` | M15 short | `momentum` | `bar3atr` | 2.30× | 0.001 | 0.021 | 0.257 | A | C |
| `EURUSD` | H1 short | `reversion` | `ibs_low_volhigh_1d` | 11.10× | 0.003 | 0.072 | 0.046 | — | B |
| `GBPJPY` | H1 long | `momentum` | `bar3atr` | 3.91× | 0.000 | 0.011 | 0.257 | B | — |
| `NIKKEI225` | H4 long | `momentum` | `bar2atr_trail` | 25.83× | 0.002 | 0.045 | 0.257 | B | — |
| `USDCAD` | H4 long | `reversion` | `down3_up200_sma5` | 3.08× | 0.002 | 0.059 | 0.038 | C | A |
| `USDCHF` | H1 short | `momentum` | `bar2atr_volup` | 2.40× | 0.002 | 0.045 | 0.257 | B | — |
| `USDJPY` | H1 short | `reversion` | `rsi2_up200_sma5` | 1.20× | 0.002 | 0.059 | 0.038 | — | C |
| `XAGUSD` | H4 long | `momentum` | `bar2atr_up200` | 4.93× | 0.001 | 0.030 | 0.257 | B | — |
| `XAUUSD` | M15 long | `momentum` | `bar3atr` | 1.54× | 0.001 | 0.030 | 0.257 | C | — |

### 6.3 Medido pero descartado por usar reloj

Estas medidas necesitan la hora, una franja de sesión o el día de la semana. Se midieron y **no se
proponen**: no lideran familia, no tienen nota y no llegan al tablero. La nota que tendrían se deja
aquí para que el conocimiento no se pierda («mejor hora», «mejor franja» y «mejor día» se eligen
mirando: su p paga la elección, su múltiplo no).


| activo | celda | medida | elegido | nota que tendría | efecto | p corr. | op/año |
|---|---|---|---|---|---|---|---|
| `DAX40` | H4 long | `band_range` | band london | C | 2.05× | 0.540 | 86 |
| `DAX40` | M15 long | `best_band` | band asia | C | 1.12× | 0.038 | 244 |
| `DAX40` | M30 long | `best_band` | band asia | C | 1.12× | 0.045 | 244 |
| `DAX40` | H1 long | `best_band` | band asia | C | 1.12× | 0.038 | 244 |
| `EURUSD` | H4 short | `best_band` | band london | C | 1.81× | 0.045 | 260 |
| `EURUSD` | H4 long | `best_hour` | hour 4 | C | 1.30× | 0.011 | 261 |
| `GBPUSD` | M15 short | `best_weekday` | weekday 4 | C | 5.18× | 0.223 | 52 |
| `GBPUSD` | M30 short | `best_weekday` | weekday 4 | C | 5.18× | 0.216 | 52 |
| `GBPUSD` | H1 short | `best_weekday` | weekday 4 | C | 5.18× | 0.216 | 52 |
| `GBPUSD` | H4 short | `best_weekday` | weekday 4 | C | 5.18× | 0.212 | 52 |
| `USDCAD` | H4 short | `best_hour` | hour 20 | C | 1.16× | 0.011 | 260 |
| `USDCAD` | H4 long | `best_hour` | hour 0 | C | 1.15× | 0.011 | 261 |
| `USDCHF` | H4 short | `best_band` | band new_york | C | 1.59× | 0.011 | 260 |
| `USDJPY` | H4 short | `best_band` | band asia | C | 1.46× | 0.011 | 261 |
| `USDJPY` | H4 short | `best_hour` | hour 4 | C | 1.37× | 0.011 | 261 |
| `USDJPY` | M30 short | `best_band` | band asia | C | 1.25× | 0.045 | 261 |
| `USDJPY` | H4 long | `best_band` | band london | C | 1.01× | 0.045 | 260 |
| `XAUUSD` | H1 long | `best_hour` | hour 1 | C | 1.31× | 0.011 | 257 |
| `XAUUSD` | H4 long | `best_hour` | hour 0 | C | 1.22× | 0.011 | 260 |


De la bibliografía, descartado por la misma razón (no se mide):

| id | qué afirma | fuente | verificado |
|---|---|---|---|
| `MOM-18-first-last-half-hour-us` | both (sign of the first half-hour return) — R² 1.6% (first half-hour), 2.6% adding the 12th half-hour; out-of-sample R² 1.69%; timing strategy SD 6.19%/yr, Sharpe 1.08; by first-half-hour volatility tercile the strategy earns 0.54% (low), 4.75% (medium), 14.73 | Gao, Han, Li, Zhou, 'Intraday Momentum: The First Half-Hour Return Predicts the Last Half-Hour Return' (Oct 2014 draft; published as 'Market intraday momentum', JFE 2018) — https://www.smallake.kr/wp-content/uploads/2015/01/SSRN-id2440866.pdf (full text read) | yes (2014 draft) |
| `MOM-19-rest-of-day-predicts-last-30min` | both — 'economically and statistically highly significant' — no numbers on the page read | Baltussen, Da, Lammers, Martens (2021), 'Hedging demand and market intraday momentum', JFE 142:377-403 — https://pure.eur.nl/en/publications/hedging-demand-and-market-intraday-momentum/ (abstract page only) | **⚠️ abstract only** |
| `MOM-20-intraday-tsmom-international` | both — pooled slope 2.86 (t = 7.53); equal-weight global ITSM portfolio Sharpe 1.26-1.77 in 2005-2017, gross | Li, Sakkas, Urquhart, 'Intraday Time Series Momentum: International Evidence' (working paper, 2020) — http://wp.lancs.ac.uk/fofi2020/files/2020/04/FoFI-2020-092-Zeming-Li.pdf (full text read) | yes |
| `MOM-21a-noise-area-breakout` | both; the paper finds no relation between VIX and SHORT-trade profit — 2007-2024: total 1,985% net, 19.6%/yr, Sharpe 1.33, hit ratio 43%; costs $0.0035/share + $0.001 slippage; Sharpe ≈1.5 on all days, ≈3.5 when VIX > 40; average day +12 bp (t 5.34) | Zarattini, Aziz, Barbon, 'Beat the Market: An Effective Intraday Momentum Strategy for S&P500 ETF (SPY)' (Swiss Finance Institute RP 24-97, v. Feb 2025) — https://alexandria.unisg.ch/bitstreams/a99aba00-f967-49b3-aceb-f544dc386e0b/download (full text read) | yes |
| `MOM-23-opening-gap-eurostoxx` | both — APR 13%, Sharpe 1.4, gross | Chan, 'Algorithmic Trading' (2013), ch. 7 'Intraday Momentum Strategies', pp. 155-157 (PDF pp. 173-175) — ~/Desktop/Books (text read) — Example 7.1 | yes |
| `MOM-24-opening-gap-gbpusd` | both — APR 7.2%, Sharpe 1.3, gross | Chan, 'Algorithmic Trading' (2013), ch. 7 'Intraday Momentum Strategies', pp. 155-157 (PDF pp. 173-175) — ~/Desktop/Books (text read) — p. 157 | yes |
| `MOM-25-crude-first-half-hour` | both — USO: β = 0.0118, t = 2.86, R² = 0.67% (2007-2019). The 2023 paper gives no figure in its abstract. An R² of 0.729% in-sample for crude futures (Wen, Gong, Ma, Xu 2021, Economic Modelling) was seen only in a search summary: not verified | Xu, Bouri, Saeed, Wen (2020), 'Intraday return predictability: Evidence from commodity ETFs and their related volatility indices', Resources Policy — https://pmc.ncbi.nlm.nih.gov/articles/PMC7480318/ (page read through the fetch summariser) ; Wen, Indriawan, Lien, Xu (2023), 'Intraday Return Predictability in the Crude Oil Market: The Role of EIA Inventory Announcements', The Energy Journal 44(5):149-172 — https://ideas.repec.org/a/sae/enejou/v44y2023i5p149-172.html (abstract only) | **⚠️ XU via summariser; WEN23 abstract only** |
| `MOM-26-metals-late-session-half-hours` | both — GLD: β = 0.0436, t = 3.03, R² = 0.49% (2004-2019); SLV: β = 0.1260, t = 3.03, R² = 1.72% (2006-2020) | Xu, Bouri, Saeed, Wen (2020), 'Intraday return predictability: Evidence from commodity ETFs and their related volatility indices', Resources Policy — https://pmc.ncbi.nlm.nih.gov/articles/PMC7480318/ (page read through the fetch summariser) | **⚠️ via summariser** |
| `NEG-27-mnq-ohlcv-intraday-momentum` | both — none passed: eleven families had gross returns of 0.07-1.50 index points, below a 2.0-point friction; two session-based controls did pass (OOS t 3.11 and 4.30) | 'Structural Limits of OHLCV-Based Intraday Momentum Signals in MNQ Futures: A Systematic Falsification Study', arXiv:2605.04004 — https://arxiv.org/abs/2605.04004 (abstract only) | **⚠️ abstract only** |
| `SES-28-overnight-drift-us-index` | long — +3.7%/yr = 1.48 bp per day in that one hour; positive in 20 of 23 years, significant in 17; hours 24-01, 01-02, 02-03 earn 0.46, 0.43, 1.5 bp; the 09:00-10:00 NY hour is negative only in recessions | Boyarchenko, Larsen, Whelan, 'The Overnight Drift', FRB New York Staff Report 917 (2020, rev. 2022) — https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr917.pdf (text read) | yes |
| `SES-29-overnight-vs-intraday-indices` | long overnight; intraday (cash open→close) negative — cumulative overnight vs intraday, from 1990 or first data to Sep 2020, as extracted from Figure 1: SPY +1288% vs -8%; Nasdaq Comp. +3402% vs -30%; DAX +1532% vs -64%; Nikkei 225 +1142% vs -95%. Cooper, Clif | Knuteson (2020), 'Strikingly Suspicious Overnight and Intraday Returns', arXiv:2010.01727 — https://arxiv.org/pdf/2010.01727 (text read; figures quoted from Figure 1 as extracted) | **⚠️ text read; figure labels paired by position** |
| `SES-30-gold-overnight` | long — GLD: +0.04% average per overnight trade, ≈11.4%/yr, intraday 'essentially flat'; period not stated on the page. Blose et al. report COMEX overnight significantly positive and day significantly negative for 1985-2012 (search summary only) | QuantifiedStrategies, 'A Quantitative Look at the Gold Overnight Strategy' — https://quantifiedstrategies.substack.com/p/a-quantitative-look-at-the-gold-overnight (page read). The academic source, Blose, Gondhalekar & Kort (2018) J. Economics and Finance 42, was NOT opened (paywall): not verified | **⚠️ blog page yes; academic paper NOT verified** |
| `SES-31-fx-fix-reversals` | USD long before each fix, USD short after — dollar portfolio: +5.3%/yr (2.1 bp/day, t≈12) from 17:00 NY to the Tokyo fix, -5.5%/yr (t≈9.2) after it; +4.3%/yr (t≈4.1) from the European open to the London fix, -4.8%/yr (t≈5.5) from it to the NY close. AUD -7.39% | Krohn, Mueller, Whelan, 'Foreign Exchange Fixings and Returns Around the Clock' (June 2020 version; later J. Finance 2024) — https://sites.insead.edu/facultyresearch/research/file.cfm?fid=66802 (text read) | yes |
| `SES-32-jpy-local-hours` | USDJPY down in the Asian day, up in US hours — post-Tokyo-fix reversal for JPY 7.70%/yr; other figures not extracted | Krohn, Mueller, Whelan, 'Foreign Exchange Fixings and Returns Around the Clock' (June 2020 version; later J. Finance 2024) — https://sites.insead.edu/facultyresearch/research/file.cfm?fid=66802 (text read). Ranaldo (2009, J. Banking & Finance 33:2199) documents the general time-of-day pattern; two machine summaries of its abstract disagreed on the SIGN, so its direction is NOT verified here | **⚠️ Krohn yes; Ranaldo's direction not verified** |
| `SES-33-fx-range-by-session` | none (a volatility fact) — the 08:00-12:00 NY overlap holds 70% of the European-hours range and 80% of the US-hours range; USDJPY and AUDJPY are the pairs whose Asian range equals their European one | Lien, 'Day Trading and Swing Trading the Currency Market' 2nd ed. (2008), ch. 5 Table 5.1, pp. 67-73 (PDF pp. 83-89) — ~/Desktop/Books (text read) | yes |
| `CAL-34-turn-of-month` | long — 7.2%/yr, Sharpe 1.04, volatility 6.9%, max drawdown -20.79% (Quantpedia's indicative figures) | Quantpedia, 'Turn of the Month in Equity Indexes' (summarising McConnell & Xu 2008) — https://quantpedia.com/strategies/turn-of-the-month-in-equity-indexes (page read; the paper itself not opened) | **⚠️ summary page only** |
| `CAL-35-pre-fomc-drift` | long — 'large average excess returns' accounting for 'sizable fractions of total annual realized stock returns' — no number on the page read | Lucca & Moench, 'The Pre-FOMC Announcement Drift', FRBNY Staff Report 512 / J. Finance 2015 — https://www.newyorkfed.org/research/staff_reports/sr512.html (abstract page only) | **⚠️ abstract page only** |
| `REV-46-chan-gap-fade-with-trend-filter` | long (the short mirror also reported profitable) — APR 8.7%, Sharpe 1.5 (10 stocks a day), gross | Chan, 'Algorithmic Trading' (2013), ch. 4 'Buy-on-Gap Model', pp. 92-95 (PDF pp. 110-113) — ~/Desktop/Books (text read) | yes |

## 7. El barrido de salidas y parámetros — «con salida razonable»

Estudio **aparte** (`python3 -m studies.research.marketProfile.report --sweep`, salida en
`AlgoData/research/profiles/sweep/`): responde a «¿esta estructura pasa el listón con una salida
razonable y parámetros cercanos?». Cada entrada se prueba con tres parámetros vecinos y nueve salidas:
duración fija a 0,5×, 1×, 2× y 4× la suya; trailing de 2 y de 4 ATR; para las entradas de reversión,
salida al volver a la media de 20 y a la de 5; para las de tendencia y ruptura, salida al perder el
mínimo de 20 velas y al cerrar bajo la media de 20; y un stop de 2 ATR con la duración doblada. Trece
entradas (`extreme`, `rsi_low`, `down_run`, `rsi_up100`, `rsi_up200`, `ibs_low`, `channel`,
`channel_d`, `prev_day`, `big_bar`, `band`, `tsmom_d`, `pullback`) × 3 × 9 × largo/corto = 702
variantes por celda, **53.352 pruebas**, 1.000 sorteos, sólo `build`, mismo coste, misma nula,
corregidas juntas **dentro del barrido** (una estadística que gana a los 1.000 sorteos toma la cola
normal de su z: con 53.352 pruebas la p mínima de 1.000 sorteos ya no puede ser significativa).
`patron` y `volatilidad` no tienen entrada propia en el barrido.

**Una variante elegida aquí es una hipótesis seleccionada dentro de muestra, no un hallazgo.** Su
trabajo es decir qué celdas merecen un build en SQX, que es donde está la prueba fuera de muestra.
«Meseta»: la variante pasa los cuatro filtros y al menos 2 de sus vecinas (parámetro contiguo, duración
contigua, la otra anchura de trailing) también pagan ≥ 2× con signo estable. Un pico aislado no es evidencia.

**Resultado:** 623 variantes significativas, **3 pasan los cuatro filtros, ninguna en meseta**.

| marco | celdas-familia | pasan desnudas | pasan con alguna variante | de ellas en meseta | no pagan 2× con ninguna variante |
|---|---|---|---|---|---|
| M15 | 190 | 1 | 1 | 0 | 124 |
| M30 | 190 | 0 | 1 | 0 | 108 |
| H1 | 190 | 1 | 1 | 0 | 80 |
| H4 | 190 | 0 | 0 | 0 | 39 |

Las tres que pasan (picos): USDJPY H1 largo `extreme` 3 ATR con salida a la media de 5 (2,9×, 55/año);
EURUSD M15 corto `big_bar` 3 ATR mantenida 4 velas (2,4×, 64/año — la misma celda del veredicto
desnudo); EURUSD M30 corto `big_bar` 3 ATR mantenida 2 velas (2,7×, 40/año).

**Cuánto era culpa de la salida fija:** poco. Elegir la mejor de las nueve salidas sube el efecto
mediano de 0,08× a 0,57× el coste y la parte de entradas con alguna variante que paga ≥ 2× del 7 % al
26 %; pero lo que paga no es significativo y lo significativo (casi todo reversión en M15-M30: 574
de 623) paga 0,3-0,5× en mediana con cualquier salida. De las 1.144 variantes que pagan, son estables
y frecuentes, 147 tienen p cruda ≤ 0,05 y 40 de ésas están en meseta — son las candidatas a build
(`sweep/variants.parquet`: DJ30 H1 largo `channel` 55, XAUUSD H1 largo `big_bar` 2 ATR, EURJPY H1
largo `pullback`, GBPJPY H1 largo `channel`), como apuesta, no como consecuencia.


## 8. Bibliografía: lo que dicen los libros y los artículos, junto a lo medido

Fuente: `AlgoData/research/literature/edges-2026-10-02.yaml` (62 entradas; cada fuente se cita como la
da el fichero y con su nota de verificación: **lo marcado con ⚠️ no está verificado y no debe leerse
como establecido**). Estado de cada entrada: «medido» (una medida del perfil la contrasta, celda a
celda), «sólo bibliografía» (es una prior, no una regla), «la bibliografía lo afirma y aquí no se
mide» (con el porqué) y «descartado por usar reloj» (apartado 6.3). Las reglas que en la fuente salen
«al cierre de D1» o «en la primera vela del día» se midieron reescritas sin reloj: el contexto de D1
vale para todo el día siguiente y la salida es por número de velas o por precio.

**Donde la bibliografía verificada y tu prior no dicen lo mismo** (las dos, una línea cada una):

- *Tendencia rápida en índices y FX desarrollado.* Prior: `tendencia` Alta en USDJPY y cruces del yen, Media en índices, principal en H4 en casi todo. Bibliografía (`TR-15` Hsu et al. 2016, revisado por pares; `TR-06` Kurth et al. 2026): las reglas de tendencia en divisas desarrolladas no son significativas desde los años 90 y la tendencia rápida (5-20 días) está plana en índices y FX desde 2009 salvo en baja volatilidad. Medido aquí: de acuerdo con la bibliografía (ver `TR-05`, `TR-06`, `TR-15` abajo).
- *Reversión barra a barra.* Prior: `reversion` principal en M15-M30 de índices USA y FX. Bibliografía (`NEG-47` Neely & Weller; `NEG-27`): los patrones intradía son estables pero no pagan costes realistas. Medido aquí: las dos cosas a la vez — significativa casi siempre, 0,2-0,4× el coste.
- *Reversión de índices.* Prior: Alta en largo en USA500 y DJ30. Bibliografía (`REV-36a`, `REV-37a`, `REV-38a`): sí, en la barra **diaria** y sólo en largo; DAX revierte a la semana, no al día. Medido aquí: el signo y la asimetría largo/corto coinciden; la significancia no llega.


34 «medido», 18 «descartado por usar reloj», 6 «la bibliografía lo afirma y aquí no se mide», 4 «sólo bibliografía» — 62 entradas.

| id | familia | qué afirma (dirección — tamaño) | fuente | verificado · grado | estado | lo medido aquí |
|---|---|---|---|---|---|---|
| `TR-01-tsmom-12m` | `tendencia` | both (sign of past return); per-contract 12-month profits positive for all 58 — diversified TSMOM Sharpe 1.1 gross, alpha significant vs standard factors; 1985-2009 (data from 1965) | Moskowitz, Ooi, Pedersen (2012), 'Time series momentum', J. Financial Economics 104:228-250 — https://w4.stern.nyu.edu/facdir/lpederse/papers/TimeSeriesMomentum.pdf (full text read) | yes · peer-reviewed | «medido» | 56 celdas con contraste: 4 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: AUDUSD H4 long `tsmom_d252_run` 14.4× · p corr. 0.37 (cruda 0.027) · 3/año — falla: no significativa, pocas operaciones |
| `TR-02-tsmom-1m-to-3m` | `tendencia` | both — alpha t-stats significant 'particularly when the look-back and holding periods are 12 months or less' (Table 2); all of the 12 most recent monthly lags positive, nine significant (Fig. 1) | Moskowitz, Ooi, Pedersen (2012), 'Time series momentum', J. Financial Economics 104:228-250 — https://w4.stern.nyu.edu/facdir/lpederse/papers/TimeSeriesMomentum.pdf (full text read) | yes (text; Table 2 cells not transcribed) · peer-reviewed | «medido» | 304 celdas con contraste: 3 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: GBPJPY H4 long `tsmom_d60_run` 11.2× · p corr. 0.37 (cruda 0.027) · 7/año — falla: no significativa, inestable, pocas operaciones |
| `TR-03-tsmom-extreme-markets` | `tendencia` | both — coefficient on squared market return significantly positive (Table 3 panel C); no per-regime Sharpe quoted | Moskowitz, Ooi, Pedersen (2012), 'Time series momentum', J. Financial Economics 104:228-250 — https://w4.stern.nyu.edu/facdir/lpederse/papers/TimeSeriesMomentum.pdf (full text read) | yes · peer-reviewed | «medido» | 79 celdas con contraste: 1 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: USATEC H4 long `donchian_d20_volup` 7.1× · p corr. 0.48 (cruda 0.040) · 4/año — falla: no significativa, pocas operaciones |
| `TR-04-slow-trend-ewm50-200` | `tendencia` | both — portfolio Sharpe 0.40 (±0.26) in 2009-2025 for EWM-50-200; 0.27 (±0.26) for EWM-20-80; pre-2009 Sharpe 0.70 at the 50-day scale | Kurth, Eisler, Rej, Bouchaud (2026), 'Is Trend Still Your Friend? A Microstructural Account of the Demise of Short-Term Trend-Following', arXiv:2607.01550 — https://arxiv.org/abs/2607.01550 (full text read) | yes · quantified practitioner test (academic working paper, CFM authors, not yet peer-reviewed) | «medido» | 152 celdas, ninguna llega a 30 operaciones en build: sin contraste |
| `TR-05-fast-trend-commodities` | `tendencia` | both — commodities and yields show 'no appreciable degradation' after 2008; large-tick tier Sharpe 1.0-1.2 post-break for the fast signal | Kurth, Eisler, Rej, Bouchaud (2026), 'Is Trend Still Your Friend? A Microstructural Account of the Demise of Short-Term Trend-Following', arXiv:2607.01550 — https://arxiv.org/abs/2607.01550 (full text read) | yes · quantified practitioner test (academic working paper) | «medido» | 32 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: USOIL M30 short `fast_d5_20_run` -0.4× · p corr. 1.00 (cruda 0.642) · 7/año — falla: no significativa, no paga 2×, inestable, pocas operaciones |
| `TR-06-fast-trend-lowvol-indices-fx` | `tendencia` | both — no number quoted in the text read (figure only) | Kurth, Eisler, Rej, Bouchaud (2026), 'Is Trend Still Your Friend? A Microstructural Account of the Demise of Short-Term Trend-Following', arXiv:2607.01550 — https://arxiv.org/abs/2607.01550 (full text read) | yes (statement; size not quantified) · quantified practitioner test (academic working paper) | «medido» | 104 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: DAX40 H1 short `fast_d5_20_quiet_run` 24.7× · p corr. 0.63 (cruda 0.064) · 5/año — falla: no significativa, pocas operaciones |
| `TR-07a-fitschen-h1-fx-10bars` | `tendencia` | both in the source (buy above, sell below); test long and short separately — $9.17 per trade per 100k versus a baseline of -$11.64 (buy each open, sell at close); positive in 5 of 9 years (2002 -100.85, 2010 -79.75); gross, no costs | Fitschen, 'Building Reliable Trading Systems' (2013), ch. 3 'Find the Path of Least Resistance', pp. 31-44 (PDF pp. 38-51) — ~/Desktop/Books (text read) — Table 3.10 | yes · quantified practitioner test | «medido» | 80 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: GBPJPY H4 short `fitschen_b10_1d` 1.9× · p corr. 0.65 (cruda 0.067) · 120/año — falla: no significativa, no paga 2× |
| `TR-07b-fitschen-h1-fx-10days` | `tendencia` | both in the source (buy above, sell below); test long and short separately — $9.17 per trade per 100k versus a baseline of -$11.64 (buy each open, sell at close); positive in 5 of 9 years (2002 -100.85, 2010 -79.75); gross, no costs | Fitschen, 'Building Reliable Trading Systems' (2013), ch. 3 'Find the Path of Least Resistance', pp. 31-44 (PDF pp. 38-51) — ~/Desktop/Books (text read) — Table 3.10 | yes · quantified practitioner test | «medido» | 80 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: GBPJPY H1 short `fitschen_d10_1d` 1.7× · p corr. 0.84 (cruda 0.132) · 100/año — falla: no significativa, no paga 2× |
| `TR-08a-fitschen-h1-commodities-10bars` | `tendencia` | both in the source — $30.05 per trade versus $21.26 baseline (+40%); negative in 2003-2005; gross | Fitschen, 'Building Reliable Trading Systems' (2013), ch. 3 'Find the Path of Least Resistance', pp. 31-44 (PDF pp. 38-51) — ~/Desktop/Books (text read) — Table 3.9 | yes · quantified practitioner test | «medido» | 32 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: XAUUSD H4 long `fitschen_b10_1d` 1.9× · p corr. 0.80 (cruda 0.116) · 124/año — falla: no significativa, no paga 2× |
| `TR-08b-fitschen-h1-commodities-10days` | `tendencia` | both in the source — $30.05 per trade versus $21.26 baseline (+40%); negative in 2003-2005; gross | Fitschen, 'Building Reliable Trading Systems' (2013), ch. 3 'Find the Path of Least Resistance', pp. 31-44 (PDF pp. 38-51) — ~/Desktop/Books (text read) — Table 3.9 | yes · quantified practitioner test | «medido» | 32 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: XAGUSD M15 long `fitschen_d10_1d` 0.8× · p corr. 0.58 (cruda 0.054) · 104/año — falla: no significativa, no paga 2× |
| `TR-09-fitschen-h1-stocks` | `tendencia` | long only in the source — 0.12% per trade versus 0.07% baseline; fades to 0.01-0.10% from 2005 and -0.05% in 2010; gross | Fitschen, 'Building Reliable Trading Systems' (2013), ch. 3 'Find the Path of Least Resistance', pp. 31-44 (PDF pp. 38-51) — ~/Desktop/Books (text read) — Table 3.8 | yes · quantified practitioner test | «medido» | 4 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: USATEC M30 long `fitschen_b10_1d` 3.7× · p corr. 0.99 (cruda 0.245) · 156/año — falla: no significativa |
| `TR-10-fitschen-d1-commodities-month` | `tendencia` | long tested; shorts make 1/2 to 1/3 of longs per the author — $158 per one-lot monthly trade versus $66 buy-and-hold and $23 for buying weakness (-$45 on 1980-2011); gross | Fitschen, 'Building Reliable Trading Systems' (2013), ch. 3 'Find the Path of Least Resistance', pp. 31-44 (PDF pp. 38-51) — ~/Desktop/Books (text read) — Table 3.2 | yes · quantified practitioner test | «medido» | 16 celdas con contraste: 4 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: UKOIL H1 long `strong_d20_21d` 4.6× · p corr. 0.29 (cruda 0.019) · 6/año — falla: no significativa, pocas operaciones |
| `TR-11-fitschen-d1-usd-pairs-trend` | `tendencia` | both — $675 per monthly trade on AUDUSD+EURUSD (84 winning months, 69 losing; 2008 alone +4,780, 2009-2011 all negative); gross | Fitschen, 'Building Reliable Trading Systems' (2013), ch. 3 'Find the Path of Least Resistance', pp. 31-44 (PDF pp. 38-51) — ~/Desktop/Books (text read) — Tables 3.5-3.6 | yes · quantified practitioner test | «medido» | 16 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: EURUSD M15 short `strong_d20_21d` 10.8× · p corr. 1.00 (cruda 0.518) · 8/año — falla: no significativa, inestable, pocas operaciones |
| `TR-12-chan-crude-30-40` | `tendencia` | both — APR 12%, Sharpe 1.1; the book gives no sample dates and no costs | Chan, 'Algorithmic Trading' (2013), ch. 6 'Interday Momentum Strategies', pp. 133-141 and 151 (PDF pp. 151-159, 169) — ~/Desktop/Books (text read) — p. 140 | yes · quantified practitioner test | «medido» | 16 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: USOIL H4 long `chan_30_40_run` 1.3× · p corr. 0.82 (cruda 0.122) · 10/año — falla: no significativa, no paga 2×, pocas operaciones |
| `TR-13-chan-lookback-hold-grid` | `tendencia` | both — Sharpe ≈1.0-1.1 each (TU 2004-2012); TU correlation table: lookback 25 / hold 1 = -0.014 (p 0.54), 60/10 = 0.17 (p 0.017), 250/25 = 0.27 (p 0.024); Hurst 0.44 and the variance-ratio test does NOT reject a random walk on the same series | Chan, 'Algorithmic Trading' (2013), ch. 6 'Interday Momentum Strategies', pp. 133-141 and 151 (PDF pp. 151-159, 169) — ~/Desktop/Books (text read) — Tables 6.1-6.2 | yes · quantified practitioner test | «la bibliografía lo afirma y aquí no se mide» | es una rejilla de correlaciones lookback × hold en D1, no una regla; los `tsmom_d*` miden sus diagonales |
| `BRK-14-katz-channel-breakout` | `ruptura` | both; longs more profitable in-sample — best in-sample return 1.2%/yr, -15.9%/yr out of sample for the HHLL breakout at the open; 'not enough to overcome transaction costs'; across all breakout tests currencies, oils and coffee did best | Katz & McCormick, 'The Encyclopedia of Trading Strategies' (2000), ch. 5 'Breakout Models', pp. 94 and 108 (PDF pp. 108, 122) — ~/Desktop/Books (text read) | yes · quantified practitioner test | «medido» | 10 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: AUDJPY H1 long `donchian_d85_opp` 4.0× · p corr. 0.95 (cruda 0.195) · 3/año — falla: no significativa, pocas operaciones |
| `TR-15-hsu-fx-daily-rules-decayed` | `tendencia` | both — full sample 1971-2015: best significant rules Sharpe 0.65 (NZD), 0.68 (DEM/EUR), 0.75 (JPY); moving-average rules best. Sub-periods: 5 of 9 developed currencies predictable in 1972-1976, 'only a few predictive rules in the 1980s, and none since the 1992-1996 period' | Hsu, Taylor, Wang (2016), 'Technical trading: Is it still beating the foreign exchange market?', J. International Economics 102:188-208 — SSRN 2765673 copy at https://technicalanalyst-cdn-1.s3.eu-west-2.amazonaws.com/wp-content/uploads/2016/04/13144511/SSRN-id2765673.pdf (full text read) | yes · peer-reviewed | «medido» | 80 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: USDCAD H1 long `fast_d5_20_run` 12.2× · p corr. 0.98 (cruda 0.232) · 9/año — falla: no significativa, pocas operaciones |
| `TR-16-man-trend-speed` | `tendencia` | both — 'risk-adjusted returns increase with slower speed' and 'are materially lower for faster speeds' after costs; fast systems keep positive skew and do best in equity sell-offs. No numbers on the page | Man Group, 'The Need for Speed in Trend-Following Strategies' (2023) — https://www.man.com/insights/need-for-speed-trend-following (page read) | **⚠️ page read; underlying figures not** · quantified practitioner test (numbers not on the page read) | «sólo bibliografía» | — |
| `TR-17-aqr-century-and-2010s` | `tendencia` | both — summary pages only: trend-following positive over 110 years since 1880; no figures extracted | Hurst, Ooi, Pedersen, 'A Century of Evidence on Trend-Following Investing' (JPM 2017) — https://www.aqr.com/Insights/Research/Journal-Article/A-Century-of-Evidence-on-Trend-Following-Investing ; and AQR, 'You Can't Always Trend When You Want' (2020) — https://www.aqr.com/Insights/Research/Journal-Article/You-Cant-Always-Trend-When-You-Want (summary pages only; the papers' tables not opened) | **⚠️ not verified beyond the abstract pages** · quantified practitioner test (JPM article; figures NOT verified) | «sólo bibliografía» | — |
| `MOM-18-first-last-half-hour-us` | `momentum` | both (sign of the first half-hour return) — R² 1.6% (first half-hour), 2.6% adding the 12th half-hour; out-of-sample R² 1.69%; timing strategy SD 6.19%/yr, Sharpe 1.08; by first-half-hour volatility tercile the strategy earns 0.54% (low), 4.75% (medium), 14.73% (high) a year; gross of costs (authors bound costs at 2.52%/yr) | Gao, Han, Li, Zhou, 'Intraday Momentum: The First Half-Hour Return Predicts the Last Half-Hour Return' (Oct 2014 draft; published as 'Market intraday momentum', JFE 2018) — https://www.smallake.kr/wp-content/uploads/2015/01/SSRN-id2440866.pdf (full text read) | yes (2014 draft) · peer-reviewed | «descartado por usar reloj» | — |
| `MOM-19-rest-of-day-predicts-last-30min` | `momentum` | both — 'economically and statistically highly significant' — no numbers on the page read | Baltussen, Da, Lammers, Martens (2021), 'Hedging demand and market intraday momentum', JFE 142:377-403 — https://pure.eur.nl/en/publications/hedging-demand-and-market-intraday-momentum/ (abstract page only) | **⚠️ abstract only** · peer-reviewed | «descartado por usar reloj» | — |
| `MOM-20-intraday-tsmom-international` | `momentum` | both — pooled slope 2.86 (t = 7.53); equal-weight global ITSM portfolio Sharpe 1.26-1.77 in 2005-2017, gross | Li, Sakkas, Urquhart, 'Intraday Time Series Momentum: International Evidence' (working paper, 2020) — http://wp.lancs.ac.uk/fofi2020/files/2020/04/FoFI-2020-092-Zeming-Li.pdf (full text read) | yes · quantified practitioner test (academic working paper) | «descartado por usar reloj» | — |
| `MOM-21a-noise-area-breakout` | `momentum` | both; the paper finds no relation between VIX and SHORT-trade profit — 2007-2024: total 1,985% net, 19.6%/yr, Sharpe 1.33, hit ratio 43%; costs $0.0035/share + $0.001 slippage; Sharpe ≈1.5 on all days, ≈3.5 when VIX > 40; average day +12 bp (t 5.34) | Zarattini, Aziz, Barbon, 'Beat the Market: An Effective Intraday Momentum Strategy for S&P500 ETF (SPY)' (Swiss Finance Institute RP 24-97, v. Feb 2025) — https://alexandria.unisg.ch/bitstreams/a99aba00-f967-49b3-aceb-f544dc386e0b/download (full text read) | yes · quantified practitioner test (SFI research paper, practitioner authors) | «descartado por usar reloj» | — |
| `MOM-21b-noise-area-clock-free` | `momentum` | both — not from the source — this is a transposition | Zarattini, Aziz, Barbon, 'Beat the Market: An Effective Intraday Momentum Strategy for S&P500 ETF (SPY)' (Swiss Finance Institute RP 24-97, v. Feb 2025) — https://alexandria.unisg.ch/bitstreams/a99aba00-f967-49b3-aceb-f544dc386e0b/download (full text read) — transposed, NOT the paper's rule | **⚠️ transposition** · quantified practitioner test (for 21a; none for this reading) | «medido» | 160 celdas con contraste: 6 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: NIKKEI225 H1 long `noise_k10` 2.6× · p corr. 0.34 (cruda 0.024) · 17/año — falla: no significativa, pocas operaciones |
| `VOL-22-narrow-range-then-intraday-trend` | `volatilidad` | both — intraday-momentum PnL per day: unconditional 12 bp (t 5.34, n=2,620); after NR4 22 bp (t 5.14, n=660, Sharpe 3.2); NR7 16 bp (t 3.07, n=367); Triangle 14 bp (t 3.19, n=664); after an inside day 5 bp (t 0.85); after a trend day -2 bp (t -0.24) | Zarattini, Aziz, Barbon, 'Beat the Market: An Effective Intraday Momentum Strategy for S&P500 ETF (SPY)' (Swiss Finance Institute RP 24-97, v. Feb 2025) — https://alexandria.unisg.ch/bitstreams/a99aba00-f967-49b3-aceb-f544dc386e0b/download (full text read) — Table 5 | yes · quantified practitioner test | «medido» | 8 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: USA500 M15 long `noise_k05_nr4` 3.1× · p corr. 0.68 (cruda 0.074) · 20/año — falla: no significativa, pocas operaciones |
| `MOM-23-opening-gap-eurostoxx` | `momentum` | both — APR 13%, Sharpe 1.4, gross | Chan, 'Algorithmic Trading' (2013), ch. 7 'Intraday Momentum Strategies', pp. 155-157 (PDF pp. 173-175) — ~/Desktop/Books (text read) — Example 7.1 | yes · quantified practitioner test | «descartado por usar reloj» | — |
| `MOM-24-opening-gap-gbpusd` | `momentum` | both — APR 7.2%, Sharpe 1.3, gross | Chan, 'Algorithmic Trading' (2013), ch. 7 'Intraday Momentum Strategies', pp. 155-157 (PDF pp. 173-175) — ~/Desktop/Books (text read) — p. 157 | yes · quantified practitioner test | «descartado por usar reloj» | — |
| `MOM-25-crude-first-half-hour` | `momentum` | both — USO: β = 0.0118, t = 2.86, R² = 0.67% (2007-2019). The 2023 paper gives no figure in its abstract. An R² of 0.729% in-sample for crude futures (Wen, Gong, Ma, Xu 2021, Economic Modelling) was seen only in a search summary: not verified | Xu, Bouri, Saeed, Wen (2020), 'Intraday return predictability: Evidence from commodity ETFs and their related volatility indices', Resources Policy — https://pmc.ncbi.nlm.nih.gov/articles/PMC7480318/ (page read through the fetch summariser) ; Wen, Indriawan, Lien, Xu (2023), 'Intraday Return Predictability in the Crude Oil Market: The Role of EIA Inventory Announcements', The Energy Journal 44(5):149-172 — https://ideas.repec.org/a/sae/enejou/v44y2023i5p149-172.html (abstract only) | **⚠️ XU via summariser; WEN23 abstract only** · peer-reviewed | «descartado por usar reloj» | — |
| `MOM-26-metals-late-session-half-hours` | `momentum` | both — GLD: β = 0.0436, t = 3.03, R² = 0.49% (2004-2019); SLV: β = 0.1260, t = 3.03, R² = 1.72% (2006-2020) | Xu, Bouri, Saeed, Wen (2020), 'Intraday return predictability: Evidence from commodity ETFs and their related volatility indices', Resources Policy — https://pmc.ncbi.nlm.nih.gov/articles/PMC7480318/ (page read through the fetch summariser) | **⚠️ via summariser** · peer-reviewed | «descartado por usar reloj» | — |
| `NEG-27-mnq-ohlcv-intraday-momentum` | `momentum` | both — none passed: eleven families had gross returns of 0.07-1.50 index points, below a 2.0-point friction; two session-based controls did pass (OOS t 3.11 and 4.30) | 'Structural Limits of OHLCV-Based Intraday Momentum Signals in MNQ Futures: A Systematic Falsification Study', arXiv:2605.04004 — https://arxiv.org/abs/2605.04004 (abstract only) | **⚠️ abstract only** · quantified practitioner test (arXiv, single author study) | «descartado por usar reloj» | — |
| `SES-28-overnight-drift-us-index` | `sesion` | long — +3.7%/yr = 1.48 bp per day in that one hour; positive in 20 of 23 years, significant in 17; hours 24-01, 01-02, 02-03 earn 0.46, 0.43, 1.5 bp; the 09:00-10:00 NY hour is negative only in recessions | Boyarchenko, Larsen, Whelan, 'The Overnight Drift', FRB New York Staff Report 917 (2020, rev. 2022) — https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr917.pdf (text read) | yes · quantified practitioner test (Federal Reserve staff report, academic) | «descartado por usar reloj» | — |
| `SES-29-overnight-vs-intraday-indices` | `sesion` | long overnight; intraday (cash open→close) negative — cumulative overnight vs intraday, from 1990 or first data to Sep 2020, as extracted from Figure 1: SPY +1288% vs -8%; Nasdaq Comp. +3402% vs -30%; DAX +1532% vs -64%; Nikkei 225 +1142% vs -95%. Cooper, Cliff & Gulen (2008) — the US equity premium is earned overnight — seen only in a search summary: not verified | Knuteson (2020), 'Strikingly Suspicious Overnight and Intraday Returns', arXiv:2010.01727 — https://arxiv.org/pdf/2010.01727 (text read; figures quoted from Figure 1 as extracted) | **⚠️ text read; figure labels paired by position** · quantified practitioner test (arXiv; replicable from public data) | «descartado por usar reloj» | — |
| `SES-30-gold-overnight` | `sesion` | long — GLD: +0.04% average per overnight trade, ≈11.4%/yr, intraday 'essentially flat'; period not stated on the page. Blose et al. report COMEX overnight significantly positive and day significantly negative for 1985-2012 (search summary only) | QuantifiedStrategies, 'A Quantitative Look at the Gold Overnight Strategy' — https://quantifiedstrategies.substack.com/p/a-quantitative-look-at-the-gold-overnight (page read). The academic source, Blose, Gondhalekar & Kort (2018) J. Economics and Finance 42, was NOT opened (paywall): not verified | **⚠️ blog page yes; academic paper NOT verified** · quantified practitioner test | «descartado por usar reloj» | — |
| `SES-31-fx-fix-reversals` | `sesion` | USD long before each fix, USD short after — dollar portfolio: +5.3%/yr (2.1 bp/day, t≈12) from 17:00 NY to the Tokyo fix, -5.5%/yr (t≈9.2) after it; +4.3%/yr (t≈4.1) from the European open to the London fix, -4.8%/yr (t≈5.5) from it to the NY close. AUD -7.39%/yr before the Tokyo fix. Trading EUR around the London fix: Sharpe 0.65 AFTER conservative costs, but 'not easy to exploit once transaction costs are accounted for' | Krohn, Mueller, Whelan, 'Foreign Exchange Fixings and Returns Around the Clock' (June 2020 version; later J. Finance 2024) — https://sites.insead.edu/facultyresearch/research/file.cfm?fid=66802 (text read) | yes · peer-reviewed (J. Finance 2024; 2020 working version read) | «descartado por usar reloj» | — |
| `SES-32-jpy-local-hours` | `sesion` | USDJPY down in the Asian day, up in US hours — post-Tokyo-fix reversal for JPY 7.70%/yr; other figures not extracted | Krohn, Mueller, Whelan, 'Foreign Exchange Fixings and Returns Around the Clock' (June 2020 version; later J. Finance 2024) — https://sites.insead.edu/facultyresearch/research/file.cfm?fid=66802 (text read). Ranaldo (2009, J. Banking & Finance 33:2199) documents the general time-of-day pattern; two machine summaries of its abstract disagreed on the SIGN, so its direction is NOT verified here | **⚠️ Krohn yes; Ranaldo's direction not verified** · peer-reviewed | «descartado por usar reloj» | — |
| `SES-33-fx-range-by-session` | `sesion` | none (a volatility fact) — the 08:00-12:00 NY overlap holds 70% of the European-hours range and 80% of the US-hours range; USDJPY and AUDJPY are the pairs whose Asian range equals their European one | Lien, 'Day Trading and Swing Trading the Currency Market' 2nd ed. (2008), ch. 5 Table 5.1, pp. 67-73 (PDF pp. 83-89) — ~/Desktop/Books (text read) | yes · quantified practitioner test (descriptive table) | «descartado por usar reloj» | — |
| `CAL-34-turn-of-month` | `sesion` | long — 7.2%/yr, Sharpe 1.04, volatility 6.9%, max drawdown -20.79% (Quantpedia's indicative figures) | Quantpedia, 'Turn of the Month in Equity Indexes' (summarising McConnell & Xu 2008) — https://quantpedia.com/strategies/turn-of-the-month-in-equity-indexes (page read; the paper itself not opened) | **⚠️ summary page only** · peer-reviewed (paper) seen through a practitioner summary | «descartado por usar reloj» | — |
| `CAL-35-pre-fomc-drift` | `sesion` | long — 'large average excess returns' accounting for 'sizable fractions of total annual realized stock returns' — no number on the page read | Lucca & Moench, 'The Pre-FOMC Announcement Drift', FRBNY Staff Report 512 / J. Finance 2015 — https://www.newyorkfed.org/research/staff_reports/sr512.html (abstract page only) | **⚠️ abstract page only** · peer-reviewed | «descartado por usar reloj» | — |
| `REV-36a-index-daily-ar1` | `reversion` | both (fade yesterday's return) — daily AR(1) before → after 1999: S&P 500 +0.103*** → -0.076*** (t -3.29); DAX +0.066*** → -0.016 (t -0.90, not significant); Nikkei 225 +0.042*** → -0.031 (t -1.65); FTSE -0.037** | Baltussen, van Bekkum, Da (2019), 'Indexing and stock market serial dependence around the world', JFE 132:26-48 — https://academicweb.nd.edu/~zda/Indexing.pdf (full text read; Table 1) | yes (Table 1) · peer-reviewed | «medido» | 40 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: NIKKEI225 H1 long `day_down_1d` 1.3× · p corr. 1.00 (cruda 0.268) · 103/año — falla: no significativa, no paga 2× |
| `REV-36b-index-mac5` | `reversion` | both — trading against MAC(5): Sharpe 0.63 on all 20 indexes, 0.67 on the S&P 500 alone, after 2 Mar 1999; 'similar Sharpe ratios for futures and ETFs'; gross | Baltussen, van Bekkum, Da (2019), 'Indexing and stock market serial dependence around the world', JFE 132:26-48 — https://academicweb.nd.edu/~zda/Indexing.pdf (full text read; Table 1) | yes · peer-reviewed | «medido» | 40 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: USATEC H1 short `mac5_down_1d` -1.3× · p corr. 0.76 (cruda 0.100) · 120/año — falla: no significativa, no paga 2×, inestable |
| `REV-36c-index-weekly-ar1` | `reversion` | both — weekly AR(1) after 1999: S&P 500 -0.077 (t -1.64); DAX -0.102** (t -2.24); Nikkei 225 -0.018 (t -0.58); Euro Stoxx 50 -0.155**; CAC -0.166*** | Baltussen, van Bekkum, Da (2019), 'Indexing and stock market serial dependence around the world', JFE 132:26-48 — https://academicweb.nd.edu/~zda/Indexing.pdf (full text read; Table 1) | yes · peer-reviewed | «medido» | 24 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: USA500 M30 long `week_down_5d` 13.1× · p corr. 1.00 (cruda 0.306) · 22/año — falla: no significativa, pocas operaciones |
| `REV-37a-ibs-long` | `reversion` | long — average next-day return +0.35% when IBS < 0.2, -0.13% when IBS > 0.8; thresholds ≈0.4 and 0.9 bound the predictive zone; 'difficult alone due to transaction costs', better combined with RSI(3) | Pagonidis, 'The IBS Effect: Mean Reversion in Equity ETFs' (NAAIM paper, 2014) — https://www.naaim.org/wp-content/uploads/2014/04/00V_Alexander_Pagonidis_The-IBS-Effect-Mean-Reversion-in-Equity-ETFs-1.pdf (text read) | yes · quantified practitioner test | «medido» | 32 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: USA500 H4 long `ibs_low_1d` 5.3× · p corr. 0.65 (cruda 0.068) · 39/año — falla: no significativa, pocas operaciones |
| `REV-37b-ibs-short` | `reversion` | short — -0.13% average next-day return after IBS > 0.8 (all regimes) | Pagonidis, 'The IBS Effect: Mean Reversion in Equity ETFs' (NAAIM paper, 2014) — https://www.naaim.org/wp-content/uploads/2014/04/00V_Alexander_Pagonidis_The-IBS-Effect-Mean-Reversion-in-Equity-ETFs-1.pdf (text read) | yes · quantified practitioner test | «medido» | 12 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: USA500 H4 short `ibs_low_volhigh_up_1d` -1.7× · p corr. 1.00 (cruda 0.501) · 7/año — falla: no significativa, no paga 2×, inestable, pocas operaciones |
| `REV-38a-rsi2-daily` | `reversion` | long (the short mirror exists in Connors' rules; no opened test of it) — Nasdaq-100 stocks, Dec 2006-2025: win rate 64.33%, average winner +2.33%, loser -3.02%, profit factor 1.45, 17.84%/yr, max drawdown 29.15%, ≈1,000 trades | StockCharts ChartSchool, 'RSI(2)' (describing Larry Connors' rules, no book cited) — https://chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/rsi-2 ; and 'The 2-Period RSI: A Simple System That Still Earns Its Keep' — https://backtest.substack.com/p/the-2-period-rsi-a-simple-system (both pages read) | **⚠️ pages read** · quantified practitioner test (blog backtest; rules as described by StockCharts, Connors' book not opened) | «medido» | 8 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: USATEC H4 long `connors_d1` 17.2× · p corr. 0.63 (cruda 0.064) · 8/año — falla: no significativa, pocas operaciones |
| `REV-38b-rsi2-intraday-bars` | `reversion` | long — none — not in any source read | StockCharts ChartSchool, 'RSI(2)' (describing Larry Connors' rules, no book cited) — https://chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/rsi-2 ; and 'The 2-Period RSI: A Simple System That Still Earns Its Keep' — https://backtest.substack.com/p/the-2-period-rsi-a-simple-system (both pages read) — transposed, NOT a documented result | **⚠️ transposition** · lore (as transposed) | «medido» | 20 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: DAX40 M15 long `rsi2_up200_sma5` 0.3× · p corr. 0.85 (cruda 0.138) · 471/año — falla: no significativa, no paga 2× |
| `REV-39-reversal-pays-in-high-vol` | `reversion` | both — no single number in the abstract | Nagel, 'Evaporating Liquidity', NBER WP 17653 (2011; Review of Financial Studies 2012) — https://www.nber.org/system/files/working_papers/w17653/w17653.pdf (abstract read) | **⚠️ abstract** · peer-reviewed | «medido» | 80 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: USA500 M15 long `ibs_low_volhigh_1d` 8.4× · p corr. 0.66 (cruda 0.071) · 18/año — falla: no significativa, pocas operaciones |
| `REV-40-fitschen-stocks-daily-counter-trend` | `reversion` | LONG ONLY: the short side loses — buying weak stocks +1.56%/month vs +0.71% buy-and-hold and +0.16% buying strong (2000-2011). Donchian counter-trend, 10-day: long +$69/trade (6,248 wins, 2,779 losses), short -$43/trade (5,355 wins, 3,631 losses; average win $258, loss $498). Profit/trade falls from $119 (20-day) to $24 (2-day) while gain-to-pain rises 0.70 → 1.24; survivorship bias acknowledged | Fitschen, 'Building Reliable Trading Systems' (2013), ch. 3 'Find the Path of Least Resistance', pp. 31-44 (PDF pp. 38-51) — ~/Desktop/Books (text read) ; Fitschen, 'Building Reliable Trading Systems' (2013), ch. 5, pp. 66-68 (PDF pp. 73-75), Tables 5.1-5.2 — ~/Desktop/Books (text read) | yes · quantified practitioner test | «medido» | 8 celdas con contraste: 3 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: USATEC M30 long `out10_counter` 48.2× · p corr. 0.52 (cruda 0.045) · 9/año — falla: no significativa, pocas operaciones |
| `REV-41-williams-pullback-in-uptrend` | `reversion` | long — buy every day, exit next close: 52% wins, $134/trade; after three down closes: 58%, $353; uptrend+pullback: 57%, $421 (figures as recorded in the dossier, optimised on the full sample) | Williams, 'Long-Term Secrets to Short-Term Trading' (1999), pp. 94-95 — via docs/AgentPDFs/ideas-de-internet-y-libros-2026-09-27.md (the project's own catalogue; the book pages it cites were NOT re-opened in this task) | **⚠️ via dossier — book page not re-opened** · quantified practitioner test (in-sample, pre-2000) | «medido» | 8 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: USA500 M15 long `d1_down3_1d` 3.3× · p corr. 1.00 (cruda 0.322) · 17/año — falla: no significativa, inestable, pocas operaciones |
| `REV-42-fitschen-fx-crosses-counter-trend` | `reversion` | both — $629 per monthly trade on the five counter-trend pairs: 192 winning months, 166 losing; only 2000, 2005, 2007 negative; gross | Fitschen, 'Building Reliable Trading Systems' (2013), ch. 3 'Find the Path of Least Resistance', pp. 31-44 (PDF pp. 38-51) — ~/Desktop/Books (text read) — Tables 3.5-3.6 | yes · quantified practitioner test | «medido» | 32 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: CADJPY M15 long `weak_d20_mean` 2.6× · p corr. 0.99 (cruda 0.246) · 9/año — falla: no significativa, pocas operaciones |
| `REV-43-fitschen-fx-all-pairs-buy-weak` | `reversion` | both — buy weak +$178, buy strong -$101, buy-and-hold -$87; the long-short counter-trend approach +$137 per trade; negative in 2000, 2007, 2008 (-1,628) | Fitschen, 'Building Reliable Trading Systems' (2013), ch. 3 'Find the Path of Least Resistance', pp. 31-44 (PDF pp. 38-51) — ~/Desktop/Books (text read) — Table 3.3 | yes · quantified practitioner test | «medido» | 32 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: USDCAD H4 long `weak_d20_21d` 21.3× · p corr. 0.88 (cruda 0.155) · 8/año — falla: no significativa, inestable, pocas operaciones |
| `REV-44-chan-usdcad-half-life` | `reversion` | both — USDCAD: ADF cannot reject a random walk at 90%; variance-ratio test does not reject (p = 0.367); half-life ≈115 days. AUDCAD linear mean reversion with a 20-day look-back: APR 6.2%, Sharpe 0.54 (6.7% / 0.58 ignoring rollover) | Chan, 'Algorithmic Trading' (2013), ch. 2 Examples 2.1-2.5, pp. 42-50 (PDF pp. 60-68), and ch. 5 Example 5.2, pp. 114-116 (PDF pp. 132-134) — ~/Desktop/Books (text read) | yes · quantified practitioner test | «la bibliografía lo afirma y aquí no se mide» | es una vida media por par en D1; el perfil sólo la mide en el marco de la celda (`pullback_speed`) |
| `REV-45-grimes-keltner-fx` | `reversion` | both — share of range inside the bands: forex 89.8% (min 87.8, max 92.0) vs random-walk series 86.8%; bars entirely outside: forex 2.3% vs random 3.8%; futures (16) 85.9% / 3.8%; large-cap stocks 87.7% / 3.4%. Text: 'in many markets there actually is a slight statistical edge to fading moves' to the channel — no figure. Also p. 369: forex is 'the most random and least predictable of all the major markets in many time frames' | Grimes, 'The Art and Science of Technical Analysis' (2012), ch. 7 Table 7.1 p. 198 (PDF p. 215); indicator definition p. 52 (PDF p. 69); p. 369 (PDF p. 386) — ~/Desktop/Books (text read) | yes · quantified practitioner test (excursion table) / book claim without numbers (the fade edge) | «medido» | 160 celdas con contraste: 24 con p cruda ≤ 0,05, 5 significativas tras corregir, 0 pasan los cuatro. Mejor: USDJPY M15 long `keltner225_mean` 1.0× · p corr. 0.01 (cruda 0.000) · 311/año — falla: no paga 2× |
| `REV-46-chan-gap-fade-with-trend-filter` | `reversion` | long (the short mirror also reported profitable) — APR 8.7%, Sharpe 1.5 (10 stocks a day), gross | Chan, 'Algorithmic Trading' (2013), ch. 4 'Buy-on-Gap Model', pp. 92-95 (PDF pp. 110-113) — ~/Desktop/Books (text read) | yes · quantified practitioner test | «descartado por usar reloj» | — |
| `NEG-47-fx-intraday-technical-rules` | `tendencia` | both — 'when realistic transaction costs and trading hours are taken into account, we find no evidence of excess returns' — though 'the trading rules discover some remarkably stable patterns' | Neely & Weller, 'Intraday Technical Trading in the Foreign Exchange Market' (1999 draft; JIMF 2003) — https://warwick.ac.uk/fac/soc/wbs/subjects/finance/research/wpaperseries/wp99-14.pdf (abstract read) | **⚠️ abstract** · peer-reviewed | «sólo bibliografía» | — |
| `CARRY-48-crash-asymmetry-short` | `ruptura` | short the high-yield/JPY cross — falls are faster than rises — carry returns are negatively skewed; skewness is positive and highest for JPY, most negative for AUD and NZD; a search summary quotes -0.322 daily skew for AUD-vs-USD carry (not located in the text read) | Brunnermeier, Nagel, Pedersen, 'Carry Trades and Currency Crashes', NBER WP 14473 (2008; NBER Macroeconomics Annual) — https://www.nber.org/system/files/working_papers/w14473/w14473.pdf (text read) | yes (text; skew figure not) · peer-reviewed | «medido» | 40 celdas, ninguna llega a 30 operaciones en build: sin contraste |
| `CARRY-49-high-vix-then-long` | `reversion` | long the high-yielder after the spike — regression evidence; no return figure transcribed | Brunnermeier, Nagel, Pedersen, 'Carry Trades and Currency Crashes', NBER WP 14473 (2008; NBER Macroeconomics Annual) — https://www.nber.org/system/files/working_papers/w14473/w14473.pdf (text read) | yes · peer-reviewed | «medido» | 12 celdas, ninguna llega a 30 operaciones en build: sin contraste |
| `FX-50-cross-sectional-momentum` | `momentum` | both, cross-sectional — winner-minus-loser spread 'up to 10% per annum', 'partially explained by transaction costs'; 'very effective limits to arbitrage' | Menkhoff, Sarno, Schmeling, Schrimpf, 'Currency Momentum Strategies', BIS WP 366 (2011; JFE 2012) — https://www.bis.org/publ/work366.pdf (read through the fetch summariser) | **⚠️ via summariser** · peer-reviewed | «sólo bibliografía» | — |
| `GOLD-51-real-yields-and-dollar` | `tendencia` | long gold when the dollar and real yields fall; short on the mirror — regression on 13-week changes, Mar 2014 - Jun 2018 (231 obs): R² 0.65; +100 bp in the TIPS yield ≈ -$173/oz; +1 point of the dollar index ≈ -$10/oz; correlation gold-dollar -0.75, gold-TIPS -0.40 (2018). 'In late 2017 gold and the TIPS yield appear to have parted ways'; a search summary reports the correlation collapsing to ≈0 in 2022-2026 (not verified) | Murenbeeld, 'An Update on Gold, Real Interest Rates and the Dollar', LBMA Alchemist issue 90 (2018) — https://www.lbma.org.uk/alchemist/issue-90/an-update-on-gold-real-interest-rates-and-the-dollar (page read) | **⚠️ page read** · quantified practitioner test | «la bibliografía lo afirma y aquí no se mide» | necesita otro activo (EURUSD como proxy del dólar): el perfil mide cada activo solo |
| `VOL-52-range-reverts` | `volatilidad` | none — range correlation coefficients -0.43 to -0.46, sign change after 3-5 days: 'a big range day has a tendency to be followed by a quiet period, and a small range day followed by bigger ranges' | Fitschen, 'Building Reliable Trading Systems' (2013), ch. 10 Table 10.3, p. 160 (PDF p. 167) — ~/Desktop/Books (text read) | yes (the definition of the coefficient was not re-read) · quantified practitioner test | «la bibliografía lo afirma y aquí no se mide» | es una correlación de rangos diarios, no una regla con operaciones |
| `VOL-53-volatility-targeting-helps-equities-only` | `volatilidad` | long index exposure — no number on the page read | Harvey et al. / Man Group, 'The Impact of Volatility Targeting' (J. Portfolio Management 2018) — https://www.man.com/insights/the-impact-of-volatility-targeting (page read) | **⚠️ page read** · peer-reviewed (JPM) via the firm's page | «la bibliografía lo afirma y aquí no se mide» | es un filtro de volatilidad sobre cualquier entrada larga de índice; medido sólo en `fast_d5_20_quiet_run` |
| `VOL-54-bollinger-width-flips-the-rule` | `volatilidad` | long in both regimes, opposite triggers — none recorded | 'New Frontiers in Technical Analysis' (2011), pp. 25-27, 44 — via docs/AgentPDFs/ideas-de-internet-y-libros-2026-09-27.md (the project's own catalogue; the book pages it cites were NOT re-opened in this task) | **⚠️ via dossier — book page not re-opened** · book claim without numbers | «la bibliografía lo afirma y aquí no se mide» | necesita terciles móviles de la anchura de Bollinger; no implementado |
| `VOL-55-compression-then-breakout` | `volatilidad` | both — Tharp: 'can easily add 10-15 cents per dollar risked' to a trend system (as recorded in the dossier) | Tharp, 'Trade Your Way to Financial Freedom', pp. 182-183, 207; Kirkpatrick & Dahlquist (Raschke), p. 386 — via docs/AgentPDFs/ideas-de-internet-y-libros-2026-09-27.md (the project's own catalogue; the book pages it cites were NOT re-opened in this task) | **⚠️ via dossier — book pages not re-opened** · book claim without numbers (one effect size, no test shown) | «medido» | 140 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: USA500 H4 long `donchian_d20_squeeze` 43.6× · p corr. 0.74 (cruda 0.096) · 6/año — falla: no significativa, pocas operaciones |

#### `AUDJPY` — lo que la bibliografía dice nombrándolo

| id | familia | qué afirma (dirección — tamaño) | fuente | verificado · grado | estado | lo medido aquí |
|---|---|---|---|---|---|---|
| `SES-33-fx-range-by-session` | `sesion` | none (a volatility fact) — the 08:00-12:00 NY overlap holds 70% of the European-hours range and 80% of the US-hours range; USDJPY and AUDJPY are the pairs whose Asian range equals their European one | Lien, 'Day Trading and Swing Trading the Currency Market' 2nd ed. (2008), ch. 5 Table 5.1, pp. 67-73 (PDF pp. 83-89) — ~/Desktop/Books (text read) | yes · quantified practitioner test (descriptive table) | «descartado por usar reloj» | — |
| `CARRY-48-crash-asymmetry-short` | `ruptura` | short the high-yield/JPY cross — falls are faster than rises — carry returns are negatively skewed; skewness is positive and highest for JPY, most negative for AUD and NZD; a search summary quotes -0.322 daily skew for AUD-vs-USD carry (not located in the text read) | Brunnermeier, Nagel, Pedersen, 'Carry Trades and Currency Crashes', NBER WP 14473 (2008; NBER Macroeconomics Annual) — https://www.nber.org/system/files/working_papers/w14473/w14473.pdf (text read) | yes (text; skew figure not) · peer-reviewed | «medido» | 8 celdas, ninguna llega a 30 operaciones en build: sin contraste |
| `CARRY-49-high-vix-then-long` | `reversion` | long the high-yielder after the spike — regression evidence; no return figure transcribed | Brunnermeier, Nagel, Pedersen, 'Carry Trades and Currency Crashes', NBER WP 14473 (2008; NBER Macroeconomics Annual) — https://www.nber.org/system/files/working_papers/w14473/w14473.pdf (text read) | yes · peer-reviewed | «medido» | 4 celdas, ninguna llega a 30 operaciones en build: sin contraste |

#### `AUDUSD` — lo que la bibliografía dice nombrándolo

| id | familia | qué afirma (dirección — tamaño) | fuente | verificado · grado | estado | lo medido aquí |
|---|---|---|---|---|---|---|
| `TR-11-fitschen-d1-usd-pairs-trend` | `tendencia` | both — $675 per monthly trade on AUDUSD+EURUSD (84 winning months, 69 losing; 2008 alone +4,780, 2009-2011 all negative); gross | Fitschen, 'Building Reliable Trading Systems' (2013), ch. 3 'Find the Path of Least Resistance', pp. 31-44 (PDF pp. 38-51) — ~/Desktop/Books (text read) — Tables 3.5-3.6 | yes · quantified practitioner test | «medido» | 8 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: AUDUSD H4 short `strong_d20_21d` 1.6× · p corr. 1.00 (cruda 0.510) · 8/año — falla: no significativa, no paga 2×, inestable, pocas operaciones |
| `SES-31-fx-fix-reversals` | `sesion` | USD long before each fix, USD short after — dollar portfolio: +5.3%/yr (2.1 bp/day, t≈12) from 17:00 NY to the Tokyo fix, -5.5%/yr (t≈9.2) after it; +4.3%/yr (t≈4.1) from the European open to the London fix, -4.8%/yr (t≈5.5) from it to the NY close. AUD -7.39%/yr before the Tokyo fix. Trading EUR around the London fix: Sharpe 0.65 AFTER conservative costs, but 'not easy to exploit once transaction costs are accounted for' | Krohn, Mueller, Whelan, 'Foreign Exchange Fixings and Returns Around the Clock' (June 2020 version; later J. Finance 2024) — https://sites.insead.edu/facultyresearch/research/file.cfm?fid=66802 (text read) | yes · peer-reviewed (J. Finance 2024; 2020 working version read) | «descartado por usar reloj» | — |
| `SES-33-fx-range-by-session` | `sesion` | none (a volatility fact) — the 08:00-12:00 NY overlap holds 70% of the European-hours range and 80% of the US-hours range; USDJPY and AUDJPY are the pairs whose Asian range equals their European one | Lien, 'Day Trading and Swing Trading the Currency Market' 2nd ed. (2008), ch. 5 Table 5.1, pp. 67-73 (PDF pp. 83-89) — ~/Desktop/Books (text read) | yes · quantified practitioner test (descriptive table) | «descartado por usar reloj» | — |
| `CARRY-49-high-vix-then-long` | `reversion` | long the high-yielder after the spike — regression evidence; no return figure transcribed | Brunnermeier, Nagel, Pedersen, 'Carry Trades and Currency Crashes', NBER WP 14473 (2008; NBER Macroeconomics Annual) — https://www.nber.org/system/files/working_papers/w14473/w14473.pdf (text read) | yes · peer-reviewed | «medido» | 4 celdas, ninguna llega a 30 operaciones en build: sin contraste |

#### `CADJPY` — lo que la bibliografía dice nombrándolo

| id | familia | qué afirma (dirección — tamaño) | fuente | verificado · grado | estado | lo medido aquí |
|---|---|---|---|---|---|---|
| `SES-33-fx-range-by-session` | `sesion` | none (a volatility fact) — the 08:00-12:00 NY overlap holds 70% of the European-hours range and 80% of the US-hours range; USDJPY and AUDJPY are the pairs whose Asian range equals their European one | Lien, 'Day Trading and Swing Trading the Currency Market' 2nd ed. (2008), ch. 5 Table 5.1, pp. 67-73 (PDF pp. 83-89) — ~/Desktop/Books (text read) | yes · quantified practitioner test (descriptive table) | «descartado por usar reloj» | — |
| `REV-42-fitschen-fx-crosses-counter-trend` | `reversion` | both — $629 per monthly trade on the five counter-trend pairs: 192 winning months, 166 losing; only 2000, 2005, 2007 negative; gross | Fitschen, 'Building Reliable Trading Systems' (2013), ch. 3 'Find the Path of Least Resistance', pp. 31-44 (PDF pp. 38-51) — ~/Desktop/Books (text read) — Tables 3.5-3.6 | yes · quantified practitioner test | «medido» | 16 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: CADJPY M15 long `weak_d20_mean` 2.6× · p corr. 0.99 (cruda 0.246) · 9/año — falla: no significativa, pocas operaciones |
| `CARRY-48-crash-asymmetry-short` | `ruptura` | short the high-yield/JPY cross — falls are faster than rises — carry returns are negatively skewed; skewness is positive and highest for JPY, most negative for AUD and NZD; a search summary quotes -0.322 daily skew for AUD-vs-USD carry (not located in the text read) | Brunnermeier, Nagel, Pedersen, 'Carry Trades and Currency Crashes', NBER WP 14473 (2008; NBER Macroeconomics Annual) — https://www.nber.org/system/files/working_papers/w14473/w14473.pdf (text read) | yes (text; skew figure not) · peer-reviewed | «medido» | 8 celdas, ninguna llega a 30 operaciones en build: sin contraste |
| `CARRY-49-high-vix-then-long` | `reversion` | long the high-yielder after the spike — regression evidence; no return figure transcribed | Brunnermeier, Nagel, Pedersen, 'Carry Trades and Currency Crashes', NBER WP 14473 (2008; NBER Macroeconomics Annual) — https://www.nber.org/system/files/working_papers/w14473/w14473.pdf (text read) | yes · peer-reviewed | «medido» | 4 celdas, ninguna llega a 30 operaciones en build: sin contraste |

#### `DAX40` — lo que la bibliografía dice nombrándolo

| id | familia | qué afirma (dirección — tamaño) | fuente | verificado · grado | estado | lo medido aquí |
|---|---|---|---|---|---|---|
| `MOM-21b-noise-area-clock-free` | `momentum` | both — not from the source — this is a transposition | Zarattini, Aziz, Barbon, 'Beat the Market: An Effective Intraday Momentum Strategy for S&P500 ETF (SPY)' (Swiss Finance Institute RP 24-97, v. Feb 2025) — https://alexandria.unisg.ch/bitstreams/a99aba00-f967-49b3-aceb-f544dc386e0b/download (full text read) — transposed, NOT the paper's rule | **⚠️ transposition** · quantified practitioner test (for 21a; none for this reading) | «medido» | 32 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: DAX40 M15 short `noise_k05` 0.8× · p corr. 0.96 (cruda 0.198) · 80/año — falla: no significativa, no paga 2× |
| `MOM-23-opening-gap-eurostoxx` | `momentum` | both — APR 13%, Sharpe 1.4, gross | Chan, 'Algorithmic Trading' (2013), ch. 7 'Intraday Momentum Strategies', pp. 155-157 (PDF pp. 173-175) — ~/Desktop/Books (text read) — Example 7.1 | yes · quantified practitioner test | «descartado por usar reloj» | — |
| `SES-29-overnight-vs-intraday-indices` | `sesion` | long overnight; intraday (cash open→close) negative — cumulative overnight vs intraday, from 1990 or first data to Sep 2020, as extracted from Figure 1: SPY +1288% vs -8%; Nasdaq Comp. +3402% vs -30%; DAX +1532% vs -64%; Nikkei 225 +1142% vs -95%. Cooper, Cliff & Gulen (2008) — the US equity premium is earned overnight — seen only in a search summary: not verified | Knuteson (2020), 'Strikingly Suspicious Overnight and Intraday Returns', arXiv:2010.01727 — https://arxiv.org/pdf/2010.01727 (text read; figures quoted from Figure 1 as extracted) | **⚠️ text read; figure labels paired by position** · quantified practitioner test (arXiv; replicable from public data) | «descartado por usar reloj» | — |
| `REV-36a-index-daily-ar1` | `reversion` | both (fade yesterday's return) — daily AR(1) before → after 1999: S&P 500 +0.103*** → -0.076*** (t -3.29); DAX +0.066*** → -0.016 (t -0.90, not significant); Nikkei 225 +0.042*** → -0.031 (t -1.65); FTSE -0.037** | Baltussen, van Bekkum, Da (2019), 'Indexing and stock market serial dependence around the world', JFE 132:26-48 — https://academicweb.nd.edu/~zda/Indexing.pdf (full text read; Table 1) | yes (Table 1) · peer-reviewed | «medido» | 8 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: DAX40 H4 long `day_down_1d` 0.7× · p corr. 1.00 (cruda 0.633) · 109/año — falla: no significativa, no paga 2× |
| `REV-36c-index-weekly-ar1` | `reversion` | both — weekly AR(1) after 1999: S&P 500 -0.077 (t -1.64); DAX -0.102** (t -2.24); Nikkei 225 -0.018 (t -0.58); Euro Stoxx 50 -0.155**; CAC -0.166*** | Baltussen, van Bekkum, Da (2019), 'Indexing and stock market serial dependence around the world', JFE 132:26-48 — https://academicweb.nd.edu/~zda/Indexing.pdf (full text read; Table 1) | yes · peer-reviewed | «medido» | 8 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: DAX40 H4 long `week_down_5d` 9.1× · p corr. 1.00 (cruda 0.385) · 28/año — falla: no significativa, pocas operaciones |
| `REV-37a-ibs-long` | `reversion` | long — average next-day return +0.35% when IBS < 0.2, -0.13% when IBS > 0.8; thresholds ≈0.4 and 0.9 bound the predictive zone; 'difficult alone due to transaction costs', better combined with RSI(3) | Pagonidis, 'The IBS Effect: Mean Reversion in Equity ETFs' (NAAIM paper, 2014) — https://www.naaim.org/wp-content/uploads/2014/04/00V_Alexander_Pagonidis_The-IBS-Effect-Mean-Reversion-in-Equity-ETFs-1.pdf (text read) | yes · quantified practitioner test | «medido» | 8 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: DAX40 M15 long `ibs_low_volhigh_1d` 7.7× · p corr. 0.91 (cruda 0.171) · 19/año — falla: no significativa, pocas operaciones |
| `REV-38b-rsi2-intraday-bars` | `reversion` | long — none — not in any source read | StockCharts ChartSchool, 'RSI(2)' (describing Larry Connors' rules, no book cited) — https://chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/rsi-2 ; and 'The 2-Period RSI: A Simple System That Still Earns Its Keep' — https://backtest.substack.com/p/the-2-period-rsi-a-simple-system (both pages read) — transposed, NOT a documented result | **⚠️ transposition** · lore (as transposed) | «medido» | 4 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: DAX40 M15 long `rsi2_up200_sma5` 0.3× · p corr. 0.85 (cruda 0.138) · 471/año — falla: no significativa, no paga 2× |

#### `DJ30` — lo que la bibliografía dice nombrándolo

| id | familia | qué afirma (dirección — tamaño) | fuente | verificado · grado | estado | lo medido aquí |
|---|---|---|---|---|---|---|
| `MOM-21b-noise-area-clock-free` | `momentum` | both — not from the source — this is a transposition | Zarattini, Aziz, Barbon, 'Beat the Market: An Effective Intraday Momentum Strategy for S&P500 ETF (SPY)' (Swiss Finance Institute RP 24-97, v. Feb 2025) — https://alexandria.unisg.ch/bitstreams/a99aba00-f967-49b3-aceb-f544dc386e0b/download (full text read) — transposed, NOT the paper's rule | **⚠️ transposition** · quantified practitioner test (for 21a; none for this reading) | «medido» | 32 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: DJ30 M15 long `noise_k05` 2.8× · p corr. 0.66 (cruda 0.070) · 82/año — falla: no significativa |
| `SES-29-overnight-vs-intraday-indices` | `sesion` | long overnight; intraday (cash open→close) negative — cumulative overnight vs intraday, from 1990 or first data to Sep 2020, as extracted from Figure 1: SPY +1288% vs -8%; Nasdaq Comp. +3402% vs -30%; DAX +1532% vs -64%; Nikkei 225 +1142% vs -95%. Cooper, Cliff & Gulen (2008) — the US equity premium is earned overnight — seen only in a search summary: not verified | Knuteson (2020), 'Strikingly Suspicious Overnight and Intraday Returns', arXiv:2010.01727 — https://arxiv.org/pdf/2010.01727 (text read; figures quoted from Figure 1 as extracted) | **⚠️ text read; figure labels paired by position** · quantified practitioner test (arXiv; replicable from public data) | «descartado por usar reloj» | — |
| `REV-36a-index-daily-ar1` | `reversion` | both (fade yesterday's return) — daily AR(1) before → after 1999: S&P 500 +0.103*** → -0.076*** (t -3.29); DAX +0.066*** → -0.016 (t -0.90, not significant); Nikkei 225 +0.042*** → -0.031 (t -1.65); FTSE -0.037** | Baltussen, van Bekkum, Da (2019), 'Indexing and stock market serial dependence around the world', JFE 132:26-48 — https://academicweb.nd.edu/~zda/Indexing.pdf (full text read; Table 1) | yes (Table 1) · peer-reviewed | «medido» | 8 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: DJ30 H4 long `day_down_1d` 1.4× · p corr. 1.00 (cruda 0.610) · 108/año — falla: no significativa, no paga 2× |
| `REV-37a-ibs-long` | `reversion` | long — average next-day return +0.35% when IBS < 0.2, -0.13% when IBS > 0.8; thresholds ≈0.4 and 0.9 bound the predictive zone; 'difficult alone due to transaction costs', better combined with RSI(3) | Pagonidis, 'The IBS Effect: Mean Reversion in Equity ETFs' (NAAIM paper, 2014) — https://www.naaim.org/wp-content/uploads/2014/04/00V_Alexander_Pagonidis_The-IBS-Effect-Mean-Reversion-in-Equity-ETFs-1.pdf (text read) | yes · quantified practitioner test | «medido» | 8 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: DJ30 M15 long `ibs_low_volhigh_1d` 5.1× · p corr. 1.00 (cruda 0.380) · 17/año — falla: no significativa, pocas operaciones |
| `REV-37b-ibs-short` | `reversion` | short — -0.13% average next-day return after IBS > 0.8 (all regimes) | Pagonidis, 'The IBS Effect: Mean Reversion in Equity ETFs' (NAAIM paper, 2014) — https://www.naaim.org/wp-content/uploads/2014/04/00V_Alexander_Pagonidis_The-IBS-Effect-Mean-Reversion-in-Equity-ETFs-1.pdf (text read) | yes · quantified practitioner test | «medido» | 4 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: DJ30 H1 short `ibs_low_volhigh_up_1d` -2.5× · p corr. 1.00 (cruda 0.625) · 10/año — falla: no significativa, no paga 2×, inestable, pocas operaciones |
| `REV-38b-rsi2-intraday-bars` | `reversion` | long — none — not in any source read | StockCharts ChartSchool, 'RSI(2)' (describing Larry Connors' rules, no book cited) — https://chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/rsi-2 ; and 'The 2-Period RSI: A Simple System That Still Earns Its Keep' — https://backtest.substack.com/p/the-2-period-rsi-a-simple-system (both pages read) — transposed, NOT a documented result | **⚠️ transposition** · lore (as transposed) | «medido» | 4 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: DJ30 H4 long `rsi2_up200_sma5` 1.1× · p corr. 1.00 (cruda 0.572) · 47/año — falla: no significativa, no paga 2× |

#### `EURJPY` — lo que la bibliografía dice nombrándolo

| id | familia | qué afirma (dirección — tamaño) | fuente | verificado · grado | estado | lo medido aquí |
|---|---|---|---|---|---|---|
| `SES-33-fx-range-by-session` | `sesion` | none (a volatility fact) — the 08:00-12:00 NY overlap holds 70% of the European-hours range and 80% of the US-hours range; USDJPY and AUDJPY are the pairs whose Asian range equals their European one | Lien, 'Day Trading and Swing Trading the Currency Market' 2nd ed. (2008), ch. 5 Table 5.1, pp. 67-73 (PDF pp. 83-89) — ~/Desktop/Books (text read) | yes · quantified practitioner test (descriptive table) | «descartado por usar reloj» | — |
| `CARRY-48-crash-asymmetry-short` | `ruptura` | short the high-yield/JPY cross — falls are faster than rises — carry returns are negatively skewed; skewness is positive and highest for JPY, most negative for AUD and NZD; a search summary quotes -0.322 daily skew for AUD-vs-USD carry (not located in the text read) | Brunnermeier, Nagel, Pedersen, 'Carry Trades and Currency Crashes', NBER WP 14473 (2008; NBER Macroeconomics Annual) — https://www.nber.org/system/files/working_papers/w14473/w14473.pdf (text read) | yes (text; skew figure not) · peer-reviewed | «medido» | 8 celdas, ninguna llega a 30 operaciones en build: sin contraste |

#### `EURUSD` — lo que la bibliografía dice nombrándolo

| id | familia | qué afirma (dirección — tamaño) | fuente | verificado · grado | estado | lo medido aquí |
|---|---|---|---|---|---|---|
| `TR-11-fitschen-d1-usd-pairs-trend` | `tendencia` | both — $675 per monthly trade on AUDUSD+EURUSD (84 winning months, 69 losing; 2008 alone +4,780, 2009-2011 all negative); gross | Fitschen, 'Building Reliable Trading Systems' (2013), ch. 3 'Find the Path of Least Resistance', pp. 31-44 (PDF pp. 38-51) — ~/Desktop/Books (text read) — Tables 3.5-3.6 | yes · quantified practitioner test | «medido» | 8 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: EURUSD M15 short `strong_d20_21d` 10.8× · p corr. 1.00 (cruda 0.518) · 8/año — falla: no significativa, inestable, pocas operaciones |
| `SES-31-fx-fix-reversals` | `sesion` | USD long before each fix, USD short after — dollar portfolio: +5.3%/yr (2.1 bp/day, t≈12) from 17:00 NY to the Tokyo fix, -5.5%/yr (t≈9.2) after it; +4.3%/yr (t≈4.1) from the European open to the London fix, -4.8%/yr (t≈5.5) from it to the NY close. AUD -7.39%/yr before the Tokyo fix. Trading EUR around the London fix: Sharpe 0.65 AFTER conservative costs, but 'not easy to exploit once transaction costs are accounted for' | Krohn, Mueller, Whelan, 'Foreign Exchange Fixings and Returns Around the Clock' (June 2020 version; later J. Finance 2024) — https://sites.insead.edu/facultyresearch/research/file.cfm?fid=66802 (text read) | yes · peer-reviewed (J. Finance 2024; 2020 working version read) | «descartado por usar reloj» | — |
| `SES-33-fx-range-by-session` | `sesion` | none (a volatility fact) — the 08:00-12:00 NY overlap holds 70% of the European-hours range and 80% of the US-hours range; USDJPY and AUDJPY are the pairs whose Asian range equals their European one | Lien, 'Day Trading and Swing Trading the Currency Market' 2nd ed. (2008), ch. 5 Table 5.1, pp. 67-73 (PDF pp. 83-89) — ~/Desktop/Books (text read) | yes · quantified practitioner test (descriptive table) | «descartado por usar reloj» | — |

#### `GBPJPY` — lo que la bibliografía dice nombrándolo

| id | familia | qué afirma (dirección — tamaño) | fuente | verificado · grado | estado | lo medido aquí |
|---|---|---|---|---|---|---|
| `SES-33-fx-range-by-session` | `sesion` | none (a volatility fact) — the 08:00-12:00 NY overlap holds 70% of the European-hours range and 80% of the US-hours range; USDJPY and AUDJPY are the pairs whose Asian range equals their European one | Lien, 'Day Trading and Swing Trading the Currency Market' 2nd ed. (2008), ch. 5 Table 5.1, pp. 67-73 (PDF pp. 83-89) — ~/Desktop/Books (text read) | yes · quantified practitioner test (descriptive table) | «descartado por usar reloj» | — |
| `REV-42-fitschen-fx-crosses-counter-trend` | `reversion` | both — $629 per monthly trade on the five counter-trend pairs: 192 winning months, 166 losing; only 2000, 2005, 2007 negative; gross | Fitschen, 'Building Reliable Trading Systems' (2013), ch. 3 'Find the Path of Least Resistance', pp. 31-44 (PDF pp. 38-51) — ~/Desktop/Books (text read) — Tables 3.5-3.6 | yes · quantified practitioner test | «medido» | 16 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: GBPJPY H1 short `weak_d20_21d` 9.7× · p corr. 1.00 (cruda 0.573) · 8/año — falla: no significativa, inestable, pocas operaciones |
| `CARRY-48-crash-asymmetry-short` | `ruptura` | short the high-yield/JPY cross — falls are faster than rises — carry returns are negatively skewed; skewness is positive and highest for JPY, most negative for AUD and NZD; a search summary quotes -0.322 daily skew for AUD-vs-USD carry (not located in the text read) | Brunnermeier, Nagel, Pedersen, 'Carry Trades and Currency Crashes', NBER WP 14473 (2008; NBER Macroeconomics Annual) — https://www.nber.org/system/files/working_papers/w14473/w14473.pdf (text read) | yes (text; skew figure not) · peer-reviewed | «medido» | 8 celdas, ninguna llega a 30 operaciones en build: sin contraste |

#### `GBPUSD` — lo que la bibliografía dice nombrándolo

| id | familia | qué afirma (dirección — tamaño) | fuente | verificado · grado | estado | lo medido aquí |
|---|---|---|---|---|---|---|
| `MOM-24-opening-gap-gbpusd` | `momentum` | both — APR 7.2%, Sharpe 1.3, gross | Chan, 'Algorithmic Trading' (2013), ch. 7 'Intraday Momentum Strategies', pp. 155-157 (PDF pp. 173-175) — ~/Desktop/Books (text read) — p. 157 | yes · quantified practitioner test | «descartado por usar reloj» | — |
| `SES-31-fx-fix-reversals` | `sesion` | USD long before each fix, USD short after — dollar portfolio: +5.3%/yr (2.1 bp/day, t≈12) from 17:00 NY to the Tokyo fix, -5.5%/yr (t≈9.2) after it; +4.3%/yr (t≈4.1) from the European open to the London fix, -4.8%/yr (t≈5.5) from it to the NY close. AUD -7.39%/yr before the Tokyo fix. Trading EUR around the London fix: Sharpe 0.65 AFTER conservative costs, but 'not easy to exploit once transaction costs are accounted for' | Krohn, Mueller, Whelan, 'Foreign Exchange Fixings and Returns Around the Clock' (June 2020 version; later J. Finance 2024) — https://sites.insead.edu/facultyresearch/research/file.cfm?fid=66802 (text read) | yes · peer-reviewed (J. Finance 2024; 2020 working version read) | «descartado por usar reloj» | — |
| `SES-33-fx-range-by-session` | `sesion` | none (a volatility fact) — the 08:00-12:00 NY overlap holds 70% of the European-hours range and 80% of the US-hours range; USDJPY and AUDJPY are the pairs whose Asian range equals their European one | Lien, 'Day Trading and Swing Trading the Currency Market' 2nd ed. (2008), ch. 5 Table 5.1, pp. 67-73 (PDF pp. 83-89) — ~/Desktop/Books (text read) | yes · quantified practitioner test (descriptive table) | «descartado por usar reloj» | — |
| `REV-43-fitschen-fx-all-pairs-buy-weak` | `reversion` | both — buy weak +$178, buy strong -$101, buy-and-hold -$87; the long-short counter-trend approach +$137 per trade; negative in 2000, 2007, 2008 (-1,628) | Fitschen, 'Building Reliable Trading Systems' (2013), ch. 3 'Find the Path of Least Resistance', pp. 31-44 (PDF pp. 38-51) — ~/Desktop/Books (text read) — Table 3.3 | yes · quantified practitioner test | «medido» | 8 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: GBPUSD H4 short `weak_d20_21d` 17.2× · p corr. 1.00 (cruda 0.356) · 8/año — falla: no significativa, inestable, pocas operaciones |

#### `NIKKEI225` — lo que la bibliografía dice nombrándolo

| id | familia | qué afirma (dirección — tamaño) | fuente | verificado · grado | estado | lo medido aquí |
|---|---|---|---|---|---|---|
| `MOM-21b-noise-area-clock-free` | `momentum` | both — not from the source — this is a transposition | Zarattini, Aziz, Barbon, 'Beat the Market: An Effective Intraday Momentum Strategy for S&P500 ETF (SPY)' (Swiss Finance Institute RP 24-97, v. Feb 2025) — https://alexandria.unisg.ch/bitstreams/a99aba00-f967-49b3-aceb-f544dc386e0b/download (full text read) — transposed, NOT the paper's rule | **⚠️ transposition** · quantified practitioner test (for 21a; none for this reading) | «medido» | 32 celdas con contraste: 3 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: NIKKEI225 H1 long `noise_k10` 2.6× · p corr. 0.34 (cruda 0.024) · 17/año — falla: no significativa, pocas operaciones |
| `SES-29-overnight-vs-intraday-indices` | `sesion` | long overnight; intraday (cash open→close) negative — cumulative overnight vs intraday, from 1990 or first data to Sep 2020, as extracted from Figure 1: SPY +1288% vs -8%; Nasdaq Comp. +3402% vs -30%; DAX +1532% vs -64%; Nikkei 225 +1142% vs -95%. Cooper, Cliff & Gulen (2008) — the US equity premium is earned overnight — seen only in a search summary: not verified | Knuteson (2020), 'Strikingly Suspicious Overnight and Intraday Returns', arXiv:2010.01727 — https://arxiv.org/pdf/2010.01727 (text read; figures quoted from Figure 1 as extracted) | **⚠️ text read; figure labels paired by position** · quantified practitioner test (arXiv; replicable from public data) | «descartado por usar reloj» | — |
| `REV-36a-index-daily-ar1` | `reversion` | both (fade yesterday's return) — daily AR(1) before → after 1999: S&P 500 +0.103*** → -0.076*** (t -3.29); DAX +0.066*** → -0.016 (t -0.90, not significant); Nikkei 225 +0.042*** → -0.031 (t -1.65); FTSE -0.037** | Baltussen, van Bekkum, Da (2019), 'Indexing and stock market serial dependence around the world', JFE 132:26-48 — https://academicweb.nd.edu/~zda/Indexing.pdf (full text read; Table 1) | yes (Table 1) · peer-reviewed | «medido» | 8 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: NIKKEI225 H1 long `day_down_1d` 1.3× · p corr. 1.00 (cruda 0.268) · 103/año — falla: no significativa, no paga 2× |
| `REV-36c-index-weekly-ar1` | `reversion` | both — weekly AR(1) after 1999: S&P 500 -0.077 (t -1.64); DAX -0.102** (t -2.24); Nikkei 225 -0.018 (t -0.58); Euro Stoxx 50 -0.155**; CAC -0.166*** | Baltussen, van Bekkum, Da (2019), 'Indexing and stock market serial dependence around the world', JFE 132:26-48 — https://academicweb.nd.edu/~zda/Indexing.pdf (full text read; Table 1) | yes · peer-reviewed | «medido» | 8 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: NIKKEI225 M30 long `week_down_5d` 4.4× · p corr. 1.00 (cruda 0.518) · 24/año — falla: no significativa, pocas operaciones |
| `REV-38b-rsi2-intraday-bars` | `reversion` | long — none — not in any source read | StockCharts ChartSchool, 'RSI(2)' (describing Larry Connors' rules, no book cited) — https://chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/rsi-2 ; and 'The 2-Period RSI: A Simple System That Still Earns Its Keep' — https://backtest.substack.com/p/the-2-period-rsi-a-simple-system (both pages read) — transposed, NOT a documented result | **⚠️ transposition** · lore (as transposed) | «medido» | 4 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: NIKKEI225 H4 long `rsi2_up200_sma5` 0.8× · p corr. 1.00 (cruda 0.254) · 42/año — falla: no significativa, no paga 2× |

#### `UKOIL` — lo que la bibliografía dice nombrándolo

| id | familia | qué afirma (dirección — tamaño) | fuente | verificado · grado | estado | lo medido aquí |
|---|---|---|---|---|---|---|
| `TR-05-fast-trend-commodities` | `tendencia` | both — commodities and yields show 'no appreciable degradation' after 2008; large-tick tier Sharpe 1.0-1.2 post-break for the fast signal | Kurth, Eisler, Rej, Bouchaud (2026), 'Is Trend Still Your Friend? A Microstructural Account of the Demise of Short-Term Trend-Following', arXiv:2607.01550 — https://arxiv.org/abs/2607.01550 (full text read) | yes · quantified practitioner test (academic working paper) | «medido» | 8 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: UKOIL M15 short `fast_d5_20_run` -0.5× · p corr. 1.00 (cruda 0.898) · 7/año — falla: no significativa, no paga 2×, inestable, pocas operaciones |
| `TR-08a-fitschen-h1-commodities-10bars` | `tendencia` | both in the source — $30.05 per trade versus $21.26 baseline (+40%); negative in 2003-2005; gross | Fitschen, 'Building Reliable Trading Systems' (2013), ch. 3 'Find the Path of Least Resistance', pp. 31-44 (PDF pp. 38-51) — ~/Desktop/Books (text read) — Table 3.9 | yes · quantified practitioner test | «medido» | 8 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: UKOIL H4 short `fitschen_b10_1d` 0.2× · p corr. 0.98 (cruda 0.227) · 113/año — falla: no significativa, no paga 2× |
| `TR-08b-fitschen-h1-commodities-10days` | `tendencia` | both in the source — $30.05 per trade versus $21.26 baseline (+40%); negative in 2003-2005; gross | Fitschen, 'Building Reliable Trading Systems' (2013), ch. 3 'Find the Path of Least Resistance', pp. 31-44 (PDF pp. 38-51) — ~/Desktop/Books (text read) — Table 3.9 | yes · quantified practitioner test | «medido» | 8 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: UKOIL M15 short `fitschen_d10_1d` 0.3× · p corr. 1.00 (cruda 0.259) · 84/año — falla: no significativa, no paga 2×, inestable |
| `TR-12-chan-crude-30-40` | `tendencia` | both — APR 12%, Sharpe 1.1; the book gives no sample dates and no costs | Chan, 'Algorithmic Trading' (2013), ch. 6 'Interday Momentum Strategies', pp. 133-141 and 151 (PDF pp. 151-159, 169) — ~/Desktop/Books (text read) — p. 140 | yes · quantified practitioner test | «medido» | 8 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: UKOIL H4 long `chan_30_40_run` -0.1× · p corr. 1.00 (cruda 0.397) · 8/año — falla: no significativa, no paga 2×, inestable, pocas operaciones |
| `MOM-25-crude-first-half-hour` | `momentum` | both — USO: β = 0.0118, t = 2.86, R² = 0.67% (2007-2019). The 2023 paper gives no figure in its abstract. An R² of 0.729% in-sample for crude futures (Wen, Gong, Ma, Xu 2021, Economic Modelling) was seen only in a search summary: not verified | Xu, Bouri, Saeed, Wen (2020), 'Intraday return predictability: Evidence from commodity ETFs and their related volatility indices', Resources Policy — https://pmc.ncbi.nlm.nih.gov/articles/PMC7480318/ (page read through the fetch summariser) ; Wen, Indriawan, Lien, Xu (2023), 'Intraday Return Predictability in the Crude Oil Market: The Role of EIA Inventory Announcements', The Energy Journal 44(5):149-172 — https://ideas.repec.org/a/sae/enejou/v44y2023i5p149-172.html (abstract only) | **⚠️ XU via summariser; WEN23 abstract only** · peer-reviewed | «descartado por usar reloj» | — |

#### `USA500` — lo que la bibliografía dice nombrándolo

| id | familia | qué afirma (dirección — tamaño) | fuente | verificado · grado | estado | lo medido aquí |
|---|---|---|---|---|---|---|
| `MOM-18-first-last-half-hour-us` | `momentum` | both (sign of the first half-hour return) — R² 1.6% (first half-hour), 2.6% adding the 12th half-hour; out-of-sample R² 1.69%; timing strategy SD 6.19%/yr, Sharpe 1.08; by first-half-hour volatility tercile the strategy earns 0.54% (low), 4.75% (medium), 14.73% (high) a year; gross of costs (authors bound costs at 2.52%/yr) | Gao, Han, Li, Zhou, 'Intraday Momentum: The First Half-Hour Return Predicts the Last Half-Hour Return' (Oct 2014 draft; published as 'Market intraday momentum', JFE 2018) — https://www.smallake.kr/wp-content/uploads/2015/01/SSRN-id2440866.pdf (full text read) | yes (2014 draft) · peer-reviewed | «descartado por usar reloj» | — |
| `MOM-21a-noise-area-breakout` | `momentum` | both; the paper finds no relation between VIX and SHORT-trade profit — 2007-2024: total 1,985% net, 19.6%/yr, Sharpe 1.33, hit ratio 43%; costs $0.0035/share + $0.001 slippage; Sharpe ≈1.5 on all days, ≈3.5 when VIX > 40; average day +12 bp (t 5.34) | Zarattini, Aziz, Barbon, 'Beat the Market: An Effective Intraday Momentum Strategy for S&P500 ETF (SPY)' (Swiss Finance Institute RP 24-97, v. Feb 2025) — https://alexandria.unisg.ch/bitstreams/a99aba00-f967-49b3-aceb-f544dc386e0b/download (full text read) | yes · quantified practitioner test (SFI research paper, practitioner authors) | «descartado por usar reloj» | — |
| `MOM-21b-noise-area-clock-free` | `momentum` | both — not from the source — this is a transposition | Zarattini, Aziz, Barbon, 'Beat the Market: An Effective Intraday Momentum Strategy for S&P500 ETF (SPY)' (Swiss Finance Institute RP 24-97, v. Feb 2025) — https://alexandria.unisg.ch/bitstreams/a99aba00-f967-49b3-aceb-f544dc386e0b/download (full text read) — transposed, NOT the paper's rule | **⚠️ transposition** · quantified practitioner test (for 21a; none for this reading) | «medido» | 32 celdas con contraste: 1 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: USA500 M15 long `noise_k07` 2.9× · p corr. 0.53 (cruda 0.046) · 47/año — falla: no significativa |
| `VOL-22-narrow-range-then-intraday-trend` | `volatilidad` | both — intraday-momentum PnL per day: unconditional 12 bp (t 5.34, n=2,620); after NR4 22 bp (t 5.14, n=660, Sharpe 3.2); NR7 16 bp (t 3.07, n=367); Triangle 14 bp (t 3.19, n=664); after an inside day 5 bp (t 0.85); after a trend day -2 bp (t -0.24) | Zarattini, Aziz, Barbon, 'Beat the Market: An Effective Intraday Momentum Strategy for S&P500 ETF (SPY)' (Swiss Finance Institute RP 24-97, v. Feb 2025) — https://alexandria.unisg.ch/bitstreams/a99aba00-f967-49b3-aceb-f544dc386e0b/download (full text read) — Table 5 | yes · quantified practitioner test | «medido» | 8 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: USA500 M15 long `noise_k05_nr4` 3.1× · p corr. 0.68 (cruda 0.074) · 20/año — falla: no significativa, pocas operaciones |
| `SES-28-overnight-drift-us-index` | `sesion` | long — +3.7%/yr = 1.48 bp per day in that one hour; positive in 20 of 23 years, significant in 17; hours 24-01, 01-02, 02-03 earn 0.46, 0.43, 1.5 bp; the 09:00-10:00 NY hour is negative only in recessions | Boyarchenko, Larsen, Whelan, 'The Overnight Drift', FRB New York Staff Report 917 (2020, rev. 2022) — https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr917.pdf (text read) | yes · quantified practitioner test (Federal Reserve staff report, academic) | «descartado por usar reloj» | — |
| `SES-29-overnight-vs-intraday-indices` | `sesion` | long overnight; intraday (cash open→close) negative — cumulative overnight vs intraday, from 1990 or first data to Sep 2020, as extracted from Figure 1: SPY +1288% vs -8%; Nasdaq Comp. +3402% vs -30%; DAX +1532% vs -64%; Nikkei 225 +1142% vs -95%. Cooper, Cliff & Gulen (2008) — the US equity premium is earned overnight — seen only in a search summary: not verified | Knuteson (2020), 'Strikingly Suspicious Overnight and Intraday Returns', arXiv:2010.01727 — https://arxiv.org/pdf/2010.01727 (text read; figures quoted from Figure 1 as extracted) | **⚠️ text read; figure labels paired by position** · quantified practitioner test (arXiv; replicable from public data) | «descartado por usar reloj» | — |
| `CAL-34-turn-of-month` | `sesion` | long — 7.2%/yr, Sharpe 1.04, volatility 6.9%, max drawdown -20.79% (Quantpedia's indicative figures) | Quantpedia, 'Turn of the Month in Equity Indexes' (summarising McConnell & Xu 2008) — https://quantpedia.com/strategies/turn-of-the-month-in-equity-indexes (page read; the paper itself not opened) | **⚠️ summary page only** · peer-reviewed (paper) seen through a practitioner summary | «descartado por usar reloj» | — |
| `CAL-35-pre-fomc-drift` | `sesion` | long — 'large average excess returns' accounting for 'sizable fractions of total annual realized stock returns' — no number on the page read | Lucca & Moench, 'The Pre-FOMC Announcement Drift', FRBNY Staff Report 512 / J. Finance 2015 — https://www.newyorkfed.org/research/staff_reports/sr512.html (abstract page only) | **⚠️ abstract page only** · peer-reviewed | «descartado por usar reloj» | — |
| `REV-36a-index-daily-ar1` | `reversion` | both (fade yesterday's return) — daily AR(1) before → after 1999: S&P 500 +0.103*** → -0.076*** (t -3.29); DAX +0.066*** → -0.016 (t -0.90, not significant); Nikkei 225 +0.042*** → -0.031 (t -1.65); FTSE -0.037** | Baltussen, van Bekkum, Da (2019), 'Indexing and stock market serial dependence around the world', JFE 132:26-48 — https://academicweb.nd.edu/~zda/Indexing.pdf (full text read; Table 1) | yes (Table 1) · peer-reviewed | «medido» | 8 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: USA500 M15 long `day_down_1d` 1.8× · p corr. 1.00 (cruda 0.574) · 95/año — falla: no significativa, no paga 2× |
| `REV-36c-index-weekly-ar1` | `reversion` | both — weekly AR(1) after 1999: S&P 500 -0.077 (t -1.64); DAX -0.102** (t -2.24); Nikkei 225 -0.018 (t -0.58); Euro Stoxx 50 -0.155**; CAC -0.166*** | Baltussen, van Bekkum, Da (2019), 'Indexing and stock market serial dependence around the world', JFE 132:26-48 — https://academicweb.nd.edu/~zda/Indexing.pdf (full text read; Table 1) | yes · peer-reviewed | «medido» | 8 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: USA500 M30 long `week_down_5d` 13.1× · p corr. 1.00 (cruda 0.306) · 22/año — falla: no significativa, pocas operaciones |
| `REV-37a-ibs-long` | `reversion` | long — average next-day return +0.35% when IBS < 0.2, -0.13% when IBS > 0.8; thresholds ≈0.4 and 0.9 bound the predictive zone; 'difficult alone due to transaction costs', better combined with RSI(3) | Pagonidis, 'The IBS Effect: Mean Reversion in Equity ETFs' (NAAIM paper, 2014) — https://www.naaim.org/wp-content/uploads/2014/04/00V_Alexander_Pagonidis_The-IBS-Effect-Mean-Reversion-in-Equity-ETFs-1.pdf (text read) | yes · quantified practitioner test | «medido» | 8 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: USA500 H4 long `ibs_low_1d` 5.3× · p corr. 0.65 (cruda 0.068) · 39/año — falla: no significativa, pocas operaciones |
| `REV-37b-ibs-short` | `reversion` | short — -0.13% average next-day return after IBS > 0.8 (all regimes) | Pagonidis, 'The IBS Effect: Mean Reversion in Equity ETFs' (NAAIM paper, 2014) — https://www.naaim.org/wp-content/uploads/2014/04/00V_Alexander_Pagonidis_The-IBS-Effect-Mean-Reversion-in-Equity-ETFs-1.pdf (text read) | yes · quantified practitioner test | «medido» | 4 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: USA500 H4 short `ibs_low_volhigh_up_1d` -1.7× · p corr. 1.00 (cruda 0.501) · 7/año — falla: no significativa, no paga 2×, inestable, pocas operaciones |
| `REV-38a-rsi2-daily` | `reversion` | long (the short mirror exists in Connors' rules; no opened test of it) — Nasdaq-100 stocks, Dec 2006-2025: win rate 64.33%, average winner +2.33%, loser -3.02%, profit factor 1.45, 17.84%/yr, max drawdown 29.15%, ≈1,000 trades | StockCharts ChartSchool, 'RSI(2)' (describing Larry Connors' rules, no book cited) — https://chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/rsi-2 ; and 'The 2-Period RSI: A Simple System That Still Earns Its Keep' — https://backtest.substack.com/p/the-2-period-rsi-a-simple-system (both pages read) | **⚠️ pages read** · quantified practitioner test (blog backtest; rules as described by StockCharts, Connors' book not opened) | «medido» | 4 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: USA500 H4 long `connors_d1` 13.8× · p corr. 0.82 (cruda 0.122) · 8/año — falla: no significativa, pocas operaciones |
| `REV-38b-rsi2-intraday-bars` | `reversion` | long — none — not in any source read | StockCharts ChartSchool, 'RSI(2)' (describing Larry Connors' rules, no book cited) — https://chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/rsi-2 ; and 'The 2-Period RSI: A Simple System That Still Earns Its Keep' — https://backtest.substack.com/p/the-2-period-rsi-a-simple-system (both pages read) — transposed, NOT a documented result | **⚠️ transposition** · lore (as transposed) | «medido» | 4 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: USA500 H1 long `rsi2_up200_sma5` 0.5× · p corr. 0.97 (cruda 0.214) · 188/año — falla: no significativa, no paga 2× |
| `REV-40-fitschen-stocks-daily-counter-trend` | `reversion` | LONG ONLY: the short side loses — buying weak stocks +1.56%/month vs +0.71% buy-and-hold and +0.16% buying strong (2000-2011). Donchian counter-trend, 10-day: long +$69/trade (6,248 wins, 2,779 losses), short -$43/trade (5,355 wins, 3,631 losses; average win $258, loss $498). Profit/trade falls from $119 (20-day) to $24 (2-day) while gain-to-pain rises 0.70 → 1.24; survivorship bias acknowledged | Fitschen, 'Building Reliable Trading Systems' (2013), ch. 3 'Find the Path of Least Resistance', pp. 31-44 (PDF pp. 38-51) — ~/Desktop/Books (text read) ; Fitschen, 'Building Reliable Trading Systems' (2013), ch. 5, pp. 66-68 (PDF pp. 73-75), Tables 5.1-5.2 — ~/Desktop/Books (text read) | yes · quantified practitioner test | «medido» | 4 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: USA500 H4 long `out10_counter` 31.3× · p corr. 0.74 (cruda 0.091) · 8/año — falla: no significativa, pocas operaciones |
| `REV-41-williams-pullback-in-uptrend` | `reversion` | long — buy every day, exit next close: 52% wins, $134/trade; after three down closes: 58%, $353; uptrend+pullback: 57%, $421 (figures as recorded in the dossier, optimised on the full sample) | Williams, 'Long-Term Secrets to Short-Term Trading' (1999), pp. 94-95 — via docs/AgentPDFs/ideas-de-internet-y-libros-2026-09-27.md (the project's own catalogue; the book pages it cites were NOT re-opened in this task) | **⚠️ via dossier — book page not re-opened** · quantified practitioner test (in-sample, pre-2000) | «medido» | 8 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: USA500 M15 long `d1_down3_1d` 3.3× · p corr. 1.00 (cruda 0.322) · 17/año — falla: no significativa, inestable, pocas operaciones |
| `REV-46-chan-gap-fade-with-trend-filter` | `reversion` | long (the short mirror also reported profitable) — APR 8.7%, Sharpe 1.5 (10 stocks a day), gross | Chan, 'Algorithmic Trading' (2013), ch. 4 'Buy-on-Gap Model', pp. 92-95 (PDF pp. 110-113) — ~/Desktop/Books (text read) | yes · quantified practitioner test | «descartado por usar reloj» | — |

#### `USATEC` — lo que la bibliografía dice nombrándolo

| id | familia | qué afirma (dirección — tamaño) | fuente | verificado · grado | estado | lo medido aquí |
|---|---|---|---|---|---|---|
| `TR-09-fitschen-h1-stocks` | `tendencia` | long only in the source — 0.12% per trade versus 0.07% baseline; fades to 0.01-0.10% from 2005 and -0.05% in 2010; gross | Fitschen, 'Building Reliable Trading Systems' (2013), ch. 3 'Find the Path of Least Resistance', pp. 31-44 (PDF pp. 38-51) — ~/Desktop/Books (text read) — Table 3.8 | yes · quantified practitioner test | «medido» | 4 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: USATEC M30 long `fitschen_b10_1d` 3.7× · p corr. 0.99 (cruda 0.245) · 156/año — falla: no significativa |
| `MOM-21b-noise-area-clock-free` | `momentum` | both — not from the source — this is a transposition | Zarattini, Aziz, Barbon, 'Beat the Market: An Effective Intraday Momentum Strategy for S&P500 ETF (SPY)' (Swiss Finance Institute RP 24-97, v. Feb 2025) — https://alexandria.unisg.ch/bitstreams/a99aba00-f967-49b3-aceb-f544dc386e0b/download (full text read) — transposed, NOT the paper's rule | **⚠️ transposition** · quantified practitioner test (for 21a; none for this reading) | «medido» | 32 celdas con contraste: 2 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: USATEC M15 long `noise_k07` 2.9× · p corr. 0.45 (cruda 0.036) · 47/año — falla: no significativa |
| `NEG-27-mnq-ohlcv-intraday-momentum` | `momentum` | both — none passed: eleven families had gross returns of 0.07-1.50 index points, below a 2.0-point friction; two session-based controls did pass (OOS t 3.11 and 4.30) | 'Structural Limits of OHLCV-Based Intraday Momentum Signals in MNQ Futures: A Systematic Falsification Study', arXiv:2605.04004 — https://arxiv.org/abs/2605.04004 (abstract only) | **⚠️ abstract only** · quantified practitioner test (arXiv, single author study) | «descartado por usar reloj» | — |
| `SES-29-overnight-vs-intraday-indices` | `sesion` | long overnight; intraday (cash open→close) negative — cumulative overnight vs intraday, from 1990 or first data to Sep 2020, as extracted from Figure 1: SPY +1288% vs -8%; Nasdaq Comp. +3402% vs -30%; DAX +1532% vs -64%; Nikkei 225 +1142% vs -95%. Cooper, Cliff & Gulen (2008) — the US equity premium is earned overnight — seen only in a search summary: not verified | Knuteson (2020), 'Strikingly Suspicious Overnight and Intraday Returns', arXiv:2010.01727 — https://arxiv.org/pdf/2010.01727 (text read; figures quoted from Figure 1 as extracted) | **⚠️ text read; figure labels paired by position** · quantified practitioner test (arXiv; replicable from public data) | «descartado por usar reloj» | — |
| `REV-36a-index-daily-ar1` | `reversion` | both (fade yesterday's return) — daily AR(1) before → after 1999: S&P 500 +0.103*** → -0.076*** (t -3.29); DAX +0.066*** → -0.016 (t -0.90, not significant); Nikkei 225 +0.042*** → -0.031 (t -1.65); FTSE -0.037** | Baltussen, van Bekkum, Da (2019), 'Indexing and stock market serial dependence around the world', JFE 132:26-48 — https://academicweb.nd.edu/~zda/Indexing.pdf (full text read; Table 1) | yes (Table 1) · peer-reviewed | «medido» | 8 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: USATEC M15 long `day_down_1d` 3.2× · p corr. 1.00 (cruda 0.494) · 94/año — falla: no significativa |
| `REV-37a-ibs-long` | `reversion` | long — average next-day return +0.35% when IBS < 0.2, -0.13% when IBS > 0.8; thresholds ≈0.4 and 0.9 bound the predictive zone; 'difficult alone due to transaction costs', better combined with RSI(3) | Pagonidis, 'The IBS Effect: Mean Reversion in Equity ETFs' (NAAIM paper, 2014) — https://www.naaim.org/wp-content/uploads/2014/04/00V_Alexander_Pagonidis_The-IBS-Effect-Mean-Reversion-in-Equity-ETFs-1.pdf (text read) | yes · quantified practitioner test | «medido» | 8 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: USATEC M15 long `ibs_low_1d` 9.8× · p corr. 0.73 (cruda 0.089) · 36/año — falla: no significativa, pocas operaciones |
| `REV-37b-ibs-short` | `reversion` | short — -0.13% average next-day return after IBS > 0.8 (all regimes) | Pagonidis, 'The IBS Effect: Mean Reversion in Equity ETFs' (NAAIM paper, 2014) — https://www.naaim.org/wp-content/uploads/2014/04/00V_Alexander_Pagonidis_The-IBS-Effect-Mean-Reversion-in-Equity-ETFs-1.pdf (text read) | yes · quantified practitioner test | «medido» | 4 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: USATEC M15 short `ibs_low_volhigh_up_1d` -8.3× · p corr. 1.00 (cruda 0.707) · 5/año — falla: no significativa, no paga 2×, inestable, pocas operaciones |
| `REV-38a-rsi2-daily` | `reversion` | long (the short mirror exists in Connors' rules; no opened test of it) — Nasdaq-100 stocks, Dec 2006-2025: win rate 64.33%, average winner +2.33%, loser -3.02%, profit factor 1.45, 17.84%/yr, max drawdown 29.15%, ≈1,000 trades | StockCharts ChartSchool, 'RSI(2)' (describing Larry Connors' rules, no book cited) — https://chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/rsi-2 ; and 'The 2-Period RSI: A Simple System That Still Earns Its Keep' — https://backtest.substack.com/p/the-2-period-rsi-a-simple-system (both pages read) | **⚠️ pages read** · quantified practitioner test (blog backtest; rules as described by StockCharts, Connors' book not opened) | «medido» | 4 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: USATEC H4 long `connors_d1` 17.2× · p corr. 0.63 (cruda 0.064) · 8/año — falla: no significativa, pocas operaciones |
| `REV-38b-rsi2-intraday-bars` | `reversion` | long — none — not in any source read | StockCharts ChartSchool, 'RSI(2)' (describing Larry Connors' rules, no book cited) — https://chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/rsi-2 ; and 'The 2-Period RSI: A Simple System That Still Earns Its Keep' — https://backtest.substack.com/p/the-2-period-rsi-a-simple-system (both pages read) — transposed, NOT a documented result | **⚠️ transposition** · lore (as transposed) | «medido» | 4 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: USATEC H4 long `rsi2_up200_sma5` 2.1× · p corr. 1.00 (cruda 0.541) · 46/año — falla: no significativa |
| `REV-40-fitschen-stocks-daily-counter-trend` | `reversion` | LONG ONLY: the short side loses — buying weak stocks +1.56%/month vs +0.71% buy-and-hold and +0.16% buying strong (2000-2011). Donchian counter-trend, 10-day: long +$69/trade (6,248 wins, 2,779 losses), short -$43/trade (5,355 wins, 3,631 losses; average win $258, loss $498). Profit/trade falls from $119 (20-day) to $24 (2-day) while gain-to-pain rises 0.70 → 1.24; survivorship bias acknowledged | Fitschen, 'Building Reliable Trading Systems' (2013), ch. 3 'Find the Path of Least Resistance', pp. 31-44 (PDF pp. 38-51) — ~/Desktop/Books (text read) ; Fitschen, 'Building Reliable Trading Systems' (2013), ch. 5, pp. 66-68 (PDF pp. 73-75), Tables 5.1-5.2 — ~/Desktop/Books (text read) | yes · quantified practitioner test | «medido» | 4 celdas con contraste: 3 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: USATEC M30 long `out10_counter` 48.2× · p corr. 0.52 (cruda 0.045) · 9/año — falla: no significativa, pocas operaciones |

#### `USDCAD` — lo que la bibliografía dice nombrándolo

| id | familia | qué afirma (dirección — tamaño) | fuente | verificado · grado | estado | lo medido aquí |
|---|---|---|---|---|---|---|
| `SES-31-fx-fix-reversals` | `sesion` | USD long before each fix, USD short after — dollar portfolio: +5.3%/yr (2.1 bp/day, t≈12) from 17:00 NY to the Tokyo fix, -5.5%/yr (t≈9.2) after it; +4.3%/yr (t≈4.1) from the European open to the London fix, -4.8%/yr (t≈5.5) from it to the NY close. AUD -7.39%/yr before the Tokyo fix. Trading EUR around the London fix: Sharpe 0.65 AFTER conservative costs, but 'not easy to exploit once transaction costs are accounted for' | Krohn, Mueller, Whelan, 'Foreign Exchange Fixings and Returns Around the Clock' (June 2020 version; later J. Finance 2024) — https://sites.insead.edu/facultyresearch/research/file.cfm?fid=66802 (text read) | yes · peer-reviewed (J. Finance 2024; 2020 working version read) | «descartado por usar reloj» | — |
| `SES-33-fx-range-by-session` | `sesion` | none (a volatility fact) — the 08:00-12:00 NY overlap holds 70% of the European-hours range and 80% of the US-hours range; USDJPY and AUDJPY are the pairs whose Asian range equals their European one | Lien, 'Day Trading and Swing Trading the Currency Market' 2nd ed. (2008), ch. 5 Table 5.1, pp. 67-73 (PDF pp. 83-89) — ~/Desktop/Books (text read) | yes · quantified practitioner test (descriptive table) | «descartado por usar reloj» | — |
| `REV-43-fitschen-fx-all-pairs-buy-weak` | `reversion` | both — buy weak +$178, buy strong -$101, buy-and-hold -$87; the long-short counter-trend approach +$137 per trade; negative in 2000, 2007, 2008 (-1,628) | Fitschen, 'Building Reliable Trading Systems' (2013), ch. 3 'Find the Path of Least Resistance', pp. 31-44 (PDF pp. 38-51) — ~/Desktop/Books (text read) — Table 3.3 | yes · quantified practitioner test | «medido» | 8 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: USDCAD H4 long `weak_d20_21d` 21.3× · p corr. 0.88 (cruda 0.155) · 8/año — falla: no significativa, inestable, pocas operaciones |
| `REV-44-chan-usdcad-half-life` | `reversion` | both — USDCAD: ADF cannot reject a random walk at 90%; variance-ratio test does not reject (p = 0.367); half-life ≈115 days. AUDCAD linear mean reversion with a 20-day look-back: APR 6.2%, Sharpe 0.54 (6.7% / 0.58 ignoring rollover) | Chan, 'Algorithmic Trading' (2013), ch. 2 Examples 2.1-2.5, pp. 42-50 (PDF pp. 60-68), and ch. 5 Example 5.2, pp. 114-116 (PDF pp. 132-134) — ~/Desktop/Books (text read) | yes · quantified practitioner test | «la bibliografía lo afirma y aquí no se mide» | es una vida media por par en D1; el perfil sólo la mide en el marco de la celda (`pullback_speed`) |

#### `USDCHF` — lo que la bibliografía dice nombrándolo

| id | familia | qué afirma (dirección — tamaño) | fuente | verificado · grado | estado | lo medido aquí |
|---|---|---|---|---|---|---|
| `SES-31-fx-fix-reversals` | `sesion` | USD long before each fix, USD short after — dollar portfolio: +5.3%/yr (2.1 bp/day, t≈12) from 17:00 NY to the Tokyo fix, -5.5%/yr (t≈9.2) after it; +4.3%/yr (t≈4.1) from the European open to the London fix, -4.8%/yr (t≈5.5) from it to the NY close. AUD -7.39%/yr before the Tokyo fix. Trading EUR around the London fix: Sharpe 0.65 AFTER conservative costs, but 'not easy to exploit once transaction costs are accounted for' | Krohn, Mueller, Whelan, 'Foreign Exchange Fixings and Returns Around the Clock' (June 2020 version; later J. Finance 2024) — https://sites.insead.edu/facultyresearch/research/file.cfm?fid=66802 (text read) | yes · peer-reviewed (J. Finance 2024; 2020 working version read) | «descartado por usar reloj» | — |
| `SES-33-fx-range-by-session` | `sesion` | none (a volatility fact) — the 08:00-12:00 NY overlap holds 70% of the European-hours range and 80% of the US-hours range; USDJPY and AUDJPY are the pairs whose Asian range equals their European one | Lien, 'Day Trading and Swing Trading the Currency Market' 2nd ed. (2008), ch. 5 Table 5.1, pp. 67-73 (PDF pp. 83-89) — ~/Desktop/Books (text read) | yes · quantified practitioner test (descriptive table) | «descartado por usar reloj» | — |
| `REV-43-fitschen-fx-all-pairs-buy-weak` | `reversion` | both — buy weak +$178, buy strong -$101, buy-and-hold -$87; the long-short counter-trend approach +$137 per trade; negative in 2000, 2007, 2008 (-1,628) | Fitschen, 'Building Reliable Trading Systems' (2013), ch. 3 'Find the Path of Least Resistance', pp. 31-44 (PDF pp. 38-51) — ~/Desktop/Books (text read) — Table 3.3 | yes · quantified practitioner test | «medido» | 8 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: USDCHF H4 short `weak_d20_21d` 16.9× · p corr. 0.91 (cruda 0.169) · 8/año — falla: no significativa, pocas operaciones |

#### `USDJPY` — lo que la bibliografía dice nombrándolo

| id | familia | qué afirma (dirección — tamaño) | fuente | verificado · grado | estado | lo medido aquí |
|---|---|---|---|---|---|---|
| `SES-31-fx-fix-reversals` | `sesion` | USD long before each fix, USD short after — dollar portfolio: +5.3%/yr (2.1 bp/day, t≈12) from 17:00 NY to the Tokyo fix, -5.5%/yr (t≈9.2) after it; +4.3%/yr (t≈4.1) from the European open to the London fix, -4.8%/yr (t≈5.5) from it to the NY close. AUD -7.39%/yr before the Tokyo fix. Trading EUR around the London fix: Sharpe 0.65 AFTER conservative costs, but 'not easy to exploit once transaction costs are accounted for' | Krohn, Mueller, Whelan, 'Foreign Exchange Fixings and Returns Around the Clock' (June 2020 version; later J. Finance 2024) — https://sites.insead.edu/facultyresearch/research/file.cfm?fid=66802 (text read) | yes · peer-reviewed (J. Finance 2024; 2020 working version read) | «descartado por usar reloj» | — |
| `SES-32-jpy-local-hours` | `sesion` | USDJPY down in the Asian day, up in US hours — post-Tokyo-fix reversal for JPY 7.70%/yr; other figures not extracted | Krohn, Mueller, Whelan, 'Foreign Exchange Fixings and Returns Around the Clock' (June 2020 version; later J. Finance 2024) — https://sites.insead.edu/facultyresearch/research/file.cfm?fid=66802 (text read). Ranaldo (2009, J. Banking & Finance 33:2199) documents the general time-of-day pattern; two machine summaries of its abstract disagreed on the SIGN, so its direction is NOT verified here | **⚠️ Krohn yes; Ranaldo's direction not verified** · peer-reviewed | «descartado por usar reloj» | — |
| `SES-33-fx-range-by-session` | `sesion` | none (a volatility fact) — the 08:00-12:00 NY overlap holds 70% of the European-hours range and 80% of the US-hours range; USDJPY and AUDJPY are the pairs whose Asian range equals their European one | Lien, 'Day Trading and Swing Trading the Currency Market' 2nd ed. (2008), ch. 5 Table 5.1, pp. 67-73 (PDF pp. 83-89) — ~/Desktop/Books (text read) | yes · quantified practitioner test (descriptive table) | «descartado por usar reloj» | — |
| `REV-43-fitschen-fx-all-pairs-buy-weak` | `reversion` | both — buy weak +$178, buy strong -$101, buy-and-hold -$87; the long-short counter-trend approach +$137 per trade; negative in 2000, 2007, 2008 (-1,628) | Fitschen, 'Building Reliable Trading Systems' (2013), ch. 3 'Find the Path of Least Resistance', pp. 31-44 (PDF pp. 38-51) — ~/Desktop/Books (text read) — Table 3.3 | yes · quantified practitioner test | «medido» | 8 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: USDJPY M15 long `weak_d20_21d` 7.1× · p corr. 1.00 (cruda 0.386) · 8/año — falla: no significativa, pocas operaciones |
| `CARRY-48-crash-asymmetry-short` | `ruptura` | short the high-yield/JPY cross — falls are faster than rises — carry returns are negatively skewed; skewness is positive and highest for JPY, most negative for AUD and NZD; a search summary quotes -0.322 daily skew for AUD-vs-USD carry (not located in the text read) | Brunnermeier, Nagel, Pedersen, 'Carry Trades and Currency Crashes', NBER WP 14473 (2008; NBER Macroeconomics Annual) — https://www.nber.org/system/files/working_papers/w14473/w14473.pdf (text read) | yes (text; skew figure not) · peer-reviewed | «medido» | 8 celdas, ninguna llega a 30 operaciones en build: sin contraste |

#### `USOIL` — lo que la bibliografía dice nombrándolo

| id | familia | qué afirma (dirección — tamaño) | fuente | verificado · grado | estado | lo medido aquí |
|---|---|---|---|---|---|---|
| `TR-05-fast-trend-commodities` | `tendencia` | both — commodities and yields show 'no appreciable degradation' after 2008; large-tick tier Sharpe 1.0-1.2 post-break for the fast signal | Kurth, Eisler, Rej, Bouchaud (2026), 'Is Trend Still Your Friend? A Microstructural Account of the Demise of Short-Term Trend-Following', arXiv:2607.01550 — https://arxiv.org/abs/2607.01550 (full text read) | yes · quantified practitioner test (academic working paper) | «medido» | 8 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: USOIL M30 short `fast_d5_20_run` -0.4× · p corr. 1.00 (cruda 0.642) · 7/año — falla: no significativa, no paga 2×, inestable, pocas operaciones |
| `TR-08a-fitschen-h1-commodities-10bars` | `tendencia` | both in the source — $30.05 per trade versus $21.26 baseline (+40%); negative in 2003-2005; gross | Fitschen, 'Building Reliable Trading Systems' (2013), ch. 3 'Find the Path of Least Resistance', pp. 31-44 (PDF pp. 38-51) — ~/Desktop/Books (text read) — Table 3.9 | yes · quantified practitioner test | «medido» | 8 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: USOIL H4 short `fitschen_b10_1d` 0.3× · p corr. 0.93 (cruda 0.180) · 111/año — falla: no significativa, no paga 2× |
| `TR-08b-fitschen-h1-commodities-10days` | `tendencia` | both in the source — $30.05 per trade versus $21.26 baseline (+40%); negative in 2003-2005; gross | Fitschen, 'Building Reliable Trading Systems' (2013), ch. 3 'Find the Path of Least Resistance', pp. 31-44 (PDF pp. 38-51) — ~/Desktop/Books (text read) — Table 3.9 | yes · quantified practitioner test | «medido» | 8 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: USOIL M30 short `fitschen_d10_1d` 0.4× · p corr. 0.77 (cruda 0.103) · 88/año — falla: no significativa, no paga 2× |
| `TR-12-chan-crude-30-40` | `tendencia` | both — APR 12%, Sharpe 1.1; the book gives no sample dates and no costs | Chan, 'Algorithmic Trading' (2013), ch. 6 'Interday Momentum Strategies', pp. 133-141 and 151 (PDF pp. 151-159, 169) — ~/Desktop/Books (text read) — p. 140 | yes · quantified practitioner test | «medido» | 8 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: USOIL H4 long `chan_30_40_run` 1.3× · p corr. 0.82 (cruda 0.122) · 10/año — falla: no significativa, no paga 2×, pocas operaciones |
| `MOM-25-crude-first-half-hour` | `momentum` | both — USO: β = 0.0118, t = 2.86, R² = 0.67% (2007-2019). The 2023 paper gives no figure in its abstract. An R² of 0.729% in-sample for crude futures (Wen, Gong, Ma, Xu 2021, Economic Modelling) was seen only in a search summary: not verified | Xu, Bouri, Saeed, Wen (2020), 'Intraday return predictability: Evidence from commodity ETFs and their related volatility indices', Resources Policy — https://pmc.ncbi.nlm.nih.gov/articles/PMC7480318/ (page read through the fetch summariser) ; Wen, Indriawan, Lien, Xu (2023), 'Intraday Return Predictability in the Crude Oil Market: The Role of EIA Inventory Announcements', The Energy Journal 44(5):149-172 — https://ideas.repec.org/a/sae/enejou/v44y2023i5p149-172.html (abstract only) | **⚠️ XU via summariser; WEN23 abstract only** · peer-reviewed | «descartado por usar reloj» | — |

#### `XAGUSD` — lo que la bibliografía dice nombrándolo

| id | familia | qué afirma (dirección — tamaño) | fuente | verificado · grado | estado | lo medido aquí |
|---|---|---|---|---|---|---|
| `TR-05-fast-trend-commodities` | `tendencia` | both — commodities and yields show 'no appreciable degradation' after 2008; large-tick tier Sharpe 1.0-1.2 post-break for the fast signal | Kurth, Eisler, Rej, Bouchaud (2026), 'Is Trend Still Your Friend? A Microstructural Account of the Demise of Short-Term Trend-Following', arXiv:2607.01550 — https://arxiv.org/abs/2607.01550 (full text read) | yes · quantified practitioner test (academic working paper) | «medido» | 8 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: XAGUSD M30 short `fast_d5_20_run` -8.3× · p corr. 1.00 (cruda 0.730) · 8/año — falla: no significativa, no paga 2×, inestable, pocas operaciones |
| `TR-08a-fitschen-h1-commodities-10bars` | `tendencia` | both in the source — $30.05 per trade versus $21.26 baseline (+40%); negative in 2003-2005; gross | Fitschen, 'Building Reliable Trading Systems' (2013), ch. 3 'Find the Path of Least Resistance', pp. 31-44 (PDF pp. 38-51) — ~/Desktop/Books (text read) — Table 3.9 | yes · quantified practitioner test | «medido» | 8 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: XAGUSD H1 long `fitschen_b10_1d` 0.4× · p corr. 0.97 (cruda 0.216) · 197/año — falla: no significativa, no paga 2×, inestable |
| `TR-08b-fitschen-h1-commodities-10days` | `tendencia` | both in the source — $30.05 per trade versus $21.26 baseline (+40%); negative in 2003-2005; gross | Fitschen, 'Building Reliable Trading Systems' (2013), ch. 3 'Find the Path of Least Resistance', pp. 31-44 (PDF pp. 38-51) — ~/Desktop/Books (text read) — Table 3.9 | yes · quantified practitioner test | «medido» | 8 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: XAGUSD M15 long `fitschen_d10_1d` 0.8× · p corr. 0.58 (cruda 0.054) · 104/año — falla: no significativa, no paga 2× |
| `MOM-26-metals-late-session-half-hours` | `momentum` | both — GLD: β = 0.0436, t = 3.03, R² = 0.49% (2004-2019); SLV: β = 0.1260, t = 3.03, R² = 1.72% (2006-2020) | Xu, Bouri, Saeed, Wen (2020), 'Intraday return predictability: Evidence from commodity ETFs and their related volatility indices', Resources Policy — https://pmc.ncbi.nlm.nih.gov/articles/PMC7480318/ (page read through the fetch summariser) | **⚠️ via summariser** · peer-reviewed | «descartado por usar reloj» | — |

#### `XAUUSD` — lo que la bibliografía dice nombrándolo

| id | familia | qué afirma (dirección — tamaño) | fuente | verificado · grado | estado | lo medido aquí |
|---|---|---|---|---|---|---|
| `TR-05-fast-trend-commodities` | `tendencia` | both — commodities and yields show 'no appreciable degradation' after 2008; large-tick tier Sharpe 1.0-1.2 post-break for the fast signal | Kurth, Eisler, Rej, Bouchaud (2026), 'Is Trend Still Your Friend? A Microstructural Account of the Demise of Short-Term Trend-Following', arXiv:2607.01550 — https://arxiv.org/abs/2607.01550 (full text read) | yes · quantified practitioner test (academic working paper) | «medido» | 8 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: XAUUSD M15 long `fast_d5_20_run` -8.1× · p corr. 1.00 (cruda 0.856) · 8/año — falla: no significativa, no paga 2×, inestable, pocas operaciones |
| `TR-08a-fitschen-h1-commodities-10bars` | `tendencia` | both in the source — $30.05 per trade versus $21.26 baseline (+40%); negative in 2003-2005; gross | Fitschen, 'Building Reliable Trading Systems' (2013), ch. 3 'Find the Path of Least Resistance', pp. 31-44 (PDF pp. 38-51) — ~/Desktop/Books (text read) — Table 3.9 | yes · quantified practitioner test | «medido» | 8 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: XAUUSD H4 long `fitschen_b10_1d` 1.9× · p corr. 0.80 (cruda 0.116) · 124/año — falla: no significativa, no paga 2× |
| `TR-08b-fitschen-h1-commodities-10days` | `tendencia` | both in the source — $30.05 per trade versus $21.26 baseline (+40%); negative in 2003-2005; gross | Fitschen, 'Building Reliable Trading Systems' (2013), ch. 3 'Find the Path of Least Resistance', pp. 31-44 (PDF pp. 38-51) — ~/Desktop/Books (text read) — Table 3.9 | yes · quantified practitioner test | «medido» | 8 celdas con contraste: 0 con p cruda ≤ 0,05, 0 significativas tras corregir, 0 pasan los cuatro. Mejor: XAUUSD M30 short `fitschen_d10_1d` 1.7× · p corr. 0.59 (cruda 0.057) · 89/año — falla: no significativa, no paga 2× |
| `MOM-26-metals-late-session-half-hours` | `momentum` | both — GLD: β = 0.0436, t = 3.03, R² = 0.49% (2004-2019); SLV: β = 0.1260, t = 3.03, R² = 1.72% (2006-2020) | Xu, Bouri, Saeed, Wen (2020), 'Intraday return predictability: Evidence from commodity ETFs and their related volatility indices', Resources Policy — https://pmc.ncbi.nlm.nih.gov/articles/PMC7480318/ (page read through the fetch summariser) | **⚠️ via summariser** · peer-reviewed | «descartado por usar reloj» | — |
| `SES-30-gold-overnight` | `sesion` | long — GLD: +0.04% average per overnight trade, ≈11.4%/yr, intraday 'essentially flat'; period not stated on the page. Blose et al. report COMEX overnight significantly positive and day significantly negative for 1985-2012 (search summary only) | QuantifiedStrategies, 'A Quantitative Look at the Gold Overnight Strategy' — https://quantifiedstrategies.substack.com/p/a-quantitative-look-at-the-gold-overnight (page read). The academic source, Blose, Gondhalekar & Kort (2018) J. Economics and Finance 42, was NOT opened (paywall): not verified | **⚠️ blog page yes; academic paper NOT verified** · quantified practitioner test | «descartado por usar reloj» | — |
| `GOLD-51-real-yields-and-dollar` | `tendencia` | long gold when the dollar and real yields fall; short on the mirror — regression on 13-week changes, Mar 2014 - Jun 2018 (231 obs): R² 0.65; +100 bp in the TIPS yield ≈ -$173/oz; +1 point of the dollar index ≈ -$10/oz; correlation gold-dollar -0.75, gold-TIPS -0.40 (2018). 'In late 2017 gold and the TIPS yield appear to have parted ways'; a search summary reports the correlation collapsing to ≈0 in 2022-2026 (not verified) | Murenbeeld, 'An Update on Gold, Real Interest Rates and the Dollar', LBMA Alchemist issue 90 (2018) — https://www.lbma.org.uk/alchemist/issue-90/an-update-on-gold-real-interest-rates-and-the-dollar (page read) | **⚠️ page read** · quantified practitioner test | «la bibliografía lo afirma y aquí no se mide» | necesita otro activo (EURUSD como proxy del dólar): el perfil mide cada activo solo |


## 9. Activos de la prior que no están en `assets/`

La prior cubre cinco activos que no tenemos y los señala como **los mejores mercados de reversión**:
`UK100` (reversión Alta, lo demás Baja o Media), `EURGBP`, `AUDNZD` y `EURCHF` (reversión Alta, el
resto Baja; M15 «evitar por coste»; EURCHF con riesgo de cola por el suelo del SNB de 2015) y
`NZDUSD` (misma fila que AUDUSD y USDCAD). Dado que aquí la reversión es la única estructura que
aparece en todas partes y lo que la mata es el coste frente al rango, son los candidatos naturales
si se añaden activos (`/asset-onboard`): no hay ninguna medida de ellos.

Activos nuestros que la prior no cubre: `USDCHF`, `UKOIL`, `USOIL` (ordenados sólo con lo medido y
la bibliografía) y `CADJPY` (tratado como cruce del yen).
