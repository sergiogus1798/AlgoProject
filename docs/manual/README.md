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
| `02-filtros.md` | el barrido de filtros: cuánto mejora cada filtro candidato el resultado OOS y a costa de cuántas estrategias |
| `03-comparar-muestras.md` | la comprobación entre generaciones: si las conclusiones de una muestra se cumplen en otras |
| `04-decaimiento.md` | el decaimiento estrategia por estrategia: cuánto edge sobrevive fuera de muestra y si te la quedas |
| `05-retest-mercados.md` | el retest en mercados adicionales: si el sistema gana por acertar cuándo entra o por estar comprado |
| `06-mover-estrategias.md` | aplicar un veredicto dentro de SQX: mover a otra databank las estrategias descartadas |
| `07-montecarlo.md` | el Monte Carlo de robustez: de qué depende el resultado de una estrategia — del orden, de qué operaciones salieron, de la ejecución o del régimen |
| `08-spp.md` | el perfil Sys. Param Permutation a CSV: cuántas permutaciones sobreviven y cuánto se aleja tu estrategia de la permutación mediana |
| `09-diccionario-spp.md` | el inventario completo: cada campo que sale de una estrategia con SPP, con su nombre exacto y qué es. La página de consulta mientras escribes el análisis |
| `09-wfm.md` | la matriz Walk-Forward a CSV: cada celda, cada tramo con sus fechas y sus parámetros, el rendimiento dentro y fuera de muestra, y los trades repartidos por tramo |
| `10-github.md` | tener el proyecto subido a GitHub y poder clonarlo en otro ordenador: qué viaja en el repositorio, qué no, y qué hay que hacer en el clon |
| `_PLANTILLA.md` | **la plantilla obligatoria.** Se copia para documentar cada módulo nuevo |
| `PENDIENTE.md` | los comandos que aún no tienen página. Solo atraso heredado; no crece |
| `assets/` | las capturas. Salidas reales, nunca inventadas |
| `AlgoProject-Manual.pdf` | generado, no está en git. Se reconstruye en segundos |

## La regla

**Un comando nuevo sale con su página de manual en el mismo trabajo que lo crea.** Es la regla 9 del
`CLAUDE.md` y `tools/checks.py` la comprueba: si un script tiene un `__main__` y no aparece —ni por
su ruta ni por su comando `-m`— ni en una página del manual ni en `PENDIENTE.md`, la comprobación
falla.

El motivo es que un análisis que nadie sabe ejecutar no existe. La documentación escrita semanas
después la escribe alguien que ya olvidó qué confundía al principio, que es justo lo que hay que
explicar.

## Por qué markdown y no un PDF a mano

El PDF no se puede editar ni comparar entre versiones. El markdown sí: se ve qué cambió en cada
commit, se corrige una frase sin rehacer el documento, y el PDF se regenera con un comando. El
original es el `.md`; el PDF es un producto.

`tools/manual.py` usa Chrome en modo headless para imprimirlo, y la ruta del navegador vive en
`config/machine.yaml` como todo lo que depende de la máquina.
