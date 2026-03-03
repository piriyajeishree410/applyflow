import logging
import time

from domain.application import Application
from domain.resume import ResumeProfile
from domain.scoring import ScoringEngine
from infrastructure.database import init_db
from infrastructure.repositories import ApplicationRepository, JobRepository
from services.collectors.base import JobCollector
from services.parser import extract_skills, extract_years
from monitoring import metrics

logger = logging.getLogger(__name__)


class IngestionWorker:
    """
    Orchestrates the full ingest → parse → score → persist pipeline.
    Publishes CloudWatch metrics on every run.
    """

    def __init__(
        self,
        collectors: list[JobCollector],
        resume: ResumeProfile,
        scoring_engine: ScoringEngine | None = None,
    ):
        self.collectors = collectors
        self.resume = resume
        self.engine = scoring_engine or ScoringEngine()
        self.job_repo = JobRepository()
        self.app_repo = ApplicationRepository()

    def run(self) -> dict:
        """Run one full ingestion cycle. Returns a summary dict."""
        init_db()
        start = time.time()

        saved = skipped_dup = failed = total_fetched = 0

        for collector in self.collectors:
            name = collector.__class__.__name__
            try:
                jobs = collector.fetch()
                total_fetched += len(jobs)
                logger.info(f"[worker] {name}: fetched {len(jobs)} jobs")
            except Exception as e:
                logger.error(f"[worker] {name}: fetch failed — {e}")
                failed += 1
                continue

            for job in jobs:
                try:
                    job.required_skills = extract_skills(job.description)
                    job.required_years = extract_years(job.description)

                    if not self.job_repo.save(job):
                        skipped_dup += 1
                        continue

                    result = self.engine.score(job, self.resume)
                    app = Application(
                        job_id=job.id,
                        match_score=result.final_score,
                    )
                    self.app_repo.save(app, result)
                    saved += 1

                except Exception as e:
                    logger.warning(f"[worker] job processing failed: {e}")
                    failed += 1

        duration = time.time() - start

        # Publish CloudWatch metrics
        metrics.record_jobs_fetched(total_fetched)
        metrics.record_jobs_saved(saved)
        metrics.record_duplicates_skipped(skipped_dup)
        metrics.record_failures(failed)
        metrics.record_ingestion_duration(duration)

        if failed == 0:
            metrics.record_last_successful_run()

        summary = {
            "saved": saved,
            "skipped_dup": skipped_dup,
            "failed": failed,
            "total_fetched": total_fetched,
            "duration_seconds": round(duration, 1),
            "total_in_db": self.job_repo.count(),
        }
        logger.info(f"[worker] cycle complete: {summary}")
        return summary