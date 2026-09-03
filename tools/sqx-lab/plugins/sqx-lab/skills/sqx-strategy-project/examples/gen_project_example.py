r"""
gen_project_example.py — worked example: clone a base project on THIS install and wire
a template set into N build tasks.

    python examples/gen_project_example.py            # emits to engine/out/ (no install writes)
    python examples/gen_project_example.py --deploy   # also places it into the install (SQX MUST be closed)

Edit INSTALL / BASE_FOLDER / TEMPLATE_SET / NEW_NAME below for your install. Run
`python engine/discover.py "<install>"` first and read catalog.json to pick real names.
"""
import os
import sys
import glob

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine.generate import make_project, deploy  # noqa: E402

# ---- EDIT THESE (use catalog.json names) ---------------------------------------------
INSTALL      = r"C:\StrategyQuantX"
BASE_FOLDER  = "FX_ID_60_MKT_NEW"            # a clonable project (its donor task = settings/data)
TEMPLATE_SET = "breakout_fleet"             # a set under user/settings/StrategyTemplates/
NEW_NAME     = "FX_ID_60_MKT_DEMO"          # the new project's name + folder
DB_PREFIX    = "BS-"                         # output-databank naming (unique per task)
AVG_TRADES   = 2                             # optional acceptance override (None = inherit donor)
TIME_MINUTES = 5                             # optional per-task time cap (None = inherit donor)
LIMIT        = None                          # int to wire only the first N templates, or None for all
# --------------------------------------------------------------------------------------

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def main():
    base = os.path.join(INSTALL, "user", "projects", BASE_FOLDER, "project.cfx")
    tpl_dir = os.path.join(INSTALL, "user", "settings", "StrategyTemplates", TEMPLATE_SET)
    if not os.path.isfile(base):
        raise SystemExit(f"base project not found: {base}")
    if not os.path.isdir(tpl_dir):
        raise SystemExit(f"template set not found: {tpl_dir}")

    picks = sorted(glob.glob(os.path.join(tpl_dir, "*.sqx")))
    if LIMIT:
        picks = picks[:LIMIT]
    if not picks:
        raise SystemExit(f"no .sqx in {tpl_dir}")

    tasks = [{
        "template": p,
        "output_db": DB_PREFIX + os.path.splitext(os.path.basename(p))[0],
        "avg_trades": AVG_TRADES,
        "time_minutes": TIME_MINUTES,
    } for p in picks]

    out_cfx = os.path.join(ROOT, "engine", "out", NEW_NAME, "project.cfx")
    report = make_project(base, NEW_NAME, tasks, out_cfx=out_cfx)

    print(f"clone of {BASE_FOLDER}  ->  {NEW_NAME}")
    print(f"  wired {len(tasks)} tasks from '{TEMPLATE_SET}'")
    print(f"  verify: {report}")
    print(f"  emitted: {out_cfx}")

    if "--deploy" in sys.argv:
        print("\n--deploy: ensure SQX is CLOSED.")
        dest = deploy(out_cfx, INSTALL, NEW_NAME)
        print(f"  deployed -> {dest}")
        print("  open SQX, open the project, run a Build on one task to confirm.")
    else:
        print("\n(dry emit only — pass --deploy to place it into the install, SQX closed)")


if __name__ == "__main__":
    main()
