from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models import DetectionResponse
from app.task_store import task_store

router = APIRouter()


@router.get("/tasks/{task_id}", response_model=DetectionResponse)
async def get_task(task_id: str) -> DetectionResponse:
    task = task_store.get(task_id)
    if task is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {"code": "task_not_found", "message": f"Task '{task_id}' was not found."}
            },
        )
    return task