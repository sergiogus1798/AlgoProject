"""The asset zone: the library of instruments, the four shared files, and every write on them."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QMessageBox, QPushButton,
                               QScrollArea, QSplitter, QStackedWidget, QVBoxLayout, QWidget)

from ui.desktop import client
from ui.desktop.assetcard import AssetCard
from ui.desktop.assetforms import NewAssetBox, explain
from ui.desktop.assetlist import AssetList, SHARED
from ui.desktop.assetspans import AssetSpans
from ui.desktop.yamltree import YamlTree

class Assets(QWidget):
    """Every instrument the project knows, and the files that say what one costs."""

    def __init__(self) -> None:
        """Build the bar, the list down the left and the three pages on the right."""
        super().__init__()
        self.data: dict = {"assets": [], "retired": [], "classes": {}}
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)
        lay.addWidget(QLabel("Activos", objectName="h1"))
        lay.addLayout(self.bar())

        split = QSplitter(Qt.Horizontal)
        self.list = AssetList()
        self.list.opened.connect(self.open)
        split.addWidget(self.list)

        self.stack = QStackedWidget()
        self.card, self.spans, self.tree = AssetCard(), AssetSpans(), YamlTree()
        self.card.changed.connect(self.reopen)
        self.spans.changed.connect(self.reopen)
        self.tree.edited.connect(self.on_edit)
        self.stack.addWidget(self.sheet())
        self.stack.addWidget(self.raw_page())
        self.retired_page = explain("")
        self.stack.addWidget(self.retired_page)
        split.addWidget(self.stack)
        split.setSizes([260, 1000])
        lay.addWidget(split, 1)

    def bar(self) -> QHBoxLayout:
        """The row of counts and actions above the list.

        Returns:
            The layout, its buttons already wired.
        """
        row = QHBoxLayout()
        self.counts = QLabel(objectName="muted")
        row.addWidget(self.counts)
        row.addStretch()
        self.raw = QPushButton("Fichero entero")
        self.raw.setCheckable(True)
        self.raw.setToolTip("La ficha muestra las decisiones. El fichero entero muestra TODOS "
                            "sus valores, cada uno con lo que el propio YAML dice de él.")
        self.raw.clicked.connect(lambda *_: self.open())
        self.new = QPushButton("Nuevo activo")
        self.new.clicked.connect(self.on_new)
        self.drop = QPushButton("Retirar")
        self.drop.setToolTip("Mueve el fichero a assets/symbols/_retired/. Deja de contar para "
                             "`core.assets`, pero no se pierde y se puede restaurar.")
        self.drop.clicked.connect(self.on_retire)
        for b in (self.raw, self.new, self.drop):
            row.addWidget(b)
        return row

    def raw_page(self) -> QWidget:
        """The whole file as a table, under the line that says which file it is.

        Returns:
            A widget holding the header and the tree. Without the header the reader cannot
            tell an asset's own file from one of the four that decide for all of them.
        """
        page = QWidget()
        inner = QVBoxLayout(page)
        inner.setContentsMargins(0, 0, 0, 0)
        inner.setSpacing(8)
        self.tree_head = QLabel(objectName="h2")
        self.tree_what = explain("")
        inner.addWidget(self.tree_head)
        inner.addWidget(self.tree_what)
        inner.addWidget(self.tree, 1)
        return page

    def sheet(self) -> QScrollArea:
        """The asset page: its costs above, its windows below, in one scroll.

        Returns:
            A scroll area holding the two widgets. They are one page and not two tabs
            because a window is read against the costs that fill it.
        """
        holder = QWidget()
        inner = QVBoxLayout(holder)
        inner.setContentsMargins(0, 0, 12, 0)
        inner.setSpacing(16)
        inner.addWidget(self.card)
        inner.addWidget(self.spans)
        inner.addStretch()
        area = QScrollArea()
        area.setWidget(holder)
        area.setWidgetResizable(True)
        area.setFrameShape(QScrollArea.NoFrame)
        return area

    def reload(self, keep: str | None = None) -> None:
        """Fetch the library and redraw the list.

        Args:
            keep: Which entry to reopen, defaulting to whichever is open.
        """
        current = keep or self.list.selected()
        self.data = client.get("assets")
        blocked = [a["symbol"] for a in self.data["assets"] if a["pending"] or a["broken"]]
        soft = [a for a in self.data["assets"] if a["provisional"] and a["symbol"] not in blocked]
        self.counts.setText(
            f"{len(self.data['assets'])} activos · {len(blocked)} bloqueados · {len(soft)} sólo "
            f"con cifras provisionales · {len(self.data['retired'])} retirados")
        self.counts.setToolTip(
            "Bloqueado = algún coste obligatorio sin pactar o el esquema roto: la preflight "
            "sale distinta de 0 y no se autoriza nada. Provisional = hay cifra, se puede "
            "trabajar, y todo resultado con coste arrastra la advertencia.")
        self.list.fill(self.data["assets"], self.data["retired"], current)

    def open(self, kind: str = "", name: str = "") -> None:
        """Draw whatever is selected, on the page its kind needs.

        Args:
            kind: "asset", "shared" or "retired". Empty means «whatever is open», which is
                what the raw/sheet toggle sends.
            name: Its name, under the same rule.
        """
        kind = kind or (self.list.currentItem().data(Qt.UserRole) or ("", ""))[0]
        name = name or self.list.selected()
        self.drop.setEnabled(kind == "asset")
        self.raw.setEnabled(kind != "retired")
        if kind == "retired":
            self.retired_page.setText(
                f"`{name}` está retirado en assets/symbols/_retired/{name}.yaml. No lo ve "
                "`core.assets`, no aparece en el índice y ninguna tarea puede usarlo. Su "
                "bloque de tramos sigue en _policy.yaml: si vuelve, vuelve con sus ventanas. "
                "Púlsalo en «Restaurar» para devolverlo a la librería.")
            self.drop.setText("Restaurar")
            self.drop.setEnabled(True)
            self.stack.setCurrentIndex(2)
            return
        self.drop.setText("Retirar")
        if kind == "shared":
            shared = client.get(f"assets/shared/{name}")
            self.tree_head.setText(f"{SHARED[name][0]} — {shared['file']}")
            self.tree_what.setText(SHARED[name][1])
            self.tree.fill(name, shared["leaves"])
            self.stack.setCurrentIndex(1)
            return
        data = client.get(f"asset/{name}")
        self.card.fill(data)
        self.spans.fill(data)
        self.tree_head.setText(f"{name} — assets/symbols/{name}.yaml")
        self.tree_what.setText("Todos los valores del fichero, cada uno con lo que su propio "
                               "comentario dice. Los tramos no están aquí: viven en "
                               "«Política y tramos», que los lleva de los 19 juntos.")
        self.tree.fill(name, data["leaves"])
        self.stack.setCurrentIndex(1 if self.raw.isChecked() else 0)

    def reopen(self) -> None:
        """Redraw after a write, keeping the same entry open."""
        self.reload(self.list.selected())

    def on_edit(self, name: str, path: list, text: str, kind: str) -> None:
        """Write a value the raw table changed.

        Args:
            name: The file it belongs to.
            path: The keys leading to it.
            text: What was typed.
            kind: "scalar" or "list".
        """
        client.post("assets/value", {"name": name, "path": path, "text": text, "kind": kind})
        self.reopen()

    def on_new(self) -> None:
        """Ask for a new instrument and add it with every cost undecided."""
        box = NewAssetBox(self.data["classes"])
        if not box.exec():
            return
        answer = client.post("assets/new", box.payload())
        if "error" in answer:
            QMessageBox.warning(self, "Ese nombre ya existe", answer["error"])
            return
        self.reload(answer["created"])

    def on_retire(self) -> None:
        """Withdraw the open asset, or put a retired one back."""
        kind, name = self.list.currentItem().data(Qt.UserRole)
        if kind == "retired":
            client.post(f"asset/{name}/restore", {})
            self.reload(name)
            return
        ok = QMessageBox.question(
            self, f"Retirar {name}",
            f"El fichero se mueve a assets/symbols/_retired/{name}.yaml. Deja de existir para "
            "`core.assets` y para el índice, y ninguna tarea nueva podrá usarlo. Sus tramos se "
            "quedan en _policy.yaml, así que restaurarlo lo devuelve entero. ¿Lo retiro?")
        if ok == QMessageBox.Yes:
            client.post(f"asset/{name}/retire", {})
            self.reload()
