import hashlib
import logging
import time

import requests

from domain.job import Job
from services.collectors.base import JobCollector

logger = logging.getLogger(__name__)

# Companies known to hire SRE/DevOps/Cloud roles via Greenhouse
DEFAULT_COMPANIES = [
    "cloudflare",
    "hashicorp",
    "datadog",
    "confluent",
    "mongodb",
    "elastic",
    "greenhouse",
    "figma",
    "notion",
    "linear",
]

GREENHOUSE_API = "https://boards-api.greenhouse.io/v1/boards/{company}/jobs"


class GreenhouseCollector(JobCollector):
    def __init__(self, companies: list[str] = None, delay: float = 1.0):
        self.companies = companies or DEFAULT_COMPANIES
        self.delay = delay  # seconds between requests — be polite

    def fetch(self) -> list[Job]:
        jobs = []
        for company in self.companies:
            try:
                fetched = self._fetch_company(company)
                logger.info(f"[greenhouse] {company}: fetched {len(fetched)} jobs")
                jobs.extend(fetched)
            except Exception as e:
                logger.error(f"[greenhouse] {company}: failed — {e}")
            time.sleep(self.delay)
        return jobs

    def _fetch_company(self, company: str) -> list[Job]:
        url = GREENHOUSE_API.format(company=company)
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        jobs = []
        for item in data.get("jobs", []):
            job = self._parse(item, company)
            if job:
                jobs.append(job)
        return jobs

    def _parse(self, item: dict, company: str) -> Job | None:
        try:
            title = item.get("title", "")
            location = item.get("location", {}).get("name", "")
            url = item.get("absolute_url", "")

            # Unique stable ID
            raw = f"greenhouse-{company}-{title}"
            job_id = hashlib.md5(raw.encode()).hexdigest()

            return Job(
                id=job_id,
                title=title,
                company=company,
                location=location,
                description="",        # full description fetched separately if needed
                required_skills=[],    # parsed by services/parser.py in next step
                required_years=0,
                source="greenhouse",
                source_url=url,
                remote="remote" in location.lower(),
            )
        except Exception as e:
            logger.warning(f"[greenhouse] parse error for item: {e}")
            return None