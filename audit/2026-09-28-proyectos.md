# Limpieza semanal de proyectos SQX — 2026-09-28

Pase desatendido (`bin/weekly-project-cleanup.sh`, cron), sin nadie delante. Regla aplicada tal
cual la escribe `sqx/projects/sweep.py`: `python3 -m sqx.projects.retire --sweep`.

## Dry run (paso 1)

```
retire? master    TestXAUUSD2                          3 tareas      0 MB  en la cola que nombró el dueño
retire? master    XAU_crossmarket_demo                 3 tareas      0 MB  en la cola que nombró el dueño
keep    custodian Test_USDJPY_donchianUpperCrossUp_M30  18 tareas      0 MB  tocado hace 17 h
```

Ningún install (máster, conductor, custodio) estaba encendido en el momento del barrido; el propio
sweep lo comprueba leyendo puerto y procesos, no se envió ningún comando a ninguna instalación.

## Comprobación de señales de vida (paso 2)

Para los dos candidatos del máster:

- `TestXAUUSD2`: sin mención en `docs/encargos/*.md`, sin línea en `OPEN.md`, sin
  `AlgoData/ledger/*.jsonl` ni `AlgoData/pipeline/TestXAUUSD2/`. Las dos citas que aparecen en
  `knowhow/` (`eng/no-slicing-xml-yaml-by-index.md`, `sqx-drive/only-flag-wrong-databank.md`) son
  evidencia de un hallazgo ya cerrado, no trabajo pendiente sobre el proyecto.
- `XAU_crossmarket_demo`: mismas comprobaciones, mismo resultado — nada vivo.

Sin señales de vida en ninguno de los dos: no hubo que retener nada.

## Retirados (paso 3)

Instalación **máster** (`~/Desktop/SQX`), vía cola del dueño
(`AlgoData/projects/retire-queue.txt`, líneas "2026-09-26: los dos del máster"):

| proyecto | tareas | MB | por qué | archivo |
|---|---|---|---|---|
| `TestXAUUSD2` | 3 | 0 | en la cola que nombró el dueño | `AlgoData/projects/retired/SQX/TestXAUUSD2-2026-09-28.tar.gz` |
| `XAU_crossmarket_demo` | 3 | 0 | en la cola que nombró el dueño | `AlgoData/projects/retired/SQX/XAU_crossmarket_demo-2026-09-28.tar.gz` |

(El tamaño en disco de `project.cfx` es pequeño — 0 MB redondeado por el barrido — pero las
carpetas ocupaban 124 KB y 116 KB respectivamente; ya archivadas y borradas.)

Se usó `python3 -m sqx.projects.retire --sweep --yes` (no había nada que retener aparte de lo ya
descartado por la propia regla, así que el paso 3 y el desencolado se hicieron juntos). Sus dos
líneas ya no están en `retire-queue.txt`; el resto de la cola (entradas de `conductor` y
`custodian` de una limpieza previa) sigue ahí sin tocar porque hoy no corresponden a ninguna
carpeta viva en esos installs — no eran candidatos de este pase.

Sin ninguna línea `FAILED`.

## Retenidos (paso 2/3)

- `Test_USDJPY_donchianUpperCrossUp_M30` (custodio, 18 tareas): tocado hace 17 h — dentro de las
  24 h de cuarentena de la propia regla. Se deja para el próximo pase; si sigue quieto una semana
  más, cae.

No hubo ningún otro candidato: el conductor y el custodio no tenían, aparte de éste, ningún
`Test_` ni ningún proyecto heredado con menos de 10 tareas en disco hoy.

## Disco liberado

124 KB + 116 KB = **240 KB** en el máster (`project.cfx` de ambos proyectos), archivados como
`.tar.gz` en `AlgoData/projects/retired/SQX/`. Nada de esto tenía databank que archivar (`--keep`
vacío): lo que dejó cada run ya está en parquet bajo `raw/`, `harvest/` y `reports/`.

## Resumen

2 proyectos retirados (máster), 1 retenido por antigüedad menor a 24 h (custodio), 0 fallos.
