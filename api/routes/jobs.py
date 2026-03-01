import subprocess
import sys
from fastapi import APIRouter, Query
from infrastructure.repositories import ApplicationRepository

router = APIRouter()


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