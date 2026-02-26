import sqlite3
from pathlib import Path

DB_PATH = Path("data/applyflow.db")


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # access columns by name
    return conn


def init_db() -> None:
    """Create tables if they don't exist."""
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS jobs (
                id            TEXT PRIMARY KEY,
                title         TEXT NOT NULL,
                company       TEXT NOT NULL,
                location      TEXT,
                description   TEXT,
                required_skills TEXT,        -- JSON array stored as text
                required_years  INTEGER DEFAULT 0,
                source        TEXT,
                source_url    TEXT,
                remote        INTEGER DEFAULT 0,
                created_at    TEXT
            );

            CREATE TABLE IF NOT EXISTS applications (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id        TEXT NOT NULL,
                status        TEXT DEFAULT 'new',
                match_score   REAL DEFAULT 0.0,
                missing_skills TEXT,         -- JSON array stored as text
                matched_skills TEXT,         -- JSON array stored as text
                experience_gap INTEGER DEFAULT 0,
                notes         TEXT DEFAULT '',
                applied_at    TEXT,
                updated_at    TEXT,
                FOREIGN KEY (job_id) REFERENCES jobs(id)
            );
        """)