import logging
from domain.application import Application
from domain.resume import ResumeProfile
from domain.scoring import ScoringEngine
from infrastructure.database import init_db
from infrastructure.repositories import ApplicationRepository, JobRepository
from services.collectors.greenhouse import GreenhouseCollector
from services.parser import extract_skills, extract_years

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── Your resume profile ───────────────────────────────────────────────────────
MY_RESUME = ResumeProfile(
    name="Piriyajeishree",
    skills=[
        "docker", "terraform", "aws", "python", "github actions",
        "cloudwatch", "ecs", "ec2", "s3", "iam", "jenkins",
        "bash", "git", "linux", "postgresql",
    ],
    experience_years=2,
    domains=["SRE", "DevOps", "Cloud"],
    certifications=["AWS Certified Cloud Practitioner"],
)

# ── Companies to collect from ─────────────────────────────────────────────────
COMPANIES = [
    "cloudflare",
    "datadog",
    "elastic",
    "mongodb",
]

# ── Keywords to filter relevant roles ─────────────────────────────────────────
RELEVANT_KEYWORDS = [
    "sre", "devops", "cloud", "infrastructure", "platform",
    "reliability", "backend", "systems", "engineer",
]


def is_relevant(title: str) -> bool:
    t = title.lower()
    return any(kw in t for kw in RELEVANT_KEYWORDS)


def main():
    logger.info("=== ApplyFlow pipeline starting ===")

    # 1. Initialise DB
    init_db()
    job_repo = JobRepository()
    app_repo = ApplicationRepository()
    engine = ScoringEngine()

    # 2. Fetch jobs
    logger.info(f"Fetching jobs from {len(COMPANIES)} companies...")
    collector = GreenhouseCollector(companies=COMPANIES)
    raw_jobs = collector.fetch()
    logger.info(f"Fetched {len(raw_jobs)} total jobs")

    # 3. Filter, parse, score, persist
    saved = skipped_irrelevant = skipped_dup = 0

    for job in raw_jobs:
        # Filter by role relevance
        if not is_relevant(job.title):
            skipped_irrelevant += 1
            continue

        # Parse skills + YOE from title (description empty in Slice 1)
        job.required_skills = extract_skills(job.title)
        job.required_years = extract_years(job.title)

        # Persist job — skip if duplicate
        if not job_repo.save(job):
            skipped_dup += 1
            continue

        # Score against resume
        result = engine.score(job, MY_RESUME)

        # Save application record
        app = Application(job_id=job.id, match_score=result.final_score)
        app_repo.save(app, result)
        saved += 1

    # 4. Summary
    logger.info("=== Pipeline complete ===")
    logger.info(f"  Saved:             {saved}")
    logger.info(f"  Skipped (dup):     {skipped_dup}")
    logger.info(f"  Skipped (irrelevant): {skipped_irrelevant}")
    logger.info(f"  Total in DB:       {job_repo.count()}")

    # 5. Preview top 5 matches
    print("\n── Top 5 matches ──────────────────────────────")
    apps = app_repo.get_all()
    for a in apps[:5]:
        print(
            f"  [{a['match_score']:5.1f}]  {a['company']:15s}  "
            f"{a['title'][:50]:50s}  {a['status']}"
        )


if __name__ == "__main__":
    main()