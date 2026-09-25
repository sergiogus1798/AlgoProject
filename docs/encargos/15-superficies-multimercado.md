# 15 · Una superficie de parámetros por mercado — encargo autocontenido

**Tu oficio:** una corrida en el custodio y Python. Sale de las secciones **A4** y **B3** del PDF
`PARAMETER_SPACE_TESTS.pdf` del dueño.

Lee `sqx/variants/README.md` · `studies/optimisation/cloud/README.md` · `assets/RULES.md`.

---

**Dónde va** (refactorización del 25-09, `docs/MAPA-DE-CARPETAS.md`): `studies/optimisation/marketSurfaces/` (ya creada con su `README.md`), al lado de `cloud/`, que lee una sola superficie. Forma de
módulo: `studies/CLAUDE.md`; contrato del resultado: `core/study/CONTRACT.md`.

## 0 · La pregunta

Que una estrategia gane en otro mercado es evidencia débil: puede estar simplemente comprada. Que
**la misma región de parámetros** sea la buena en dos mercados distintos ya no lo es, porque una
coincidencia así no la produce el azar de un backtest.

Así que: cada variante del lote se retestea también sobre un conjunto de mercados fijado de
antemano, sale una superficie por mercado, y se miden dos cosas entre cada par (a, b):

```
rho_ab = Spearman(M^a, M^b)                     el orden entre variantes
J_ab   = |T^a ∩ T^b| / |T^a ∪ T^b|              solape de los deciles superiores
```

## 1 · Lo que ya existe y NO se reescribe

| pieza | qué da | dónde |
|---|---|---|
| cosecha por mercado | `equity_markets.parquet`, P&L por día **por variante y por mercado** | `sqx/variants/equity.py` — ya lo escribe cuando los cross-checks están |
| métricas por segmento y mercado | leídas del propio `.sqx` | `sqx/variants/united.py` |
| el conjunto de mercados | fijado por activo, **antes** de mirar nada | `assets/_markets.yaml` |
| la lectura de una sola superficie | A1, A2, A3, B2, C1 | `studies/optimisation/cloud/` |

**Tu trabajo no es la cosecha.** Es (a) conseguir que el retest del lote lleve los cross-checks, y
(b) las dos estadísticas de arriba más la tabla que las lee.

## 2 · Lo que está bloqueado, y quién lo desbloquea

🔴 **Los costes.** `OPEN.md` §27: dieciséis de diecisiete activos siguen sin coste acordado en las
unidades nuevas, y el paso 9 del `WORKFLOW.md` se niega a escribirse sin ellos. Una superficie por
mercado a costes inventados es peor que ninguna. **Antes de nada**: `python3 -m core.assets <SYMBOL>`
para cada mercado del conjunto, reporta lo que falta, y si falta algo **párate y dilo al dueño**.

🟡 **El coste en CPU.** Son J × número de mercados backtests. Con 2.000 variantes y cuatro mercados
son 8.000. Elige los mercados a conciencia, deja escrito cuáles antes de correr, y **repórtalos
todos** — mirar diez y contar los tres donde salió meseta es data snooping, y está escrito como tal
en la sección E del PDF.

## 3 · Verificación

1. La columna del mercado principal de `equity_markets.parquet` tiene que **coincidir** con la
   `equity.parquet` que ya existe. Si no, estás leyendo el bloque de resultados equivocado — es la
   trampa que `sqx/variants/README.md` documenta con las tres curvas de un `.sqx` retesteado.
2. `rho_ab` entre el mercado principal y sí mismo debe dar 1.0. Suena tonto; es el control que
   detecta un emparejamiento de variantes mal hecho.
3. `python3 tools/depmap.py && python3 tools/checks.py` → 0 problemas.

## 4 · Cómo cierras

Página de manual en español con salida real, y una fila en el ledger (encargo 8) diciendo cuántos
mercados y cuántas variantes se miraron. **Mercados y periodos también son búsquedas**: si no queda
registrado cuántos se probaron, el resultado no se puede interpretar después.
