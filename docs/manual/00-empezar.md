# 0. Empezar

Este manual explica **cómo usar el proyecto**, no cómo está programado por dentro. Todo lo que
aparece aquí son comandos que puedes copiar y pegar en una terminal.

## Qué es esto

StrategyQuant X genera y testea estrategias. Este proyecto hace las matemáticas que SQX no hace:
saca los datos de SQX, los analiza y te devuelve gráficas y conclusiones para que decidas qué
estrategias usar y con qué filtros generarlas.

El trabajo está partido en fases. Cada una tiene su carpeta:

| carpeta | de qué va | ejemplo |
|---|---|---|
| `1_sqx/` | hablar con SQX: sacar datos, inspeccionar proyectos, repararlos | exportar las métricas de un databank |
| `2_tasks/` | analizar **poblaciones enteras**: miles de estrategias a la vez | ¿qué métrica del histórico predice el futuro? |
| `3_strategies/` | analizar **una** estrategia a fondo | traducir una estrategia a Python |
| `4_portfolio/` | carteras | — |

Si tu pregunta es sobre miles de estrategias, es `2_tasks/`. Si es sobre una, es `3_strategies/`.

## La primera vez, en esta máquina

Ya está hecho. Solo lo necesitas si cambias de ordenador:

```bash
cd ~/Desktop/AlgoProject
cp config/machine.example.yaml config/machine.yaml   # y editar las rutas de dentro
python3 -m pip install -r requirements.txt
```

`config/machine.yaml` es el **único** archivo que cambia entre ordenadores: dice dónde está SQX,
dónde van los datos y dónde está el navegador. Ningún otro archivo tiene rutas dentro.

## Cómo se ejecuta cualquier cosa

Siempre igual, y siempre desde la raíz del proyecto:

```bash
cd ~/Desktop/AlgoProject
python3 ruta/del/script.py --unos --flags
```

Todos los comandos aceptan `--help`, que te lista los flags sin ejecutar nada:

```bash
python3 2_tasks/reports/is_oos.py --help
```

## Dónde acaban las cosas

Nada se guarda dentro del proyecto. Todo va a `~/Desktop/AlgoData`, que tiene tres zonas y **cada
una se comporta distinto**. Esto importa:

| zona | qué pasa cuando vuelves a exportar |
|---|---|
| `metrics/<proyecto>/<databank>/` | **se borra lo anterior y se escribe lo nuevo.** Hay un solo CSV vigente por databank, para que nunca tengas dudas de cuál es el bueno |
| `raw/<proyecto>/<databank>/<fecha>/` | **no se toca nada.** Cada exportación de trades y barras es de un día y se queda ahí para siempre |
| `reports/<proyecto>/<databank>/<fecha>/` | **se acumulan.** Los análisis nunca se borran |

La lógica: un CSV lo puedes volver a sacar de SQX cuando quieras. Las conclusiones que sacaste un
día no. Por eso los reportes se guardan todos y los CSV no.

`~/Desktop/AlgoData/INDEX.md` es la lista de todo lo que ya existe. **Míralo antes de exportar
nada**, porque una exportación cuesta minutos de SQX y puede que ya la tengas.

## Las reglas que no puedes romper

Estas son de SQX, no del código, y romperlas destruye trabajo de verdad:

1. **SQX borra del disco las estrategias que no tiene en memoria.** Cada vez que sincroniza. Si vas
   a hacer algo que reinicie SQX, copia antes `user/projects` a otro sitio.
2. **Nunca lances `sqcli` en el SQX principal con la ventana abierta.** No responde. Para eso está
   el worker, que los scripts arrancan y paran solos.
3. **Nunca mates procesos con `pkill -f StrategyQuantX`** — ese patrón también coge tu propia
   terminal. Se mata por PID o no se mata.
4. **Nunca empieces un build.** La ventana de SQX es tuya y de nadie más; los scripts no lanzan
   builds y no deben hacerlo.
5. **Nunca edites un `project.cfx` que SQX tenga abierto.** SQX reescribe el archivo al guardar y
   al salir, y tu cambio desaparece sin avisar.

## Cuándo puedes tener SQX abierto

| lo que haces | ¿puedes tener la GUI de SQX abierta? |
|---|---|
| analizar datos ya exportados | **sí**, no toca SQX para nada |
| exportar métricas, trades o barras | **sí**: los scripts usan el worker, que es una copia aparte |
| inspeccionar proyectos (leer `project.cfx`) | **sí**, es solo lectura |
| reparar un proyecto | **no**, hay que cerrar SQX antes |

## Si algo falla

- **`FileNotFoundError` con una ruta de `AlgoData`** — no has exportado todavía. Mira el paso
  "Antes de empezar" de la página del módulo.
- **Un CSV que sale vacío o solo con la cabecera** — el worker exportó antes de terminar de cargar.
  Vuelve a lanzarlo; el script espera, pero si SQX estaba a medias puede pasar.
- **El comando se queda colgado varios minutos** — normal si toca SQX. Arrancar el worker son ~30 s
  y exportar 10.000 estrategias son minutos. Si pasa de 15 minutos, algo va mal.

## Índice

- [1. Análisis IS/OOS](01-analisis-is-oos.md) — qué métrica del histórico predice el futuro
