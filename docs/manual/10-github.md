# 10. GitHub — tener el proyecto subido y poder clonarlo

## Qué pregunta responde  *(obligatoria)*

«¿Lo que hay en GitHub es lo mismo que tengo en este ordenador?» Y si no lo es, lo sube.

Sirve para dos cosas distintas. Una es **copia de seguridad**: el trabajo de meses no vive solo en
un disco. La otra es **poder trabajar en otro ordenador**: clonas el repositorio y tienes el
proyecto entero, sin tener que copiar carpetas a mano.

Lo que **no** sube nunca son los datos. Los CSV exportados, los `.sqx` y las bases de datos de SQX
se quedan en `~/Desktop/AlgoData` y en las instalaciones. El repositorio son el código y la
documentación: 12 MB, se clona en segundos.

## Cuándo lo usas, y cuándo no  *(obligatoria)*

**Cuándo sí:**

- Al acabar una sesión de trabajo que ha dejado cosas sin commitear.
- **Antes de clonar el proyecto en otro ordenador.** Lo que no esté subido, no aparece en el clon.
- Cuando no sabes si está subido. Preguntarlo cuesta tres segundos.

**Cuándo no:**

- Para mover datos entre ordenadores. Los datos no van por aquí. Se copia `AlgoData` aparte, o se
  vuelve a exportar en el ordenador nuevo.
- Para deshacer algo. Esto sube; no borra ni reescribe historia.
- A mitad de un trabajo que está roto. Si `tools/checks.py` sale en rojo, se arregla primero. Un
  commit roto en GitHub es peor que uno sin subir, porque el siguiente clon empieza desde ahí.

## Antes de empezar  *(obligatoria)*

**Una sola vez en cada ordenador**, hay que identificarse contra GitHub. Es lo único que no puede
hacer una sesión de Claude por ti: necesita un navegador y un código de un solo uso.

```bash
gh auth login
```

Responde: `GitHub.com` → `HTTPS` → sí a autenticar git con las credenciales → `Login with a web
browser`. Te da un código de ocho caracteres, lo pegas en la página que se abre, y ya está para
siempre en ese ordenador.

`gh` está instalado en `~/.local/bin/gh`, no en el sistema. Si `gh: command not found`, añade eso
al PATH:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Para comprobar que estás dentro:

```bash
$ gh auth status
github.com
  ✓ Logged in to github.com account sergioguslw (keyring)
```

SQX no tiene nada que ver con esto. Puedes tener la GUI abierta y a media generación: esto no la
toca.

## Cómo se ejecuta  *(obligatoria)*

No es un script de Python, es una **skill**. Se lanza escribiendo esto en Claude Code:

```
/sync
```

No lleva flags. Lo que hace lo decide leyendo el estado del repositorio:

| situación | qué hace |
|---|---|
| no hay repositorio en GitHub | lo crea **privado** y sube todo |
| hay cosas sin commitear | las agrupa por tema, hace varios commits y los sube |
| todo está commiteado pero sin subir | solo sube |
| todo está subido | te lo dice y no hace nada |

Tarda segundos. Si prefieres hacerlo a mano, son tres órdenes:

```bash
git status --porcelain          # qué hay pendiente
python3 tools/depmap.py && python3 tools/checks.py   # tiene que salir verde
git push -u origin --all
```

La diferencia es que la skill además comprueba que no se cuele nada que no debe.

## Qué produce  *(obligatoria)*

Nada en disco. Cambia dos cosas:

- El **historial de git local**: uno o varios commits nuevos.
- El **repositorio de GitHub**, que pasa a tener lo mismo que tú.

No sobrescribe nada tuyo, no borra ramas y no reescribe commits ya subidos.

## Cómo se lee el resultado  *(obligatoria)*

Al final te dice qué commits ha hecho. Así salió la primera vez, con todo el atraso acumulado:

```
$ git log --oneline -10
b5680cf Make the analysis half of the project run on Windows
16b0e71 claude: the three analysis skills, and permissions that ask before touching SQX
645a21f knowhow and audit: custom metric columns, export and databank findings
63d85ca docs: manual pages for filters, samples, decay, retests, Monte Carlo, SPP and WFM
628713b strategies: cross-market random-entry study and the trade-level Monte Carlo suite
df75471 tasks: decay, improvement and replication analyses, with the filter and comparison reports
2cabbd7 sqx: exporters for bars, retests, SPP and WFM, and the curation step that applies a verdict
559b37e core: readers for bars, trades, databank stats, SPP profiles and walk-forward matrices
fce8635 OPEN.md: record the layout rename and the retired pipeline maps
```

**La línea que importa de verdad es esta:**

```
$ git status -sb
## fix/open-issues-2026-09-04...origin/fix/open-issues-2026-09-04
```

Si detrás del nombre de la rama **no** pone `[ahead 3]` ni `[behind 1]`, GitHub tiene exactamente lo
que tienes tú. Si pone `[ahead N]`, hay N commits tuyos sin subir. Si pone `[behind N]`, hay N
commits en GitHub que tú no tienes, que es lo que pasa cuando has trabajado en el otro ordenador.

Y si el `git status --porcelain` final sale **vacío**, no queda nada sin commitear. Cualquier línea
que salga ahí es trabajo que **no** está en GitHub y que **no** aparecerá en el clon.

## Un ejemplo completo  *(obligatoria)*

Clonar el proyecto en otro ordenador, de principio a fin. En el ordenador de siempre:

```
/sync
```

Te contesta con la URL. En el ordenador nuevo:

```bash
git clone https://github.com/sergioguslw/AlgoProject.git
cd AlgoProject
cp config/machine.example.yaml config/machine.yaml
```

Ahora **edita `config/machine.yaml`** con las rutas de ese ordenador. Es el único archivo que no
viaja en el repositorio, a propósito: es lo único que cambia de una máquina a otra. Si te olvidas,
el error te lo dice con todas las letras:

```
/ruta/AlgoProject/config/machine.yaml is missing. Copy config/machine.example.yaml
to it and edit the paths for this machine — it is the only file not in git.
```

Después:

```bash
python3 -m pip install -r requirements.txt
python3 tools/checks.py
```

Y tiene que salir esto:

```
85 files checked, 0 problems
```

Ahí ya está listo. Los datos no han venido: para analizar, copia `~/Desktop/AlgoData` o vuelve a
exportar. El manual en PDF tampoco viene, se reconstruye con `python3 tools/manual.py`.

En **Windows** funciona la mitad de análisis del proyecto, no la que maneja SQX. Está explicado en
la sección *Windows* del `README.md`, y en `machine.yaml` las rutas se escriben con barras normales:
`C:/Users/sergio/Desktop/AlgoData`.

## Qué NO te dice  *(obligatoria)*

- **No te dice si el código está bien.** Solo que pasa las comprobaciones mecánicas: longitudes,
  docstrings, rutas absolutas, READMEs. Eso es `/audit`, y ni eso juzga si un análisis concluye bien.
- **No decide qué rama es la buena.** Sube las que haya y las deja ahí. Fusionar `master` con una
  rama de trabajo lo decides tú.
- **Un repositorio subido no es una copia de seguridad de tu trabajo con SQX.** Los proyectos, las
  databanks y las estrategias no están aquí. Si se pierde la instalación de SQX, GitHub no te la
  devuelve.
- **No garantiza que el clon dé los mismos números.** Da el mismo código. Los mismos resultados
  necesitan además los mismos datos, y los datos van por su cuenta.

## Si algo falla

**`gh: command not found`** — `gh` está en `~/.local/bin`. `export PATH="$HOME/.local/bin:$PATH"`.

**`You are not logged into any GitHub hosts`** — falta `gh auth login`. Tienes que hacerlo tú, en tu
terminal, porque hace falta el navegador.

**`Updates were rejected because the remote contains work that you do not have`** — has trabajado en
el otro ordenador y ahí hay commits que aquí no. `git pull --rebase` y vuelve a subir. **Nunca
`--force`**: eso borra de GitHub el trabajo del otro ordenador.

**`checks.py` en rojo** — se arregla antes de subir. No hay prisa que justifique subir algo roto.
