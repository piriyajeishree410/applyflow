from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Job:
    id: str                          # hash(source + company + title)
    title: str
    company: str
    location: str
    description: str
    required_skills: list[str]       # parsed from JD
    required_years: int              # parsed from JD, 0 if not found
    source: str                      # "greenhouse", "lever", "rss"
    source_url: str
    remote: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)