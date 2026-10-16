# 75 — Cifras únicas: una sola definición de cada métrica, y los cuatro arreglos cuant

## Estado (cada sesión actualiza su fila)

| parte | qué | estado |
|---|---|---|
| A | `engines/metrics.py`: Sharpe, `dd_money`, `dd_pct`, profit factor, años, constantes | hecho 2026-10-16 — en `core/metrics.py`, no en `engines/`: `core/significance.py` y `sqx/variants/united.py` lo llaman y por capas ni `core` ni `sqx` pueden importar `engines` |
| B | Borrar las copias y llamar a la única, con tests que fijen los números | hecho — `tests/test_metrics_unique.py` fija las cifras de las copias borradas; quedan las formas rápidas (núcleo numba, mcRetest, CSCV) atadas a las mismas reglas por test. Sin tocar: el PF del Monte Carlo de cartera (NaN sin pérdida, difiere más allá del caso plano) y los años `(días+1)` de `verdict/metrics.py` — cartera congelada |
| C | Ventanas: `last_day()`, `drift()` y `latest_harvest()` únicos | hecho — `core.assetdata.first_day/last_day`, `gate.inputs.drift`, `core.paths.latest_harvest` (lanza error con proyecto y databank en vez de `None`). Pendiente: ALPHA/SEED al ledger — `improvement`, `replication` y `monkeyExcess` no tienen `config.yaml` al que apuntar |
| D | Semilla del benchmark por madre; NaN explícito; `share_null` vacío; terciles de régimen | D1, D2 (core: `Psr.state`, `Deflated.state`), D3 y D5 hechos (D5: 0 de 123 lotes reales lanzan). D2 de `portfolio/…/deflate.py` y D4 (su único llamador es el MC de cartera) bloqueados por la cartera congelada |
| E | DSR/PSR con n efectivo: **medir antes y después, aplicar solo con el sí del dueño** | medido, parado en E3: 64.261 estrategias de 66 cosechas del paso 8, 1.472 → 1.458 pasan (14 caen, todas marginales, USDJPY M30 doubleROC); store 0 cambios de 681. Espera el sí del dueño |

## Tu oficio

Eres el **orquestador, en Opus**: las definiciones de A y la medida de E son estadística (regla 17).
B y C son mecánicas: repártelas a subagentes `general-purpose` con `model: "sonnet"`, un paquete por
subagente (`studies/`, `portfolio/`, `ui/daemon/`, `sqx/`+`mt5/`), lanzados a la vez porque no
comparten fichero. Cada uno recibe su parte copiada en el brief, no el fichero entero.

## Tu encargo

Que una misma estrategia dé **el mismo Sharpe, el mismo drawdown y el mismo profit factor** en todos
los pasos, en la ventana y en MT5 contra SQX. Hoy hay 8 Sharpe y 16 drawdown que no coinciden en los
casos límite. Devuelves al dueño una tabla: qué cifra cambió, dónde y en cuánto, sobre las
estrategias del almacén.

## §0 De dónde sale

Revisión estructural del 2026-10-16 (`AlgoData/audit/refactorScout/2026-10-16.md`, hallazgos
`dup-sharpe-copies`, `dup-drawdown-copies`, `dup-years-span`, `dup-window-end-drift`,
`dup-newest-harvest`, `dup-profit-factor`, `dup-constants`, `quant-*`). Decisiones del dueño, el
mismo día: drawdown en **dos funciones con nombre**; Sharpe de una serie plana = **NaN**; las copias
de `portfolio/` **se tocan solo para llamar a la función única** (la cartera sigue congelada:
ninguna lógica nueva allí); el DSR con **n efectivo, midiendo antes**; la semilla del benchmark
**salada por madre**.

## Parte A — Las definiciones (Opus)

`engines/metrics.py`, un módulo, sin clases:

- `sharpe(returns, periods_per_year)` — NaN si hay menos de 2 rendimientos o la desviación es 0.
  `periods_per_year` siempre explícito: 252 para diarios de SQX, 52 para semanales.
- `dd_money(curve)` — el pico arranca en el primer valor de la curva.
- `dd_pct(curve, deposit)` — el pico arranca en el depósito. Es la que usa todo lo de cuentas y MT5.
- `profit_factor(pnl)` — inf si no hay pérdidas y sí ganancias; NaN si no hay operaciones. La
  ventana lo pinta como «∞» o «—», nunca como None.
- `years(first, last)` — `(last - first).days / 365.25`, **una** convención; documenta en la
  docstring por qué no `+1`.
- `TRADING_DAYS = 252`, `YEAR_DAYS = 365.25`.

Lee primero las copias para ver qué hace cada una: `core/significance.py:197`,
`engines/nulls/stats.py:13,30,45`, `engines/nulls/kernel.py:11`, `mt5/verify/judge.py:58`. La forma
vectorizada de `engines/nulls/stats.py` se queda allí si es más rápida, pero llamando a las mismas
reglas de borde (un test lo fija).

## Parte B — Borrar las copias (Sonnet, por paquete)

Antes de tocar nada: `tests/test_metrics_unique.py` corre cada copia actual y la nueva sobre cuatro
curvas (normal, plana, sin pérdidas, vacía) y **fija** que coinciden en la normal. Luego cada copia
se borra y su llamador usa `engines.metrics`. Las copias están listadas en el informe; búscalas otra
vez con `grep -rnE "def .*(sharpe|drawdown|profit_factor)|cummax|maximum.accumulate|sqrt\(252\)|365\.25|/ ?365\b" --include=*.py`
fuera de `scratch/`, `tools/sqx-lab/` y `tests/`.

- **`portfolio/`**: solo se borra la copia y se cambia la llamada. Si una copia de allí hace algo
  distinto de la regla nueva en algo que no sea el caso plano, **para y pregunta**.
- **`mt5/verify/judge.py`** pasa a `dd_pct(curve, deposit)`; el SQX que compara, también.
- `ui/daemon/databank/equity.py:51` y `ui/daemon/strategy/costcurve.py:17` son idénticas: las dos
  pasan a `dd_money`. Si el 77 ya movió esas carpetas, ve a su nueva ruta.

## Parte C — Ventanas y cosechas (Sonnet)

- `core/assetdata.last_day(to)` sustituye a los cinco `f"{last}-12-31" if isinstance(last, int)`
  (`wfc/inputs/batch.py:44`, `cscv/inputs/batch.py:42`, `wfm/inputs/asset.py:52`,
  `marketSurfaces/inputs/batch.py:47`, `crossmarket/inputs/markets.py:122`) y a `core/assets.py:_day`.
- Un `drift()` en `studies/screening/gate/` sustituye a las seis copias (`wfc/inputs/batch.py:28`,
  `cscv/inputs/batch.py:34`, `marketSurfaces/inputs/batch.py:34`, `cloud/inputs/cloud.py:40`,
  `wfm/inputs/asset.py:62`, `mcRetest/neighbours/t1.py:138`); el `parents[3]` de `cscv` desaparece.
- `latest_harvest(project, databank) -> Path | None` sustituye a los seis `newest()`; quien no
  encuentra cosecha lanza un error que dice qué proyecto y databank, en vez de un `IndexError`.
- `ALPHA` y `SEED` sueltos: el α pasa a leerse del ledger (`ledger:<clave>`, fila nueva al final de
  su sección); las semillas, de la config de cada estudio.

## Parte D — Cuatro arreglos cuant (Opus revisa, Sonnet escribe)

1. **Semilla del benchmark por madre**: `engines/nulls/footprint.py:63` y
   `studies/optimisation/oos2Reading/report.py:~48` — `SeedSequence([seed, crc32(name)])`, como ya
   hace el null de volteo.
2. **NaN explícito**: `core/significance.py:23` y `portfolio/common/construct/verdict/deflate.py:~48`
   — un Sharpe o un DSR NaN da el estado `"undefined"`, no `"fail"` por accidente; el ledger no
   guarda NaN sin estado.
3. **`share_null` con familia vacía** (`engines/inference/excess.py`): devuelve «sin pruebas», no NaN.
4. **Terciles de régimen** (`engines/regimes/regime.py:137`): bordes ajustados solo en `build`.
5. **Calentamiento** (`engines/variants/panel.py:142`): un `assert` de que las fechas repetidas
   tienen como mucho un valor distinto de cero.

## Parte E — DSR y PSR con n efectivo (Opus; se para antes de aplicar)

`core/surface/plateau.py:109-113` y `ledger/trials.py:137` usan √(n−1) con rendimientos i.i.d.

1. Escribe la versión con n efectivo (`n_eff = n / (1 + 2 Σ ρ_k)`, con los retardos que justifiques
   en la docstring) **al lado**, sin cambiar la de producción todavía.
2. Recalcula con las dos todas las estrategias del almacén (`/store-open`) y las corridas guardadas
   del paso 8. Saca la tabla: estrategia, DSR viejo, DSR nuevo, ¿cambia de veredicto?
3. **Para y enséñasela al dueño.** Solo con su sí sustituye la vieja (regla 21: la vieja se borra) y
   edita la ficha `knowhow/research/psr-dsr-two-conventions-jsharpe.md` con lo medido.

## Decisiones del dueño — pregúntalas (regla 11)

- E3: ¿se aplica el n efectivo, a la vista de la tabla?
- Cualquier copia de `portfolio/` que difiera en algo más que el caso plano.

## Lo que no tocas

El master; `oos2`; la lógica de `portfolio/` (solo cambian las llamadas); `ledger/thresholds.yaml`
salvo la fila del α; ficheros con cambios sin commitear de otra sesión (`git status` antes de cada
parte: hoy hay en `studies/screening/gate/inputs.py` y `studies/optimisation/marketSurfaces/`).

## Objetivo — un comando

(La exclusión es `core/metrics.py`: el módulo vive en `core/` por capas, ver fila A.)

```bash
python3 -m pytest tests/test_metrics_unique.py -q && \
! grep -rnE "def (annual_)?sharpe|def (max_)?drawdown|sqrt\(252\)" --include=*.py core studies portfolio sqx ui mt5 pipeline engines ledger | grep -v '^core/metrics.py' && \
python3 tools/depmap.py && python3 tools/checks.py
```

## Cómo cierras

Qué hizo · qué verificó, con la salida pegada · qué dejó sin hacer y por qué · qué descubrió para
`knowhow/`. `graphify update . && python3 tools/projectmap.py` (regla 22). La lista de ficheros
cambiados y **¿Quieres hacer el commit?**

/loop Lee docs/encargos/75-cifras-unicas.md y ejecútalo entero. Tras cada iteración corre el Objetivo; si sale 0, para el bucle; si no, arregla lo que falló y vuelve a correrlo.
