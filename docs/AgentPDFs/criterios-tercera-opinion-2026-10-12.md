# Tercera opinión sobre el proceso de validación — un estadístico de fondo audita la cadena (2026-10-12)

**Para:** el dueño. **De:** un auditor externo que no ha leído las dos opiniones anteriores. **Material:**
`criterios-implementados-2026-10-12.md` (en adelante `dossier:N` = línea N de ese fichero), `pipeline/autopilot/criteria.yaml`,
`engines/inference/snooping/superior.py`, `studies/screening/falsePositives/README.md`, `engines/README.md`, el motor
de nulos (`engines/nulls/`, `studies/readings/monkey/`) y las operaciones cosechadas del paso 7 de **27 poblaciones**
(`AlgoData/reports/<P>/Results/<día>/gate/operaciones.parquet`). Nada se ha ejecutado en SQX; lo que mido yo está en
`AlgoData/reports/tercera-opinion-2026-10-12/` (`eb.py`, `cell.py`, `cells.py`, `cells.csv`), reproducible con Python y nada más.

**Encargo del dueño además del guion:** la aleatoriedad entera — qué se aleatoriza, con qué distribución, qué métrica
se mira, dónde, y qué cabe esperar. Es la sección 2 y es la más larga a propósito.

**La respuesta en una línea:** apostaría **0,30** (intervalo honesto 0,20–0,45) a que una superviviente de hoy tiene
ventaja neta positiva en los tres años siguientes; **ningún paso de la cadena da ese número hoy**: sale de un control que
la cadena ya tiene (`falsePositives`, paso 8) y de dos medidas que la cadena no hace y yo he hecho sobre sus propios
datos — el número efectivo de estrategias independientes de una población (≈ 2–4, no 10.000) y la fiabilidad
mitad-mitad de la t dentro de oos1 (negativa en 26 de 27 poblaciones). Cómo se calcula: sección 4.

---

## 1. Lo roto antes de cualquier umbral

Estas cinco cosas invalidan la lectura de todos los umbrales que vienen después. Van primero porque arreglar un umbral
encima de ellas es afinar la mira de un rifle torcido.

### 1.1 Una población de 10.000 son dos o tres apuestas — y todo el proceso cuenta como si fueran 10.000

Medido sobre el panel semanal de exceso neto (cada estrategia dividida por la desviación de sus propias operaciones)
de las 27 poblaciones cosechadas (`cells.py`, columna `n_eff`):

| población | N con t | corr. media entre pares (semanal) | N efectivo |
|---|---|---|---|
| USATEC H1 ruptura (`leaseWeb`) | 7.822 | 0,471 | **2,1** |
| USA500 H1 tendencia wf1 | 6.097 | 0,565 | 1,8 |
| NIKKEI225 H1 aroon cal6 | 4.963 | 0,591 | 1,7 |
| NIKKEI225 M30 volatilidad wf3 | 6.117 | 0,322 | 3,1 |
| DAX40 H1 reversión wf2 | 2.822 | 0,248 | 4,0 |
| GBPUSD H1 tendencia cal4 | 926 | 0,105 | 9,5 (el máximo de las 27) |
| XAUUSD H1 ruptura wf4 | 3.458 | 0,516 | 1,9 |
| mediana de las 27 | — | 0,33 | **3,0** |

El dossier ya lo insinuaba por otra vía (`dossier:272`: correlación semanal mediana 0,73 ≈ 2 independientes entre las
guardadas; `dossier:590`: +0,22 medio entre dos de las 10.000 de B5). Consecuencia: **la hipótesis que se contrasta en el
paso 8 no es «esta estrategia tiene ventaja» sino «esta plantilla en este mercado y marco tiene ventaja», y se contrasta
10.000 veces con el mismo dato**. Un umbral por estrategia a t ≥ 1,65 (`criteria.yaml:33`) sobre 2 apuestas independientes
no tiene tasa de error definida en el sentido en que lo dice el spec (`dossier:757-761`: «3,9 % a 5,8 % de nulas»).

### 1.2 El orden por t dentro de oos1 no persiste: el paso 8 selecciona carga de régimen, no ventaja

Partí oos1 por la mediana de fechas de cierre y calculé la t del exceso de cada estrategia en cada mitad (`cells.py`,
`rho_mitades`, `top_h2`, `resto_h2`):

| población | ρ Spearman t(1.ª mitad) vs t(2.ª mitad) | t media en la 2.ª mitad del 1,7 % mejor de la 1.ª | t media del resto |
|---|---|---|---|
| USATEC H1 ruptura | −0,058 | 0,25 | 0,52 |
| DAX40 H1 reversión wf2 | −0,737 | −0,70 | 0,57 |
| NIKKEI225 H1 aroon mc1b | −0,674 | −0,66 | 0,64 |
| USA500 H1 tendencia wf1 | −0,510 | −0,09 | 0,19 |
| USDJPY M30 doubleROC B5 | −0,523 | 0,12 | 0,84 |
| NIKKEI225 H1 aroon cal6 | **+0,180** (la única positiva) | 1,04 | 0,56 |

En 26 de 27 poblaciones la correlación es negativa, entre −0,06 y −0,75, y en 24 de 27 las mejores por t en la primera
mitad hacen **peor** que el resto en la segunda. Esto no es ruido puro (ruido daría ρ ≈ 0): es la firma de un factor común
cuyo signo cambia entre mitades — las estrategias que más cargan el régimen suben juntas y bajan juntas. Es la misma
señal que el dossier ve de otra forma en B5: ρ = +0,39 entre Ret/DD del build y t de oos1 (`dossier:672`) mientras que en
USATEC la correlación de Spearman entre `is_trades_per_year` y `drift_excess_t` es **−0,455** y entre `is_net_per_year_r` y
`drift_excess_t` es **−0,267** (`eb.py`): cuanto mejor en build, peor en oos1.

**Conclusión operativa:** R3 a 1,65 no ordena estrategias por ventaja; ordena por suerte y por carga de régimen. Las 173
«supervivientes» de USATEC son las 173 réplicas más afortunadas de la misma apuesta. Lo que sí vale de R3 es su signo
(quitar lo que pierde), no su rango.

### 1.3 La nula del paso 8 está centrada en −0,52, y el control mide un umbral que no es el que el spec cree

Distribución de `drift_excess_t` en USATEC (`eb.py`, 5.000 monos sin ventaja, cascada apagada; 10.000 reales):

| población | media | sd | P(t ≥ 1,65) | P(t ≥ 2,33) |
|---|---|---|---|---|
| nula (monos) | **−0,525** | 0,933 | 1,00 % | 0,16 % |
| real (10.000) | +0,169 | 0,741 | 1,73 % | 0,07 % |
| plantada 0,05 | +0,888 | 0,914 | 20,0 % | 5,6 % |
| plantada 0,10 | +1,751 | 0,931 | 53,9 % | 26,7 % |
| plantada 0,15 | +2,579 | 0,969 | 83,0 % | 59,3 % |

Tres lecturas: (a) el 1,65 está a **2,3 desviaciones** de la media de la nula, no a 1,65 — por eso pasa el 1 % y no el 5 %
(`dossier:761` lo mide, `dossier:757` lo explica como «sesgo residual 0,017», que es otra cosa: el residuo es de la t
analítica, el −0,52 es el coste pagado por el mono); (b) la real tiene **menos** dispersión que la nula (0,74 frente a
0,93) — imposible si fueran 10.000 apuestas con ruido propio; es lo que da una población de dos apuestas; (c) por encima
de 2,0 la real tiene **menos** masa que la nula (0,40 % frente a 0,50 %; a 2,33, 0,07 % frente a 0,16 %): toda la
diferencia real–nula está en la franja 1,65–2,0.

### 1.4 La ventaja plantada es 2,5 a 7,5 veces mayor que la ventaja que el generador produce

Sharpe neto por operación en oos1, mediana de la población (`cells.csv`, `sharpe_net_med`): USATEC 0,020, DAX40 wf2
0,018, USA500 wf1 0,020, USDJPY B5 0,042, XAUUSD wf4 **−0,017**, USATEC M15 doubleROC **−0,020**; mediana de las 27:
0,018. El coste por operación en unidades de desviación (`cost_sd`) va de 0,021 (USATEC H1) a 0,070 (XAUUSD): **el coste
es la mitad de la ventaja bruta** (USATEC: bruta 0,041, coste 0,021, neta 0,020). Las tres plantas (0,05/0,10/0,15,
`falsePositives/README.md:147-151`) miden la potencia contra ventajas que ninguna población real tiene (sólo NIKKEI cal6,
0,107, y ésa es el factor común de 1.2). Toda potencia citada («19 %, 50 %, 75 %», `dossier:863-867`) es potencia
contra un enemigo imaginario; contra 0,02 neto la potencia de R3 es **≈ 2,8 %** (t media −0,525 + 0,02·√385 = −0,13;
P(N(−0,13; 0,93) ≥ 1,65) = 2,8 %), es decir, un cociente de verosimilitud de **2,8** frente al 1,0 % de la nula.

Y como el coste es la mitad de lo bruto, un error del 50 % en el coste cambia el signo de la ventaja neta de la población
mediana. Hoy hay tres cifras para el mismo spread (`dossier:354`: 304 / 607 / 747 puntos en NIKKEI build), el swap de hoy
se aplica a toda la historia (`dossier:374-375`: NIKKEI largo, una noche = 45 % de una ida y vuelta), la comisión forex
tiene dos valores (5 y 8 USD, `dossier:360`) y el P/L reprecificado no reproduce el de SQX en 8 de 12 lotes del 17
(`dossier:2154`, descuadre 0,925–1,0). Hasta que el coste esté a ±10 %, ningún umbral neto es interpretable.

### 1.5 Los tramos están gastados y la puerta que los protege no cierra

- oos1 lo lee el paso 8 (R2, R3, R5c, mono), el 10 (P4 en V2 y `e_principal`, `dossier:1014`; costes), el 11/11.5/12 (`criteria.yaml:140,145`), el 14
  (T1 oos1, `dossier:1311`), el 15/16 (SPP OOS, `dossier:1364`: «SPP OOS deja de ser OOS») y el 17 como pierna «dentro» de c1
  (`dossier:1737`). En `USDJPY_M30_doubleROCLong` oos1 se cribó **cuatro veces** con cuatro `config_hash` (`dossier:273`).
- oos2 lo leen 17, 18, 18.5, 19 y 20 con las mismas 143–195 semanas (`dossier:2188`), y el 20 hereda veredictos ya condicionados
  a oos2 (`dossier:2303`). Esa misma celda tiene ya **94 filas de ledger sobre oos2** (`dossier:273`).
- La reserva de oos2 sólo ata a `ALGO_AUTONOMOUS=1`, que nadie pone (`dossier:333, 508, 2277`).
- Las poblaciones con las que se calibra desde el 2026-10-10 pasan por `dev.on: true, sample: 3` (`criteria.yaml:1-5`,
  `dossier:882`): las cifras de los pasos 9–20 son de 1 a 25 estrategias por corrida (`dossier:898`). No hay evidencia a escala.
- 15 de 27 feeds tienen `stable_from` posterior al inicio del build (`dossier:398`); en NIKKEI el IS «empieza tarde» (`dossier:650`).

---

## 2. La aleatoriedad, entera: qué se aleatoriza, con qué ley, qué se mira, dónde, y qué debería salir

Esto responde al encargo extra del dueño. Hay **siete familias** de aleatoriedad en la cadena; cada fila dice qué conserva la
nula, qué entrega al azar, su ley, sus sorteos, la métrica, el umbral, dónde se aplica y lo observado. Después, lo que opino
de cada una.

### 2.1 Inventario

| paso · pieza | qué conserva | qué entrega al azar y con qué ley | sorteos · semilla | métrica y umbral | ventana | observado |
|---|---|---|---|---|---|---|
| 1 · perfil (`series.py:123-151`) | nada de la regla | **barras remuestreadas con reposición, bloque = 1 barra** | 3.000 · entropía (593561232) | p empírica, BH 5 % sobre 16.188 pruebas; múltiplo ≥ 2× coste | build | 504 nombradas, 5 pagan 2× (`dossier:55,74`) |
| 6 · build | — | el genético de SQX: 20 islas × 250, 25 generaciones (`dossier:589`); **ninguna nula** | — | filtros IS: ≥35 ops/año, PF ≥ 1, neto > 0 | build | 5,8–6,6 % aceptadas (`dossier:580`) |
| 8 · R3 (`drift_term`, variante d) | lado, duración, tamaño | **nula analítica**: deriva media ponderada 1/ATR de `open[j+h]−open[j]` en la ventana-año; sin sorteo | — | t AR(1) del exceso ≥ 1,65 | oos1 | nula 1,0 %, real 1,7 % (`dossier:761`) |
| 8 · R7 (`homogeneity`) | las operaciones | **permutación** de operaciones entre trimestres | 5.000 · 3929614098 | Q, p > 0,05 → Pasa, si no Limbo | oos1 | 0 Falla; nula pasa 87 % (`dossier:806`) |
| 8 · R6 (`drawdown`) | media de oos1, n de oos1 | **bootstrap por bloques de 8** de las operaciones del build, recentradas | 5.000 · 2340908895 | `dd_p` > 0,10 Pasa, > 0,01 Limbo | build→oos1 | 0 Falla en 169; nula cae 0,3 % (`dossier:811`) |
| 8 · mono 3c (`windowed.py`) | n, lado, duración, **ventana-año** de cada operación | **entrada uniforme en las barras elegibles de su ventana-año**; tamaño `c/ATR` en la barra sorteada; reprecio con spread, slippage, swap y comisión | 5.000 · fresca (1851582449) | `z = (visto − media)/sd` de P/L medio por operación ≥ 1,65 → Pasa, si no Limbo; `mono_p` sólo anota | oos1 | real 65 Pasa / 104 Limbo / 0 Falla; nula z ~ N(−0,04; 0,99) (`eb.py`) |
| 8 · control (`falsePositives`) | la **huella** de la donante (n, duraciones, lados; en IS y en oos1) | peldaño `free`: entrada, duraciones (bootstrap) y tamaño medio; **50 monos por donante**; plus **planta** constante por operación = `s·sd + coste medio` | 5.000 por población · 3747935572 | las 17 reglas, cascada apagada | oos1 (IS sólo para hechos) | nula 0,98 %, real 1,69 %, plantadas 19/50/75 % (`dossier:863-867`) |
| 10 · P3–P9 (`shift.py`) | operaciones reales, dependencia entre mercados (un desplazamiento compartido) | **desplazamiento por semanas enteras dentro del año**; reprecio a open | 5.000 · 20261007 | `z_conj` ≥ 2,33 Pasa, < 0 Falla; P4, P5, P9 en z | build+oos1 (V0/V1/V2) | sintético sin ventaja: rechazo 7 % al 5 % nominal; `z<0` mata ≈ 50 % (`dossier:984-1020`) |
| 11.5 · T1–T4 (`tf/null.py`) | ídem | mismo desplazamiento semanal, sin cruzar build/oos1 | 5.000 · 20261007 | sin regla viva | oos1 | rechazo 3,0–5,7 % en sintético (`tests/test_crosstf_tf_null.py:30,98`) |
| 12 · `z_new` (escalera `timing`) | n, lado, duración, tamaño | **entrada uniforme en todo el tramo** (no por ventana), sin spread ni slippage (`calibrate.charged`) | 100.000 por defecto, no verificado (`dossier:1197`) · fresca | Sharpe por operación; `z_new = (z_sis − ρ·z_madre)/√(1−ρ²)`, combinada ≥ 2,33, nunca Falla | oos1 | FP 2,7–6,3 % calibrado con 68 nulas; datos borrados (`dossier:1171,1192`) |
| 13 · MCR (SQX) | la estrategia | **barra inicial** (±500), **OHLC** ±15 % con prob. 30 % | 200 / 500 | ninguna; alimenta 14 | build | T3 = 1,000 en 58/58 (`dossier:1324`) |
| 14 · T1 vecinas (`neighbours.py`) | la madre | **hipercubo uniforme independiente**: `x·(1+u)`, u ~ U(±15 %) entrada, U(±30 %) salida | 500 · [0, crc32(nombre)] | `ret_med` ≥ 0,6 y `f_pos` ≥ 0,9 Pasa; < 0,3 o < 0,7 Falla | build (y oos1 sólo signo) | 47/50 Falla en mc2, 9/9 en mc1b (`dossier:1304-1305`) |
| 16 · ruido (`noise.py`) | la rejilla SPP | **nula analítica** `σ·√(2 ln n_eff)` | — | sin umbral que corte | build, oos1 | n_eff 8.000–11.200; pass=0 en 6/6 sobre Sharpe (`dossier:1383`) |
| 16.5 · nube | la madre | **Latin Hypercube** (semilla 20260921), 1.000 + 4 controles; 300 Sobol piloto; **200 barajados** del exceso para «legible»; Sobol 2¹² sobre la cuadrática | — | R² ajustado > p95 de los barajados | build, oos1 | todas legibles: 0,21–0,79 vs 0,01–0,02 (`dossier:1683`) |
| 17 · WFC (`flip.py`) | panel semanas × variantes, pierna «dentro» fija | **volteo de signo por semana, el mismo para todas las variantes** | 2.000 · 0 | ρ Spearman dentro/fuera (bruto), `p_nivel` del top 20 % (neto) ≤ 0,05 | build+oos1 → oos2 | 0 PASA / 9 LIMBO / 3 NO PASA; sd nula de ρ 0,09–0,45 (`dossier:1801`) |
| 18 · CSCV (`measure/null.py`) | la estructura de bloques | **bootstrap estacionario** (bloque medio 4 semanas) de columnas **estandarizadas y centradas en la misma media**; 3 Sharpe plantados | 200 · 20260922 | `p_pérdida` ≥ 0,5 o PBO ≥ p95 nulo → NO PASA | build+oos1+oos2 | 10/10 PASA; C18-1 falla 14,7–29,3 % sin ventaja (`dossier:2024`) |
| 18.5 · superficies | ídem 17 | volteo semanal compartido por mercados | 2.000 · 0 | orden perverso (p− ≤ 0,05) → NO PASA; prima ≤ p5 → LIMBO | build+oos1 (oos2 sólo Limbo) | 13/13 neutro; ρ propia ≈ 0 (`dossier:2107,2125`) |
| 19 · WFM L1 | las 30 celdas | volteo semanal, un signo para las 30 | 2.000 · 0 | p− ≤ 0,05 → NO PASA; mediana ≤ 0 → LIMBO | oos2 | 0 NO PASA / 3 LIMBO de 10; 13 % de rechazo al 5 % con asimetría (`dossier:2188`) |
| 20 · benchmark + SPA/StepM | n, lado, lotes, duración M1 | **entrada uniforme en todo oos2** (`RUNGS["timing"]`); luego **bootstrap estacionario** de Hansen sobre K madres | 2.000 · **0 para todas las madres** (`benchmark.py:44-45`); SPA 1.000 · 0 | lectura `peor` decide; SPA/StepM FWER 0,05 sólo informan | oos2 | SPA nunca < 0,40; StepM 0 nombradas en 10 corridas (`dossier:2311-2318`) |
| 22, 23, 24 (borrados) | — | bootstrap percentil 9.999; subconjuntos 10.000; 100.000 cuentas | — | — | — | 41–78 % de ≥1 celda falsa; 15–20 % falso «aporta»; 11,55 % tocado (`dossier:2410-2475`) |

### 2.2 Lo que está bien hecho, y por qué conviene saberlo

- **El mono del paso 8 está bien calibrado como instrumento**: sobre 5.000 monos nulos, `z_mono` ~ N(−0,04; 0,99) (`eb.py`);
  el volteo semanal de 17–19 y el desplazamiento semanal de 10–11.5 dan tasas al 5 % nominal entre 3 % y 7 % en sintético.
  Las semillas se registran. El reprecio del mono de la puerta cobra los cuatro costes (`windowed.py:133-138`), cosa que la
  escalera del 12 **no** hace (`calibrate.charged`, sólo swap y comisión: `engines/nulls/README.md:113-115`).
- **El control negativo existe** (`falsePositives`): es lo mejor de la cadena. Lo que falta es que la planta sea realista (1.4)
  y que el control baje del paso 8 (hoy «del 10 en adelante los monos vivos son un techo, no una medida», `README.md:197`).
- **La deriva se resta** en todas partes (`drift_term`, ventana-año). Es la decisión correcta para índices alcistas, y es la
  razón por la que la nula sale en −0,52: la deriva se devuelve, el coste no.

### 2.3 Lo que está mal, con su cifra

1. **Tres pruebas que son la misma prueba.** En las 173 que pasan R3 de USATEC, Spearman(`drift_excess_t`, `t_exceso_k`) =
   **1,00**, con `t_sin_3_mejores` **0,90**, con `t_sin_mejor_trimestre` 0,89, con `z_mono` **0,68** (0,77 de Pearson en las
   10.000) y con `z_mono_timing_sizing` 0,79 (`eb.py`). R3, R5c-t, R8 y el mono son cuatro lecturas del mismo número.
   El dossier lo reconoce para el mono (`dossier:819`: «casi la misma hipótesis nula que R3»). Un Limbo del mono con
   mediana 1,575 y el umbral en el percentil 60 (`dossier:820`) no informa de nada que R3 no haya dicho.
2. **El mono es uniforme en horas y días; la estrategia no.** La escalera y el mono de la puerta sortean la barra de entrada
   uniforme sobre las barras del tramo o de la ventana-año (`model.py:32`, `windowed.py:107-114`); «restringir a las horas
   que opera la estrategia» es una decisión del dueño del 2026-09-25 **no implementada** (`engines/nulls/README.md:140-143`).
   Con un spread 9× la media a la hora 0 del servidor (`dossier:357`) y plantillas de ruptura que entran al abrir, el mono
   paga el coste medio en horas que la estrategia nunca pisa. En USATEC, los monos nulos ganan **más** R al año que las
   reales (2,86 frente a 2,05, `eb.py`) con el doble de dispersión: el mono compara otra cosa.
3. **El número de operaciones nunca se aleatoriza** y los solapes se permiten (`engines/nulls/README.md:124-127`). Para una
   plantilla cuyo filtro reduce operaciones, la nula hereda exactamente la selección de n; el `filter.py` que lo
   corregiría no está en la cadena.
4. **La planta es constante por operación** (`falsePositives/README.md:169`): una ventaja real no es constante; es rara,
   concentrada y correlada con la volatilidad. Un umbral de concentración (R8) calibrado con una planta uniforme está
   calibrado contra lo contrario de lo que busca. R8 deja en Limbo al 89 % de las reales (`dossier:784`) y al 88,6 % de la
   nula: no separa.
5. **El nulo del CSCV estandariza y centra todas las columnas en la misma media** (`dossier:2038`): destruye la heterogeneidad
   entre variantes que el PBO mide. Resultado: 10/10 PASA con PBO real de hasta 0,825 (`dossier:2035-2041`) y falsos NO
   PASA del 14,7–29,3 % en sintético. Es una prueba que no puede fallar donde debe y falla donde no.
6. **Semilla 0 para todas las madres del 20** (`benchmark.py:44-45`): 2.000 traders idénticos en sus números aleatorios para
   cada madre. No sesga la media, pero convierte K madres en un mismo sorteo: el SPA cree que ve K errores independientes.
7. **`z ≥ 1,65` normal sobre monos cuando `mono_p` empírica está calculada y no se juzga** (`level3c.py:48-49`): en 5.000
   sorteos la p empírica es gratis y no supone normalidad. Hoy no importa (ver 1), pero si el mono sigue, que juzgue la p.
8. **La calibración del 17 se midió volteando por día y el código voltea por semana** (`dossier:1794,1970`, `dossier:12`); los
   «falsos PASA 0,02 / falsos NO PASA 0,22» no son del código vigente. Remedido con semana: 0,03 y 0,13, no registrado.
9. **La nula de la fábrica no existe.** Todo mono nace en Python y «nunca fue seleccionado por un build»
   (`falsePositives/README.md:138-140`). La hipótesis nula correcta para «¿el generador encontró algo?» es: **el mismo
   Builder, con los mismos filtros IS, sobre precios sin ventaja** (signos volteados alrededor de la deriva, o barras en
   bloques). Es exactamente lo que propone `criterios-mcpt-fabrica-propuesta-2026-10-12.md` del dueño; mi diseño (sección 5)
   converge con ella y añade la unidad de apuesta (la celda) y la fiabilidad mitad-mitad.
10. **La verificación de uniformidad del mono (`verify.py:62-81`) calcula 400 p contra el mismo `rest`**: no son
    independientes; su KS prueba intercambiabilidad de los sorteos, no calibración frente a la estrategia real.

### 2.4 Qué cabe esperar de cada aleatoriedad, bien hecha

- Entrada aleatoria con huella conservada y costes cobrados: nula centrada en **−coste/SE** (−0,5 t en índices H1, −1 a −2 en
  forex M30 con coste 0,04–0,07 sd/operación). La real debe compararse en z sobre esa nula, nunca en t absoluta.
- Volteo de signo semanal: exacto bajo simetría; con asimetría positiva de +1 (habitual en ruptura) rechaza 13 % al 5 % en la
  cola baja (`dossier:2188`). Remedio barato: volteo **centrado** (restar la mediana semanal antes de voltear) o bootstrap
  estacionario de semanas, que ya existe en `superior.py:8-22`.
- Permutación entre trimestres (R7) y bootstrap por bloques (R6): correctas; su resultado esperado es que **nunca corten**
  (0 Falla en 169 reales; 0,3 % y 12,8 % en la nula). Son diagnósticos, no criterios.
- Bootstrap de barras con bloque 1 (paso 1): destruye la autocorrelación; el propio proyecto midió 4,0–7,5 % de falsas alarmas
  frente a 0,3–0,8 % con bloque 24 (`dossier:65-66`). Debe ser bloque 24 o estacionario.

---

## 3. La tabla de predicciones (pasos 8 a 20)

Reglas del juego que asumo, porque cambian las cifras y el dueño debe fijarlas (sección 6): (i) «tasa de paso» = fracción que
**no recibe Falla / NO PASA / DESCARTAR** (Limbo sigue), medida sobre lo que entra al paso; (ii) la planta se aplica a los tres
tramos y se hereda por variantes y hermanas (si sólo está en oos1, como hoy en `falsePositives`, del 10 en adelante la
plantada se comporta como la nula: lo marco con †); (iii) la población nula y la plantada se emulan en Python con la huella
de la donante donde el paso exige una tarea SQX (10, 12, 13–16, 19); (iv) `dev.on: false`. Donde la cifra sale de una medida de
la cadena la cito; donde es cálculo mío lo digo; donde no sé, lo digo.

| paso | real | nula | plantada 0,05 / 0,10 / 0,15 | razón en una línea |
|---|---|---|---|---|
| 8 (puerta entera) | **1,7 %** (0,02–15,7 % según celda: XAUUSD 0,03 %, NIKKEI cal6 15,7 %) | **1,0 %** | **19 / 50 / 75 %** | medido en USATEC (`dossier:863-867`); R3 es el 97,8 % del corte y vale `P(N(−0,52+s·√n; 0,93) ≥ 1,65)` con n ≈ 385 |
| 9 (retest otros mercados) | 100 % | 100 % | 100 % | sin criterio (`dossier:911`) |
| 10 (P1–P9) | **55 %** (1 de 3 falla en USATEC; 5 de 10 en NIKKEI) | **45 %** | **45 / 45 / 45 %** † (sin planta en otros mercados); con planta en los 11 mercados: 70 / 90 / 97 % | P3 `z_conj < 0` mata ≈ 50 % de una población sin ventaja (`dossier:1020`); la ventaja real no viaja porque es carga de régimen local (1.2) |
| 11.5 | 100 % | 100 % | 100 % | `rules: []` (`criteria.yaml:142`) |
| 12 (madres) | 100 % | 100 % | 100 % | `else: limbo`, nunca Falla (`criteria.yaml:148`); hermanas: 0 % siempre |
| 14 (T1/T2/T3) | **50 %** (3 de 4 corridas pierden ≥1 madre; 47/50 en mc2; 9/9 en mc1b) | **15 %** | **70 / 90 / 95 %** (†: 15 %) | `f_pos ≥ 0,7` con vecinas sin ventaja ≈ P(Binomial) ≈ 0,5 → Falla; con planta 0,05 las vecinas heredan t ≈ +0,9 y f_pos ≈ 0,8 |
| 16 | 100 % | 100 % | 100 % | `rules: []` (`criteria.yaml:177`) |
| 17 (NO PASA, se lee en el 20) | **75 %** | **52 %** | **78 / 93 / 98 %** (†: 52 %) | real: 3 NO PASA de 12 (`dossier:1860`); nula: calibración sintética 0,48 NO PASA (`dossier:1920`); 0,05/op ≈ Sharpe anual 0,5–0,7 → 0,22; 0,10 ≈ 1,0–1,4 → 0,07 |
| 18 (CSCV) | **100 %** (10/10) | **75 %** | **85 / 92 / 95 %** | sintético: C18-1 falla 14,7–29,3 % sin ventaja (`dossier:2024`); la potencia d01–d03 0,05–1,0 (`dossier:2050`) |
| 18.5 (orden perverso) | **100 %** (13/13 neutro) | **95 %** | **97 / 98 / 99 %** | p− ≤ 0,05 en un test que ρ ≈ 0 no puede disparar (`dossier:2107,2125`) |
| 19 (WFM L1) | **100 %** (0 NO PASA de 10) | **88 %** | **96 / 99 / 99 %** | p− ≤ 0,05 con asimetría → 13 % nominal (`dossier:2188`); con ventaja la cola baja se aleja |
| 20 (`peor` sobre 17–19) | **75 %** | **33 %** | **62 / 80 / 89 %** (†: 33 %) | producto de 17·18·18.5·19 porque `peor` = cualquier fallo (`dossier:2284`); leen las mismas semanas, así que el producto es cota inferior |
| **cadena 8→20** | **≈ 0,35 %** (≈ 35 de 10.000) | **≈ 0,02 %** (≈ 2 de 10.000) | **≈ 4 / 18 / 32 %** (†: 0,7 / 1,8 / 2,8 %) | producto; cociente real/nula ≈ 16, real/plantada-0,05 ≈ 0,09 |

**Lo que no sé y por qué:** (a) paso 10 para la plantada, porque depende de si la planta viaja a los 11 mercados — hoy no hay
mono en otros mercados (`falsePositives/README.md:191`); (b) paso 14 para nula y plantada, porque una población de monos no tiene
parámetros que perturbar: la cifra supone vecinas = la misma huella re-sorteada; (c) la tasa real del 8 varía **dos órdenes de
magnitud** entre celdas (0,03 % XAUUSD, 15,7 % NIKKEI cal6) y no es una propiedad de la cadena sino del régimen de oos1 en
cada celda (1.2): una predicción «en real» sólo tiene sentido por celda.

**Lo que esta tabla dice si se cumple:** la cadena multiplica la proporción de verdaderas por ≈ 16 frente a la nula, pero
casi todo ese factor (1,7 de 16) está en el 8, otro 3–4 en el 14 y 1,5 en el 17–20; el 9, 11.5, 12, 16, 18, 18.5 y 19
aportan un factor ≈ 1 cada uno. Y contra una ventaja realista (0,02 neto/op) el factor del 8 es 2,8, no 19.

---

## 4. Qué probabilidad daría y qué paso me la da

**La apuesta:** 0,30 a que una superviviente de la cadena de hoy tiene ventaja neta > 0 en los tres años siguientes sobre su
mercado y marco. Intervalo 0,20–0,45. A que tiene ventaja neta ≥ 2× su coste (la ventaja que paga el riesgo de ejecución y la
deriva de spread): **0,15**.

**Cómo lo calculo (es un cálculo bayesiano a nivel de celda, no de estrategia, por 1.1):**

1. *Prior por celda.* De 27 poblaciones cosechadas, el test de población que yo hago (volteo semanal sobre la media del panel,
   `cells.csv`, `p_pob`) da p ≤ 0,05 en **2** (GBPUSD H1 cal4 0,013; EURUSD H1 chk8 0,043) y 0,062 en NIKKEI cal6; al 5 % se
   esperan 1,35 por azar. Ninguna sobrevive a Bonferroni sobre 27. Prior razonable de que una celda cualquiera tenga ventaja
   neta: **0,05–0,15**; uso 0,10.
2. *Verosimilitud de la cadena* para una ventaja del tamaño que el generador produce (0,02 neto/operación, 1.4): paso 8, LR
   2,8 (cálculo en 1.4); paso 10, ≈ 1 (la ventaja local no viaja); paso 14, ≈ 2 (f_pos con t ≈ +0,4 frente a 0); 17–20, ≈ 1,4
   ((1−0,30)/(1−0,48)). Producto **≈ 8**.
3. *Posterior:* odds 0,11 × 8 = 0,9 → **P ≈ 0,47** con prior 0,10; con prior 0,05, 0,30; con prior 0,15, 0,58. El valor 0,30 es
   el que doy porque el prior 0,10 ya es generoso: 2 de 27 celdas a p < 0,05 es lo que da el azar.
4. *Descuento por lo roto:* coste a ±50 % (1.4) y tramos gastados (1.5) no entran en el LR y sólo pueden bajarlo. De ahí el 0,30.

**El paso que la da:** ninguno. Hoy el único número con tasa de error medida es el 8 (control `falsePositives`), y su LR
contra una ventaja realista es 2,8. Los pasos 17–20 tienen calibración sintética pero no real (`dossier:1916-1920,1984`); el 10, 12,
14 y 16 no tienen ninguna (`criteria.yaml:80,154`). **En mi diseño la probabilidad la da un solo número: la p de la celda bajo
la nula de la fábrica, corregida por el número de celdas del ledger**, y la estrategia concreta hereda la p de su celda
encogida hacia la media de la celda con fiabilidad mitad-mitad (que hoy es ≤ 0: encogimiento total).

---

## 5. Lo que haría yo

Cada punto acaba en una decisión ejecutable con su coste y su ganancia. El orden es el de ejecución.

### 5.1 Cambiar la unidad: una hipótesis por celda, no por estrategia (Python, 1 minuto por celda)

**Prueba:** sobre el panel semanal de exceso neto de **toda** la población de oos1 (lo que ya exporta el paso 7), la media
entre estrategias por semana, y su suma contra 5.000 volteos semanales centrados (o bootstrap estacionario de semanas,
`superior.py:8-22`). Una p por celda. Corrección BH sobre el ledger de celdas (hoy 27; `ledger/trials.py` ya cuenta).
**Potencia:** con n_eff ≈ 3 y 4 años, detecta al 80 % una ventaja neta de ≈ 0,05 sd/operación; contra 0,02 la potencia es
≈ 15 %. Es poca, y es la verdad: cuatro años de un mercado son cuatro años. **Ganancia:** sustituye 10.000 pruebas
dependientes por una con tasa de error real; convierte el paso 8 en «¿esta celda vale?» y deja el «¿cuál de ellas?» a
5.3. **Coste en estrategias:** ninguno dentro de la celda; a nivel de celda, con la evidencia de hoy, **ninguna de las 27
pasa**. Hay que decirlo así.

### 5.2 La nula correcta: la fábrica sobre precios sin ventaja (un build de SQX por celda, ≈ 40 min en el custodio)

Es la propuesta MCPT del dueño (`criterios-mcpt-fabrica-propuesta-2026-10-12.md`). Lo que añado: que el resultado que se
compare sea el de 5.1 (la p de la celda) y la tasa de paso del 8 **por celda**, no por estrategia; y que K = 5 réplicas
sintéticas por celda bastan para situar la real en su percentil (el 1,7 % real contra 1,0 % de monos de Python no es una
comparación válida porque los monos no pasaron por el generador, `README.md:138-140`). **Ganancia:** es la única manera de
medir el sesgo de selección del build, que hoy no mide nadie (`dossier:893`). **Decisión:** aprobar un `Test_` sintético por
celda nueva, antes del paso 8 real.

### 5.3 Dentro de la celda: dejar de ordenar por t; ordenar por robustez y coste

Dado 1.2, la t de oos1 no predice la segunda mitad de oos1. **Decisión:** R3 pasa a `>= 0` (quita lo que pierde: deja ≈ 60 %
de 10.000 en vez de 1,7 %) y el orden dentro de la celda lo da (a) `edge_mean_oos ≥ 2` (R5c, que sí mide algo distinto:
Spearman 0,61 con t) y (b) la fiabilidad mitad-mitad **de la propia estrategia** sobre build (dos mitades del build dan ρ
estimable sin tocar oos1). Las supervivientes se escogen por **diversidad** (menor correlación semanal entre ellas), no por
rango de t: con n_eff ≈ 2, quedarse con las 3 mejores por t es quedarse tres veces con la misma. **Coste:** ninguno en CPU;
en estrategias, el paso 8 deja pasar más y el 5.1 decide la celda.

### 5.4 Fusionar las cuatro lecturas del mismo número y borrar lo que nunca corta

R3, R5c-t, R8 y el mono (correlaciones 0,89–1,00, sección 2.3.1) → **una** regla: la z de la estrategia sobre su mono
(con horas restringidas, 5.5) juzgada con `mono_p` empírica. R6 y R7 (0 Falla en 169; en la nula R6 Falla 0,3 % y R7 Limbo 12,8 %) → diagnóstico sin
regla. R9b, calidad de datos y retraso se quedan (miden otra cosa: Spearman ≤ 0,27 con t). **Ganancia:** de 17 líneas a 8,
y cada una mide una hipótesis distinta. **Coste:** 0 estrategias (ninguna de las borradas corta hoy).

### 5.5 El mono con las horas de la estrategia (≈ 50 líneas en `windowed.py`)

Implementar la decisión del 2026-09-25: barras elegibles = las horas y días de semana en que la estrategia abre
(`engines/nulls/README.md:140-143`). **Ganancia:** el mono paga el spread de las horas que la estrategia paga; con spread 9×
a la hora 0 (`dossier:357`) es la diferencia entre comparar con un trader y comparar con nadie. **Prueba de potencia:**
repetir `falsePositives` con planta 0,02/0,04/0,06 (5.6); espero que la nula suba de 1,0 % a ≈ 2–3 % y la separación
real–nula baje.

### 5.6 Plantas realistas: 0,02 / 0,04 / 0,06 neto, concentradas

Sustituir 0,05/0,10/0,15 por 0,02/0,04/0,06 (la real mediana es 0,018) y plantar **no constante**: la planta se reparte
sobre el 30 % de operaciones de mayor ATR (así R8 y R9b se calibran contra lo que buscan). **Ganancia:** las tasas de la tabla 3
pasan a medir potencia contra el enemigo real. **Coste:** 70 min de Python por celda (`dossier:875`), que se reducen a 15
bajando a 20 monos por donante (el error del 1 % con 5.000 monos es ±0,14 pp; con 2.000, ±0,22 pp: sobra).

### 5.7 El bloque ciego: una prueba, no cuatro

17, 18, 18.5 y 19 leen las mismas 143–195 semanas de oos2 con las mismas variantes y `peor` multiplica sus falsos fallos
(nula: 33 % sobrevive al 20 aun sin que ninguno mida nada). **Decisión:** una sola lectura de oos2 por madre — la suma
semanal del exceso neto de **la madre** (no de la familia) contra 5.000 volteos centrados, una cola, α = 0,05, más la mediana
de la familia como diagnóstico. **Borrar 18.5** (0 NO PASA en 13, ρ ≈ 0 en todas) y **18** (10/10 PASA, falso NO PASA 15–29 %
en sintético, nulo que destruye lo que mide). **19** se queda como diagnóstico de SQX (el área) sin regla. **Ganancia:** un
error de tipo I conocido (5 %) en lugar del producto 0,52·0,75·0,95·0,88; **coste:** ninguno en estrategias (hoy 18, 18.5 y 19
no cortan a nadie), −40 s por madre.

### 5.8 Paso 14: T1 sólo sobre el exceso de oos1, y T2/T3 fuera

T3 = 1,000 en 58/58 (`dossier:1324`): borrar. T2 usa el P/L de SQX con sus costes y la deriva «aprox» (`dossier:1316`): borrar.
T1 en build mata madres con exceso de build ≤ 0 que no son frágiles (29/50, 5/9: `dossier:1351`): T1 sólo en oos1 y sólo
`f_pos ≥ 0,6` (la mitad más un margen de las vecinas en positivo). **Ganancia:** el 14 deja de ser el segundo cuello (50 %)
por una razón que no es fragilidad. **Coste:** −500 retests de build por madre.

### 5.9 Lo que dejaría como está

El 10 (la lógica viaja) es la única prueba de la cadena que mira datos **nuevos** (V0, `dossier:986`), y hoy ninguna regla lee
V0. Decisión: P3 sobre V0+V2 (fuera V1, que es el build del principal), umbral en z ≥ 1,65 a una cola, y el resto de P1–P9 como
diagnóstico. El 16.5 (nube, LHS) y la lectura del 16 son buenos mapas; sin regla, como ahora.

### 5.10 Antes de nada

`dev.on: false` (`criteria.yaml:2`); una sola cifra de spread por tramo con su intervalo (`dossier:354-361`); el descuadre
reprecio/SQX a < 1 % antes de leer el 17–20 (`dossier:2154`); y aceptar que `USDJPY_M30_doubleROCLong` ya no tiene oos2
(94 filas): su siguiente muestra limpia es el futuro — el paso 26 en cuenta demo es, hoy, la única prueba fuera de muestra que
le queda a esa celda.

---

## 6. Decisiones del dueño, como preguntas

1. **¿Qué es «ventaja real»?** (a) neto > 0 en los tres años siguientes; (b) neto ≥ 2× coste. Doy 0,30 y 0,15: son
   apuestas distintas y la cadena debe decir cuál persigue.
2. **¿La unidad de la apuesta es la estrategia o la celda?** Con n_eff ≈ 2–4 yo digo celda (5.1). Si el dueño quiere seguir
   por estrategia, el paso 8 debe decir «réplica n de la misma apuesta», no «superviviente».
3. **¿La planta se aplica sólo a oos1 (como hoy) o a los tres tramos y a variantes y hermanas?** Cambia la tabla 3 del paso
   10 en adelante (las filas †).
4. **¿R3 a `>= 0` (quitar perdedoras) o a 1,65 (ordenar por suerte)?** 5.3 argumenta `>= 0`.
5. **¿Se aprueba un build sintético por celda (5.2, ≈ 40 min de custodio) antes de cada paso 8 real?**
6. **¿El mono con horas restringidas (5.5) sustituye al mono uniforme, o conviven como dos peldaños?** Yo: sustituye; dos
   peldaños son dos p más por estrategia.
7. **¿Se borran 18 y 18.5 y se funden 17 y 19 en una lectura (5.7)?** Coste cero en supervivientes hoy.
8. **El 10 lee V1 (el build del principal) dentro de P3.** Dos lecturas posibles: (a) es deliberado, para dar peso a la
   ventana larga; (b) es réplica del sesgo de selección (`dossier:986,1047`). ¿Cuál?
9. **Tres cifras de spread para el mismo tramo (304 / 607 / 747).** ¿Cuál es la de la ficha y con qué intervalo?
10. **`dev.on`:** ¿se apaga ya o sigue hasta que 5.1–5.6 estén hechas?

---

## 7. Tabla final por paso

Coste = lo que gasta (CPU/SQX/tramo); información = cociente de verosimilitud aproximado contra una ventaja realista de
0,02 neto/operación (sección 3 y 4); veredicto = mantener / fusionar / borrar / diagnóstico.

| paso | coste | información (LR) | veredicto | razón |
|---|---|---|---|---|
| 8 · R1a, R1b, R2 | nulo | sanidad | **mantener** | presencia y neto > 0; R2 ya quita 21–71 % (`dossier:740-742`) |
| 8 · R3 | nulo | 2,8 (a 1,65); ≈ 1,3 (a 0) | **mantener a `>= 0`** | el rango por t no persiste (1.2); el signo sí sirve |
| 8 · R5c, R8, mono, R5c-t | 10 s + 26,9 GB (mono) | ≈ 1 marginal sobre R3 (ρ 0,68–1,00) | **fusionar** en una z sobre el mono con horas (5.4, 5.5) | cuatro lecturas de un número |
| 8 · R6, R7 | 5.000 sorteos cada una | ≈ 1 (0 Falla en 169 reales) | **diagnóstico** | nunca cortan ni deben |
| 8 · R9b, calidad, retraso | nulo | ≈ 1 pero ortogonal (ρ ≤ 0,27) | **mantener** | miden ejecución, no ventaja |
| 8 · control `falsePositives` | 70 min → 15 min | es el que da la tasa de error | **mantener, replantar** (5.6) | la única calibración real de la cadena |
| **nuevo** · test de celda (5.1) | 1 min Python | la hipótesis correcta | **añadir** | n_eff ≈ 2–4 |
| **nuevo** · fábrica sobre sintético (5.2) | 40 min custodio por celda | mide el sesgo del build | **añadir** | nadie lo mide hoy |
| 9 | 11 retests SQX | 0 | **mantener** (alimenta el 10) | sin criterio |
| 10 | Python | ≈ 1 hoy; > 1 si lee V0 | **mantener, leer V0** (5.9) | única ventana nueva de la cadena |
| 11, 11.5, 11.7, 12 | 2 builds SQX + retests | 1 (nunca falla una madre) | **diagnóstico**; hermanas: borrar de la cola | `z_new` calibrado con datos borrados (`dossier:1171,1192`) |
| 13 · MCR 1 Bar, 4 MinDist, 7 OHLC | 94–844 s SQX | 1 (T3 = 1,000 en 58/58) | **borrar 1 Bar y 4 MinDist**; 7 OHLC diagnóstico | no alimentan ninguna regla útil |
| 14 · T1 build | 500 retests SQX | ≈ 2, pero mata por razón equivocada | **fusionar** en T1 oos1 `f_pos ≥ 0,6` (5.8) | exceso build ≤ 0 no es fragilidad |
| 14 · T2, T3 | SQX | 1 | **borrar** | 1,000 en 58/58; «aprox» |
| 15, 16 | 216–295 s SQX | 1 (sin regla) | **mantener como mapa** | alimenta 16.5 |
| 16.5 · nube, LHS, Sobol | 300 s/madre | 1 (sin regla) | **mantener como mapa** | buen diseño; «legible» nunca discrimina (`dossier:1683`) |
| 17 · WFC | 5 s | ≈ 1,4 | **fusionar** con 19 en una lectura de oos2 (5.7) | mismas semanas, mismas variantes |
| 18 · CSCV | 9 s | ≈ 1,1 (10/10 PASA; nulo mal construido) | **borrar** | 2.3.5 |
| 18.5 · superficies | 18 s | ≈ 1,0 (13/13 neutro, ρ ≈ 0) | **borrar** | no puede disparar |
| 19 · WFM | SQX (30 celdas) | ≈ 1,05 | **diagnóstico** (área de SQX), regla a la lectura fundida | asimetría → 13 % al 5 % |
| 20 · `peor` + benchmark + SPA/StepM | 15 s + 200 MB | el producto de 17–19 | **sustituir** por la lectura única; SPA/StepM diagnóstico con semilla por madre | semilla 0 compartida (2.3.6); SPA nunca < 0,40 |
| 21 | Python | 0 (describe) | **mantener** | no juzga, no estorba |
| 26 | MT5 | — | **mantener y subir de rango** | para las celdas con oos2 gastado es la única muestra limpia que queda |

**Si el proceso debería tener otra forma:** sí, y es ésta en dos líneas — *una celda, una nula de fábrica, una p; dentro de
la celda, diversidad y coste, no rango; un oos2, una lectura.* Con la evidencia de hoy (27 celdas, 2 a p < 0,05 sin corregir,
n_eff ≈ 3, ventaja neta mediana 0,018 sd/operación con coste 0,021–0,070) la respuesta honesta a «¿tiene ventaja real?» es
**«todavía no se ha demostrado en ninguna celda»**, y la cadena actual no puede demostrarlo porque pregunta 10.000 veces lo
que es una pregunta y luego pregunta cuatro veces lo que es otra.
