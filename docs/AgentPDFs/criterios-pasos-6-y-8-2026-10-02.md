# Criterios de búsqueda y descarte — pasos 6 y 8 del workflow

**2026-10-02 · propuesta de agente, PROVISIONAL hasta que la apruebes.** Qué estrategia entra en el
databank mientras SQX construye (paso 6) y cuál sigue adelante después del retest fuera de muestra
(paso 8), con tres veredictos: **Pass**, **Limbo** y **Fallo**.

Los criterios ya están escritos donde se aplican: `assets/_study.yaml` (paso 6) y
`pipeline/autopilot/criteria.yaml` (paso 8). Nada está en commit.

---

## 1. Lo que hay que decidir

| # | decisión | mi recomendación | lo que cuesta la alternativa |
|---|---|---|---|
| 1 | **Suelo de operaciones al año.** Tú quieres 40-50. | Dejarlo como está escrito: menos de 20/año es Fallo, de 20 a 40 es **Limbo**, 40 o más puede ser Pass. Tu suelo es la línea de Pass, no un descarte. | Si 40 pasa a ser descarte duro, siguen adelante un 50-63 % menos de estrategias (§4.2), y la potencia para probarse sube del 37 % al 53 %. |
| 2 | **Apagar el modo desarrollo del autopilot** (`dev.on` en `criteria.yaml`). Hoy sortea 5 estrategias entre las que pasan. | Apagarlo cuando apruebes estos criterios. | Mientras siga encendido, las reglas se aplican pero sólo siguen 5 al azar. |
| 3 | **Dar de alta en SQX las sesiones** `<ACTIVO>_ftmo` de los 15 activos que no son XAUUSD ni USDJPY, y decidir la de la plata. | Es lo que más desbloquea: sin ellas no se puede construir nada en esos activos. | Sus criterios son hoy extrapolados, no medidos. |
| 4 | **Riesgo por operación en fondeo.** | 0,5 % de cuenta por R. | Al 1 %, el 27 % de las supervivientes rompe el límite diario del 5 % o el total del 10 % dentro de oos1 (§5.4). |

---

## 2. Qué se ha medido

- **28 poblaciones sin seleccionar, 118.235 estrategias**, construidas esta noche en el custodio con
  filtros mínimos (≥ 100 operaciones y beneficio > 0 en el IS), retesteadas en `oos1` y pasadas por
  el paso 8. USDJPY y XAUUSD; M30, H1 y H4; largo y corto; generación genética y aleatoria; dos
  familias (la estrategia libre con hasta dos condiciones y paleta amplia de 842 bloques, y la
  plantilla Donchian); con y sin la salida del viernes.
- **11,9 millones de estrategias nulas** (entrada al azar con tu doctrina y los costes de cada
  activo) en 17 activos, largo y corto, de 20 a 200 operaciones al año. Miden cuánto azar deja pasar
  cada regla. Cada una tiene una gemela sin costes: la estrategia que ni gana ni pierde.
- **Una prueba A/B de 12 builds:** el mismo filtro puesto dentro del build frente a aplicado después.
- **Un crítico independiente** que recalculó la propuesta y la corrigió en cuatro puntos.

**Lo que no se ha podido medir:** los otros 15 activos. Su sesión `<ACTIVO>_ftmo` no existe en ningún
proyecto de ninguna instalación y el builder se niega a inventar horarios. Para ellos los números son
extrapolados de sus nulas, sus ventanas y sus costes, y van marcados como provisionales.

---

## 3. Las cinco conclusiones que mandan

1. **Sólo hay edge medible en una celda: USDJPY en largo.** Ahí siguen adelante entre 5 y 13 veces
   más estrategias que con entrada al azar. En todo lo demás (oro en los dos lados, USDJPY en corto)
   pasan las mismas que pasarían por azar: 138 reales frente a 136 nulas.
2. **Ninguna estrategia es significativa por sí sola después de la búsqueda.** La t más alta de las
   118.235 es 3,57, y tras cientos de intentos independientes haría falta 3,7. El paso 8 no
   certifica: **enriquece**. La prueba la dan los pasos siguientes (otros mercados, otros
   timeframes, `oos2`).
3. **Manda la ventana, no la estrategia.** En USDJPY en largo el 93 % gana en `oos1`; en oro en
   largo, el 13 %. «Ganó fuera de muestra» no significa nada si no se descuenta lo que habría ganado
   el propio mercado. Por eso la prueba central descuenta la deriva.
4. **Un filtro puesto dentro del build pierde estrategias buenas.** El genético deja de criar lo
   que funcionaba. El mismo corte aplicado después cuesta menos (§4.1).
5. **El riesgo flotante es un eje aparte.** La significancia no dice nada de cuánto se hunde una
   estrategia en un día (correlación 0,06). Para el fondeo hace falta su propia regla.

---

## 4. Paso 6 — filtros del Build en SQX

### 4.1 Lo que queda escrito

Todas las condiciones se leen sobre el **IS** (sólo la ventana de construcción). Un filtro del build
nunca puede leer el OOS: lo gastaría y el paso 8 dejaría de servir.

| condición en «Ranking» del Build | valor | por qué |
|---|---|---|
| Número de operaciones, mínimo | 10 por año × años del build (≈ 100 en total) | sólo para que haya estadística que leer |
| Número de operaciones, máximo | 150/año en H1, 200 en M30, 100 en H4 | el doble del techo del paso 8; casi nunca muerde |
| Profit factor | ≥ 1,0 | sólo no perder |
| Beneficio neto | > 0 | idem |
| Sortino > 0,6 y Stagnation < 540 (heredados del donante) | **quitados** | nadie los había decidido, y con «más de 500 operaciones» dejaban 140 de 56.121 estrategias y ninguna de las buenas |

**Por qué tan poco.** La prueba A/B (un build de 6 minutos por variante, las mismas en tres
poblaciones; «buena» = pasa la prueba central del paso 8):

| población | sin filtro (a) | 30-75 ops/año y PF ≥ 1,20 (b) | 40-75 y PF ≥ 1,20 (c) | 50-100 y PF ≥ 1,15 (d) | el filtro (b) aplicado después a (a) |
|---|---|---|---|---|---|
| USDJPY H1 libre largo | 273 de 5.734 (4,8 %) | 9 de 444 (2,0 %) | 0 de 239 | 0 de 659 | 31 de 794 (3,9 %) |
| USDJPY H1 Donchian largo | 1.399 de 10.254 (13,6 %) | 410 de 4.619 (8,9 %) | 22 de 380 (5,8 %) | 27 de 505 (5,3 %) | 114 de 1.368 (8,3 %) |
| XAUUSD H1 libre corto | 34 de 7.028 (0,5 %) | 1 de 1.412 | 0 de 862 | 1 de 563 | 9 de 1.398 (0,6 %) |

Buenas por minuto de build, de (a) a (b): 45 → 1,5, 857 → 68 y 5,6 → 0,17. Cuanto más alto el
suelo dentro del build, peor. La variante (d) además da el mayor riesgo flotante (drawdown mediano
de 35R frente a 12R).

*Salvedad: es un build por variante, y el genético varía mucho de una corrida a otra. La lectura se
apoya en que el signo es el mismo en las tres poblaciones.*

### 4.2 El suelo de operaciones al año

Cortando después del build, sobre USDJPY H1 en largo:

| suelo en el IS (ops/año) | siguen adelante por cada 1.000 | frente al suelo de 20 | potencia para llegar a Pass* |
|---|---|---|---|
| 20 | 31,7 | — | 37 % |
| 25 | 20,8 | −34 % | 40 % |
| 30 | 17,6 | −44 % | 44 % |
| 40 | 11,8 | −63 % | 53 % |
| 50 | 8,6 | −73 % | 60 % |

\* Probabilidad de que una estrategia con edge real (Sharpe neto por operación de 0,15) alcance la
línea de Pass en 5 años de `oos1`, promediada sobre las estrategias que quedan por encima de ese
suelo (operan a frecuencias distintas).

Las dos cosas son ciertas a la vez:

- **A favor de tu suelo:** con pocas operaciones nadie puede probar nada. Una estrategia buena que
  opera exactamente 20 veces al año llega a Pass el 18 % de las veces; una que opera 50, el 50 %.
- **En contra:** el suelo alto no discrimina mejor (la proporción entre donde hay edge y donde no es
  6,5 con suelo 20 y 6,6 con suelo 40) y el riesgo flotante crece con la frecuencia: la regla de
  fondeo tumba al 13-17 % de las significativas por debajo de 25/año y al 35-38 % entre 25 y 40.

**Cómo queda resuelto:** tu suelo de 40 es la línea de **Pass**, y de 20 a 40 es **Limbo**. Una
estrategia de 28 operaciones al año no se descarta: sigue marcada como «no ha podido probarse» y la
juzgan los pasos siguientes.

### 4.3 Lo que no se filtra, y por qué

| candidato | veredicto |
|---|---|
| Ret/DD, Sharpe, Sortino, Stagnation, % de aciertos como filtro | No. O cuestan demasiadas buenas o no se sostienen de una población a otra. |
| Tope de profit factor («demasiado bueno = sobreajuste») | No. El decil más alto de PF en el IS es el mejor en `oos1`. |
| Suelo de PF por activo sacado del azar | No como filtro. El PF de suerte depende de las operaciones, no del activo (§6.1). |
| Máximo de 3 condiciones | No aporta (×1,02). |
| Objetivo del genético | Se queda en Ret/DD del IS. PF y SQN predicen algo mejor (+0,04 a +0,07 de correlación); beneficio neto es el que hay que evitar. |
| Genética o aleatoria | Genética: da de 3 a 18 veces más buenas por minuto, aunque sólo porque acepta más. Por estrategia aceptada no es mejor salvo en USDJPY largo (×3). |

### 4.4 Por activo

Suelo y techo totales de operaciones que el builder escribe en SQX (suelo de 10/año, mínimo ~100):

| activos | años de build | M30 | H1 | H4 | estado |
|---|---|---|---|---|---|
| USDJPY, XAUUSD | 10 | 100-2.000 | 100-1.500 | 100-1.000 | **medido** |
| EURUSD, GBPUSD, AUDUSD, USDCAD, USDCHF, EURJPY, GBPJPY, AUDJPY, CADJPY, XAGUSD | 10 | 100-2.000 | 100-1.500 | 100-1.000 | provisional (sin sesión en SQX) |
| NIKKEI225 | 8,28 | 108-1.655 | 108-1.242 | 108-827 | provisional |
| USA500, USATEC | 7,95 | 104-1.590 | 104-1.192 | 104-795 | provisional |
| UKOIL, USOIL | 7 | 105-1.400 | 105-1.050 | 105-700 | provisional |
| DAX40, DJ30 | 6,25 | 100-1.250 | 100-937 | 100-625 | provisional |

---

## 5. Paso 8 — Pass, Limbo y Fallo

**Cómo se lee.** Cada regla mira un dato de la estrategia y da Pass, Limbo o Fallo. El veredicto de
la estrategia es **el peor** de sus reglas. Un dato que falta cuenta como Limbo.

- **Pass:** probada con los datos que hay.
- **Limbo:** no ha podido probarse todavía. Sigue adelante, marcada.
- **Fallo:** azar casi seguro, o un riesgo que una cuenta de fondeo no aguanta.

### 5.1 Las reglas

| # | qué mira | Pass | Limbo | Fallo |
|---|---|---|---|---|
| R1 | Está en el databank OOS, y su lista de operaciones no es escasa ni un clon de otra | sí | — | no |
| R2 | Beneficio neto en `oos1` | > 0 | — | ≤ 0 |
| **R3** | **t de la operación descontando la deriva del mercado** | ≥ 2,33 (H4: 2,5) | ≥ 1,65 (H4: 1,9) | menos |
| R4 | Operaciones por año en el IS, suelo | ≥ 40 | ≥ 20 | < 20 |
| R4 | Operaciones por año en el IS, techo | ≤ 75 (M30: 100 · H4: 50) | ≤ 100 (M30: 130 · H4: 65) | más |
| R5 | Operaciones por año en `oos1` | ≥ 15 | ≥ 10 | < 10 |
| R6 | Drawdown máximo de `oos1` dividido entre el del IS | ≤ 1,25 | ≤ 2,0 | más |
| R7 | Años naturales de `oos1` con beneficio | ≥ 3 | ≥ 2 | menos |
| R8 | Mejor trimestre dividido entre el neto total de `oos1` | ≤ 0,5 | ≤ 0,8 | más |
| R9 | Peor día, con el flotante, en R | ≥ −3R | ≥ −5R | peor |
| R9 | Peor pérdida flotante de una operación, en R | ≥ −3R | ≥ −5R | peor |
| R9 | Drawdown máximo dividido entre el neto anual | ≤ 1,5 | ≤ 2,5 | más |

**R = el riesgo por operación del sizing** (1.000 USD en la doctrina actual).

### 5.2 La prueba central (R3)

Para cada operación de `oos1` se resta lo que habría ganado el mercado por sí solo mientras estuvo
abierta, al mismo tamaño. Sobre lo que queda se calcula la t: la media dividida entre su error. Una
t de 2 quiere decir que la media está a dos errores estándar de cero.

Cuánto azar deja pasar, medido en las nulas (H1):

| contra qué | t ≥ 1,65 | t ≥ 2,33 |
|---|---|---|
| Una estrategia sin edge y sin costes, celda mediana | 3,9 % | 0,6 % |
| Idem, peor celda de los 17 activos y los dos lados | 5,8 % | 1,1 % |
| Entrada al azar pagando costes, tras el filtro del build | 0,85 % | 0,11 % |

- **Una sola línea vale para todos los activos y los dos lados.** Descontar la deriva quita casi
  todo el efecto del lado favorecido: sin descontarla, los dos lados de un activo diferían hasta 10
  veces (USATEC 12,9 % en largo y 1,2 % en corto); descontándola, 2,3 veces como mucho.
- **M30** se comporta como H1. **H4** es más ruidoso (peor celda 8,9 % y 1,7 %): por eso su línea
  es 1,9 y 2,5.

### 5.3 Qué aporta cada regla

- **R3 es casi todo.** Una vez exigida la t, el beneficio, el PF al spread real, el Sharpe del
  snooping y la p del mono se cumplen solos entre el 99,8 y el 100 % de las veces.
- **R1 y R2** son las que convierten en Fallo a lo que muere pronto en la puerta. Sin ellas, 21.666
  perdedoras quedarían en Limbo por falta de datos.
- **R6, R7 y R9** miran cosas que la t no ve.
- **R8 nunca decide sola.** Se queda como red de seguridad.

### 5.4 Riesgo flotante (R9)

Medido sobre 1.405 supervivientes reales (t ≥ 1,65), el 91 % de USDJPY en largo:

| | mediana |
|---|---|
| Drawdown máximo | 4,9R |
| Peor día | −2,3R |
| Peor pérdida flotante de una operación | −2,6R |
| Neto anual | 3,6R |

- **Coste de la regla:** de las supervivientes, el 37 % queda en Pass, el 41 % en Limbo y el 21 % en
  Fallo. Entre las de t ≥ 2,33, el 64 % en Pass y el 10 % en Fallo.
- **Tamaño.** Al 1 % de cuenta por R, el 15 % rompe el límite diario del 5 %, el 15 % un drawdown
  del 10 % y el 41 % un trailing del 6 %, todo dentro de `oos1`. Al 0,5 %, ninguna rompe el 5 % ni
  el 10 %, y el 7,5 % rompe el trailing del 6 %.
- **Limitación.** El peor día sale de la curva diaria de SQX, que guarda el mínimo de cada día. Es
  una aproximación a la regla de pérdida diaria de la empresa, no la regla exacta. La comprobación
  exacta es el paso 26.

### 5.5 Lo que no lleva regla

| estudio | por qué |
|---|---|
| p del mono | Toma la semilla del sistema: tres corridas dan tres p distintas. Además repite lo que dice la t. |
| Edge por coste | No elimina a nadie por sí sola, y mezcla IS y OOS. |
| PF al spread real, snooping | Repiten lo que dice la t (correlación 0,99). |
| Calidad del feed, forma del beneficio, calidad de la entrada | Fuera de este criterio por decisión tuya (2026-10-01). |

Todos siguen corriendo y mostrándose en la ventana. Sólo dejan de decidir.

### 5.6 El embudo

Las reglas tal como quedan escritas, sobre las 28 poblaciones:

| | estrategias | Pass | Limbo | siguen por cada 1.000 |
|---|---|---|---|---|
| USDJPY H1 largo, genética | 17.611 | 3 | 380 | 21,7 |
| Todo lo demás | 100.624 | 1 | 176 | 1,8 |
| **Total** | **118.235** | **4** | **556** | 4,7 |

Fuera de USDJPY en largo sigue adelante el 0,18 %: lo que daría el azar. Es el resultado correcto
donde no hay edge.

**Pass es raro a propósito.** Exige a la vez 40 operaciones al año y t ≥ 2,33. La mayor parte de lo
que sigue va en Limbo, y eso es honesto: nadie ha podido probarse todavía con un solo tramo.

---

## 6. Profit factor y Kaufman

### 6.1 Profit factor

Es útil como **suelo**, y poco más.

- **Como suelo:** un PF bajo no sobrevive a los costes. En la estrategia libre, pedir PF ≥ 1,10 en
  el IS sube la proporción de buenas a ×1,24. En la plantilla Donchian no hace nada.
- **Como selector, no:** todos los deciles de PF del IS tienen una mediana de PF en `oos1` por
  debajo de 1 (de 0,87 a 0,93).
- **El PF que da la suerte depende de las operaciones.** Una estrategia sin edge alcanza por azar,
  una de cada veinte veces:

| operaciones al año | build de 6,25 años | 8 años | 10 años |
|---|---|---|---|
| 20 | 1,48 | 1,41 | 1,36 |
| 30 | 1,37 | 1,33 | 1,29 |
| 50 | 1,28 | 1,24 | 1,21 |
| 75 | 1,22 | 1,19 | 1,17 |

Un PF de 1,3 con 20 operaciones al año es lo que da la suerte. Con 75, ya no. Por eso los índices,
con builds más cortos, necesitan más PF para decir lo mismo.

### 6.2 Efficiency ratio de Kaufman

Medidas las dos lecturas que pediste:

- **Sobre la curva de equity.** Por operación es exactamente (PF − 1) / (PF + 1): es el PF con otro
  nombre. Por día correlaciona 0,98 con el PF, y no es una columna de SQX. No añade nada.
- **Sobre el mercado al entrar.** No persiste: el tercil que mejor rinde en el IS es el mejor en
  `oos1` en 8 de 20 poblaciones, menos que al azar entre tres. Operar sólo en el mejor tercil del
  IS empeora al 77 % de las estrategias.

---

## 7. Lo que es firme y lo que es provisional

| | estado |
|---|---|
| La línea de la t (R3) en H1 y M30, todos los activos | **firme**: medida en 11,9 M de nulas |
| Quitar los filtros del donante y no filtrar dentro del build | **firme**: mismo signo en tres poblaciones |
| USDJPY y XAUUSD, H1 | medido |
| M30 | sin calibrar del todo: sólo 26 buenas en 5.947 |
| H4 | la línea de 2,5 es dudosa: da 3 Pass en la aleatoria y 1 en la genética |
| Los otros 15 activos | **provisional**: extrapolado, sin ninguna población |
| R6 y R7 en índices (su `oos1` tiene 4 años, no 5) | sin probar |
| Las curvas del paso 6 | descansan en un activo, una dirección y una ventana |

**Tres advertencias:**

1. **El `oos1` de USDJPY y XAUUSD queda gastado** en esta calibración. Los umbrales se eligieron
   después de leerlo, así que hay que congelarlos antes del siguiente build. `oos2` no se ha tocado.
2. **El 99 % de las que pasan rindió mejor fuera que dentro de muestra** (retención mediana 2,49).
   Una que pasa es una ganadora de la ventana hasta que los pasos siguientes digan otra cosa.
3. **El build real de un proyecto `Trade_` llena el databank** (10.000 en unos minutos) y durante
   el resto de los 180 minutos sustituye por Ret/DD del IS. Eso es una selección que no se ha
   medido. Ver §8.

---

## 8. Siguientes pruebas

| prueba | qué contesta | coste |
|---|---|---|
| Build de 180 minutos con el databank lleno frente a uno de 6 minutos | si las 3 horas de selección por Ret/DD dan más buenas o sólo queman CPU | 3 h de custodio |
| Los 15 activos, en cuanto existan sus sesiones | sus criterios medidos, no extrapolados | 10 min por población; la cola ya está hecha |
| El A/B del suelo repetido 3 veces | si el coste del suelo dentro del build es estable | 2 h |
| Exponer el PF del IS como dato del paso 8 | poder poner PF ≥ 1,10 como regla | pequeño cambio de código |
| Comparar contra una gemela de generación aleatoria | saber si una población está enriquecida o es azar | ya construido |

---

## 9. Lo que ha cambiado en el código

- **`assets/_study.yaml`** (nuevo) y su escritor: el builder ya escribe los filtros del Build en
  cada proyecto nuevo. Antes se heredaban del donante.
- **`pipeline/autopilot/criteria.yaml`**: las 13 reglas del paso 8. Una regla puede variar por
  timeframe, símbolo o clase de activo (`by:`).
- **La t de la puerta estaba mal.** Metía el Sharpe anualizado donde va el diario: comprimía la t y
  le ponía un techo. Corregida, con test.
- **Datos nuevos en la puerta:** la t descontando la deriva, las operaciones por año y el riesgo
  flotante en R.
- **Todo dato del paso 8 llega al autopilot.** Antes las reglas sobre la puerta salían siempre en
  Limbo por un fallo de identidad.
- **La revisión tras SQX pasó de 15 a 5 minutos** sobre 5.000 estrategias, con resultados
  idénticos.
- **Fallo de unidades del swap** documentado: en pares de JPY un modelo que use `tick_size` cobra
  el swap 10 veces de más.

**Dónde está la evidencia:** `AlgoData/scratch/` — `calib_out/` (un informe por población),
`null2/` (las nulas), `calib_redteam/review.md` (el crítico), `calib_final/` (la validación y el
A/B) y `calib_queue/` (la cola desatendida, con su `HANDOFF.md`).
