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
| `1_sqx/export/export_trades.py` | exporta todos los trades de un databank y las barras sobre las que operaron | alta — es la entrada de todo el análisis de estrategia individual |
| `core/assets.py` | muestra los costes y overrides configurados para un símbolo. Es obligatorio correrlo antes de tocar cualquier proyecto o plantilla | alta — ya es una regla dura del proyecto y no está explicada en ningún sitio para un humano |
| `1_sqx/inspect/project_health.py` | dice qué está roto en cada proyecto de una instalación | alta |
| `1_sqx/inspect/dump_project.py` | convierte un `project.cfx` en un mapa legible de sus tareas | media |
| `1_sqx/inspect/template_check.py` | comprueba si las estrategias que construyó un proyecto usan de verdad los bloques de su plantilla | media |
| `1_sqx/inspect/instruments.py` | lista los costes de trading configurados por instrumento | media |
| `1_sqx/export/archive_logs.py` | copia los logs de SQX antes de que SQX los borre | baja |
| `1_sqx/inspect/index_sqx.py` | indexa todos los `.sqx` de la máquina por el hash de su XML interno | baja |
| `1_sqx/inspect/keep_tasks.py` | genera una variante de un `project.cfx` conservando solo ciertas tareas | baja |
| `1_sqx/repair/graft_tasks.py` | repara un `project.cfx` al que le faltan archivos de tarea | baja — es peligroso y necesita SQX cerrado, así que su página tiene que ser especialmente clara |

## Orden sugerido

Primero `core/assets.py` y `export_trades.py`: uno es una regla dura que nadie ha explicado nunca en
castellano, y el otro es el que alimenta la fase 3. Después el grupo de `inspect/`, que se puede
documentar en una sola página común porque todos son de solo lectura y se usan igual.

`graft_tasks.py` el último y con cuidado: es el único que modifica archivos de SQX.
