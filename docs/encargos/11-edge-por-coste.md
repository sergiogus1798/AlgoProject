# 11 · Edge por operación y coste de breakeven — encargo autocontenido

**Tu oficio:** Python puro. No toca SQX salvo para un export que ya existe.

Lee `knowhow/09-costs.md` **entero** antes de escribir una línea, y `knowhow/04-export.md` §«El
trade export».

---

## 0 · La pregunta del dueño, ya investigada — léela antes de diseñar nada

> *«Quizás es posible acceder directamente al spread que ha usado cada run del MC Retest.»*

**No lo es, y está medido.** 🔬 `knowhow/01-file-formats.md`: un cross-check de MC Retest guarda
**por simulación únicamente el vector de P/L** — `MonteCarloRetest_Simulation<N>Orders.bin` es un
entero big-endian con el número de operaciones seguido de esos int32 de P/L en céntimos. Cuatro
bytes por operación y nada más: ni fechas, ni precios, ni tamaño, ni dirección, ni el spread
sorteado. Comprobado en 4.896 de 4.896 ficheros.

Lo que **sí** se recupera del MC Retest:

- **El rango sorteado, no el sorteo.** `lastSettings.xml` → `<MonteCarloRetest>` lleva los diez
  métodos con sus `<Params>`, así que se sabe que `RandomizeSpread` fue, por ejemplo, 5–12 puntos
  sobre un spread real de 10 — pero no qué valor le tocó a la simulación 348.
- **Once cuantiles por métrica**, no mil. Los `LevelStat` son 50/60/70/80/90/92/95/97/98/99/100.
- ⚠️ **Y una trampa que hay que escribir en el informe:** un nivel de confianza es un estadístico de
  orden **por métrica**, no un escenario. El NetProfit y el Drawdown de la fila «95 %» vienen de
  simulaciones distintas. Ninguna fila de esa tabla es una curva de equity coherente.

**Conclusión de diseño:** el MC Retest sirve para la curva Sharpe-contra-multiplicador-de-coste, y
para nada más de este encargo. El edge por operación y el breakeven salen del **export de trades**.

## 1 · La segunda trampa: el spread no es un cargo

🔬 `knowhow/09-costs.md`: el spread **va dentro de los precios de fill**, no aparece en el residual
`gross − P/L`. Ahí sólo está la comisión ($16/lote ida y vuelta en el oro). Así que el P&L **bruto**
por operación hay que reconstruirlo:

```
coste_spread_por_trade = defaultSpread × pointValue × Size × (ida y vuelta según convención)
gross ≈ P/L + comisión + coste_spread
```

⚠️ **`Size` varía por operación.** Un `pointValue` constante aplicado a un `Size` fijo da números
mal, y es el error que ya se cometió una vez con MAE/MFE (que además vienen en **moneda de cuenta**,
no en puntos).

⚠️ **OPEN.md issue 26 está abierto y te muerde**: la comisión porcentual puede cobrar por pata o por
operación — un factor de 2 sin medir. Si el activo que analizas la usa, **mídelo antes** con un caso
conocido y escribe el resultado en `knowhow/09-costs.md`. Si no puedes, dilo y marca los números
como provisionales; `pipeline/ledger` ya tiene `costs_provisional` para exactamente esto.

## 2 · Lo que construyes

Carpeta nueva `strategies/edge/`, forma de la casa. Métricas:

| métrica | definición | cómo se lee |
|---|---|---|
| **edge en unidades de spread** | P&L bruto medio por operación ÷ spread medio en la entrada | **media y mediana**, siempre las dos: unos pocos ganadores grandes dominan la media |
| **coste de breakeven `c*`** | el coste de ida y vuelta al que la expectativa neta llega a cero = P&L bruto medio por operación | exprésalo como **múltiplo del coste modelado hoy** |
| **ratio coste/edge** | coste modelado ÷ edge bruto por operación | |
| **curva Sharpe vs multiplicador** | 1x · 1.5x · 2x · 3x | de las salidas del MC Retest que ya existen |
| **desglose por sesión y hora de entrada** | | el spread real es variable: rollover, noticias, apertura |

**La cota se fija en `ledger/thresholds.yaml` (encargo 8) y se fija ANTES de mirar resultados.**
Orden de magnitud de partida: edge ≥ 2–3 spreads por operación. Un umbral ajustado después de ver
los números no es un umbral.

## 3 · Verificación

1. **Reconciliación primero.** Reconstruye el P&L **neto** desde las piezas y compáralo con el que
   SQX reporta, operación a operación. Sin esa conciliación, el bruto es decoración. Precedente: la
   misma puerta salvó el estudio de `nulls/` (0.87 contra un suelo de 0.99 → el fill era
   `open-open`).
2. **Un caso a mano.** Una operación, con sus números escritos en el informe, que cualquiera pueda
   repetir con una calculadora.
3. `python3 tools/depmap.py && python3 tools/checks.py` → 0 problems.

## 4 · Cómo cierras

Página de manual (regla dura 8): `docs/manual/41-edge.md`, en español, con salida real.

Y **escribe en `knowhow/09-costs.md`**, en esta misma tarea, lo que hayas medido sobre la comisión
porcentual (issue 26) — es el hallazgo más valioso que puede salir de este encargo.
