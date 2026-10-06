# 43 · Criterios Pasa / Limbo / Falla de los pasos 10, 12, 14, 16 y 20 — encargo autocontenido

**Tu oficio:** jefe de un equipo de agentes. Estadística y diseño: **Opus** para ti, la síntesis y
el equipo rojo; **Sonnet** para lo mecánico (regla 17).
**Tu encargo:** que cada paso que juzga después del 8 tenga **una regla medida** en
`pipeline/autopilot/criteria.yaml` — o una razón escrita de por qué no corta —, **con lo que gana y
lo que cuesta en estrategias al lado**, calibrada sobre las poblaciones nuevas del encargo 42 y sus
nulos. Es el punto **1.6** del plan `docs/encargos/41-fases-0-y-1.md`: léelo (`sed -n 199,209p`),
hazlo entero y actualiza su fila.

Lee `CLAUDE.md` · `docs/AgentPDFs/WORKFLOW.md` (los pasos 9 a 20: qué segmento lee cada uno y qué
entrega al siguiente) · `pipeline/autopilot/README.md`, `criteria.yaml` (cabecera y pasos 10-16,
`:121-143`) y `facts.py` · el `README.md` y el `config.yaml` del estudio de cada paso
(`studies/transfer/crossmarket/`, `studies/transfer/crossTF/`, `studies/breakage/mcRetest/`,
`studies/breakage/spp/`) · `ledger/thresholds.yaml` · el dossier que entregue el encargo 42 · las
cabeceras de `knowhow/research/gate-t-scales.md` y `knowhow/research/post-selection-bias.md`.

---

## 0 · De dónde sale

- El dueño quiere criterios que descansen en estadística y que acepten que el mundo es imperfecto:
  donde los datos no fijan una cifra, se dice y se toma la prudente. **Pasa** = probado con los datos
  que hay · **Limbo** = no se pudo probar todavía, sigue marcado · **Falla** = casi seguro azar, o un
  riesgo que una cuenta de fondeo no aguanta. **Un hecho que falta es Limbo** (dueño, 2026-10-01): no
  lo cambies; lo que deba fallar lleva su regla explícita.
- **Lo que hay hoy** en `criteria.yaml`: el paso 10 tiene dos reglas, el 12 una y el 14 una
  (sólo mata), puestas por un Council el 2026-10-04 **sin datos**: son un punto de partida razonado,
  no una calibración. El 16 está en `rules: []` porque los dos hechos que necesitaría no se exponen.
  El 20 no tiene definición de «pasar» (decisión D3 del plan 41).
- Sustituye a `docs/AgentPDFs/prompt-criterios-otros-pasos-2026-10-02.md` (borrado; en git hasta
  `936e394`).

## 1 · De qué depende — no empieces sin esto

1. **El encargo 42 entregado**: las poblaciones sin seleccionar, sus gemelas aleatorias, los nulos y
   los criterios de los pasos 6-8 propuestos. Sin los muertos del paso anterior no se puede medir lo
   que una regla cuesta ni si discrimina.
2. **El carril** que el dueño eligió en la D1 del 42: estas poblaciones tienen que pasar por las
   tareas de SQX de los pasos 9, 11, 13 y 15, y eso también va por un solo comando (regla 19).
   **Todas las supervivientes del 16 en adelante pasan por 16.5-19 sin filtrar** (dueño).

## 2 · Método, por paso y en este orden

1. **Qué calcula el paso de verdad** (un agente por paso, sólo lectura, cada uno deja su informe en
   disco): fórmulas exactas de la tarea de SQX y del estudio de Python, sus nulos y cada clave de
   hecho que emite por estrategia. Verifica las fórmulas contra el código: la estadística central del
   paso 8 tenía un error de unidades que nadie había visto.
2. **Primero los hechos.** `python3 -m pipeline.autopilot.facts --project <P> --step <N>`: lo que
   falte se expone como columna numérica antes de calibrar. Para el 16: «solución en pico» y «media
   de la rejilla − 1 σ < 0».
3. **Lo que entra al paso:** lo que el anterior deja pasar con sus criterios **más una muestra sin
   seleccionar** de lo que falló. Largo y corto, genética y aleatoria, M30 y H1, los activos del 42.
4. **Un nulo sobre la misma estadística** que el paso calcula: misma contabilidad, mismo ajuste de
   deriva, mismo N efectivo. Compara cada población con su gemela aleatoria: un paso que «pasa»
   estrategias donde el anterior no encontró enriquecimiento está leyendo suerte.
5. **Cada regla candidata** con: qué deja, qué parte de lo bueno pierde, elevación, intervalo de
   confianza agrupado por estructura, tasa de falsos positivos en los nulos y **efecto en solitario**.
   Quita las que nunca disparan solas, salvo que sean redes de seguridad baratas. «Buena» se define
   con datos que la regla no lee; tasas, no recuentos.
6. **Cuánta evidencia nueva añade el paso.** Ninguna estrategia es significativa por sí sola tras la
   búsqueda: cada paso enriquece y la cadena prueba. Un paso que vuelve a leer `oos1` añade poco:
   dilo con su número, y di qué pasos son el mismo eje.
7. **El riesgo flotante** allí donde el paso lo ve (peor día, peor MAE, drawdown sobre neto anual,
   en R): las cuentas de fondeo se juzgan por el flotante.
8. **Los umbrales, a un sitio:** los de crossmarket, crossTF, mcRetest y WFC pasan del `config.yaml`
   de cada estudio a `ledger/thresholds.yaml` (filas al final de su sección, con `set_by` y
   `set_on`), leídos como `ledger:<clave>`.
9. **Equipo rojo** con contexto limpio (CONFIRMADO / FALSO / EXAGERADO / SIN APOYO por afirmación) y
   validación por el camino real (`facts.per_strategy` → `criteria.resolved` → `criteria.outcomes`):
   el embudo del 8 al 20, por población y agrupado.
10. **Lo que se midió a posteriori se prueba dentro de SQX** con un A/B (misma caja, un brazo por
    ajuste): un filtro dentro de una tarea cambia lo que la tarea produce.

Trampas ya pagadas: como mucho 8-12 procesos de Python y 25 GB libres (64 lecturas por estrategia en
paralelo mataron la sesión y el custodio); nunca `pkill -f`; el mono con `--seed`, o su p no se
repite; ficheros grandes a `AlgoData`, no a `/tmp`; un umbral elegido tras leer un segmento lo gasta:
di qué segmento usó cada paso y congela las cifras antes del siguiente build.

## 3 · Lo que entregas

- Las reglas de 10, 12, 14 y 16 en `criteria.yaml`, **propuesta de un agente** hasta la firma; las
  del Council se confirman, se corrigen o se quitan, cada una con su dato.
- Un dossier en castellano en `docs/AgentPDFs/` con su PDF: una tabla por paso (regla · gana ·
  cuesta · falsos positivos · segmento que gastó) y el embudo entero.
- Fichas de `knowhow/` por cada hecho no obvio, el capítulo del manual de lo que cambie, y la fila
  1.6 del plan 41 al día.

## Decisiones del dueño — pregúntalas (regla 11)

- **D1 · El paso 16 (SPP):** hoy es «un mapa, no un filtro». ¿Corta, o `criteria.yaml` dice por
  escrito que no corta? Llévale lo que costaría y lo que ganaría.
- **D2 · Qué es pasar el paso 20** (la D3 del plan 41): con las lecturas posibles escritas.
- **D3 · El paso 14, ¿sólo mata?** El Council lo dejó así: sobrevivir no es evidencia. ¿Lo mantiene
  si los datos dicen que además discrimina?
- **D4 · El paso 12 nunca falla** (por debajo de la línea es Limbo). ¿Sigue así?
- **D5 · Adoptar cada criterio** y apagar `dev.on`: suyo. Tráele la decisión con su coste y para.

## Lo que no tocas

- El master. **`oos2`**, reservado. El riesgo por operación y las sesiones.
- Los criterios de los pasos 6 y 8: son del encargo 42. Si un hallazgo los contradice, se anota.
- La campaña (`pipeline/campaign/`): la lleva otra sesión.

## Verificación

- `python3 -m pipeline.autopilot.facts --project <P> --step <N>` para 10, 12, 14 y 16: todos los
  hechos de las reglas existen.
- `grep -n 'rules: \[\]' pipeline/autopilot/criteria.yaml`: cada resultado lleva su razón al lado.
- El embudo por el camino real y el informe del equipo rojo, pegados.
- `python3 tools/depmap.py && python3 tools/checks.py`.

## Cómo cierras

Qué hiciste · qué verificaste, con la salida pegada · qué dejaste sin hacer y por qué · qué
descubriste para `knowhow/` · los ficheros cambiados y, como última línea, **¿Quieres hacer el
commit?**
