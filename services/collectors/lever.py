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
    "netflix",
    "reddit",
    "twitter",
    "lyft",
    "scale-ai",
    "openai",
    "anthropic",
    "robinhood",
    "coinbase",
    "duolingo",
    "canva",
    "airtable",
    "zapier",
    "klaviyo",
    "hubspot",
]

LEVER_API = "https://api.lever.co/v0/postings/{company}?mode=json"
TAG_RE = re.compile(r"<[^>]+>")

RELEVANT_KEYWORDS = [
    "sre", "devops", "cloud", "infrastructure", "platform",
    "reliability", "backend", "systems engineer", "site reliability",
]


def _is_relevant(title: str) -> bool:
    return any(kw in title.lower() for kw in RELEVANT_KEYWORDS)


def _strip_html(raw: str) -> str:
    return TAG_RE.sub(" ", html.unescape(raw)).strip()


class LeverCollector(JobCollector):
    def __init__(self, companies: list[str] = None, delay: float = 0.5):
        self.companies = companies or DEFAULT_COMPANIES
        self.delay = delay

    def fetch(self) -> list[Job]:
        jobs = []
        for company in self.companies:
            try:
                fetched = self._fetch_company(company)
                if fetched:
                    logger.info(f"[lever] {company}: fetched {len(fetched)} relevant jobs")
                    jobs.extend(fetched)
            except Exception as e:
                logger.error(f"[lever] {company}: failed — {e}")
            time.sleep(self.delay)
        return jobs

    def _fetch_company(self, company: str) -> list[Job]:
        url = LEVER_API.format(company=company)
        for attempt in range(3):
            try:
                resp = requests.get(url, timeout=30)
                if resp.status_code == 404:
                    return []
                resp.raise_for_status()
                items = resp.json()
                jobs = []
                for item in items:
                    if not _is_relevant(item.get("text", "")):
                        continue
                    job = self._parse(item, company)
                    if job:
                        jobs.append(job)
                return jobs
            except requests.exceptions.Timeout:
                logger.warning(f"[lever] {company}: timeout attempt {attempt+1}/3")
                time.sleep(2 ** attempt)
        return []

    def _parse(self, item: dict, company: str) -> Job | None:
        try:
            title = item.get("text", "")
            location = item.get("categories", {}).get("location", "")
            url = item.get("hostedUrl", "")

            # Description from lists
            lists = item.get("lists", [])
            description = " ".join(
                _strip_html(l.get("content", "")) for l in lists
            )
            # Add plain text description
            description += " " + _strip_html(
                item.get("descriptionPlain", "") or
                item.get("description", "")
            )

            raw = f"lever-{company}-{title}"
            job_id = hashlib.md5(raw.encode()).hexdigest()

            return Job(
                id=job_id,
                title=title,
                company=company,
                location=location,
                description=description,
                required_skills=[],
                required_years=0,
                source="lever",
                source_url=url,
                remote="remote" in location.lower(),
            )
        except Exception as e:
            logger.warning(f"[lever] parse error: {e}")
            return None