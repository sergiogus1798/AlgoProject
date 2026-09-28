# 29 · La meseta en el tiempo — encargo autocontenido

**Tu oficio:** Python. Lee lotes de variantes ya retesteados; SQX no interviene.
**Tu encargo es comprobar si la región buena de parámetros —la meseta— está en el mismo sitio y
tiene la misma forma en `build`, en `oos1` y en `oos2`, cada uno por separado**, en el mercado de la
estrategia. Y, con el tiempo, si leer una meseta predice algo en este proyecto.

Lee `CLAUDE.md` · `CODESTYLE.md` · `docs/AgentPDFs/WORKFLOW.md` (pasos 16.5 a 20) · `studies/CLAUDE.md` ·
`core/study/CONTRACT.md` · `studies/optimisation/marketSurfaces/README.md` ·
`studies/optimisation/cloud/README.md` · `studies/optimisation/wfc/README.md` · `ledger/README.md` ·
`assets/_policy.yaml`.

---

## 0 · De dónde sale

Del dossier `docs/AgentPDFs/ideas-de-internet-y-libros-2026-09-27.md`, §1.3. Katz (p. 45): «la tolerancia
de los parámetros no sirve para medir la robustez». Su contraejemplo (pp. 100-103): una ruptura de
volatilidad rentable con los cien juegos de parámetros dentro de muestra y con ninguno fuera. Una meseta
protege de afinar un número hasta el punto exacto, pero no de ajustarse al periodo: si el build cae en
un tramo concreto, toda una región puede ganar allí y perder junta después. El dueño, 2026-09-28:

> *«Sería buena idea mirar las mesetas en periodos diferentes. Es decir, mirar si la posición y forma
> de la meseta coinciden en el IS separado, en el oos1 separado y en el oos2 por separado. Eso es un
> poco también aplicarlo a diferentes mercados y ver las mesetas allí.»*

## 1 · Lo que ya existe, y el hueco

| pieza | qué compara | lo que no hace |
|---|---|---|
| WFC, paso 17 | el orden de **todas** las variantes dentro contra fuera | no dice dónde está la región buena ni su forma |
| nube, `cloud` | si la forma de la superficie aguanta cortada en periodos, dentro de `build` y `oos1` | no llega a `oos2` y no compara la posición de la región buena |
| superficies por mercado, paso 18.5 | la misma región buena **entre mercados**, por tramo: Spearman, solape del decil superior y mapa de consenso | no compara **tramos entre sí** en el mismo mercado |

La parte «en otros mercados» de la idea del dueño ya es el paso 18.5. Lo que falta es exactamente lo
mismo, pero con los tramos en el lugar de los mercados.

## 2 · Objetivos

1. **Parte A — la meseta entre tramos.** Para cada madre con lote de variantes, y en su mercado:
   ¿la región buena de `build` es la región buena de `oos1` y de `oos2`?
2. **Parte B — ¿predice la meseta?** Acumular, madre a madre, la lectura de meseta o pico y lo que
   pasó después, hasta poder responder con el ledger si las madres en meseta sobreviven más.
3. Que las dos dejen sus filas en el ledger, respeten la puerta de `oos2` y se lean a ciegas en el
   paso 20, como el resto de 17 a 19.

## 3 · Parte A — la meseta entre tramos

**Dónde va.** Como ampliación de `studies/optimisation/marketSurfaces/`, no como estudio nuevo: ya
tiene la métrica, el decil superior, el mapa de consenso, la deduplicación de variantes y la
neutralización por exposición. Los pares dejan de ser sólo mercado contra mercado y pasan a incluir
tramo contra tramo en el mercado de la madre: (`build`, `oos1`), (`build`, `oos2`), (`oos1`, `oos2`).

Por cada par de tramos:

| medida | qué dice |
|---|---|
| `rho` de Spearman | si el orden de las variantes se mantiene |
| `J`, solape del decil superior | si las mejores son las mismas. Por azar, `J` sale cerca de lo que da un decil elegido al azar; el informe lo pone al lado, con un nulo por permutación |
| **desplazamiento del centro** | dónde está el centro de la región buena en cada tramo, en unidades de cada parámetro normalizado, y cuánto se movió |
| **forma** | el área de la región buena y si es una sola mancha o varias, con la regla de meseta o borde que ya usa `cloud` |
| la madre dentro | si el punto de la madre cae dentro de la región buena de cada tramo |

**Lo que ve el dueño.** Las mismas rejillas por par de parámetros que el paso 18.5 dibuja por mercado,
aquí una por tramo, lado a lado y con la misma escala de color. Y el **mapa de consenso entre tramos**:
en cuántos tramos cada celda está en el decil superior, de 0 a 3. Una meseta que se sostiene es una
mancha alta y continua, con la madre dentro. Una que se mueve o se deshace se ve a simple vista.

**Qué no hace.** No elige parámetros. Una región que aguanta los tres tramos no es una invitación a
mover la madre hacia su centro: el PDF del dueño prohíbe sustituir la madre por el mejor clon.

## 4 · Parte B — ¿predice la meseta?

Una tabla que crece con cada madre que llega al paso 20:

| columna | de dónde sale |
|---|---|
| la lectura de `cloud`: meseta o pico | `cloud.json` del lote |
| el consenso entre tramos de la parte A | este encargo |
| lo que pasó: sobrevive o no al paso 20, y su resultado en `oos2` | la lectura conjunta del paso 20 y el ledger |

Con ella, una tabla de contingencia y su p exacta de Fisher: ¿las madres en meseta sobreviven más que
las de pico? Mientras haya pocas madres, el informe dice cuántas hay y que todavía no se puede concluir,
**sin inventar un veredicto**. Esta es la comprobación que pide Katz. Si con suficientes madres la meseta
no predice nada, la lectura de meseta es decorativa, y eso también es un resultado.

## 5 · La puerta de `oos2`, y la lectura a ciegas

- `assets/_policy.yaml` reserva `oos2` para `WFC, CSCV, MarketSurfaces, WFM, ATRStop`. Esta
  ampliación vive dentro de MarketSurfaces, así que puede leer `oos2`, siempre pidiendo antes
  `ledger.gate.allow(18.5, segmento, activo)` y dejando una fila por tramo leído.
- Hoy `marketSurfaces` sólo lee `build` y `oos1` por defecto, y su README dice que añadir `oos2` es
  decisión del dueño. **Pregúntalo antes de construir** (regla dura 11): la política lo permite, pero
  el módulo nunca lo ha hecho.
- El paso 18.5 forma parte de la lectura conjunta y ciega del paso 20. Los resultados de esta
  ampliación **se retienen** hasta que 17, 18, 18.5 y 19 estén todos hechos: `ledger.gate.allow_read`.
  La ventana tampoco los pinta antes.

## 6 · Decisiones del dueño antes de construir — pregúntalas

1. **¿Se incluye `oos2` en la comparación entre tramos?** Propuesta: sí, porque es el tramo que más
   dice, y la política ya lo reserva para este paso.
2. **La métrica.** Propuesta: el beneficio neto por tramo, la misma del WFC y del 18.5, para que las
   tres lecturas hablen del mismo número. ¿Añadir el factor de beneficio como segunda lectura?
3. **El tamaño de la región buena.** Propuesta: el decil superior, el mismo `top_share` del 18.5.
4. **Los tramos de distinta longitud.** `oos2` es más corto que `build`. El beneficio neto de un tramo
   corto es más ruidoso y su decil superior, menos estable. Propuesta: se compara el orden, no el
   nivel, y el informe dice la longitud de cada tramo.

## 7 · Verificación

1. **Caso de respuesta conocida.** Un lote sintético donde la región buena se desplaza una cantidad
   conocida entre tramos: el desplazamiento medido tiene que coincidir. Y otro donde no se mueve: `J`
   tiene que salir alto y el desplazamiento cerca de cero.
2. **El nulo sale donde debe.** Con los tramos barajados entre variantes, `J` tiene que caer al valor
   de azar.
3. **Nada de `oos2` sin permiso.** Un test en el que la puerta niega `oos2` y el módulo se para antes
   de abrir un fichero, igual que el que ya existe para el 18.5.
4. **Un lote real.** Uno de los tres lotes de USDJPY que usó el 18.5, con su tiempo y su memoria.

## 8 · Cómo cierras

- Ampliar el capítulo 52 del manual (superficies por mercado) en `AlgoData/manual-fuentes/`, con
  capturas reales, y regenerar con `python3 tools/manual.py` (regla dura 8).
- La fila del paso 18.5 en `WORKFLOW.md`, diciendo que ahora compara también tramos.
- El known-answer test en `tests/test_marketsurfaces.py`.
- Tarjeta en `knowhow/research/` con lo que salga del primer lote real.
- `python3 tools/depmap.py && python3 tools/checks.py`.
- Lista de ficheros cambiados y **¿Quieres hacer el commit?** (regla dura 12).
