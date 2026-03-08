import subprocess
import sys
import requests as http_requests
from fastapi import APIRouter, Query
from infrastructure.repositories import ApplicationRepository

router = APIRouter()


@router.get("/check-company")
def check_company(name: str = Query(...)):
    """Check if a company has a Greenhouse job board."""
    try:
        url = f"https://boards-api.greenhouse.io/v1/boards/{name.lower()}/jobs"
        r = http_requests.get(url, timeout=5)
        if r.status_code == 200:
            count = r.json().get("total", 0)
            return {"found": True, "company": name.lower(), "job_count": count}
        return {"found": False, "company": name.lower(), "job_count": 0}
    except Exception:
        return {"found": False, "company": name.lower(), "job_count": 0}


@router.get("")
def list_jobs(
    company: str = Query(None),
    status: str = Query(None),
    min_score: float = Query(0.0),
):
    """List all jobs with scores, filterable."""
    apps = ApplicationRepository().get_all()

    if company:
        apps = [a for a in apps if a["company"] == company]
    if status:
        apps = [a for a in apps if a["status"] == status]
    apps = [a for a in apps if a["match_score"] >= min_score]

    return {"jobs": apps, "total": len(apps)}


@router.post("/ingest")
def trigger_ingest():
    """Manually trigger the ingestion pipeline."""
    result = subprocess.run(
        [sys.executable, "main.py"],
        capture_output=True,
        text=True,
    )
    return {
        "success": result.returncode == 0,
        "stdout": result.stdout[-2000:],  # last 2000 chars
        "stderr": result.stderr[-500:] if result.stderr else "",
    }