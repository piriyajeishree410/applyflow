from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from domain.application import ApplicationStatus
from infrastructure.repositories import ApplicationRepository

router = APIRouter()


class StatusUpdate(BaseModel):
    status: str
    notes: str = ""


@router.get("")
def list_applications():
    return {"applications": ApplicationRepository().get_all()}


@router.patch("/{job_id}")
def update_status(job_id: str, body: StatusUpdate):
    try:
        status = ApplicationStatus(body.status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {body.status}")

    ApplicationRepository().update_status(job_id, status)
    return {"job_id": job_id, "status": body.status, "updated": True}