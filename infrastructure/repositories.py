import json
from datetime import datetime
from domain.job import Job
from domain.application import Application, ApplicationStatus
from domain.scoring import ScoreResult
from infrastructure.database import get_connection


class JobRepository:
    def save(self, job: Job) -> bool:
        """Insert job. Returns False if job already exists (dedup)."""
        with get_connection() as conn:
            existing = conn.execute(
                "SELECT id FROM jobs WHERE id = ?", (job.id,)
            ).fetchone()
            if existing:
                return False  # duplicate — silent skip

            conn.execute("""
                INSERT INTO jobs
                    (id, title, company, location, description,
                     required_skills, required_years, source, source_url,
                     remote, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job.id,
                job.title,
                job.company,
                job.location,
                job.description,
                json.dumps(job.required_skills),
                job.required_years,
                job.source,
                job.source_url,
                int(job.remote),
                job.created_at.isoformat(),
            ))
            return True

    def get_all(self) -> list[Job]:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM jobs ORDER BY created_at DESC"
            ).fetchall()
            return [self._row_to_job(r) for r in rows]

    def count(self) -> int:
        with get_connection() as conn:
            return conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]

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
        """Insert or update an application with its score result."""
        with get_connection() as conn:
            existing = conn.execute(
                "SELECT id FROM applications WHERE job_id = ?", (app.job_id,)
            ).fetchone()

            if existing:
                conn.execute("""
                    UPDATE applications
                    SET status=?, match_score=?, missing_skills=?,
                        matched_skills=?, experience_gap=?, updated_at=?
                    WHERE job_id=?
                """, (
                    app.status.value,
                    result.final_score,
                    json.dumps(result.missing_skills),
                    json.dumps(result.matched_skills),
                    result.experience_gap,
                    datetime.utcnow().isoformat(),
                    app.job_id,
                ))
            else:
                conn.execute("""
                    INSERT INTO applications
                        (job_id, status, match_score, missing_skills,
                         matched_skills, experience_gap, notes, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    app.job_id,
                    app.status.value,
                    result.final_score,
                    json.dumps(result.missing_skills),
                    json.dumps(result.matched_skills),
                    result.experience_gap,
                    app.notes,
                    datetime.utcnow().isoformat(),
                ))

    def get_all(self) -> list[dict]:
        with get_connection() as conn:
            rows = conn.execute("""
                SELECT a.*, j.title, j.company, j.location, j.source_url
                FROM applications a
                JOIN jobs j ON a.job_id = j.id
                ORDER BY a.match_score DESC
            """).fetchall()
            return [dict(r) for r in rows]

    def update_status(self, job_id: str, status: ApplicationStatus) -> None:
        with get_connection() as conn:
            conn.execute("""
                UPDATE applications
                SET status=?, updated_at=?
                WHERE job_id=?
            """, (status.value, datetime.utcnow().isoformat(), job_id))