from fastapi import APIRouter
from app.db.connection import db_manager

router = APIRouter(tags=["Health"])

@router.get("/health/live")
def health_live():
    return {"status": "alive", "service": "oceanguard-backend"}

@router.get("/health/ready")
def health_ready():
    db_status = "connected_mock" if db_manager.is_mock else "connected_live"
    return {
        "status": "ready",
        "database": db_status,
        "environment": "active"
    }
