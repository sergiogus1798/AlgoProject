# 10 · SPA de Hansen y StepM de Romano–Wolf — encargo autocontenido

**Tu oficio:** Python puro. No tocas SQX, no gastas CPU de máquina, no quemas ventanas nuevas si lo
colocas donde dice el §2.

Lee `CODESTYLE.md` · `studies/screening/gate/README.md` · `studies/optimisation/wfc/README.md`.

---

## 0 · Qué pregunta añade, y por qué no la contesta el CSCV

Ya tenemos CSCV/PBO. Pregunta **si la forma de elegir sobreajusta**. Esto pregunta otra cosa:
**qué estrategias concretas baten al benchmark una vez descontada toda la búsqueda**. Son
complementarias y no se sustituyen.

⚠️ **No corren sobre la misma matriz, y quien diga lo contrario no ha mirado el código.**

| | CSCV (paso 18, construido) | SPA / StepM (tú) |
|---|---|---|
| columnas | las **variantes de UNA madre** | las **K supervivientes de la población** |
| filas | períodos semanales de P&L | retornos diarios |
| de dónde | `sqx/variants/equity.py` → panel del lote | `studies/screening/gate/collect.py` → equity diaria de la cosecha |
| pregunta | ¿mi regla de elegir parámetros sobreajusta? | ¿cuáles baten al benchmark contando toda la búsqueda? |

## 1 · Dónde va — **decisión del dueño, dos sitios posibles**

- **A · pegado al paso 8**, tras la puerta OOS, sobre `oos1`. Reusa la cosecha que ya se hace
  (`studies/screening/gate/harvest.py` lee los dos databanks una vez y nada vuelve a tocar SQX), criba pronto y
  barato. Coste: una mirada más a `oos1`.
- **B · dentro del paso 20**, con el análisis ciego de 17-18-19. Es donde la pregunta de verdad
  decide, pero llega tarde para ahorrar máquina.

**Recomendación: A para cribar y B para decidir**, el mismo test dos veces sobre poblaciones
distintas. Son **dos miradas** y las dos se registran en el ledger del encargo 8. Si el dueño no ha
elegido cuando llegues aquí, construye el módulo agnóstico del sitio —toma un panel y devuelve un
veredicto— y no lo cablees a ningún paso hasta que lo diga.

## 2 · Lo que construyes

Tres sitios, ya creados con su `README.md` (refactorización del 25-09, `docs/MAPA-DE-CARPETAS.md`):
el motor en `engines/inference/snooping/` (SPA y StepM calculan, no juzgan), la criba de la cosecha
en `studies/screening/snoopingScreen/` y la prueba conjunta ciega del paso 20 en
`studies/closing/blindJoint/`. Los dos estudios con la forma de `studies/CLAUDE.md` (`config.yaml`,
`tooltips.py`, `one.py`/`many.py`, `report.py`) y el contrato de `core/study/CONTRACT.md`.

**Entrada.** Matriz T×K de retornos diarios de las K candidatas que pasaron los filtros de SQX. Ya
existe: `studies/screening/gate/collect.py` se lleva métricas, trades y equity diaria en una sola pasada.

**Benchmark.** Cero, o una estrategia ingenua sobre el mismo instrumento. Declara cuál y por qué; el
benchmark **define la hipótesis nula** y cambiarlo cambia el resultado.

**Tests.** `arch.bootstrap.SPA` y `StepM` con bootstrap estacionario (Politis–White). Añade `arch` a
`requirements.txt` — **línea nueva, sin reordenar nada**, es fichero compartido.

**Salidas.**
- Las tres p del SPA: `consistent`, `lower`, `upper`. Las tres, no una. La distancia entre `lower`
  y `upper` es la información sobre cuántas candidatas malas están arrastrando el test.
- El conjunto StepM que sobrevive al FWER elegido, con el FWER escrito al lado.
- Cuántas entran y cuántas salen → al ledger.

## 3 · Los tres modos de fallo

1. **Retornos por fecha de cierre en vez de mark-to-market.** Una operación de tres semanas
   contabilizada entera el día que cierra rompe la dependencia serial que el bootstrap estacionario
   está justamente ahí para preservar. Usa la equity diaria, que es mark-to-market.
2. **El último período.** 🔬 SQX marca a mercado una posición abierta en la última vela mientras el
   beneficio neto sólo cuenta cerradas: medido en 172 de 962 variantes, hasta 332 $. `panel.py` ya
   descarta el último período por eso — haz lo mismo y dilo en el README.
3. **Una K que no es la K real.** Las K que entran al test no son todas las que se probaron: son las
   que sobrevivieron. El SPA corrige por las K que ve. **Lo que se probó de verdad lo sabe el
   ledger**, y es la razón de que el encargo 8 vaya primero.

## 4 · Verificación

```bash
python3 tools/depmap.py && python3 tools/checks.py    # 0 problems
```

1. **Control negativo:** K series de ruido sin edge → el StepM no debe nombrar a ninguna, salvo por
   el FWER declarado. Corre 20 semillas y enseña la tasa.
2. **Control positivo:** una serie con edge conocido metida entre ruido → tiene que salir nombrada.
3. **Contra el CSCV, sobre la misma población:** no tienen por qué coincidir, y si coinciden
   siempre, uno de los dos está mal cableado. Explica las discrepancias que encuentres.

## 5 · Cómo cierras

Página de manual (regla dura 8): `docs/manual/40-snooping.md`, en español, con salida real.

Devuelve: qué construiste · la salida de la §4 pegada · dónde lo dejaste cableado (o sin cablear, a
la espera del dueño) · qué descubriste, escrito en `knowhow/` en esta misma tarea.
