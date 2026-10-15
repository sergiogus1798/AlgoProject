"""WFC and CSCV in Configuración SQX: every study input listed, and each write one line, on copies of the files."""

import difflib
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
from ui.daemon.sqxconfig import api, studies

# What the owner found missing on 2026-09-28, and the rest of both steps' inputs.
WFC = {
    ("sppdesign", "min_levels"),
    ("thresholds", "value"),
    ("variants", "seed"),
    ("batch", "min_trades"),
    ("batch", "split_mode"),
    ("thresholds", "value"),
    ("calibcfg", "seed"),
    ("cloudcfg", "sobol_power"),
}
CSCV = {("thresholds", "value"), ("cscvstudy", "seed"), ("cscvstudy", "median_low")}
# Steps 18.5 and 19 are editable from the window like the other two (2026-10-07).
SURFACES = {
    ("thresholds", "value"),
    ("surfstudy", "chunk"),
    ("surfstudy", "workers"),
    ("batch", "min_trades"),
}
WFM = {("thresholds", "value"), ("wfmstudy", "modo_real"), ("wfmstudy", "charged")}


def http() -> TestClient:
    """A local app holding only the zone's router; never the real daemon, never 8765."""
    app = FastAPI()
    app.include_router(api.ROUTER)
    return TestClient(app)


def post(c: TestClient, file: str, path: list, value: object) -> tuple[int, dict]:
    """One write through the route, as the window sends it."""
    r = c.post(
        "/api/sqxconfig/value", json={"file": file, "path": path, "value": value}
    )
    return r.status_code, r.json()


def changed(before: str, after: str) -> list[str]:
    """The lines that differ between two versions of a file."""
    a, b = before.splitlines(), after.splitlines()
    return [f"{x!r} -> {y!r}" for x, y in zip(a, b) if x != y] + (
        ["length"] if len(a) != len(b) else []
    )


def leaf_paths(key: str) -> set[tuple]:
    """(file, path) of every value the zone lists for one section, ledger placeholders aside."""
    return {(f["file"], tuple(f["path"])) for f in studies.fields(key)}


def gate_checks(c: TestClient, copies: dict) -> list[str]:
    """Every key of the gate's and falsePositives' config listed, written back, comments kept."""
    out = []
    for key, name in (("gate", "gatecfg"), ("falsepositives", "fpcfg")):
        read(copies[name])
        want = {
            (name, tuple(l["path"]))
            for l in studies_leaves(copies[name])
            if l["path"][0] != "screens"
            and l["path"][-1] not in ("name", "kind", "why")
        }
        have = {x for x in leaf_paths(key) if x[0] == name}
        if want - have:
            out.append(f"{key}: faltan {sorted(want - have, key=str)}")
    # (file, path, typed, expected back): a number, a choice, a list, a blank seed, a refusal.
    for file, path, value, back in (
        ("gatecfg", ["drift", "window"], "semester", "semester"),
        ("gatecfg", ["monkey", "draws"], "6000", 6000),
        ("gatecfg", ["centring", "cap_log_rate"], "1", 1.0),
        ("gatecfg", ["centring", "cap_slope"], "0.2", 0.2),
        ("gatecfg", ["centring", "cap_slope"], "", None),
        ("gatecfg", ["homogeneity", "seed"], "7", 7),
        ("gatecfg", ["delay", "variants"], ["E+1", "ES-1"], ["E+1", "ES-1"]),
        ("gatecfg", ["cascade", "on"], False, False),
        ("fpcfg", ["population", "edges"], ["0.1", "0.2"], [0.1, 0.2]),
    ):
        before = copies[file].read_text(encoding="utf-8")
        code, res = post(c, file, path, value)
        node = read(copies[file])
        for k in path:
            node = node[k]
        diff = changed(before, copies[file].read_text(encoding="utf-8"))
        if (
            code != 200 or list(node) != back
            if isinstance(back, list)
            else (code != 200 or node != back)
        ):
            out.append(f"{file}{path} = {value!r}: {code} {res} leyó {node!r}")
        # `seed:` is first written back as `seed: null`; only its own key may differ besides.
        diff = [
            d
            for d in diff
            if f"{path[-1]}:" in d.split(" -> ")[0] or "null" not in d.split(" -> ")[1]
        ]
        if len(diff) != 1:
            out.append(f"{file}{path}: cambió más de su línea: {diff}")
    for file, path, value, why in (
        ("gatecfg", ["drift", "window"], "month", "opciones"),
        ("gatecfg", ["monkey", "draws"], "100", "mínimo"),
        ("gatecfg", ["homogeneity", "permutations"], "4999", "mínimo"),
        ("gatecfg", ["drawdown", "sequences"], "10", "mínimo"),
        ("gatecfg", ["frequency", "phi_min"], "9", "phi_max"),
        ("gatecfg", ["delay", "variants"], ["X+1"], "retraso"),
        ("gatecfg", ["cost_stress", "k"], "0.5", "mínimo"),
        ("fpcfg", ["population", "edges"], ["-1"], "mayores"),
    ):
        code, res = post(c, file, path, value)
        if code != 422 or why not in res.get("detail", ""):
            out.append(
                f"{file}{path} = {value!r} debió negarse por «{why}»: {code} {res}"
            )
    text = copies["gatecfg"].read_text(encoding="utf-8")
    if "# sorteos por estrategia" not in text or "# ventana de calendario" not in text:
        out.append("gate/config.yaml perdió comentarios al escribir")
    ledger = [f for f in studies.fields("gate") if f["file"] == "thresholds"]
    if len(ledger) != 2:
        out.append(
            f"gate.sanidad.min_trades debía salir como número y porqué del Ledger: {len(ledger)}"
        )
    return out


def studies_leaves(path: Path) -> list[dict]:
    """The leaves of one YAML file, as the zone reads them."""
    from core.assetyaml import leaves

    return leaves(path)


def main() -> None:
    """List both sections, then write on temporary copies and read the files back."""
    failures = []
    real = {k: p.read_bytes() for k, p in studies.FILES.items() if p.exists()}
    c = http()
    secs = {s["key"]: s for s in c.get("/api/sqxconfig").json()["sections"]}
    for key, want in (
        ("wfc", WFC),
        ("cscv", CSCV),
        ("surfaces", SURFACES),
        ("wfmreading", WFM),
    ):
        have = {
            (f.get("file"), f["path"][-1] if f.get("file") != "thresholds" else "value")
            for f in secs.get(key, {"fields": []})["fields"]
        }
        missing = want - have
        if missing:
            failures.append(f"{key}: faltan {sorted(missing)}")
    blocks = [f for f in secs["cscv"]["fields"] if f["key"] == "blocks"]
    if not blocks or "12870" not in blocks[0]["help"].replace(".", "").replace(",", ""):
        failures.append("cscv: los bloques no dicen sus 12870 particiones")

    with tempfile.TemporaryDirectory() as tmp:
        # the calibration's file may not exist yet (another agent writes it)
        copies = {
            k: Path(tmp) / f"{k}.yaml" for k, p in studies.FILES.items() if p.exists()
        }
        for k in copies:
            shutil.copy(studies.FILES[k], copies[k])
        with mock.patch.dict(studies.FILES, copies):
            text = {k: p.read_text(encoding="utf-8") for k, p in copies.items()}
            code, out = post(c, "sppdesign", ["design", "min_levels"], "6")
            diff = changed(
                text["sppdesign"], copies["sppdesign"].read_text(encoding="utf-8")
            )
            if (
                code != 200
                or len(diff) != 1
                or "min_levels: 6" not in diff[0]
                or "#" not in diff[0]
            ):
                failures.append(f"min_levels: {code} {out} {diff}")
            for file, path, value, why in (
                ("sppdesign", ["design", "min_levels"], "5.5", "entero"),
                ("sppdesign", ["design", "min_levels"], "12", "max_levels"),
                ("wfmstudy", ["modo_real"], "otro", "opciones"),
                ("variants", ["execute", "project"], "Builder", "no es un valor"),
                ("batch", ["min_trades"], "-1", "mínimo"),
            ):
                code, out = post(c, file, path, value)
                if code != 422 or why not in out.get("detail", ""):
                    failures.append(
                        f"{path} = {value!r} debió negarse por «{why}»: {code} {out}"
                    )
            i = blocks[0]["path"][1]
            code, out = post(c, "thresholds", ["thresholds", i, "value"], "13")
            if code != 422 or "impar" not in out.get("detail", ""):
                failures.append(f"bloques impares aceptados: {code} {out}")
            before = text["thresholds"]
            was = read(copies["thresholds"])["thresholds"][i][
                "value"
            ]  # the ledger's, not a literal
            code, out = post(c, "thresholds", ["thresholds", i, "value"], "10")
            row = read(copies["thresholds"])["thresholds"][i]
            if (
                code != 200
                or row["value"] != 10
                or row["set_by"] != "dueño"
                or row["set_on"] != date.today()
                or f"antes {was}" not in row["why"]
                or "252" not in row["why"]
            ):
                failures.append(f"bloques no sellados: {code} {out} {dict(row)}")
            # Only the row's own lines go: its value, its date and its why (two lines folded, one after).
            gone = [
                d[2:]
                for d in difflib.ndiff(
                    before.splitlines(),
                    copies["thresholds"].read_text(encoding="utf-8").splitlines(),
                )
                if d[0] in "-+"
            ]
            if len(gone) > 7 or any(
                not d.lstrip().startswith(
                    ("value", "set_on", "why", "pasada", "10 bloques")
                )
                for d in gone
            ):
                failures.append(f"el Ledger cambió más que su fila: {gone}")
            if not out.get("reload"):
                failures.append("un cambio de bloques no pide recargar la zona")
            post(c, "thresholds", ["thresholds", i, "value"], str(was))
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
            nmin = next(
                i
                for i, r in enumerate(read(copies["thresholds"])["thresholds"])
                if r["key"] == "variants.n_min"
            )
            code, out = post(c, "thresholds", ["thresholds", nmin, "value"], "90000")
            if code != 200 or "por encima del tope" not in out["note"]:
                failures.append(f"mínimo sobre el tope sin aviso: {code} {out}")
            gap = next(
                i
                for i, r in enumerate(read(copies["thresholds"])["thresholds"])
                if r["key"] == "wfc.r_sel_min_gap"
            )
            post(c, "thresholds", ["thresholds", gap, "value"], "1")
            if not isinstance(
                read(copies["thresholds"])["thresholds"][gap]["value"], float
            ):
                failures.append("r_sel_min_gap escrito «1» perdió su tipo float")
            code, out = post(c, "batch", ["min_trades"], "31")
            if code != 200 or not out.get("reload"):
                failures.append(
                    f"un valor compartido por WFC y CSCV no pide recargar: {code} {out}"
                )
            doubled = (
                copies["thresholds"]
                .read_text(encoding="utf-8")
                .replace(
                    "  - key: marketSurfaces.null_draws", "  - key: cscv.blocks", 1
                )
            )
            copies["thresholds"].write_text(doubled, encoding="utf-8")
            r = c.get("/api/sqxconfig")
            locked = (
                [
                    f
                    for s in r.json().get("sections", [])
                    if s["key"] == "cscv"
                    for f in s["fields"]
                    if f.get("locked")
                ]
                if r.status_code == 200
                else []
            )
            if not locked or "2 veces" not in locked[0]["locked"]:
                failures.append(
                    f"una fila duplicada del Ledger tumba la zona: {r.status_code}"
                )
            failures += gate_checks(c, copies)
    if {k: p.read_bytes() for k, p in studies.FILES.items() if p.exists()} != real:
        failures.append("un fichero real cambió: las escrituras debían ir a las copias")
    if failures:
        print("\n".join(failures))
        sys.exit(1)
    print(
        f"ok: WFC {len(secs['wfc']['fields'])} valores, CSCV {len(secs['cscv']['fields'])}, "
        f"superficies {len(secs['surfaces']['fields'])}, WFM {len(secs['wfmreading']['fields'])}, "
        "escrituras y negativas sobre copias"
    )


if __name__ == "__main__":
    main()
