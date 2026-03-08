import hashlib
import html
import logging
import re
import xml.etree.ElementTree as ET

import requests

from domain.job import Job
from services.collectors.base import JobCollector

logger = logging.getLogger(__name__)

TAG_RE = re.compile(r"<[^>]+>")

# Free RSS job feeds — no auth needed
RSS_FEEDS = [
    {
        "name": "weworkremotely-devops",
        "url": "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
    },
    {
        "name": "weworkremotely-backend",
        "url": "https://weworkremotely.com/categories/remote-back-end-programming-jobs.rss",
    },
    {
        "name": "jobicy-devops",
        "url": "https://jobicy.com/?feed=job_feed&job_categories=devops&job_types=full-time",
    },
]

RELEVANT_KEYWORDS = [
    "sre", "devops", "cloud", "infrastructure", "platform",
    "reliability", "backend", "systems", "kubernetes", "terraform",
    "engineer", "developer",
]


def _is_relevant(title: str) -> bool:
    return any(kw in title.lower() for kw in RELEVANT_KEYWORDS)


def _strip_html(raw: str) -> str:
    return TAG_RE.sub(" ", html.unescape(raw or "")).strip()


class RSSCollector(JobCollector):
    def __init__(self, feeds: list[dict] = None):
        self.feeds = feeds or RSS_FEEDS

    def fetch(self) -> list[Job]:
        jobs = []
        for feed in self.feeds:
            try:
                fetched = self._fetch_feed(feed)
                logger.info(f"[rss] {feed['name']}: fetched {len(fetched)} jobs")
                jobs.extend(fetched)
            except Exception as e:
                logger.error(f"[rss] {feed['name']}: failed — {e}")
        return jobs

    def _fetch_feed(self, feed: dict) -> list[Job]:
        resp = requests.get(feed["url"], timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)

        jobs = []
        for item in root.findall(".//item"):
            title = item.findtext("title", "")
            if not _is_relevant(title):
                continue
            job = self._parse(item, feed["name"])
            if job:
                jobs.append(job)
        return jobs

    def _parse(self, item, source_name: str) -> Job | None:
        try:
            title = _strip_html(item.findtext("title", ""))
            link = item.findtext("link", "")
            description = _strip_html(item.findtext("description", ""))

            # Try to extract company from title (WWR format: "Company | Role")
            if "|" in title:
                parts = title.split("|")
                company = parts[0].strip().lower().replace(" ", "-")
                title = parts[1].strip()
            elif ":" in title:
                parts = title.split(":", 1)
                company = parts[0].strip().lower().replace(" ", "-")
                title = parts[1].strip()
            else:
                company = source_name

            raw = f"{source_name}-{company}-{title}"
            job_id = hashlib.md5(raw.encode()).hexdigest()

            return Job(
                id=job_id,
                title=title,
                company=company,
                location="Remote",
                description=description,
                required_skills=[],
                required_years=0,
                source=source_name,
                source_url=link,
                remote=True,
            )
        except Exception as e:
            logger.warning(f"[rss] parse error: {e}")
            return None