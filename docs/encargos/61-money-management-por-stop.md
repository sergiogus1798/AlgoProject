# 61 · Money management por stop loss — sólo queda 61-4c

El informe (`AlgoData/audit/money-management/por-stop-2026-10-14.md`) y las respuestas del dueño (2026-10-14 y 2026-10-15) están implementados en `mt5/verify`:
dos modos de concordancia MT5-SQX que tienen que pasar los dos (1 lote fijo y 1.000 USD de riesgo desde el SL, `mt5/verify/config.yaml` `modes`), tolerancia al 10 %
(`mt5verify.trade_gap_max_r` y `mt5verify.size_gap_max_pct`), `own_sizing` acepta `FixedAmount`, fila 6 de tamaño y fila 7 de tope de pérdida real (la estrategia FALLA si salta).

## Pendiente

- **61-4c · la cifra de `mt5verify.loss_cap_usd`** (USD, la pérdida real máxima de UNA operación en el modo de riesgo): sigue sin valor en `ledger/thresholds.yaml` y `mt5.verify.run` se niega a arrancar con un error que nombra la clave hasta que el dueño la dé. No se inventa.
- **Para el dueño, nuevo:** el paso 24 está eliminado (2026-10-11) y las estrategias de la doctrina no llevan stop, así que el modo de riesgo queda «Sin veredicto» para todas y, con los dos modos obligatorios, el paso 26 no valida ninguna hasta que la estrategia lleve stop o él decida otra cosa. La fila 7 está en el juez del paso 26, no en un «paso 24» que ya no existe.
