# 23 · El archivo de estrategias — encargo autocontenido

**Tu oficio:** Python (formato de almacenamiento, escritura y lectura). La ventana consume esto desde
dos sitios: el botón «Archivar» de la ficha de estrategia y el botón «Importar» de PORTFOLIOS
(`22-ventana-rediseno.md` §2 y §5).

Lee `core/study/CONTRACT.md` · `studies/CLAUDE.md` · `portfolio/CLAUDE.md` · `ledger/`.

---

## 0 · Por qué existe

Una estrategia que ha pasado la secuencia ha costado mucha CPU. El dueño quiere guardarla «como oro
en paño», con el `.sqx` de SQX y todos los resultados de Python, y **recargarla después sin rehacer
ningún test**, sobre todo para el módulo de portfolio.

## 1 · Cuándo se archiva

**A mano, con un botón «Archivar»**, en cualquier paso. Decisión del dueño, 2026-09-27. No hay
archivado automático. El archivo anota en qué paso del workflow estaba la estrategia al archivarla.

## 2 · Qué se guarda

- **El dato, no el veredicto.** Guardar solo «pasa / no pasa» no sirve: hace falta el resultado
  entero de cada estudio, sobre todo de los caros (la distribución completa de las 25.000 corridas
  del monkey, no volver a correrla). Lo barato, como un profit factor, da igual si se guarda o se
  recalcula.
- **Sin figuras.** La ventana redibuja a partir de los números (`desktop/blocks/`).
- Además de los resultados, **congelar lo que hace falta para poder juzgarla después**:
  - el `.sqx` y el export de trades;
  - **la versión de la ficha de costes del activo** con la que se hizo cada backtest (los costes de
    `assets/` cambian con el tiempo);
  - el `config_hash` de cada estudio y el commit de git;
  - **la cuenta del Ledger**: cuántas estrategias se buscaron para dar con esta. Sin ella, el
    módulo de portfolio no puede deflactar su Sharpe y no hay forma de saber si es oro o suerte;
  - el paso del workflow en el que se archivó.
- La clave es el `identity` (SHA-256 normalizado), el mismo que usa todo el proyecto.
- **Una vez archivada, es de solo lectura.** Si se vuelve a correr un estudio, se archiva otra
  versión; nunca se sobrescribe.

## 3 · Formato

El dueño delega el diseño («sé que puede ser un lío, acepto tus sugerencias»). Punto de partida:
cada estudio ya escribe `verdict.csv` + `manifest.json` en `reports/<P>/<D>/<día>/<estudio>/`. El
archivo **consolida y congela** eso por `identity`, desde todos los databanks y estudios del
proyecto de origen, en una carpeta propia. Encima va un `manifest.json` que lista qué estudios hay,
con qué `config_hash` y todo lo del §2.

Es dato pesado: va en `AlgoData` (`core/paths.py`), nunca en el repositorio (regla 7).

## 4 · Importar

«Importar» en PORTFOLIOS carga una estrategia archivada y la muestra **igual que si viniera de un
databank real**: todos los paneles y todos los datos, sin recalcular nada. Este encargo expone la
lectura: dado un `identity`, devolver la misma forma de datos que el visor ya consume. El encargo 22
pone el botón.

Por ahora solo se importa desde el archivo. Importar desde databanks vivos queda para cuando el dueño
lo pida.

## 5 · Cómo cierra

Como todos: **qué hizo · qué verificó, con la salida pegada · qué dejó sin hacer y por qué · qué
descubrió que merezca ir a `knowhow/`.** Prueba de aceptación: archivar una estrategia real con
varios estudios caros, apartar su carpeta de `reports/` original e importarla. Los paneles tienen que
verse idénticos y **no puede lanzarse ni un cálculo**. Además, el capítulo del manual correspondiente
(regla 8).
