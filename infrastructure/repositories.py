import json
from datetime import datetime

from domain.application import Application, ApplicationStatus
from domain.job import Job
from domain.scoring import ScoreResult
from infrastructure.database import USE_POSTGRES, get_connection


def _ph() -> str:
    """Return the correct placeholder for the active DB driver."""
    return "%s" if USE_POSTGRES else "?"


def _cursor(conn):
    """Return a dict-row cursor for Postgres; plain conn for SQLite."""
    if USE_POSTGRES:
        import psycopg2.extras
        return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    return conn  # SQLite uses conn directly with row_factory


class JobRepository:
    def save(self, job: Job) -> bool:
        ph = _ph()
        conn = get_connection()
        try:
            cur = conn.cursor() if USE_POSTGRES else conn
            if USE_POSTGRES:
                cur.execute(f"SELECT id FROM jobs WHERE id = {ph}", (job.id,))
                exists = cur.fetchone()
            else:
                exists = conn.execute(
                    f"SELECT id FROM jobs WHERE id = {ph}", (job.id,)
                ).fetchone()

            if exists:
                return False

            params = (
                job.id, job.title, job.company, job.location,
                job.description, json.dumps(job.required_skills),
                job.required_years, job.source, job.source_url,
                int(job.remote), job.created_at.isoformat(),
            )
            sql = f"""
                INSERT INTO jobs
                    (id, title, company, location, description,
                     required_skills, required_years, source, source_url,
                     remote, created_at)
                VALUES ({','.join([ph]*11)})
            """
            if USE_POSTGRES:
                cur.execute(sql, params)
                conn.commit()
            else:
                conn.execute(sql, params)
            return True
        finally:
            if USE_POSTGRES:
                conn.close()

    def get_all(self) -> list[Job]:
        conn = get_connection()
        try:
            sql = "SELECT * FROM jobs ORDER BY created_at DESC"
            if USE_POSTGRES:
                import psycopg2.extras
                cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cur.execute(sql)
                rows = cur.fetchall()
            else:
                rows = conn.execute(sql).fetchall()
            return [self._row_to_job(r) for r in rows]
        finally:
            if USE_POSTGRES:
                conn.close()

    def count(self) -> int:
        conn = get_connection()
        try:
            if USE_POSTGRES:
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM jobs")
                return cur.fetchone()[0]
            else:
                return conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        finally:
            if USE_POSTGRES:
                conn.close()

    def _row_to_job(self, row) -> Job:
        return Job(
            id=row["id"],
            title=row["title"],
            company=row["company"],
            location=row["location"] or "",
            description=row["description"] or "",
            required_skills=json.loads(row["required_skills"] or "[]"),
            required_years=row["required_years"] or 0,
            source=row["source"] or "",
            source_url=row["source_url"] or "",
            remote=bool(row["remote"]),
        )


class ApplicationRepository:
    def save(self, app: Application, result: ScoreResult) -> None:
        ph = _ph()
        conn = get_connection()
        try:
            if USE_POSTGRES:
                cur = conn.cursor()
                cur.execute(
                    f"SELECT id FROM applications WHERE job_id = {ph}",
                    (app.job_id,)
                )
                exists = cur.fetchone()
            else:
                exists = conn.execute(
                    f"SELECT id FROM applications WHERE job_id = {ph}",
                    (app.job_id,)
                ).fetchone()

            now = datetime.utcnow().isoformat()

            if exists:
                sql = f"""
                    UPDATE applications
                    SET status={ph}, match_score={ph}, missing_skills={ph},
                        matched_skills={ph}, experience_gap={ph}, updated_at={ph}
                    WHERE job_id={ph}
                """
                params = (
                    app.status.value, result.final_score,
                    json.dumps(result.missing_skills),
                    json.dumps(result.matched_skills),
                    result.experience_gap, now, app.job_id,
                )
            else:
                sql = f"""
                    INSERT INTO applications
                        (job_id, status, match_score, missing_skills,
                         matched_skills, experience_gap, notes, updated_at)
                    VALUES ({','.join([ph]*8)})
                """
                params = (
                    app.job_id, app.status.value, result.final_score,
                    json.dumps(result.missing_skills),
                    json.dumps(result.matched_skills),
                    result.experience_gap, app.notes, now,
                )

            if USE_POSTGRES:
                cur.execute(sql, params)
                conn.commit()
            else:
                conn.execute(sql, params)
        finally:
            if USE_POSTGRES:
                conn.close()

    def get_all(self) -> list[dict]:
        conn = get_connection()
        try:
            sql = """
                SELECT a.*, j.title, j.company, j.location, j.source_url
                FROM applications a
                JOIN jobs j ON a.job_id = j.id
                ORDER BY a.match_score DESC
            """
            if USE_POSTGRES:
                import psycopg2.extras
                cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cur.execute(sql)
                return [dict(r) for r in cur.fetchall()]
            else:
                rows = conn.execute(sql).fetchall()
                return [dict(r) for r in rows]
        finally:
            if USE_POSTGRES:
                conn.close()

    def update_status(self, job_id: str, status: ApplicationStatus) -> None:
        ph = _ph()
        conn = get_connection()
        try:
            sql = f"""
                UPDATE applications SET status={ph}, updated_at={ph}
                WHERE job_id={ph}
            """
            params = (status.value, datetime.utcnow().isoformat(), job_id)
            if USE_POSTGRES:
                cur = conn.cursor()
                cur.execute(sql, params)
                conn.commit()
            else:
                conn.execute(sql, params)
        finally:
            if USE_POSTGRES:
                conn.close()