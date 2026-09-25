# Comandos todavía sin página de manual

Esta lista es **solo el atraso heredado**: comandos que ya existían el 2026-09-04, cuando se
estableció la regla de que toda funcionalidad se documenta a la vez que se programa.

**Nada nuevo entra aquí.** Un comando que se programe a partir de ahora sale con su página o no
sale. Esta lista solo puede encoger.

`tools/checks.py` la lee: un comando que no esté documentado y tampoco aparezca aquí hace fallar la
comprobación.

## Pendientes

| comando | qué hace | prioridad |
|---|---|---|
| `python3 -m sqx.inspect.project_health` | dice qué está roto en cada proyecto de una instalación | alta |
| `python3 -m sqx.inspect.dump_project` | convierte un `project.cfx` en un mapa legible de sus tareas | media |
| `python3 -m sqx.export.archive_logs` | copia los logs de SQX antes de que SQX los borre | baja |
| `python3 -m sqx.inspect.index_sqx` | indexa todos los `.sqx` de la máquina por el hash de su XML interno | baja |
| `python3 -m sqx.inspect.keep_tasks` | genera una variante de un `project.cfx` conservando solo ciertas tareas | baja |
| `python3 -m sqx.repair.graft_tasks` | repara un `project.cfx` al que le faltan archivos de tarea | baja — es peligroso y necesita SQX cerrado, así que su página tiene que ser especialmente clara |

## Orden sugerido

Primero el grupo de `inspect/`, que se puede documentar en una sola página común porque todos son de
solo lectura y se usan igual.

`graft_tasks.py` el último y con cuidado: es el único que modifica archivos de SQX.
