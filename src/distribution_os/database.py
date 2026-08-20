from __future__ import annotations

import json
import hashlib
import sqlite3
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS platforms (
    platform_id TEXT PRIMARY KEY,
    platform_name TEXT NOT NULL,
    rule_status TEXT NOT NULL,
    adapter_maturity TEXT NOT NULL,
    data_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS rules (
    rule_id TEXT PRIMARY KEY,
    platform_id TEXT NOT NULL REFERENCES platforms(platform_id),
    rule_version TEXT NOT NULL,
    status TEXT NOT NULL,
    data_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(platform_id, rule_version)
);

CREATE TABLE IF NOT EXISTS verticals (
    vertical_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    status TEXT NOT NULL,
    priority TEXT NOT NULL,
    evaluated_score REAL NOT NULL,
    data_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS assets (
    asset_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    vertical_id TEXT NOT NULL,
    status TEXT NOT NULL,
    priority INTEGER NOT NULL,
    data_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS accounts (
    account_id TEXT PRIMARY KEY,
    platform_id TEXT NOT NULL REFERENCES platforms(platform_id),
    brand_name TEXT NOT NULL,
    status TEXT NOT NULL,
    health_status TEXT NOT NULL,
    data_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_one_active_publisher
ON accounts(platform_id, brand_name)
WHERE status = 'ACTIVE';

CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    asset_id TEXT,
    platform_id TEXT,
    account_id TEXT,
    job_type TEXT NOT NULL,
    priority INTEGER NOT NULL,
    status TEXT NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE,
    scheduled_at TEXT NOT NULL,
    retry_count INTEGER NOT NULL DEFAULT 0,
    data_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    started_at TEXT,
    finished_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_jobs_claim
ON jobs(status, scheduled_at, priority DESC, created_at);

CREATE TABLE IF NOT EXISTS publications (
    publication_id TEXT PRIMARY KEY,
    asset_id TEXT NOT NULL REFERENCES assets(asset_id),
    platform_id TEXT NOT NULL REFERENCES platforms(platform_id),
    account_id TEXT NOT NULL,
    asset_version TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    status TEXT NOT NULL,
    mode TEXT NOT NULL,
    data_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(content_hash, platform_id, account_id, asset_version)
);

CREATE TABLE IF NOT EXISTS variants (
    variant_id TEXT PRIMARY KEY,
    asset_id TEXT NOT NULL REFERENCES assets(asset_id),
    platform_id TEXT NOT NULL REFERENCES platforms(platform_id),
    asset_version TEXT NOT NULL,
    adapter_name TEXT NOT NULL,
    adapter_version TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    status TEXT NOT NULL,
    data_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(asset_id, platform_id, asset_version, adapter_version, content_hash)
);

CREATE TABLE IF NOT EXISTS metrics (
    metric_id TEXT PRIMARY KEY,
    asset_id TEXT NOT NULL,
    platform_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    source TEXT NOT NULL,
    data_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS experiments (
    experiment_id TEXT PRIMARY KEY,
    vertical TEXT NOT NULL,
    platform TEXT NOT NULL,
    decision TEXT NOT NULL,
    data_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS human_reviews (
    review_id TEXT PRIMARY KEY,
    job_id TEXT,
    asset_id TEXT,
    platform_id TEXT,
    action TEXT NOT NULL,
    status TEXT NOT NULL,
    risk_level TEXT NOT NULL,
    data_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    resolved_at TEXT
);

CREATE TABLE IF NOT EXISTS audit_logs (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id TEXT,
    reason TEXT NOT NULL,
    input_json TEXT NOT NULL,
    output_json TEXT NOT NULL,
    token_usage INTEGER NOT NULL DEFAULT 0,
    result TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS token_usage (
    usage_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    task TEXT NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    cached_tokens INTEGER NOT NULL,
    estimated_cost REAL NOT NULL,
    asset_id TEXT,
    job_id TEXT
);

CREATE TABLE IF NOT EXISTS human_time (
    entry_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    task TEXT NOT NULL,
    human_minutes REAL NOT NULL,
    asset_id TEXT,
    job_id TEXT,
    notes TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS circuit_breakers (
    platform_id TEXT PRIMARY KEY,
    failure_count INTEGER NOT NULL DEFAULT 0,
    state TEXT NOT NULL DEFAULT 'CLOSED',
    opened_at TEXT,
    last_failure_at TEXT,
    last_error TEXT
);

CREATE TABLE IF NOT EXISTS health_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    component_type TEXT NOT NULL,
    component_id TEXT NOT NULL,
    status TEXT NOT NULL,
    details_json TEXT NOT NULL
);
"""


class Database:
    def __init__(self, path: Path):
        self.path = Path(path)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA busy_timeout = 5000")
        return connection

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.executescript(SCHEMA)
            review_columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(human_reviews)").fetchall()
            }
            if "action" not in review_columns:
                connection.execute(
                    "ALTER TABLE human_reviews ADD COLUMN action TEXT NOT NULL DEFAULT ''"
                )

    @contextmanager
    def transaction(self, immediate: bool = False) -> Iterator[sqlite3.Connection]:
        connection = self.connect()
        try:
            connection.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        with self.connect() as connection:
            connection.execute(sql, params)

    def fetch_one(self, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Row | None:
        with self.connect() as connection:
            return connection.execute(sql, params).fetchone()

    def fetch_all(self, sql: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        with self.connect() as connection:
            return list(connection.execute(sql, params).fetchall())

    def set_setting(self, key: str, value: Any, timestamp: str) -> None:
        self.execute(
            """
            INSERT INTO settings(key, value_json, updated_at) VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json,
                updated_at=excluded.updated_at
            """,
            (key, json.dumps(value, ensure_ascii=False), timestamp),
        )

    def get_setting(self, key: str, default: Any = None) -> Any:
        row = self.fetch_one("SELECT value_json FROM settings WHERE key = ?", (key,))
        return default if row is None else json.loads(row["value_json"])

    def backup(self, destination: Path) -> dict[str, Any]:
        destination = Path(destination).resolve()
        source = self.path.resolve()
        if destination == source:
            raise ValueError("Backup destination must differ from the live database")
        if destination.exists():
            raise FileExistsError(f"Backup already exists: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        handle = tempfile.NamedTemporaryFile(
            prefix=f".{destination.name}.",
            suffix=".tmp",
            dir=destination.parent,
            delete=False,
        )
        temporary = Path(handle.name)
        handle.close()
        try:
            with self.connect() as live, sqlite3.connect(temporary) as snapshot:
                live.backup(snapshot)
                result = snapshot.execute("PRAGMA integrity_check").fetchone()
                if result is None or result[0] != "ok":
                    raise RuntimeError(f"SQLite integrity check failed: {result}")
            temporary.replace(destination)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
        digest = hashlib.sha256(destination.read_bytes()).hexdigest()
        return {
            "path": str(destination),
            "bytes": destination.stat().st_size,
            "sha256": digest,
            "integrity_check": "ok",
        }
