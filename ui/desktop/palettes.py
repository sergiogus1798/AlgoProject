"""The palette view: the library of block selections, and what the open one lets the builder draw."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QLabel, QListWidget, QListWidgetItem, QSplitter, QVBoxLayout,
                               QWidget)

from ui.desktop import client
from ui.desktop.blocktable import BlockTable
from ui.desktop.palettebar import PaletteBar
from ui.desktop.theme import C, chip


class Palettes(QWidget):
    """One palette of the library at a time, its blocks by category, and the writes."""

    def __init__(self) -> None:
        """Build the bar, the category list and the block table."""
        super().__init__()
        self.data: dict = {"blocks": {}, "palettes": {}, "family_labels": {}}
        self.open = ""
        self.pending: dict[str, int] = {}

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)
        lay.addWidget(QLabel("Paletas de bloques", objectName="h1"))
        self.bar = PaletteBar()
        self.bar.opened.connect(self.on_open)
        self.bar.searched.connect(self.fill_table)
        self.bar.restated.connect(self.restate)
        self.bar.saved.connect(self.write)
        self.bar.cloned.connect(self.on_clone)
        self.bar.removed.connect(self.on_delete)
        lay.addWidget(self.bar)

        self.about = QLabel()
        self.about.setWordWrap(True)
        lay.addWidget(self.about)
        self.caveat = QLabel(objectName="faint")
        self.caveat.setWordWrap(True)
        lay.addWidget(self.caveat)

        split = QSplitter(Qt.Horizontal)
        self.categories = QListWidget()
        self.categories.setMinimumWidth(260)
        self.categories.currentItemChanged.connect(lambda *_: self.fill_table())
        split.addWidget(self.categories)
        self.table = BlockTable()
        self.table.picked.connect(self.on_weight)
        split.addWidget(self.table)
        split.setSizes([280, 880])
        lay.addWidget(split, 1)

    def entry(self) -> dict:
        """The open palette's whole entry — its file, its resolution and its summary."""
        return self.data["palettes"][self.open]

    def reload(self, keep: str | None = None) -> None:
        """Fetch the library and redraw everything.

        Args:
            keep: Slug to reopen, defaulting to whichever was open.
        """
        self.data = client.get("palettes")
        self.pending = {}
        self.open = self.bar.fill(self.data["palettes"], self.data["family_labels"],
                                  keep or self.open)
        self.on_open(self.open)

    def on_open(self, name: str) -> None:
        """Open one palette of the library.

        Args:
            name: Its slug.
        """
        self.open = name or self.open
        self.pending = {}
        p = self.entry()["palette"]
        self.bar.policy.setCurrentIndex(self.bar.policy.findData(p["unlabelled"]))
        self.bar.delete.setEnabled(p["origin"] != "default")
        self.bar.delete.setToolTip(
            "Una paleta por defecto no se borra: clónala y edita la copia."
            if p["origin"] == "default" else "")
        self.fill_categories()
        self.fill_table()

    def resolved(self, key: str) -> dict:
        """One block's switch under the open palette, pending edits included.

        Args:
            key: Block key.

        Returns:
            `use`, `weight` and `why` as the daemon resolved them, unless the reader has
            changed this block since the last save — then the pending override, because a
            table that showed the saved value after a click would look broken.
        """
        if key not in self.pending:
            return self.entry()["resolved"][key]
        weight = self.pending[key]
        return {"use": weight > 0, "weight": max(weight, 1), "why": "pendiente"}

    def fill_categories(self) -> None:
        """Rebuild the left list, each category with how many of its blocks are on."""
        current = self.categories.currentItem()
        keep = current.data(Qt.UserRole) if current else None
        self.categories.clear()
        by: dict[str, list[str]] = {}
        for key, block in self.data["blocks"].items():
            by.setdefault(block["category"], []).append(key)
        for category in sorted(by):
            on = sum(1 for k in by[category] if self.resolved(k)["use"])
            item = QListWidgetItem(f"{category}    {on}/{len(by[category])}")
            item.setData(Qt.UserRole, category)
            if on == 0:
                item.setForeground(Qt.GlobalColor.gray)
            self.categories.addItem(item)
        self.categories.setCurrentRow(
            next((i for i in range(self.categories.count())
                  if self.categories.item(i).data(Qt.UserRole) == keep), 0))

    def rows(self) -> list[tuple[str, dict]]:
        """The blocks the table should show, under the category and the search box.

        Returns:
            Key and block, sorted. A search term ignores the category so a block can be
            found without knowing which of the 83 categories SQX filed it under.
        """
        term = self.bar.search.text().lower()
        item = self.categories.currentItem()
        category = item.data(Qt.UserRole) if item else None
        out = []
        for key, block in sorted(self.data["blocks"].items()):
            if term:
                if term not in key.lower() and term not in block["form"].lower():
                    continue
            elif block["category"] != category:
                continue
            out.append((key, block))
        return out

    def fill_table(self) -> None:
        """Redraw the block table for the current category or search."""
        stored = self.entry()["palette"]["overrides"]
        family = self.entry()["palette"]["family"]
        self.table.show_blocks([(key, block, self.resolved(key),
                                 self.pending.get(key, stored.get(key)),
                                 block["archetypes"].get(family))
                                for key, block in self.rows()])
        self.restate()

    def on_weight(self, key: str, weight: int | None) -> None:
        """Record an override the reader picked, without writing it yet.

        Args:
            key: Block key.
            weight: The chosen weight, or None to drop the override.
        """
        if weight is None:
            self.pending.pop(key, None)
            self.entry()["palette"]["overrides"].pop(key, None)
        else:
            self.pending[key] = weight
        self.fill_categories()
        self.restate()

    def restate(self) -> None:
        """Update the counts, the description of the open palette and the caveat."""
        p, s = self.entry()["palette"], self.entry()["summary"]
        pend = f"  ·  {len(self.pending)} sin guardar" if self.pending else ""
        band = chip(f"condiciones {s['signal']['on']}", C["promising"] if s["conditions_ok"]
                    else C["dead"])
        self.bar.counts.setText(
            f"{band}  de {s['signal']['of']}  ·  "
            f"indicador {s['indicator']['on']}/{s['indicator']['of']}  ·  "
            f"nivel {s['level']['on']}/{s['level']['of']}  ·  "
            f"{s['overridden']} elegidos a mano  ·  {s['unlabelled']} sin etiquetar{pend}")
        self.bar.counts.setToolTip(
            "El dueño pide entre 90 y 170 condiciones por build: por debajo el builder no "
            "tiene de dónde combinar, por encima vuelve el sobreajuste que esto evita.")
        self.bar.save.setEnabled(
            bool(self.pending) or self.bar.policy.currentData() != p["unlabelled"])
        self.about.setText(self.describe(p, s))
        note = ("Una paleta gobierna los huecos LIBRES de una plantilla. Un hueco atado a un "
                "grupo sortea ese grupo y la ignora; un bloque fijo es parte del esqueleto. "
                "Medido el 2026-09-24.")
        if s["pooled_off"]:
            note += (f"  {chip(str(s['pooled_off']) + ' apagados están en un grupo', C['weak'])}"
                     "  — esos se escapan por esa vía.")
        self.caveat.setText(note)

    def describe(self, p: dict, s: dict) -> str:
        """The line under the bar saying what the open palette is, and whether it does anything.

        Args:
            p: The open palette.
            s: Its summary.

        Returns:
            Rich text. A palette whose every decision still comes from the unlabelled
            default is doing nothing, and saying so is the difference between a view that
            looks broken and one that is honest about being empty.
        """
        bits = [chip(self.data["family_labels"][p["family"]], C["accent"]),
                chip(p["origin"], C["muted"])]
        if p["based_on"]:
            bits.append(chip(f"de {p['based_on']}", C["muted"]))
        head = " ".join(bits) + f'  <span style="color:{C["muted"]}">{p["note"]}</span>'
        if not s["conditions_ok"]:
            head += (f'<br><span style="color:{C["dead"]}">⚠️ {s["signal"]["on"]} condiciones: '
                     "fuera del 90–170 que pide el dueño. "
                     + ("Faltan bloques por elegir." if s["signal"]["on"] < 90
                        else "Sobran: esta paleta no está estrechando lo suficiente.")
                     + "</span>")
        if s["overridden"] == 0 and s["unlabelled"] == len(self.data["blocks"]):
            head += (f'<br><span style="color:{C["weak"]}">⚠️ Esta paleta no elige nada '
                     f'todavía: sus {s["unlabelled"]} bloques salen del valor por defecto, '
                     "así que deja pasar todo el vocabulario. Elige bloques en la columna "
                     "Peso, o etiqueta la familia en taxonomy.yaml.</span>")
        return head

    def write(self) -> None:
        """Send the open palette to the daemon and redraw from what it wrote."""
        p = self.entry()["palette"]
        overrides = dict(p["overrides"])
        overrides.update(self.pending)
        client.post(f"palette/{self.open}",
                    {"label": p["label"], "note": p["note"],
                     "unlabelled": self.bar.policy.currentData(), "overrides": overrides})
        self.reload()

    def on_clone(self, slug: str, label: str, source: str) -> None:
        """Add a copy of the open palette to the library.

        Args:
            slug: File name for the copy.
            label: What it is called on screen.
            source: Slug being copied.
        """
        family = self.data["palettes"][source]["palette"]["family"]
        client.post("palettes/new",
                    {"name": slug, "label": label, "family": family, "source": source})
        self.reload(slug)

    def on_delete(self) -> None:
        """Remove the open palette and fall back to whatever the library still holds."""
        client.post(f"palette/{self.open}/delete", {})
        self.open = ""
        self.reload(None)
