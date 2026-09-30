"""WFC and CSCV in Configuración SQX: every study input listed, and each write one line, on copies of the files."""

import os
import shutil
import sys
import tempfile
from datetime import date
from pathlib import Path
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.assetyaml import read
from core.paths import ROOT
from ui.daemon.sqxconfig import api, studies

# What the owner found missing on 2026-09-28, and the rest of both steps' inputs.
WFC = {("sppdesign", "n_target"), ("variants", "variants"), ("variants", "seed"),
       ("batch", "min_trades"), ("batch", "split_mode"), ("wfcstudy", "rho_floor")}
CSCV = {("thresholds", "value"), ("cscvstudy", "rules"), ("cscvstudy", "random_draws"),
        ("cscvstudy", "bootstrap"), ("batch", "split_mode")}


def http() -> TestClient:
    """A local app holding only the zone's router; never the real daemon, never 8765."""
    app = FastAPI()
    app.include_router(api.ROUTER)
    return TestClient(app)


def post(c: TestClient, file: str, path: list, value: object) -> tuple[int, dict]:
    """One write through the route, as the window sends it."""
    r = c.post("/api/sqxconfig/value", json={"file": file, "path": path, "value": value})
    return r.status_code, r.json()


def changed(before: str, after: str) -> list[str]:
    """The lines that differ between two versions of a file."""
    a, b = before.splitlines(), after.splitlines()
    return [f"{x!r} -> {y!r}" for x, y in zip(a, b) if x != y] + (["length"] if len(a) != len(b) else [])


def main() -> None:
    """List both sections, then write on temporary copies and read the files back."""
    failures = []
    real = {k: p.read_bytes() for k, p in studies.FILES.items()}
    c = http()
    secs = {s["key"]: s for s in c.get("/api/sqxconfig").json()["sections"]}
    for key, want in (("wfc", WFC), ("cscv", CSCV)):
        have = {(f.get("file"), f["path"][-1] if f.get("file") != "thresholds" else "value")
                for f in secs.get(key, {"fields": []})["fields"]}
        missing = want - have
        if missing:
            failures.append(f"{key}: faltan {sorted(missing)}")
    blocks = [f for f in secs["cscv"]["fields"] if f["key"] == "blocks"]
    if not blocks or "924" not in blocks[0]["help"].replace(".", ""):
        failures.append("cscv: los bloques no dicen sus 924 particiones")

    with tempfile.TemporaryDirectory() as tmp:
        copies = {k: Path(tmp) / f"{k}.yaml" for k in studies.FILES}
        for k, p in studies.FILES.items():
            shutil.copy(p, copies[k])
        with mock.patch.dict(studies.FILES, copies):
            text = {k: p.read_text(encoding="utf-8") for k, p in copies.items()}
            code, out = post(c, "sppdesign", ["design", "n_target"], "6000")
            diff = changed(text["sppdesign"], copies["sppdesign"].read_text(encoding="utf-8"))
            if code != 200 or len(diff) != 1 or "6000" not in diff[0] or "#" not in diff[0]:
                failures.append(f"n_target: {code} {out} {diff}")
            for file, path, value, why in (
                    ("sppdesign", ["design", "n_target"], "5000.5", "entero"),
                    ("sppdesign", ["design", "min_levels"], "12", "max_levels"),
                    ("cscvstudy", ["cscv", "score"], "calmar", "opciones"),
                    ("cscvstudy", ["cscv", "rules"], ["argmax", "argmax"], "repite"),
                    ("variants", ["execute", "project"], "Builder", "no es un valor"),
                    ("batch", ["min_trades"], "-1", "mínimo")):
                code, out = post(c, file, path, value)
                if code != 422 or why not in out.get("detail", ""):
                    failures.append(f"{path} = {value!r} debió negarse por «{why}»: {code} {out}")
            code, out = post(c, "sppdesign", ["design", "strata", "factorial"], "0.5")
            if code != 200 or "suman 0.9" not in out["note"]:
                failures.append(f"estratos: no avisa de la suma: {code} {out}")
            i = blocks[0]["path"][1]
            code, out = post(c, "thresholds", ["thresholds", i, "value"], "13")
            if code != 422 or "impar" not in out.get("detail", ""):
                failures.append(f"bloques impares aceptados: {code} {out}")
            before = text["thresholds"]
            code, out = post(c, "thresholds", ["thresholds", i, "value"], "10")
            row = read(copies["thresholds"])["thresholds"][i]
            if (code != 200 or row["value"] != 10 or row["set_by"] != "dueño"
                    or row["set_on"] != date.today() or "antes 12" not in row["why"]
                    or "252" not in row["why"]):
                failures.append(f"bloques no sellados: {code} {out} {dict(row)}")
            if len(changed(before, copies["thresholds"].read_text(encoding="utf-8"))) != 3:
                failures.append("el Ledger cambió más de las tres líneas de su fila")
            if not out.get("reload"):
                failures.append("un cambio de bloques no pide recargar la zona")
            post(c, "thresholds", ["thresholds", i, "value"], "12")
            again = read(copies["thresholds"])["thresholds"][i]["why"]
            if again.count("fijado por") != 1:
                failures.append(f"el porqué propuesto anida los anteriores: {again}")
            for typed in ("mi razón", "no", "2026-09-28", "bloques: 10 porque sí"):
                code, out = post(c, "thresholds", ["thresholds", i, "why"], typed)
                got = read(copies["thresholds"])["thresholds"][i]["why"]
                if code != 200 or got != typed:
                    failures.append(f"why «{typed}» escrito como {got!r}: {code} {out}")
            code, out = post(c, "thresholds", ["thresholds", i, "why"], "  ")
            if code != 422:
                failures.append(f"un porqué vacío se aceptó: {code} {out}")
            code, out = post(c, "sppdesign", ["design", "n_target"], "500")
            if code != 200 or "por debajo del mínimo" not in out["note"]:
                failures.append(f"máximo bajo el mínimo sin aviso: {code} {out}")
            post(c, "wfcstudy", ["rho_floor"], "1")
            if not isinstance(read(copies["wfcstudy"])["rho_floor"], float):
                failures.append("rho_floor escrito «1» perdió su tipo float")
            code, out = post(c, "batch", ["min_trades"], "31")
            if code != 200 or not out.get("reload"):
                failures.append(f"un valor compartido por WFC y CSCV no pide recargar: {code} {out}")
            doubled = copies["thresholds"].read_text(encoding="utf-8").replace(
                "  - key: marketSurfaces.rho_floor", "  - key: cscv.blocks", 1)
            copies["thresholds"].write_text(doubled, encoding="utf-8")
            r = c.get("/api/sqxconfig")
            locked = [f for s in r.json().get("sections", []) if s["key"] == "cscv"
                      for f in s["fields"] if f.get("locked")] if r.status_code == 200 else []
            if not locked or "2 veces" not in locked[0]["locked"]:
                failures.append(f"una fila duplicada del Ledger tumba la zona: {r.status_code}")
    if {k: p.read_bytes() for k, p in studies.FILES.items()} != real:
        failures.append("un fichero real cambió: las escrituras debían ir a las copias")
    if failures:
        print("\n".join(failures))
        sys.exit(1)
    print(f"ok: WFC {len(secs['wfc']['fields'])} valores, CSCV {len(secs['cscv']['fields'])}, "
          "escrituras y negativas sobre copias")


if __name__ == "__main__":
    main()
