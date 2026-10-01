# 37 · La matriz pasa/no pasa del WFM con sus diez condiciones — encargo autocontenido

**Tu oficio:** Python sobre los `.sqx` que SQX ya guardó, más un export en el conductor si hace falta.
**Tu encargo:** que la pestaña «Walk Forward Matrix» enseñe la matriz pasa/no pasa **igual que la de
SQX**. Hoy solo puede juzgar 2 de las 10 condiciones y casi todas las celdas salen «2/2» en verde.
Cada celda tiene que decir qué criterios cumple y cuáles no, y debajo tiene que ir el conjunto de las
30 curvas con estadísticas agregadas.

Lee `CLAUDE.md` · `CODESTYLE.md` · `studies/CLAUDE.md` · `core/study/CONTRACT.md` ·
`studies/optimisation/wfm/README.md` · `knowhow/conditions/wfm-acceptance.md` ·
`knowhow/export/wfm-export.md` · el bloque `wfm:` de `assets/_build.yaml` · `sqx/export/export_wfm.py` ·
`core/wfmatrix.py` · `core/wftrades.py`.

---

## 0 · De dónde sale

Del feedback de la ventana del 2026-09-30, §8.3: «Primero, la matriz pasa/no pasa igual que la de SQX
(exportarla de SQX o reconstruirla). En cada celda, qué criterios se cumplieron, verde/rojo y el
detalle de acierto/fallo. Segundo subpanel: equity curves de las 24-30 celdas juntas, con mediana y
bandas de confianza, y estadísticas agregadas del conjunto.»

La sesión de esa noche reconstruyó la regla de SQX (`studies/optimisation/wfm/measure/gaterule.py`):
la puntuación de una celda es el % de condiciones activas que cumple, y la estrategia pasa si algún
rectángulo `robCombRows × robCombCols` tiene `robMinComb` celdas aprobadas. Pero solo puede leer la
familia `oos`.

**Por qué faltan ocho.** SQX calcula las condiciones a partir de cuatro familias de estadísticos de
cada celda (`knowhow/conditions/wfm-acceptance.md`):

| subresult | familia | condiciones del proyecto que la usan |
|---|---|---|
| 30 | `WF <métrica>`: lo concatenado fuera de muestra | NetProfit > 0, ProfitFactor > 1,05 |
| 31 | `WF Stability <métrica>`: OOS frente a optimización, ×100 | Stability PF > 60, Stability NetProfit > 20, Stability DrawdownPct < 150 |
| 32 | `WF Score of <métrica>`: el WF entero frente al backtest original, ×100 | Score PF > 85 |
| 33 | `WF Special …`: `WFPctOfProfitableRuns`, `WFMaxProfitByRunInPct`, `WFMinTradesInRun`, `WFMaxPctDDbyRun` | las cuatro últimas |

`export_wfm.py` solo exportó el subresult 30. Los otros tres están en los blobs de estadísticos de cada
celda del `.sqx` y nadie los decodificó.

## 1 · Objetivos

1. **Las diez condiciones por celda.** Decodificar los subresults 31, 32 y 33 de cada celda: del `.sqx`
   directamente, o pidiéndoselos a SQX en el export con las columnas `WF Stability …`, `WF Score of …` y
   `WF …` especiales. Elige lo que sea fiable y dilo. Si los calculas tú desde las operaciones por
   pasada, la definición tiene que ser **exactamente la de SQX**: la de la tarjeta de knowhow, con el
   último paso excluido de Stability y las métricas «dependientes del periodo» divididas por días. Tienes
   que demostrar la coincidencia con SQX en al menos una estrategia.
2. **La matriz como SQX la pinta.** Filas = número de pasadas, columnas = % fuera de muestra. En cada
   celda: aprobada o suspendida en verde o rojo, su puntuación (`met/active`), y al pasar el ratón la
   lista de las diez condiciones con su valor, el umbral, y si cumple o no. Marca el mejor rectángulo
   que da por aprobada a la estrategia y la combinación recomendada, que es su centro.
3. **El veredicto de la estrategia** con la regla real de `robCombRows/robCombCols/robMinComb` del
   proyecto, leída de su `project.cfx` o de `WalkForwardConditions` del `.sqx`, no de un valor fijo.
4. **El panel de equity.** Las 24-30 curvas OOS concatenadas juntas, con la mediana y las bandas
   p5-p95, y **una sola tabla de estadísticas agregadas del conjunto**: mediana y dispersión de Net
   Profit, PF, Sharpe (la fórmula clásica sobre todo el tramo, ×√252, días laborables), Max DD, % de
   celdas rentables. Nada de una tabla por curva.
5. **Que la verifique SQX.** Para una estrategia del custodio, la matriz que reconstruyes tiene que dar
   las mismas celdas aprobadas que el `FiltersResultFailedReason` y la matriz de la GUI de SQX con las
   mismas condiciones. Si no coincide, el encargo no está hecho.

## 2 · Lo que ya existe y no hay que rehacer

- `gaterule.score` y `gaterule.area` (la regla), y `computable()`, que hoy se queda en `oos` y dice
  «2 de 10». Cuando las diez sean computables, ese aviso desaparece solo.
- El cono de 30 curvas con la mediana (`measure/equity.py`). Falta la tabla agregada y las bandas.
- La descripción de ρ por celda (glosario de `wfm/many.py`), que está bien.

## 3 · Lo que no puedes hacer

- Tocar la configuración del WFM en un proyecto del dueño. Los umbrales viven en `assets/_build.yaml`.
- Correr nada en el master. Si necesitas un export nuevo, en el conductor (`SQX_w1`), con la regla 2 de
  `CLAUDE.md`.

## 4 · Hecho es

- `Test_USDJPY_donchianUpperCrossUp_H1`, las 15 madres: la matriz con 10/10 condiciones evaluadas y
  coincidiendo con SQX en la estrategia de control.
- La pestaña en la ventana, con el tooltip por celda.
- Un test de respuesta conocida (`tests/test_wfm_*`) con una celda de valores puestos a mano.
- La tarjeta `knowhow/conditions/wfm-acceptance.md` actualizada con cómo se leen 31-33.
