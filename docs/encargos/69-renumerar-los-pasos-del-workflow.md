# 69 · Renumerar los pasos del workflow (aplazado)

**Estado:** apuntado, sin empezar. Dueño, 2026-10-13: «A por ahora, apunta en un mini encargo para
hacer en el futuro». No se hace hasta que él lo pida.

**Tu oficio:** renombrado mecánico con comprobación (Sonnet, regla 17), tras una decisión del dueño.
**Tu encargo:** decidir con el dueño si los pasos del workflow se renumeran ahora que 22, 23, 24 y 25
no existen (borrados el 2026-10-11) y el MT5 sigue llamándose «paso 26»; si dice que sí, hacerlo de
una vez y sin dejar ningún número viejo.

## Lo medido el 2026-10-13

- «paso 26» / «step 26» / `paso-26` / `"26"`: 77 ficheros, 179 líneas.
- pasos 21 a 25: 82 ficheros, 166 líneas.
- 10 carpetas `paso-2*` en corridas ya guardadas de `AlgoData/autopilot/`.
- Además: umbrales (`ledger/thresholds.yaml`), raíles de los proyectos, `criteria.yaml`, los PDF del
  manual y `docs/AgentPDFs/WORKFLOW.md`.

## Por qué se aplazó

- «paso 22» ya nombra otra cosa en encargos, fichas e historial (el mapa condicional): reutilizar el
  número vuelve ambiguo todo documento viejo.
- Los números ya son nombres, no posiciones: 10.5, 11.5, 11.7, 16.5, 18.5 y 19.5.

## Preguntas que el dueño contesta antes de empezar

**Contestadas por el dueño (2026-10-14)** — lo que sigue manda sobre la lista de abajo:
- Sigue aplazado. Cuando se haga: N1 → **sólo el 26 pasa a ser 22**; N2 → **una nota**, sin renombrar carpetas; N3 → **los históricos no se tocan**.


| código | qué se decide | A | B |
|---|---|---|---|
| N1 | el alcance | sólo el 26 pasa a ser 22 | se renumera todo, medios pasos incluidos, del 1 al final |
| N2 | las corridas ya guardadas | se dejan con su número viejo y una nota | se renombran sus carpetas |
| N3 | los documentos históricos (encargos cerrados, bitácoras) | no se tocan | se reescriben |

## Hecho cuando

`grep` de los números viejos no devuelve nada fuera de lo que N2 y N3 dejen, `python3 tools/checks.py`
da 0 problemas, y una corrida entera del workflow (`bin/workflow-test.sh`) pasa sin errores.
