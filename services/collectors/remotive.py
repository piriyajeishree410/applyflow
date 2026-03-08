import hashlib
import html
import logging
import re

import requests

from domain.job import Job
from services.collectors.base import JobCollector

logger = logging.getLogger(__name__)

REMOTIVE_API = "https://remotive.com/api/remote-jobs"
TAG_RE = re.compile(r"<[^>]+>")

# Categories that map to SRE/DevOps/Cloud roles
RELEVANT_CATEGORIES = [
    "devops / sysadmin",
    "software dev",
    "backend",
]

RELEVANT_KEYWORDS = [
    "sre", "devops", "cloud", "infrastructure", "platform",
    "reliability", "backend", "systems", "kubernetes", "terraform",
]


def _is_relevant(title: str, category: str) -> bool:
    t = title.lower()
    c = category.lower()
    return any(kw in t for kw in RELEVANT_KEYWORDS) or \
           any(cat in c for cat in RELEVANT_CATEGORIES)


def _strip_html(raw: str) -> str:
    return TAG_RE.sub(" ", html.unescape(raw or "")).strip()


class RemotiveCollector(JobCollector):
    def fetch(self) -> list[Job]:
        try:
            resp = requests.get(REMOTIVE_API, timeout=10)
            resp.raise_for_status()
            jobs_raw = resp.json().get("jobs", [])

            jobs = []
            for item in jobs_raw:
                title = item.get("title", "")
                category = item.get("category", "")
                if not _is_relevant(title, category):
                    continue
                job = self._parse(item)
                if job:
                    jobs.append(job)

            logger.info(f"[remotive] fetched {len(jobs)} relevant jobs")
            return jobs

        except Exception as e:
            logger.error(f"[remotive] failed — {e}")
            return []

    def _parse(self, item: dict) -> Job | None:
        try:
            title = item.get("title", "")
            company = item.get("company_name", "").lower().replace(" ", "-")
            url = item.get("url", "")
            description = _strip_html(item.get("description", ""))
            location = item.get("candidate_required_location", "Remote")

            raw = f"remotive-{company}-{title}"
            job_id = hashlib.md5(raw.encode()).hexdigest()

            return Job(
                id=job_id,
                title=title,
                company=company,
                location=location,
                description=description,
                required_skills=[],
                required_years=0,
                source="remotive",
                source_url=url,
                remote=True,
            )
        except Exception as e:
            logger.warning(f"[remotive] parse error: {e}")
            return None