#!/usr/bin/env python3
"""The results routes over the real reports, read-only: shapes, pairing by identity, staleness, old reports."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.paths import DATA, ROOT
from ui.daemon.results import catalogue
from ui.daemon.results.api import ROUTER

STATES = {"pass", "fail", "watch", "info", "none"}


def client() -> TestClient:
    """A local app with only the results router: no daemon, no port.

    Returns:
        The test client.
    """
    app = FastAPI()
    app.include_router(ROUTER)
    return TestClient(app)


def fixture() -> tuple[str, str, str, str]:
    """One real per-strategy contract result to test against.

    Returns:
        project, databank folder, study, strategy name — the last gate strategy JSON by path.
    """
    path = sorted(DATA.glob("reports/*/*/*/gate/estrategias/*.json"))[-1]
    return path.parts[-6], path.parts[-5], path.parts[-3], path.name[:-len(".json")]


def check_catalogue(c: TestClient, failures: list[str]) -> None:
    """Every study folder is listed once, in family order, with a known role."""
    got = c.get("/api/catalogue").json()["studies"]
    keys = [s["key"] for s in got]
    folders = {p.name for p in ROOT.glob("studies/*/*") if p.is_dir()} - {"analysis"}
    if set(keys) != folders | {"monteCarlo"} or len(keys) != len(set(keys)):
        failures.append(f"el catálogo no casa con studies/: {sorted(set(keys) ^ folders)}")
    order = [catalogue.FAMILIES.index(s["family"]) for s in got]
    if order != sorted(order):
        failures.append("el catálogo no sigue el orden de familias")
    if {s["role"] for s in got} - {"gate", "describe"}:
        failures.append("un rol que no es gate ni describe")
    if not {"gate", "crossmarket"} <= {s["key"] for s in got if s["role"] == "gate"}:
        failures.append("la puerta o el cross-market no salen como gate")


def check_result(c: TestClient, failures: list[str]) -> None:
    """A strategy's result pairs by identity; staleness is the hash comparison; the matrix agrees."""
    project, bank, study, name = fixture()
    base = f"/api/result?project={project}&databank={bank}&study={study}"
    one = c.get(f"{base}&strategy={name}").json()
    res, meta = one["result"], one["meta"]
    if res is None or res["strategy"] != name:
        failures.append(f"sin resultado para {name}: {meta}")
        return
    if meta["stale"] != (meta["config_hash"] != meta["current_hash"]):
        failures.append("stale no es config_hash != current_hash")
    wrong = c.get(f"{base}&strategy={name}&identity={'0' * 64}").json()
    if wrong["result"] is not None or not wrong["meta"]["skipped"]:
        failures.append("una identidad distinta con el mismo nombre no se rechaza")
    right = c.get(f"{base}&strategy={name}&identity={res['identity']}").json()
    if right["result"] is None:
        failures.append("la identidad correcta no encuentra su resultado")
    whole = c.get(base).json()["result"]
    if whole is None or whole["strategy"] is not None:
        failures.append("el resultado de población no llega")
    runs = c.get(f"/api/history?project={project}&databank={bank}&study={study}"
                 f"&strategy={name}").json()["runs"]
    if not runs or runs[0]["day"] != meta["day"] or runs[0]["state"] not in STATES:
        failures.append(f"el historial no empieza por el resultado más nuevo: {runs[:1]}")
    grid = c.get(f"/api/matrix?project={project}&databank={bank}").json()
    cell = grid["cells"].get(res["identity"], {}).get(study)
    if cell is None or cell["state"] != res["verdict"]["state"]:
        failures.append(f"la matriz no da el estado del JSON por identidad: {cell}")
    if not all(s["state"] in STATES for row in grid["cells"].values() for s in row.values()):
        failures.append("una celda con un estado fuera de los cinco")


def check_old_reports(c: TestClient, failures: list[str]) -> None:
    """Reports that predate the contract are skipped with a reason, never a crash."""
    for project in sorted(p.name for p in (DATA / "reports").iterdir() if p.is_dir()):
        for bank in sorted(p.name for p in (DATA / "reports" / project).iterdir() if p.is_dir()):
            r = c.get(f"/api/matrix?project={project}&databank={bank}")
            if r.status_code != 200:
                failures.append(f"la matriz de {project}/{bank} rompe: {r.status_code}")
    old = sorted(DATA.glob("reports/*/*/*/decay"))
    if old:
        project, bank = old[0].parts[-4], old[0].parts[-3]
        got = c.get(f"/api/result?project={project}&databank={bank}&study=decay").json()
        if got["result"] is None and not all(s["reason"] for s in got["meta"]["skipped"]):
            failures.append("un informe antiguo se salta sin motivo")
    projects = c.get("/api/projects").json()["projects"]
    if not projects or any(p["project"].startswith("_") for p in projects):
        failures.append("la lista de proyectos está vacía o incluye fixtures")


def check_config(c: TestClient, failures: list[str]) -> None:
    """The drawer's hash is the study's own; an override moves it; a bad one is an error."""
    drawer = c.get("/api/config?study=gate").json()
    knobs = {k["key"]: k for s in drawer["sections"] for k in s["knobs"]}
    if knobs.get("sanidad.min_trades", {}).get("type") != "int" or not knobs[
            "sanidad.min_trades"]["tip"]:
        failures.append("el mando sanidad.min_trades no llega con su tipo y su ayuda")
    same = c.post("/api/config/hash", json={"study": "gate", "overrides": []}).json()
    more = knobs["sanidad.min_trades"]["value"] + 1
    moved = c.post("/api/config/hash", json={
        "study": "gate", "overrides": [f"sanidad.min_trades={more}"]}).json()
    if same.get("hash") != drawer["hash"] or moved.get("hash") in (None, drawer["hash"]):
        failures.append(f"el hash no responde al ajuste: {same} {moved}")
    bad = c.post("/api/config/hash", json={"study": "gate",
                                           "overrides": ["sanidad.min_trades=muchas"]}).json()
    if "error" not in bad:
        failures.append("un ajuste de otro tipo no da error")
    if c.get("/api/config?study=decay").json() != {"sections": [], "hash": None}:
        failures.append("un estudio sin config.yaml no devuelve un cajón vacío")


def main() -> None:
    """Run every check and exit non-zero on the first failure list."""
    c = client()
    failures: list[str] = []
    for check in (check_catalogue, check_result, check_old_reports, check_config):
        check(c, failures)
    print("\n".join(failures) or "ok: catálogo, resultado por identidad, historial, matriz, "
                                 "informes antiguos y cajón de configuración")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
