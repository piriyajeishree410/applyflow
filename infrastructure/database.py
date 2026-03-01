import os
import sqlite3
from pathlib import Path

# Set DATABASE_URL env var to use Postgres
# Leave unset to fall back to SQLite (local dev)
DATABASE_URL = os.getenv("DATABASE_URL", "")
USE_POSTGRES = DATABASE_URL.startswith("postgresql")

SQLITE_PATH = Path("data/applyflow.db")

CREATE_JOBS_TABLE = """
    CREATE TABLE IF NOT EXISTS jobs (
        id              TEXT PRIMARY KEY,
        title           TEXT NOT NULL,
        company         TEXT NOT NULL,
        location        TEXT,
        description     TEXT,
        required_skills TEXT,
        required_years  INTEGER DEFAULT 0,
        source          TEXT,
        source_url      TEXT,
        remote          INTEGER DEFAULT 0,
        created_at      TEXT
    );
"""

CREATE_APPLICATIONS_TABLE = """
    CREATE TABLE IF NOT EXISTS applications (
        id              SERIAL PRIMARY KEY,
        job_id          TEXT NOT NULL,
        status          TEXT DEFAULT 'new',
        match_score     REAL DEFAULT 0.0,
        missing_skills  TEXT,
        matched_skills  TEXT,
        experience_gap  INTEGER DEFAULT 0,
        notes           TEXT DEFAULT '',
        applied_at      TEXT,
        updated_at      TEXT,
        FOREIGN KEY (job_id) REFERENCES jobs(id)
    );
"""


def get_connection():
    if USE_POSTGRES:
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    else:
        SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        return conn


def init_db() -> None:
    if USE_POSTGRES:
        conn = get_connection()
        with conn.cursor() as cur:
            # Postgres uses SERIAL not AUTOINCREMENT
            jobs_ddl = CREATE_JOBS_TABLE
            apps_ddl = CREATE_APPLICATIONS_TABLE
            cur.execute(jobs_ddl)
            cur.execute(apps_ddl)
        conn.commit()
        conn.close()
    else:
        with get_connection() as conn:
            # SQLite uses AUTOINCREMENT
            apps_ddl = CREATE_APPLICATIONS_TABLE.replace(
                "SERIAL PRIMARY KEY",
                "INTEGER PRIMARY KEY AUTOINCREMENT"
            )
            conn.executescript(CREATE_JOBS_TABLE + apps_ddl)