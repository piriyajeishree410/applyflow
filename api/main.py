from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from infrastructure.database import init_db, get_connection, USE_POSTGRES
from infrastructure.repositories import JobRepository, ApplicationRepository
from api.routes import jobs, applications, analytics

app = FastAPI(title="ApplyFlow API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
app.include_router(applications.router, prefix="/applications", tags=["applications"])
app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])


@app.on_event("startup")
def startup():
    init_db()


@app.get("/health")
def health():
    """Health check — used by ECS and dashboard status bar."""
    db_status = "connected"
    try:
        conn = get_connection()
        if USE_POSTGRES:
            cur = conn.cursor()
            cur.execute("SELECT 1")
            conn.close()
        else:
            conn.execute("SELECT 1")
    except Exception as e:
        db_status = f"error: {e}"

    return {
        "status": "ok" if db_status == "connected" else "degraded",
        "db": db_status,
        "timestamp": datetime.utcnow().isoformat(),
        "total_jobs": JobRepository().count(),
        "total_applications": len(ApplicationRepository().get_all()),
    }