# 14 · El mapa de rendimiento condicional — encargo autocontenido

**Tu oficio:** Python sobre operaciones y barras. No toca SQX. Sale del **item 6** del PDF del dueño
`TRADE_LEVEL_TESTS.pdf`.

Lee `CODESTYLE.md` · `strategies/entryQuality/README.md` (el mismo kernel de situar operaciones
sobre la rejilla) · `knowhow/07-practices.md` §«Any statistic measured after selecting on the OOS».

---

## 0 · Qué es

Clasificar cada operación por **el estado del mercado en el momento de entrar**, usando sólo
información disponible entonces, y mirar el rendimiento celda a celda:

- **volatilidad** realizada (p. ej. 20 días) en terciles;
- **tendencia**: ratio de eficiencia `ER = |P_t − P_{t−n}| / Σ|ΔP|` en terciles;
- **sesión** (Asia / Londres / Nueva York / solape) y **día de la semana**.

Por celda: número de operaciones, P&L medio por operación con intervalo por bootstrap, y acierto.

## 1 · Por qué va el último de la tanda, y con condiciones

**Es el único test del PDF que fabrica hipótesis en vez de comprobarlas.** Con tres cortes y varias
celdas por corte, alguna va a salir significativa por azar en cualquier estrategia, incluida una sin
ninguna ventaja. Por eso el propio PDF lo marca como **descriptivo** y prohíbe expresamente sacar
filtros de él sin anotarlos como búsqueda nueva.

Las tres reglas, y no son negociables:

1. **Sin mirar al futuro.** Los umbrales de los terciles salen de una ventana expansiva o del tramo
   de construcción, nunca de la muestra que se está describiendo.
2. **Tamaño mínimo de celda** (30 operaciones, el mismo suelo que `nulls/config.yaml`), y mapas de
   dos dimensiones sólo donde haya celdas pobladas.
3. **Nada de filtros nuevos** sin registrarlos en el ledger (encargo 8) y revalidarlos sobre datos
   que no se hayan mirado.

## 2 · Lo que ya existe

- Situar operaciones sobre la rejilla, la ATR y la reconciliación: `nulls/inputs.py`,
  `nulls/calibrate.py`, usados ya por `strategies/entryQuality/`.
- Barras de cualquier timeframe desde el M1: `core.barstore.read`.
- La sesión declarada de cada activo: `assets/symbols/<SYMBOL>.yaml`, campo `session`. **Úsala**, no
  inventes husos.
- El intervalo por bootstrap sobre una métrica: `core.surface.dedupe.bootstrap_ci`.

## 3 · La pregunta que el mapa sí puede contestar

No «¿qué filtro añado?», sino **«¿de qué depende que esto siga funcionando?»**. Una estrategia que
sólo gana en el tercil de volatilidad alta depende de que ese régimen vuelva, y eso es una propiedad
del objeto que hay que escribir en su ficha — al lado de la concentración temporal que
`strategies/profitShape/` ya mide, que es la misma idea sobre el eje del calendario.

## 4 · Cómo cierras

`python3 tools/depmap.py && python3 tools/checks.py` → 0 problemas, y página de manual en español
con salida real que **empiece** por la advertencia de comparaciones múltiples, no que la esconda al
final.
