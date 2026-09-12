from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.detectors import detect_text, model_info
from app.errors import model_version
from app.models import DetectionResponse, TextDetectionRequest
from app.runner import run_detection
from app.task_store import task_store

router = APIRouter()


@router.post("/detections/text", response_model=DetectionResponse)
async def create_text_detection(
    request: TextDetectionRequest,
    background_tasks: BackgroundTasks,
) -> DetectionResponse:
    text = request.text.strip()
    if not text:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {"code": "invalid_text", "message": "The text field must not be empty."}
            },
        )

    version = model_version(request.model, "text")
    task_id = task_store.new_id()
    task = DetectionResponse(
        id=task_id,
        modality="text",
        status="queued",
        model=model_info(request.model, version),
    )
    task_store.create(task)
    background_tasks.add_task(
        run_detection, task_id, detect_text, (text, request.context, request.model, version), request.model, version
    )
    return task