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
| `python3 -m sqx.export.export_trades` | exporta todos los trades de un databank y las barras sobre las que operaron | alta — es la entrada de todo el análisis de estrategia individual |
| `python3 -m core.assets` | muestra los costes y overrides configurados para un símbolo. Es obligatorio correrlo antes de tocar cualquier proyecto o plantilla | alta — ya es una regla dura del proyecto y no está explicada en ningún sitio para un humano |
| `python3 -m sqx.inspect.project_health` | dice qué está roto en cada proyecto de una instalación | alta |
| `python3 -m sqx.inspect.dump_project` | convierte un `project.cfx` en un mapa legible de sus tareas | media |
| `python3 -m sqx.inspect.template_check` | comprueba si las estrategias que construyó un proyecto usan de verdad los bloques de su plantilla | media |
| `python3 -m sqx.inspect.instruments` | lista los costes de trading configurados por instrumento | media |
| `python3 -m sqx.export.archive_logs` | copia los logs de SQX antes de que SQX los borre | baja |
| `python3 -m sqx.inspect.index_sqx` | indexa todos los `.sqx` de la máquina por el hash de su XML interno | baja |
| `python3 -m sqx.inspect.keep_tasks` | genera una variante de un `project.cfx` conservando solo ciertas tareas | baja |
| `python3 -m sqx.repair.graft_tasks` | repara un `project.cfx` al que le faltan archivos de tarea | baja — es peligroso y necesita SQX cerrado, así que su página tiene que ser especialmente clara |

## Orden sugerido

Primero `core/assets.py` y `export_trades.py`: uno es una regla dura que nadie ha explicado nunca en
castellano, y el otro es el que alimenta la fase 3. Después el grupo de `inspect/`, que se puede
documentar en una sola página común porque todos son de solo lectura y se usan igual.

`graft_tasks.py` el último y con cuidado: es el único que modifica archivos de SQX.
