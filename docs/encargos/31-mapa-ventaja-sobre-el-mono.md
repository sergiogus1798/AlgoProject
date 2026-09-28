# 31 · El mapa mercado × parámetro de la ventaja sobre el mono — encargo autocontenido

**Tu oficio:** Python, más un export de operaciones de SQX en el conductor o el custodio.
**Tu encargo es una capa nueva del paso 18.5:** para cada combinación de mercado y nivel de
parámetro, no el beneficio neto, sino **cuánto supera a sus monos**. Una región que bate al azar en
varios mercados es mucho más difícil de fabricar por suerte que una región que sólo gana dinero.

Lee `CLAUDE.md` · `CODESTYLE.md` · `docs/AgentPDFs/WORKFLOW.md` (pasos 16.5 a 20) · `studies/CLAUDE.md` ·
`core/study/CONTRACT.md` · `studies/optimisation/marketSurfaces/README.md` · `engines/nulls/README.md` ·
`studies/readings/monkey/README.md` · `studies/transfer/crossmarket/README.md` · `ledger/README.md`.

---

## 0 · De dónde sale

Del plugin WinRateEdge de StrategyQuant, guía *Parameter Sweeps and Multiple Testing*, §6 (copia en
`~/Downloads/codebase-strategy-vs-random-edge-testing-winrateedge-results-panel/`). Su figura 3 es una
rejilla de mercados por periodos de Donchian, donde cada celda es la z de la entrada contra entradas al
azar. Se lee por columnas, un parámetro que funciona en muchos mercados; por filas, un mercado que responde
en muchos parámetros; y por celdas sueltas, un aviso. El dueño, 2026-09-28: apúntalo como encargo.

**Lo que existe hoy.** El paso 18.5 (`studies/optimisation/marketSurfaces/`) pinta, por cada par de
parámetros, una rejilla por mercado y tramo con **la mediana del beneficio neto** de las variantes de
cada celda, y un mapa de consenso. El beneficio neto mezcla dos cosas: la ventaja de la regla y lo que el
mercado se movió mientras estaba dentro. Un nivel de parámetro que opera mucho en un mercado alcista sale
verde sin predecir nada. El README del 18.5 ya lo avisa: el beneficio de una estrategia larga es, en parte,
exposición por deriva.

## 1 · Objetivos

1. **Por cada celda** (mercado × nivel de parámetro, o mercado × par de niveles), una medida de ventaja
   **contra el mono de la misma celda**: mismas barras, mismos costes de ese mercado, misma huella de trading.
2. **Pintarla como la rejilla del 18.5**, con la misma escala en todos los mercados, y un mapa de consenso:
   en cuántos mercados cada celda bate a su mono con significación.
3. **Corregir por el número de celdas.** Una rejilla de 10 mercados por 30 celdas son 300 pruebas.
4. **Que entre en la lectura ciega del paso 20**, como el resto del 18.5.

## 2 · Qué se mide en cada celda

**La unidad es la variante en un mercado.** Para cada variante del lote y cada mercado, el mono de
`engines/nulls/` sobre las operaciones de esa variante en ese mercado: la p empírica y su z, con el peldaño
de la escalera que decida el dueño (§4). La celda resume las variantes que caen en ella: la mediana de la z
y la fracción de variantes con p por debajo del umbral.

**Por qué no la z del plugin.** El plugin compara tasas de acierto con un error binomial que trata cada
operación como independiente. Las operaciones se solapan en el tiempo, y esa z sobrestima la confianza. El
mono del proyecto no tiene ese problema: compara la estadística real con su distribución bajo el azar,
tirada a tirada.

**Por qué no multiplicar las p entre mercados.** El plugin dice que dos mercados que confirman dan
5 % × 5 % = 0,25 % de azar. Eso sólo vale si los mercados son independientes. US100 y US500, o USDJPY y los
cruces del yen, no lo son. El mapa de consenso cuenta mercados, y el informe dice cuántos grupos
independientes hay entre ellos, con la correlación de sus rendimientos.

**La corrección por pruebas múltiples.** Benjamini-Hochberg sobre todas las celdas de la rejilla, con
`engines/inference/fdr.py`. Una celda verde aislada entre grises es sospechosa aunque su p sea pequeña; el
informe lo dice.

## 3 · El dato que falta, y lo que cuesta

El lote de variantes guarda `equity_markets.parquet`: el P&L **diario** por variante, mercado y tramo. El
mono necesita **las operaciones**, con su hora de entrada, su salida y su tamaño. Hay que exportarlas.

- `sqx.export` ya exporta operaciones de un retest multimercado con la columna `Symbol`
  (`knowhow/export/`). Úsalo, no escribas otro.
- **El volumen es el problema.** Un lote completo son unas 5.000 variantes por 10 mercados. Mide con
  `perf/` el tiempo y el disco de exportar una muestra antes de proponer nada.
- Si el lote entero no cabe, una alternativa: exportar sólo **unas pocas variantes representativas por
  celda**, por ejemplo la mediana de la celda, y decirlo en el informe. Es decisión del dueño (§4).
- El export corre en un worker. Protocolo de las reglas duras 1-3: `ListAgents`, proyectos recientes y
  log del día antes de tocarlo. Si otra sesión lo usa, se espera.

**La puerta de `oos2`.** El 18.5 lee `build` y `oos1` por defecto, y `oos2` sólo si el dueño lo decide
(ver encargo 29, §5). Esta capa hereda esa regla y pide `ledger.gate.allow(18.5, segmento, activo)` antes de
abrir nada.

## 4 · Decisiones del dueño antes de construir — pregúntalas (regla dura 11)

1. **¿Todo el lote o variantes representativas?** Depende de lo que cueste exportar (§3).
2. **El peldaño del mono.** Propuesta: el que fija la huella de trading, frecuencia, duración y dirección,
   y sortea la entrada. Es el que aísla la entrada, que es lo que mide el plugin.
3. **La estadística.** Propuesta: la misma que usa la puerta, para que la celda y la estrategia se lean
   con el mismo número.
4. **El umbral** de la celda verde y la tasa de descubrimientos falsos. Van a `ledger/thresholds.yaml`.
5. **¿Rejilla de un parámetro o de pares?** El 18.5 dibuja pares. Propuesta: pares, para que las dos capas
   se superpongan.

## 5 · Dónde va

Como capa nueva de `studies/optimisation/marketSurfaces/`: una pestaña más en su contrato, con la misma
selección de ejes «Eje X» y «Eje Y», al lado del beneficio neto. El mono se calcula con `engines/nulls/`, sin
copiar nada: `marketSurfaces` importa el motor, nunca otro estudio. Si el cálculo es largo, en paralelo con
`fork` como `crossmarket.report`, e imprimiendo el avance por orden de terminación (`OPEN.md` §47).

## 6 · Verificación

1. **Caso de respuesta conocida.** Un lote sintético con ventaja plantada en unas celdas y mercados
   conocidos: el mapa tiene que encenderlas a ellas y no a las otras.
2. **Un lote sin ventaja.** Variantes de entrada aleatoria: la fracción de celdas verdes tiene que quedar
   en la tasa de descubrimientos falsos elegida.
3. **Coherencia con la puerta.** En la celda de la madre y su mercado, la p de esta capa tiene que coincidir
   con la que la puerta le dio a la madre, si las dos usan el mismo peldaño y la misma estadística.
4. **Un lote real,** con su tiempo y su memoria.

## 7 · Cómo cierras

- Ampliar el capítulo 52 del manual (superficies por mercado) en `AlgoData/manual-fuentes/` con capturas
  reales, y regenerar (regla dura 8).
- La fila del paso 18.5 en `WORKFLOW.md`.
- Tarjeta en `knowhow/` con lo que cueste el export y con lo que enseñe el primer lote real.
- `python3 tools/depmap.py && python3 tools/checks.py`.
- Lista de ficheros cambiados y **¿Quieres hacer el commit?** (regla dura 12).
