import logging

from domain.resume import ResumeProfile
from infrastructure.repositories import ApplicationRepository
from services.collectors.greenhouse import GreenhouseCollector
from workers.ingestion_worker import IngestionWorker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

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

COMPANIES = [
    "cloudflare",
    "datadog",
    "elastic",
    "mongodb",
]


def main():
    logger.info("=== ApplyFlow pipeline starting ===")

    worker = IngestionWorker(
        collectors=[GreenhouseCollector(companies=COMPANIES)],
        resume=MY_RESUME,
    )
    summary = worker.run()

    logger.info("=== Pipeline complete ===")
    logger.info(f"  Saved:         {summary['saved']}")
    logger.info(f"  Skipped (dup): {summary['skipped_dup']}")
    logger.info(f"  Failed:        {summary['failed']}")
    logger.info(f"  Total in DB:   {summary['total_in_db']}")

    # Preview top 5
    print("\n── Top 5 matches ──────────────────────────────")
    for a in ApplicationRepository().get_all()[:5]:
        print(
            f"  [{a['match_score']:5.1f}]  {a['company']:15s}  "
            f"{a['title'][:50]:50s}  {a['status']}"
        )


if __name__ == "__main__":
    main()