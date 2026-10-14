"""Names vulture cannot see a caller for, and why each stays.

Run `python3 -m vulture . tools/vulture_whitelist.py --min-confidence 60 --exclude scratch,tools/sqx-lab,archive`;
a new finding is dead code (delete it, rule 21) or belongs here with its reason.
"""

# ruff: noqa
# pyright: reportUndefinedVariable=false, reportUnusedExpression=false

# attribute set on a stdlib/third-party object, read by that library
_.whitespace  # .claude/hooks/shellwords.py
_.whitespace_split  # .claude/hooks/shellwords.py
_.commenters  # .claude/hooks/shellwords.py
_.preserve_quotes  # core/assetyaml.py
_.row_factory  # portfolio/funded/sim/plans.py
_.row_factory  # sqx/projects/registryxml.py

# MCP tools: registered by the @mcp.tool decorator
mt5_status  # mt5/server.py
mt5_compile  # mt5/server.py
mt5_backtest_start  # mt5/server.py
mt5_backtest_result  # mt5/server.py
mt5_runs  # mt5/server.py
mt5_compare  # mt5/server.py
mt5_account  # mt5/server.py
mt5_symbols  # mt5/server.py
mt5_symbol  # mt5/server.py
mt5_bars  # mt5/server.py
mt5_ticks  # mt5/server.py
mt5_positions  # mt5/server.py
mt5_history  # mt5/server.py

# test fixtures, monkeypatch lambdas and mock signatures: the signature is forced by the thing replaced
top_  # tests/test_advance.py
side_buy  # tests/test_fleet_progress.py
_.row_factory  # tests/test_funded_price.py
LENGTHS  # tests/test_inference_vs_jsharpe.py
SHARPES  # tests/test_inference_vs_jsharpe.py
BENCHMARKS  # tests/test_inference_vs_jsharpe.py
TRIALS  # tests/test_inference_vs_jsharpe.py
feed_name  # tests/test_marketprofile.py
_.do_POST  # tests/test_perf66_fakesqx.py
_.log_message  # tests/test_perf66_fakesqx.py
_.writeable  # tests/test_perf66_kernel.py
_.__class__  # tests/test_perf66_live_presave.py
WRITTEN  # tests/test_perf66_membank.py
feed_name  # tests/test_pooledprofile.py
scores10  # tests/test_portfolio_stagea.py
scores_ftmo  # tests/test_portfolio_stagea.py
feed_name  # tests/test_profilepower.py
pr  # tests/test_ui_research.py

# FastAPI route handlers: reached by the @ROUTER decorator, never called by name
confirmable  # ui/daemon/advance/api.py
archive_list  # ui/daemon/archive/api.py
archive_show  # ui/daemon/archive/api.py
tick_size  # ui/daemon/assetapi.py
min_distance  # ui/daemon/assetapi.py
asset_state  # ui/daemon/assetapi.py
set_asset_value  # ui/daemon/assetapi.py
new_asset  # ui/daemon/assetapi.py
retire_asset  # ui/daemon/assetapi.py
restore_asset  # ui/daemon/assetapi.py
get_batch  # ui/daemon/batch/api.py
get_has  # ui/daemon/batch/api.py
campaign_list  # ui/daemon/campaign/api.py
campaign_show  # ui/daemon/campaign/api.py
campaign_open  # ui/daemon/campaign/api.py
campaign_extra  # ui/daemon/campaign/api.py
author  # ui/daemon/create/api.py
feedquality  # ui/daemon/data/api.py
get_panels  # ui/daemon/databank/api.py
get_table  # ui/daemon/databank/api.py
get_segments  # ui/daemon/databank/api.py
get_columns  # ui/daemon/databank/api.py
post_columns  # ui/daemon/databank/api.py
get_equity  # ui/daemon/databank/api.py
post_equity  # ui/daemon/databank/api.py
get_funnel  # ui/daemon/databank/api.py
get_state  # ui/daemon/filters/api.py
get_saved  # ui/daemon/filters/api.py
post_saved  # ui/daemon/filters/api.py
_reap  # ui/daemon/jobs.py
job_list  # ui/daemon/jobsapi.py
progress_installs  # ui/daemon/jobsapi.py
progress_state  # ui/daemon/jobsapi.py
confirmable  # ui/daemon/launch/api.py
load_status  # ui/daemon/loader/api.py
force_close  # ui/daemon/mt5bridge/api.py
get_pulse  # ui/daemon/ops/api.py
get_sqx_runs  # ui/daemon/ops/api.py
get_steps  # ui/daemon/ops/api.py
get_ledger  # ui/daemon/ops/api.py
every_project  # ui/daemon/projects/api.py
one_project  # ui/daemon/projects/api.py
find_strategy  # ui/daemon/projects/api.py
catalogue_list  # ui/daemon/results/api.py
strategy_presence  # ui/daemon/results/api.py
study_run  # ui/daemon/runner/api.py
study_only  # ui/daemon/runner/api.py
study_offer  # ui/daemon/runner/api.py
study_screen  # ui/daemon/runner/api.py
job_cancel  # ui/daemon/runner/api.py
sqxconfig  # ui/daemon/sqxconfig/api.py
strategy_meta  # ui/daemon/strategy/api.py
strategy_costcurve  # ui/daemon/strategy/api.py
strategy_stats  # ui/daemon/strategy/api.py
strategy_archive  # ui/daemon/strategy/api.py
trade_gallery  # ui/daemon/tearmarket/api.py
tearsheet_exits  # ui/daemon/tearsheet/api.py
coverage_matrix  # ui/daemon/templates.py
palette_state  # ui/daemon/templates.py
set_palette  # ui/daemon/templates.py
new_palette  # ui/daemon/templates.py
delete_palette  # ui/daemon/templates.py
interview_step  # ui/daemon/templates.py
interview_finish  # ui/daemon/templates.py
get_workflow  # ui/daemon/workflow/api.py
post_run  # ui/daemon/workflow/api.py
post_backfill  # ui/daemon/workflow/api.py

# Qt overrides: the framework calls them by name
_.paintEvent  # ui/desktop/batchview/parallel.py
_.mouseMoveEvent  # ui/desktop/batchview/parallel.py
_.leaveEvent  # ui/desktop/batchview/parallel.py
_.paintEvent  # ui/desktop/blocks/chart.py
_.mouseMoveEvent  # ui/desktop/blocks/chart.py
_.leaveEvent  # ui/desktop/blocks/chart.py
_.eventFilter  # ui/desktop/cmdpalette.py
_.eventFilter  # ui/desktop/combofix.py
_.mousePressEvent  # ui/desktop/helpmark.py
_.mouseReleaseEvent  # ui/desktop/helpmark.py
_.eventFilter  # ui/desktop/helpmark.py
_.eventFilter  # ui/desktop/helpmark.py
_.base_url  # ui/desktop/portfolios/preview.py
_.mouseReleaseEvent  # ui/desktop/workspace/card.py
_.paintEvent  # ui/desktop/workspace/curves.py
_.paintEvent  # ui/desktop/workspace/curves.py
_.paintEvent  # ui/desktop/workspace/funnel.py
_.eventFilter  # ui/desktop/workspace/gallery.py
_.mouseReleaseEvent  # ui/desktop/workspace/railrow.py

# Documented public accessor or module constant that a README / RULES.md / script reads by name
set_expected_sign  # core/assetwrite/markets.py
broker_pct  # core/commission.py
MIRRORS  # core/paths.py
view_file  # core/paths.py
PRESERVES  # engines/resample/draws.py
PAYS  # studies/research/marketProfile/favourable.py
bucket  # ui/daemon/data/catalogue.py
HISTORY_FALLBACK_YEARS  # ui/daemon/mt5bridge/runs.py
