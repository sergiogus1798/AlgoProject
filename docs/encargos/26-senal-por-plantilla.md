# 26 · Desglose de la señal, agregado por plantilla — encargo autocontenido

**Tu oficio:** Python numérico + lectura de `sqx/templates/registry.py`. No toca SQX en vivo — lee
metrics y trade exports ya generados de proyectos que usan plantillas de la librería. Nace de la
comparación con BuildAlpha del 2026-09-27: BuildAlpha desglosa frecuencia de acierto/fallo por
señal dentro de una sola estrategia; el dueño pidió en su lugar la versión que aquí tiene sentido —
**agregada por plantilla**, no por estrategia suelta, porque lo que se quiere decidir es qué
plantillas de la librería merece la pena seguir explotando.

Lee `sqx/CLAUDE.md` · `studies/CLAUDE.md` · `studies/readings/structure/README.md` (el módulo más
cercano: qué bloque lleva el borde, por ablaciones) · `ui/README.md` §zona **Cobertura** /
**Plantillas** (`docs/AgentPDFs/catalogo-para-la-ui-2026-09-25.md` líneas 87-89) · `sqx/templates/registry.py`.

---

## 0 · Antes de programar nada: la ambigüedad a resolver con el dueño (regla 11 de `CLAUDE.md`)

"Desglose de la señal por plantilla" admite más de una lectura y hay que preguntar cuál antes de
tocar código:

1. **Frecuencia y win rate de la condición fija de la plantilla** (el bloque que `template-run`
   comprueba que todas las estrategias llevan) — cuántas veces dispara, qué win rate tiene esa
   señal en concreto, agregado sobre todas las estrategias construidas con esa plantilla, en todos
   los mercados donde se ha probado.
2. **Comparación entre plantillas**: de las plantillas en la librería, cuáles producen estrategias
   con mejor relación señal/ruido — un ranking, no sólo una ficha por plantilla.
3. **Ambas cosas**, con (1) como el dato por plantilla y (2) como la vista comparativa que lee (1)
   para varias plantillas a la vez.

La lectura (3) es la que más encaja con "por templates estaría bien" y con la zona **Cobertura** ya
descrita en el catálogo de la ventana, pero **pregúntalo explícitamente antes de fijar el alcance**
— no asumas.

## 1 · Dónde vive, y por qué no es obvio

Dos candidatos, y la elección también se pregunta:

- **`studies/readings/` junto a `structure/`** si la unidad de análisis sigue siendo una población
  de una plantilla en un mercado (como hoy vive `structure`, que ya usa `sqx/structural/` para las
  ablaciones) — y luego una capa aparte que reúne varias fichas para el ranking.
- **Un módulo nuevo bajo `sqx/`** si lo central es leer `registry.csv` a través de muchos proyectos
  y mercados a la vez, más parecido a un informe de cobertura que a una lectura de `readings/`.

Anota la decisión y por qué en el `README.md` que crees, para que no se tenga que redescubrir.

## 2 · Lo que hace falta para que la agregación tenga sentido

- **La plantilla debe ser identificable en cada estrategia.** `template-run` ya verifica que las
  estrategias construidas llevan de verdad el bloque fijo — reutiliza esa comprobación, no la
  repitas a mano.
- **Comparar entre plantillas exige mercados y ventanas comparables**, o la comparación mezcla el
  efecto de la plantilla con el efecto del mercado (`studies/CLAUDE.md` §«dos poblaciones
  estructuralmente distintas pueden compartir un databank: sepáralas antes de promediar» — el mismo
  riesgo, entre plantillas en vez de entre poblaciones).
- **Corrige por número de plantillas comparadas** si el resultado es un ranking — es la misma
  multiplicidad que ya vigila `engines/inference` en `gate` y `snoopingScreen`; una plantilla no
  "gana" el ranking sólo por haberse probado en más mercados.

## 3 · La decisión que debe salir

No una tabla de frecuencias por sí sola: el resultado que el dueño puede usar es una de estas dos
cosas (o ambas, si (3) de arriba es lo pedido) — **una plantilla concreta a retirar de la rotación
porque su señal no bate el ruido en ningún mercado probado**, o **una plantilla a priorizar en la
próxima ronda de generación** porque su señal se sostiene across markets. Con su coste al lado: en
cuántos mercados y estrategias se apoya la conclusión.

## 4 · Cómo cierras

Confirma el alcance (§0) y la ubicación (§1) con el dueño antes de escribir código. Después:
`python3 tools/depmap.py && python3 tools/checks.py` → 0 problemas · página de manual en español
con salida real · fila añadida a la tabla del README de la familia que corresponda · si el criterio
de "plantilla comparable" o el de corrección por multiplicidad revela algo no obvio, a `knowhow/`.
