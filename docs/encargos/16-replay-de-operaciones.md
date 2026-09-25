# 16 · El simulador de replay de operaciones — encargo autocontenido

**Tu oficio:** Python numérico. No toca SQX. Sale del **item 4, tier 2** del PDF del dueño
`TRADE_LEVEL_TESTS.pdf`, y es el único de ese documento que no se pudo construir el 2026-09-24.

Lee `CODESTYLE.md` · `strategies/entryQuality/README.md` · `knowhow/04-export.md` §«El trade
export» · `nulls/README.md` §reconciliación.

---

## 0 · Qué es y qué no es

**No es un motor de backtest.** Las entradas vienen de SQX y la lógica de entrada no se
reimplementa nunca. El simulador sólo vuelve a ejecutar cada operación desde una entrada
—posiblemente desplazada `d` barras— caminando el M1 hasta que algo la cierra.

Existe porque el **tier 1 ya construido** (`strategies/entryQuality/delay.py`) supone que las
salidas no se mueven. Eso es correcto para salidas por señal y por número de barras, y **falso para
un stop o un target**, que se recalculan desde el precio de entrada nuevo.

## 1 · Lo ya investigado — no lo repitas

🔬 Medido el 2026-09-24 sobre `XAUUSD/MC_Trades` (960.705 operaciones, 236 estrategias):

- **SQX sí exporta la razón de salida**, en la columna `Close type`. En esta población hay
  exactamente tres valores: `Exit After X Bars` (720.874), `Exit Signal` (187.853) y
  `End Of Friday (Time)` (51.978). **Ni un solo SL o TP.**
- Esto tiene dos consecuencias y conviene entender las dos: (a) el tier 1 es legítimo sobre esta
  población, y (b) **sobre esta población no puedes validar la parte del simulador que más importa**,
  que es la que recalcula stops. Necesitarás una estrategia con stop; si no existe todavía, dilo y
  párate antes de escribir el recálculo a ciegas.
- **El M1 del oro son 7.949.285 barras y se cargan en 0,4 s** con `core.barstore.source`. No hace
  falta memory-mapping ni cargar por trozos, al contrario de lo que sugiere el PDF.
- `core.trades` y `nulls.calibrate` ya dan lo que necesitas por operación: `point_value` medido de
  los propios trades (99.85 contra 100 configurado en el oro), el coste real `bruto − neto`, y
  `nulls.inputs.on_grid` para situar cada operación en la rejilla.

## 2 · El criterio de aceptación, que es el encargo entero

**Con `d = 0` el simulador tiene que reproducir la lista de operaciones de SQX**: mismos instantes
de salida, misma razón de salida, y P&L dentro de una tolerancia pequeña. Antes de eso, ningún
resultado con retraso vale nada.

Reporta la **tasa de coincidencia** e investiga cada discrepancia. El precedente está medido y es
exactamente el mismo patrón: `nulls/calibrate.convention()` encontró que el fill es `open-open` con
una correlación de **0.999985**, y el runner-up daba 0.9629 — la reconciliación es lo que licenció
todo lo demás de aquel módulo. Sin ella habría sido decoración.

Causas típicas de discrepancia, en orden de probabilidad: precisión intrabarra, modelo de spread,
redondeo, swap.

## 3 · Las decisiones que el PDF deja abiertas y hay que cerrar por escrito

| situación | qué decidir |
|---|---|
| SL y TP tocados en la misma barra M1 | el PDF propone asumir SL primero (conservador). **Mide la convención de SQX antes de asumirla** |
| la operación dura menos que el retraso | no existe: se descarta, y se reporta la fracción descartada por `d` |
| salida por señal desconocida tras un SL/TP que ya no ocurre | dejarla correr hasta su propio SL/TP o un tope de duración, marcarla, y **reportar la fracción marcada**: si es grande, el tier 1 es más fiable que el tier 2 |
| entradas pendientes (stop/limit) | ¿retrasar la colocación de la orden o desplazar el nivel? Documenta la elección |

Y las dos variantes van las dos, porque responden a cosas distintas: **retraso sólo en la entrada**
(prueba la robustez temporal de la señal) y **latencia completa**, entradas y salidas por señal
retrasadas (el caso real en vivo).

## 4 · Rendimiento

El PDF propone Numba. **No está en `requirements.txt` y añadir una dependencia compilada a este
proyecto es decisión del dueño** — `sudo` pide contraseña en esta máquina y las ruedas se instalan
en `~/.local`. Antes de pedirla: el camino se puede vectorizar por lotes de operaciones con numpy
(el mismo truco que `nulls/barrier.py` usa para el triple barrier sobre miles de corridas a la vez),
y ese módulo ya demuestra que se puede. Mide primero, pide dependencia después.

## 5 · Cómo cierras

`python3 tools/depmap.py && python3 tools/checks.py` → 0 problemas · página de manual en español con
salida real · y **escribe en `knowhow/04-export.md`** la convención intrabarra que midas. Es el dato
que hoy no tiene nadie y el que hace reutilizable todo lo demás.
