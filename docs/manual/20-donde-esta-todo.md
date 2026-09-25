# 20. Dónde está todo — el mapa de los datos

### Qué pregunta responde

**¿Dónde ha quedado esto que acabo de generar?** Y la de al lado, que es la que de verdad hace
perder tiempo: *¿esto ya existe, o lo vuelvo a exportar?*

Hay **dos sitios**, y la frontera entre ellos es la regla dura 7 del proyecto:

| dónde | qué vive ahí | cuánto pesa |
|---|---|---|
| `~/Desktop/SQX*/user/projects/` | **las estrategias vivas**, dentro de SQX. Las que ves en la GUI | 4,2 GB en el maestro |
| `~/Desktop/AlgoData/` | **todo lo que este proyecto produce**: exports, backtests, métricas, informes | 7,3 GB |
| `~/Desktop/AlgoProject/` | **solo código y texto**. Nunca datos | 30 MB |

⚠️ **En el repositorio no entra ni un dato.** `.gitignore` bloquea `*.csv`, `*.parquet` y `*.sqx`,
y `checks.py` falla si algún módulo escribe fuera de `core/paths.py`. Si buscas un número, no está
en el repo: está en `AlgoData`.

### Cuándo lo usas, y cuándo no

**Lo usas** cuando no encuentras algo, cuando vas a exportar y quieres comprobar si ya está, o
cuando te preguntas qué se puede borrar. **No lo usas** para saber qué contiene cada fichero: eso lo
dice `~/Desktop/AlgoData/INDEX.md`, que lleva una línea por export con sus filas y sus columnas.

### Antes de empezar

Nada. Es lectura.

### Cómo se ejecuta

```bash
cat ~/Desktop/AlgoData/INDEX.md          # qué hay, export por export
python3 -m perf.disk.report --quick      # qué pesa cada rama y contra qué presupuesto
```

### Qué produce

Nada. Este capítulo describe lo que producen los demás.

---

## Las estrategias — hay cuatro sitios y conviene no confundirlos

| qué | dónde | quién lo escribe |
|---|---|---|
| **Las vivas, las del maestro** | `~/Desktop/SQX/user/projects/<proyecto>/databanks/<databank>/*.sqx` | SQX. 7.546 hoy |
| **Las fabricadas** (las 5.000 permutaciones) | `AlgoData/pipeline/<proyecto>/<estrategia>/sqx/P*.sqx` | `sqx.variants.make` |
| **Las copiadas a un export** | `AlgoData/raw/<proyecto>/<databank>/<fecha>/strategies/*.sqx` | `sqx.export.*`, al exportar trades |
| **El snapshot de seguridad** | `AlgoData/snapshots/<fecha>/master/projects/` | copia manual antes de algo destructivo |

⚠️ **Las del maestro son volátiles y las demás no.** Cada sync de SQX borra del disco los `.sqx`
que no tiene en memoria, y hay auto-sync horario: por eso existe la rama `snapshots/`, y por eso el
donante congelado vive en `AlgoData/projectsBackup/`, no en el install. Regla dura 1.

⚠️ **Las fabricadas se borran a propósito.** Son 14 KB cada una y 5.000 por estrategia madre; el
paso de limpieza las tira cuando ya se midieron. **Lo que sobrevive es el registro**, que pesa
kilobytes y dice qué había. Eso es lo que hace que el borrado sea auditable en vez de una pérdida.

## Los backtests y las métricas

| qué | dónde | vida |
|---|---|---|
| **Las métricas de un databank** (una fila por estrategia, IS y OOS emparejados) | `AlgoData/metrics/<proyecto>/<databank>/metrics.csv` | **una sola copia**, se reemplaza al refrescar |
| **Las operaciones, todas** (12 columnas tipadas) | `AlgoData/raw/<proyecto>/<databank>/<fecha>/trades.parquet` | fechada, inmutable |
| **El perfil SPP** (la tabla de permutaciones) | `AlgoData/raw/<proyecto>/<databank>/<fecha>/spp/` | fechada, inmutable |
| **El panel de un lote de variantes** | `AlgoData/pipeline/<proyecto>/<estrategia>/retest.csv` | se rehace al reejecutar |
| **Ese panel unido al diseño** (contrato C3) | `AlgoData/pipeline/<proyecto>/<estrategia>/metrics.parquet` | **esta es la tabla del estudio** |
| **Las barras** | `AlgoData/bars/<feed>/M1.parquet` | la única copia. M30/H1/H4/D1 se resamplean |
| **Las barras resampleadas** (caché) | `AlgoData/barsDerived/<feed>/<TF>-<huella>.parquet` | se puede borrar, se regenera |

**`metrics/` guarda una sola copia a propósito**, para que "cuál es el CSV bueno" no pueda ser una
pregunta. `raw/` va fechado porque un export de hoy y uno de hace un mes son datos distintos, no
versiones del mismo.

## Los informes y los veredictos

| qué | dónde |
|---|---|
| Informes de un databank (`explorer.html`, `summary.md`) | `AlgoData/reports/<proyecto>/<databank>/<fecha>/` |
| El brief de diseño de una madre (contrato C1) | `AlgoData/reports/<proyecto>/<databank>/<fecha>/design_brief_<estrategia>.json` |
| **El gráfico del walk forward correlation** | `AlgoData/pipeline/<proyecto>/<estrategia>/wfc.html` |
| Su veredicto en números | `AlgoData/pipeline/<proyecto>/<estrategia>/wfc.json` |
| **El libro mayor de una madre** | `AlgoData/pipeline/<proyecto>/<estrategia>/state.json` |

`reports/` **no se borra nunca**. El CSV se puede regenerar desde SQX; el razonamiento no.

## Una carpeta de pipeline por dentro

Es donde vive un estudio completo de una estrategia madre:

```
AlgoData/pipeline/XAUUSD/Strategy_17-9-39/
├── plan.csv            el diseño entero: qué combinaciones y de qué estrato
├── design.json         el resumen del diseño: presupuesto por estrato y faltante
├── sqx/P*.sqx          las 5.000 fabricadas.  ← LO ÚNICO PESADO. Se borra
├── manifest.parquet    contrato C2: qué es cada fichero, leído DEL DISCO
├── build.json          cuántos ficheros y cuántos bytes se escribieron
├── retest.csv          el panel tal y como lo escupe SQX
├── ran.json            cuántas se cargaron y cuántas volvieron
├── metrics.parquet     contrato C3: el panel unido al diseño.  ← LA TABLA
├── collected.json      los controles, y si alguno no volvió
├── wfc.html            EL GRÁFICO
├── wfc.json            rho, su intervalo, el veredicto
└── state.json          el libro mayor. Sobrevive al borrado de sqx/
```

**Todo menos `sqx/` pesa unos 500 KB.** `sqx/` pesa 70 MB con 5.000 variantes. Por eso el borrado
solo toca esa carpeta, y solo después de que `metrics.parquet` esté escrito y verificado.

## El resto de ramas

| rama | qué es | ¿se puede borrar? |
|---|---|---|
| `projectsBackup/` | copias congeladas: `project.cfx` donantes, las madres, y las configs de los installs. El punto fijo del que salen los proyectos nuevos | **no** |
| `snapshots/` | `user/projects` copiado antes de algo destructivo, **sin las carpetas `log/` de los proyectos** (`rsync -a --exclude='log/'`). Vive hasta que se comprueba que el reinicio no perdió nada, y entonces **se borra** (dueño, 23-09-2026): el del 21-09 eran 3,5 GB sin un solo fichero que el maestro vivo no tuviera | sí, en cuanto se verifica |
| `logs/` | los logs de SQX comprimidos, de los tres installs. Un log gigante se guarda *condensado* (`*.condensed.log.gz`): sin trazas Java ni las líneas por estrategia del EdgeDecay, que eran el 97 % | **no** — es lo que hace seguro podar los vivos |
| `cache/` | cachés de los paneles (Monte Carlo, cross-market) | sí, se regeneran |
| `profiling/` | el catálogo de lo que cuesta cada cosa y cuánto ocupa el disco | **no** |
| `strategyPermutations/` | las variantes fabricadas a mano de una estrategia (fuera del pipeline) | cuando el pipeline las haya cubierto |

## Cómo se sabe qué produjo un fichero

**Cada directorio lleva un `manifest.json`** con el comando que lo escribió, cuándo y con qué
entradas. Uno sin manifiesto no es reproducible, y el auditor lo marca como hallazgo.

```bash
cat ~/Desktop/AlgoData/raw/XAUUSD/SPP_IS/2026-09-10/manifest.json
```

## Presupuestos — qué pasa cuando una rama crece

`perf/config.yaml` le pone techo a cada rama, y el pipeline **se niega a empezar otra madre** si el
total o alguna rama está por encima. No es un aviso: para la corrida.

```
AlgoData: 7.27 GB de 90 GB (8%) en 70 ramas
           ok      4.78 GB /   20 GB     24%  snapshots
           ok      1.96 GB /   40 GB      5%  raw
           ok      0.00 GB /   15 GB      0%  variants
```

Una rama nueva sin presupuesto sale como `unbudgeted` en vez de pasar en silencio, a propósito: que
aparezca algo que crece tiene que verse.

### Qué NO te dice

- **No te dice qué hay dentro de cada export.** Eso es `AlgoData/INDEX.md`, una línea por export con
  sus filas y columnas.
- **No te dice qué se puede borrar con seguridad.** Eso lo calcula `python3 -m perf.disk.report`,
  que propone y nunca borra.
- **No cubre el árbol de SQX.** Lo que hay dentro de un `.sqx` o de un `project.cfx` está en
  `knowhow/sqx-format/`.

### Si algo falla

| síntoma | qué pasa |
|---|---|
| no encuentras un export que juras haber hecho | míralo en `AlgoData/INDEX.md`; si no está, no se escribió |
| un directorio sin `manifest.json` | no es reproducible. Vuelve a exportarlo antes de usarlo |
| `AlgoData N GB de 90 GB` y se para una corrida | `python3 -m perf.disk.report` dice qué rama y qué sobra |
| faltan `.sqx` en un databank del maestro | regla dura 1: un sync los borró. Mira `knowhow/databanks/sync-deletes-unloaded-files.md` |
