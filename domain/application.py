from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ApplicationStatus(Enum):
    NEW = "new"
    APPLIED = "applied"
    PHONE_SCREEN = "phone_screen"
    TECHNICAL = "technical"
    FINAL_ROUND = "final_round"
    REJECTED = "rejected"
    OFFER = "offer"


@dataclass
class Application:
    job_id: str
    status: ApplicationStatus = ApplicationStatus.NEW
    match_score: float = 0.0
    notes: str = ""
    applied_at: datetime | None = None
    updated_at: datetime = field(default_factory=datetime.utcnow)