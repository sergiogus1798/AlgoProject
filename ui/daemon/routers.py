"""Every router the daemon serves, in the order `app.py` includes them.

Each surface that would double `app.py` arrives as a router rather than as a second daemon. One
router = one line appended to `ROUTERS`; never reorder (plan 24 §5).
"""

from ui.daemon.advance.api import ROUTER as ADVANCE
from ui.daemon.launch.api import ROUTER as LAUNCH
from ui.daemon.archive.api import ROUTER as ARCHIVE
from ui.daemon.assetapi import ROUTER as ASSETS
from ui.daemon.batch.api import ROUTER as BATCH
from ui.daemon.create.api import ROUTER as CREATE
from ui.daemon.data.api import ROUTER as DATA
from ui.daemon.databank.api import ROUTER as DATABANK
from ui.daemon.filters.api import ROUTER as FILTERS
from ui.daemon.jobsapi import ROUTER as JOBS
from ui.daemon.loader.api import ROUTER as LOADER
from ui.daemon.mt5bridge.api import ROUTER as MT5BRIDGE
from ui.daemon.ops.api import ROUTER as OPS
from ui.daemon.projects.api import ROUTER as PROJECTS
from ui.daemon.research.api import ROUTER as RESEARCH
from ui.daemon.results.api import ROUTER as RESULTS
from ui.daemon.runner.api import ROUTER as RUNNER
from ui.daemon.sqxconfig.api import ROUTER as SQXCONFIG
from ui.daemon.strategy.api import ROUTER as STRATEGY
from ui.daemon.tearmarket.api import ROUTER as TEARMARKET
from ui.daemon.tearsheet.api import ROUTER as TEARSHEET
from ui.daemon.templates import ROUTER as TEMPLATES
from ui.daemon.workflow.api import ROUTER as WORKFLOW

ROUTERS = (
    TEMPLATES,
    ASSETS,
    JOBS,
    RESULTS,
    RUNNER,
    WORKFLOW,
    OPS,
    TEARSHEET,
    TEARMARKET,
    BATCH,
    LOADER,
    DATA,
    SQXCONFIG,
    PROJECTS,
    DATABANK,
    FILTERS,
    STRATEGY,
    ADVANCE,
    LAUNCH,
    ARCHIVE,
    CREATE,
    MT5BRIDGE,
    RESEARCH,
)
