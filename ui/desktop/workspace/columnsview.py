"""The panel's column views: the metric choice per databank, read off the GUI thread and kept."""

import threading

import httpx
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget

from ui.desktop import client
from ui.desktop.workspace.aggregate import ask
from ui.desktop.workspace.columns import (choices, column_id, diff, is_metric, resolve,
                                          shown_ids)
from ui.desktop.workspace.columnsmenu import ColumnsMenu
from ui.desktop.workspace.table import pick

UNION = "|IS+OOS1"
# The store's key for a databank's metric choice, which every table of it shows (owner,
# 2026-09-28: «se guarda por databank»). A study's own columns stay per table («tab › sub»):
# hiding the gate's verdict in «Build + OOS1» must not blank the «Cribas» tab.
WIDE = "métricas"


class Views(QObject):
    """The column choices and IS+OOS1 figures of the panel's databanks: the metrics one
    databank shows in every table of it, the study columns per table. Both are asked in a
    thread (`fetched` lands them); until then the table paints its default, or «–» with
    «leyendo…» for an IS+OOS1 column, and repaints when they land. A failed read is said and
    not kept: the next paint, the chooser or «Recargar» asks again."""

    fetched = Signal(dict)

    def __init__(self, panel: QWidget) -> None:
        """Belong to one `Panel`, whose `project`, `sub_spec`, `cache` and `open_sub` it uses."""
        super().__init__(panel)
        self.panel = panel
        self.views: dict[str, dict] = {}
        self.segs: dict[str, dict] = {}
        self.failed: dict[tuple, str] = {}
        self.asking: set[tuple] = set()
        self.waiting = ""               # a databank whose chooser opens once its data lands
        self.fetched.connect(self.land)

    def reset(self) -> None:
        """A new project: forget everything read."""
        self.views, self.segs, self.failed, self.waiting = {}, {}, {}, ""

    def forget(self, databank: str | None = None) -> None:
        """A rerun or a reload: read this databank's IS+OOS1 again (every one's for None)."""
        self.segs = {k: v for k, v in self.segs.items() if databank and k != databank}
        self.failed = {}

    def name(self) -> str:
        """The table on screen as the store keys it: «tab › sub»."""
        return f"{self.panel.tab()} › {self.panel.sub_spec().get('sub', '')}"

    def fetch(self, kind: str, databank: str) -> None:
        """Ask `/api/databank/<kind>` (columns | segments) in a thread, once at a time."""
        if (kind, databank) in self.asking:
            return
        self.asking.add((kind, databank))
        project = self.panel.project

        def run() -> None:
            """The GET, off the GUI thread."""
            got = ask(f"databank/{kind}", project=project, databank=databank)
            self.fetched.emit({"kind": kind, "project": project, "databank": databank,
                               "got": got})
        threading.Thread(target=run, daemon=True).start()

    def land(self, msg: dict) -> None:
        """Keep what a thread read (or its failure, unkept) and repaint or open the chooser."""
        kind, bank, got = msg["kind"], msg["databank"], msg["got"]
        self.asking.discard((kind, bank))
        if msg["project"] != self.panel.project:
            return
        if kind == "columns" and "views" in got:
            self.views[bank] = got["views"]
        elif kind == "segments" and "rows" in got:
            self.segs[bank] = got | {"no_oos": set(got.get("no_oos", []))}
        else:
            self.failed[(kind, bank)] = got.get("error", "respuesta sin datos")
        spec = self.panel.sub_spec()
        if spec.get("databank") == bank and not spec.get("blocked"):
            if self.waiting == bank and self.ready(bank, True):
                self.waiting = ""
                self.panel.say(self.choose())
            else:
                self.panel.open_sub(self.panel.sub.currentIndex())
        if (kind, bank) in self.failed:
            self.panel.say(f"No se pudieron leer las columnas de {bank}: "
                           f"{self.failed[(kind, bank)]}")

    def ready(self, bank: str, full: bool) -> bool:
        """Whether what a paint (or, `full`, the chooser) needs is read or failed."""
        need = [("columns", self.views)] + ([("segments", self.segs)] if full else [])
        return all(bank in held or (kind, bank) in self.failed for kind, held in need)

    def seg_state(self, bank: str) -> dict | None:
        """The IS+OOS1 figures, `{error}` when the read failed, None while not read."""
        err = self.failed.get(("segments", bank))
        return {"error": err} if err else self.segs.get(bank)

    def offer(self, table: dict, spec: dict, full: bool) -> tuple[dict, list[str], list[str]]:
        """What the table can show, what it shows, and its default ids; asks what is missing.

        Args:
            table: Its databank's payload.
            spec: The sub-panel.
            full: The chooser: read the IS+OOS1 figures even when no column shows them.
        """
        bank = spec["databank"]
        if bank not in self.views and ("columns", bank) not in self.failed:
            self.fetch("columns", bank)
        held = self.views.get(bank, {})
        own = pick(table["columns"], spec)
        defaults = [column_id(table["columns"][i]) for i, _ in own[1:]]
        ids = shown_ids(held.get(WIDE), [d for d in defaults if is_metric(d)]) + [
            k for k in shown_ids(held.get(self.name()), [d for d in defaults if not is_metric(d)])
            if not is_metric(k)]
        if ((full or any(k.endswith(UNION) for k in ids)) and bank not in self.segs
                and ("segments", bank) not in self.failed):
            self.fetch("segments", bank)
        return choices(table["columns"], own, self.seg_state(bank)), ids, defaults

    def view(self, table: dict, spec: dict) -> tuple[list[dict], list[int], dict | None]:
        """The columns to paint, the sub-panel's own study columns and the IS+OOS1 figures.

        Returns:
            (`columns.resolve`, payload indices of the study columns that decide which rows a
            study sub-panel holds — empty for «every study» —, the segments read or None).
        """
        offered, ids, _ = self.offer(table, spec, False)
        own = pick(table["columns"], spec)
        judged = ([i for i, _ in own if table["columns"][i]["kind"] == "study"]
                  if spec["studies"] != ["*"] else [])
        return resolve(ids, offered), judged, self.segs.get(spec["databank"])

    def keep(self, shown: list[str] | None) -> str:
        """Write the choice as its difference from the default: the metrics for the whole
        databank, the study columns for this table (None: forget both).

        Returns:
            What went wrong, or ''.
        """
        spec = self.panel.sub_spec()
        bank, held = spec["databank"], self.views.get(spec["databank"], {})
        wanted = {WIDE: None, self.name(): None}
        if shown is not None:
            offered, _, defaults = self.offer(self.panel.cache[bank], spec, False)
            for key, metric in ((WIDE, True), (self.name(), False)):
                wanted[key] = diff([k for k in shown if is_metric(k) == metric],
                                   [d for d in defaults if is_metric(d) == metric],
                                   held.get(key), offered)
        errors = []
        for key, view in wanted.items():
            try:            # a click the owner waits for: two local writes, a few ms
                got = client.post("databank/columns", {"project": self.panel.project,
                                                       "databank": bank, "table": key,
                                                       "view": view})
            except httpx.HTTPError as failed:
                got = {"error": f"El demonio no respondió: {failed}"}
            if "views" in got:
                self.views[bank] = got["views"]
                continue
            errors.append(got.get("error", ""))
            kept = self.views.setdefault(bank, {})    # not on disk: at least for this session
            kept.pop(key, None)
            if view is not None:
                kept[key] = view
        return f"Métricas cambiadas solo en esta sesión: {errors[0]}" if errors else ""

    def choose(self) -> str:
        """«Métricas»: the chooser over the table on screen, once its data is read.

        Returns:
            A line for the panel's status, '' when nothing needs saying.
        """
        spec = self.panel.sub_spec()
        if not spec or spec.get("blocked") or spec["databank"] not in self.panel.cache:
            return "Este panel no tiene tabla: no hay columnas que elegir."
        bank = spec["databank"]
        self.failed = {k: v for k, v in self.failed.items() if k[1] != bank}
        offered, ids, _ = self.offer(self.panel.cache[bank], spec, True)
        if not self.ready(bank, True):
            self.waiting = bank
            return f"Leyendo las columnas de {bank}…"
        menu = ColumnsMenu(offered, ids, bank, self.seg_state(bank), self.panel)
        if not menu.exec():
            return ""
        said = self.keep(menu.answer)
        self.panel.open_sub(self.panel.sub.currentIndex())
        return said
