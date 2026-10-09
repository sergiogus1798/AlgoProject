# Paso 20 — el análisis conjunto de 17, 18, 18.5 y 19, y el SPA/StepM contra el buy & hold: qué hace, cómo decide y qué no cuadra

**Fecha:** 2026-10-08 · **Para:** el dueño · **Alcance:** `studies/closing/blindJoint/` entero, el motor `engines/inference/snooping/`, las dos puertas de `ledger/gate.py`, `ledger.backfill --blind`, las reglas «16.5» a «19» de `pipeline/autopilot/criteria.yaml` (el «20» no existe), `pipeline/autopilot/tail.py`, `blind.py` y `judge.py`, y el capítulo `56-paso-20.md` del manual.

Revisado por un miembro del Council (Feynman) el 2026-10-08; correcciones aplicadas.

**De dónde salen los números.** Las fórmulas y reglas, del código en disco leído hoy hasta las 10:02 UTC, con `fichero:línea`. A las 10:15 UTC el árbol no tiene ningún fichero del alcance con hora posterior a las 09:34 (`run.py`), y la distinción `HEAD` / árbol de trabajo de más abajo sigue siendo la correcta (comprobado por el revisor). Los ejemplos reales, de lo que ya escribieron cuatro corridas (no se ha releído `oos2`): `Trade_NIKKEI225_M30_volatilidadL` (2026-10-04, 10 madres), `Test_NIKKEI225_M30_simpleL_fin` (2026-10-05, 10), `Test_USA500_H1_indicesIBS` (2026-10-06, 3) y `Test_USDJPY_M30_doubleROCLong` (2026-10-06, 3), más los ledgers de `AlgoData/ledger/`. Lo marcado **«calculado por mí»** son simulaciones sobre datos sintéticos, con su script en la carpeta temporal `…/scratchpad/paso20/` (`potencia_stepm.py`, `juguete.py`, `juguete2.py`).

**El commit descrito y lo que está sin confirmar.** `HEAD` es `b2b4c8c` (2026-10-08 07:42, «steps 17-20…»). **El paso 20 que describe este dossier NO es el de ese commit: es el del árbol de trabajo.** Con cambios sin confirmar, según `git status --short`:

- `studies/closing/blindJoint/`: `README.md`, `benchmark.py`, `config.yaml`, `inputs.py`, `measure.py`, `one.py`, `pieces.py`, `readings.py`, `report.py`, `tooltips.py`, `words.py` (todos menos `many.py`).
- `assets/_policy.yaml`, `engines/inference/snooping/superior.py` y su `README.md`, `ledger/gate.py`, `ledger/blind.py`, `ledger/steprows.py`, `pipeline/autopilot/blind.py`, `facts.py`, `judge.py`, `plan.py`, `run.py`, `tailrun.py`, `variants.py`.
- `pipeline/autopilot/criteria.yaml`, `tail.py` y `ledger/backfill.py` están confirmados y sin tocar.

Tres consecuencias que conviene tener presentes al leer:

1. **La lectura `peor` no está en el commit.** En `HEAD`, `config.yaml` dice `pieces: sin_fallo` y `readings.py` no tiene `WORST` ni `worst()`; sin embargo el `report.py` de `HEAD` ya nombra `readings.WORST` (línea 78). El commit quedó a medias en este módulo: funciona mientras `oos2` no se niegue y revienta con `AttributeError` si se niega.
2. **`BlindJoint` en la reserva de `oos2` tampoco está en el commit.** `assets/_policy.yaml:48` lo lista en disco; en `HEAD` no.
3. **Otra sesión estaba editando el módulo mientras lo leía**: `measure.py` y `report.py` llevan hora 09:26 y `README.md` 09:29. Lo único que cambia en esos dos respecto a `HEAD` es que el `report` guarda ahora el bootstrap del SPA en `distribuciones.parquet` (`report.py:137-139`, `measure.py:87-90`); no vi ningún fichero a medio escribir.

**Ninguna corrida se ha hecho con este código.** Las diez carpetas `blindJoint` de `AlgoData/reports/` son del 2026-09-29 al 2026-10-06: todas con `sin_fallo` (o sin regla) y con los estados antiguos de las piezas (`no fiable`, `no viaja`, `blind`…). Donde un ejemplo viene de ahí lo digo, y separo «lo que el código hace hoy» de «lo que la corrida guardó».

**Ninguna línea está congelada.**

---

## 0. En una página

**La pregunta del paso.** Son dos, y sólo la primera decide hoy:

1. *Con los cuatro juicios de 17, 18, 18.5 y 19 delante a la vez, ¿qué se hace con cada madre?* Regla viva (provisional, dueño 2026-10-07): **manda el peor de los cuatro estados**. Algún NO PASA → DESCARTAR; si no, algún LIMBO → REVISAR; si no → MANTENER.
2. *¿Alguna madre bate al buy & hold a igual riesgo en `oos2`, una vez pagado el haber probado K madres?* (SPA de Hansen y StepM de Romano-Wolf.) **Se calcula, se enseña y no decide nada** bajo `peor`.

**Lo cargado hoy.**

| qué | dónde | valor |
|---|---|---|
| cómo se combinan las piezas | `config.yaml:26` | `peor` (provisional; árbol de trabajo sin confirmar — en `HEAD`: `sin_fallo`) |
| sobre quién cuenta el StepM | `config.yaml:33` | `entrantes` (toda madre completa) |
| FWER del StepM | `ledger/thresholds.yaml:30` | 0,05 |
| benchmark | `config.yaml:13` | buy & hold a igual riesgo |
| bootstrap | `config.yaml:40-41` | 1.000 remuestreos, semilla 0 |
| regla del paso 20 en `criteria.yaml` | — | **no existe** |

**Lo que sale en las corridas reales** (todas anteriores al rediseño): 26 madres completas en cuatro corridas, **26 DESCARTAR con la regla antigua `sin_fallo+entrantes` y los estados antiguos de las piezas** (ninguna corrida usa `peor`), y el autopiloto siguió con todas. El StepM no nombró a ninguna en ninguna corrida; la p del SPA fue 0,58 a 0,90.

**Las doce cosas que conviene saber.**

1. **El DESCARTAR sólo se anota.** `criteria.yaml` no tiene entrada «20», así que el juez escribe los hechos y dice «ninguno: el paso no tiene criterio» (`judge.py:175-176`). En `Test_USA500_H1_indicesIBS` el paso 20 marcó DESCARTAR a las 3 (lectura de ayer, `sin_fallo+entrantes`) y las 3 salieron como finalistas del paso 25. El ledger, en cambio, apuntó `n_out = 0`.
2. **REVISAR es «se queda».** Todo lo que no es DESCARTAR mantiene a la madre (`report.py:20`, `judge.py:22`). Con las tasas medidas del paso 17 y las nominales supuestas de 18, 18.5 y 19, y suponiendo las cuatro pruebas independientes (no lo son: leen la misma madre sobre tramos que se solapan), una madre **sin ventaja** acaba en MANTENER entre el 0,8 % y el 2 % y en REVISAR entre el 44 % y el 50 %; el reparto real no está medido (§5.14). Con dependencia positiva, MANTENER es más probable y DESCARTAR menos que en estas cuentas. Como filtro, `peor` deja pasar a casi la mitad de las que no tienen nada (§2.3, calculado por mí).
3. **Una madre con ventaja real y modesta rara vez sale MANTENER.** Con Sharpe 0,5 el paso 17 solo da PASA entre el 20 % y el 43 % de las veces (su propia calibración), y MANTENER exige PASA en las cuatro.
4. **El StepM contra el buy & hold casi no puede nombrar a nadie en 2,75 años.** Con un buy & hold de Sharpe 1 (el NIKKEI y el USA500 de `oos2` lo tienen), una madre que sólo iguala al índice (Sharpe 1 frente a 1) no es nombrada en el 0,3-4 % de los casos, que es lo correcto; para ser nombrada la mitad de las veces necesita un Sharpe real de 2,4 a 3 según la correlación con el activo y K (§2.8, calculado por mí). Con datos reales la tabla es un techo (cosa 10).
5. **El SPA de la librería no está estandarizado**, aunque el código y su README lo den por hecho: compara medias en dólares por día, así que la madre más volátil manda en el contraste (§5.1).
6. **Aunque no decida, el SPA gasta una mirada a `oos2`** cada vez que corre, y queda en el ledger. El estudio `NIKKEI225_M30_simple_long` lleva seis.
7. **Dos documentos (el README del estudio y el capítulo 56 del manual) dicen sin matiz que el paso 20 no puede leer `oos2`; en disco sí puede** (`_policy.yaml:48`); WORKFLOW fila 20 y el comentario de `gate.py:18-21` siguen listando `BlindJoint` como ausente de `reserved_for`. Y tres documentos dicen que 17-19 no se apuntan solos en el ledger; se apuntan: la WFC y el CSCV desde el 2026-09-27, la WFM desde el 2026-10-04.
8. **Hay dos tablas para los mismos cuatro estados**: la de cada estudio (la que lee el paso 20) y la de `criteria.yaml` «17»-«19» (la que lee el juez de cada paso). Hoy coinciden; nada obliga a que sigan coincidiendo.
9. **Las probabilidades de la regla `peor` salen de tasas nominales supuestas y de independencia entre las cuatro pruebas.** Las cuatro leen la misma madre; con dependencia positiva MANTENER sube y DESCARTAR baja respecto a cada cifra de §2.3 y §6 (§5.15).
10. **La tabla de potencia del StepM es un techo:** error de ± 4,9 puntos al 95 % (no ± 2,5), FWER comprobado sólo con el buy & hold a Sharpe 0, y con autocorrelación y volatilidad agrupada unos 5-7 puntos menos de potencia y FWER del 7-8 % (§5.16).
11. **Toda cifra de las corridas antiguas es de la regla `sin_fallo`, no de `peor`:** los 26 DESCARTAR y los 3 de USA500 (§5.17).
12. **El DESCARTAR sigue sin aplicarse y la regla `peor` sólo existe en el árbol de trabajo:** comprobado por el revisor a las 10:15 UTC del 2026-10-08, ningún fichero del alcance con hora posterior a 09:34:47 (§5.18).

---

## 1. Qué es el paso y cómo decide

### 1.1 Dónde está

Es el primer paso de la familia «Cierre». Llega después del bloque ciego: 17 (WFC), 18 (CSCV), 18.5 (superficies por mercado) y 19 (WFM) se calculan uno tras otro para **todas** las supervivientes del paso 16, sin que ninguno corte nada (`cut: null` en los cuatro). El paso 20 es donde por primera vez se leen juntos.

### 1.2 El recorrido, en orden

`python3 -m studies.closing.blindJoint.report --project P --wfm-databank WFM --feed F --symbol S --timeframe TF --family FAM` hace esto (`report.py:82-144`):

1. **Lee los mandos** (`inputs.config`).
2. **Puerta ciega** (`inputs.blind_door` → `gate.allow_read`, `gate.py:141-162`): si el proceso es un agente autónomo (`ALGO_AUTONOMOUS=1`, que el autopiloto pone siempre, `run.py:235`), exige que el ledger del estudio tenga filas de los pasos 17, 18 y 19. Para un humano no comprueba nada.
3. **Reúne la población** (`pieces.population`, `pieces.py:71-100`): una fila por cada madre que aparezca en el `verdict.csv` de la WFM **o** tenga carpeta en `AlgoData/strategyPermutations/<P>/`. Una madre es *completa* si tiene los cuatro resultados; si le falta uno se lista como INCOMPLETA y no se le lee ninguno.
4. **Puerta de `oos2`** (`inputs.segment_door` → `gate.allow(20, "oos2", S)`): pregunta a la política si el paso 20 puede mirar `oos2`. Una negativa no es un fallo: es un texto que se guarda en `refused`.
5. **Puerta de las operaciones** (`inputs.trades_door`): cada madre completa necesita `trades.parquet` en su lote de variantes. Si falta, también es `refused`.
6. Si la lectura elegida necesita el StepM y está negado, se para (`need_stepm`, `report.py:75-79`). **`peor` está exenta**: sigue sin StepM.
7. Si nada lo niega: reconstruye el resultado diario de cada madre en `oos2`, calcula el buy & hold a igual riesgo, el SPA y un StepM por lectura.
8. Escribe la página, `readings.csv`, `verdict.csv`, y —sólo si leyó `oos2`— `distribuciones.parquet` y **una fila en el ledger** (paso 20, tramo `oos2`).

### 1.3 Los cuatro estados que lee

El paso 20 **no recalcula ningún umbral**: abre el JSON pequeño que dejó cada estudio y copia su estado (`pieces.said`, `pieces.py:48-68`).

| pieza | fichero que abre | de dónde saca el estado |
|---|---|---|
| 17 WFC | `<lote>/estudios/wfc.json` | `facts.<composición que decide>.estado` (`pasa`/`limbo`/`no_pasa`), traducido por `pieces.WFC` (`pieces.py:16`) |
| 18 CSCV | `<lote>/estudios/cscv.json` | `verdict.state` |
| 18.5 superficies | `<lote>/estudios/marketSurfaces.json` | `verdict.state` |
| 19 WFM | `reports/<P>/<WFM>/<día más reciente>/wfm/estrategias/<madre>.json` | `verdict.state` |

Las tres palabras internas son `pass`, `watch` y `fail`, que equivalen a PASA, LIMBO y NO PASA. Qué hace falta hoy para cada una (lo fijan los estudios, no el paso 20):

| pieza | NO PASA (`fail`) | LIMBO (`watch`) | PASA (`pass`) | `fichero:línea` |
|---|---|---|---|---|
| 17 | la mediana neta fuera del 20 % mejor de dentro es ≤ 0 | mediana > 0 pero su p > 0,05, u orden perverso, o menos de 30 variantes | orden no perverso, mediana > 0 y p ≤ 0,05 | `wfc/verdict/state.py:34-56` |
| 18 | la elegida pierde fuera en ≥ 50 % de las particiones, o el PBO llega al p95 de su nulo | la P de pérdida supera el p95 de su nulo, o menos de 30 variantes | el resto | `cscv/verdict/state.py:9-27` |
| 18.5 | orden entre mercados perverso (build+oos1) | sin dato, prima del 20 % mejor ≤ p5 de su nulo, u orden perverso o sin dato en `oos2` | el resto | `marketSurfaces/verdict/call.py:29-45` |
| 19 | L1 pierde en `oos2` con p− ≤ 0,05 | la mediana del exceso en `oos2` es ≤ 0 sin esa significancia | el resto | `wfm/verdict/call.py:9-38` |

Un PASA es, en las cuatro, **un veto levantado y no un voto a favor**: 18.5 y 19 dan PASA a todo lo que no sea claramente malo. Los detalles de cada una están en sus dossiers; ojo, los cinco del 2026-10-07 describen el estado anterior al rediseño.

### 1.4 La regla de combinación viva: `peor`

Una sola función (`readings.py:26-28`):

```
si alguna de las cuatro es fail      → fail
si las cuatro son pass                → pass
en cualquier otro caso                → watch
```

Y su traducción a lo que lee `/curate` (`report.py:20` y `57-72`):

| peor estado | `verdict.csv` | qué le pasa a la madre |
|---|---|---|
| `fail` | DESCARTAR | hoy nada: se anota (§4.3) |
| `watch` | REVISAR | se queda |
| `pass` | MANTENER | se queda |
| incompleta | MANTENER, motivo «incompleta: no leída» | se queda |

Ejemplo a mano con los estados de una madre real, `Strategy 10.23.380` de `Test_USDJPY_M30_doubleROCLong` (2026-10-06; estados con las reglas antiguas): WFC `fail`, CSCV `pass`, superficies `watch`, WFM `watch`. Hay un `fail` → **DESCARTAR**. Si la WFC hubiera dado `watch`, quedarían `watch, pass, watch, watch` → **REVISAR**. Sólo `pass, pass, pass, pass` da **MANTENER**.

### 1.5 Las otras lecturas, que siguen calculándose

`readings.csv` lleva una columna por lectura (`readings.py:31-54`):

| lectura | pasa las piezas si… | y además |
|---|---|---|
| `unanimidad` | las cuatro son `pass` | el StepM la nombra |
| `sin_fallo` | ninguna es `fail` | el StepM la nombra |
| `ninguna` | siempre | el StepM la nombra (decide solo) |
| `peor` | — | tres valores; el StepM no cuenta |

`unanimidad` y `sin_fallo` se combinan con las dos poblaciones para el StepM: `supervivientes` (sólo las que las piezas dejan) o `entrantes` (todas las completas); `ninguna` y `peor` sólo con `entrantes` (con `supervivientes` serían la misma columna). Son seis columnas. Ayer la lectura elegida era `sin_fallo+entrantes`, y por eso las cuatro corridas guardadas dicen «No pasa» para todas: ninguna fue nombrada por el StepM.

### 1.6 Qué cambió respecto a ayer

- La lectura: `sin_fallo` (dos valores, exige el StepM) → `peor` (tres valores, sin StepM).
- Aparece REVISAR.
- Con `oos2` o las operaciones negadas, ayer el `report` se paraba; hoy bajo `peor` da el veredicto con los cuatro estados, no escribe fila en el ledger y avisa «Falta el StepM» (`many.py:105-108`).
- `criteria.yaml` tiene ahora reglas «17», «18», «18.5» y «19» (ayer ninguna). Sigue sin «20».
- Los cuatro estudios cambiaron sus tablas: los estados guardados no predicen los de hoy. Sobre la misma matriz de `Trade_NIKKEI225_M30_volatilidadL`, la lectura de la WFM del 2026-10-04 dio 1 `pass`, 4 `watch` y 5 `fail`; la del 2026-10-07 (regla nueva, `reports/…/WFM/2026-10-07/wfm/verdict.csv`) da 4 `pasa`, 5 `limbo` y 1 `no_pasa`.

---

## 2. Fundamentos, desde cero

### 2.1 Qué significa combinar pruebas con «manda la peor»

Cada prueba puede equivocarse de dos maneras: dejar pasar a una estrategia que no vale (falso PASA) o tumbar a una que sí vale (falso NO PASA). Al juntar varias con la regla «manda la peor»:

- **Para salir MANTENER hay que acertar en todas.** Las probabilidades de PASA se multiplican (si las pruebas fueran independientes; no lo son, ver abajo), así que MANTENER es difícil para todas: las malas y las buenas.
- **Para salir DESCARTAR basta fallar una.** Las probabilidades de NO PASA casi se suman, así que DESCARTAR es fácil para todas: las malas y las buenas.

Ejemplo de juguete. Dos pruebas independientes; una estrategia buena pasa cada una el 80 % de las veces y falla el 10 % (el 10 % restante, limbo):

- MANTENER = 0,8 × 0,8 = **64 %**.
- DESCARTAR = 1 − 0,9 × 0,9 = **19 %**.
- REVISAR = el resto = **17 %**.

Con cuatro pruebas iguales: MANTENER 0,8⁴ = 41 %, DESCARTAR 1 − 0,9⁴ = 34 %. La regla es exigente con las buenas a medida que se añaden piezas.

Las pruebas no son independientes. Con dependencia positiva, MANTENER es más probable y DESCARTAR menos probable que en estas cuentas; las cifras de aquí son el extremo de independencia y están por medir (§5.14).

### 2.2 Qué tasas declara cada prueba

Para hacer esa cuenta con las cuatro piezas reales hace falta que cada una diga con qué frecuencia da cada estado a una estrategia sin ventaja y a una con ventaja. Lo que hay:

| pieza | sin ventaja: PASA / LIMBO / NO PASA | con ventaja | de dónde |
|---|---|---|---|
| 17 WFC | **0,020 / 0,503 / 0,477** | Sharpe 0,5: 0,203 / 0,577 / 0,220 (el orden no se transmite) o 0,427 / 0,487 / 0,087 (se transmite). Sharpe 1,0: 0,510 / 0,420 / 0,070 o 0,917 / 0,080 / 0,003 | calibración registrada, `AlgoData/ledger/wfc_calibration.json`, 2026-10-07, 300 familias sintéticas por fila, 2,75 años fuera |
| 18 CSCV | **no las declara.** Por construcción, el PBO llega al p95 de su nulo como mínimo el 5 % de las veces (NO PASA; el corte es `>=` y el PBO es discreto, `state.py:62`) y la P de pérdida supera el p95 el 5 % (LIMBO). Con qué frecuencia una sin ventaja tiene P de pérdida ≥ 0,5 no está escrito en ningún sitio | `potencia.dNN` por madre (hecho del estudio); ninguna corrida lo tiene guardado con el código nuevo | `cscv/verdict/state.py:59-78` |
| 18.5 | nominal: orden perverso 5 % (NO PASA); prima ≤ p5 un 5 % y orden perverso en `oos2` otro 5 % (LIMBO) | curva de potencia por madre (`power_draws: 200`); sin corrida guardada | `marketSurfaces/verdict/call.py`, `thresholds.yaml` |
| 19 WFM | nominal: p− ≤ 0,05 el 5 % (NO PASA); mediana ≤ 0 la mitad de las veces (LIMBO ≈ 45 %); PASA ≈ 50 % | **no las declara** | `wfm/verdict/call.py:26-29` |

«Nominal» quiere decir «lo que sale del corte elegido si el nulo del estudio es correcto», no una medición. **Sólo el paso 17 tiene tasas medidas.**

### 2.3 La cuenta para las cuatro (calculado por mí)

Aritmética sobre la tabla anterior. Supuestos míos: las cuatro pruebas son independientes (ver abajo: no lo son); 18, 18.5 y 19 se comportan a su tasa nominal supuesta, no medida; el CSCV nunca falla por la P de pérdida (el supuesto más favorable a la madre, porque esa tasa no está declarada).

Hay un segundo supuesto que empuja al otro lado: se ha fijado en cero el NO PASA del CSCV por P de pérdida >= 0,5, cuya tasa sin ventaja no está medida (`optimisation/cscv/verdict/state.py:25`); si fuera positiva, DESCARTAR sube y REVISAR baja.

**Madre sin ventaja (Sharpe 0):**

- MANTENER = 0,020 (17) × 0,90 (18: ni NO PASA ni LIMBO) × 0,857 (18.5: 0,95³) × 0,50 (19) = **0,8 %**. Aunque las otras tres pasaran siempre, el paso 17 la deja en **2 % como mucho**.
- No falla ninguna = 0,523 (17) × 0,95 (18) × 0,95 (18.5) × 0,95 (19) = 44,8 %, luego **DESCARTAR ≈ 55 %**.
- **REVISAR ≈ 44 %**.

Las pruebas 17 y 19 no son independientes: las dos juzgan a la madre en los mismos 2,75 años de `oos2` (el propio código lo dice, `wfm/verdict/call.py:21`). Si una va mal, la otra tiende a ir mal. Además, 18 y 18.5 también leen `oos2` (el 18 en el segmento «build+oos1+oos2», el 18.5 en su bloque ciego de `oos2`) y 17, 18 y 18.5 leen el mismo lote de variantes de la madre: la dependencia no es sólo 17-19. Rangos (calculados por el revisor, rehaciendo la cuenta de arriba con cada supuesto):

- Cuatro pruebas independientes (extremo alto): DESCARTAR 55 %, MANTENER 0,8 %.
- 17 y 19 totalmente dependientes (el NO PASA del 19 dentro del del 17) y las otras dos independientes al 5 %: ninguna falla = (1 − 0,4767) × 0,95 × 0,95 = 0,472, luego DESCARTAR **52,8 %**; MANTENER ≤ 0,02 × 0,90 × 0,857 = 1,5 %; REVISAR ≈ 45,7 %.
- Las cuatro totalmente dependientes (extremo bajo): DESCARTAR 47,7 % (el NO PASA del 17 solo), MANTENER 2 %, REVISAR 50,3 %.

El resultado útil no cambia: **entre el 45 % y el 50 % de las madres sin ventaja se quedan, casi todas como REVISAR.**

**Madre con ventaja (Sharpe 0,5):** sólo el 17 declara algo, así que sólo puedo dar cotas.

- MANTENER ≤ **20 %** si el orden de sus variantes no se transmite fuera, ≤ **43 %** si se transmite. Las otras tres piezas sólo pueden bajarlo.
- DESCARTAR de una madre con Sharpe 0,5: al menos el **22 %** (el orden no se transmite) o el **9 %** (se transmite) por el 17 solo; a lo sumo 33 % y 22 % si las otras tres fallaran al 5 % y fueran independientes (cota superior bajo esos supuestos, no un valor esperado; con dependencia positiva, aún menos).

Con Sharpe 1,0 y orden que se transmite: MANTENER ≤ 92 %, DESCARTAR ≥ 0,3 %.

Lectura llana: **`peor` separa bien las dos colas (MANTENER casi nunca es una sin ventaja), pero el grueso de las madres, con o sin ventaja, cae en REVISAR**, y REVISAR hoy es «se queda».

### 2.4 El problema de buscar entre K: el reality check de White

Si pruebas 10 estrategias y te quedas con la mejor, esa mejor parece buena aunque ninguna valga: has elegido el máximo de 10 tiradas. La pregunta honrada no es «¿es buena la mejor?» sino «¿es la mejor más buena de lo que sería el máximo de 10 que no valen nada?».

White (2000) lo contesta así:

1. De cada estrategia se toma su **exceso diario** sobre el benchmark. La hipótesis nula: ninguna tiene exceso medio positivo.
2. El estadístico es **el mayor exceso medio** de las K.
3. Se fabrica el mundo en el que ninguna vale: a cada columna se le resta su propia media (queda con media cero) y se remuestrean los días, **los mismos días para todas las columnas**, para conservar lo que se parecen entre sí. De cada remuestreo se apunta el mayor exceso medio.
4. La p es la fracción de remuestreos en los que ese máximo supera al observado.

**Juguete (calculado por mí con el motor del paso, `juguete2.py`).** Tres estrategias, seis días de exceso en dólares:

| día | A | B | C |
|---|---|---|---|
| 1 | +3 | +1 | −4 |
| 2 | −2 | −2 | −2 |
| 3 | +1 | +1 | −6 |
| 4 | +3 | 0 | −1 |
| 5 | −1 | −1 | −3 |
| 6 | +2 | −1 | −2 |
| **media** | **+1,00** | **−0,33** | **−3,00** |

El estadístico observado es +1,00 (el de A). Se centra cada columna: a A se le resta 1, a B se le suma 0,33, a C se le suma 3. Un remuestreo: salen los días 4, 4, 1, 6, 2, 4. Con las columnas centradas, A da (2+2+2+1−3+2)/6 = +1,00; B da (0,33+0,33+1,33−0,67−1,67+0,33)/6 = 0,00; C da (2+2−1+1+1+2)/6 = +1,17. El máximo de ese remuestreo es **+1,17, y lo pone C**: la peor de las tres, una vez «perdonada» su media, es la que supera a A.

Con 1.000 remuestreos (bloque medio 1, es decir, días sueltos; semilla 0; error de simulación ≈ ± 1 punto), 107 superan +1,00: **p de White = 0,107**. Con A sola, la p es 0,073. La diferencia (0,073 → 0,107) es el precio de haber probado tres.

### 2.5 El SPA de Hansen: no pagar por las claramente malas

El defecto de White está a la vista en el juguete: C pierde 3 dólares al día y nunca podría ser «la mejor por azar», pero al centrarla en cero entra en el sorteo y sube el listón. Cuantas más estrategias malas se metan, más difícil lo tiene la buena. Es absurdo: añadir basura no debería quitar evidencia.

Hansen (2005) cambia a quién se centra, y da tres p:

| p | a quién centra en cero | qué supone |
|---|---|---|
| `upper` | a todas | la de White: el peor caso, cada mala cuenta en contra |
| `consistent` | a todas menos a las **claramente peores** que el benchmark | la que Hansen recomienda |
| `lower` | sólo a las que tienen media positiva | el suelo: ninguna mala cuenta |

«Claramente peor» tiene definición: su media está por debajo de −√(varianza/T × 2·ln ln T). Con T = 709 días eso es un estadístico t por debajo de −1,94.

En el juguete: C queda fuera (su umbral es −0,72 y su media −3,00); B se queda (umbral −0,49, media −0,33: es peor, pero no claramente). Resultado: `lower` 0,073, `consistent` **0,078**, `upper` 0,107.

Cómo leer las tres juntas: si `consistent` = `upper`, ninguna madre era lo bastante mala para descartarla del sorteo; si `lower` queda muy por debajo, hay madres con media negativa que pesan en el listón. En `Trade_NIKKEI225_M30_volatilidadL`: 0,648 / 0,902 / 0,902.

**El SPA dice «alguna» o «ninguna», no cuál.**

### 2.6 El StepM de Romano-Wolf: cuáles, por rondas

El StepM (2005) nombra. Usa el mismo sorteo, por rondas:

1. Ronda 1: se calcula el listón, que es el percentil 95 del máximo remuestreado (para un FWER de 0,05). Se **nombra** a toda estrategia cuya media lo supere.
2. Se retiran las nombradas y se repite con las que quedan. Con menos competidoras el máximo por azar es menor, el listón baja, y puede caer alguna más.
3. Se para cuando una ronda no nombra a nadie.

**FWER** (tasa de error de la familia) es la probabilidad de nombrar **al menos una** que en realidad no bate al benchmark. 0,05 quiere decir: de cada 20 veces que corra sobre madres que no valen, como mucho una nombrará a alguna.

En el juguete, el listón al 5 % es 1,33 y A tiene 1,00: **no se nombra a nadie**. Al 25 % el listón baja y se nombra a A; en la ronda 2 quedan B y C, con medias negativas, y se para.

En el código la bajada está escrita a mano sobre el SPA de la librería `arch` (`superior.py:79-103`) porque el `StepM` de `arch` 7.2.0 revienta cuando sus rondas nombran a todas, cosa que con 2 a 5 madres ocurre. Usa el listón `consistent`.

### 2.7 El bootstrap estacionario y la longitud de bloque

Los días de una estrategia no son independientes: hay rachas. Remuestrear días sueltos las rompe y hace parecer el azar más pequeño de lo que es. El bootstrap estacionario (Politis y Romano) remuestrea **tramos** de días seguidos de longitud aleatoria, con una media fija: el «bloque medio». Ejemplo: con bloque medio 3 sobre 9 días puede salir 4-5-6, 1, 7-8-9-1-2.

El bloque medio lo calcula la fórmula de Politis y White por columna, y se toma **la mediana de las columnas** para todo el panel (`superior.py:8-22`), porque se remuestrean los mismos días para todas. En las corridas guardadas salió 3 días (NIKKEI) y 1 día (USA500, USDJPY). Con bloque 1 el bootstrap es de días sueltos.

### 2.8 Qué es «buy & hold a igual riesgo»

El benchmark es comprar el activo el primer día de `oos2` y no tocarlo. Para que la comparación sea justa hay que decidir **cuántos lotes**: uno de más y el buy & hold gana por ir más apalancado.

«A igual riesgo» (`benchmark.py:23-27`): para cada madre, los lotes del buy & hold se eligen de modo que **su resultado diario sea igual de volátil que el de la madre**:

```
lotes  = desviación diaria de la madre / desviación diaria de 1 lote del activo
exceso = resultado diario de la madre − lotes × resultado diario de 1 lote
```

Con las dos volatilidades iguales, **un exceso medio positivo es exactamente «la madre tiene más Sharpe que el buy & hold»**. El paso 20 pregunta, por tanto, si el Sharpe de la madre supera al del activo.

Juguete. La madre se mueve 200 $ al día y gana de media 12 $; un lote del activo se mueve 40 $ y gana 2 $. Lotes = 200/40 = 5. El buy & hold a igual riesgo gana 5 × 2 = 10 $ al día. Exceso = +2 $. En Sharpe diario: 12/200 = 0,060 frente a 2/40 = 0,050; la diferencia, 0,010, es 2/200.

**Ejemplo real, recalculado sobre las curvas que guardó la corrida** (`Strategy 10.11.484`, `Trade_NIKKEI225_M30_volatilidadL`, 709 días de `oos2`; `juguete.py`): desviación diaria de la madre 288,78 $; la del buy & hold con 5,99 lotes, 288,78 $ (iguales, como debe); media de la madre 19,54 $ al día, del buy & hold 18,07 $; exceso **+1,47 $ al día**; Sharpe anual 1,074 frente a 0,993. Es la única de las 10 con exceso positivo. Su estadístico t es **0,11**: indistinguible de cero. La correlación entre sus días y los del buy & hold es 0,24.

Dos detalles de cómo se construye:

- El resultado diario de la madre no es la curva de SQX (que guarda el mínimo del día) sino el **cierre a cierre reconstruido** con sus operaciones y las barras M1 (`inputs.panel`, `inputs.py:132-156`). Se acepta sólo si los mínimos de esa reconstrucción coinciden con la curva de SQX, dentro de 1 $, en el 99 % de los días (mediana entre madres). Si no, el `report` se para.
- Una madre que no opera en `oos2` (desviación cero) se deja fuera del contraste y se avisa (`measure.py:71-72`).

**Cuánto Sharpe hace falta para que el StepM nombre a una madre (calculado por mí, `potencia_stepm.py`).** Datos sintéticos: 709 días, resultado diario normal e independiente, K − 1 madres con Sharpe 0 y una «buena»; 400 tiradas por caso, 500 remuestreos, FWER 0,05, con el propio código del paso (`benchmark.equal_risk` y `superior.stepm`). Error típico de cada cifra: hasta 2,5 puntos (intervalo del 95 %: hasta ± 4,9 puntos en p = 0,5 y ± 1,4 en p = 0,0025; calculado por el revisor, sqrt(p(1−p)/400)). La cifra de 0,3 % es 1 acierto en 400 tiradas.

| K | Sharpe del buy & hold | correlación madre-B&H | la buena con Sharpe 1 | Sharpe 2 | Sharpe 3 |
|---|---|---|---|---|---|
| 10 | 0 | 0 | 10 % | 50 % | 89 % |
| 10 | 0 | 0,5 | 19 % | 78 % | 99 % |
| 10 | 1 | 0 | 0,3 % | 10 % | 51 % |
| 10 | 1 | 0,5 | 1 % | 25 % | 86 % |
| 3 | 1 | 0 | 4 % | 18 % | 64 % |

(Probabilidad de que la buena sea nombrada.) Control (Sharpe del buy & hold = 0, todas las madres en 0; así están las dos filas `frontera` de `potencia_stepm.py`): el StepM nombró a alguna el 6,5 % de las veces con K = 10 y el 4,3 % con K = 3. No se ha hecho el control con el buy & hold a Sharpe 1. Repetición del revisor (200 tiradas, K = 10, buy & hold 0): 7,5 %, consistente con 5 % pero sin poder descartar un FWER real de 7-8 %.

Lo que dice la tabla: en `oos2` el buy & hold tuvo Sharpe 0,99 (NIKKEI), 1,17 (USA500) y 0,49 (USDJPY). **Una madre que sólo iguala al índice (Sharpe 1 frente a 1) no es nombrada en el 0,3-4 % de los casos, que es lo correcto: la simulación pone al buy & hold en Sharpe 1, así que esa madre no lo bate.** Para ser nombrada la mitad de las veces necesita un Sharpe real de 2,4 (correlación 0,5) a 2,7 (K = 3, correlación 0) o 3 (K = 10, correlación 0); la madre real de arriba tiene correlación 0,24. El contraste no falla: batir en Sharpe a un índice en años alcistas, con 2,75 años de datos, pide un Sharpe de 2,4 a 3. Supuestos que no se cumplen del todo en lo real: los días no son normales ni independientes.

Con colas gruesas (t de 4 grados) la potencia no cambia de forma medible; con autocorrelación 0,15 y volatilidad agrupada baja unos 5-7 puntos y el FWER medido queda en 7-8 % (200 tiradas por celda; calculado por el revisor con `benchmark.equal_risk` y `superior.stepm`, 500 remuestreos, K = 10, una sola semilla y una sola configuración de dependencia, error típico ≈ 3,5 puntos: orden de magnitud, no medida). Ejemplo: buy & hold 1 y Sharpe 3, 47,5 % con normales, 46,0 % con t(4), 40,0 % con t(4) + autocorrelación + volatilidad agrupada. La tabla es, por tanto, un techo de lo que el contraste nombraría con datos reales.

### 2.9 Qué gasta de `oos2`

`oos2` es el último tramo fuera de muestra (2024 a 2026-09-30 en índices, 2023 a 2026-09-30 en divisas). «Gastarlo» es mirarlo y decidir con lo visto: cada mirada que influye en qué estrategia sigue lo hace un poco menos fuera de muestra.

El paso 20 lo toca de dos maneras:

- **Indirecta, y es la que decide.** Los estados que combina ya llevan `oos2` dentro: el 17 juzga sobre `oos2`, el 19 también, el 18 lo usa junto al resto del histórico, y el 18.5 lo usa para añadir LIMBO. La regla `peor` es una decisión tomada sobre `oos2`.
- **Directa, y hoy no decide.** El SPA/StepM lee los días de `oos2` de cada madre. Cada ejecución escribe una fila en el ledger (`report.py:23-54`): paso 20, tramo `oos2`, cuántas entraron y cuántas quedan, y el Sharpe diario medio, su desviación y su máximo.

Quién puede: `assets/_policy.yaml:48` reserva `oos2` para `WFC, CSCV, MarketSurfaces, WFM, BlindJoint, ATRStop` (`BlindJoint` sólo en el árbol de trabajo; no está en `HEAD`). La reserva sólo ata a un agente autónomo; a un humano nunca se le niega (`gate.py:68-69`). Como `BlindJoint` está en la lista, **hoy nadie encuentra cerrado `oos2` para el paso 20**; lo único que puede dejar sin SPA es que falten las operaciones de la madre o que ninguna madre esté completa.

Lo ya gastado, contado en los ledgers (filas con `oos2`):

| estudio | 17 | 18 | 18.5 | 19 | 20 | 24 |
|---|---|---|---|---|---|---|
| `NIKKEI225_M30_simple_long` | 60 | 70 | 60 | 6 | **6** | 11 |
| `USA500_H1_indicesIBS` | 6 | 6 | 6 | 2 | 1 | 2 |
| `USDJPY_M30_doubleROCLong` | 6 | 6 | 4 | 2 | 2 | 4 |
| `USDJPY_H1_donchianUpperCrossUp` | 22 | 37 | 51 | 1 | 4 | — |

(En 17, 18 y 18.5 hay una fila por madre y tramo; en 19 y 20, una por ejecución.)

---

## 3. Lo que calcula, pieza a pieza

### 3.1 La población y quién está completa

`pieces.population` (`pieces.py:71-100`). El nombre de la madre sale del nombre de la carpeta del lote cambiando `_` por espacio (`pieces.py:31`); el lote no guarda la identidad, así que el cruce con la WFM es **por nombre**.

Ejemplo real: en `Test_USA500_H1_indicesIBS` hay seis carpetas de lote y la WFM sólo trae tres madres. Las otras tres (`16.25.255`, `19.10.435`, `8.10.355`) son lotes de un sorteo anterior del mismo proyecto. Salen como INCOMPLETA («le falta WFM»), con `verdict` MANTENER.

### 3.2 Los estados: `states`

Una tabla de madres × cuatro piezas con `pass`/`watch`/`fail` (`measure.states`, `measure.py:12-23`). Es lo único que usa `peor`.

Lo guardado (reglas antiguas), 26 madres completas:

| corrida | madres | con algún `fail` | con la regla `peor` aplicada a los estados antiguos (no vale como previsión) |
|---|---|---|---|
| `Trade_NIKKEI225_M30_volatilidadL` | 10 | 10 (las 10 fallan superficies) | 10 DESCARTAR |
| `Test_NIKKEI225_M30_simpleL_fin` | 10 | 10 (las 10 fallan superficies) | 10 DESCARTAR |
| `Test_USA500_H1_indicesIBS` | 3 | 3 | 3 DESCARTAR |
| `Test_USDJPY_M30_doubleROCLong` | 3 | 3 (las 3 fallan la WFC) | 3 DESCARTAR |

Coste, pues, sobre lo guardado (estados de la regla `sin_fallo`): **26 de 26**. No vale como previsión: el `fail` de superficies era la regla «no viaja», que ya no existe (hoy sólo falla un orden perverso), y la WFC y la WFM también cambiaron de tabla.

### 3.3 El panel de exceso, los lotes y el Sharpe

`measure.run` (`measure.py:70-93`). Por madre: `lots_bh`, `sharpe` (media/desviación × √252 de sus días de `oos2`), `excess_day` (exceso medio en $ al día) y `named_all` (si el StepM sobre todas la nombra). Para el activo: `sharpe_bh`.

Real, `Trade_NIKKEI225_M30_volatilidadL` (709 días, bloque 3, K = 10, Sharpe del buy & hold 0,993):

| madre | Sharpe | exceso $/día | lotes B&H | nombrada |
|---|---|---|---|---|
| 10.11.484 | 1,07 | +1,47 | 5,99 | no |
| 4.13.338 | 0,87 | −4,08 | 10,75 | no |
| 13.3.390 | 0,70 | −4,24 | 4,84 | no |
| 15.9.352 | 0,34 | −13,12 | 6,61 | no |
| 14.3.479 | 0,32 | −10,41 | 5,06 | no |
| 3.9.284 | 0,21 | −17,73 | 7,47 | no |
| 16.5.352 | 0,19 | −25,07 | 10,29 | no |
| 3.11.426 | 0,16 | −17,16 | 6,78 | no |
| 19.2.363 | −0,10 | −17,39 | 5,23 | no |
| 18.5.355 | −0,30 | −23,83 | 6,08 | no |

Los lotes van de 4,84 a 10,75: la madre más volátil mueve al día 2,2 veces lo que la menos. Importa en §5.1.

### 3.4 El SPA

`superior.spa` (`superior.py:25-52`): las tres p de «ninguna madre bate al buy & hold». Guardado:

| corrida | K | días | bloque | lower | consistent | upper |
|---|---|---|---|---|---|---|
| `Trade_NIKKEI225_M30_volatilidadL` | 10 | 709 | 3 | 0,648 | 0,902 | 0,902 |
| `Test_NIKKEI225_M30_simpleL_fin` | 10 | 709 | 3 | 0,499 | 0,731 | 0,731 |
| `Test_USA500_H1_indicesIBS` | 3 | 709 | 1 | 0,547 | 0,815 | 0,815 |
| `Test_USDJPY_M30_doubleROCLong` | 3 | 974 | 1 | 0,403 | 0,579 | 0,579 |

En las cuatro, `consistent` = `upper`: ninguna madre era «claramente peor». En ninguna hay indicio de batir al buy & hold.

Nuevo desde hoy (sin confirmar, `report.py:137-139`): los 1.000 valores del máximo remuestreado bajo cada p se guardan en `distribuciones.parquet` con el observado. Ninguna corrida lo tiene aún.

### 3.5 El StepM, una vez por lectura

`measure.py:76-80`: seis StepM (uno por columna de `readings.csv`), todos con el mismo bloque y la misma semilla; sólo cambia sobre qué madres se cuenta. Las cuatro columnas `+entrantes` son el mismo cálculo repetido (`measure.py:76-80`); sólo las dos `+supervivientes` difieren.

En las cuatro corridas guardadas: cero nombradas bajo cualquier lectura.

### 3.6 `readings.csv` y `verdict.csv`

- `readings.csv`: madres completas × seis lecturas. Bajo `peor` la celda es `pass`, `watch` o `fail`; bajo las otras, `pass`, `fail` o `none` (StepM sin leer) (`readings.py:75-100`).
- `verdict.csv`: una fila por madre, completa o no, con `strategy`, `identity`, `verdict` (DESCARTAR, REVISAR o MANTENER), `reason` y los cuatro estados (`report.py:57-72`).

### 3.7 La fila del ledger

Sólo si se leyó `oos2` (`report.py:142`). `n_in` = madres completas; `n_out` = las que la lectura elegida no descarta (bajo `peor`: MANTENER más REVISAR, `report.py:47`); `criterion` = `blindJoint/peor+entrantes`; en la nota, cuántas pasan por cada lectura, las tres p y el Sharpe del buy & hold.

Real (`USA500_H1_indicesIBS`, 2026-10-06, lectura de ayer): `n_in 3`, `n_out 0`, `criterion blindJoint/sin_fallo+entrantes`, SPA 0,547 / 0,815 / 0,815, Sharpe del buy & hold 1,166.

### 3.8 Los hechos que ve el juez del autopiloto

El juez del paso 20 recoge del resultado (`facts.gather`): `blindJoint.summary.complete` (1/0), `blindJoint.verdict.pass` (1 sólo si el estado es `pass`), `blindJoint.verdict_csv.drop` (1 si DESCARTAR), el valor de cada parte y la tabla del buy & hold (Sharpe de la madre, del activo, lotes, exceso). En `USA500` fueron 36 hechos para 6 madres (`autopilot/…/20261006-182925/paso-20/hechos.parquet`). El estado de cada pieza no llega como número; las tres lecturas no elegidas, tampoco.

### 3.9 `ledger.backfill --blind`

`python3 -m ledger.backfill --blind <P> --symbol S --timeframe TF --family F [--write]` reconstruye las filas de 17, 18 y 19 que falten en el ledger a partir de los resultados en disco (`ledger/blind.py:95-117`), marcadas `backfill`, una por tramo (`build`, `oos1`, `oos2`). Sin `--write` sólo imprime; con `--write` se niega si el estudio ya tiene filas de alguno de esos pasos (`backfill.py:152-154`).

**Hoy ya no hace falta en una corrida normal.** Los tres estudios se apuntan solos: la WFC (`wfc/report.py:79`), el CSCV (`cscv/report.py:132`) y la WFM (`ledger/steprows.py:61-83`). El autopiloto, además, tiene su propia versión (`blind.register`, `pipeline/autopilot/blind.py:98-130`), que en la corrida de `USA500` contestó «17, 18 y 19 ya tenían sus filas». Queda para corridas anteriores a esas fechas (WFC y CSCV, 2026-09-27; WFM, 2026-10-04).

Un detalle: para el 18 lee `<lote>/cscv.json` (`ledger/blind.py:68-73`), y el CSCV nuevo ya no escribe ese fichero. En un lote nuevo sin filas propias no reconstruiría nada del 18. Con las filas vivas no tiene efecto.

---

## 4. El criterio cargado y por qué

### 4.1 En `criteria.yaml`

| paso | línea | `cut` | reglas |
|---|---|---|---|
| 16.5 | 230 | `null` | ninguna (fábrica y nube: no cortan) |
| 17 | 234 | `null` | `wfc.c1.estado`: ≥ 1 PASA, ≥ 0 LIMBO, si no NO PASA; sin dato LIMBO |
| 18 | 251 | `null` | `cscv.p_perdida` < 0,5 o NO PASA · `cscv.p_perdida_sobre_p95` < 1 o LIMBO · `cscv.pbo_sobre_p95` < 1 o NO PASA; sin dato LIMBO |
| 18.5 | 268 | `null` | `orden.estado` ≥ 0 o NO PASA · `prima.bajo_p5` < 1 o LIMBO · `oos2.perverso` < 1 o LIMBO · `oos2.sin_dato` < 1 o LIMBO |
| 19 | 287 | `null` | `wfm.l1.p_menos` > 0,05 o NO PASA · `wfm.l1.mediana_exceso` > 0 o LIMBO · dos reglas de `reoptimizado` que sólo añaden LIMBO |
| **20** | — | — | **no hay entrada** |

`cut: null` significa «juzga y escribe, no borra nada en SQX» (`judge.py:179-183` y `203`): el juez de 17, 18, 18.5 y 19 deja `hechos.parquet`, `verdict.csv` y una fila en el ledger, y todas las madres siguen.

Estas reglas dicen lo mismo que las tablas de los estudios de §1.3 (lo he cotejado regla a regla), pero **el paso 20 no las lee**: lee el estado que escribió cada estudio.

### 4.2 En el estudio

La regla del paso 20 son las tres líneas de `readings.worst` y el mando `joint.pieces: peor`. No hay ningún umbral numérico propio salvo el FWER 0,05 del StepM, que bajo `peor` no decide.

Por qué `peor`, según lo escrito: es provisional «hasta que el dueño rediseñe el paso 20» (`config.yaml:26-29`, WORKFLOW fila 20). La decisión anterior (`sin_fallo`, 2026-10-04) exigía ser nombrada por el StepM, y nadie lo fue nunca.

### 4.3 ¿El DESCARTAR se aplica hoy? No: sólo se anota

La cadena, paso a paso:

1. El plan del autopiloto mete siempre un «juicio» tras el paso 20, tenga reglas o no (`tail.py:104`).
2. El juez busca la entrada «20» en `criteria.yaml`. No existe, y el sorteo de desarrollo sólo actúa en el paso 8. Sale por `judge.py:175-176`: escribe los hechos y devuelve «ninguno: el paso no tiene criterio».
3. Los pasos 21 a 25 toman sus madres del databank que cortó el último paso con `cut` (`survivors.py:14` y `21-30`). Como ni 17-19 ni 20 cortan, sigue siendo «SPP OOS», el del paso 16.

Prueba, `autopilot/Test_USA500_H1_indicesIBS/20261006-182925/resumen.md`:

```
| 20 | joint | 5 | blindJoint sobre el estudio USA500_H1_indicesIBS |
| 20 | judge | 0 | 36 hechos; ninguno: el paso no tiene criterio |
| 23 | structural | 40 | 3 madre(s) …
| 25 | finalists | 0 | 3 finalista(s) …
```

Las tres estaban en DESCARTAR (regla antigua `sin_fallo+entrantes`). Con el código de hoy el DESCARTAR seguiría sin aplicarse (no hay entrada «20»); que esas tres cayeran en DESCARTAR es de la regla antigua.

El `verdict.csv` está en el formato de `/curate`, así que a mano sí se puede aplicar. `survivors.py:14` ya prevé que el paso 20 tenga `cut` «el día que el dueño le dé reglas».

### 4.4 Qué haría falta para escribir la regla «20»

No propongo ninguna; esto es lo que hay y lo que falta:

- **Hechos disponibles:** `blindJoint.verdict_csv.drop` (1 = DESCARTAR) y `blindJoint.verdict.pass` (1 = MANTENER). Con los dos se distinguen los tres veredictos.
- **Falta decir qué databank se corta** (`cut`). Los pasos 21-25 leen «SPP OOS»; 23 y 24 fabrican lotes desde ahí.
- **Falta decidir qué es REVISAR para el corte:** hoy es «se queda».
- **Las INCOMPLETAS** llegan sin hecho de veredicto: con la gramática actual, un hecho que falta es LIMBO.

---

## 5. Lo que no cuadra o no está medido

### 5.1 El SPA no está estandarizado, y el código cree que sí

`measure.py:61-62` y el README del motor (`engines/inference/snooping/README.md:38-39`) hablan de «studentize»: dividir el exceso medio de cada madre por su error, para compararlas en la misma escala. En la librería instalada (`arch` 7.2.0, `arch/bootstrap/multiple_comparison.py:668` y `692`) el estadístico es **la media en bruto**, en dólares por día; la varianza sólo se usa para decidir quién es «claramente peor».

Comprobado (calculado por mí, `juguete.py`): 709 días, dos columnas, una con ventaja clara (t ≈ 4) y otra de puro ruido. Con el ruido a la misma escala, el StepM nombra a la buena en el 98-100 % de las veces; con el ruido 20 veces más volátil, entre el 5 y el 12 % (100 y 300 semillas, calculado por mí y por el revisor).

En el paso 20: la escala de cada columna es la volatilidad en dólares de cada madre, y entre las 10 de `Trade_NIKKEI225` varía por 2,2. La madre que más se mueve pesa más en el listón de todas. No cambia ningún resultado guardado (nadie estuvo cerca de ser nombrada), pero el contraste no es el que se describe.

La arquitectura de la librería lo confirma (comprobado por el revisor: `multiple_comparison.py:668` toma `loss_diff.mean(axis=0)` y `:692` resta la media en bruto; la varianza sólo entra en `_check_column_validity`, `:737`; `studentize` sólo rotula `_info`). Era la afirmación de la que convenía pedir una segunda lectura: la saco del código de la librería y de una prueba, no de su documentación.

### 5.2 Dos documentos dicen sin matiz que el paso 20 no puede leer `oos2`

- `studies/closing/blindJoint/README.md:47-51`: «Step 20 is not listed, so today the SPA half is not read».
- Manual `56-paso-20.md:168-170` y `185`.
- WORKFLOW, fila 20 («el SPA sobre `oos2` se lee para un humano; sólo un agente autónomo lo encuentra cerrado») y el comentario de `ledger/gate.py:18-21` (habla de «la palabra que el dueño añadiría», sin afirmar que esté cerrado) siguen listando `BlindJoint` como ausente de `reserved_for`, que en disco ya no es cierto. La reserva sólo ata con `ALGO_AUTONOMOUS=1`, que el autopiloto pone (`run.py:235`).

En disco, `assets/_policy.yaml:46-48` lo lista con la nota «añadido por el dueño el 2026-10-04». En `HEAD` no. Las cuatro corridas de octubre leyeron `oos2` en el paso 20.

### 5.3 «17-19 no se apuntan solos» ya no es cierto (WFC y CSCV desde el 2026-09-27, WFM desde el 2026-10-04)

`README.md:65-67` y WORKFLOW fila 20 («antes, `ledger.backfill --blind`»). Se apuntan los tres (§3.9). El manual `56:39-52` sigue poniendo el `backfill` como paso previo obligado.

### 5.4 El README describe los estados antiguos

`README.md:71-72` nombra `no_fiable/indeciso/fiable`, «PBO over 0.5», `no viaja/a medias/viaja` y `perverse/blind/predicts`. Hoy son `pasa/limbo/no_pasa` en las cuatro. La tabla «What it found the first time» (líneas 92-103) es del 2026-09-26 con esas palabras.

### 5.5 El manual dice que el `report` se niega; bajo `peor` no

`56-paso-20.md:33-34`: «`report` sigue negándose a una lectura elegida si `oos2` o las operaciones de la madre están vetados». `report.py:75-79` exime a `peor`. El manual es del 2026-10-07 23:26; el cambio, del 2026-10-08.

### 5.6 WORKFLOW dice que el paso 17 no pide significancia

Fila 17: «sin pedir significancia (`p_nivel` se anota y ya no decide)». El código (`wfc/verdict/state.py:56`) y el comentario de `criteria.yaml` («dueño, 2026-10-08: el nivel LLEVA significancia») dicen lo contrario. No es un matiz para el paso 20: sin la significancia, el PASA del 17 para una madre sin ventaja sería 0,49 en vez de 0,02 (lo mide la propia calibración), y el MANTENER de §2.3 pasaría de menos del 2 % a cerca del 20 %.

### 5.7 Dos tablas para los mismos estados

El README dice «A piece's threshold lives in its study» (línea 69). Pero `criteria.yaml` repite los mismos cortes (`< 0.5`, `> 0.05`, los tres valores del estado) para el juez de cada paso. El `verdict.csv` del paso 17 lo escribe el juez con `criteria.yaml`; el DESCARTAR del paso 20 sale del estado del estudio. Un cambio en uno solo de los dos sitios los separa sin que nada avise.

### 5.8 El ledger dice una cosa y SQX otra

La fila del paso 20 apunta `n_out` como si la lectura cortara (0 de 3 en `USA500`), y las tres madres siguieron. Quien lea el embudo del ledger verá cero supervivientes donde hubo tres finalistas.

### 5.9 Cada ejecución es otra mirada, y K sólo cuenta las de esa ejecución

`NIKKEI225_M30_simple_long` tiene seis filas del paso 20 en dos días, de seis proyectos, cada una con K = 10: sesenta madres del mismo activo y los mismos años contrastadas en seis tandas de diez. El StepM paga por 10. El README del motor lo dice («It only corrects for the K it sees»); el paso no lo avisa. Repetir el `report` sobre el mismo proyecto también añade fila (`USDJPY_M30_doubleROCLong` tiene dos).

### 5.10 Lotes viejos como madres incompletas

`pieces.batches` (`pieces.py:19-31`) lista todas las carpetas del proyecto, también las de corridas anteriores. Aparecen como INCOMPLETA con `verdict` MANTENER (3 de 6 filas en `USA500` y en `USDJPY doubleROC`). No rompe nada hoy; con una regla «20» serían tres LIMBO que no existen en el databank.

### 5.11 Nada comprueba de qué versión es cada pieza

`pieces.said` (`pieces.py:64-66`) usa el `estado` nuevo de la WFC si está y, si no, el `verdict.state` que haya. Relanzar hoy el paso 20 sobre `Trade_NIKKEI225_M30_volatilidadL` mezclaría la WFM releída el 2026-10-07 (regla nueva) con WFC, CSCV y superficies del 2026-10-04 (reglas antiguas) sin aviso.

### 5.12 La puerta ciega no pide el 18.5

`gate.BLIND = (17, 18, 19)` (`gate.py:24`). Que una madre esté completa sí exige su JSON de superficies, así que el efecto es pequeño: la puerta se abre sin fila del 18.5 en el ledger.

### 5.13 Menores

- El texto «sin leer: la política no deja al paso 20 mirar oos2» está fijo en `one.py:27-28`, aunque el motivo real sea que faltan las operaciones o que no hay ninguna madre completa.
- El Sharpe se anualiza con 252 días (`measure.py:9`) y el feed trae 258 a 260 filas por año: sale un 1 % a 2 % por debajo, igual para la madre que para el buy & hold.
- El test de respuesta conocida (`tests/test_blindjoint.py:45-52`) planta un Sharpe **diario** de 0,25 (anual ≈ 4) sobre 1.250 días. Demuestra que la máquina nombra una ventaja enorme; no dice nada de ventajas realistas en 709 días (§2.8).

### 5.14 Lo que no está medido

- **Ninguna corrida con el código de hoy.** No hay un solo reparto real MANTENER / REVISAR / DESCARTAR bajo `peor`.
- **Las tasas de 18, 18.5 y 19** con y sin ventaja: sólo el 17 tiene calibración. La cuenta de §2.3 es mía y descansa en tasas nominales.
- **Cuánto se parecen los cuatro estados entre sí** en madres reales (17 y 19 comparten `oos2`).
- **La cadena entera con una población sin ventaja** (el recordatorio del mono de punta a punta, WORKFLOW): es lo único que diría cuántas sin ventaja llegan a MANTENER o a REVISAR de verdad.
- No he ejecutado `tests/test_blindjoint.py` ni el `report`.

### 5.15 Las probabilidades de `peor` descansan en tasas supuestas y en independencia

Las cifras de §2.1, §2.3 y §6 (0,8 %, 55 %, 44 %, 22 %/9 %, 33 %/22 %) salen de tasas nominales supuestas para 18, 18.5 y 19 y de que las cuatro pruebas sean independientes. Las cuatro leen la misma madre, así que con dependencia positiva MANTENER sube (la cota de 2 % del 17 sigue valiendo) y DESCARTAR baja respecto a cada una de esas cifras; REVISAR sube. Los ejemplos de juguete de §2.1 (64 %/19 % y 41 %/34 %) quedan, con dependencia, más generosos con las buenas. Por el otro lado, la tasa de NO PASA del CSCV por P de pérdida está fijada en cero (§2.3); si fuera positiva, DESCARTAR sube. Ninguno de los dos efectos está medido.

### 5.16 La tabla de potencia del StepM es un techo

La tabla de §2.8 tiene error típico de hasta 2,5 puntos (intervalo del 95 %: ± 4,9), su control de FWER se hizo sólo con el buy & hold a Sharpe 0 (no a Sharpe 1, donde se apoyan §0 cosa 4 y §6.4-6.5), y con autocorrelación 0,15 y volatilidad agrupada la repetición del revisor da unos 5-7 puntos menos de potencia y un FWER del 7-8 % (200 tiradas, una configuración; calculado por el revisor). `tests/test_blindjoint.py:54-56` ya usa t(4), pero con 20 semillas y umbral de más de 3 falsos: no distingue un 5 % de un 8 %.

### 5.17 Las cifras de las corridas antiguas son de la regla `sin_fallo`

Los 26 DESCARTAR de cuatro corridas y los 3 de `USA500` salieron de la regla `sin_fallo+entrantes` con los estados antiguos de las piezas (la columna `reason` de los `verdict.csv` dice «lectura sin_fallo+entrantes: No pasa»), no de `peor`. Aquí es inocuo —las 26 tienen además algún `fail`—, pero ninguna cifra guardada es un resultado de `peor`.

### 5.18 El DESCARTAR sigue sin aplicarse y `peor` sólo está en el árbol de trabajo

No hay entrada «20» en `criteria.yaml` (§4.3), y la regla `peor`, `BlindJoint` en `_policy.yaml:48` y los once ficheros de `blindJoint` sólo existen en el árbol de trabajo; en `HEAD`, `config.yaml` dice `sin_fallo`. Comprobado por el revisor a las 10:15 UTC del 2026-10-08: ningún fichero del alcance con hora posterior a 09:34:47.

---

## 6. Cierre: las decisiones que quedan

Cada una con lo que gana y lo que cuesta. No hay cifras reales bajo `peor`; donde doy una, digo de dónde sale.

**1. ¿Se aplica el DESCARTAR del paso 20?** Hoy no. Aplicarlo es dar entrada «20» a `criteria.yaml` con su `cut`.
- *Gana:* los pasos 21 a 26 dejan de gastar tiempo en madres que el propio workflow ha tumbado, y el ledger y SQX dirían lo mismo.
- *Cuesta:* sobre lo guardado (reglas antiguas, `sin_fallo`, no `peor`), 26 de 26. Con las tasas nominales supuestas y las cuatro pruebas independientes (extremo alto), en torno al 55 % de las madres sin ventaja (entre el 48 % y el 55 %, con independencia como extremo alto; calculado por el revisor); en las de Sharpe 0,5, al menos el 22 % o el 9 % (por el 17 solo) y a lo sumo 33 % y 22 % si las otras tres fallaran al 5 % e independientes. Con dependencia positiva, menos. Es la primera decisión de la cadena que cortaría con `oos2`.

**2. ¿Qué es REVISAR?** Hoy, «se queda».
- *Si sigue quedándose:* pasan MANTENER y REVISAR, es decir, entre el 45 % y el 50 % de las madres sin ventaja (independencia y dependencia total como extremos; calculado por el revisor).
- *Si se cortara:* sólo pasan las MANTENER: entre el 0,8 % y el 2 % de las sin ventaja (con dependencia positiva, más cerca del 2 %), pero también menos del 20 % al 43 % de las que tienen Sharpe 0,5.
- No hay punto intermedio escrito. Es la decisión con más efecto de las siete.

**3. ¿Se queda `peor`, o qué la sustituye?** Es provisional por escrito. Lo que este dossier aporta para el rediseño: MANTENER exige cuatro PASA y sólo el 17 pide evidencia a favor; los otros tres PASA son vetos levantados. El estado final lo fija casi siempre el 17.

**4. ¿Sigue calculándose el SPA/StepM mientras no decida?**
- *Gana si sigue:* la tabla de cada madre contra el buy & hold, que es información que ningún otro paso da.
- *Cuesta:* una mirada a `oos2` por ejecución, apuntada en el ledger, para un contraste que con un buy & hold de Sharpe 1 no nombra a una madre que sólo lo iguala (Sharpe 1) en el 0,3-4 % de los casos, que es lo correcto (calculado por mí); con datos reales, techo (§5.16).

**5. Si el StepM vuelve a decidir algún día: ¿contra qué benchmark y sobre qué K?** Contra el buy & hold a igual riesgo, en índices alcistas pide Sharpe ≈ 3. Y K es hoy las madres de una ejecución, no las del estudio (seis tandas en NIKKEI).

**6. ¿Se corrige la estandarización del SPA (§5.1)?** Es de ingeniería, pero cambia qué contrasta el paso: hoy pesa más la madre más volátil.

**7. Lo que conviene confirmar o corregir cuanto antes, por ser barato:**
- Confirmar en git el módulo entero: `HEAD` tiene `report.py` nuevo con `readings.py` y `config.yaml` viejos.
- Poner de acuerdo README, manual 56, WORKFLOW y `gate.py` con `_policy.yaml` (§5.2), con el ledger en vivo (§5.3) y con la significancia del 17 (§5.6).
- Decidir si el paso 20 debe leer sólo los lotes de la corrida en curso (§5.10) y negarse a mezclar piezas de versiones distintas (§5.11).

**Lo que haría falta para fijar cualquiera de las tres primeras con datos:** una corrida real con el código de hoy, y la cadena 17-20 pasada por una población sin ventaja.
