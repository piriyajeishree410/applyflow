from dataclasses import dataclass, field
from enum import Enum


class ExperienceLevel(Enum):
    INTERN = "intern"       # 0 YOE
    ENTRY  = "entry"        # 0-2 YOE
    MID    = "mid"          # 2-5 YOE


class LocationPref(Enum):
    REMOTE  = "remote"
    HYBRID  = "hybrid"
    ONSITE  = "onsite"
    ANY     = "any"


@dataclass
class SearchProfile:
    user_id: str
    name: str                           # display name
    role_keywords: list[str]            # e.g. ["SRE", "DevOps", "Cloud Engineer"]
    required_stack: list[str]           # e.g. ["Docker", "Terraform", "AWS"]
    preferred_stack: list[str]          # nice to have
    experience_level: ExperienceLevel
    location_pref: LocationPref = LocationPref.ANY
    min_match_score: float = 0.0        # only show jobs above this threshold
    active: bool = True

    # Resume info for scoring
    skills: list[str] = field(default_factory=list)
    experience_years: int = 0
    certifications: list[str] = field(default_factory=list)