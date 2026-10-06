# 45 · Módulo de fondeo: cuánto riesgo admite una cartera dentro de los límites — encargo autocontenido

> **Listo para planificar.** Lo estadístico está definido (dueño, 2026-10-06); **cinco decisiones
> de encaje son suyas y van antes de escribir código** (sección «Decisiones del dueño»). La
> primera entrega de este encargo es el inventario y esas cinco preguntas con una recomendación.

**Tu oficio:** estadístico de riesgo de cuentas de fondeo. Diseño y estadística: **Opus**; lo
mecánico, **Sonnet** (regla 17).

**Tu encargo:** un módulo que, para una **cartera** de estrategias que ya pasaron la puerta y el
WFM, y para una cuenta de fondeo concreta, devuelva **el riesgo máximo por operación (el tamaño
de 1R, en % de la cuenta) que cabe dentro del límite diario y del límite total**, y con él un
veredicto — viable, dudosa, inviable — con el rendimiento anual a ese riesgo anotado al lado.
La puerta (paso 8) responde «¿hay ventaja real y estable?»; este módulo, «¿cómo la opero dentro
de los límites?». Lo que el dueño hace con la respuesta: fijar el riesgo por operación de la
cartera en esa cuenta, o descartar la combinación cartera × plan.

**Lee, en este orden:** `CLAUDE.md` · `CODESTYLE.md` · `portfolio/CLAUDE.md` · `OPEN.md` #85 (lo
abierto del fondeo) · `portfolio/funded/sim/README.md`, `rules/README.md` y `decide/README.md`
(lo que ya existe) · `portfolio/funded/catalog/README.md` (de dónde salen los límites de cada
firma y plan) · `docs/AgentPDFs/criterios-paso-08-R9-propuesta-2026-10-06.md` (`:65-142`: de ahí
sale el diseño) · `docs/AgentPDFs/puerta-is-oos-paso-08-especificacion-2026-10-06.md`, su
sección de R6 y la de lo que se deja al fondeo · `docs/encargos/44-puerta-is-oos-paso-8.md`
parte L (qué deja guardado la cadena, y cuándo).

## Estado — lo actualiza cada sesión

| parte | qué | estado |
|---|---|---|
| 1 | inventario de lo que ya existe y las cinco decisiones del dueño | pendiente |
| 2 | la cola del peor día (`q_día`) | pendiente |
| 3 | el drawdown esperado de la cartera (`DD_95`) | pendiente |
| 4 | el riesgo máximo y el veredicto | pendiente |
| 5 | la prueba del retraso con el feed de la firma | pendiente |
| 6 | la vista en la ventana y el capítulo del manual | pendiente |

**Bitácora:**

- 2026-10-06 · redactado; nada ejecutado.

---

## 0 · De dónde sale

- Dueño, 2026-10-06: R9a (peor día) y R9c (drawdown sobre neto anual) no dicen si hay ventaja,
  sino cuánto riesgo se le puede poner: es dimensionado, no validación. Salieron del paso 8.
  **Desde que el encargo 44 se ejecute y hasta que este módulo exista, nada en la cadena juzga
  el peor día ni el drawdown** — el dueño aceptó ese hueco, y es la razón de no dejar esto dormir.
- En fondeo manda el **flotante** (MAE, MFE), no las operaciones cerradas (dueño).
- Fondeo va antes que la cuenta real en Darwinex (dueño): este módulo es parte del camino crítico.

## 1 · Inventario y decisiones — la primera entrega

`portfolio/funded/` ya tiene un simulador de cuentas (`sim/`: `account.py`, `kernel.py`,
`bank.py`, `plans.py`, `haircut.py`, `monkey.py`…), una máquina de reglas (`rules/`: `machine.py`,
`floors.py`) y una decisión por plan (`decide/`), y `portfolio/` tiene el Monte Carlo a nivel de
operación. **Puede que parte de este encargo ya esté hecho, con otro nombre.** Antes de proponer
nada:

1. Una tabla: por cada pieza de las partes 2 a 5, qué existe (`fichero:línea`), qué responde hoy
   y la distancia a lo que se pide aquí. Usa `graphify explain` antes de abrir ficheros.
2. Las cinco decisiones de la sección «Decisiones del dueño», cada una con tu recomendación y
   lo que cuesta, en una sola pregunta.

No se escribe código hasta que conteste.

## 2 · El peor día que llegará, no el que se vio — `q_día`

El peor día observado en oos1 es una sola observación del extremo, y el siguiente será peor.

- **Dato:** la curva diaria de **flotante** de la cartera en oos1, en R: la suma, día a día, de
  las curvas de sus estrategias (el límite diario se juega con varias abiertas a la vez; sumar
  los peores días de cada una por separado no vale, ni por exceso ni por defecto).
- **Método:** *peaks over threshold*. Se toman las pérdidas diarias que superan un umbral alto
  y se les ajusta una Pareto generalizada; de ella se lee `q_día`, la pérdida diaria con
  probabilidad ≈ 0,05 / 252 — un 5 % de tener un día así en un año de operativa.
- **Conservador por construcción:** con unas 100 excedencias el ajuste es ruidoso. Se usa **el
  extremo conservador del intervalo de confianza** de `q_día`, no su estimación central, y el
  intervalo se saca por bootstrap con al menos 5.000 repeticiones.
- **A mirar al implementarlo:** cómo se elige el umbral (gráfico de vida media residual o un
  percentil fijo, configurable) y que el resultado no baile con él; qué se hace cuando hay
  menos excedencias de las que el ajuste aguanta (entonces no hay `q_día`: el veredicto es
  «sin dato», nunca un número inventado); y la dependencia entre días malos seguidos
  (*declustering*).

## 3 · El drawdown esperado de la cartera — `DD_95`

El paso 8 deja por estrategia `gate.scorecard.dd_esperado_p95_r`: el percentil 95 del drawdown
en el bootstrap por bloques de R6. **El de la cartera no es la suma** de los de sus estrategias:
se recalcula sobre la curva de la cartera con el mismo método (bloques, 5.000 secuencias),
conservando la simultaneidad — los bloques se cortan por fecha, los mismos para todas las
estrategias. Reutiliza el bootstrap de R6 del encargo 44 y el Monte Carlo de `portfolio/`; no
se escribe un tercero.

## 4 · El riesgo máximo y el veredicto

$$\text{riesgo}_{\max} = \min\!\left(\frac{L_d}{q_{\text{día}}},\ \frac{L_{\text{tot}}}{\text{DD}_{95}}\right)$$

con `L_d` y `L_tot` los límites diario y total del plan, **leídos del catálogo de fondeo**
(`python3 -m portfolio.funded.catalog.show <firma o plan>`), nunca escritos aquí. Hay que
respetar cómo mide cada firma su límite — sobre balance o sobre equity, estático o *trailing*,
a qué hora corta el día —: eso ya lo modela `portfolio/funded/rules/`; úsalo.

- **Veredicto de partida** (orientativo, configurable): viable con `riesgo_max` ≥ 0,75 %,
  dudosa entre 0,4 % y 0,75 %, inviable por debajo.
- **Anotado, nunca regla:** el rendimiento anual a ese riesgo (`riesgo_max` × neto anual en R)
  — lleva dentro la media de oos1, que ya juzgó R3 — y el tiempo de recuperación
  (`DD_95` / neto anual). Y cuál de los dos límites manda.
- **Referencia para comprobar el orden de magnitud** (propuesta, `:119-135`; con aproximaciones
  optimistas y por estrategia suelta): con 5 % diario y 10 % total, A ≈ 0,74 % y ≈ 7 % anual;
  C ≈ 0,99 % y ≈ 1,2 % anual. En las dos manda el límite total.

## 5 · La prueba del retraso con el feed de la firma

La puerta mide si la ventaja sobrevive a entrar una barra tarde, sobre el histórico propio. La
versión real (`docs/AgentPDFs/criterios-paso-08-estudios-4.2-4.3-4.4-propuesta-2026-10-06.md:141`):
con las barras de la propia firma, ¿la estrategia se dispara en los mismos momentos? El paso 26
(`mt5/verify/README.md`) ya corre cada estrategia en MT5 con la cuenta de cada firma: mira qué
de esto da ya antes de construir nada, y propón al dueño si es parte de este módulo o una
lectura más del paso 26.

## 6 · Dónde se ve

Lo que tenga interfaz es una vista dentro de `ui/` (estilo terminal, `theme.T`), con todos sus
parámetros editables desde la ventana y su frase de ayuda. La zona de cartera sigue la estructura
de Quant Analyzer con los colores de la ventana: **se enseña la propuesta al dueño antes de
construirla**. Un comando nuevo lleva su capítulo del manual en la misma tarea (regla 8).

## Todo es un parámetro, y en la ventana

La probabilidad del día extremo (0,05 / 252), el umbral de la cola, el nivel del intervalo de
confianza, el percentil del drawdown (95), la longitud de bloque, las repeticiones (por defecto
**al menos 5.000**), la semilla y los niveles del veredicto (0,75 % / 0,4 %). Los límites, del
catálogo.

## Decisiones del dueño — pregúntalas (regla 11)

Ya decidido: R9a y R9c viven aquí; todo por cartera; el rendimiento anual sólo se anota; los
datos se guardan cuando la estrategia pasa el WFM (paso 19).

Antes de escribir código:

1. **Dónde vive y en qué paso se lee:** dentro de `portfolio/funded/` junto al simulador (que es
   lo que se recomienda mirar primero), o como estudio de `studies/`; y si es un paso numerado
   del WORKFLOW o una lectura de la zona de cartera.
2. **Corta o anota:** ¿una cartera inviable sale, o sólo queda marcada?
3. **Qué cartera:** la que el dueño arme a mano, la que salga del buscador de carteras, o todas
   las combinaciones de las supervivientes. Y si además se da el número por estrategia suelta.
4. **Contra qué cuentas:** todos los planes del catálogo, sólo los de las firmas activas, o los
   que él elija en la ventana.
5. **Qué hace con el simulador que ya existe** (`portfolio/funded/sim/`): ¿este número es una
   entrada suya, una comprobación al lado, o lo sustituye en parte? Depende del inventario.

Y con números, cuando existan: la probabilidad del día extremo y los niveles 0,75 % / 0,4 %.

## Lo que no tocas

El maestro. `oos2` sin autorización. `pipeline/autopilot/criteria.yaml` del paso 8 y
`studies/screening/gate/` (son del encargo 44; de ahí sólo se lee). El catálogo y las ofertas
(`portfolio/funded/catalog/`, `deals/`) sólo se leen. Ninguna orden a MT5: el terminal sólo se
consulta.

## Verificación

- Respuesta conocida: sobre pérdidas diarias simuladas de una Pareto generalizada con
  parámetros dados, `q_día` cae dentro de su intervalo en la proporción que dice el nivel.
- Una cartera de una sola estrategia da el mismo `DD_95` que `dd_esperado_p95_r` de la puerta.
- Dos estrategias idénticas en cartera doblan `q_día` y `DD_95`; dos que nunca coinciden, no.
- Con los límites de un plan real del catálogo, `riesgo_max` sale a mano igual que en el módulo.
- `python3 -m pytest -q tests/<fichero>` de cada test nuevo.
- `python3 tools/depmap.py && python3 tools/checks.py`

## Cómo cierras

La tabla de estado y la bitácora actualizadas · qué hizo · qué verificó, con la salida pegada ·
qué dejó sin hacer y por qué · qué descubrió para `knowhow/` — la lista de ficheros cambiados y
**¿Quieres hacer el commit?**
