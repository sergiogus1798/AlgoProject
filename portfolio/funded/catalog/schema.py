"""The funding database's tables, keys and connection — one SQLite file under the data root."""

import sqlite3
from pathlib import Path

from core.datapaths import funding_dir

DB = funding_dir() / "funding.sqlite"

# Natural key and value columns of every versioned table. A row is current while `valid_to` is
# NULL; a change closes it and opens a new one, so every past price and rule stays queryable.
TABLES = {
    "plans": (("plan_key",),
              ("firm", "family", "steps", "size", "account_ccy", "price", "price_ccy",
               "platform", "eas_allowed")),
    "stages": (("plan_key", "stage"),
               ("profit_target_pct", "daily_loss_pct", "max_loss_pct", "max_loss_mode",
                "min_days", "time_limit_days", "consistency_pct", "reward_share_pct",
                "payout_days", "news_ok", "weekend_ok", "filled_from")),
    "options": (("plan_key", "option_key"),
                ("label", "effect", "price_pct")),
    "rules": (("firm", "family", "rule_key"),
              ("value", "text", "source", "status", "checked_on")),
}

_DDL = """
CREATE TABLE IF NOT EXISTS {name} ({cols}, valid_from TEXT NOT NULL, valid_to TEXT);
CREATE INDEX IF NOT EXISTS {name}_current ON {name} ({keys}, valid_to);
"""

EXTRA = """
CREATE TABLE IF NOT EXISTS snapshots (firm TEXT, fetched_on TEXT, source TEXT, raw_path TEXT,
                                      sha256 TEXT, plans INTEGER);
CREATE TABLE IF NOT EXISTS changes (detected_on TEXT, tbl TEXT, key TEXT, field TEXT,
                                    old TEXT, new TEXT);
CREATE TABLE IF NOT EXISTS combos (plan_key TEXT, options TEXT, price REAL, price_ccy TEXT,
    firm TEXT, family TEXT, size REAL, eas_allowed INTEGER,
    p1_target_pct REAL, p2_target_pct REAL, p3_target_pct REAL, daily_loss_pct REAL,
    max_loss_pct REAL, max_loss_mode TEXT, min_days INTEGER, consistency_pct REAL,
    reward_share_pct REAL, payout_days INTEGER, news_ok INTEGER, weekend_ok INTEGER,
    extras TEXT);
"""


def connect(path: Path = DB) -> sqlite3.Connection:
    """Open the database, creating any missing table."""
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    for name, (keys, values) in TABLES.items():
        db.executescript(_DDL.format(name=name, cols=", ".join(keys + values),
                                     keys=", ".join(keys)))
    db.executescript(EXTRA)
    return db
