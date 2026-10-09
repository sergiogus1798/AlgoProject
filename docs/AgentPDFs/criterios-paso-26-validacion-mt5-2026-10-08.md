# Paso 26 — Validación en MT5 con la feed de cada empresa de fondeo: qué se compara, con qué cuentas y qué criterio hay cargado

**Fecha:** 2026-10-08 · **Para:** el dueño, que va a fijar los criterios él mismo · **Alcance:** sólo el paso 26 (`mt5/verify/`, `mt5/compare.py`, `sqx/projects/mt5verify.py`, `ui/daemon/mt5bridge/`, el pool de `AlgoData/pool/`).

Revisado por dos miembros del Council (Feynman, Taleb) el 2026-10-08; correcciones aplicadas.

**Qué es:** el documento de consulta del paso 26, con la misma forma que los de los pasos 8, 10 y 16. Explica desde cero por qué un backtest de SQX y uno de MT5 de la misma estrategia no dan lo mismo, qué traduce el código para cada empresa, cómo empareja las operaciones, las seis cifras que calcula con su fórmula y su `fichero:línea`, los siete umbrales cargados, y cierra con lo que no cuadra y con las decisiones que te quedan.

**Commit descrito:** `b2b4c8c`. **Ficheros del paso con cambios sin confirmar:** `mt5/verify/autopilot.py`, `mt5/verify/pool.py` y sus tests (`tests/test_mt5_pool.py`, `tests/test_mt5_autopilot.py`) están sin añadir a git (nunca se han confirmado); el resto de `mt5/verify/`, `mt5/compare.py`, `mt5/tester.py`, `mt5/report.py`, `sqx/projects/mt5verify.py`, `ui/daemon/mt5bridge/` y las claves `mt5verify.*` de `ledger/thresholds.yaml` están como en el commit.

**De dónde salen los números.** Hay 27 carpetas en `AlgoData/mt5/verify/`; 18 terminaron (34 comparaciones estrategia × empresa) y 9 se cayeron o se cancelaron. Uso dos:

- **Ejemplo principal — la corrida del autopiloto del 2026-10-04** (21:22 a 21:46): cinco finalistas de `Trade_NIKKEI225_M30_volatilidadL` (`S00V014` a `S04V014`, cada una su madre con el stop del paso 24 injertado), NIKKEI225 M30, largas, ventana 2024-01-01 → 2026-09-30, modelo del tester «every tick», en FTMO y en Hantec. La sexta (`S05V014`) se canceló desde la ventana. Es la corrida más reciente y está hecha con el código de hoy (ningún fichero del paso es posterior). **He recalculado las seis cifras de las diez comparaciones desde las operaciones guardadas en disco y coinciden con las guardadas en todos los decimales** (`recalc.py`, en mi carpeta temporal).
- **Ejemplo secundario — `Strategy 16.9.76`, USDJPY H1, 2026-09-30** (ventana 2022-06-01 → 2026-09-24, modelo «OHLC M1»): una de las dos estrategias con un «Validada» guardado (la otra es `10.9.72`; las dos sólo en FTMO, en Hantec ninguna; uso `16.9.76`). Es anterior a dos cambios: el valor de punto del USDJPY pasó de 653,92 a 631,34 el 2026-10-01 y su feed pasó del reloj de Israel al de EETUS. Recalculada con la ficha de hoy, las filas 1, 2 y 3a salen idénticas y las 3b, 4 y 5 cambian en el cuarto decimal o por el factor 631,34/653,92. Cito las cifras guardadas.

Estas estrategias **no son supervivientes reales** de los pasos 1-25: las del NIKKEI salieron de un sorteo en el paso 8 (dossier del paso 16) y las del USDJPY son madres de un proyecto `Test_`. Sirven para ver la mecánica, no para juzgar el paso.

**Sobre `oos2`.** La ventana del NIKKEI es exactamente `oos2` (el ledger lo anota así). Todo lo que añado yo —marcado «calculado por mí»— mide el **acuerdo entre SQX y MT5** y no propongo ningún umbral a partir de ello. Pero el paso sí enseña rendimiento de `oos2` (revisión de Taleb): la ventana del NIKKEI es exactamente `oos2` y el ledger anota diez lecturas (`NIKKEI225_M30_mt5verify`; 22 con `oos1+oos2` en `USDJPY_H1_mt5verify`). Por diseño (encargo 34, líneas 19-22) `oos2` ya está gastado cuando se llega aquí y el veredicto no elige por rendimiento; pero la curva de P&L de la pestaña, el informe de MT5 y varias tablas de este documento muestran rendimiento. Cada repetición es otra mirada; sin límite de repeticiones, tampoco lo hay de miradas.

**Ninguna línea de este documento está congelada.** Los siete umbrales son «valores de partida aceptados» el 2026-09-29, parámetros de entrada que una corrida puede cambiar con `--set`.

---

## 0. En una página

**La pregunta del paso.** El histórico largo de SQX (15 años) ¿vale para la cuenta de esta empresa? Se contesta comparando, en el tramo en que las dos fuentes tienen datos, el backtest de SQX con los costes de esa empresa contra el backtest en MT5 del EA que SQX exporta, en la cuenta de esa empresa. No elige por rendimiento.

**Lo que un «Validada» demuestra y lo que no** (revisión de Taleb). Demuestra que el EA exportado, en el tester de MT5 de esa empresa, abre las operaciones en las mismas barras que SQX y mueve un precio parecido, en el tramo común (2,75 años en el NIKKEI). No demuestra que la estrategia gane, ni que el histórico de 15 años valga (no se compara, y el retest de SQX se corrió con otros costes: spread 304,11 y deslizamiento 106,44 en la tabla de parámetros frente a 1.000 y 0 de FTMO, 700 y 0 de Hantec en `S00V014`), ni nada de la ejecución real: las dos partes son simulaciones sin deslizamiento, sin rechazos y sin huecos, y el EA comparado no lleva el filtro de noticias. «Validada» significa «el tester de MT5 coincide con SQX», no «apta para operar». (El texto que el dueño lee en la ventana, `judge.py:154-155`, dice «SQX reproduce lo que el EA hace en su cuenta: el histórico largo de SQX vale para ella»; es el tester de esa cuenta, no la cuenta.)

**Lo que hay cargado hoy.** Seis comprobaciones (las «cinco filas» del encargo 34; la 3 son dos) contra siete umbrales de `ledger/thresholds.yaml`. «Validada» = pasan las seis (`mt5/verify/judge.py:151`). No hay ninguna regla en `pipeline/autopilot/criteria.yaml` ni ningún hecho en `facts.py`: el paso juzga dentro de su propio módulo. No existe el estado Limbo: una cifra que no se puede calcular falla (`judge.py:95`).

**Lo que sale en la corrida real.** NIKKEI225, cinco finalistas × dos empresas: **las diez «No validada»**. Emparejan entre el 46 % y el 88 % de las operaciones (el umbral es 95 %). El pool validado tiene diez líneas y **cero estrategias validadas**. En USDJPY, `16.9.76` valida en FTMO (95,9 % emparejadas) y falla en Hantec sólo por la fila 5.

Este 0 de 10 está sin diagnosticar: no se sabe si fallan las estrategias, la traducción (spread leído en domingo, alineación de barras del feed) o un listón que en un índice al contado quizá no se puede alcanzar (no existe la pareja de referencia, apartado 4.2). Con los feeds y el código de hoy el paso no ha dado todavía ningún «Validada»: los seis que hay guardados (dos estrategias de USDJPY, `16.9.76` y `10.9.72`, en FTMO, tres pasadas cada una) son anteriores al cambio de feed y de valor de punto. En tres de las cinco del NIKKEI sólo el 21-26 % de las operaciones de SQX tienen pareja en la misma barra (tabla del 3.5). No debe leerse como «estas cinco estrategias son malas».

**Las trece cosas que conviene saber antes de leer el resto:**

1. **Las filas 3b y 4 no pueden fallar en el NIKKEI225 a 0,1 lotes.** Se miden en % de una cuenta de 100.000 USD y la estrategia opera su lote fijo de 0,1. En el NIKKEI un día medio mueve el 0,0016 % de la cuenta y el peor día el 0,0045 %; los límites son 0,1 % y 0,5 puntos. Aunque MT5 no hubiera hecho ni una operación, las dos filas pasarían (pérdida máxima posible de una posición: 0,32 % de la cuenta, calculado por el revisor Feynman con el valor de punto 0,063137 y un índice de como mucho unos 50.000 puntos). Pero en USDJPY el margen es sólo 1,5 veces (el peor día guardado de `16.9.76` es −0,344 % frente al 0,5) y en XAUUSD la fila 4 ya falló (`Strategy 3.48.75`, corrida 20260929-201535, lote 0,1: 0,5926 frente a 0,5). No son un seguro en general (apartado 5.1).
2. **La comisión y el swap se traducen a SQX con cuidado y después ninguna fila los mira.** Las seis cifras se calculan sobre el movimiento de precio (cierre − apertura), no sobre el P&L de la cuenta (`mt5/compare.py:90-93`). Un swap mal traducido o una noche de triple swap equivocada no hace fallar nada.
3. **La fila 1 sólo se mide desde el lado de SQX.** Las operaciones que MT5 hace y SQX no (entre 10 y 68 por comparación en el NIKKEI) sólo aparecen en una nota. Y no hay tolerancia de precio ni de salida: basta el mismo lado y la entrada a una barra como mucho. Una pareja puede cerrar seis horas y media más tarde en MT5 y sigue siendo pareja.
4. **El spread de SQX es una foto; el de MT5, no.** SQX corre toda la ventana con el spread que la empresa cotizaba en el instante de leerlo. En la corrida del NIKKEI ese instante fue el **domingo 4 a las 21:22 UTC** (23:22 en Madrid, 00:22 del lunes en el reloj de FTMO): 1.000 puntos en FTMO y 700 en Hantec. No se ha comprobado si el mercado estaba cerrado; 1.000 es un nivel normal de 2026 en FTMO (media de 920 a 1.094 en 2026), aunque unas 2 veces la de 2025 (487) y más que la de 2024 (745) con que SQX cobró toda la ventana (`knowhow/costs/funded-tick-spread-vs-price.md:15`). El `tester.ini` no pasa ningún spread (`mt5/tester.py:23-28`); se supone que el tester usa el de su propio histórico, pero ninguna ficha de `knowhow/mt5/` lo dice: es inferencia, no verificada. Con un coste distinto en cada lado, el acuerdo de la fila 2 no puede atribuirse al EA (apartado 5.3).
5. **«R» es la pérdida media de SQX**, no el riesgo inicial, y la fila 2 es una **media** de diferencias absolutas, que unas pocas parejas con salida distinta dominan: en `S00V014`/FTMO la media es 0,36 USD y la mediana 0,04 USD.
6. **La tolerancia de una barra tapa un error de reloj de una hora en H1.** En USDJPY, sin convertir zonas, 27 parejas quedan a 60 minutos (20 de ellas en marzo, las semanas del cambio de hora) y el porcentaje emparejado es el mismo, 371 de 387. El código lo sabe y por eso convierte zonas antes de emparejar; pero la fila 1 por sí sola no lo habría detectado.
7. **El pool se queda con el último veredicto, sin límite de repeticiones.** El encargo decía «se corrige y se compara una vez más»; el código no cuenta intentos. El 2026-09-30 las mismas tres estrategias de USDJPY se verificaron tres veces cada una.
8. **Hoy el paso 26 no es una puerta, y la documentación va por detrás.** La cartera lee un pool declarado a mano (`portfolio/common/construct/inputs/pool.py`), y cualquier estrategia que alguien declare ahí entra, tenga «Validada», «No validada» o ninguna verificación; las diez «No validada» del NIKKEI no impiden nada. Además WORKFLOW dice que «falta el pool» (existe y tiene diez líneas) y que el pool es «lo único que lee la cartera» (ningún módulo de `portfolio/` lo lee todavía); el README de `mt5/verify` dice que el paso 26 del autopiloto «no se ha corrido» (se corrió el 2026-10-04).
9. **Qué demuestra el paso y qué no.** Compara dos simulaciones, no la ejecución real, y «Validada» no dice que la estrategia gane (ver el recuadro de arriba y 5.13).
10. **Nada de lo que mira una cuenta de fondeo lo comprueba ninguna fila:** ni el flotante, ni la pérdida diaria, ni el saldo con comisión y swap. En las diez pasadas del NIKKEI el drawdown de equity del informe de MT5 es entre un 5 % y un 27 % mayor que el de balance (calculado por el revisor Taleb, sobre los `summary.json` guardados: «Equity Drawdown Maximal» frente a «Balance Drawdown Maximal», p. ej. 11,24 frente a 8,85 en `S00V014`/FTMO) y no entra en ninguna fila (apartado 5.14).
11. **El paso 26 no es todavía una puerta** (ver el punto 8): nada en `portfolio/` importa `mt5.verify.pool`, comprobado con grep (apartado 5.15).
12. **Las filas 3b y 4 «no pueden fallar» sólo en el NIKKEI** (ver el punto 1): en XAUUSD la fila 4 ya falló y en USDJPY el margen es 1,5 veces (apartado 5.16).
13. **`pool.py:105-106` toma el último `pass` sin mirar umbrales, ventana ni modelo**: un `pass` conseguido con `--set` de un umbral más laxo, con otra ventana o con otro modelo del tester cuenta igual (apartados 5.9 y 5.17).

---

## 1. Qué es el paso y cómo decide

### 1.1 Dónde está

Es el último paso de la estrategia individual y la puerta de la cartera: del 27 en adelante sólo deberían entrar estrategias del pool validado. Diseño del dueño, 2026-09-29 (encargo 34 §0.5), que sustituyó a «traducir el histórico de SQX»: **un backtest de SQX por empresa, con las condiciones de esa empresa, contra el backtest del EA en MT5 en la cuenta de esa empresa.** FTMO con FTMO, Hantec con Hantec.

### 1.2 La cadena, pieza a pieza

| # | qué pasa | quién | dónde |
|---|---|---|---|
| 1 | Regla 5 sobre el activo | `ui.daemon.launch.run.assets` | `mt5/verify/run.py:145` |
| 2 | El terminal entra en la cuenta de cada empresa y lee el símbolo: spread de ese instante, `point`, modo y valor del swap, día del triple swap, apalancamiento, primera barra | `conditions.read` | `conditions.py:15-38` |
| 3 | Esas cifras se pasan a unidades de SQX; la comisión sale de la ficha del activo | `conditions.for_sqx` | `conditions.py:41-91` |
| 4 | Se fija la ventana | `earliest`, `latest` | `run.py:68-106` |
| 5 | Proyecto `Test_MT5Verify_<activo>_<tf>_<hora>` en el conductor: un retest por empresa («MT5 FTMO», «MT5 HANTEC») y una tarea que exporta el EA («MQL5») | `sqxside.build`, `mt5verify.configure` | `sqx/projects/mt5verify.py:148-195` |
| 6 | El conductor arranca, corre, vuelca y se para; las operaciones se exportan con el conductor parado; el proyecto se retira | `sqxside.run`, `firm_trades`, `retire` | `sqxside.py:42-127` |
| 7 | El `.mq5` se compila con el lote fijo de la estrategia | `mt5side.compile_ea` | `mt5side.py:33-53` |
| 8 | Una pasada del tester por cuenta (y una segunda en «Real ticks» si se pide) | `mt5side.backtest`, `ticks.backtest` | `mt5side.py:56-90` |
| 9 | Por empresa: recorte a la ventana, conversión de reloj, emparejado, seis cifras, veredicto | `judge.firm_result` | `judge.py:121-181` |
| 10 | Una fila en el ledger por empresa y modelo; `result.json` y `run.json` | `record.log`, `report.finish` | `run.py:219-225`, `mt5/verify/report.py:14-63` |
| 11 | (Desde el autopiloto) una línea por empresa en el pool | `pool.record` | `autopilot.py:162-163` |

Cada verificación del NIKKEI tardó entre 3 y 6 minutos (`wall_s` 191 a 351 s).

### 1.3 Qué estrategia se verifica

Desde la ventana (MT5 BRIDGE › Verificar): un `.sqx` del archivo, de un databank o de una carpeta. Desde el autopiloto: cada **finalista** de `finalistas.json`, que es el fichero de la madre **con el stop del paso 24 injertado** (`pipeline/autopilot/finalists.py:34-37`). Su identidad es la de ese fichero, no la de la madre. En la corrida real: `S00V014` = madre `Strategy 10.11.484` con stop en el percentil 90 × 2,2108.

El EA que se prueba es el que exporta SQX, **sin filtro de noticias**. El filtro de `/ea-news` es otro EA, parcheado después; lo que cuesta la regla de noticias se mide aparte (`mt5.newsfilter.reading`).

### 1.4 Lo que no tiene valor por defecto

La ventana (Desde, Hasta), el modelo del tester y las empresas los da el dueño cada vez. Faltando uno, el autopiloto se para (`pipeline/autopilot/tail.py:161-165`). «Desde = MT5» significa «la fecha más tardía entre la primera barra útil de cada servidor y el primer día de SQX» (`run.py:100`). «Hasta» se recorta al día anterior al último de SQX (`run.py:72`).

### 1.5 Los estados

| situación | qué pasa |
|---|---|
| Las seis cifras pasan | «Validada» para esa empresa; `pass` |
| Alguna falla o no se puede calcular | «No validada»; `fail`, con las filas que fallan |
| La empresa no se puede preparar (sin símbolo en `mt5:`, comisión sin confirmar, modo de swap que SQX no expresa) | «No se pudo verificar»: **no es un veredicto**, no deja línea en el pool |
| La verificación se cae | `run.json` queda `failed`; el autopiloto se para |

El titular de una verificación con varias empresas es verde si todas validan, ámbar («Validada en FTMO») si alguna, rojo si ninguna (`mt5/verify/report.py:31-32`). Cada empresa se juzga sola.

### 1.6 Qué escribe

- `AlgoData/mt5/verify/<fecha-hora>_<estrategia>/`: `run.json`, `result.json` (contrato de estudio: pestañas Resumen y Verificación), `in/` (el `.sqx`), `mq5/` (el EA exportado y el compilado), `sqx/<empresa>/trades.parquet`.
- `AlgoData/mt5/tests/<EA>_<empresa>_<símbolo>_<tf>_<desde>_<hasta>_<modelo>/`: `tester.ini`, `report.htm`, `deals.parquet`, `trades.parquet`, `summary.json`.
- Ledger: `<ACTIVO>_<TF>_mt5verify`, una fila por empresa y modelo, con los umbrales usados.
- `AlgoData/pool/<empresa>.csv` (sólo desde el autopiloto o con `python3 -m mt5.verify.pool --rebuild`).
- Desde el autopiloto, además: `verificados.csv` y `mt5verify.log` en la carpeta de la corrida.

---

## 2. Fundamentos: por qué SQX y MT5 no dan lo mismo

Un backtest es una simulación: toma una serie de precios, aplica las reglas y anota operaciones. Dos simuladores con la misma estrategia difieren por tres razones: **no ven los mismos precios**, **no cobran lo mismo** y **no cuentan igual**. La verificación intenta igualar la segunda y la tercera para que lo que quede sea la primera.

### 2.1 El reloj del servidor y el horario de verano

Cada feed sella sus barras en la hora de su bróker, no en UTC. Los servidores de FTMO y Hantec usan «EETUS»: la hora de Nueva York más siete horas. Es como la hora de Europa del Este, pero cambia al horario de verano en las fechas de Estados Unidos. Un feed con reloj europeo o israelí coincide casi todo el año y se separa una hora durante las semanas en que EE. UU. ya ha cambiado y Europa no (marzo, y finales de octubre).

Por qué importa: una estrategia H1 decide en la barra de las 10:00. Si un lado llama «10:00» a lo que el otro llama «11:00», las dos listas contienen la misma operación con una hora de diferencia, y además el **día** al que pertenece una operación que cierra cerca de medianoche cambia. Las reglas de pérdida diaria de una fondeada leen el día del servidor.

Qué hace el código: convierte cada hora de SQX de la zona de su feed a EETUS, operación a operación (`compare.py:101-132`), y después busca si queda un desfase de horas enteras, entre −3 y +3 (`judge.py:27-46`). Hoy los feeds de SQX ya están en EETUS, así que la conversión no mueve nada. El desfase hallado es 0 en las diez comparaciones del NIKKEI y en 29 de las 34 guardadas; las cinco con ±1 hora son de USDJPY, de las 13:29 a las 14:14 (UTC) del 2026-09-30, antes de que existiera la conversión de zonas (desde las 14:17 todas son 0).

Ejemplo real (calculado por mí, USDJPY `16.9.76`/FTMO, cuando el feed era el de the5ers con reloj de Israel): sin convertir, 27 de las 371 parejas quedan a 60 minutos y 20 son de marzo; convirtiendo, quedan 5 y ninguna en marzo.

### 2.2 La feed: no son los mismos precios

SQX corre sobre su propio histórico (Dukascopy/Darwinex); MT5, sobre el del servidor de la empresa. En un par de divisas líquido casi coinciden: en USDJPY la diferencia mediana del precio de entrada entre parejas es 0,002 yenes. En un índice al contado no: cada bróker fabrica su precio del Nikkei, con su horario y sus huecos. En `S00V014`/FTMO la diferencia mediana de entrada es de 8 puntos de índice, y en `S02V014` de 33.

Esto no se puede traducir. Es justo lo que el paso quiere medir: si la lógica dispara en los mismos sitios a pesar de que los precios no sean idénticos.

### 2.3 El modelado de ticks

Dentro de una barra, el simulador tiene que inventar el recorrido del precio. MT5 ofrece cuatro modelos (`mt5/tester.py:13`):

| modelo | qué hace |
|---|---|
| `open_prices` | sólo el precio de apertura de cada barra |
| `ohlc_m1` | cuatro precios por cada barra de un minuto |
| `every_tick` | ticks sintéticos interpolados desde las barras M1 |
| `real_ticks` | los ticks que el bróker grabó, con su spread real |

Donde el servidor no tiene barras M1, el tester fabrica en silencio 4 ticks por barra del timeframe (`knowhow/mt5/mt5-tester-m1-gaps-hide-news-window.md`). El informe da una «calidad del histórico»: 99 % en las corridas del NIKKEI.

Un stop que salta dentro de la barra sale a un precio y a un minuto que dependen del modelo. Por eso en MT5 una salida por stop lleva hora 06:09:33 y en SQX 06:00.

### 2.4 El spread

El spread es la distancia entre el precio de compra y el de venta. Una compra entra al precio caro y sale al barato, así que el spread ya está dentro de los precios de apertura y cierre de cada operación.

SQX usa **un spread fijo** para toda la ventana. El dueño eligió «el spread actual del símbolo» (2026-09-29): el que cotiza la empresa en el momento de leerlo. Se supone que MT5 usa el de su histórico, que cambia a lo largo del día (inferencia: el `tester.ini` no pasa spread y ninguna ficha de `knowhow/mt5/` dice cuál usa).

### 2.5 La comisión

Lo que el bróker cobra por abrir y cerrar. En SQX sale de la ficha del activo (`costs.commission.brokers.<empresa>`), y si no está confirmada la empresa se rechaza: nunca se adivina (`conditions.py:62-67`). En MT5 la cobra el tester según el grupo de la cuenta. NIKKEI: cero en los dos lados. USDJPY/FTMO: 5 USD por lote y vuelta en SQX; el informe de MT5 suma 199,50 USD en 399 operaciones de 0,1 lote, es decir, 0,50 USD por operación, lo mismo.

### 2.6 El swap y la noche de triple swap

El swap es el interés por dejar una posición abierta de un día para otro. Se cobra a la hora del cierre diario del servidor, y un día a la semana se cobra triple para cubrir el fin de semana (miércoles en divisas, viernes en este índice).

MT5 lo expresa de varias maneras (`swap_mode`); el código traduce cuatro y rechaza el resto (`conditions.py:6`):

| modo de MT5 | en SQX | escala |
|---|---|---|
| 0, desactivado | puntos, 0 y 0 | — |
| 1, en puntos | `points` | × `point` ÷ `tick_size` |
| 4, en dinero | `money` | sin escala |
| 5 y 6, en % anual | `percent` | sin escala |

El día del triple sale del servidor (`swap_rollover3days`; si el servidor no lo da, miércoles: `conditions.py:76`). La hora del cierre diario sale de la ficha del activo, no del servidor (`conditions.py:77`).

### 2.7 El tamaño del punto y del contrato

«Punto» no significa lo mismo en los dos programas. En MT5 es el último decimal de la cotización (`point`); en SQX es el `tick_size` del instrumento. La conversión es:

> puntos de SQX = puntos de MT5 × `point` ÷ `tick_size`

Ese cociente es el `to_sqx` de la ficha (`mt5_point.<empresa>.to_sqx`). No es siempre dividir entre diez:

| activo | FTMO | Hantec |
|---|---|---|
| EURUSD, GBPUSD, USDJPY, cruces del yen | 0,1 | 0,1 |
| Oro, plata, NIKKEI225, USA500 | 1 | 1 |
| Brent (UKOIL) | 1 | **10** |

Ejemplos reales: el USDJPY de FTMO cotizaba 2 puntos de MT5 → 2 × 0,001 ÷ 0,01 = **0,2** puntos de SQX. El JP225 de FTMO, 1.000 puntos → 1.000 × 0,01 ÷ 0,01 = **1.000**.

El código no usa el `to_sqx` guardado: calcula el cociente con el `point` que el servidor da en ese instante (`conditions.py:61`) y avisa si no coincide con el de la ficha (`conditions.py:84-88`).

El **valor del punto** es cuántos dólares vale un movimiento de 1,0 en el precio con un lote. Aquí hay una diferencia de fondo: en un instrumento cotizado en yenes, SQX convierte a dólares con un tipo de cambio fijo y MT5 con el de cada día. La misma operación da dólares distintos sin que el EA haya hecho nada distinto. Por eso el dueño decidió (2026-09-30) que las seis cifras se calculen **sobre el movimiento de precio, al mismo valor de punto en los dos lados** (`compare.py:76-93`):

> P&L comparado = (cierre − apertura) × (+1 compra, −1 venta) × valor del punto × lotes

Ejemplo real, primera operación de `S00V014`/FTMO (valor del punto 0,063137; 0,1 lotes):

| | entrada | salida | movimiento | P&L comparado | P&L de la cuenta |
|---|---|---|---|---|---|
| SQX | 21:30, 33.795,27 | 06:00, 33.686,16 | −109,11 | −0,689 USD | −0,75 |
| MT5 | 22:00, 33.826,00 | 06:09:33, 33.715,00 | −111,00 | −0,701 USD | −0,83 |

La consecuencia, que vuelve en el apartado 5.2: la comisión y el swap están en la columna de la derecha y no en la que se juzga.

### 2.8 El tamaño de la operación

La primera prueba real enseñó que ninguno de los dos lados usa solo el tamaño de la estrategia: la tarea de SQX aplicaba el dimensionado por ATR del donante (entre 0,07 y 0,47 lotes) y el EA exportado traía un «importe fijo» propio. Hoy se lee el `FixedSize` del fichero y se impone en los dos lados (`mt5verify.py:29-44`, `mt5side.py:11-30`). Una estrategia con otro dimensionado se rechaza. En todas las corridas terminadas salvo la primera de XAUUSD (20260929-194955, sin lote guardado, dimensionado por ATR) el lote es 0,1 sobre una cuenta de 100.000 USD.

### 2.9 Emparejar dos listas: un ejemplo de juguete

Tolerancia de una barra H1 = 60 minutos. Compras todas.

| SQX | MT5 |
|---|---|
| A 10:00 | X 11:00 |
| B 11:00 | Y 15:00 |
| C 15:00 | Z 20:00 |
| D 18:00 | |

El algoritmo recorre SQX por orden y da a cada operación la de MT5 **más cercana que siga libre**, del mismo lado y a 60 minutos o menos:

- A (10:00): la más cercana libre es X (11:00), a 60 minutos. Vale. A–X.
- B (11:00): X ya está cogida; Y queda a 4 horas. **B se queda sin pareja**, aunque X era exactamente la suya.
- C (15:00): Y. C–Y, a 0 minutos.
- D (18:00): Z está a 2 horas. Sin pareja.

Resultado: 2 de 4 emparejadas (50 %); en MT5, Z queda sin pareja. Tres nombres:

- **Emparejada:** tiene una operación de MT5 del mismo lado con la entrada dentro de la tolerancia.
- **Huérfana de SQX:** no la tiene. Es lo que cuenta la fila 1.
- **Huérfana de MT5:** operación de MT5 que nadie cogió. Sólo sale en una nota.

No existe una categoría «distinta». Una pareja con precios o salidas diferentes sigue siendo pareja, y su diferencia va a la fila 2.

El ejemplo enseña el defecto del método «el primero que llega»: A le quita la pareja a B. Por eso la búsqueda del desfase de reloj puntúa primero las parejas a media tolerancia o menos (`judge.py:44-46`).

### 2.10 Correlación y diferencia media absoluta, con cinco días

P&L diario en % de la cuenta:

| día | SQX | MT5 | diferencia |
|---|---|---|---|
| 1 | +1 | +1 | 0 |
| 2 | −2 | −2 | 0 |
| 3 | +3 | +2 | 1 |
| 4 | 0 | +1 | 1 |
| 5 | −1 | −1 | 0 |

**Diferencia media absoluta:** (0 + 0 + 1 + 1 + 0) ÷ 5 = **0,4**. Dice cuánto se separan en un día típico, en las unidades de la tabla.

**Correlación:** mide si los dos suben y bajan los mismos días, de −1 a +1. Las dos medias son 0,2. Se resta la media a cada dato, se multiplican las parejas y se suman: 0,64 + 4,84 + 5,04 − 0,16 + 1,44 = 11,8. Se divide entre la raíz del producto de las sumas de cuadrados: √(14,8 × 10,8) = 12,64. Resultado: **0,933**. Con dos días de cinco algo distintos ya no llega a 0,95.

Dos propiedades que importan después:

- La correlación **no cambia con la escala**: si todo se divide entre cien sigue siendo 0,933.
- La diferencia media absoluta **sí**: dividida entre cien es 0,004. Un umbral fijo en % de la cuenta depende del tamaño del lote.

### 2.11 Drawdown máximo

Balance 100; operaciones +2, −3, −1, +5 → 102, 99, 98, 103. El máximo previo es 102 y el suelo 98: drawdown = (102 − 98) ÷ 102 = 3,92 %. Si el otro lado diera 3,00 %, la diferencia relativa es (3,92 − 3,00) ÷ 3,92 = 23,5 %.

El drawdown máximo es **un solo tramo** de toda la curva: el peor. Basta una operación huérfana dentro de ese tramo para moverlo mucho.

### 2.12 Cuánto se puede fiar uno de un porcentaje con pocas operaciones

Si cada operación de SQX tuviera una probabilidad *p* de encontrar pareja, el número de emparejadas en *n* operaciones sería como tirar *n* veces una moneda trucada. Con *n* = 105 hacen falta 100 parejas para llegar al 95 %. Si la moneda es del 93 % (fidelidad real por debajo del umbral), salen 100 o más una de cada cuatro veces. El apartado 4.4 da la tabla entera.

---

## 3. Lo que calcula, pieza a pieza

### 3.1 La traducción de costes a SQX (`conditions.for_sqx`)

| cifra | regla | `fichero:línea` | NIKKEI/FTMO | USDJPY/FTMO |
|---|---|---|---|---|
| spread | puntos MT5 × `point` ÷ `tick_size`, 4 decimales | `conditions.py:61` | 1.000 | 0,2 |
| comisión | la de la ficha para esa empresa | `conditions.py:62-67` | 0 % | 5 por lote |
| swap largo / corto | según el modo; en puntos, × `point` ÷ `tick_size` | `conditions.py:68-74` | −924,73 / −308,24 | 0,424 / −2,213 |
| triple swap | día del servidor | `conditions.py:76` | viernes | miércoles |
| deslizamiento | 0: el tester de MT5 no desliza una orden a mercado | `config.yaml:22` | 0 | 0 |

Hantec en el NIKKEI: spread 700, swap −838,029 / −355,65, viernes.

La tarea de SQX recibe además la ventana, sin tramo fuera de muestra, sin comprobaciones cruzadas, con la aceptación apagada y con el dimensionado de la estrategia (`mt5verify.py:66-79`).

### 3.2 El lado de MT5

El `tester.ini` lleva cuenta y servidor, EA, símbolo, timeframe, modelo, fechas, depósito y apalancamiento (`tester.py:17-29`). **No lleva spread ni comisión ni swap**: los pone el servidor. El informe HTML se lee fila a fila; cada entrada («in») se une con su salida («out») y el P&L de la operación suma beneficio, comisión y swap (`mt5/report.py:49-79`). Un informe con operaciones de inversión («in/out») o con dos posiciones a la vez se rechaza. (Este `report.py` es `mt5/report.py`; el que escribe `result.json` es `mt5/verify/report.py`.)

### 3.3 La ventana

Las dos listas se recortan a las operaciones **abiertas** entre Desde y Hasta, ambos incluidos (`compare.py:70-73`). El recorte de SQX se hace con sus horas antes de convertir el reloj (`run.py:214`).

Operaciones en el tramo común:

| estrategia | ventana | años | SQX | MT5 FTMO | MT5 Hantec | SQX por año |
|---|---|---|---|---|---|---|
| S00V014 | 2024-01 → 2026-09 | 2,75 | 105 | 101 | 102 | 38 |
| S01V014 | íd. | 2,75 | 61 | 67 | 63 | 22 |
| S02V014 | íd. | 2,75 | 125 | 131 | 127 | 45 |
| S03V014 | íd. | 2,75 | 137 (135 con los costes de Hantec) | 140 | 146 | 50 |
| S04V014 | íd. | 2,75 | 130 | 136 | 128 | 47 |
| 16.9.76 (USDJPY H1) | 2022-06 → 2026-09 | 4,3 | 387 | 399 | 393 | 90 |

El lado de SQX no es el mismo para las dos empresas: cada una tiene su retest con sus costes (`S03V014`: 137 y 135).

### 3.4 El reloj (`judge.clock`)

Para cada desfase de −3 a +3 horas empareja y puntúa, por este orden: más parejas a media tolerancia o menos; más parejas; menor suma de distancias; menor |desfase| y, a igualdad, el positivo (`judge.py:40-46`, la clave es `(close, hit, -gaps, -abs(h), h)` con `max`). El elegido se guarda como `clock_h`: 0 en 29 de las 34 comparaciones guardadas, +1 en cuatro y −1 en una (todas de USDJPY, anteriores a la conversión de zonas).

### 3.5 El emparejado (`compare.pair`)

Regla (`compare.py:20-34`): por cada operación de SQX, en su orden, la operación de MT5 libre, del mismo tipo (compra o venta), con la hora de entrada más cercana y a `tolerancia` minutos **o menos** (el límite cuenta). Tolerancia = `entry_tolerance_bars` × minutos del timeframe (`judge.py:146`): 30 minutos en M30, 60 en H1.

No mira: el precio de entrada, la hora ni el precio de salida, el tamaño.

Reparto real de las parejas por distancia de entrada (calculado por mí):

| comparación | parejas | a 0 min | a una barra | a 0 min, sobre las de SQX |
|---|---|---|---|---|
| S00V014 / FTMO | 91 | 81 | 8 (más 1 a 0,5 min y 1 a 25 min) | 77 % |
| S01V014 / FTMO | 51 | 35 | 11 (más 5 a 25 min) | 57 % |
| S02V014 / FTMO | 85 | 30 | 55 | 24 % |
| S03V014 / FTMO | 89 | 29 | 52 (más 8 a 24-25 min) | 21 % |
| S04V014 / FTMO | 71 | 33 | 37 (más 1 a 25 min) | 25 % |
| 16.9.76 / FTMO | 371 | 366 | 5 | 94,6 % |

En tres de las cinco del NIKKEI, más de la mitad de las parejas están a una barra de distancia, en los dos sentidos y a cualquier hora del día. No he diagnosticado la causa. (La última columna cuenta las parejas que quedan a 0 minutos con la tolerancia cargada; con tolerancia cero el emparejado puede dar una o dos más o menos, porque el reparto cambia: es la primera columna de la tabla del 5.6.)

Una pareja que no lo parece (`S00V014`/FTMO, 2024-02-22): SQX entra a la 01:30 y sale a las 05:00 con +1,36; MT5 entra a la 01:05 y sale a las 11:30 con +2,45. Entradas a 25 minutos: emparejadas.

### 3.6 Fila 1 — operaciones de SQX emparejadas

> fila 1 = parejas ÷ operaciones de SQX en la ventana  (`judge.py:75-76`)

Pasa si es **≥ 0,95**. La nota añade «de las N de MT5, el X % tienen pareja» (`judge.py:77`, `101-102`); ese segundo porcentaje no se juzga.

`S00V014`/FTMO: 91 ÷ 105 = 0,867. Falla. La nota: de las 101 de MT5, el 90 %.

### 3.7 Fila 2 — diferencia media por operación, en R

> R = media de |P&L| de las operaciones **perdedoras de SQX** en la ventana (todas, no sólo las emparejadas)  (`judge.py:78-79`)
> fila 2 = media, sobre las parejas, de |P&L MT5 − P&L SQX| ÷ R  (`judge.py:80-81`)

P&L es el «comparado» del apartado 2.7. Pasa si es **≤ 0,05**. La nota da el sesgo: la media de la diferencia con su signo.

`S00V014`/FTMO: 49 perdedoras, R = 1,358 USD; diferencia absoluta media de las 91 parejas = 0,361 USD; 0,361 ÷ 1,358 = **0,266**. Falla. Sesgo +0,17 USD (MT5 gana algo más por operación). La **mediana** de esa misma diferencia es 0,040 USD (calculado por mí): la mitad de las parejas difieren menos del 3 % de R, y la media la suben las parejas con salida distinta.

`16.9.76`/FTMO: R = 23,71 USD (con el valor de punto de aquel día); fila 2 = 0,036. Pasa.

### 3.8 Filas 3a y 3b — el P&L diario

Cada operación se asigna al **día del servidor en que cierra**; se suma el P&L comparado del día y se divide entre el depósito, en % (`judge.py:49-54`). Se toman los días en que algún lado cerró algo y se pone 0 donde el otro no cerró nada (`judge.py:82-84`).

> fila 3a = correlación entre las dos series  (`judge.py:85`); si hay dos días o menos, o una serie es constante, no se calcula y falla
> fila 3b = media de |SQX − MT5| por día, en % de la cuenta  (`judge.py:86`)

Pasan si 3a **≥ 0,95** y 3b **≤ 0,1**.

`S00V014`/FTMO: 94 días; 3a = 0,844 (falla); 3b = 0,00052 % (pasa). Primeros días:

| día | SQX % | MT5 % |
|---|---|---|
| 2024-01-09 | −0,00069 | −0,00070 |
| 2024-01-10 | +0,00321 | +0,00328 |
| 2024-01-31 | −0,00108 | −0,00108 |
| 2024-02-08 | +0,00114 | +0,00116 |
| 2024-02-13 | −0,00112 | −0,00004 |

El 13 de febrero SQX tiene una compra 07:30 → 16:00 y MT5 una compra 05:30 → 16:00 (revisión de Feynman): misma salida y entrada dos horas (4 barras) antes. Lo más probable es la misma operación con otra barra de entrada, fuera de la tolerancia de 30 minutos; el emparejado las cuenta como dos huérfanas, no como una operación que MT5 «no hizo». Además ilustra que la tolerancia de entrada decide la fila 1 (apartado 5.6).

### 3.9 Fila 4 — el peor día

> fila 4 = |peor día de SQX − peor día de MT5|, en puntos de %  (`judge.py:87-88`)

Pasa si es **≤ 0,5**. Compara los dos mínimos, **aunque no sean el mismo día**.

`S00V014`/FTMO: −0,00454 % y −0,00433 %, los dos el 2026-07-31; fila 4 = 0,00021. `S02V014`/FTMO: el peor de SQX es el 2026-02-09 y el de MT5 el 2026-07-31; fila 4 = 0,00067. Pasa igual.

### 3.10 Fila 5 — el drawdown máximo

> balance = depósito + suma acumulada del P&L comparado, por orden de cierre
> drawdown = máximo de (pico − balance) ÷ pico, en %  (`judge.py:57-63`)
> fila 5 = |DD SQX − DD MT5| ÷ el mayor de los dos  (`judge.py:89-90`)

Pasa si es **≤ 0,10**. Es el drawdown del balance **al cierre de cada operación**; el flotante intradía con barras M1 que pedía el encargo no está hecho, y la propia nota de la fila lo dice (`judge.py:116-117`).

`S00V014`/FTMO: 0,00819 % y 0,00817 % → 0,0022. Pasa. `16.9.76`/Hantec: 0,635 % y 0,535 % (las guardadas; 0,613 y 0,516 con la ficha de hoy, mismo 0,157) → 0,157. **Falla, y es la única fila que falla**: las otras cinco son mejores que las de FTMO, que valida.

### 3.11 La pasada en Real ticks

Opcional (`--also-real-ticks`). Se juzga con las mismas seis cifras y se dibuja al lado. **El estado que va al pool es el de la primera pasada**, la del modelo que eligió el dueño (`ticks.py:42-54`). Ninguna corrida guardada la tiene.

### 3.12 El pool (`pool.py`)

Un CSV por empresa, sólo se añaden líneas. Cada línea: identidad, estrategia, proyecto, madre, activo, timeframe, empresa, carpeta de la verificación, fecha, ventana, modelo, veredicto, huella de los umbrales con que se juzgó, huella de la configuración, las dos cuentas de operaciones, `clock_h`, las seis cifras, el stop (percentil y múltiplo) y la ruta del fichero.

**Qué entra en el «pool validado»** (`pool.read`, `pool.py:98-106`): las identidades cuya **última** línea, por fecha de verificación, es `pass`. Validada una vez y fallada después: fuera. Al revés: dentro. Una empresa rechazada o una verificación caída no dejan línea, así que un `pass` anterior sigue en pie.

Estado hoy: `ftmo.csv` y `hantec.csv`, 5 líneas cada uno, las diez `fail`. Validadas: 0 y 0. Las 24 comparaciones anteriores (XAUUSD y USDJPY, del 29 y 30 de septiembre) no están en el pool; `--rebuild` las añadiría, y con ellas `16.9.76` y `10.9.72` entrarían como validadas en FTMO (calculado por mí con `pool.pending(pool.rebuild())`, sin escribir nada).

---

## 4. El criterio cargado y por qué

### 4.1 Los siete umbrales

`ledger/thresholds.yaml:1041-1088`, todos `set_by: dueño`, `set_on: 2026-09-29`, «valor de partida aceptado»:

| clave | valor | fila | sentido |
|---|---|---|---|
| `mt5verify.matched_min` | 0,95 | 1 | ≥ |
| `mt5verify.entry_tolerance_bars` | 1 | 1 | tolerancia del emparejado |
| `mt5verify.trade_gap_max_r` | 0,05 | 2 | ≤ |
| `mt5verify.daily_corr_min` | 0,95 | 3a | ≥ |
| `mt5verify.daily_mad_max_pct` | 0,1 | 3b | ≤ |
| `mt5verify.worst_day_gap_max_pp` | 0,5 | 4 | ≤ |
| `mt5verify.dd_rel_gap_max` | 0,10 | 5 | ≤ |

Más dos constantes del `config.yaml` que también deciden: la búsqueda del reloj en ±3 horas y la zona del servidor `EETUS`.

### 4.2 De dónde salen

De la tabla del encargo 34 §3, que el agente propuso y el dueño aceptó como punto de partida. Antes, `OPEN.md` #78 había propuesto otro listón: emparejadas ≥ 95 % **en los dos sentidos**, entrada a una barra, **misma salida ≥ 90 %**, correlación del P&L ≥ 0,95. De ahí vienen el 95 % y la barra; «los dos sentidos» y «misma salida» no llegaron al código.

Ninguno sale de una medición. No hay una pareja de referencia —la misma estrategia, el mismo feed, los dos simuladores— que diga qué acuerdo es alcanzable cuando todo va bien.

### 4.3 El resultado sobre lo que hay en disco

NIKKEI225 M30, 2026-10-04, every tick. En negrita lo que falla:

| estrategia | empresa | fila 1 | fila 2 | 3a | 3b | 4 | 5 | huérfanas de MT5 |
|---|---|---|---|---|---|---|---|---|
| S00V014 | FTMO | **0,867** | **0,266** | **0,844** | 0,0005 | 0,0002 | 0,002 | 10 de 101 |
| S00V014 | Hantec | **0,876** | **0,230** | **0,827** | 0,0006 | 0,0002 | 0,052 | 10 de 102 |
| S01V014 | FTMO | **0,836** | **0,157** | 0,965 | 0,0009 | 0,0009 | **0,150** | 16 de 67 |
| S01V014 | Hantec | **0,738** | **0,174** | 0,954 | 0,0010 | 0,0000 | 0,004 | 18 de 63 |
| S02V014 | FTMO | **0,680** | **1,028** | **0,496** | 0,0009 | 0,0007 | **0,151** | 46 de 131 |
| S02V014 | Hantec | **0,672** | **0,968** | **0,549** | 0,0009 | 0,0007 | **0,383** | 43 de 127 |
| S03V014 | FTMO | **0,650** | **0,334** | **0,822** | 0,0009 | 0,0003 | **0,241** | 51 de 140 |
| S03V014 | Hantec | **0,600** | **0,306** | **0,807** | 0,0009 | 0,0014 | **0,279** | 65 de 146 |
| S04V014 | FTMO | **0,546** | **0,162** | **0,749** | 0,0016 | 0,0020 | **0,147** | 65 de 136 |
| S04V014 | Hantec | **0,462** | **0,162** | **0,725** | 0,0017 | 0,0007 | **0,293** | 68 de 128 |

Las diez fallan las filas 1 y 2; ocho, la 3a; siete, la 5; ninguna, la 3b ni la 4.

USDJPY H1, 2026-09-30, OHLC M1, tres estrategias verificadas tres veces cada una (y una cuarta, `10.1.79`, dos veces, fallando en las dos empresas): `16.9.76` y `10.9.72` validan en FTMO y fallan en Hantec; `21.9.59` falla en las dos. La de este documento:

| estrategia | empresa | fila 1 | fila 2 | 3a | 3b | 4 | 5 |
|---|---|---|---|---|---|---|---|
| 16.9.76 | FTMO | 0,959 | 0,036 | 0,957 | 0,0031 | 0,0005 | 0,089 |
| 16.9.76 | Hantec | 0,961 | 0,020 | 0,979 | 0,0020 | 0,0001 | **0,157** |

En FTMO pasa con poco margen en tres filas: 371 parejas donde hacían falta 368; 0,957 frente a 0,95; 0,089 frente a 0,10.

### 4.4 Qué potencia tiene la fila 1 (calculado por mí)

Cuenta exacta con la binomial (`potencia.py`), suponiendo que cada operación encuentra pareja con probabilidad *p*, independiente de las demás. Cada casilla es la probabilidad de **pasar** la fila 1:

| operaciones de SQX | huérfanas permitidas | *p* = 0,99 | 0,97 | 0,95 | 0,93 | 0,90 | 0,85 |
|---|---|---|---|---|---|---|---|
| 27 | 1 | 0,97 | 0,81 | 0,61 | 0,43 | 0,23 | 0,07 |
| 61 | 3 | 1,00 | 0,89 | 0,64 | 0,37 | 0,13 | 0,01 |
| 105 | 5 | 1,00 | 0,90 | 0,57 | 0,25 | 0,04 | 0,00 |
| 137 | 6 | 1,00 | 0,88 | 0,47 | 0,15 | 0,01 | 0,00 |
| 387 | 19 | 1,00 | 0,99 | 0,53 | 0,06 | 0,00 | 0,00 |
| 1.000 | 50 | 1,00 | 1,00 | 0,54 | 0,01 | 0,00 | 0,00 |

Cómo leerla:

- Con un centenar de operaciones, un EA con fidelidad real del 97 % **falla una de cada diez veces**, y uno del 93 % **pasa una de cada cuatro**.
- Con 61 operaciones (`S01V014`) sólo se permiten 3 huérfanas y la separación es menor que con 105 (0,52 entre el 93 % y el 97 %, frente a 0,65), pero sigue siendo grande; lo que casi no separa es el 93 % del 95 % (0,37 frente a 0,64).
- Hacen falta unas 300 operaciones para que un 93 % real pase menos del 10 % de las veces (calculado por el revisor Feynman con la misma binomial: pasa 0,103 con 300 y 0,078 con 310; desde 301 queda siempre bajo el 10 %; el revisor Taleb da 218 como primera n que lo cumple, con oscilaciones por el redondeo de las huérfanas permitidas hasta 300).
- El supuesto de independencia es optimista y falla en los dos sentidos: las huérfanas llegan en rachas (un hueco del histórico, unas semanas de reloj). Si llegan en bloques de 5 a 10 operaciones, con 105 operaciones un EA con fidelidad real del 90 % pasa una de cada tres veces en lugar de una de cada veinticinco, y uno del 85 % una de cada cinco o seis en lugar de ninguna; con 387 operaciones un 93 % real pasa 0,20-0,23 en vez de 0,06 (calculado por el revisor Taleb con una binomial sobre bloques de 5 o 10 operaciones, sin datos; supone el tamaño del bloque). Discrepancia mínima detectable (pasa menos del 5 % de las veces, con independencia): fidelidad real ≤ 87,8 % con 61 operaciones, ≤ 90,2 % con 105, ≤ 91,5 % con 137, ≤ 92,9 % con 387; en racimos de 5-10 ni un 85 % queda detectado con 105 (mismo método). Con rachas, ni las 387 de USDJPY bastan para el 93 %.

Para las diez del NIKKEI esto no cambia nada: están entre el 46 % y el 88 %, lejos del umbral con cualquier *n*.

### 4.5 Qué precisión tiene la fila 3a (calculado por mí)

Intervalo del 95 % de una correlación observada, con la transformación de Fisher y días independientes:

| días | si se observa 0,95 | si se observa 0,97 |
|---|---|---|
| 53 | 0,915 a 0,971 | 0,948 a 0,983 |
| 94 | 0,926 a 0,967 | 0,955 a 0,980 |
| 160 | 0,932 a 0,963 | 0,959 a 0,978 |
| 360 | 0,939 a 0,959 | 0,963 a 0,976 |

El 0,957 de `16.9.76`/FTMO, con 360 días, es compatible con una correlación verdadera de 0,947 a 0,965: no distingue «justo por encima» de «justo por debajo».

Para las filas 2, 4 y 5 no he calculado potencia: la 2 es una media con cola larga, y la 4 y la 5 son extremos de una sola trayectoria, sin una teoría sencilla que aplicar. Está sin medir.

### 4.6 Lo que el criterio no tiene

- **Limbo.** La doctrina dice que un hecho que falta es Limbo; aquí una cifra que no se puede calcular falla, y una empresa que no se puede preparar no deja rastro en el pool.
- **Suelo de operaciones.** No hay mínimo de operaciones en la ventana para dar un veredicto. Con 20 operaciones se permite una sola huérfana.
- **Suelo de calidad del histórico.** Se anota y se enseña (99 %), pero no impide validar (`mt5/report.py:83`, «No floor»).
- **Regla en el autopiloto.** `criteria.yaml` no tiene paso 26. El autopiloto anota, no corta: una finalista que no valida «es un resultado» y sigue con la siguiente.

---

## 5. Lo que no cuadra o no está medido

### 5.1 Las filas 3b y 4 no pueden fallar a este tamaño (en el NIKKEI)

La diferencia media absoluta entre dos series no puede superar la suma de sus medias absolutas, y la diferencia entre dos peores días (los dos negativos) no puede superar el mayor de los dos. En las doce comparaciones de este documento (calculado por mí):

| | día medio, % de la cuenta | peor día, % | límite 3b | límite 4 |
|---|---|---|---|---|
| NIKKEI, las diez | 0,0011 a 0,0036 | −0,004 a −0,020 | 0,1 | 0,5 |
| USDJPY 16.9.76 (cifras recalculadas con la ficha de hoy; guardado: peor día −0,344) | 0,023 | −0,33 | 0,1 | 0,5 |

En el NIKKEI el límite de 3b es entre unas 30 y unas 90 veces el día medio. Si MT5 no hubiera operado nunca, 3b valdría lo que el día medio de SQX y pasaría. La razón es el tamaño: 0,1 lotes de este índice en una cuenta de 100.000 USD mueven céntimos. Los dos umbrales están escritos para una cuenta dimensionada como se operará; la verificación usa el lote del fichero. Y por tanto la pérdida diaria, que es la primera regla de una cuenta de fondeo, no la comprueba hoy ninguna fila.

El alcance es el del NIKKEI (revisión de Feynman, cuentas propias): el valor de punto es 0,063137 USD por punto y lote, así que 0,1 lotes son 0,0063137 USD por punto; con el índice a 50.000 como mucho, la pérdida máxima de una posición es 316 USD = 0,32 % de la cuenta, menos que el 0,5 de la fila 4 (no puede fallar ni en teoría), y para que 3b superase el 0,1 haría falta una media de 100 USD al día = unos 15.838 puntos diarios. En USDJPY el margen no es tal: 631,34 × 0,1 = 63,1 USD por yen; el 0,5 % son 7,9 yenes y el peor día guardado de `16.9.76` es −0,344 % (5,3 yenes): margen de 1,45 veces. Y en XAUUSD sí falla: `Strategy 3.48.75`, corrida 20260929-201535 (lote 0,1, depósito 100.000), fila 4 = 0,5926 > 0,5 (nota guardada: «SQX −0.602 %, MT5 −1.194 %»); la corrida 194955 (sin lote registrado, dimensionado por ATR) falla además 3b = 0,556 y fila 4 = 1,348.

### 5.2 La comisión y el swap se traducen y no se juzgan

`compare.in_points` sustituye el P&L por el movimiento de precio (`compare.py:92-93`; su docstring lo dice: «Commission and swap are not in the price move»). El capítulo 76 del manual también. Pero el encargo 34 §1 pide comparar «lo que las reglas leen», y una fondeada lee el balance con comisión y swap.

Lo que he podido mirar (calculado por mí): en el NIKKEI, la diferencia entre el P&L de cuenta y el de precio en SQX —que es su swap más el redondeo a céntimos, porque la comisión es cero— suma −1,11 / −1,13 / −0,26 / −2,19 / −5,35 USD en las cinco de FTMO; el swap que cobra el tester de MT5 suma −1,14 / −1,32 / −0,24 / −2,04 / −5,41 USD. Se parecen, sobre conjuntos de operaciones que no son los mismos. Es una observación de cinco casos, no una comprobación que el paso haga. «Se parecen» vale sólo para el NIKKEI, donde la comisión es cero. En USDJPY `16.9.76`/FTMO, la que valida, el coste total es −180,90 USD en SQX (P&L de cuenta menos P&L de precio) y −140,41 USD en MT5 (comisión −199,50, swap +59,09): 40,5 USD de diferencia, 1,8 R, sin explicar y mezclada con el tipo de cambio fijo de SQX y las 12 operaciones de más de MT5 (calculado por el revisor Taleb sobre el `recalc.json` del autor; nadie la ha mirado).

### 5.3 El spread se lee una vez y a la hora que toque

La verificación del NIKKEI leyó el spread el domingo 2026-10-04 a las 21:22 UTC (23:22 en Madrid, 00:22 del lunes en el reloj de FTMO; el sello de `run.json` es UTC): 1.000 puntos (10 puntos de índice) en FTMO y 700 en Hantec. La ficha del activo lleva 796,12 para `oos2`. No se ha comprobado que el mercado estuviera cerrado a esa hora, ni si la cifra es la última cotización del viernes o un spread ensanchado. Contra la tesis del ensanchado de cierre, `knowhow/costs/funded-tick-spread-vs-price.md:15` da la media de FTMO JP225.cash en 745 puntos (2024), 487 (2025), 920 (2026) y 1.094 (julio-septiembre 2026): 1.000 es un nivel normal de 2026. Lo que sí es cierto (revisión de Feynman): SQX cobró 1.000 fijo durante 2024 (media 745) y 2025 (media 487). SQX aplicó esa cifra a los 2,75 años; el `tester.ini` no pasa ningún spread (`mt5/tester.py:23-28`) y se supone que MT5 usa el de su histórico, inferencia que ninguna ficha de `knowhow/mt5/` recoge.

Tamaño de lo que está en juego (revisión de Taleb; calculado por el revisor con el valor de punto 0,063137, 0,1 lotes y las R del `recalc.json` del autor): los 1.000 puntos de FTMO son 10 puntos de índice = 0,063 USD por operación = entre 0,021 y 0,083 R según la estrategia (0,046 R en `S00V014`, 0,083 R en `S02V014`); los 700 de Hantec, entre 0,015 y 0,059 R. El límite de la fila 2 es 0,05 R: si el tester de MT5 aplicara un spread mucho menor, la foto del spread sola puede ocupar entre un tercio y todo el margen de la fila 2 antes de que el EA haga nada distinto. Mientras no se sepa qué spread aplicó el tester en cada pasada, un acuerdo o un desacuerdo en la fila 2 no dice nada del EA. El `recalc.json` del autor guarda la diferencia media con signo del precio de entrada, que el apartado 2.2 no cita (sólo la mediana): −9,37 puntos de índice en `S00V014`/FTMO (82 de 91 parejas en la misma barra) con el spread de SQX en 10, compatible con que SQX cobre un spread que MT5 no cobra; no concluyente (Hantec −12,8 con spread 7; en `S01V014` y `S03V014`/FTMO el signo es +14,5 y +10,3).

Además, la tabla «Parámetros de la comparación» pone al lado, como «SQX», el coste del tramo **`build`** (304,11), siempre (`run.py:230`), aunque la ventana caiga en `oos2`.

### 5.4 La tabla de parámetros rotula «puntos/noche» un swap que no está en puntos

`judge.py:230-233` escribe «swap largo (puntos/noche)» sin mirar el tipo. En el NIKKEI la ficha lo tiene en porcentaje (−4,78) y lo que se lee de la empresa es −924,73: la tabla los enseña juntos como si fueran la misma unidad. El tipo leído de la empresa no se guarda en ningún fichero de la corrida.

### 5.5 La fila 1 mira en un solo sentido, y sin precio ni salida

`OPEN.md` #78 proponía «en los dos sentidos» y «misma salida ≥ 90 %». El código mide el sentido SQX → MT5 y no mira la salida. En `S04V014`/Hantec MT5 hace 68 operaciones de 128 que SQX no hace. La proporción de parejas que además cierran dentro de una barra es del 71 % al 92 % en el NIKKEI y del 100 % en USDJPY (calculado por mí).

### 5.6 La tolerancia decide la fila 1

Porcentaje emparejado según la tolerancia (calculado por mí; el cargado es 1 barra):

| comparación | 0 barras | 1 | 2 | 4 | 8 |
|---|---|---|---|---|---|
| S00V014 / FTMO | 77 % | 87 % | 89 % | 91 % | 93 % |
| S02V014 / FTMO | 26 % | 68 % | 79 % | 81 % | 83 % |
| S04V014 / FTMO | 25 % | 55 % | 64 % | 72 % | 75 % |
| 16.9.76 / FTMO | 94,6 % | 95,9 % | 95,9 % | 96,6 % | 97,4 % |

`16.9.76`/FTMO valida gracias a cinco parejas que están a una barra: con tolerancia cero quedaría en 366 de 387 y no pasaría. No es una propuesta de umbral; es cuánto pesa el que hay.

### 5.7 «R» es una lectura sin confirmar

El README y el encargo lo dicen: R es la pérdida media de SQX «porque estas estrategias no llevan stop». Las finalistas del autopiloto **sí llevan stop** (el del paso 24). El código sigue usando la pérdida media (`judge.py:78-79`) y la nota de la fila sigue diciendo «sin stop» (`judge.py:106-107`).

### 5.8 La fila 5 no es la del encargo

El encargo y la fila 26 de WORKFLOW dicen «drawdown intradía máximo sobre flotante, con la equity reconstruida con M1». Lo cargado es el drawdown del balance al cierre. Para una fondeada, donde manda el flotante, es la diferencia que más importa. Es un pendiente declarado en el encargo, no un desvío descubierto (`docs/encargos/34-validacion-mt5-pool.md:53`: «Queda 3. La fila 5 es el drawdown del balance al cierre de cada operación; el flotante con M1 falta»); sólo la fila 26 de WORKFLOW («drawdown intradía») lo vende sin matiz.

### 5.9 Repetir no cuesta nada

Encargo 34 §3: «se corrige y se compara **una** vez; si sigue fallando, no entra» y «el ledger cuenta las repeticiones con otros umbrales como ensayos». El código escribe una fila en el ledger por comparación, pero no he encontrado nada que cuente los intentos ni que los limite, y el pool toma el último veredicto. Repetir con la misma ventana, modelo y umbrales da casi lo mismo: el tester sobre el mismo histórico es determinista y, en lo guardado, ningún veredicto cambió (`16.9.76`, `21.9.59` y `10.9.72`, tres veces cada una en dos empresas). Lo que puede fabricar un «Validada» es cambiar algo entre intentos —la ventana, el modelo del tester, un umbral con `--set`, el spread leído ese día— y el pool no lo distingue: toma el último `pass` sin mirar con qué umbrales, ventana ni modelo se obtuvo (`pool.py:105-106`; `pool.read` no mira `thresholds_hash`). Ejemplos guardados: `10.1.79`/FTMO con ventana desde 2008 da fila 1 = 0,913 y fila 2 = 0,36; desde 2022, 0,936 y 0,069. Y `16.9.76`/Hantec, misma ventana y modelo, tres pasadas en 48 minutos con el código cambiando: fila 3a = 0,967 → 0,944 → 0,979 (cruza el 0,95 dos veces). Si cada intento fuera una tirada independiente (hipótesis, no lo que ocurre con el tester), una estrategia que pasa una de cada cuatro veces estaría validada con probabilidad 0,44 a los 2 intentos, 0,58 a los 3, 0,76 a los 5 y 0,94 a los 10; con q = 0,04 (90 % real) 0,12 a los 3 y 0,34 a los 10 (calculado por el revisor Taleb, 1 − (1 − q)^k).

### 5.10 El pool y la cartera

- WORKFLOW, fila 26: «falta el pool». Existe (`pool.py`, `AlgoData/pool/`).
- WORKFLOW: el pool es «lo único que lee la cartera». Ningún módulo de `portfolio/` importa `mt5.verify.pool`; sólo lo hace su test. El capítulo 86 del manual lo dice bien: «todavía no lo lee el módulo de carteras».
- Encargo 34 §0.5, «Queda»: el punto 1 (el pool) y el 5 (`mt5/symbols.csv` sólo tiene XAUUSD) están resueltos; los símbolos viven en `mt5:` de cada ficha. El fichero `mt5/symbols.csv` sigue en la carpeta sin que el paso lo lea.
- `mt5/verify/README.md`: `autopilot.py` «unrun against a real conductor and terminal». Las diez líneas del pool llevan proyecto, madre y stop: salieron de él.
- El formato del pool está «propuesto, por confirmar por el dueño» (README).
- La identidad del pool es la del fichero con el stop injertado. El encargo pedía «identidad y versión del archivo»; las finalistas vienen de `AlgoData/atrCalculator/…`, no del archivo.
- `pool.py` y `autopilot.py` no están en git.

### 5.11 Detalles menores

- El `tester.ini` de FTMO pide apalancamiento 50 (el que da la cuenta) y el informe dice 1:100. Con 0,1 lotes no afecta.
- El título de `OPEN.md` #78 sigue diciendo «built, not yet run».
- El primer README habla de «cinco filas»; son seis comprobaciones.
- La hora del cierre diario para el swap sale de la ficha y no del servidor.

### 5.12 Lo que no está medido

1. **Cuánto acuerdo es alcanzable.** Falta la referencia: una estrategia sencilla sobre un activo donde los dos feeds coincidan, para saber qué dan las seis cifras cuando no hay nada roto.
2. **Por qué el NIKKEI empareja a una barra.** La mitad de las parejas de tres estrategias están a 30 minutos, en los dos sentidos. Puede ser el horario de sesión de cada feed, las barras que faltan o el momento en que cada simulador evalúa la señal. Sin diagnosticar.
3. **La diferencia entre modelos del tester.** Ninguna corrida tiene la segunda pasada en Real ticks.
4. **El efecto del spread leído** sobre las seis cifras.
5. **La potencia de las filas 2, 4 y 5.**
6. **Una superviviente real.** El «hecho es» del encargo —una superviviente de los 25 pasos con su línea en el pool— no se ha dado.


### 5.13 Qué demuestra el paso y qué no

Compara dos simulaciones (el retest de SQX y el tester de MT5 de esa empresa), no una simulación con la ejecución real. Un «Validada» dice que, en el tramo común, las dos abren las operaciones en las mismas barras y mueven un precio parecido; no dice que la estrategia gane. Tampoco dice que el histórico de 15 años valga: ese tramo no se compara, y el retest comparado se corrió con otros costes que el de la elección (en `S00V014`, spread 304,11 y deslizamiento 106,44 frente a 1.000 y 0 en FTMO, 700 y 0 en Hantec). El EA comparado es el exportado sin filtro de noticias (apartado 1.3), no el que operará. El texto que el dueño lee en la ventana (`judge.py:154-155`) dice «SQX reproduce lo que el EA hace en su cuenta: el histórico largo de SQX vale para ella».

### 5.14 Lo que mira una cuenta de fondeo y ninguna fila comprueba

Una cuenta de fondeo lee el flotante intradía, la pérdida diaria y el saldo con comisión y swap. La fila 5 mide el balance al cierre de cada operación (`judge.py:57-63`, nota de la fila en `judge.py:116-117`); las filas 3b y 4 no pueden fallar en el NIKKEI a 0,1 lotes (apartado 5.1); la comisión y el swap no entran en ninguna cifra (apartado 5.2). Lo que sí comprueban las cuatro filas que pueden fallar (1, 2, 3a, 5) es si las entradas caen en la misma barra y si el movimiento de precio por operación y por día se parece. El informe de MT5 ya trae el drawdown de equity y nadie lo compara: en los diez `summary.json` del NIKKEI «Equity Drawdown Maximal» es entre un 5 % y un 27 % mayor que «Balance Drawdown Maximal» (11,24 frente a 8,85 en `S00V014`/FTMO; 42,76 frente a 40,60 en `S03V014`/Hantec; calculado por el revisor Taleb sobre cifras guardadas).

### 5.15 El paso 26 hoy no es una puerta

La cartera lee pools declarados a mano: `portfolio/common/construct/inputs/pool.py` (`declare(name, rows, added_by)` escribe `pools/<name>.csv` y `read` lo lee), sin mirar ningún veredicto del paso 26. Ningún fichero de `portfolio/` importa `mt5.verify.pool` (grep, comprobado al aplicar esta revisión). Cualquier estrategia que alguien declare ahí entra, tenga «Validada», «No validada» o ninguna verificación; las diez «No validada» del NIKKEI no impiden nada.

### 5.16 Las filas 3b y 4 «no pueden fallar» sólo en el NIKKEI

En XAUUSD la fila 4 ya falló (`Strategy 3.48.75`, 0,5926 frente a 0,5, a 0,1 lotes) y en USDJPY el margen es 1,5 veces (el peor día guardado de `16.9.76` es −0,344 % frente al 0,5). Detalle en el apartado 5.1.

### 5.17 El pool toma el último `pass` sin mirar con qué condiciones se obtuvo

`pool.py:105-106` toma, por identidad, la última línea por fecha de verificación y la deja entrar si es `pass`. No mira la huella de umbrales, la ventana ni el modelo del tester: un `pass` conseguido con `--set` de un umbral más laxo, con otra ventana o con otro de los cuatro modelos cuenta igual que uno conseguido con los valores cargados. Las ventanas y los modelos se guardan en cada línea, pero `pool.read` no los usa.

---

## 6. Cierre

### 6.1 Las reglas, en una tabla

| fila | qué mide | umbral | qué no ve |
|---|---|---|---|
| 1 | operaciones de SQX con pareja en MT5 | ≥ 95 %, a 1 barra | las huérfanas de MT5; el precio; la salida |
| 2 | diferencia media de P&L de precio por pareja, en R | ≤ 0,05 | comisión y swap; que R es la pérdida media |
| 3a | correlación del P&L diario | ≥ 0,95 | — |
| 3b | diferencia diaria media, % de la cuenta | ≤ 0,1 | no puede fallar en el NIKKEI a 0,1 lotes (en XAUUSD sí falló) |
| 4 | diferencia entre peores días | ≤ 0,5 puntos | íd.; no exige que sea el mismo día |
| 5 | diferencia relativa del drawdown máximo | ≤ 10 % | el flotante intradía |

### 6.2 El resultado

NIKKEI225, cinco finalistas de sorteo, dos empresas: 0 de 10 validadas. USDJPY, tres madres de prueba: dos validadas en FTMO, ninguna en Hantec (y fuera del pool hasta un `--rebuild`). Pool validado hoy: vacío.

### 6.3 Las decisiones que te quedan

| # | decisión | lo que ganas | lo que cuesta |
|---|---|---|---|
| 1 | **En qué unidad van las filas 3b y 4**: % de la cuenta al lote del fichero (hoy), o a un tamaño de referencia, o relativas al día medio | que dos de las seis comprobaciones puedan fallar | hay que decir cuál es el tamaño de referencia; sobre las doce comparaciones de este documento no cambia ningún veredicto, porque todas las que fallan lo hacen por otras filas (no es así en XAUUSD, donde la fila 4 ya falló, apartado 5.1) |
| 2 | **Si la comisión y el swap se juzgan** (una séptima cifra sobre el P&L de cuenta, o el coste total por lado) | la traducción de costes, que es media verificación, queda comprobada | en instrumentos en yenes el P&L de cuenta difiere por el tipo de cambio fijo de SQX: habría que separar eso |
| 3 | **Si la fila 1 cuenta los dos sentidos** | un EA que opera de más deja de pasar desapercibido | más estrategias fallan; en USDJPY/FTMO el sentido MT5 → SQX es 93 %, por debajo del 95 %: `16.9.76` dejaría de validar |
| 4 | **Si la pareja exige algo de la salida o del precio** | «emparejada» pasa a significar «la misma operación» | más huérfanas; hay que fijar otra tolerancia |
| 5 | **Qué es R** ahora que las finalistas llevan stop | la fila 2 dice lo que el encargo quería | cambia la escala de la fila 2 en todas |
| 6 | **Cuándo se lee el spread** (cualquier momento, sólo con el mercado abierto, o el de la ficha) | que SQX no corra 2,75 años con un spread de un instante cualquiera (domingo 21:22 UTC; no se sabe si con el mercado cerrado) | atarlo al horario complica el lanzamiento desatendido |
| 7 | **Un mínimo de operaciones** para dar veredicto | no validar ni rechazar con una ventana que no puede distinguir (tabla del 4.4) | estrategias de pocas operaciones se quedan sin veredicto en empresas con poco histórico |
| 8 | **Cuántas repeticiones valen** y si el pool recuerda los fallos | la validación deja de poder conseguirse por insistencia | hay que distinguir «repito porque arreglé el reloj» de «repito a ver si sale» |
| 9 | **Qué hacer con una empresa rechazada o una cifra incalculable**: ¿Limbo? | coherencia con el resto del workflow | un estado más en el pool |
| 10 | **La fila 5 sobre flotante con M1** | es la que leen las reglas de la fondeada | es trabajo nuevo; comparte pieza con la conciliación semanal |
| 11 | **Confirmar el formato del pool y conectarlo a la cartera** | el paso 26 pasa a ser de verdad una puerta | hasta entonces la cartera lee pools declarados a mano (`portfolio/common/construct/inputs/pool.py`) sin mirar ningún veredicto del paso 26 |
| 12 | **Una corrida de referencia** antes de tocar umbrales | sabrías qué acuerdo es alcanzable y cuánto es ruido del método | una verificación (unos minutos) y elegir bien la estrategia y el activo |

### 6.4 El límite que no cambia

El paso compara dos simulaciones, no una simulación con la cuenta real. Un «Validada» dice que SQX reproduce al tester de MT5 de esa empresa en el tramo común; lo que pase en vivo —deslizamiento, rechazos, el filtro de noticias, el flotante— lo lee la conciliación semanal, que es otra pieza. Y el tramo común es corto: con dos o tres años y cuarenta operaciones al año, la fila 1 separa un EA por debajo del 85 % de uno fiel si las huérfanas no vienen en rachas, y mal un 93 % de un 97 %.
