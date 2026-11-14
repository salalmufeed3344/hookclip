"""SQLite storage (local dev / single-box deploy).

Schema mirrors the Supabase migration in ../supabase/migrations/001_init.sql
so the deploy swaps the backend, not the data model. One connection per
call; the worker is single-process in P0, so this is enough.
"""
import json
import sqlite3
from datetime import datetime, timezone

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    plan TEXT NOT NULL DEFAULT 'free',
    credits INTEGER NOT NULL DEFAULT 60,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    source_url TEXT NOT NULL,
    source_type TEXT NOT NULL,
    title TEXT,
    duration_sec REAL,
    status TEXT NOT NULL DEFAULT 'queued',
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    kind TEXT NOT NULL DEFAULT 'process',
    clip_id TEXT,
    stage TEXT NOT NULL DEFAULT 'queued',
    progress REAL NOT NULL DEFAULT 0,
    error TEXT,
    attempts INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS transcripts (
    project_id TEXT PRIMARY KEY,
    segments_json TEXT NOT NULL,
    words_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS chat_windows (
    project_id TEXT NOT NULL,
    window_start REAL NOT NULL,
    msg_count INTEGER NOT NULL,
    velocity_ratio REAL NOT NULL,
    PRIMARY KEY (project_id, window_start)
);
CREATE TABLE IF NOT EXISTS moments (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    start_sec REAL NOT NULL,
    end_sec REAL NOT NULL,
    signals_json TEXT NOT NULL,
    score INTEGER NOT NULL DEFAULT 0,
    score_reason TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS hooks (
    id TEXT PRIMARY KEY,
    moment_id TEXT NOT NULL,
    text TEXT NOT NULL,
    rank INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS clips (
    id TEXT PRIMARY KEY,
    moment_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    caption_style TEXT NOT NULL DEFAULT 'bold',
    hook_text TEXT,
    trim_start REAL,
    trim_end REAL,
    export_path TEXT,
    format TEXT NOT NULL DEFAULT '9:16',
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS credit_ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    delta INTEGER NOT NULL,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS waitlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    role TEXT,
    created_at TEXT NOT NULL
);
"""


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(config.DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)
        # Lightweight migrations for DBs created before a column existed.
        for col, ddl in (
            ("kind", "ALTER TABLE jobs ADD COLUMN kind TEXT NOT NULL DEFAULT 'process'"),
            ("clip_id", "ALTER TABLE jobs ADD COLUMN clip_id TEXT"),
        ):
            try:
                conn.execute(ddl)
            except Exception:
                pass  # column already there


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def to_json(value) -> str:
    return json.dumps(value)


def from_json(text: str):
    return json.loads(text) if text else None
