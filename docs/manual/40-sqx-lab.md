# 40. sqx-lab — instalar y refrescar el kit de autoría sin `/plugin`

## Qué pregunta responde

«¿Por qué las skills que escriben bloques, grupos, plantillas y proyectos de SQX no se instalan con
`/plugin` como dice su web, y cómo me aseguro de que están bien?»

`sqx-lab` es un plugin de Claude Code del autor de StrategyQuant. Su instalación oficial son dos
comandos:

```
/plugin marketplace add /home/sergioguslw/Desktop/AlgoProject/tools/sqx-lab
/plugin install sqx-lab@sqx-lab
```

y **en este entorno no existen**. Medido el 2026-09-24: la extensión de VSCode responde
`/plugin isn't available in this environment`. Así que el kit se instala a mano, y este script es esa
mano.

**Lo único que pierdes** respecto a una instalación de plugin de verdad es la actualización
automática. Las cuatro skills y los dos comandos se comportan igual una vez enchufados.

## Cuándo lo usas, y cuándo no

- **Sí**, la primera vez en una máquina nueva.
- **Sí**, después de bajar una versión nueva del zip y descomprimirla sobre `tools/sqx-lab/`.
- **Sí**, cada vez que cambien los bloques o los grupos del install que construye — los catálogos se
  quedan rancios y **un catálogo rancio no falla: inventa átomos** que no están en el install, y la
  plantilla sale silenciosamente mal.
- **No** para arreglar un fallo de una plantilla concreta. Para eso, `/sqx-doctor` primero.

## Antes de empezar

Sólo que exista el install cuyos catálogos quieres construir. El script lo comprueba y se niega si
no está. No hace falta parar SQX: sólo lee `customBlocks.xml`, `blockGroups.xml`, `user/projects` y
`user/settings/StrategyTemplates`.

## Cómo se ejecuta

```bash
bin/sqx-lab-install.sh
bin/sqx-lab-install.sh --role custodian     # construir los catálogos de otro install
```

| flag | obligatorio | qué hace |
|---|---|---|
| `--role` | no | de qué install salen los catálogos. Por defecto **conductor**, que es el carril de autoría |

Es **idempotente**: se puede correr todas las veces que quieras. Tarda unos segundos, salvo los
catálogos, que son medio minuto.

## Qué produce

| ruta | qué es |
|---|---|
| `~/.claude/skills/sqx-*` | **cuatro symlinks** a las skills del plugin. Enlaces, no copias: así una versión nueva se ve sin volver a copiar nada |
| `~/.claude/commands/sqx-setup.md`, `sqx-doctor.md` | **copias**, y aquí está el detalle que importa |
| `tools/sqx-lab/.../catalog.json` y `catalog.md` | los catálogos, uno por skill, junto a su propia skill |
| `~/.sqx-lab/sqx-install.txt` | el install que las cuatro comparten. Lo escribe el bootstrap |

⚠️ **Por qué los comandos son copias y no enlaces.** Los del fabricante llaman a
`"${CLAUDE_PLUGIN_ROOT}/doctor.py"`, y esa variable sólo la define una instalación de plugin de
verdad. El script las copia sustituyendo la variable por la ruta real. **Ésa es la razón por la que
una actualización obliga a volver a correr esto**: los enlaces se actualizan solos, las copias no.

⚠️ **Hay una quinta carpeta de skill que NO se enchufa a propósito.** `sqx-spp` es local, no viene
del zip, y duplica el `/spp` de este proyecto. Dos skills de SPP solapadas es peor que una, así que
el script nombra las cuatro del fabricante una por una en lugar de recorrer la carpeta. Cuidado:
descomprimir una versión nueva encima de `tools/sqx-lab/` **se la lleva por delante**.

## Cómo se lee el resultado

Salida real del 2026-09-24:

```
sqx-lab 1.2.0  ->  conductor (/home/sergioguslw/Desktop/SQX_w1)
  skill   sqx-custom-block
  skill   sqx-random-group
  skill   sqx-strategy-template
  skill   sqx-strategy-project
  command /sqx-setup
  command /sqx-doctor
catálogos:
    note: 74 talib_* atoms flagged UNUSABLE in single-symbol builds
    .../sqx-random-group/catalog.md
wrote .../sqx-strategy-template/engine/catalog.json
-> .../sqx-strategy-project/engine/catalog.json (7 projects, 8 templates)

====================================================================
All green — the full block -> group -> template -> project chain is usable.
```

**La última línea es la que se mira.** Cualquier cosa que no sea `All green` la explica el propio
doctor con la orden que lo arregla. Lo que decía antes de correr esto, el 2026-09-24:

```
[ WARN ] sqx-custom-block  —  built 20d ago from a DIFFERENT install: /home/sergioguslw/Desktop/SQX
```

Veinte días rancio y construido contra el **maestro** en vez del conductor. Eso es el fallo que hay
que reconocer: las skills diseñaban contra bloques de otro install.

## Un ejemplo completo — actualizar a una versión nueva

```bash
cd /tmp && curl -sSLO https://strategyquant.com/wp-content/uploads/2026/08/sqx-lab-1.2.0.zip
unzip -q sqx-lab-1.2.0.zip -d nuevo

# mira qué cambia antes de sobrescribir; los catalog.json y __pycache__ salen siempre
diff -rq nuevo/sqx-lab ~/Desktop/AlgoProject/tools/sqx-lab | grep -v catalog -e __pycache__

# guarda la skill local, que el copiado se la lleva
cp -r ~/Desktop/AlgoProject/tools/sqx-lab/plugins/sqx-lab/skills/sqx-spp /tmp/
cp -r nuevo/sqx-lab/. ~/Desktop/AlgoProject/tools/sqx-lab/
cp -r /tmp/sqx-spp ~/Desktop/AlgoProject/tools/sqx-lab/plugins/sqx-lab/skills/

cd ~/Desktop/AlgoProject && bin/sqx-lab-install.sh
```

## Qué NO te dice

- **No dice que una plantilla vaya a construir.** Sólo que las skills ven el vocabulario correcto.
  Lo que construye o no lo dice el motor: `sqx/inspect/template_check.py` después del build.
- **No compara los tres installs entre sí.** Un bloque puede estar en el conductor y no en el
  custodio, y entonces el build ignora la plantilla sin un solo error. Eso es
  `python3 -m sqx.inspect.vocabulary --diff custodian`.
- **No instala nada en SQX.** Los bloques que una skill escribe se instalan con
  `python3 -m sqx.blocks.install`, con el install parado.

## Si algo falla

- **`no está el plugin en …`** — `tools/sqx-lab/` no existe o está a medio descomprimir. Baja el zip
  otra vez.
- **`el install <rol> no existe`** — el rol no está en `config/machine.yaml`.
- **Un `[ WARN ] STALE catalog` justo después de correrlo** — el install cambió entre el bootstrap y
  el doctor, o construiste los catálogos contra un rol distinto del que mira el doctor. Ese rol sale
  de `~/.sqx-lab/sqx-install.txt`.
