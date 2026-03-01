import json
from collections import Counter
from fastapi import APIRouter
from domain.application import ApplicationStatus
from infrastructure.repositories import ApplicationRepository

router = APIRouter()


@router.get("/conversion")
def conversion_stats():
    """Interview and offer conversion rates."""
    apps = ApplicationRepository().get_all()
    total = len(apps)
    if total == 0:
        return {"total": 0}

    counts = Counter(a["status"] for a in apps)
    applied = counts.get(ApplicationStatus.APPLIED.value, 0)
    interviewed = sum(counts.get(s.value, 0) for s in [
        ApplicationStatus.PHONE_SCREEN,
        ApplicationStatus.TECHNICAL,
        ApplicationStatus.FINAL_ROUND,
    ])
    offers = counts.get(ApplicationStatus.OFFER.value, 0)

    return {
        "total": total,
        "applied": applied,
        "interviewed": interviewed,
        "offers": offers,
        "interview_rate": round(interviewed / applied * 100, 1) if applied else 0,
        "offer_rate": round(offers / applied * 100, 1) if applied else 0,
        "by_status": dict(counts),
    }


@router.get("/skills-gap")
def skills_gap():
    """Most frequently missing skills across all jobs."""
    apps = ApplicationRepository().get_all()
    all_missing = []
    for a in apps:
        missing = json.loads(a.get("missing_skills") or "[]")
        all_missing.extend(missing)

    counts = Counter(all_missing)
    return {
        "top_missing_skills": [
            {"skill": skill, "count": count}
            for skill, count in counts.most_common(10)
        ]
    }