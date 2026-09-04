# docs/manual — el manual de uso

Está escrito **en castellano** y para un humano, no para una sesión futura. Es la única excepción a
la regla "Files in English" del `CLAUDE.md`, y es deliberada: su lector es el dueño del proyecto.

## Leerlo

```bash
python3 tools/manual.py
xdg-open docs/manual/AlgoProject-Manual.pdf
```

Un solo PDF con todos los capítulos, portada e índice. También puedes leer los `.md` sueltos en
GitHub o en el editor: son el original, el PDF es solo el resultado.

## Qué hay aquí

| archivo | qué es |
|---|---|
| `00-empezar.md` | instalación, cómo se ejecuta cualquier cosa, dónde acaban los datos, las reglas de SQX que no se rompen |
| `01-analisis-is-oos.md` | el análisis IS/OOS: qué responde, cómo se corre, cómo se lee el panel |
| `_PLANTILLA.md` | **la plantilla obligatoria.** Se copia para documentar cada módulo nuevo |
| `PENDIENTE.md` | los comandos que aún no tienen página. Solo atraso heredado; no crece |
| `assets/` | las capturas. Salidas reales, nunca inventadas |
| `AlgoProject-Manual.pdf` | generado, no está en git. Se reconstruye en segundos |

## La regla

**Un comando nuevo sale con su página de manual en el mismo trabajo que lo crea.** Es la regla 9 del
`CLAUDE.md` y `tools/checks.py` la comprueba: si un script tiene un `__main__` y no aparece ni en una
página del manual ni en `PENDIENTE.md`, la comprobación falla.

El motivo es que un análisis que nadie sabe ejecutar no existe. La documentación escrita semanas
después la escribe alguien que ya olvidó qué confundía al principio, que es justo lo que hay que
explicar.

## Por qué markdown y no un PDF a mano

El PDF no se puede editar ni comparar entre versiones. El markdown sí: se ve qué cambió en cada
commit, se corrige una frase sin rehacer el documento, y el PDF se regenera con un comando. El
original es el `.md`; el PDF es un producto.

`tools/manual.py` usa Chrome en modo headless para imprimirlo, y la ruta del navegador vive en
`config/machine.yaml` como todo lo que depende de la máquina.
