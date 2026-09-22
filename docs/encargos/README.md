# docs/encargos — un fichero por instancia de agente

Cada fichero de esta carpeta es **un encargo autocontenido**: lo que una sola instancia necesita
para hacer su parte, y nada más. Se despacha diciéndole al agente que lea **su** fichero, no el
plan entero.

El plan completo vive en `docs/AgentPDFs/plan-ejecucion-2026-09-21.md` y sigue siendo la referencia
de por qué existe cada tarea y cómo encajan. **Los encargos son la versión ejecutable de una parte
de él.** Donde discrepen, manda el plan — y se arregla el encargo.

## Los cuatro de esta tanda

| fichero | agente | posee | lote del plan |
|---|---|---|---|
| `1-sqx.md` | instalaciones SQX | los installs, `knowhow/` | S1, S9, S7, S6 |
| `2-portabilidad.md` | Python | `core/paths.py`, `core/worker.py`, `bin/`, `tools/`, `config/` | P1 |
| `3-pipeline.md` | Python | `pipeline/` *(nueva)* | P2 · W6 |
| `4-variantes.md` | Python | `sqx/variants/` *(nueva)*, `tests/` | P3 · W2 |

**Se lanzan los cuatro a la vez.** Las carpetas son disjuntas por diseño.

## Cómo se despacha

> Lee `docs/encargos/2-portabilidad.md` y ejecútalo entero. Es tu encargo completo: no necesitas
> leer el plan grande ni los otros encargos. Si algo te bloquea, párate y dímelo.

## Protocolo anticolisión

Tres ficheros son compartidos y los tocan varios agentes. Las reglas son las tres:

- **`docs/DEPENDENCIES.md` se regenera, nunca se fusiona.** Si hay conflicto, `python3
  tools/depmap.py` y se queda lo que salga.
- **`requirements.txt`: se añade línea, nunca se reordena.**
- **`core/` lo posee el agente 2 en esta tanda.** Si el 3 o el 4 necesitan un helper compartido, lo
  escriben dentro de su propia carpeta y lo anotan en su entrega. No tocan `core/`.

Árbol git compartido, porque las carpetas no se solapan. Si prefieres ramas separadas, una por
encargo y el merge al final.

## Qué devuelve cada agente

Todos cierran igual: **qué hizo · qué verificó, con la salida pegada · qué dejó sin hacer y por
qué · qué descubrió que merezca ir a `knowhow/`.**

## Idioma

Español, como el resto de `docs/` cuyo lector es el dueño. El código, los `README.md` de carpetas de
código y `knowhow/` siguen en inglés (`CLAUDE.md`).
