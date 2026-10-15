# 62 · Registro único de «ya probado» — una sola respuesta a «¿se probó esta celda?»

**Tu oficio:** contabilidad de búsquedas y corrección por pruebas múltiples; Python sobre el contador
por celda que ya existe (`ledger/cells.py`), sin SQX. **Opus**: cambiar qué se cuenta para el listón
es estadística (regla 17).
**Tu encargo:** (1) **una tabla de «antes y después»** para que el dueño decida si el listón del paso 8
cuenta los lotes por celda (hoy) o por símbolo entero; (2) el aviso de tramos gastados en la campaña,
que el dueño ya contestó; (3) aplicar lo que él elija en las preguntas de abajo, y nada antes de su sí.

> **Cambiar qué se cuenta cambia veredictos.** El paso 8 corta en z ≥ Φ⁻¹(1 − α/B), con α 0,01 y B =
> lotes cribados en `oos1` en la celda (`pipeline/autopilot/criteria.py:93-95`,
> `pipeline/autopilot/judge.py:111-126`, `ledger/cells.py:215-230`). Contar B en otro sitio mueve
> ese listón para todo lo que se juzgue después. La parte 1 sólo lo **calcula de las dos maneras**.

Lee `CLAUDE.md` (reglas 8, 9, 11, 16, 20, 21) · `CODESTYLE.md` · `ledger/README.md` ·
`docs/encargos/65-consenso-cuatro-opiniones.md` §5.1, §5.2 y §6 (sólo esos trozos: `grep -n '^### 5.1\|^### 5.2\|^### 6' …`).

## Estado

| # | parte | modelo | depende de | estado |
|---|---|---|---|---|
| 0 | El comando «¿se probó esta celda?» | — | — | ✅ `python3 -m ledger.cells --ask <SÍMBOLO> <MARCO> [--template T] [--direction D] [--json]` (commit 0df79b2), test `tests/test_ledger_cells.py`. Falta sólo explicar en `ledger/README.md` las dos diferencias de la celda del ejemplo (ver parte 0) |
| 1 | Tabla «B por celda → B por símbolo» | Opus | — | ⬜ |
| 2 | Aviso de tramos gastados en la campaña (pregunta 1, ya contestada) | Sonnet | — | ⬜ |
| 3 | Aplicar B por símbolo y recalcular/marcar lo juzgado | Sonnet | P62-A, P62-D | 🔴 espera al dueño |
| 4 | Tope de cribas en `oos1` | Sonnet | P62-C | 🔴 espera al dueño |

**Bitácora**
- 2026-10-12 — el encargo 65 §5.1 hizo el contador por celda (`ledger/cells.py`: seis enteros por activo ×
  TF × dirección × familia, `Test_` cuenta igual que `Trade_`), el sello del paso 8 (`seal.json`,
  `judgements.csv`) y el tope de 3 miradas a `oos2` («solo vivo», `cells.look_oos2`,
  `ledger:oos2Reading.max_looks`). §5.2 puso el paso 8 a una z del mono con horas con listón por B.
- 2026-10-14 — respuestas del dueño a las preguntas 1-5 (abajo). La parte 1 antigua se hizo sobre `ledger/cells.py`.
- 2026-10-15: reescrito contra el 65 (fila 5 del orden). Fuera: el N por serie de `ledger/trials.py`
  (no juzga nada — ver §0), BH del perfil de mercado (el paso 1 está apagado — pregunta P62-B), y el
  comando `ledger.cell` (existe como `ledger.cells --ask`).

## 0 · De dónde sale, y qué cambió

Revisión del dueño del 2026-10-11 (`~/Desktop/revision-pasos-01-07-2026-10-11.md`) §3: «Un solo registro
de "ya probado". Que cuente los `Test_` y los tramos gastados» y «El número de ensayos por serie de
precios, no por plantilla». §1: «Aplicar BH sobre una familia fijada por propuesta».

Lo que el 65 dejó, comprobado en el código el 2026-10-15:

- **Lo que juzga es B, no N.** El N acumulado de `ledger/trials.py` (Sharpe deflactado) ya no corta en
  ningún paso: sólo se muestra (`core/archive/manifest.py:113`, `ui/daemon/ops/ledgerview.py:65`, el panel
  de variantes `engines/variants/panel.py:162`). La parte 2 antigua («N por serie» sobre `trials.py`)
  no movería ningún veredicto: fuera. La cuenta que juzga es B, la del paso 8.
- **La celda del ejemplo** (`USDJPY M30 doubleROCLong`), hoy con `--ask`: 7 `Test_` (el dossier decía
  11), `oos1` cribado 4 veces ✓, 30 filas sobre `oos2` (decía 24). Sobre el símbolo entero `oos1` lleva
  58 cribas. Explica las dos diferencias en `ledger/README.md` (proyectos retirados o con otro nombre;
  filas de `oos2` escritas después del 2026-10-12): no ajustes la cuenta.
- **El perfil de mercado ya no lanza nada**: el paso 1 está apagado (65 §2; el mapa se regenera a mano).
  BH por familia sellada (pregunta 3, contestada) no tiene hoy propuestas que sellar: pregunta P62-B.
- **La campaña ya cumple la respuesta 1 en lo que mira**: `pipeline/campaign/plan.py:36-42` sólo da por
  lanzada una celda con `Trade_` o `Research_`. Le falta el aviso (parte 2).

## 1 · La tabla «B por celda → B por símbolo» (sólo lectura)

Un script de un solo uso en `scratch/` (no se queda en el código, regla 21; sin `__main__` nuevo en el
repo) que lea `cells.table()` y `judgements.csv`, y escriba `AlgoData/audit/ledger/b-por-simbolo-<fecha>.md`:

| símbolo | celdas | B por celda (máx · mediana) | B por símbolo | z mínima hoy → por símbolo | juicios del 8 que cambiarían |
|---|---|---|---|---|---|

«Juicios que cambiarían»: para cada proyecto juzgado en el paso 8, recalcula con la z del mono que ya
guardó la puerta (`z_mono` en su scorecard, `studies/screening/gate/many.py:50`) cuántas estrategias
pasan con el B de hoy y con el B del símbolo — **sobre lo ya guardado**, sin medir nada nuevo. Nombra las
del almacén que pasarían de Pasa a no pasar. La columna «hoy» debe reproducir los veredictos vigentes
(diferencia 0); si no, para y explica por qué.

## 2 · Aviso de tramos gastados en la campaña (respuesta 1: «un `Test_` gasta tramos, no la celda»)

`pipeline/campaign/plan.py`: al proponer una celda, una línea con lo que `cells.ask(símbolo, marco,
plantilla, dirección)` devuelve de `oos1` (cribas) y `oos2` (filas) — sólo informa, no cambia qué se
propone. Test en `tests/test_campaign.py`: una celda con sólo `Test_` sigue
propuesta y lleva el aviso. Si cambia lo que imprime un comando del manual, actualiza su capítulo (regla 8,
`106-campana.md`).

## 3 · Aplicar B por símbolo (sólo tras el sí a P62-A)

Si el dueño elige A: `per: symbol` en la regla del paso 8 de `pipeline/autopilot/criteria.yaml:112`,
y `judge.per_cell` / `cells.batches_for` cuentan B sobre todas las celdas del símbolo cuando la regla lo
declara. Test en `tests/test_ledger_cells.py`. La edición de `criteria.yaml` queda en
`ledger/criteria-history.jsonl` como las demás (`ledger/README.md:26`) con la frase del dueño. Luego la
respuesta 4 («recalcular y marcar»): los juicios ya hechos se recalculan con la tabla de la parte 1 y se
**marcan** junto a su veredicto en el almacén, sin reescribirlo ni retirar nada (dónde se marca: lo que
diga `core/store/README.md`; si no lo dice, pregunta).

## 4 · Tope de cribas en `oos1` (sólo tras el sí a P62-C)

La respuesta 5 («el workflow se niega a partir de 3 cribas de un tramo») ya se cumple en `oos2`
(`cells.look_oos2`, tope 3). En `oos1` hoy no hay tope: lo cobra el listón α/B. Si el dueño elige A,
el paso 8 se niega cuando `cells.batches_for(proyecto) > 3`, con mensaje claro y su test.

## Lo que no tocas

SQX, en ningún install · `ledger/thresholds.yaml` · `AlgoData/ledger/cells/seal.json` (el sello es uno)
· las filas ya escritas del registro, del libro y de `cells/` · `oos2`, ni una medida nueva sobre `oos1`
· `pipeline/autopilot/criteria.yaml`, `judge.py` y `ledger/cells.py` antes del sí a P62-A/C ·
`studies/research/marketProfile/many.py` (P62-B) · `ledger/trials.py` y `ledger/study.py`.

## Decisiones del dueño — pregúntalas (regla 11)

**Contestadas por el dueño (2026-10-14)** — mandan:
1 → un `Test_` gasta tramos, no la celda. 2 → una serie de precios es el símbolo entero. 3 → familias
declaradas y selladas antes de medir. 4 → recalcular y marcar lo ya juzgado. 5 → el workflow se niega a
partir de 3 cribas de un tramo.

**Nuevas tras el 65** (la respuesta 2 se dio sobre el N de `trials.py`, que ya no juzga):

| código | qué se decide | A | B | recomendación |
|---|---|---|---|---|
| P62-A | ¿La respuesta 2 («serie = símbolo entero») vale para el B del paso 8? | B se cuenta sobre todo el símbolo: en USDJPY pasaría de 4 a 58 lotes, z mínima de 2,81 a 3,58 | B sigue por celda (lo que calibró la corrida nula del 65 §5.4); el símbolo entero se queda en lo que se muestra | **B**, con la tabla de la parte 1 delante: las cribas de M30 y H1 del mismo símbolo leen el mismo `oos1` y están correlacionadas; Bonferroni sobre ellas castiga de más |
| P62-B | BH sobre familia sellada (respuesta 3), con el paso 1 apagado | se quita de este encargo; la respuesta 3 se escribe en `studies/research/marketProfile/README.md` para cuando vuelva el paso 1 | se aplica ya en `many.py` para el tablero que `/research-direct` usa a mano | **A**: hoy no hay propuestas que sellar |
| P62-C | ¿La respuesta 5 pide también un tope en `oos1`? | sí: el paso 8 se niega a partir del 4.º lote en la celda (la celda del ejemplo ya tiene 4) | no: en `oos1` lo cobra α/B; el tope vale para `oos2`, donde ya está | **B**: un tope encima de α/B cobra dos veces la misma mirada |
| P62-D | Si P62-A = A, el cambio de `criteria.yaml` suma una edición a todas las celdas (`cells.edits`) y el sello no se repone | se acepta la edición: queda contada | se permite un segundo sello | **A**: la edición es real y el contador debe verla |

## Objetivo — un comando

```
python3 tools/depmap.py && python3 tools/checks.py \
  && python3 -m pytest tests/test_ledger_cells.py tests/test_oos2_reading.py tests/test_campaign.py -q \
  && ls ~/Desktop/AlgoData/audit/ledger/b-por-simbolo-*.md \
  && grep -q 'doubleROCLong' ledger/README.md
```

Sale 0 con las partes 0 (las diferencias explicadas), 1 y 2 hechas. Las partes 3 y 4 quedan «bloqueadas
por P62-A / P62-C» mientras no haya respuesta, y su test se añade al comando cuando se hagan.

## Cómo cierras

Qué hizo · qué verificó, con la salida del Objetivo y la tabla de la parte 1 pegadas · qué dejó sin hacer
y por qué · qué descubrió para `knowhow/` (qué cuenta juzga y cuál sólo se muestra: B del paso 8 frente al
N de `trials.py`, en `knowhow/pipeline/` o `knowhow/locations/`, editando la ficha que exista) · la lista
de ficheros cambiados y, como última línea, **¿Quieres hacer el commit?**

```
/loop Lee docs/encargos/62-registro-unico-de-ya-probado.md y ejecútalo entero. Tras cada iteración corre el Objetivo; si sale 0, para el bucle; si no, arregla lo que falló y vuelve a correrlo.
```
