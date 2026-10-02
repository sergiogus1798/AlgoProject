# 39 · Edge por coste: cuánto se mueve la ventaja con cada coste, swaps incluidos — encargo autocontenido

**Tu oficio:** Python sobre la cosecha que ya existe. No toca SQX.
**Tu encargo:** completar `studies/readings/edgeCost/` para que responda a la pregunta del dueño:
**cuánto se mueve el edge de una estrategia en función de los costes** (comisión, swap, spread y
slippage), con una tabla por coste, y el swap medido o modelado, no deducido de un residuo.

Lee `CLAUDE.md` · `CODESTYLE.md` · `studies/CLAUDE.md` · `core/study/CONTRACT.md` ·
`studies/readings/edgeCost/README.md` · `costs.py` · `spread_share.py` · `one.py` · `many.py` ·
`knowhow/costs/where-the-spread-is.md` · `knowhow/costs/swap-types.md` · `assets/RULES.md` · el bloque
de costes de `assets/symbols/USDJPY.yaml` · `assets/_policy.yaml` (convenciones de swap).

---

## 0 · De dónde sale

Del feedback de la ventana del 2026-09-30, §9.5: «Concepto: cuánto se mueve el edge en función de los
costes (comisiones, swaps, spread…). Añadir tablas con comisiones, swaps y valores como median gross,
min gross, median min cost, etc.» Y: «la línea que ocupa todo el ancho de la pantalla no hace falta:
el valor en una tabla, verde si es bueno y rojo si es malo».

La sesión de esa noche añadió la tabla coloreada, la media, mediana y mínimo del bruto y del coste, y
una tabla de comisión. **Falta el swap.** Hoy el swap solo aparece como «residual medio» de la
reconciliación, es decir, lo que no cuadra entre el bruto reconstruido y el P&L de SQX. Ese residuo
mezcla swap con redondeos, y la exportación de SQX no trae columna de swap.

## 1 · Objetivos

1. **El swap de cada operación, modelado.** Noches que cruza la operación (con la noche triple del
   activo, `assets/_policy.yaml`) × el swap largo o corto del activo en puntos (`assets/symbols/*.yaml`,
   `swap_long` y `swap_short`), convertido a dinero con el valor del punto y el tamaño. Contrástalo con
   el residuo de la reconciliación. Si el residuo medio y el swap modelado no cuadran dentro de un
   margen que tú midas, el informe lo dice y explica por qué (por ejemplo, SQX sin swap en ese proyecto).
2. **Una tabla por coste**, cada una con el bruto por operación, el coste medio y mediano por operación,
   y lo que queda de edge:
   - comisión
   - swap (con el reparto largos / cortos y el nº de noches)
   - spread (el medido, `spread_share`)
   - slippage (el modelado del activo)
   - y el total
3. **La sensibilidad.** El edge por operación y el Profit Factor neto con cada coste multiplicado por
   0, 0,5, 1, 1,5, 2 y 3, de uno en uno y todos a la vez. Para cada coste, **el múltiplo de punto
   muerto** (a qué multiplicador el edge llega a 0). Es la pregunta «cuánto margen tengo si este coste
   empeora». En tabla, coloreada: verde con margen, rojo con poco. El umbral del color lo propones tú
   con datos y lo fija el dueño.
4. **En la población (`many.py`)**, las mismas columnas resumidas por estrategia: el punto muerto de
   cada coste y qué coste muerde antes. Así se puede ordenar el databank por ellas.
5. **Nombres como pidió el dueño:** median gross, min gross, median min cost y similares; los términos
   técnicos en inglés como en el resto de la ventana, el resto en castellano, con mayúscula inicial y
   «?» en cada columna.

## 2 · Lo que no hay que tocar

- El umbral `min_edge_spreads` y `action` de `config.yaml` son del dueño.
- La medida del spread (`spread_share.py`) está revisada: úsala, no la cambies.

## 3 · Hecho es

- Re-run en un directorio temporal sobre la cosecha de `Test_USDJPY_donchianUpperCrossUp_H1`, una
  estrategia y la población: las cuatro tablas, la sensibilidad y el punto muerto.
- Un test de respuesta conocida: unas pocas operaciones puestas a mano con swap conocido (una que cruza
  la noche triple) y el punto muerto calculable a mano.
- `README.md`, tooltips y el capítulo del manual (`AlgoData/manual-fuentes/`, el del paso 25) al día, y
  `python3 tools/manual.py`.
