from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Request

router = APIRouter(prefix="/api")


@router.get("/health")
def get_health(request: Request) -> dict:
    config = request.app.state.config
    return {
        "status": "ok",
        "service": "backend",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "debug": config.debug,
    }
