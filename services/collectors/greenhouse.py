import hashlib
import html
import logging
import re
import time

import requests

from domain.job import Job
from services.collectors.base import JobCollector

logger = logging.getLogger(__name__)

DEFAULT_COMPANIES = [
    "cloudflare",
    "datadog",
    "elastic",
    "mongodb",
]

GREENHOUSE_LIST_API   = "https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
GREENHOUSE_DETAIL_API = "https://boards-api.greenhouse.io/v1/boards/{company}/jobs/{job_id}"

# Relevant role keywords — only fetch full description for these
RELEVANT_KEYWORDS = [
    "sre", "devops", "cloud", "infrastructure", "platform",
    "reliability", "backend", "systems engineer", "site reliability",
]

TAG_RE = re.compile(r"<[^>]+>")  # strip HTML tags from descriptions


def _is_relevant(title: str) -> bool:
    t = title.lower()
    return any(kw in t for kw in RELEVANT_KEYWORDS)


def _strip_html(raw: str) -> str:
    unescaped = html.unescape(raw)       # &lt; → <, &amp; → & etc.
    return TAG_RE.sub(" ", unescaped).strip()


class GreenhouseCollector(JobCollector):
    def __init__(self, companies: list[str] = None, delay: float = 0.5):
        self.companies = companies or DEFAULT_COMPANIES
        self.delay = delay

    def fetch(self) -> list[Job]:
        jobs = []
        for company in self.companies:
            try:
                fetched = self._fetch_company(company)
                logger.info(f"[greenhouse] {company}: fetched {len(fetched)} relevant jobs")
                jobs.extend(fetched)
            except Exception as e:
                logger.error(f"[greenhouse] {company}: failed — {e}")
            time.sleep(self.delay)
        return jobs

    def _fetch_company(self, company: str) -> list[Job]:
        url = GREENHOUSE_LIST_API.format(company=company)
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        items = resp.json().get("jobs", [])

        # Pre-filter by title relevance before fetching descriptions
        relevant = [i for i in items if _is_relevant(i.get("title", ""))]
        logger.info(f"[greenhouse] {company}: {len(items)} total → {len(relevant)} relevant")

        jobs = []
        for item in relevant:
            job = self._fetch_detail(item, company)
            if job:
                jobs.append(job)
            time.sleep(self.delay)
        return jobs

    def _fetch_detail(self, item: dict, company: str) -> Job | None:
        try:
            gh_id   = item["id"]
            title   = item.get("title", "")
            location = item.get("location", {}).get("name", "")
            list_url = item.get("absolute_url", "")

            # Fetch full description
            detail_url = GREENHOUSE_DETAIL_API.format(company=company, job_id=gh_id)
            resp = requests.get(detail_url, timeout=10)
            resp.raise_for_status()
            detail = resp.json()
            raw_html = detail.get("content", "")
            description = _strip_html(raw_html)

            raw = f"greenhouse-{company}-{title}"
            job_id = hashlib.md5(raw.encode()).hexdigest()

            return Job(
                id=job_id,
                title=title,
                company=company,
                location=location,
                description=description,
                required_skills=[],   # parsed by parser after collection
                required_years=0,
                source="greenhouse",
                source_url=list_url,
                remote="remote" in location.lower(),
            )
        except Exception as e:
            logger.warning(f"[greenhouse] detail fetch failed for {item.get('id')}: {e}")
            return None